# pylint: disable=too-many-lines

import collections
import copy
import enum
import logging
import os
import socket
import uuid

import heapdict
import sortedcontainers

import common.constants
import constants
import encoding.ttypes
import fib
import fsm
import interface
import kernel
import next_hop
import offer
import packet_common
import rib
import rib_route
import spf_dest
import stats
import table
import timer
import utils

MY_NODE_TIE_NR = 1
MY_PREFIX_TIE_NR = 2
MY_POS_DISAGG_TIE_NR = 3
MY_NEG_DISAGG_TIE_NR = 5

FLUSH_LIFETIME = 60


# TODO: Make static method of Node
def compare_tie_header_lifetime_age(header_lifetime_1, header_lifetime_2):
    # Returns -1 is header1 is older, returns +1 if header1 is newer, 0 if "same" age
    # It is not allowed to call this function with headers with different TIE-IDs.
    assert header_lifetime_1.header.tieid == header_lifetime_2.header.tieid
    # Highest sequence number is newer
    if header_lifetime_1.header.seq_nr < header_lifetime_2.header.seq_nr:
        return -1
    if header_lifetime_1.header.seq_nr > header_lifetime_2.header.seq_nr:
        return 1
    # When a node advertises remaining_lifetime 0 in a TIRE, it means a request (I don't have
    # that TIRE, please send it). Thus, if one header has remaining_lifetime 0 and the other
    # does not, then the one with non-zero remaining_lifetime is always newer.
    remaining_lifetime_1 = header_lifetime_1.remaining_lifetime
    remaining_lifetime_2 = header_lifetime_2.remaining_lifetime
    if remaining_lifetime_1 == 0 and remaining_lifetime_2 != 0:
        return -1
    if remaining_lifetime_1 != 0 and remaining_lifetime_2 == 0:
        return 1
    # The header with the longest remaining lifetime is considered newer. However, if the
    # difference in remaining lifetime is less than 5 minutes (300 seconds), they are considered
    # to be the same age.
    age_diff = abs(remaining_lifetime_1 - remaining_lifetime_2)
    if age_diff > common.constants.lifetime_diff2ignore:
        if remaining_lifetime_1 < remaining_lifetime_2:
            return -1
        if remaining_lifetime_1 > remaining_lifetime_2:
            return 1
    # TODO: Figure out what to do with origination_time
    # If we get this far, we have a tie (same age)
    return 0


class Node:
    _next_node_nr = 1

    ZTP_MIN_NUMBER_OF_PEER_FOR_LEVEL = 3

    SEND_TIDES_INTERVAL = 2.0

    # TODO: Use constant from Thrift file (it is currently not there, but Tony said he added it)
    # Don't use the actual lowest value 0 (which is enum value Illegal) for direction or tietype,
    # but value 1 (direction South) or value 2 (tietype TieTypeNode). Juniper RIFT doesn't accept
    # illegal values.
    MIN_TIE_ID = encoding.ttypes.TIEID(
        direction=constants.DIR_SOUTH,
        originator=0,
        tietype=common.ttypes.TIETypeType.NodeTIEType,
        tie_nr=0)
    # For the same reason don't use DirectionMaxValue or TIETypeMaxValue but North and
    # KeyValueTIEType instead
    MAX_TIE_ID = encoding.ttypes.TIEID(
        direction=constants.DIR_NORTH,
        originator=packet_common.MAX_U64,
        tietype=common.ttypes.TIETypeType.KeyValueTIEType,
        tie_nr=packet_common.MAX_U32)

    MIN_SPF_INTERVAL = 1.0

    SPF_TRIGGER_HISTORY_LENGTH = 10

    # TODO: This value is not specified anywhere in the specification
    DEFAULT_HOLD_DOWN_TIME = 3.0

    class State(enum.Enum):
        UPDATING_CLIENTS = 1
        HOLDING_DOWN = 2
        COMPUTE_BEST_OFFER = 3

    class Event(enum.Enum):
        CHANGE_LOCAL_CONFIGURED_LEVEL = 1
        NEIGHBOR_OFFER = 2
        BETTER_HAL = 3
        BETTER_HAT = 4
        LOST_HAL = 5
        LOST_HAT = 6
        COMPUTATION_DONE = 7
        HOLD_DOWN_EXPIRED = 8

    verbose_events = [Event.NEIGHBOR_OFFER]

    def remove_offer(self, removed_offer, reason):
        removed_offer.removed = True
        removed_offer.removed_reason = reason
        if removed_offer.interface_name in self._rx_offers:
            old_offer = self._rx_offers[removed_offer.interface_name]
        else:
            old_offer = None
        new_compare_needed = old_offer and not old_offer.removed
        self._rx_offers[removed_offer.interface_name] = removed_offer
        if new_compare_needed:
            self.compare_offers()

    def update_offer(self, updated_offer):
        if updated_offer.interface_name in self._rx_offers:
            old_offer = self._rx_offers[updated_offer.interface_name]
            new_compare_needed = ((old_offer.system_id != updated_offer.system_id) or
                                  (old_offer.level != updated_offer.level) or
                                  (old_offer.not_a_ztp_offer != updated_offer.not_a_ztp_offer) or
                                  (old_offer.state != updated_offer.state)
                                  )
        else:
            old_offer = None
            new_compare_needed = True
        self._rx_offers[updated_offer.interface_name] = updated_offer
        if new_compare_needed:
            self.compare_offers()
        elif old_offer is not None:
            updated_offer.best = old_offer.best
            updated_offer.best_three_way = old_offer.best_three_way

    def expire_offer(self, interface_name):
        if interface_name not in self._rx_offers:
            return

        old_offer = self._rx_offers[interface_name]
        new_compare_needed = not old_offer.removed
        old_offer.removed = True
        old_offer.removed_reason = "Hold-time expired"
        if new_compare_needed:
            self.compare_offers()

    def better_offer(self, offer1, offer2, three_way_only):
        # Don't consider removed offers
        if (offer1 is not None) and (offer1.removed):
            offer1 = None
        if (offer2 is not None) and (offer2.removed):
            offer2 = None
        # Don't consider offers that are marked "not a ZTP offer"
        if (offer1 is not None) and (offer1.not_a_ztp_offer):
            offer1 = None
        if (offer2 is not None) and (offer2.not_a_ztp_offer):
            offer2 = None
        # If asked to do so, only consider offers from neighbors in state 3-way as valid candidates
        if three_way_only:
            if (offer1 is not None) and (offer1.state != interface.Interface.State.THREE_WAY):
                offer1 = None
            if (offer2 is not None) and (offer2.state != interface.Interface.State.THREE_WAY):
                offer2 = None
        # If there is only one candidate, it automatically wins. If there are no candidates, there
        # is no best.
        if offer1 is None:
            return offer2
        if offer2 is None:
            return offer1
        # Pick the offer with the highest level
        if offer1.level > offer2.level:
            return offer1
        if offer2.level < offer1.level:
            return offer2
        # If the level is the same for both offers, pick offer with lowest system id as tie breaker
        if offer1.system_id < offer2.system_id:
            return offer1
        return offer2

    def compare_offers(self):
        # Select "best offer" and "best offer in 3-way state" and do update flags on the offers
        best_offer = None
        best_offer_three_way = None
        for compared_offer in self._rx_offers.values():
            compared_offer.best = False
            compared_offer.best_three_way = False
            best_offer = self.better_offer(best_offer, compared_offer, False)
            best_offer_three_way = self.better_offer(best_offer_three_way, compared_offer, True)
        if best_offer:
            best_offer.best = True
        if best_offer_three_way:
            best_offer_three_way.best_three_way = True
        # Determine if the Highest Available Level (HAL) would change based on the current offer.
        # If it would change, push an event, but don't update the HAL yet.
        if best_offer:
            hal = best_offer.level
        else:
            hal = None
        if self._highest_available_level != hal:
            if hal:
                self.fsm.push_event(self.Event.BETTER_HAL)
            else:
                self.fsm.push_event(self.Event.LOST_HAL)
        # Determine if the Highest Adjacency Three-way (HAT) would change based on the current
        # offer. If it would change, push an event, but don't update the HAL yet.
        if best_offer_three_way:
            hat = best_offer_three_way.level
        else:
            hat = None
        if self.highest_adjacency_three_way != hat:
            if hat:
                self.fsm.push_event(self.Event.BETTER_HAT)
            else:
                self.fsm.push_event(self.Event.LOST_HAT)

    def level_compute(self):
        # Find best offer overall and best offer in state 3-way. This was computer earlier in
        # compare_offers, which set the flag on the offer to remember the result.
        best_offer = None
        best_offer_three_way = None
        for checked_offer in self._rx_offers.values():
            if checked_offer.best:
                best_offer = checked_offer
            if checked_offer.best_three_way:
                best_offer_three_way = checked_offer
        # Update Highest Available Level (HAL)
        if best_offer:
            hal = best_offer.level
        else:
            hal = None
        self._highest_available_level = hal
        # Update Adjacency Three-way (HAT)
        if best_offer_three_way:
            hat = best_offer_three_way.level
        else:
            hat = None
        self.highest_adjacency_three_way = hat
        # Push event COMPUTATION_DONE
        self.fsm.push_event(self.Event.COMPUTATION_DONE)

    def action_level_compute(self):
        self.level_compute()

    def action_store_leaf_flags(self, leaf_flags):
        # TODO: on ChangeLocalHierarchyIndications in UpdatingClients finishes in ComputeBestOffer:
        # store leaf flags
        pass

    def action_update_or_remove_offer(self, updated_or_removed_offer):
        if updated_or_removed_offer.not_a_ztp_offer is True:
            self.remove_offer(updated_or_removed_offer, "Not a ZTP offer flag set")
        elif updated_or_removed_offer.level is None:
            self.remove_offer(updated_or_removed_offer, "Level is undefined")
        elif updated_or_removed_offer.level == common.constants.leaf_level:
            self.remove_offer(updated_or_removed_offer, "Level is leaf")
        else:
            self.update_offer(updated_or_removed_offer)

    def action_store_level(self, level_symbol):
        self._configured_level_symbol = level_symbol
        parse_result = self.parse_level_symbol(self._configured_level_symbol)
        assert parse_result is not None, "Set command should not have allowed invalid config"
        (configured_level, leaf_only, leaf_2_leaf, top_of_fabric_flag) = parse_result
        self.configured_level = configured_level
        self._leaf_only = leaf_only
        self.leaf_2_leaf = leaf_2_leaf
        self._top_of_fabric_flag = top_of_fabric_flag

    def action_purge_offers(self):
        for purged_offer in self._rx_offers.values():
            if not purged_offer.removed:
                purged_offer.removed = True
                purged_offer.removed_reason = "Purged"

    def action_update_all_lie_fsms(self):
        if self._highest_available_level is None:
            self._derived_level = None
        elif self._highest_available_level > 0:
            self._derived_level = self._highest_available_level - 1
        else:
            self._derived_level = 0

    def any_southbound_adjacencies(self):
        # We define a southbound adjacency as any adjacency between this node and a node that has
        # a numerically lower level value. It doesn't matter what state the adjacency is in.
        # TODO: confirm this with Tony.
        #
        this_node_level = self.level_value()
        if this_node_level is None:
            return False
        for checked_offer in self._rx_offers.values():
            if checked_offer.removed:
                continue
            if checked_offer.level is None:
                continue
            if checked_offer.level < this_node_level:
                return True
        return False

    def action_start_timer_on_lost_hal(self):
        if self.any_southbound_adjacencies():
            self._hold_down_timer.start()
        else:
            self.fsm.push_event(self.Event.HOLD_DOWN_EXPIRED)

    def action_stop_hold_down_timer(self):
        self._hold_down_timer.stop()

    _state_updating_clients_transitions = {
        Event.CHANGE_LOCAL_CONFIGURED_LEVEL: (State.COMPUTE_BEST_OFFER, [action_store_level]),
        Event.NEIGHBOR_OFFER: (None, [action_update_or_remove_offer]),
        Event.BETTER_HAL: (State.COMPUTE_BEST_OFFER, []),
        Event.BETTER_HAT: (State.COMPUTE_BEST_OFFER, []),
        Event.LOST_HAL: (State.HOLDING_DOWN, [action_start_timer_on_lost_hal]),
        Event.LOST_HAT: (State.COMPUTE_BEST_OFFER, []),
    }

    _state_holding_down_transitions = {
        Event.CHANGE_LOCAL_CONFIGURED_LEVEL: (State.COMPUTE_BEST_OFFER, [action_store_level]),
        Event.NEIGHBOR_OFFER: (None, [action_update_or_remove_offer]),
        Event.BETTER_HAL: (None, []),
        Event.BETTER_HAT: (None, []),
        Event.LOST_HAL: (None, []),
        Event.LOST_HAT: (None, []),
        Event.COMPUTATION_DONE: (None, []),
        Event.HOLD_DOWN_EXPIRED: (State.COMPUTE_BEST_OFFER, [action_purge_offers]),
    }

    _state_compute_best_offer_transitions = {
        Event.CHANGE_LOCAL_CONFIGURED_LEVEL: (None, [action_store_level, action_level_compute]),
        Event.NEIGHBOR_OFFER: (None, [action_update_or_remove_offer]),
        Event.BETTER_HAL: (None, [action_level_compute]),
        Event.BETTER_HAT: (None, [action_level_compute]),
        Event.LOST_HAL: (State.HOLDING_DOWN, [action_start_timer_on_lost_hal]),
        Event.LOST_HAT: (None, [action_level_compute]),
        Event.COMPUTATION_DONE: (State.UPDATING_CLIENTS, []),
    }

    _transitions = {
        State.UPDATING_CLIENTS: _state_updating_clients_transitions,
        State.HOLDING_DOWN: _state_holding_down_transitions,
        State.COMPUTE_BEST_OFFER: _state_compute_best_offer_transitions
    }

    _state_actions = {
        State.UPDATING_CLIENTS: ([action_update_all_lie_fsms], []),
        State.COMPUTE_BEST_OFFER: ([action_stop_hold_down_timer, action_level_compute], []),
    }

    fsm_definition = fsm.FsmDefinition(
        state_enum=State,
        event_enum=Event,
        transitions=_transitions,
        initial_state=State.COMPUTE_BEST_OFFER,
        state_actions=_state_actions,
        verbose_events=verbose_events)

    def __init__(self, config, engine=None, force_passive=False, stand_alone=False):
        # pylint:disable=too-many-statements
        self.engine = engine
        self._config = config
        self._node_nr = Node._next_node_nr
        Node._next_node_nr += 1
        self.name = self.get_config_attribute("name", self.generatename())
        self._passive = force_passive or self.get_config_attribute('passive', False)
        self.running = self.is_running()
        self.system_id = self.get_config_attribute("systemid", self.generate_system_id())
        self.log_id = self.name
        self.log = logging.getLogger('node')
        self._fsm_log = self.log.getChild("fsm")
        self._tie_db_log = self.log.getChild("tie_db")
        self._spf_log = self.log.getChild("spf")
        self._floodred_log = self.log.getChild("floodred")
        self._rib_log = self.log.getChild("rib")
        self._fib_log = self.log.getChild("fib")
        self._kernel_log = self.log.getChild("kernel")
        self._kernel_route_table = self.get_config_attribute("kernel_route_table", None)
        if self._kernel_route_table is None:
            if stand_alone:
                self._kernel_route_table = "main"
            elif self._node_nr <= 250:
                self._kernel_route_table = self._node_nr
            else:
                self._kernel_route_table = "none"
        if self.engine:
            simulated_interfaces = self.engine.simulated_interfaces
        else:
            simulated_interfaces = True
        self.kernel = kernel.Kernel(
            simulated_interfaces,
            self._kernel_route_table,
            self._kernel_log,
            self.log_id)
        self.log.info("[%s] Create node", self.log_id)
        self._configured_level_symbol = self.get_config_attribute('level', 'undefined')
        parse_result = self.parse_level_symbol(self._configured_level_symbol)
        assert parse_result is not None, "Configuration validation should have caught this"
        (configured_level, leaf_only, leaf_2_leaf, top_of_fabric_flag) = parse_result
        self.configured_level = configured_level
        self._leaf_only = leaf_only
        self.leaf_2_leaf = leaf_2_leaf
        self._top_of_fabric_flag = top_of_fabric_flag
        self.interfaces_by_name = sortedcontainers.SortedDict()
        self.interfaces_by_id = {}
        self.rx_lie_ipv4_mcast_address = self.get_config_attribute(
            'rx_lie_mcast_address', constants.DEFAULT_LIE_IPV4_MCAST_ADDRESS)
        self._tx_lie_ipv4_mcast_address = self.get_config_attribute(
            'tx_lie_mcast_address', constants.DEFAULT_LIE_IPV4_MCAST_ADDRESS)
        self.rx_lie_ipv6_mcast_address = self.get_config_attribute(
            'rx_lie_v6_mcast_address', constants.DEFAULT_LIE_IPV6_MCAST_ADDRESS)
        self._tx_lie_ipv6_mcast_address = self.get_config_attribute(
            'tx_lie_v6_mcast_address', constants.DEFAULT_LIE_IPV6_MCAST_ADDRESS)
        self._rx_lie_port = self.get_config_attribute('rx_lie_port', constants.DEFAULT_LIE_PORT)
        self.tx_lie_port = self.get_config_attribute('tx_lie_port', constants.DEFAULT_LIE_PORT)
        # TODO: make lie-send-interval configurable
        self.lie_send_interval_secs = constants.DEFAULT_LIE_SEND_INTERVAL_SECS
        self.rx_flood_port = self.get_config_attribute('rx_tie_port', constants.DEFAULT_TIE_PORT)
        self.floodred_enabled = self.get_config_attribute('flooding_reduction', True)
        self.floodred_redundancy = self.get_config_attribute(
            'flooding_reduction_redundancy',
            constants.DEFAULT_FLOODING_REDUCTION_REDUNDANCY)
        self.floodred_similarity = self.get_config_attribute(
            'flooding_reduction_similarity',
            constants.DEFAULT_FLOODING_REDUCTION_SIMILARITY)
        if engine:
            system_random = engine.floodred_system_random
        else:
            system_random = 0
        self.floodred_node_random = self.generate_node_random(system_random, self.system_id)
        self.floodred_parents = []
        self.floodred_grandparents = {}
        key_id = self.get_config_attribute('active_authentication_key', None)
        self.active_outer_key = self.key_id_to_key(key_id)
        self.active_outer_key_src = "Node Active Key"
        key_ids = self.get_config_attribute('accept_authentication_keys', None)
        self.accept_outer_keys = self.key_ids_to_keys(key_ids)
        self.accept_outer_keys_src = "Node Accept Keys"
        key_id = self.get_config_attribute('active_origin_authentication_key', None)
        self.active_origin_key = self.key_id_to_key(key_id)
        key_ids = self.get_config_attribute('accept_origin_authentication_keys', None)
        self.accept_origin_keys = self.key_ids_to_keys(key_ids)
        self._derived_level = None
        self._rx_offers = {}  # Indexed by interface name
        self._tx_offers = {}  # Indexed by interface name
        self._highest_available_level = None
        self.highest_adjacency_three_way = None
        self._holdtime = 1
        if self.engine:
            node_ztp_fsm_stats_sum_group = self.engine.node_ztp_fsm_stats_group
            intf_traffic_stats_sum_group = self.engine.intf_traffic_stats_group
            intf_security_stats_sum_group = self.engine.intf_security_stats_group
            intf_lie_fsm_stats_sum_group = self.engine.intf_lie_fsm_stats_group
        else:
            node_ztp_fsm_stats_sum_group = None
            intf_traffic_stats_sum_group = None
            intf_security_stats_sum_group = None
            intf_lie_fsm_stats_sum_group = None
        self.node_ztp_fsm_stats_group = stats.Group(node_ztp_fsm_stats_sum_group)
        self.intf_traffic_stats_group = stats.Group(intf_traffic_stats_sum_group)
        self.intf_security_stats_group = stats.Group(intf_security_stats_sum_group)
        self.intf_lie_fsm_stats_group = stats.Group(intf_lie_fsm_stats_sum_group)
        self._next_interface_id = 1
        if 'interfaces' in config:
            for interface_config in self._config['interfaces']:
                self.create_interface(interface_config)
        self.my_node_tie_seq_nrs = {
            common.ttypes.TieDirectionType.South: 0,
            common.ttypes.TieDirectionType.North: 0
        }
        self.my_node_tie_packet_infos = {}    # Indexed by neighbor direction
        self.peer_node_tie_packet_infos = {}  # Same-level nodes, indexed by tie_id
        self._originating_default = False
        self._my_south_prefix_tie_packet_info = None
        self._my_north_prefix_tie_packet_info = None
        self._my_pos_disagg_tie_packet_info = None
        self._parent_neighbors = None
        self._my_neg_disagg_tie_info = None
        self.tie_packet_infos = sortedcontainers.SortedDict()  # Indexed by tie_id
        self._last_received_tide_end = self.MIN_TIE_ID
        self._defer_spf_timer = None
        self._spf_triggers_count = 0
        self._spf_triggers_deferred_count = 0
        self._spf_deferred_trigger_pending = False
        self._spf_runs_count = 0
        self._spf_trigger_history = collections.deque([], self.SPF_TRIGGER_HISTORY_LENGTH)
        self._spf_destinations = {
            (constants.DIR_SOUTH, False): {},
            (constants.DIR_NORTH, False): {},
            (constants.DIR_SOUTH, True): {}
        }
        self._ipv4_fib = fib.ForwardingTable(
            constants.ADDRESS_FAMILY_IPV4,
            self.kernel,
            self._fib_log,
            self.log_id)
        self._ipv6_fib = fib.ForwardingTable(
            constants.ADDRESS_FAMILY_IPV6,
            self.kernel,
            self._fib_log,
            self.log_id)
        self._ipv4_rib = rib.RouteTable(
            constants.ADDRESS_FAMILY_IPV4,
            self._ipv4_fib,
            self._rib_log,
            self.log_id)
        self._ipv6_rib = rib.RouteTable(
            constants.ADDRESS_FAMILY_IPV6,
            self._ipv6_fib,
            self._rib_log,
            self.log_id)
        if "skip-self-orginated-ties" not in self._config:
            self.regenerate_my_node_ties()
            self.regenerate_my_north_prefix_tie()
            self.regenerate_my_south_prefix_tie()
        self._age_ties_timer = timer.Timer(
            interval=1.0,
            expire_function=self.age_ties,
            periodic=True,
            start=True)
        self.fsm = fsm.Fsm(
            definition=self.fsm_definition,
            action_handler=self,
            log=self._fsm_log,
            log_id=self.log_id,
            sum_stats_group=self.node_ztp_fsm_stats_group)
        self._hold_down_timer = timer.Timer(
            interval=self.DEFAULT_HOLD_DOWN_TIME,
            expire_function=lambda: self.fsm.push_event(self.Event.HOLD_DOWN_EXPIRED),
            periodic=False,
            start=False)
        self._send_tides_timer = timer.Timer(
            interval=self.SEND_TIDES_INTERVAL,
            expire_function=self.send_tides,
            periodic=True,
            start=True)
        self.fsm.start()

    def key_id_to_key(self, key_id):
        if self.engine:
            return self.engine.key_id_to_key(key_id)
        else:
            return None

    def key_ids_to_keys(self, key_ids):
        if self.engine:
            return self.engine.key_ids_to_keys(key_ids)
        else:
            return []

    def generate_system_id(self):
        mac_address = uuid.getnode()
        pid = os.getpid()
        system_id = (((mac_address & 0xffffffffff) << 24) |
                     (pid & 0xffff) << 8 |
                     (self._node_nr & 0xff)
                     )

        return system_id

    def generatename(self):
        return socket.gethostname().split('.')[0] + str(self._node_nr)

    @staticmethod
    def generate_node_random(system_random, system_id):
        assert 0 <= system_random <= 0xffffffffffffffff
        assert 0 <= system_id <= 0xffffffffffffffff
        system_random ^= system_id
        word_1 = system_random & 0xffff
        word_2 = (system_random >> 16) & 0xffff
        word_3 = (system_random >> 32) & 0xffff
        word_4 = (system_random >> 48) & 0xffff
        word_1 = Node.left_shift_circular_16(word_1, 1)
        word_2 = Node.left_shift_circular_16(word_1, 2)
        word_3 = Node.left_shift_circular_16(word_1, 3)
        word_4 = Node.left_shift_circular_16(word_1, 4)
        node_random = word_1 ^ word_2 ^ word_3 ^ word_4
        assert 0 <= node_random <= 0xffff
        return node_random

    @staticmethod
    def left_shift_circular_16(number, shift):
        assert 0 <= number <= 0xffff
        for _count in range(0, shift):
            number <<= 1
            if number & 0x10000:
                number &= 0xffff
                number |= 0x0001
        return number

    @staticmethod
    def parse_level_symbol(level_symbol):
        # Parse the "level symbolic value" which can be:
        # - undefined => This node uses ZTP to determine it's level value
        # - leaf => This node is hard-configured to be a leaf (not using leaf-2-leaf procedures)
        # - leaf-to-leaf => This node is hard-configured to be a leaf (does use leaf-2-leaf
        #   procedures)
        # - top-of-fabric => This node is hard-configured to be a top-of-fabric (level value 24)
        # - integer value => This node is hard-configured to be the specified level (0 means leaf)
        # This function returns
        #  - None if the level_symbol is invalid (i.e. one of the above)
        #  - (configured_level, leaf_only, leaf_2_leaf, top_of_fabric_flag) is level_symbol is valid
        if level_symbol == 'undefined':
            return (None, False, False, False)
        if level_symbol == 'leaf':
            return (None, True, False, False)
        if level_symbol == 'leaf-2-leaf':
            return (None, True, True, False)
        if level_symbol == 'top-of-fabric':
            return (None, False, False, True)
        try:
            level_value = int(level_symbol)
        except ValueError:
            return None
        leaf_only = level_value == 0
        top_of_fabric_flag = level_value == common.constants.top_of_fabric_level
        return (level_value, leaf_only, False, top_of_fabric_flag)

    def level_value(self):
        if self.configured_level is not None:
            return self.configured_level
        elif self._top_of_fabric_flag:
            return common.constants.top_of_fabric_level
        elif self._leaf_only:
            return common.constants.leaf_level
        else:
            return self._derived_level

    def level_value_str(self):
        level_value = self.level_value()
        if level_value is None:
            return 'undefined'
        else:
            return str(level_value)

    def top_of_fabric(self):
        # TODO: Not wrong per-se, but we need to implement the TOP_OF_FABRIC logic and update
        # ZTP accordingly.
        return self.level_value() == common.constants.top_of_fabric_level

    def is_leaf(self):
        return self.level_value() == common.constants.leaf_level

    def record_tx_offer(self, tx_offer):
        self._tx_offers[tx_offer.interface_name] = tx_offer

    def send_not_a_ztp_offer_on_intf(self, interface_name):
        # If ZTP is not enabled (typically because the level is hard-configured), our level value
        # is never derived from someone elses offer, so never send a poison reverse to anyone.
        if not self.zero_touch_provisioning_enabled():
            return False
        # TODO: Introduce concept of HALS (HAL offering Systems) and simply check for membership
        # Section 4.2.9.4.6 / Section B.1.3.2
        # If we received a valid offer over the interface, and the level in that offer is equal to
        # the highest available level (HAL) for this node, then we need to poison reverse, i.e. we
        # need to set the not_a_ztp_offer flag on offers that we send out over the interface.
        if not interface_name in self._rx_offers:
            # We did not receive an offer over the interface
            return False
        rx_offer = self._rx_offers[interface_name]
        if rx_offer.removed:
            # We received an offer, but it was removed from consideration for some reason
            # (e.g. level undefined, not-a-ztp-offer flag was set, received from a leaf, ...)
            return False
        if rx_offer.level == self._highest_available_level:
            # Receive a valid offer and it is equal to our HAL
            return True
        return False

    def zero_touch_provisioning_enabled(self):
        # Is "Zero Touch Provisioning (ZTP)" aka "automatic level derivation" aka "level
        # determination procedure" aka "auto configuration" active? The criteria that determine
        # whether ZTP is enabled are spelled out in the first paragraph of section 4.2.9.4.
        if self.configured_level is not None:
            return False
        elif self._top_of_fabric_flag:
            return False
        elif self._leaf_only:
            return False
        else:
            return True

    def is_running(self):
        if self.engine is None:
            running = True
        elif self.engine.active_nodes == constants.ActiveNodes.ONLY_PASSIVE_NODES:
            running = self._passive
        elif self.engine.active_nodes == constants.ActiveNodes.ALL_NODES_EXCEPT_PASSIVE_NODES:
            running = not self._passive
        else:
            running = True
        return running

    def get_config_attribute(self, attribute, default):
        if attribute in self._config:
            return self._config[attribute]
        else:
            return default

    def create_interface(self, interface_config):
        interface_name = interface_config['name']
        intf = interface.Interface(self, interface_config)
        self.interfaces_by_name[interface_name] = intf
        self.interfaces_by_id[intf.local_id] = intf
        return intf

    def cli_details_table(self):
        tab = table.Table(separators=False)
        tab.add_rows([
            ["Name", self.name],
            ["Passive", self._passive],
            ["Running", self.is_running()],
            ["System ID", utils.system_id_str(self.system_id)],
            ["Configured Level", self._configured_level_symbol],
            ["Leaf Only", self._leaf_only],
            ["Leaf 2 Leaf", self.leaf_2_leaf],
            ["Top of Fabric Flag", self._top_of_fabric_flag],
            ["Zero Touch Provisioning (ZTP) Enabled", self.zero_touch_provisioning_enabled()],
            ["ZTP FSM State", self.fsm.state.name],
            ["ZTP Hold Down Timer", self._hold_down_timer.remaining_time_str()],
            ["ZTP Hold Down Timer", self._hold_down_timer.remaining_time_str()],
            ["Highest Available Level (HAL)", self._highest_available_level],
            ["Highest Adjacency Three-way (HAT)", self.highest_adjacency_three_way],
            ["Level Value", self.level_value_str()],
            ["Receive LIE IPv4 Multicast Address", self.rx_lie_ipv4_mcast_address],
            ["Transmit LIE IPv4 Multicast Address", self._tx_lie_ipv4_mcast_address],
            ["Receive LIE IPv6 Multicast Address", self.rx_lie_ipv6_mcast_address],
            ["Transmit LIE IPv6 Multicast Address", self._tx_lie_ipv6_mcast_address],
            ["Receive LIE Port", self._rx_lie_port],
            ["Transmit LIE Port", self.tx_lie_port],
            ["LIE Send Interval", "{} secs".format(self.lie_send_interval_secs)],
            ["Receive TIE Port", self.rx_flood_port],
            ["Kernel Route Table", self._kernel_route_table],
            ["Originating South-bound Default Route", self._originating_default],
            ["Flooding Reduction Enabled", self.floodred_enabled],
            ["Flooding Reduction Redundancy", self.floodred_redundancy],
            ["Flooding Reduction Similarity", self.floodred_similarity],
            ["Flooding Reduction Node Random", self.floodred_node_random],
        ])
        return tab

    def cli_statistics_attributes(self):
        return [
            ["SPF Runs", self._spf_runs_count],
            ["SPF Deferrals", self._spf_triggers_deferred_count]
        ]

    def allocate_interface_id(self):
        # We assume an i32 is never going to wrap (i.e. no more than ~2M interfaces)
        interface_id = self._next_interface_id
        self._next_interface_id += 1
        return interface_id

    # TODO: Need to re-evaluate peer_node_tie_packet_infos when the level of this node changes

    def is_same_level_tie(self, tie_packet):
        if tie_packet.header.tieid.tietype != common.ttypes.TIETypeType.NodeTIEType:
            # Not a node TIE
            return False
        if tie_packet.header.tieid.direction != common.ttypes.TieDirectionType.South:
            # Not a south TIE. We only consider south TIEs because we only consider nodes in the
            # same plane as same-level-nodes for the purpose of positive disaggregation.
            # South-Node-TIEs from the nodes in the same plane are reflected to this node.
            # South-Node-TIEs from nodes in other planes are not relected and also not propagated
            # through interplane east-west links.
            return False
        if tie_packet.element.node.level != self.level_value():
            # Not from a node at the same level
            return False
        if tie_packet.header.tieid.originator == self.system_id:
            # From myself, i.e. not from another node
            return False
        return True

    def up_interfaces(self, interface_going_down):
        for intf in self.interfaces_by_name.values():
            if ((intf.fsm.state == interface.Interface.State.THREE_WAY) and
                    (intf != interface_going_down)):
                yield intf

    def make_node_tie_protocol_packet(self, direction, tie_nr, seq_nr):
        node_tie_packet = packet_common.make_node_tie_packet(
            name=self.name,
            level=self.level_value(),
            direction=direction,
            originator=self.system_id,
            tie_nr=tie_nr,
            seq_nr=seq_nr)
        packet_header = encoding.ttypes.PacketHeader(
            sender=self.system_id,
            level=self.level_value())
        packet_content = encoding.ttypes.PacketContent()
        protocol_packet = encoding.ttypes.ProtocolPacket(
            header=packet_header,
            content=packet_content)
        protocol_packet.content.tie = node_tie_packet
        return protocol_packet

    def regenerate_node_tie(self, direction, interface_going_down=None):
        tie_nr = MY_NODE_TIE_NR
        self.my_node_tie_seq_nrs[direction] += 1
        seq_nr = self.my_node_tie_seq_nrs[direction]
        protocol_packet = self.make_node_tie_protocol_packet(direction, tie_nr, seq_nr)
        tie_packet = protocol_packet.content.tie
        for intf in self.up_interfaces(interface_going_down):
            # Did we already report the neighbor on the other end of this interface? This
            # happens if we have multiple parallel interfaces to the same neighbor.
            if intf.neighbor.system_id in tie_packet.element.node.neighbors:
                continue
            # Gather all interfaces (link id pairs) from this node to the same neighbor. Once
            # again, this happens if we have multiple parallel interfaces to the same neighbor.
            link_ids = set()
            for intf2 in self.up_interfaces(interface_going_down):
                if intf.neighbor.system_id == intf2.neighbor.system_id:
                    local_id = intf2.local_id
                    remote_id = intf2.neighbor.local_id
                    link_id_pair = encoding.ttypes.LinkIDPair(local_id, remote_id)
                    link_ids.add(link_id_pair)
            node_neighbor = encoding.ttypes.NodeNeighborsTIEElement(
                level=intf.neighbor.level,
                cost=1,  # TODO: Take this from config file
                link_ids=link_ids,
                bandwidth=100)  # TODO: Take this from config file or interface
            tie_packet.element.node.neighbors[intf.neighbor.system_id] = node_neighbor
        packet_info = packet_common.encode_protocol_packet(protocol_packet, self.active_origin_key)
        packet_common.set_lifetime(packet_info, common.constants.default_lifetime)
        self.my_node_tie_packet_infos[direction] = packet_info
        self.store_tie_packet_info(packet_info)
        self.info("Regenerated node TIE for direction %s: %s",
                  packet_common.direction_str(direction), tie_packet)
        self.unsol_flood_tie_packet_info(packet_info)
        if self.level_value() is not None:
            self._parent_neighbors = dict(filter(lambda x: x[1].level > self.level_value(),
                                                 tie_packet.element.node.neighbors.items()))

    def regenerate_my_node_ties(self, interface_going_down=None):
        for direction in [common.ttypes.TieDirectionType.South,
                          common.ttypes.TieDirectionType.North]:
            self.regenerate_node_tie(direction, interface_going_down)

    def make_prefix_tie_protocol_packet(self, direction, seq_nr):
        prefix_tie_packet = packet_common.make_prefix_tie_packet(
            direction=direction,
            originator=self.system_id,
            tie_nr=MY_PREFIX_TIE_NR,
            seq_nr=seq_nr)
        packet_header = encoding.ttypes.PacketHeader(
            sender=self.system_id,
            level=self.level_value())
        packet_content = encoding.ttypes.PacketContent()
        protocol_packet = encoding.ttypes.ProtocolPacket(
            header=packet_header,
            content=packet_content)
        protocol_packet.content.tie = prefix_tie_packet
        return protocol_packet

    def regenerate_my_north_prefix_tie(self):
        config = self._config
        if ('v4prefixes' not in config) and ('v6prefixes' not in config):
            self._my_north_prefix_tie_packet_info = None
            tie_id = packet_common.make_tie_id(
                direction=common.ttypes.TieDirectionType.North,
                originator=self.system_id,
                tie_type=common.ttypes.TIETypeType.PrefixTIEType,
                tie_nr=MY_PREFIX_TIE_NR)
            self.remove_tie(tie_id)
            return
        protocol_packet = self.make_prefix_tie_protocol_packet(
            direction=common.ttypes.TieDirectionType.North,
            seq_nr=1)
        tie_packet = protocol_packet.content.tie
        if 'v4prefixes' in config:
            for v4prefix in config['v4prefixes']:
                prefix_str = v4prefix['address'] + "/" + str(v4prefix['mask'])
                prefix = packet_common.make_ipv4_prefix(prefix_str)
                metric = v4prefix['metric']
                tags = set(v4prefix.get('tags', []))
                packet_common.add_ipv4_prefix_to_prefix_tie(tie_packet, prefix, metric, tags)
        if 'v6prefixes' in config:
            for v6prefix in config['v6prefixes']:
                prefix_str = v6prefix['address'] + "/" + str(v6prefix['mask'])
                prefix = packet_common.make_ipv6_prefix(prefix_str)
                metric = v6prefix['metric']
                tags = set(v6prefix.get('tags', []))
                packet_common.add_ipv6_prefix_to_prefix_tie(tie_packet, prefix, metric, tags)
        packet_info = packet_common.encode_protocol_packet(protocol_packet, self.active_origin_key)
        packet_common.set_lifetime(packet_info, common.constants.default_lifetime)
        self._my_north_prefix_tie_packet_info = packet_info
        self.store_tie_packet_info(self._my_north_prefix_tie_packet_info)
        self.info("Regenerated north prefix TIE: %s", tie_packet)
        self.unsol_flood_tie_packet_info(self._my_north_prefix_tie_packet_info)

    def regenerate_my_pos_disagg_tie(self):
        # Gather the set of (prefix, metric, tags) containing all prefixes which we should currently
        # advertise in our TIE.
        should_adv_disagg = {}
        for dest in self._spf_destinations[(constants.DIR_SOUTH, False)].values():
            if dest.positively_disaggregate:
                attr = encoding.ttypes.PrefixAttributes(dest.cost, dest.tags, None)
                should_adv_disagg[dest.prefix] = attr
        # Gather the set of (prefix, metric, tags) containing all prefixes which we currently
        # actually do advertise.
        do_adv_disagg = {}
        if self._my_pos_disagg_tie_packet_info:
            protocol_packet = self._my_pos_disagg_tie_packet_info.protocol_packet
            element = protocol_packet.content.tie.element
            prefixes = element.positive_disaggregation_prefixes.prefixes
            for prefix, attr in prefixes.items():
                do_adv_disagg[prefix] = attr
        # If what we actually advertise is equal to what we should advertise, we are done.
        if do_adv_disagg == should_adv_disagg:
            return
        # Something changed; we need regenerate a new prefix TIE for the positively disaggregated
        # prefixes.
        # Determine the sequence number.
        if self._my_pos_disagg_tie_packet_info:
            protocol_packet = self._my_pos_disagg_tie_packet_info.protocol_packet
            new_seq_nr = protocol_packet.content.tie.header.seq_nr + 1
        else:
            new_seq_nr = 1
        # Build the new prefix TIE.
        tie_header = packet_common.make_tie_header(
            direction=common.ttypes.TieDirectionType.South,
            originator=self.system_id,
            tie_type=common.ttypes.TIETypeType.PositiveDisaggregationPrefixTIEType,
            tie_nr=MY_POS_DISAGG_TIE_NR,
            seq_nr=new_seq_nr)
        prefix_tie_element = encoding.ttypes.PrefixTIEElement(
            prefixes=should_adv_disagg)
        tie_element = encoding.ttypes.TIEElement(
            positive_disaggregation_prefixes=prefix_tie_element)
        tie_packet = encoding.ttypes.TIEPacket(header=tie_header, element=tie_element)
        # If the new TIE is empty and we were not already advertising a positive disaggregation
        # TIE, then don't start now.
        if (not tie_packet.element.positive_disaggregation_prefixes.prefixes
                and not self._my_pos_disagg_tie_packet_info):
            return
        # Wrap the tie_packet into a protocol packet, and encode it into a packet_info
        packet_header = encoding.ttypes.PacketHeader(
            sender=self.system_id,
            level=self.level_value())
        packet_content = encoding.ttypes.PacketContent()
        protocol_packet = encoding.ttypes.ProtocolPacket(
            header=packet_header,
            content=packet_content)
        protocol_packet.content.tie = tie_packet
        packet_info = packet_common.encode_protocol_packet(protocol_packet, self.active_origin_key)
        packet_common.set_lifetime(packet_info, common.constants.default_lifetime)
        # Make the newly constructed TIE the current positive disaggregation TIE and update the
        # database.
        self._my_pos_disagg_tie_packet_info = packet_info
        self.store_tie_packet_info(packet_info)
        self.info("Regenerated positive disaggregation TIE: %s", tie_packet)
        self.unsol_flood_tie_packet_info(packet_info)

    def regenerate_my_neg_disagg_tie(self, fallen_leafs):
        # If the no fallen leafs are present and we were not already advertising
        # a negative disaggregation TIE, return.
        if not fallen_leafs and not self._my_neg_disagg_tie_info:
            return
        if self._my_neg_disagg_tie_info:
            # Check that found fallen_leafs are equal to the ones specified
            # in the announced TIE
            protocol_packet = self._my_neg_disagg_tie_info.protocol_packet
            element = protocol_packet.content.tie.element
            tie_fallen_leafs = element.negative_disaggregation_prefixes.prefixes
            fallen_leafs_prefixes = fallen_leafs.keys()
            tie_prefixes = tie_fallen_leafs.keys()
            # Discover new fallen leaf nodes
            new_fallen_leafs = fallen_leafs_prefixes - tie_prefixes
            # Check if there are any recovered fallen leaf nodes
            recovered_leafs = tie_prefixes - fallen_leafs_prefixes
            # Nothing new to announce, exit
            if not new_fallen_leafs and not recovered_leafs:
                return
        # We need regenerate a new prefix TIE for the negatively disaggregated prefixes.
        # Determine the sequence number.
        if self._my_neg_disagg_tie_info:
            protocol_packet = self._my_neg_disagg_tie_info.protocol_packet
            new_seq_nr = protocol_packet.content.tie.header.seq_nr + 1
        else:
            new_seq_nr = 1
        # Build the new prefix TIE.
        tie_header = packet_common.make_tie_header(
            direction=common.ttypes.TieDirectionType.South,
            originator=self.system_id,
            tie_type=common.ttypes.TIETypeType.NegativeDisaggregationPrefixTIEType,
            tie_nr=MY_NEG_DISAGG_TIE_NR,
            seq_nr=new_seq_nr)
        fallen_leafs_attrs = {}
        for prefix, dest in fallen_leafs.items():
            fallen_leafs_attrs[prefix] = encoding.ttypes.PrefixAttributes(
                common.constants.infinite_distance, dest.tags, None)
        prefix_tie_element = encoding.ttypes.PrefixTIEElement(prefixes=fallen_leafs_attrs)
        tie_element = encoding.ttypes.TIEElement(
            negative_disaggregation_prefixes=prefix_tie_element)
        tie_packet = encoding.ttypes.TIEPacket(header=tie_header, element=tie_element)
        # Wrap the tie_packet into a protocol packet, and encode it into a packet_info
        packet_header = encoding.ttypes.PacketHeader(sender=self.system_id,
                                                     level=self.level_value())
        packet_content = encoding.ttypes.PacketContent()
        protocol_packet = encoding.ttypes.ProtocolPacket(header=packet_header,
                                                         content=packet_content)
        protocol_packet.content.tie = tie_packet
        packet_info = packet_common.encode_protocol_packet(protocol_packet, self.active_origin_key)
        lifetime = common.constants.default_lifetime if fallen_leafs \
            else common.constants.purge_lifetime
        packet_common.set_lifetime(packet_info, lifetime)
        self._my_neg_disagg_tie_info = packet_info
        self.store_tie_packet_info(packet_info)
        self.info("Regenerated negative disaggregation TIE: %s", tie_packet)
        self.unsol_flood_tie_packet_info(packet_info)

    def is_overloaded(self):
        # Is this node overloaded?
        # In the current implementation, we are never overloaded.
        return False

    def have_s_or_ew_adjacency(self, interface_going_down):
        # Does this node have at least one south-bound or east-west adjacency?
        for intf in self.interfaces_by_name.values():
            if ((intf.fsm.state == interface.Interface.State.THREE_WAY) and
                    (intf != interface_going_down)):
                if intf.neighbor_direction() in [constants.DIR_SOUTH,
                                                 constants.DIR_EAST_WEST]:
                    return True
        return False

    def have_ew_adjacency(self):
        # Does this node have at least one east-west adjacency?
        return any(filter(lambda x: x.fsm.state == interface.Interface.State.THREE_WAY and
                          x.neighbor_direction() == constants.DIR_EAST_WEST,
                          self.interfaces_by_name.values()))

    def other_nodes_are_overloaded(self):
        # Are all the other nodes at my level overloaded?
        if not self.peer_node_tie_packet_infos:
            # There are no other nodes at my level
            return False
        for node_tie_packet_info in self.peer_node_tie_packet_infos.values():
            node_tie_packet = node_tie_packet_info.protocol_packet.content.tie
            flags = node_tie_packet.element.node.flags
            if (flags is not None) and (not flags.overload):
                return False
        return True

    def other_nodes_have_no_n_adjacency(self):
        # Do all the other nodes at my level have NO north-bound adjacencies?
        if not self.peer_node_tie_packet_infos:
            # There are no other nodes at my level
            return False
        for node_tie_packet_info in self.peer_node_tie_packet_infos.values():
            node_tie_packet = node_tie_packet_info.protocol_packet.content.tie
            for check_neighbor in node_tie_packet.element.node.neighbors.values():
                if check_neighbor.level > self.level_value():
                    return False
        return True

    def have_n_spf_route_to_default(self):
        # Has this node computed reachability to a default route during N-SPF?
        # TODO: We need to implement SPF (route calculation before we can implement this; for now
        # always return True)
        return True

    def regenerate_my_south_prefix_tie(self, interface_going_down=None):
        if self.is_overloaded():
            decision = (False, "This node is overloaded")
        elif not self.have_s_or_ew_adjacency(interface_going_down):
            decision = (False, "This node has no south-bound or east-west adjacency")
        elif self.other_nodes_are_overloaded():
            decision = (True, "All other nodes at my level are overloaded")
        elif self.other_nodes_have_no_n_adjacency():
            decision = (True, "All other nodes at my level have no north-bound adjacencies")
        elif self.have_n_spf_route_to_default():
            decision = (True, "This node has computed reachability to a default route during N-SPF")
        (must_originate_default, reason) = decision
        # If we don't want to originate a default now, and we never originated one in the past, then
        # we don't create a prefix TIE at all. But if we have ever originated one in the past, then
        # we have to flush it by originating an empty prefix TIE.
        if (not must_originate_default) and (self._my_south_prefix_tie_packet_info is None):
            self.info("Don't originate south prefix TIE because: %s", reason)
            return
        if ((must_originate_default != self._originating_default) or
                (self._my_south_prefix_tie_packet_info is None)):
            self._originating_default = must_originate_default
            if self._my_south_prefix_tie_packet_info is None:
                next_seq_nr = 1
            else:
                protocol_packet = self._my_south_prefix_tie_packet_info.protocol_packet
                tie_packet = protocol_packet.content.tie
                next_seq_nr = tie_packet.header.seq_nr + 1
            new_protocol_packet = self.make_prefix_tie_protocol_packet(
                direction=common.ttypes.TieDirectionType.South,
                seq_nr=next_seq_nr)
            new_tie_packet = new_protocol_packet.content.tie
            if must_originate_default:
                # The specification does not mention what metric the default route should be
                # originated with. Juniper originates with metric 1, so that is what I will do as
                # well.
                metric = 1
                packet_common.add_ipv4_prefix_to_prefix_tie(
                    new_tie_packet,
                    packet_common.make_ipv4_prefix("0.0.0.0/0"),
                    metric)
                packet_common.add_ipv6_prefix_to_prefix_tie(
                    new_tie_packet,
                    packet_common.make_ipv6_prefix("::/0"),
                    metric)
            new_packet_info = packet_common.encode_protocol_packet(new_protocol_packet,
                                                                   self.active_origin_key)
            packet_common.set_lifetime(new_packet_info, common.constants.default_lifetime)
            self._my_south_prefix_tie_packet_info = new_packet_info
            self.store_tie_packet_info(self._my_south_prefix_tie_packet_info)
            self.info("Regenerated south prefix TIE because %s: %s", reason, new_tie_packet)
            self.unsol_flood_tie_packet_info(self._my_south_prefix_tie_packet_info)

    def clear_all_generated_node_ties(self):
        for direction in [common.ttypes.TieDirectionType.South,
                          common.ttypes.TieDirectionType.North]:
            node_tie_packet_info = self.my_node_tie_packet_infos[direction]
            if node_tie_packet_info is not None:
                tie_packet = node_tie_packet_info.protocol_packet.content.tie
                self.remove_tie(tie_packet.header)
                self.my_node_tie_packet_infos[direction] = None

    def send_tides(self):
        # The current implementation prepares, encodes, and sends a unique TIDE packet for each
        # individual neighbor. We do NOT (yet) have any optimization that attempts to prepare and
        # encode a TIDE only once in total or once per direction (N, S, EW). See the comment in the
        # function is_flood_allowed for a more detailed discussion on why not.
        for intf in self.interfaces_by_name.values():
            self.send_tides_on_interface(intf)

    def send_tides_on_interface(self, intf):
        if intf.fsm.state != interface.Interface.State.THREE_WAY:
            return
        tide_packet = self.generate_tide_packet(
            neighbor_direction=intf.neighbor_direction(),
            neighbor_system_id=intf.neighbor.system_id,
            neighbor_level=intf.neighbor.level,
            neighbor_is_top_of_fabric=intf.neighbor.top_of_fabric(),
            my_level=self.level_value(),
            i_am_top_of_fabric=self.top_of_fabric())
        self.debug("Regenerated TIDE for neighbor %s: %s", intf.neighbor.system_id, tide_packet)
        packet_content = encoding.ttypes.PacketContent(tide=tide_packet)
        packet_header = encoding.ttypes.PacketHeader(
            sender=self.system_id,
            level=self.level_value())
        protocol_packet = encoding.ttypes.ProtocolPacket(
            header=packet_header,
            content=packet_content)
        intf.send_protocol_packet(protocol_packet, flood=True)

    @staticmethod
    def cli_summary_headers():
        return [
            ["Node", "Name"],
            ["System", "ID"],
            ["Running"]]

    def cli_summary_attributes(self):
        return [
            self.name,
            utils.system_id_str(self.system_id),
            self.running]

    @staticmethod
    def cli_level_headers():
        return [
            ["Node", "Name"],
            ["System", "ID"],
            ["Running"],
            ["Configured", "Level"],
            ["Level", "Value"]]

    def cli_level_attributes(self):
        if self.running:
            return [
                self.name,
                utils.system_id_str(self.system_id),
                self.running,
                self._configured_level_symbol,
                self.level_value_str()]
        else:
            return [
                self.name,
                utils.system_id_str(self.system_id),
                self.running,
                self._configured_level_symbol,
                '?']

    def command_clear_intf_stats(self, cli_session, parameters):
        interface_name = parameters['interface']
        if not interface_name in self.interfaces_by_name:
            cli_session.print("Error: interface {} not present".format(interface_name))
            return
        intf = self.interfaces_by_name[interface_name]
        intf.clear_stats()

    def command_clear_node_stats(self, _cli_session):
        self.node_ztp_fsm_stats_group.clear()
        self.intf_traffic_stats_group.clear()
        self.intf_security_stats_group.clear()
        self.intf_lie_fsm_stats_group.clear()

    def command_show_intf_fsm_hist(self, cli_session, parameters, verbose):
        interface_name = parameters['interface']
        if not interface_name in self.interfaces_by_name:
            cli_session.print("Error: interface {} not present".format(interface_name))
            return
        shown_interface = self.interfaces_by_name[interface_name]
        tab = shown_interface.fsm.history_table(verbose)
        cli_session.print(tab.to_string())

    def command_show_intf_queues(self, cli_session, parameters):
        interface_name = parameters['interface']
        if not interface_name in self.interfaces_by_name:
            cli_session.print("Error: interface {} not present".format(interface_name))
            return
        intf = self.interfaces_by_name[interface_name]
        intf.command_show_intf_queues(cli_session)

    def command_show_intf_security(self, cli_session, parameters):
        interface_name = parameters['interface']
        if not interface_name in self.interfaces_by_name:
            cli_session.print("Error: interface {} not present".format(interface_name))
            return
        intf = self.interfaces_by_name[interface_name]
        cli_session.print("Outer Keys:")
        tab = intf.intf_outer_keys_table()
        cli_session.print(tab.to_string())
        cli_session.print("Nonces:")
        tab = intf.nonces_table()
        cli_session.print(tab.to_string())
        cli_session.print("Security Statistics:")
        tab = intf.security_stats_table(exclude_zero=False)
        cli_session.print(tab.to_string())

    def command_show_intf_sockets(self, cli_session, parameters):
        interface_name = parameters['interface']
        if not interface_name in self.interfaces_by_name:
            cli_session.print("Error: interface {} not present".format(interface_name))
            return
        intf = self.interfaces_by_name[interface_name]
        tab = intf.sockets_table()
        cli_session.print(tab.to_string())

    def command_show_intf_stats(self, cli_session, parameters, exclude_zero):
        interface_name = parameters['interface']
        if not interface_name in self.interfaces_by_name:
            cli_session.print("Error: interface {} not present".format(interface_name))
            return
        intf = self.interfaces_by_name[interface_name]
        cli_session.print("Traffic:")
        tab = intf.traffic_stats_table(exclude_zero)
        cli_session.print(tab.to_string())
        cli_session.print("Security:")
        tab = intf.security_stats_table(exclude_zero)
        cli_session.print(tab.to_string())
        cli_session.print("LIE FSM:")
        tab = intf.lie_fsm_stats_table(exclude_zero)
        cli_session.print(tab.to_string())

    def command_show_intf_tides(self, cli_session, parameters):
        interface_name = parameters['interface']
        if not interface_name in self.interfaces_by_name:
            cli_session.print("Error: interface {} not present".format(interface_name))
            return
        intf = self.interfaces_by_name[interface_name]
        cli_session.print("Send TIDEs:")
        tab = intf.send_tides_table()
        cli_session.print(tab.to_string())

    def command_show_interface(self, cli_session, parameters):
        interface_name = parameters['interface']
        if not interface_name in self.interfaces_by_name:
            cli_session.print("Error: interface {} not present".format(interface_name))
            return
        intf = self.interfaces_by_name[interface_name]
        cli_session.print("Interface:")
        cli_session.print(intf.cli_details_table().to_string())
        neighbor_table = intf.cli_neighbor_details_table()
        if neighbor_table:
            cli_session.print("Neighbor:")
            cli_session.print(neighbor_table.to_string())

    def command_show_interfaces(self, cli_session):
        # TODO: Report neighbor uptime (time in THREE_WAY state)
        tab = table.Table()
        tab.add_row(interface.Interface.cli_summary_headers())
        for intf in self.interfaces_by_name.values():
            tab.add_row(intf.cli_summary_attributes())
        cli_session.print(tab.to_string())

    def floodred_parents_table(self):
        tab = table.Table()
        tab.add_row(FloodRedParent.cli_summary_headers())
        for parent in self.floodred_parents:
            tab.add_row(parent.cli_summary_attributes())
        return tab

    def floodred_grandparents_table(self):
        sorted_floodred_grandparents = sortedcontainers.SortedDict(self.floodred_grandparents)
        tab = table.Table()
        tab.add_row(FloodRedGrandparent.cli_summary_headers())
        for grandparent in sorted_floodred_grandparents.values():
            tab.add_row(grandparent.cli_summary_attributes())
        return tab

    def floodred_interfaces_table(self):
        tab = table.Table()
        tab.add_row(interface.Interface.cli_floodred_summary_headers())
        for intf in self.interfaces_by_name.values():
            tab.add_row(intf.cli_floodred_summary_attributes())
        return tab

    def command_show_flooding_reduction(self, cli_session):
        cli_session.print("Parents:")
        cli_session.print(self.floodred_parents_table().to_string())
        cli_session.print("Grandparents:")
        cli_session.print(self.floodred_grandparents_table().to_string())
        cli_session.print("Interfaces:")
        cli_session.print(self.floodred_interfaces_table().to_string())

    def command_show_kernel_addresses(self, cli_session):
        self.kernel.command_show_addresses(cli_session)

    def command_show_kernel_links(self, cli_session):
        self.kernel.command_show_links(cli_session)

    def command_show_kernel_routes(self, cli_session):
        self.kernel.command_show_routes(cli_session, None)

    def command_show_kernel_routes_tab(self, cli_session, parameters):
        table_nr = self.get_table_param(cli_session, parameters)
        if table_nr is None:
            return
        self.kernel.command_show_routes(cli_session, table_nr)

    def command_show_kernel_routes_pref(self, cli_session, parameters):
        table_nr = self.get_table_param(cli_session, parameters)
        prefix = self.get_prefix_param(cli_session, parameters)
        if (table_nr is None) or (prefix is None):
            return
        self.kernel.command_show_route_prefix(cli_session, table_nr, prefix)

    def command_show_node(self, cli_session):
        cli_session.print("Node:")
        cli_session.print(self.cli_details_table().to_string())
        cli_session.print("Received Offers:")
        tab = table.Table()
        tab.add_row(offer.RxOffer.cli_headers())
        sorted_rx_offers = sortedcontainers.SortedDict(self._rx_offers)
        for off in sorted_rx_offers.values():
            tab.add_row(off.cli_attributes())
        cli_session.print(tab.to_string())
        cli_session.print("Sent Offers:")
        tab = table.Table()
        tab.add_row(offer.TxOffer.cli_headers())
        sorted_tx_offers = sortedcontainers.SortedDict(self._tx_offers)
        for off in sorted_tx_offers.values():
            tab.add_row(off.cli_attributes())
        cli_session.print(tab.to_string())

    def command_show_node_fsm_history(self, cli_session, verbose):
        tab = self.fsm.history_table(verbose)
        cli_session.print(tab.to_string())

    def command_show_node_stats(self, cli_session, exclude_zero):
        cli_session.print("Node ZTP FSM:")
        tab = self.node_ztp_fsm_stats_group.table(exclude_zero, sort_by_description=True)
        cli_session.print(tab.to_string())
        cli_session.print("Node Interfaces Traffic:")
        tab = self.intf_traffic_stats_group.table(exclude_zero)
        cli_session.print(tab.to_string())
        cli_session.print("Node Interfaces Security:")
        tab = self.intf_security_stats_group.table(exclude_zero)
        cli_session.print(tab.to_string())
        cli_session.print("Node Interface LIE FSMs:")
        tab = self.intf_lie_fsm_stats_group.table(exclude_zero, sort_by_description=True)
        cli_session.print(tab.to_string())

    @staticmethod
    def tide_content_append_tie_id(contents, tie_id):
        contents.append("  Direction: " + packet_common.direction_str(tie_id.direction))
        contents.append("  Originator: " + utils.system_id_str(tie_id.originator))
        contents.append("  TIE Type: " + packet_common.tietype_str(tie_id.tietype))
        contents.append("  TIE Nr: " + str(tie_id.tie_nr))

    def command_show_route_prefix(self, cli_session, parameters):
        prefix = self.get_prefix_param(cli_session, parameters)
        if prefix is None:
            return
        if prefix.ipv4prefix is not None:
            af_rib = self._ipv4_rib
        else:
            af_rib = self._ipv6_rib
        at_least_one = False
        tab = table.Table()
        tab.add_row(rib_route.RibRoute.cli_summary_headers())
        for rte in af_rib.all_prefix_routes(prefix):
            at_least_one = True
            tab.add_row(rte.cli_summary_attributes())
        if at_least_one:
            cli_session.print(tab.to_string())
        else:
            cli_session.print("Prefix {} not present".format(prefix))

    def command_show_route_prefix_owner(self, cli_session, parameters):
        prefix = self.get_prefix_param(cli_session, parameters)
        if prefix is None:
            return
        owner = self.get_owner_param(cli_session, parameters)
        if owner is None:
            return
        if prefix.ipv4prefix is not None:
            af_rib = self._ipv4_rib
        else:
            af_rib = self._ipv6_rib
        rte = af_rib.get_route(prefix, owner)
        if rte is None:
            cli_session.print("Prefix {} owner {} not present".
                              format(prefix, constants.owner_str(owner)))
        else:
            tab = table.Table()
            tab.add_row(rib_route.RibRoute.cli_summary_headers())
            tab.add_row(rte.cli_summary_attributes())
            cli_session.print(tab.to_string())

    def command_show_routes(self, cli_session):
        self.command_show_routes_af(cli_session, constants.ADDRESS_FAMILY_IPV4)
        self.command_show_routes_af(cli_session, constants.ADDRESS_FAMILY_IPV6)

    def command_show_routes_family(self, cli_session, parameters):
        family = parameters["family"].lower()
        if family == "ipv4":
            self.command_show_routes_af(cli_session, constants.ADDRESS_FAMILY_IPV4)
        elif family == "ipv6":
            self.command_show_routes_af(cli_session, constants.ADDRESS_FAMILY_IPV6)
        else:
            cli_session.print("Error: unknown family {} (valid values are: ipv4, ipv6)"
                              .format(family))

    def command_show_routes_af(self, cli_session, address_family):
        cli_session.print(constants.address_family_str(address_family) + " Routes:")
        if address_family == constants.ADDRESS_FAMILY_IPV4:
            tab = self._ipv4_rib.cli_table()
        else:
            assert address_family == constants.ADDRESS_FAMILY_IPV6
            tab = self._ipv6_rib.cli_table()
        cli_session.print(tab.to_string())

    def command_show_forwarding_prefix(self, cli_session, parameters):
        prefix = self.get_prefix_param(cli_session, parameters)
        if prefix is None:
            return
        if prefix.ipv4prefix is not None:
            af_fib = self._ipv4_fib
        else:
            af_fib = self._ipv6_fib
        rte = af_fib.get_route(prefix)
        if rte is None:
            cli_session.print("Prefix {} not present".format(prefix))
            return
        tab = table.Table()
        tab.add_row(rib_route.RibRoute.cli_summary_headers())
        tab.add_row(rte.cli_summary_attributes())
        cli_session.print(tab.to_string())

    def command_show_forwarding(self, cli_session):
        self.command_show_forwarding_af(cli_session, constants.ADDRESS_FAMILY_IPV4)
        self.command_show_forwarding_af(cli_session, constants.ADDRESS_FAMILY_IPV6)

    def command_show_forwarding_family(self, cli_session, parameters):
        family = parameters["family"].lower()
        if family == "ipv4":
            self.command_show_forwarding_af(cli_session, constants.ADDRESS_FAMILY_IPV4)
        elif family == "ipv6":
            self.command_show_forwarding_af(cli_session, constants.ADDRESS_FAMILY_IPV6)
        else:
            cli_session.print("Error: unknown family {} (valid values are: ipv4, ipv6)"
                              .format(family))

    def command_show_forwarding_af(self, cli_session, address_family):
        cli_session.print(constants.address_family_str(address_family) + " Routes:")
        if address_family == constants.ADDRESS_FAMILY_IPV4:
            tab = self._ipv4_fib.cli_table()
        else:
            assert address_family == constants.ADDRESS_FAMILY_IPV6
            tab = self._ipv6_fib.cli_table()
        cli_session.print(tab.to_string())

    def command_show_disaggregation(self, cli_session):
        # Same Level Nodes
        cli_session.print("Same Level Nodes:")
        tab = self.same_level_nodes_table()
        cli_session.print(tab.to_string())
        # Partially Connected Interfaces
        cli_session.print("Partially Connected Interfaces:")
        tab = table.Table()
        tab.add_row(["Name", "Nodes Causing Partial Connectivity"])
        for intf in self.interfaces_by_name.values():
            if intf.partially_connected:
                tab.add_row([intf.name, intf.partially_connected_causes_str()])
        cli_session.print(tab.to_string())
        # Positive disaggregation TIEs
        cli_session.print("Positive Disaggregation TIEs:")
        tab = self.tie_db_table(
            filter_tie_type=common.ttypes.TIETypeType.PositiveDisaggregationPrefixTIEType,
            return_none_if_empty=False)
        cli_session.print(tab.to_string())
        # Negative disaggregation TIEs
        cli_session.print("Negative Disaggregation TIEs:")
        tab = self.tie_db_table(
            filter_tie_type=common.ttypes.TIETypeType.NegativeDisaggregationPrefixTIEType,
            return_none_if_empty=False)
        cli_session.print(tab.to_string())

    def command_show_security(self, cli_session):
        cli_session.print("Security Keys:")
        tab = self.security_keys_table()
        cli_session.print(tab.to_string())
        cli_session.print("Origin Keys:")
        tab = self.node_origin_keys_table()
        cli_session.print(tab.to_string())
        cli_session.print("Security Statistics:")
        tab = self.intf_security_stats_group.table(exclude_zero=False)
        cli_session.print(tab.to_string())

    def command_show_spf(self, cli_session):
        cli_session.print("SPF Statistics:")
        tab = self.spf_statistics_table()
        cli_session.print(tab.to_string())
        self.command_show_spf_destinations(cli_session, constants.DIR_SOUTH)
        self.command_show_spf_destinations(cli_session, constants.DIR_NORTH)
        self.command_show_spf_destinations(cli_session, constants.DIR_SOUTH,
                                           special_for_neg_disagg=True)

    @staticmethod
    def get_direction_param(cli_session, parameters):
        assert "direction" in parameters
        direction_str = parameters["direction"]
        if direction_str.lower() == "south":
            return constants.DIR_SOUTH
        if direction_str.lower() == "north":
            return constants.DIR_NORTH
        cli_session.print('Invalid direction "{}" (valid values: "south", "north")'
                          .format(direction_str))
        return None

    @staticmethod
    def get_spf_direction_param(cli_session, parameters):
        assert "direction" in parameters
        direction_str = parameters["direction"]
        if direction_str.lower() == "south":
            return constants.DIR_SOUTH, False
        if direction_str.lower() == "north":
            return constants.DIR_NORTH, False
        if direction_str.lower() == "south-with-ew":
            return constants.DIR_SOUTH, True
        cli_session.print(
            'Invalid direction "{}" (valid values: "south", "north", "south-with-ew")'.format(
                direction_str))
        return None, None

    @staticmethod
    def get_tie_type_param(cli_session, parameters):
        assert "tie-type" in parameters
        tie_type_str = parameters["tie-type"].lower()
        if tie_type_str == "node":
            return common.ttypes.TIETypeType.NodeTIEType
        if tie_type_str == "prefix":
            return common.ttypes.TIETypeType.PrefixTIEType
        if tie_type_str == "pos-dis-prefix":
            return common.ttypes.TIETypeType.PositiveDisaggregationPrefixTIEType
        if tie_type_str == "neg-dis-prefix":
            return common.ttypes.TIETypeType.NegativeDisaggregationPrefixTIEType
        if tie_type_str == "ext-prefix":
            return common.ttypes.TIETypeType.ExternalPrefixTIEType
        if tie_type_str == "pg-prefix":
            return common.ttypes.TIETypeType.PGPrefixTIEType
        if tie_type_str == "key-value":
            return common.ttypes.TIETypeType.KeyValueTIEType
        cli_session.print(
            'Invalid tie-type "{}" (valid values: "node", "prefix", "pos-dis-prefix", '
            '"neg-dis-prefix", "ext-prefix", "pg-prefix", "key-value")'.format(tie_type_str))
        return None

    @staticmethod
    def get_destination_param(cli_session, parameters):
        assert "destination" in parameters
        destination_str = parameters["destination"]
        # Is it a system-id (integer)?
        try:
            destination = int(destination_str)
        except ValueError:
            pass
        else:
            return destination
        # Is it an IPv4 prefix?
        try:
            destination = packet_common.make_ipv4_prefix(destination_str)
        except ValueError:
            pass
        else:
            return destination
        # Is it an IPv6 prefix?
        try:
            destination = packet_common.make_ipv6_prefix(destination_str)
        except ValueError:
            pass
        else:
            return destination
        # None of the above
        cli_session.print('Invalid destination "{}" (valid values: system-id, ipv4-prefix, '
                          'ipv6-prefix)'.format(destination_str))
        return None

    @staticmethod
    def get_prefix_param(cli_session, parameters):
        assert "prefix" in parameters
        prefix_str = parameters["prefix"]
        # Is it an IPv4 prefix?
        try:
            prefix = packet_common.make_ipv4_prefix(prefix_str)
        except ValueError:
            pass
        else:
            return prefix
        # Is it an IPv6 prefix?
        try:
            prefix = packet_common.make_ipv6_prefix(prefix_str)
        except ValueError:
            pass
        else:
            return prefix
        # None of the above
        cli_session.print('Invalid prefix "{}" (valid values: ipv4-prefix, ipv6-prefix)'
                          .format(prefix_str))
        return None

    @staticmethod
    def get_owner_param(cli_session, parameters):
        assert "owner" in parameters
        direction_str = parameters["owner"]
        if direction_str.lower() == "south-spf":
            return constants.OWNER_S_SPF
        if direction_str.lower() == "north-spf":
            return constants.OWNER_N_SPF
        cli_session.print('Invalid owner "{}" (valid values: "south-spf", "north-spf")'
                          .format(direction_str))
        return None

    @staticmethod
    def get_table_param(cli_session, parameters):
        # No matter how the table is specified (name or number), this always returns a table number
        assert "table" in parameters
        table_str = parameters["table"].lower()
        if table_str == "local":
            return 255
        elif table_str == "main":
            return 254
        elif table_str == "default":
            return 253
        elif table_str == "unspecified":
            return 0
        else:
            try:
                return int(table_str)
            except ValueError:
                cli_session.print('Invalid table "{}" (valid values: "local", "main", '
                                  '"default", "unspecified", or number)'.format(table_str))
                return None

    @staticmethod
    def get_int64u_param(cli_session, parameters, param_name):
        assert param_name in parameters
        value_str = parameters[param_name]
        try:
            return int(value_str)
        except ValueError:
            cli_session.print('Invalid {} "{}" (valid values: 0..18446744073709551615)'
                              .format(param_name, value_str))
            return None

    def command_show_spf_dir(self, cli_session, parameters):
        (direction, special_for_neg_disagg) = self.get_spf_direction_param(cli_session, parameters)
        if direction is None:
            return
        self.command_show_spf_destinations(cli_session, direction, special_for_neg_disagg)

    def command_show_spf_dir_dest(self, cli_session, parameters):
        (direction, special_for_neg_disagg) = self.get_spf_direction_param(cli_session, parameters)
        if direction is None:
            return
        destination = self.get_destination_param(cli_session, parameters)
        if destination is None:
            return
        dest_table = self._spf_destinations[(direction, special_for_neg_disagg)]
        if destination in dest_table:
            tab = table.Table()
            tab.add_row(spf_dest.SPFDest.cli_summary_headers())
            tab.add_row(dest_table[destination].cli_summary_attributes())
            cli_session.print(tab.to_string())
        else:
            cli_session.print("Destination {} not present".format(destination))

    def command_show_spf_destinations(self, cli_session, direction, special_for_neg_disagg=False):
        if not special_for_neg_disagg:
            cli_session.print(constants.direction_str(direction) + " SPF Destinations:")
        else:
            cli_session.print("South SPF (with East-West Links) Destinations:")
        tab = self.spf_tree_table(direction, special_for_neg_disagg)
        cli_session.print(tab.to_string())

    def command_show_tie_db(self, cli_session):
        tab = self.tie_db_table()
        if tab is None:
            cli_session.print("TIE database is empty")
            return
        cli_session.print(tab.to_string())

    def command_show_tie_db_dir(self, cli_session, parameters):
        direction = self.get_direction_param(cli_session, parameters)
        if direction is None:
            return
        tab = self.tie_db_table(filter_direction=direction)
        if tab is None:
            cli_session.print("No TIE with direction {} in database"
                              .format(parameters["direction"]))
            return
        cli_session.print(tab.to_string())

    def command_show_tie_db_dir_orig(self, cli_session, parameters):
        direction = self.get_direction_param(cli_session, parameters)
        if direction is None:
            return
        originator = self.get_int64u_param(cli_session, parameters, "originator")
        if originator is None:
            return
        tab = self.tie_db_table(filter_direction=direction, filter_originator=originator)
        if tab is None:
            cli_session.print("No TIE with direction {} and originator {} in database"
                              .format(parameters["direction"], parameters["originator"]))
            return
        cli_session.print(tab.to_string())

    def command_show_tie_db_dir_orig_type(self, cli_session, parameters):
        # pylint:disable=invalid-name
        direction = self.get_direction_param(cli_session, parameters)
        if direction is None:
            return
        originator = self.get_int64u_param(cli_session, parameters, "originator")
        if originator is None:
            return
        tie_type = self.get_tie_type_param(cli_session, parameters)
        if tie_type is None:
            return
        tab = self.tie_db_table(filter_direction=direction, filter_originator=originator,
                                filter_tie_type=tie_type)
        if tab is None:
            cli_session.print("No TIE with direction {} and originator {} and tie-type {} "
                              "in database".format(parameters["direction"],
                                                   parameters["originator"],
                                                   parameters["tie-type"]))
            return
        cli_session.print(tab.to_string())

    def command_set_interface_failure(self, cli_session, parameters):
        interface_name = parameters['interface']
        if not interface_name in self.interfaces_by_name:
            cli_session.print("Error: interface {} not present".format(interface_name))
            return
        failure = parameters['failure'].lower()
        if failure not in ["ok", "rx-failed", "tx-failed", "failed"]:
            cli_session.print("Error: unknown failure {} (valid values are: "
                              "ok, failed, rx-failed, tx-failed)".format(failure))
            return
        tx_fail = failure in ["failed", "tx-failed"]
        rx_fail = failure in ["failed", "rx-failed"]
        self.interfaces_by_name[interface_name].set_failure(tx_fail, rx_fail)

    def debug(self, msg, *args):
        self.log.debug("[%s] %s" % (self.log_id, msg), *args)

    def info(self, msg, *args):
        self.log.info("[%s] %s" % (self.log_id, msg), *args)

    def db_debug(self, msg, *args):
        if self._tie_db_log is not None:
            self._tie_db_log.debug("[%s] %s" % (self.log_id, msg), *args)

    def spf_debug(self, msg, *args):
        if self._spf_log is not None:
            self._spf_log.debug("[%s] %s" % (self.log_id, msg), *args)

    def floodred_debug(self, msg, *args):
        if self._floodred_log is not None:
            self._floodred_log.debug("[%s] %s" % (self.log_id, msg), *args)

    def floodred_info(self, msg, *args):
        if self._floodred_log is not None:
            self._floodred_log.info("[%s] %s" % (self.log_id, msg), *args)

    def floodred_warning(self, msg, *args):
        if self._floodred_log is not None:
            self._floodred_log.warning("[%s] %s" % (self.log_id, msg), *args)

    def ties_differ_enough_for_spf(self, old_tie_info, new_tie_info):
        old_tie = old_tie_info.protocol_packet.content.tie
        new_tie = new_tie_info.protocol_packet.content.tie
        # Only TIEs with the same TIEID should be compared
        assert old_tie.header.tieid == new_tie.header.tieid
        # Any change in seq_nr triggers an SPF
        if old_tie.header.seq_nr != new_tie.header.seq_nr:
            return True
        # All remaining_lifetime values are the same, except zero, for the purpose of running SPF
        if old_tie_info.remaining_tie_lifetime == 0 and new_tie_info.remaining_tie_lifetime != 0:
            return True
        if old_tie_info.remaining_tie_lifetime != 0 and new_tie_info.remaining_tie_lifetime == 0:
            return True
        # Ignore any changes in origination_lifetime for the purpose of running SPF (TODO: really?)
        # Any change in the element contents (node, prefixes, etc.) trigger an SPF
        if old_tie.element != new_tie.element:
            return True
        # If we get here, nothing of relevance to SPF changed
        return False

    def update_partially_conn_all_intfs(self):
        for intf in self.interfaces_by_name.values():
            intf.update_partially_connected()

    def store_tie_packet_info(self, tie_packet_info):
        tie_packet = tie_packet_info.protocol_packet.content.tie
        tie_id = tie_packet.header.tieid
        tie_type = tie_id.tietype
        reason = ""
        if tie_id in self.tie_packet_infos:
            old_tie_packet_info = self.tie_packet_infos[tie_id]
            trigger_spf = self.ties_differ_enough_for_spf(old_tie_packet_info, tie_packet_info)
            if trigger_spf:
                reason = "TIE " + packet_common.tie_id_str(tie_id) + " changed"
        else:
            trigger_spf = True
            reason = "TIE " + packet_common.tie_id_str(tie_id) + " added"
        self.tie_packet_infos[tie_id] = tie_packet_info
        if self.is_same_level_tie(tie_packet):
            self.peer_node_tie_packet_infos[tie_packet.header.tieid] = tie_packet_info
            self.update_partially_conn_all_intfs()
            self.regenerate_my_south_prefix_tie()
        if tie_type == common.ttypes.TIETypeType.NegativeDisaggregationPrefixTIEType:
            if self.level_value() != common.constants.leaf_level:
                if tie_id.originator in self._parent_neighbors and \
                        self.level_value() < self._parent_neighbors[tie_id.originator].level:
                    trigger_spf = True
                    reason = "TIE " + packet_common.tie_id_str(tie_id) + " added negative"
                    self.update_neg_disagg_propagation(tie_packet)
        if trigger_spf:
            self.trigger_spf(reason)

    def update_neg_disagg_propagation(self, neg_tie):
        neg_disagg_type = common.ttypes.TIETypeType.NegativeDisaggregationPrefixTIEType
        current_neg_disagg_prefixes = {}
        rx_prefixes = neg_tie.element.negative_disaggregation_prefixes.prefixes
        if rx_prefixes is None:
            rx_prefixes = {}
        for prefix, attrs in rx_prefixes.items():
            must_propagate = True
            for neighbor_system_id in self._parent_neighbors.keys():
                # Get neighbor negative disaggregation ties
                nbr_neg_ties = self.ties_of_type(constants.DIR_SOUTH, neighbor_system_id,
                                                 neg_disagg_type)
                # If neighbor ties list is empty, prefix is not present. So nothing to propagate
                if not nbr_neg_ties:
                    must_propagate = False
                    break
                # Check if negative ties of current neighbor contain the prefix
                for tie in nbr_neg_ties:
                    if prefix not in tie.element.negative_disaggregation_prefixes.prefixes:
                        must_propagate = False
                        break
            # If the prefix is contained in all neighbors negative ties, store it in the
            # current prefixes to propagate
            if must_propagate:
                current_neg_disagg_prefixes[prefix] = attrs
            else:
                break
        # Associate each prefix to a spf destination at infinite distance
        fallen_leafs = {prefix: spf_dest.make_prefix_dest(prefix, attrs.tags,
                                                          cost=common.constants.infinite_distance,
                                                          is_leaf=True,
                                                          is_pos_disagg=False,
                                                          is_neg_disagg=True)
                        for prefix, attrs in current_neg_disagg_prefixes.items()}
        # Regenerate the tie for the fallen leafs
        self.regenerate_my_neg_disagg_tie(fallen_leafs)

    def remove_tie(self, tie_id):
        # It is not an error to attempt to delete a TIE which is not in the database
        if tie_id in self.tie_packet_infos:
            del self.tie_packet_infos[tie_id]
            reason = "TIE " + packet_common.tie_id_str(tie_id) + " removed"
            self.trigger_spf(reason)
        if tie_id in self.peer_node_tie_packet_infos:
            del self.peer_node_tie_packet_infos[tie_id]
            self.update_partially_conn_all_intfs()
            self.regenerate_my_south_prefix_tie()

    def find_tie_packet_info(self, tie_id):
        # Returns None if tie_id is not in database
        return self.tie_packet_infos.get(tie_id)

    def start_sending_db_ties_in_range(self, start_sending_tie_headers, start_id, start_incl,
                                       end_id, end_incl):
        db_tie_ids = self.tie_packet_infos.irange(start_id, end_id, (start_incl, end_incl))
        for db_tie_id in db_tie_ids:
            db_tie_packet_info = self.tie_packet_infos[db_tie_id]
            db_tie_packet = db_tie_packet_info.protocol_packet.content.tie
            # TODO: Make sure that lifetime is decreased by at least one before propagating
            # TODO: Maybe do that when TIE is received and stored in tie-db?
            start_sending_tie_headers.append(db_tie_packet.header)

    def process_rx_tide_packet(self, tide_packet):
        request_tie_headers_lifetime = []
        start_sending_tie_headers = []
        stop_sending_tie_headers = []
        # It is assumed TIDEs are sent and received in increasing order or range. If we observe
        # a gap between the end of the range of the last TIDE (if any) and the start of the range
        # of this TIDE, then we must start sending all TIEs in our database that fall in that gap.
        if tide_packet.start_range < self._last_received_tide_end:
            # The neighbor has wrapped around: it has sent its last TIDE and is not sending the
            # first TIDE again (look for comment "wrap-around" in test_tie_db.py for an example)
            # Note - I am not completely happy with this rule since it may lead to unnecessarily
            # putting TIEs on the send queue if TIDEs are received out of order.
            self._last_received_tide_end = self.MIN_TIE_ID
        if tide_packet.start_range > self._last_received_tide_end:
            # There is a gap between the end of the previous TIDE and the start of this TIDE
            self.start_sending_db_ties_in_range(start_sending_tie_headers,
                                                self._last_received_tide_end, True,
                                                tide_packet.start_range, False)
        self._last_received_tide_end = tide_packet.end_range
        # The first gap that we need to consider starts at start_range (inclusive)
        last_processed_tie_id = tide_packet.start_range
        minimum_inclusive = True
        # Process the TIDE
        for header_lifetime_in_tide in tide_packet.headers:
            header_in_tide = header_lifetime_in_tide.header
            # Make sure all tie_ids in the TIDE in the range advertised by the TIDE
            if header_in_tide.tieid < last_processed_tie_id:
                # TODO: Handle error (not sorted)
                assert False
            # Start/mid-gap processing: send TIEs that are in our TIE DB but missing in TIDE
            self.start_sending_db_ties_in_range(start_sending_tie_headers,
                                                last_processed_tie_id, minimum_inclusive,
                                                header_in_tide.tieid, False)
            last_processed_tie_id = header_in_tide.tieid
            minimum_inclusive = False
            # Process all tie_ids in the TIDE
            db_tie_packet_info = self.find_tie_packet_info(header_in_tide.tieid)
            if db_tie_packet_info is None:
                if header_in_tide.tieid.originator == self.system_id:
                    # Self-originate an empty TIE with a higher sequence number.
                    bumped_own_tie_header = self.bump_own_tie(None, header_in_tide)
                    start_sending_tie_headers.append(bumped_own_tie_header)
                else:
                    # We don't have the TIE, request it
                    # To request a a missing TIE, we have to set the seq_nr to 0. This is not
                    # mentioned in the RIFT draft, but it is described in ISIS ISO/IEC 10589:1992
                    # section 7.3.15.2 bullet b.4
                    request_header = header_lifetime_in_tide
                    request_header.header.seq_nr = 0
                    request_header.header.origination_time = None
                    request_header.remaining_lifetime = 0
                    request_tie_headers_lifetime.append(request_header)
            else:
                db_tie_packet = db_tie_packet_info.protocol_packet.content.tie
                db_tie_header = db_tie_packet.header
                db_tie_header_lifetime = packet_common.expand_tie_header_with_lifetime(
                    db_tie_header,
                    db_tie_packet_info.remaining_tie_lifetime)
                comparison = compare_tie_header_lifetime_age(db_tie_header_lifetime,
                                                             header_lifetime_in_tide)
                if comparison < 0:
                    if header_in_tide.tieid.originator == self.system_id:
                        # Re-originate DB TIE with higher sequence number than the one in TIDE
                        bumped_own_tie_header = self.bump_own_tie(db_tie_packet_info,
                                                                  header_in_tide)
                        start_sending_tie_headers.append(bumped_own_tie_header)
                    else:
                        # We have an older version of the TIE, request the newer version
                        request_tie_headers_lifetime.append(header_lifetime_in_tide)
                elif comparison > 0:
                    # We have a newer version of the TIE, send it
                    start_sending_tie_headers.append(db_tie_packet.header)
                else:
                    # We have the same version of the TIE, if we are trying to send it, stop it
                    stop_sending_tie_headers.append(db_tie_packet.header)
        # End-gap processing: send TIEs that are in our TIE DB but missing in TIDE
        self.start_sending_db_ties_in_range(start_sending_tie_headers,
                                            last_processed_tie_id, minimum_inclusive,
                                            tide_packet.end_range, True)
        return (request_tie_headers_lifetime, start_sending_tie_headers, stop_sending_tie_headers)

    def process_rx_tire_packet(self, tire_packet):
        request_tie_headers_lifetime = []
        start_sending_tie_headers = []
        acked_tie_headers = []
        for header_lifetime_in_tire in tire_packet.headers:
            db_tie_packet_info = self.find_tie_packet_info(header_lifetime_in_tire.header.tieid)
            if db_tie_packet_info is not None:
                db_tie_packet = db_tie_packet_info.protocol_packet.content.tie
                db_tie_header = db_tie_packet.header
                db_tie_header_lifetime = packet_common.expand_tie_header_with_lifetime(
                    db_tie_header,
                    db_tie_packet_info.remaining_tie_lifetime)
                comparison = compare_tie_header_lifetime_age(db_tie_header_lifetime,
                                                             header_lifetime_in_tire)
                if comparison < 0:
                    # We have an older version of the TIE, request the newer version
                    request_tie_headers_lifetime.append(header_lifetime_in_tire)
                elif comparison > 0:
                    # We have a newer version of the TIE, send it
                    start_sending_tie_headers.append(db_tie_packet.header)
                else:
                    # We have the same version of the TIE, treat it as an ACK
                    acked_tie_headers.append(db_tie_packet.header)
        return (request_tie_headers_lifetime, start_sending_tie_headers, acked_tie_headers)

    def find_according_node_tie(self, rx_tie_header):
        # We have to originate an empty node TIE for the purpose of flushing it. Use the same
        # contents as the real node TIE that we actually originated, except don't report any
        # neighbors.
        real_node_tie_id = copy.deepcopy(rx_tie_header.tieid)
        real_node_tie_id.tie_nr = MY_NODE_TIE_NR
        real_node_tie_packet_info = self.find_tie_packet_info(real_node_tie_id)
        assert real_node_tie_packet_info is not None
        return real_node_tie_packet_info

    def make_according_empty_tie(self, rx_tie_header):
        new_tie_header = packet_common.make_tie_header(
            rx_tie_header.tieid.direction,
            rx_tie_header.tieid.originator,
            rx_tie_header.tieid.tietype,
            rx_tie_header.tieid.tie_nr,
            rx_tie_header.seq_nr + 1,  # Higher sequence number
        )
        tietype = rx_tie_header.tieid.tietype
        if tietype == common.ttypes.TIETypeType.NodeTIEType:
            real_node_tie_packet_info = self.find_according_node_tie(rx_tie_header)
            real_node_tie_packet = real_node_tie_packet_info.protocol_packet.content.tie
            new_element = copy.deepcopy(real_node_tie_packet.element)
            new_element.node.neighbors = {}
        elif tietype == common.ttypes.TIETypeType.PrefixTIEType:
            empty_prefixes = encoding.ttypes.PrefixTIEElement()
            new_element = encoding.ttypes.TIEElement(prefixes=empty_prefixes)
        elif tietype == common.ttypes.TIETypeType.PositiveDisaggregationPrefixTIEType:
            empty_prefixes = encoding.ttypes.PrefixTIEElement()
            new_element = encoding.ttypes.TIEElement(
                positive_disaggregation_prefixes=empty_prefixes)
        elif tietype == common.ttypes.TIETypeType.NegativeDisaggregationPrefixTIEType:
            empty_prefixes = encoding.ttypes.PrefixTIEElement()
            new_element = encoding.ttypes.TIEElement(
                negative_disaggregation_prefixes=empty_prefixes)
        elif tietype == common.ttypes.TIETypeType.PGPrefixTIEType:
            # TODO: Policy guided prefixes are not yet in model in specification
            assert False
        elif tietype == common.ttypes.TIETypeType.KeyValueTIEType:
            empty_keyvalues = encoding.ttypes.KeyValueTIEElement()
            new_element = encoding.ttypes.TIEElement(keyvalues=empty_keyvalues)
            # TODO: External
        else:
            assert False
        according_empty_tie = encoding.ttypes.TIEPacket(
            header=new_tie_header,
            element=new_element)
        header = encoding.ttypes.PacketHeader(sender=self.system_id, level=self.level_value())
        content = encoding.ttypes.PacketContent(tie=according_empty_tie)
        protocol_packet = encoding.ttypes.ProtocolPacket(header=header, content=content)
        packet_info = packet_common.encode_protocol_packet(protocol_packet, self.active_origin_key)
        packet_info.remaining_tie_lifetime = common.constants.default_lifetime
        return packet_info

    def bump_own_tie(self, db_tie_packet_info, rx_tie_header):
        if db_tie_packet_info is None:
            # We received a TIE (rx_tie) which appears to be self-originated, but we don't have that
            # TIE in our database. Re-originate the "according" (same TIE ID) TIE, but then empty
            # (i.e. no neighbor, no prefixes, no key-values, etc.), with a higher sequence number,
            # and a short remaining life time
            db_tie_packet_info = self.make_according_empty_tie(rx_tie_header)
        else:
            # Re-originate DB TIE with higher sequence number than the one in RX TIE
            db_tie_packet = db_tie_packet_info.protocol_packet.content.tie
            db_tie_packet.header.seq_nr = rx_tie_header.seq_nr + 1
        self.store_tie_packet_info(db_tie_packet_info)
        return db_tie_packet_info.protocol_packet.content.tie.header

    def process_rx_tie_packet_info(self, rx_tie_packet_info):
        start_sending_tie_header = None
        ack_tie_header = None
        rx_tie_packet = rx_tie_packet_info.protocol_packet.content.tie
        rx_tie_header = rx_tie_packet.header
        rx_tie_id = rx_tie_header.tieid
        db_tie_packet_info = self.find_tie_packet_info(rx_tie_id)
        if db_tie_packet_info is None:
            if rx_tie_id.originator == self.system_id:
                # Self-originate an empty TIE with a higher sequence number.
                start_sending_tie_header = self.bump_own_tie(None, rx_tie_packet.header)
            else:
                # We don't have this TIE in the database, store and ack it
                self.store_tie_packet_info(rx_tie_packet_info)
                ack_tie_header = rx_tie_header
        else:
            db_tie_packet = db_tie_packet_info.protocol_packet.content.tie
            ###@@@
            print("... rx_tie:")
            print("    db_tie_header = {}".format(db_tie_packet.header))
            print("    rx_tie_header = {}".format(rx_tie_header))
            ###@@@
            db_tie_lifetime = packet_common.expand_tie_header_with_lifetime(
                db_tie_packet.header,
                db_tie_packet_info.remaining_tie_lifetime)
            rx_tie_lifetime = packet_common.expand_tie_header_with_lifetime(
                rx_tie_header,
                rx_tie_packet_info.remaining_tie_lifetime)
            comparison = compare_tie_header_lifetime_age(db_tie_lifetime, rx_tie_lifetime)
            if comparison < 0:
                print("    db_tie is older") ###@@@
                # We have an older version of the TIE, ...
                if rx_tie_id.originator == self.system_id:
                    # Re-originate DB TIE with higher sequence number than the one in RX TIE
                    start_sending_tie_header = self.bump_own_tie(db_tie_packet_info,
                                                                 rx_tie_packet.header)
                else:
                    # We did not originate the TIE, store the newer version and ack it
                    self.store_tie_packet_info(rx_tie_packet_info)
                    ack_tie_header = rx_tie_packet.header
                    # Flood the TIE
                    self.unsol_flood_tie_packet_info(rx_tie_packet_info)
            elif comparison > 0:
                print("    db_tie is newer") ###@@@
                # We have a newer version of the TIE, send it
                start_sending_tie_header = db_tie_packet.header
            else:
                print("   db_tie is same age") ###@@@
                # We have the same version of the TIE, ACK it
                ack_tie_header = db_tie_packet.header
        return (start_sending_tie_header, ack_tie_header)

    def tie_is_originated_by_node(self, tie_header, node_system_id):
        return tie_header.tieid.originator == node_system_id

    def tie_originator_level(self, tie_header):
        # We cannot determine the level of the originator just by looking at the TIE header; we have
        # to look in the TIE-DB to determine it. We can be confident the TIE is in the TIE-DB
        # because we wouldn't be here, considering sending a TIE to a neighbor, if we did not have
        # the TIE in the TIE-DB. Also, this question can only be asked about Node TIEs (other TIEs
        # don't store the level of the originator in the TIEPacket)
        assert tie_header.tieid.tietype == common.ttypes.TIETypeType.NodeTIEType
        db_tie_packet_info = self.find_tie_packet_info(tie_header.tieid)
        if db_tie_packet_info is None:
            # Just in case it unexpectedly not in the TIE-DB
            return None
        else:
            db_tie_packet = db_tie_packet_info.protocol_packet.content.tie
            return db_tie_packet.element.node.level

    def is_flood_allowed(self,
                         tie_header,
                         to_node_direction,
                         to_node_system_id,
                         from_node_system_id,
                         from_node_level,
                         from_node_is_top_of_fabric):
        # Note: there is exactly one rule below (the one marked with [*]) which actually depend on
        # the neighbor_system_id. If that rule wasn't there we would have been able to encode a TIDE
        # only one per direction (N, S, EW) instead of once per neighbor, and still follow all the
        # flooding scope rules. We have chosen to follow the rules strictly (not doing so causes all
        # sorts of other complications), so -alas- we swallow the performance overhead of encoding
        # separate TIDE packets for every individual neighbor. TODO: I may revisit this decision
        # when the exact nature of the "other complications" (namely persistent oscillations) are
        # better understood (correctness first, performance later).
        # See https://www.dropbox.com/s/b07dnhbxawaizpi/zoom_0.mp4?dl=0 for a video recording of a
        # discussion where these complications were discussed in detail.
        if tie_header.tieid.direction == constants.DIR_SOUTH:
            # S-TIE
            if tie_header.tieid.tietype == common.ttypes.TIETypeType.NodeTIEType:
                # Node S-TIE
                if to_node_direction == constants.DIR_SOUTH:
                    # Node S-TIE to S: Flood if level of originator is same as level of this node
                    if self.tie_originator_level(tie_header) == from_node_level:
                        return (True, "Node S-TIE to S: originator level is same as from-node")
                    else:
                        return (False, "Node S-TIE to S: originator level is not same as from-node")
                elif to_node_direction == constants.DIR_NORTH:
                    # Node S-TIE to N: flood if level of originator is higher than level of this
                    # node
                    originator_level = self.tie_originator_level(tie_header)
                    if originator_level is None:
                        return (False, "Node S-TIE to N: could not determine originator level")
                    elif originator_level > from_node_level:
                        return (True, "Node S-TIE to N: originator level is higher than from-node")
                    else:
                        return (False,
                                "Node S-TIE to N: originator level is not higher than from-node")
                elif to_node_direction == constants.DIR_EAST_WEST:
                    # Node S-TIE to EW: Flood only if this node is not top of fabric
                    if from_node_is_top_of_fabric:
                        return (False, "Node S-TIE to EW: from-node is top of fabric")
                    else:
                        return (True, "Node S-TIE to EW: from-node is not top of fabric")
                else:
                    # Node S-TIE to ?: We can't determine the direction of the neighbor; don't flood
                    assert to_node_direction is None
                    return (False, "Node S-TIE to ?: never flood")
            else:
                # Non-Node S-TIE
                if to_node_direction == constants.DIR_SOUTH:
                    # Non-Node S-TIE to S: Flood self-originated only
                    if self.tie_is_originated_by_node(tie_header, from_node_system_id):
                        return (True, "Non-node S-TIE to S: self-originated")
                    else:
                        return (False, "Non-node S-TIE to S: not self-originated")
                elif to_node_direction == constants.DIR_NORTH:
                    # [*] Non-Node S-TIE to N: Flood only if the neighbor is the originator of
                    # the TIE
                    if to_node_system_id == tie_header.tieid.originator:
                        return (True, "Non-node S-TIE to N: to-node is originator of TIE")
                    else:
                        return (False, "Non-node S-TIE to N: to-node is not originator of TIE")
                elif to_node_direction == constants.DIR_EAST_WEST:
                    # Non-Node S-TIE to EW: Flood only if if self-originated and this node is not
                    # ToF
                    if from_node_is_top_of_fabric:
                        return (False, "Non-node S-TIE to EW: this top of fabric")
                    elif self.tie_is_originated_by_node(tie_header, from_node_system_id):
                        return (True, "Non-node S-TIE to EW: self-originated and not top of fabric")
                    else:
                        return (False, "Non-node S-TIE to EW: not self-originated")
                else:
                    # We cannot determine the direction of the neighbor; don't flood
                    assert to_node_direction is None
                    return (False, "None-node S-TIE to ?: never flood")
        else:
            # S-TIE
            assert tie_header.tieid.direction == constants.DIR_NORTH
            if to_node_direction == constants.DIR_SOUTH:
                # S-TIE to S: Never flood
                return (False, "N-TIE to S: never flood")
            elif to_node_direction == constants.DIR_NORTH:
                # S-TIE to N: Always flood
                return (True, "N-TIE to N: always flood")
            elif to_node_direction == constants.DIR_EAST_WEST:
                # S-TIE to EW: Flood only if this node is top of fabric
                if from_node_is_top_of_fabric:
                    return (True, "N-TIE to EW: top of fabric")
                else:
                    return (False, "N-TIE to EW: not top of fabric")
            else:
                # S-TIE to ?: We cannot determine the direction of the neighbor; don't flood
                assert to_node_direction is None
                return (False, "N-TIE to ?: never flood")

    def flood_allowed_from_node_to_nbr(self,
                                       tie_header,
                                       neighbor_direction,
                                       neighbor_system_id,
                                       node_system_id,
                                       node_level,
                                       node_is_top_of_fabric):
        return self.is_flood_allowed(
            tie_header=tie_header,
            to_node_direction=neighbor_direction,
            to_node_system_id=neighbor_system_id,
            from_node_system_id=node_system_id,
            from_node_level=node_level,
            from_node_is_top_of_fabric=node_is_top_of_fabric)

    def flood_allowed_from_nbr_to_node(self,
                                       tie_header,
                                       neighbor_direction,
                                       neighbor_system_id,
                                       neighbor_level,
                                       neighbor_is_top_of_fabric,
                                       node_system_id):
        if neighbor_direction == constants.DIR_SOUTH:
            neighbor_reverse_direction = constants.DIR_NORTH
        elif neighbor_direction == constants.DIR_NORTH:
            neighbor_reverse_direction = constants.DIR_SOUTH
        else:
            neighbor_reverse_direction = neighbor_direction
        return self.is_flood_allowed(
            tie_header=tie_header,
            to_node_direction=neighbor_reverse_direction,
            to_node_system_id=node_system_id,
            from_node_system_id=neighbor_system_id,
            from_node_level=neighbor_level,
            from_node_is_top_of_fabric=neighbor_is_top_of_fabric)

    def unsol_flood_tie_packet_info(self, tie_packet_info):
        self_originated = tie_packet_info.rx_intf is None
        flood_count = 0
        tie_packet = tie_packet_info.protocol_packet.content.tie
        for tx_intf in self.interfaces_by_name.values():
            # Never flood back to interface on which TIE was received (split horizon)
            if tx_intf == tie_packet_info.rx_intf:
                continue
            # Only flood to adjacencies that are in state 3-way
            if tx_intf.fsm.state != tx_intf.State.THREE_WAY:
                continue
            # In some race conditions when the interface is in the process of going down, the
            # neighbor can already be gone, but the state is still saying THREE_WAY. Skip those too.
            if tx_intf.neighbor is None:
                continue
            # If flooding reduction is enabled, only flood to flood repeaters
            if self.floodred_enabled:
                if not tx_intf.floodred_nbr_is_fr:
                    continue
            # Only flood if allowed by flooding scope rules
            (allowed, _reason) = self.flood_allowed_from_node_to_nbr(
                tie_header=tie_packet.header,
                neighbor_direction=tx_intf.neighbor_direction(),
                neighbor_system_id=tx_intf.neighbor.system_id,
                node_system_id=self.system_id,
                node_level=self.level_value(),
                node_is_top_of_fabric=self.top_of_fabric())
            if not allowed:
                continue
            # Put the packet on the transmit queue.
            flood_count += 1
            tx_intf.tx_tie(tie_packet.header)
        # Log to how many interfaces the TIE was flooded
        if flood_count > 0:
            if self_originated:
                self.db_debug("Self-originated TIE %s flooded to %d interfaces", tie_packet.header,
                              flood_count)
            else:
                self.db_debug("TIE %s received on %s flooded to %d interfaces", tie_packet.header,
                              tie_packet_info.rx_intf.name, flood_count)

    def generate_tide_packet(self,
                             neighbor_direction,
                             neighbor_system_id,
                             neighbor_level,
                             neighbor_is_top_of_fabric,
                             my_level,
                             i_am_top_of_fabric):
        # The algorithm for deciding which TIE headers go into a TIDE packet are based on what is
        # described as "the solution to oscillation #1" in slide deck
        # http://bit.ly/rift-flooding-oscillations-v1. During the RIFT core team conference call on
        # 19 Oct 2018, Tony reported that the RIFT specification was already updated with the same
        # rules, but IMHO sections Table 3 / B.3.1. / B.3.2.1 in the draft are still ambiguous and
        # I am not sure if they specify the same behavior.
        #
        # We generate a single TIDE packet which covers the entire range and we report all TIE
        # headers in that single TIDE packet. We simple assume that it will fit in a single UDP
        # packet which can be up to 64K. And if a single TIE gets added or removed we swallow the
        # cost of regenerating and resending the entire TIDE packet.
        tide_packet = packet_common.make_tide_packet(
            start_range=self.MIN_TIE_ID,
            end_range=self.MAX_TIE_ID)
        # Look at every TIE in our database, and decide whether or not we want to include it in the
        # TIDE packet. This is a rather expensive process, which is why we want to minimize the
        # the number of times this function is run.
        for tie_packet_info in self.tie_packet_infos.values():
            tie_packet = tie_packet_info.protocol_packet.content.tie
            tie_header = tie_packet.header
            # The first possible reason for including a TIE header in the TIDE is to announce that
            # we have a TIE that we want to send to the neighbor. In other words the TIE in the
            # flooding scope from us to the neighbor.
            (allowed, reason1) = self.flood_allowed_from_node_to_nbr(
                tie_header=tie_header,
                neighbor_direction=neighbor_direction,
                neighbor_system_id=neighbor_system_id,
                node_system_id=self.system_id,
                node_level=my_level,
                node_is_top_of_fabric=i_am_top_of_fabric)
            if allowed:
                self.db_debug("Include TIE %s in TIDE because %s (perspective us to neighbor)",
                              tie_header, reason1)
                packet_common.add_tie_header_to_tide(
                    tide_packet,
                    packet_common.expand_tie_header_with_lifetime(
                        tie_header,
                        tie_packet_info.remaining_tie_lifetime))
                continue
            # The second possible reason for including a TIE header in the TIDE is because the
            # neighbor might be considering to send the TIE to us, and we want to let the neighbor
            # know that we already have the TIE and what version it it.
            (allowed, reason2) = self.flood_allowed_from_nbr_to_node(
                tie_header=tie_header,
                neighbor_direction=neighbor_direction,
                neighbor_system_id=neighbor_system_id,
                neighbor_level=neighbor_level,
                neighbor_is_top_of_fabric=neighbor_is_top_of_fabric,
                node_system_id=self.system_id)
            if allowed:
                self.db_debug("Include TIE %s in TIDE because %s (perspective neighbor to us)",
                              tie_header, reason2)
                packet_common.add_tie_header_to_tide(
                    tide_packet,
                    packet_common.expand_tie_header_with_lifetime(
                        tie_header,
                        tie_packet_info.remaining_tie_lifetime))
                continue
            # If we get here, we decided not to include the TIE header in the TIDE
            self.db_debug("Exclude TIE %s from TIDE because %s (perspective us to neighbor) and "
                          "%s (perspective neighbor to us)", tie_header, reason1, reason2)
        return tide_packet

    def check_sysid_partially_connected(self, look_for_sysid):
        # Check every other node and the same level, and if there is at least one other node that
        # that does not have the sysid as a south-bound adjacencies, then declare the sysid as
        # partially connected. Note: if there are no other nodes at the same level, then the sysid
        # is not partially connected.
        node_adj_with_look_for_sysid = {}  # Indexed by sysid of other node at same level
        for node_tie_packet_info in self.peer_node_tie_packet_infos.values():
            node_tie_packet = node_tie_packet_info.protocol_packet.content.tie
            node_sysid = node_tie_packet.header.tieid.originator
            node_level = node_tie_packet.element.node.level
            if node_sysid not in node_adj_with_look_for_sysid:
                node_adj_with_look_for_sysid[node_sysid] = False
            for nbr_sysid, nbr_info in node_tie_packet.element.node.neighbors.items():
                nbr_level = nbr_info.level
                if nbr_level < node_level and nbr_sysid == look_for_sysid:
                    node_adj_with_look_for_sysid[node_sysid] = True
        partially_connected = False
        partially_connected_causes = []
        for node_sysid, adjacent in node_adj_with_look_for_sysid.items():
            if not adjacent:
                partially_connected = True
                partially_connected_causes.append(node_sysid)
        partially_connected_causes = sorted(list(set(partially_connected_causes)))
        return (partially_connected, partially_connected_causes)

    def node_descr(self, sysid):
        # This is an expensive function, only intended to make show commands more readable
        # by reporting the name of a node in addition to its system id (if the name is known)
        node_name = None
        ties = self.node_ties(constants.DIR_SOUTH, sysid)
        if ties:
            node_name = ties[0].element.node.name
        else:
            ties = self.node_ties(constants.DIR_NORTH, sysid)
            if ties:
                node_name = ties[0].element.node.name
        if node_name:
            return node_name + " (" + str(sysid) + ")"
        return "(" + str(sysid) + ")"

    def same_level_nodes_table(self):
        tab = table.Table()
        tab.add_row([
            ["Same-Level", "Node"],
            ["North-bound", "Adjacencies"],
            ["South-bound", "Adjacencies"],
            ["Missing", "South-bound", "Adjacencies"],
            ["Extra", "South-bound", "Adjacencies"]])
        # If there are no other nodes at my level; return empty table.
        if not self.peer_node_tie_packet_infos:
            return tab
        # Collect all north- and south-bound adjacencies of nodes at the same level
        nodes = {}
        for node_tie_packet_info in self.peer_node_tie_packet_infos.values():
            node_tie_packet = node_tie_packet_info.protocol_packet.content.tie
            node_sysid = node_tie_packet.header.tieid.originator
            node_level = node_tie_packet.element.node.level
            if node_sysid not in nodes:
                nodes[node_sysid] = ([], [])
            for nbr_sysid, nbr_info in node_tie_packet.element.node.neighbors.items():
                nbr_level = nbr_info.level
                if nbr_level > node_level:
                    nodes[node_sysid][0].append(nbr_sysid)  # Add north-bound adjacency
                elif nbr_level < node_level:
                    nodes[node_sysid][1].append(nbr_sysid)  # Add south-bound adjacency
        # Determine the south-bound adjacencies of this node
        my_south_adjacencies = []
        for intf in self.interfaces_by_name.values():
            if intf.fsm.state != intf.State.THREE_WAY:
                continue
            if intf.neighbor_direction() != constants.DIR_SOUTH:
                continue
            my_south_adjacencies.append(intf.neighbor.system_id)
        # Format collected information into table
        sorted_node_sysids = sorted(list(nodes.keys()))
        for node_sysid in sorted_node_sysids:
            (node_north_adjacencies, node_south_adjacencies) = nodes[node_sysid]
            # Sort adjacencies and remove duplicates
            node_north_adjacencies = sorted(node_north_adjacencies)
            node_south_adjacencies = sorted(node_south_adjacencies)
            # Determine missing adjacencies
            missing_adjacencies = set(my_south_adjacencies) - set(node_south_adjacencies)
            missing_adjacencies = sorted(list(missing_adjacencies))
            # Determine missing adjacencies
            extra_adjacencies = set(node_south_adjacencies) - set(my_south_adjacencies)
            extra_adjacencies = sorted(list(extra_adjacencies))
            # Convert system ids into descriptions
            node_north_adjacencies = list(map(self.node_descr, node_north_adjacencies))
            node_south_adjacencies = list(map(self.node_descr, node_south_adjacencies))
            missing_adjacencies = list(map(self.node_descr, missing_adjacencies))
            extra_adjacencies = list(map(self.node_descr, extra_adjacencies))
            # Add row to table
            tab.add_row([self.node_descr(node_sysid),
                         node_north_adjacencies,
                         node_south_adjacencies,
                         missing_adjacencies,
                         extra_adjacencies])
        return tab

    def security_keys_table(self):
        tab = table.Table()
        tab.add_row(["Key ID", "Algorithm", "Secret"])
        for configured_key in self.engine.keys.values():
            tab.add_row([
                configured_key.key_id,
                configured_key.algorithm,
                configured_key.secret])
        return tab

    @staticmethod
    def key_str(key):
        if key is None:
            return "None"
        else:
            return key.key_id

    @staticmethod
    def keys_str(keys):
        if keys is None:
            return "None"
        else:
            return ", ".join([str(key.key_id) for key in keys])

    def node_origin_keys_table(self):
        tab = table.Table()
        tab.add_row(["Key", "Key ID(s)"])
        tab.add_row(["Active Origin Key", self.key_str(self.active_origin_key)])
        tab.add_row(["Accept Origin Keys", self.keys_str(self.accept_origin_keys)])
        return tab

    def auth_errors_table(self):
        tab = table.Table()
        tab.add_row([
            "Interface",
            ["Authentication", "Errors"],
            ["Error", "Count"],
            ["Error", "Rate"],
            ["Last Change"]
        ])
        for intf in self.interfaces_by_name.values():
            for counter in intf.auth_error_counters():
                if not counter.is_zero():
                    tab.add_row([
                        intf.name,
                        counter.description(),
                        counter.value_display_str(),
                        counter.rate_display_str(),
                        counter.last_change_display_str()
                    ])
        return tab

    def spf_statistics_table(self):
        tab = table.Table()
        tab.add_rows(self.cli_statistics_attributes())
        return tab

    @staticmethod
    def compare_spf_dest_key(dest_key):
        if isinstance(dest_key, int):
            return (0, dest_key)
        else:
            return (1, dest_key)

    def spf_tree_table(self, direction, special_for_neg_disagg):
        tab = table.Table()
        tab.add_row(spf_dest.SPFDest.cli_summary_headers())
        sorted_spf_destinations = sorted(
            self._spf_destinations[(direction, special_for_neg_disagg)].values())
        for destination in sorted_spf_destinations:
            tab.add_row(destination.cli_summary_attributes())
        return tab

    def tie_db_table(self, filter_direction=None, filter_originator=None, filter_tie_type=None,
                     return_none_if_empty=True):
        tab = table.Table()
        found_something = False
        tab.add_row(self.cli_tie_db_summary_headers())
        for tie_packet_info in self.tie_packet_infos.values():
            tie_packet = tie_packet_info.protocol_packet.content.tie
            tie_id = tie_packet.header.tieid
            if filter_direction and tie_id.direction != filter_direction:
                continue
            if filter_originator and tie_id.originator != filter_originator:
                continue
            if filter_tie_type and tie_id.tietype != filter_tie_type:
                continue
            found_something = True
            tab.add_row(self.cli_tie_db_summary_attributes(tie_packet,
                                                           tie_packet_info.remaining_tie_lifetime))
        if not found_something and return_none_if_empty:
            return None
        return tab

    def age_ties(self):
        expired_key_ids = []
        for tie_id, tie_packet_info in self.tie_packet_infos.items():
            tie_packet_info.remaining_tie_lifetime -= 1
            if tie_packet_info.remaining_tie_lifetime <= 0:
                expired_key_ids.append(tie_id)
        for key_id in expired_key_ids:
            # TODO: log a message
            self.remove_tie(key_id)

    @staticmethod
    def cli_tie_db_summary_headers():
        return [
            "Direction",
            "Originator",
            "Type",
            "TIE Nr",
            "Seq Nr",
            "Lifetime",
            "Contents"]

    def cli_tie_db_summary_attributes(self, tie_packet, lifetime):
        tie_id = tie_packet.header.tieid
        return [
            packet_common.direction_str(tie_id.direction),
            tie_id.originator,
            packet_common.tietype_str(tie_id.tietype),
            tie_id.tie_nr,
            tie_packet.header.seq_nr,
            lifetime,
            packet_common.element_str(tie_id.tietype, tie_packet.element)
        ]

    def trigger_spf(self, reason):
        self._spf_triggers_count += 1
        self._spf_trigger_history.appendleft(reason)
        if self._defer_spf_timer is None:
            self.start_defer_spf_timer()
            self._spf_deferred_trigger_pending = False
            self.spf_debug("Trigger and run SPF: %s", reason)
            self.spf_run()
        else:
            self._spf_deferred_trigger_pending = True
            self._spf_triggers_deferred_count += 1
            self.spf_debug("Trigger and defer SPF: %s", reason)

    def start_defer_spf_timer(self):
        self._defer_spf_timer = timer.Timer(
            interval=self.MIN_SPF_INTERVAL,
            expire_function=self.defer_spf_timer_expired,
            periodic=False,
            start=True)

    def defer_spf_timer_expired(self):
        self._defer_spf_timer = None
        if self._spf_deferred_trigger_pending:
            self.start_defer_spf_timer()
            self._spf_deferred_trigger_pending = False
            self.spf_debug("Run deferred SPF")
            self.spf_run()

    def ties_of_type(self, direction, system_id, prefix_type):
        # Return an ordered list of TIEs from the given node and in the given direction
        # and of the given type
        node_ties = []
        start_tie_id = packet_common.make_tie_id(direction, system_id, prefix_type, 0)
        end_tie_id = packet_common.make_tie_id(direction, system_id, prefix_type,
                                               packet_common.MAX_U32)
        node_tie_ids = self.tie_packet_infos.irange(start_tie_id, end_tie_id, (True, True))
        for node_tie_id in node_tie_ids:
            node_tie_packet_info = self.tie_packet_infos[node_tie_id]
            node_tie_packet = node_tie_packet_info.protocol_packet.content.tie
            node_ties.append(node_tie_packet)
        return node_ties

    def node_ties(self, direction, system_id):
        # Return an ordered list of all node TIEs from the given node and in the given direction
        return self.ties_of_type(direction, system_id, common.ttypes.TIETypeType.NodeTIEType)

    def node_neighbors(self, node_ties, neighbor_directions):
        # A generator that yields (nbr_system_id, nbr_level, nbr_tie_element) tuples for all
        # neighbors in the specified directions of the nodes in the node_ties list.
        for node_tie in node_ties:
            # If a node reports no level but does report neighbors, those neighbors cannot be
            # considered to point in any particular direction.
            node_level = node_tie.element.node.level
            if node_level is None:
                continue
            for nbr_system_id, nbr_tie_element in node_tie.element.node.neighbors.items():
                nbr_level = nbr_tie_element.level
                correct_direction = False
                if constants.DIR_SOUTH in neighbor_directions:
                    correct_direction = (nbr_level < node_level)
                if not correct_direction and constants.DIR_NORTH in neighbor_directions:
                    correct_direction = (nbr_level > node_level)
                if not correct_direction and constants.DIR_EAST_WEST in neighbor_directions:
                    correct_direction = (nbr_level == node_level)
                if correct_direction:
                    yield nbr_system_id, nbr_level, nbr_tie_element

    def spf_run(self):
        self._spf_runs_count += 1
        # TODO: Currently we simply always run both North-SPF and South-SPF, but maybe we can be
        # more intelligent about selectively triggering North-SPF and South-SPF separately.

        # Run normal SPFs (south and north)
        self.spf_run_direction(constants.DIR_SOUTH, special_for_neg_disagg=False)
        self.spf_run_direction(constants.DIR_NORTH, special_for_neg_disagg=False)

        # Run special SPF (southbound) for negative disaggregation only if current node is a ToF
        # and it has at least an E-W link
        if self.top_of_fabric() and self.have_ew_adjacency():
            self.spf_run_direction(constants.DIR_SOUTH, special_for_neg_disagg=True)

        self.floodred_elect_repeaters()
        self.regenerate_my_pos_disagg_tie()

    def spf_run_direction(self, spf_direction, special_for_neg_disagg):
        # Shortest Path First (SPF) uses the Dijkstra algorithm to compute the shortest path to
        # each destination that is reachable from this node.
        # Each destination is represented by an SPFDest object, which represents either a node or a
        # prefix. The attributes of the SPFDest object contain all the information that is needed to
        # run SPF, such the best-known path cost thus far, the predecessor nodes, etc. See module
        # spf_dest for details. Each SPFDest object also has a key which unique identifies it. For
        # node destinations this is the system-id, and for prefix destinations it is the IP prefix.
        # The attribute _spf_destinations contains ALL known destinations. It is a dictionary
        # indexed by direction (south and north) and a boolean which indicates if the SPF is a
        # special run for negative disaggregation. Each value in the dictionary (i.e.
        # _spf_destinations[direction, False]) is itself a dictionary again: the values are SPFDest
        # SPFDest objects and the index is the key of the SPFDest object (a system-id or prefix).
        # It contains both destinations for which the best path has not yet definitely been
        # determined (so-called candidates) and also destinations for which the best path has
        # already been definitely been determined. In the latter case the best attribute of the
        # SPFDest object is set to True. This dictionary is kept around after the SPF run is
        # completed, and there is a "show spf" CLI command to view it for debugging purposes.

        # Ensure that special SPF is called southbound!
        if special_for_neg_disagg:
            assert spf_direction == constants.DIR_SOUTH

        # Tuple index is used to save both normal SPFs and special SPF
        spf_direction_index = (spf_direction, special_for_neg_disagg)

        self._spf_destinations[spf_direction_index] = {}
        dest_table = self._spf_destinations[spf_direction_index]

        # Initially, there is only one known destination, namely this node.
        self_destination = spf_dest.make_node_dest(self.system_id, self.name, 0, self.is_leaf())
        dest_table[self.system_id] = self_destination

        # The variable "candidates" contains the set of destinations (nodes and prefixes) for which
        # we have already determined some feasible path (which may be an ECMP path) but for which
        # we have not yet established that the known path is indeed the best path.
        # For efficiency, candidates is implemented as a priority queue that contains the
        # destination keys with the best known path cost thus far as the priority.
        # We use module heapdict (as opposed to the more widely used heapq module) because we need
        # an efficient way to decrease the priority of an element which is already on the priority
        # queue. Heapq only allows you to do this by calling the internal method _siftdown (see
        # http://bit.ly/siftdown)
        candidates = heapdict.heapdict()
        # Initially, there is one destination in the candidates heap, namely the starting node (i.e.
        # this node) with cost zero.
        candidates[self.system_id] = 0
        # Keep going until we have no more candidates
        while candidates:
            # Remove the destination with the lowest cost from the candidate priority queue.
            (dest_key, dest_cost) = candidates.popitem()

            # If already have a best path to the destination move on to the next candidate. In this
            # case the best path should have a strictly lower cost than the candidate's cost.
            destination = dest_table[dest_key]
            if destination.best:
                assert dest_cost > destination.cost
                continue
            # Mark that we now have the best path to the destination.
            destination.best = True

            # If the destination is a node (i.e. its key is a system-id number rather than an IP
            # prefix), potentially add its neighbor nodes and its prefixes as a new candidate or
            # as a new ECMP path for an existing candidate.
            if isinstance(dest_key, int):
                self.spf_add_candidates_from_node(dest_key, dest_cost, destination.is_leaf,
                                                  candidates, spf_direction, special_for_neg_disagg)

        # For south-bound SPF runs only (not for negative disaggregation special run),
        # decide which prefixes need to be positively disaggregated
        if spf_direction == constants.DIR_SOUTH and not special_for_neg_disagg:
            self.spf_mark_pos_disagg_prefixes()

        # SPF run is done.
        if not special_for_neg_disagg:
            # Install the computed routes into the route table (RIB) if run is normal
            self.spf_install_routes_in_rib(spf_direction)
        else:
            # Handle any fallen leaf if present
            self.update_neg_disagg_fallen_leafs()

    def spf_add_candidates_from_node(self, node_system_id, node_cost, node_is_leaf, candidates,
                                     spf_direction, special_for_neg_disagg):
        node_ties = self.node_ties(self.spf_use_tie_direction(node_system_id, spf_direction),
                                   node_system_id)

        if not node_ties:
            return

        # Update the name of the node (we take it from the first node TIE)
        dest_table = self._spf_destinations[(spf_direction, special_for_neg_disagg)]
        dest_table[node_system_id].name = node_ties[0].element.node.name

        # Add the neighbors of this node as candidates,
        # if special_for_neg_disagg = True also consider E-W links
        self.spf_add_neighbor_candidates(node_system_id, node_cost, node_ties, candidates,
                                         spf_direction, special_for_neg_disagg)

        # Add the prefixes of this node as candidates
        self.spf_add_prefixes(node_system_id, node_cost, node_is_leaf, candidates, spf_direction,
                              special_for_neg_disagg)
        self.spf_add_pos_disagg_prefixes(node_system_id, node_cost, node_is_leaf, candidates,
                                         spf_direction, special_for_neg_disagg)
        self.spf_add_neg_disagg_prefixes(node_system_id, node_cost, node_is_leaf, candidates,
                                         spf_direction, special_for_neg_disagg)

    def spf_add_neighbor_candidates(self, node_system_id, node_cost, node_ties, candidates,
                                    spf_direction, special_for_neg_disagg):
        # For a given node, it visits each neighbor in the SPF direction, and either adds that
        # neighbor to the candidate heap for the SPF run, or if the neighbor is already on the
        # candidate heap, it (potentially) updates the cost and predecessors of the neighbor.
        #
        # Consider each neighbor of the visited node in the direction of the SPF
        directions = [spf_direction]
        if special_for_neg_disagg:
            # If runnin ag special SPF for negative disaggregation, also allow east-west links.
            directions.append(constants.DIR_EAST_WEST)
        neighbors = self.node_neighbors(node_ties, neighbor_directions=directions)
        for nbr_system_id, nbr_level, nbr_tie_element in neighbors:
            # Only consider bi-directional adjacencies.
            if self.is_neighbor_bidirectional(node_system_id, nbr_system_id, nbr_tie_element,
                                              spf_direction, special_for_neg_disagg):
                # We have found a feasible path to the neighbor node; is the best path?
                cost = min(node_cost + nbr_tie_element.cost, common.constants.infinite_distance)
                is_leaf = nbr_level == common.constants.leaf_level
                destination = spf_dest.make_node_dest(nbr_system_id, None, cost, is_leaf)
                self.spf_consider_candidate_dest(destination, nbr_tie_element, node_system_id,
                                                 candidates, spf_direction, special_for_neg_disagg)

    def spf_add_prefixes(self, node_sysid, node_cost, node_is_leaf, candidates, spf_direction,
                         special_for_neg_disagg):
        prefix_ties = self.ties_of_type(
            direction=self.spf_use_tie_direction(node_sysid, spf_direction),
            system_id=node_sysid,
            prefix_type=common.ttypes.TIETypeType.PrefixTIEType)
        for prefix_tie in prefix_ties:
            self.spf_add_prefixes_common(node_sysid, node_cost, node_is_leaf, candidates,
                                         spf_direction, special_for_neg_disagg,
                                         prefix_tie.element.prefixes.prefixes,
                                         is_pos_disagg=False, is_neg_disagg=False)

    def spf_add_pos_disagg_prefixes(self, node_sysid, node_cost, node_is_leaf, candidates,
                                    spf_direction, special_for_neg_disagg):
        prefix_ties = self.ties_of_type(
            direction=self.spf_use_tie_direction(node_sysid, spf_direction),
            system_id=node_sysid,
            prefix_type=common.ttypes.TIETypeType.PositiveDisaggregationPrefixTIEType)
        for prefix_tie in prefix_ties:
            pos_disagg_prefixes = prefix_tie.element.positive_disaggregation_prefixes.prefixes
            self.spf_add_prefixes_common(node_sysid, node_cost, node_is_leaf, candidates,
                                         spf_direction, special_for_neg_disagg,
                                         pos_disagg_prefixes,
                                         is_pos_disagg=True, is_neg_disagg=False)

    def spf_add_neg_disagg_prefixes(self, node_sysid, node_cost, node_is_leaf, candidates,
                                    spf_direction, special_for_neg_disagg):
        prefix_ties = self.ties_of_type(
            direction=self.spf_use_tie_direction(node_sysid, spf_direction),
            system_id=node_sysid,
            prefix_type=common.ttypes.TIETypeType.NegativeDisaggregationPrefixTIEType)
        for prefix_tie in prefix_ties:
            neg_disagg_prefixes = prefix_tie.element.negative_disaggregation_prefixes.prefixes
            self.spf_add_prefixes_common(node_sysid, node_cost, node_is_leaf, candidates,
                                         spf_direction, special_for_neg_disagg,
                                         neg_disagg_prefixes,
                                         is_pos_disagg=False, is_neg_disagg=True)

    def spf_add_prefixes_common(self, node_sysid, node_cost, node_is_leaf, candidates,
                                spf_direction, special_for_neg_disagg, prefixes, is_pos_disagg,
                                is_neg_disagg):
        if not prefixes:
            return
        for prefix, attributes in prefixes.items():
            tags = attributes.tags
            cost = min(node_cost + attributes.metric, common.constants.infinite_distance)
            dest = spf_dest.make_prefix_dest(prefix, tags, cost, node_is_leaf, is_pos_disagg,
                                             is_neg_disagg)
            self.spf_consider_candidate_dest(dest, None, node_sysid, candidates,
                                             spf_direction, special_for_neg_disagg)

    def spf_consider_candidate_dest(self, destination, nbr_tie_element, predecessor_system_id,
                                    candidates, spf_direction, special_for_neg_disagg):
        dest_key = destination.key()
        dest_table = self._spf_destinations[(spf_direction, special_for_neg_disagg)]
        if dest_key not in dest_table:
            # We did not have any previous path to the destination. Add it.
            self.set_spf_predecessor(destination, nbr_tie_element, predecessor_system_id,
                                     spf_direction, special_for_neg_disagg)
            dest_table[dest_key] = destination
            candidates[dest_key] = destination.cost
        else:
            # We already had a previous path to the destination. How does the new path compare to
            # the existing path in terms of cost?
            old_destination = dest_table[dest_key]
            if destination.cost < old_destination.cost:
                # The new path is strictly better than the existing path. Replace the existing path
                # with the new path.
                self.set_spf_predecessor(destination, nbr_tie_element, predecessor_system_id,
                                         spf_direction, special_for_neg_disagg)
                dest_table[dest_key] = destination
                candidates[dest_key] = destination.cost
            elif destination.cost == old_destination.cost:
                # The new path is equal cost to the existing path. Add an ECMP path to the existing
                # path.
                self.add_spf_predecessor(old_destination, predecessor_system_id,
                                         spf_direction, special_for_neg_disagg)
                old_destination.inherit_tags(destination)

    def set_spf_predecessor(self, destination, nbr_tie_element, predecessor_system_id,
                            spf_direction, special_for_neg_disagg):
        destination.add_predecessor(predecessor_system_id)
        if (nbr_tie_element is not None) and (predecessor_system_id == self.system_id):
            for link_id_pair in nbr_tie_element.link_ids:
                nhop = self.interface_id_to_ipv4_next_hop(link_id_pair.local_id)
                if nhop:
                    destination.add_ipv4_next_hop(nhop)
                nhop = self.interface_id_to_ipv6_next_hop(link_id_pair.local_id)
                if nhop:
                    destination.add_ipv6_next_hop(nhop)
        else:
            dest_table = self._spf_destinations[(spf_direction, special_for_neg_disagg)]
            destination.inherit_next_hops(dest_table[predecessor_system_id])

    def add_spf_predecessor(self, destination, predecessor_system_id, spf_direction,
                            special_for_neg_disagg):
        destination.add_predecessor(predecessor_system_id)
        dest_table = self._spf_destinations[(spf_direction, special_for_neg_disagg)]
        destination.inherit_next_hops(dest_table[predecessor_system_id])

    def spf_mark_pos_disagg_prefixes(self):
        # Mark the prefixes in the SPF table for which this router wants to do positive aggregation
        # (not to be confused with prefixes in this SPF tables which were received because some
        # north-bound router did positive disaggregation)
        for dest in self._spf_destinations[(constants.DIR_SOUTH, False)].values():
            if dest.dest_type != spf_dest.DEST_TYPE_PREFIX:
                continue
            if dest.prefix.ipv4prefix:
                nexthops = dest.ipv4_next_hops
            else:
                assert dest.prefix.ipv6prefix
                nexthops = dest.ipv6_next_hops
            all_nexthops_partial = True
            at_least_one_nexthop = False
            for nexthop in nexthops:
                at_least_one_nexthop = True
                intf = self.interfaces_by_name[nexthop.interface]
                if not intf.partially_connected:
                    all_nexthops_partial = False
            if all_nexthops_partial and at_least_one_nexthop:
                dest.positively_disaggregate = True

    def interface_id_to_ipv4_next_hop(self, interface_id):
        if interface_id not in self.interfaces_by_id:
            return None
        intf = self.interfaces_by_id[interface_id]
        if intf.neighbor is None:
            return None
        if intf.neighbor.ipv4_address is None:
            return None
        remote_address = packet_common.make_ip_address(intf.neighbor.ipv4_address)
        return next_hop.NextHop(intf.name, remote_address)

    def interface_id_to_ipv6_next_hop(self, interface_id):
        if interface_id not in self.interfaces_by_id:
            return None
        intf = self.interfaces_by_id[interface_id]
        if intf.neighbor is None:
            return None
        if intf.neighbor.ipv6_address is None:
            return None
        remote_address_str = intf.neighbor.ipv6_address
        if "%" in remote_address_str:
            remote_address_str = remote_address_str.split("%")[0]
        remote_address = packet_common.make_ip_address(remote_address_str)
        return next_hop.NextHop(intf.name, remote_address)

    def spf_use_tie_direction(self, visit_system_id, spf_direction):
        if spf_direction == constants.DIR_SOUTH:
            # , we always want to use the North-Node-TIEs to look for
            # neighbors and North-Prefix-TIEs to look for prefixes.
            return constants.DIR_NORTH
        elif visit_system_id != self.system_id:
            # When running a North SPF, we normally want to use the South-Node-TIEs to look for
            # neighbors and South-Prefix-TIEs to look for prefixes...
            return constants.DIR_SOUTH
        else:
            # ... except that for self-originated TIEs, we always want to use
            # (a) The self-originated North-Node-TIE because leafs may not originate a
            #     South-Node-TIE and
            # (b) The self-origianted North-Prefix-TIE (if any) because we want SPF to not
            #     prefer the self-originated default route over the received default route route.
            return constants.DIR_NORTH

    def is_neighbor_bidirectional(self, visit_system_id, nbr_system_id, nbr_tie_element,
                                  spf_direction, special_for_neg_disagg):
        # Locate the Node-TIE(s) of the neighbor node in the desired direction. If we can't find
        # the neighbor's Node-TIE(s), we declare the adjacency to be not bi-directional.
        reverse_direction = constants.reverse_dir(spf_direction)

        nbr_node_ties = self.node_ties(reverse_direction, nbr_system_id)
        if not nbr_node_ties:
            return False

        # Check for bi-directional connectivity: the neighbor must report the visited node
        # as an adjacency with the same link-id pair (in reverse).
        bidirectional = False

        reverse_directions = [reverse_direction] if not special_for_neg_disagg \
            else [reverse_direction, constants.DIR_EAST_WEST]

        node_neighbors = self.node_neighbors(nbr_node_ties, neighbor_directions=reverse_directions)

        for nbr_nbr_system_id, _nbr_nbr_level, nbr_nbr_tie_element in node_neighbors:
            # Does the neighbor report the visited node as its neighbor?
            if nbr_nbr_system_id != visit_system_id:
                continue

            # Are the link_ids bidirectional?
            if not self.are_link_ids_bidirectional(nbr_tie_element, nbr_nbr_tie_element):
                continue

            # Yes, connectivity is bidirectional
            bidirectional = True
            break

        return bidirectional

    def are_link_ids_bidirectional(self, nbr_tie_element_1, nbr_tie_element_2):
        # Does the set link_ids_1 contain any link-id (local_id, remote_id) which is present in
        # reverse (remote_id, local_id) in set link_ids_2?
        for id1 in nbr_tie_element_1.link_ids:
            for id2 in nbr_tie_element_2.link_ids:
                if (id1.local_id == id2.remote_id) and (id1.remote_id == id2.local_id):
                    return True
        return False

    def spf_install_routes_in_rib(self, spf_direction):
        if spf_direction == constants.DIR_NORTH:
            owner = constants.OWNER_N_SPF
        else:
            owner = constants.OWNER_S_SPF

        self._ipv4_rib.mark_owner_routes_stale(owner)
        self._ipv6_rib.mark_owner_routes_stale(owner)

        # Index is (direction, False) because special SPF does not install any route in RIB
        dest_table = self._spf_destinations[(spf_direction, False)]

        all_next_hops_ipv4 = {}
        all_next_hops_ipv6 = {}

        for dest_key, dest in dest_table.items():
            if isinstance(dest_key, int):
                # Destination is a node, do nothing
                pass
            elif not dest.predecessors:
                # Local node destination, don't install in RIB as result of SPF
                pass
            elif dest.predecessors == [self.system_id]:
                # Local prefix destination, don't install in RIB as result of SPF
                pass
            else:
                prefix = dest_key
                if prefix.ipv4prefix is not None:
                    next_hops = dest.ipv4_next_hops
                    if prefix not in all_next_hops_ipv4:
                        all_next_hops_ipv4[prefix] = {}
                    all_next_hops_ipv4[prefix][dest.dest_type] = next_hops
                else:
                    assert prefix.ipv6prefix is not None
                    next_hops = dest.ipv6_next_hops
                    if prefix not in all_next_hops_ipv6:
                        all_next_hops_ipv6[prefix] = {}
                    all_next_hops_ipv6[prefix][dest.dest_type] = next_hops

        self._install_rib_routes(all_next_hops_ipv4, owner, self._ipv4_rib)
        self._install_rib_routes(all_next_hops_ipv6, owner, self._ipv6_rib)

        self._ipv4_rib.del_stale_routes()
        self._ipv6_rib.del_stale_routes()

    @staticmethod
    def _install_rib_routes(destinations_next_hops, owner, route_family_rib):
        for prefix, next_hops in destinations_next_hops.items():
            positive_next_hops = []
            negative_next_hops = []
            if spf_dest.DEST_TYPE_PREFIX in next_hops:
                positive_next_hops.extend(next_hops[spf_dest.DEST_TYPE_PREFIX])
            if spf_dest.DEST_TYPE_POS_DISAGG_PREFIX in next_hops:
                positive_next_hops.extend(next_hops[spf_dest.DEST_TYPE_POS_DISAGG_PREFIX])
            if spf_dest.DEST_TYPE_NEG_DISAGG_PREFIX in next_hops:
                negative_next_hops = next_hops[spf_dest.DEST_TYPE_NEG_DISAGG_PREFIX]
            rte = rib_route.RibRoute(prefix, owner, positive_next_hops, negative_next_hops)
            route_family_rib.put_route(rte)

    @staticmethod
    def is_leaf_prefix(item):
        (sysid_or_prefix, destination) = item
        if not isinstance(sysid_or_prefix, common.ttypes.IPPrefixType):
            return False
        if not destination.is_leaf:
            return False
        return True

    def update_neg_disagg_fallen_leafs(self):
        normal_southbound_run = self._spf_destinations[(constants.DIR_SOUTH, False)]
        special_southbound_run = self._spf_destinations[(constants.DIR_SOUTH, True)]
        normal_southbound_dests = dict(filter(self.is_leaf_prefix, normal_southbound_run.items()))
        special_southbound_dests = dict(filter(self.is_leaf_prefix, special_southbound_run.items()))
        difference = special_southbound_dests.keys() - normal_southbound_dests.keys()
        fallen_leafs = {prefix: special_southbound_dests[prefix] for prefix in difference}
        for prefix in fallen_leafs.values():
            prefix.negatively_disaggregate = True
        self.regenerate_my_neg_disagg_tie(fallen_leafs)

    def floodred_elect_repeaters(self):
        self.floodred_debug("Re-elect flood repeaters")
        if self.floodred_enabled:
            # Update parents and grandparents
            self.floodred_update_ancestry()
            # Sort and shuffle parents (order by decreasing grandparent count)
            self.floodred_sort_shuffle_parents()
            # Pick flood repeaters to get the required coverage of grandparents
            self.floodred_pick_repeaters()
            # Active newly elected flood repeater interfaces (gracefully, i.e. activating new flood
            # repeaters before de-activating old flood repeaters)
            self.floodrep_update_intfs()
        else:
            # Flooding reduction is disabled. Don't compute parents or grandparents. Tell all
            # north neighbors that they are flood repeaters (i.e. no reduction in flooding)
            self.floodrep_all_intfs_are_fr()

    def floodred_update_ancestry(self):
        # Update the following information about parents and grandparents
        #
        # floodred_parents: A list of FloodRedParent objects (not sorted at this point)
        self.floodred_parents = self.floodred_gather_parents()
        #
        # floodred_grandparents: A dictionary of FloodRedGrandparent objects, indexed by sysid
        self.floodred_grandparents = {}
        for parent in self.floodred_parents:
            grandparent_sysids = self.floodred_gather_grandparents(parent)
            for grandparent_sysid in grandparent_sysids:
                if grandparent_sysid in self.floodred_grandparents:
                    grandparent = self.floodred_grandparents[grandparent_sysid]
                else:
                    grandparent = FloodRedGrandparent(self, grandparent_sysid)
                    self.floodred_grandparents[grandparent_sysid] = grandparent
                parent.add_grandparent(grandparent)  # Grandparent of this node, parent of parent
                grandparent.add_parent(parent)  # Parent of this node, child of grandparent

    def floodred_gather_parents(self):
        # Gather list of FloodRedParent objects (not sorted at this time)
        parents = []
        for intf in self.interfaces_by_name.values():
            if (intf.fsm.state == intf.State.THREE_WAY and
                    intf.neighbor_direction() == constants.DIR_NORTH):
                parent = FloodRedParent(self, intf)
                parents.append(parent)
        return parents

    def floodred_gather_grandparents(self, parent):
        # Gather list of sysids of parents of parent, i.e. sysids of grandparents of this node
        grandparent_sysids = []
        parent_node_ties = self.node_ties(constants.DIR_SOUTH, parent.sysid)
        for grandparent_nbr in self.node_neighbors(parent_node_ties,
                                                   neighbor_directions=[constants.DIR_NORTH]):
            (grandparent_sysid, _grandparent_level, _grandparent_tie_element) = grandparent_nbr
            grandparent_sysids.append(grandparent_sysid)
        return grandparent_sysids

    def floodred_sort_shuffle_parents(self):
        # Sort the parents array by decreasing grandparents count
        self.floodred_parents.sort(reverse=True)
        # Shuffle parents that have the same grandparent count. Follow the pseudo-code in the draft
        # verbatim, even though it is not very Pythonic. I do the shuffling in-place, as is hinted
        # to by the "abstract action, maybe noop" comment in the draft (and hence we don't need k)
        parents = self.floodred_parents
        nr_parents = len(parents)
        similarity_group_index = 1  # Corresponds to k=0 in the draft
        i = 0
        while i < nr_parents:
            j = i
            while True:
                if i >= nr_parents:
                    break
                i_nr_grandparents = len(parents[i].grandparents)
                j_nr_grandparents = len(parents[j].grandparents)
                if j_nr_grandparents - i_nr_grandparents > self.floodred_similarity:
                    break
                i += 1
            self.shuffle_parents_slice(j, i, similarity_group_index)
            similarity_group_index += 1

    def shuffle_parents_slice(self, start_inclusive, end_exclusive, similarity_group_index):
        # Shuffle a slice of the parents list, using the modern Durstenfeld variation of the
        # Fisher-Yates algorithm.
        lst = self.floodred_parents
        high_grandparent_count = len(lst[start_inclusive].grandparents)
        low_grandparent_count = len(lst[end_exclusive - 1].grandparents)
        similarity_group = (str(similarity_group_index) + ": " +
                            str(high_grandparent_count) + "-" + str(low_grandparent_count))
        for i in reversed(range(start_inclusive + 1, end_exclusive)):
            random_range = i - start_inclusive
            j = start_inclusive + self.floodred_node_random % random_range
            lst[i], lst[j] = lst[j], lst[i]
            lst[i].similarity_group = similarity_group
        lst[start_inclusive].similarity_group = similarity_group

    def floodred_pick_repeaters(self):
        # Visit each parent (in the shuffled order) and decide whether or not it should be a
        # flood repeater.
        for parent in self.floodred_parents:
            # Make the parent a flood repeater if it connect to at least one grandparent that does
            # not yet have a sufficient number of adjacencies to elected flood repeaters.
            make_flood_repeater = False
            for grandparent in parent.grandparents:
                if grandparent.fr_adjacencies < self.floodred_redundancy:
                    make_flood_repeater = True
                    break
            if make_flood_repeater:
                parent.flood_repeater = True
                for grandparent in parent.grandparents:
                    grandparent.fr_adjacencies += 1
        # Warn about any grandparents that could not be covered with sufficient redundancy
        for grandparent in self.floodred_grandparents.values():
            if grandparent.fr_adjacencies >= self.floodred_redundancy:
                grandparent.covered = True
            else:
                grandparent.covered = False
                self.floodred_info("Grandparent system-id %s not redundantly covered by flooding"
                                   "repeaters", utils.system_id_str(grandparent.sysid))

    def floodrep_update_intfs(self):
        # Do all activations before any de-activations (so that the de-activations can known whether
        # they need to way for any pending activations to be completed)
        for parent in self.floodred_parents:
            if parent.flood_repeater:
                self.floodrep_activate_fr_on_intf(parent.intf)
        for parent in self.floodred_parents:
            if not parent.flood_repeater:
                self.floodrep_deactivate_fr_on_intf(parent.intf)

    def floodrep_all_intfs_are_fr(self):
        for intf in self.interfaces_by_name.values():
            intf.activate_flood_repeater(force=True)

    def floodrep_activate_fr_on_intf(self, intf):
        if intf.activate_flood_repeater():
            pending_str = "(pending)"
        else:
            pending_str = "(immediate)"
        self.floodred_debug("Activate interface %s as flood repeater %s", intf.name, pending_str)

    def floodrep_deactivate_fr_on_intf(self, intf):
        if intf.deactivate_flood_repeater():
            pending_str = "(pending)"
        else:
            pending_str = "(immediate)"
        self.floodred_debug("Deactivate interface %s as flood repeater %s", intf.name, pending_str)


class FloodRedParent:

    def __init__(self, node, intf):
        self.node = node
        self.intf = intf
        self.sysid = intf.neighbor.system_id
        self.name = intf.neighbor.name
        self.grandparents = []  # Grandparents of this node, i.e. parent of parent
        self.similarity_group = None
        self.flood_repeater = False

    def add_grandparent(self, grandparent):
        # Add grandparent of this node, i.e. parent of parent
        self.grandparents.append(grandparent)

    def __lt__(self, other):
        grandparent_count = len(self.grandparents)
        other_grandparent_count = len(other.grandparents)
        if grandparent_count < other_grandparent_count:
            return True
        if grandparent_count > other_grandparent_count:
            return False
        # Need a tie-breaker to make shuffling deterministic (which is needed for unit testing)
        if self.sysid < other.sysid:
            return True
        return False

    @staticmethod
    def cli_summary_headers():
        return [
            ["Interface", "Name"],
            ["Parent", "System ID"],
            ["Parent", "Interface", "Name"],
            ["Grandparent", "Count"],
            ["Similarity", "Group"],
            ["Flood", "Repeater"]
        ]

    def cli_summary_attributes(self):
        return [
            self.intf.name,
            utils.system_id_str(self.sysid),
            self.name,
            len(self.grandparents),
            self.similarity_group,
            self.flood_repeater
        ]


class FloodRedGrandparent:

    def __init__(self, node, sysid):
        self.node = node
        self.sysid = sysid
        self.parents = []  # Parents of this node, i.e. children of grandparent
        self.fr_adjacencies = 0
        self.covered = False

    def add_parent(self, parent):
        # Add parent of this node, i.e. child of grandparent
        # TODO: Don't need this if my e-mail is correct
        self.parents.append(parent)

    @staticmethod
    def cli_summary_headers():
        return [
            ["Grandparent", "System ID"],
            ["Parent", "Count"],
            ["Flood", "Repeater", "Adjacencies"],
            ["Redundantly", "Covered"]
        ]

    def cli_summary_attributes(self):
        return [
            utils.system_id_str(self.sysid),
            len(self.parents),
            self.fr_adjacencies,
            self.covered
        ]
