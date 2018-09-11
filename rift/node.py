import enum
import logging
import os
import socket
import uuid

import sortedcontainers

import common.constants
import constants
import fsm
import interface
import offer
import table
import timer
import utils

# TODO: Command line argument and/or configuration option for CLI port

class Node:

    _next_node_nr = 1

    ZTP_MIN_NUMBER_OF_PEER_FOR_LEVEL = 3

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
            new_compare_needed = (
                (old_offer.system_id != updated_offer.system_id) or
                (old_offer.level != updated_offer.level) or
                (old_offer.not_a_ztp_offer != updated_offer.not_a_ztp_offer) or
                (old_offer.state != updated_offer.state))
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
        if not interface_name in self._rx_offers:
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
        # If there is only one candidate, it automatically wins. If there are no canidates, there
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
                self._fsm.push_event(self.Event.BETTER_HAL)
            else:
                self._fsm.push_event(self.Event.LOST_HAL)
        # Determine if the Highest Adjacency Three-way (HAT) would change based on the current
        # offer. If it would change, push an event, but don't update the HAL yet.
        if best_offer_three_way:
            hat = best_offer_three_way.level
        else:
            hat = None
        if self._highest_adjacency_three_way != hat:
            if hat:
                self._fsm.push_event(self.Event.BETTER_HAT)
            else:
                self._fsm.push_event(self.Event.LOST_HAT)

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
        self._highest_adjacency_three_way = hat
        # Push event COMPUTATION_DONE
        self._fsm.push_event(self.Event.COMPUTATION_DONE)

    def action_level_compute(self):
        self.level_compute()

    def action_store_leaf_flags(self, leaf_flags):
        # TODO: on ChangeLocalLeafIndications in UpdatingClients finishes in ComputeBestOffer:
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
        self._configured_level = configured_level
        self._leaf_only = leaf_only
        self._leaf_2_leaf = leaf_2_leaf
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
            self._fsm.push_event(self.Event.HOLD_DOWN_EXPIRED)

    def action_stop_hold_down_timer(self):
        self._hold_down_timer.stop()

    _state_updating_clients_transitions = {
        Event.CHANGE_LOCAL_CONFIGURED_LEVEL: (State.COMPUTE_BEST_OFFER, [action_store_level]),
        Event.NEIGHBOR_OFFER:                (None, [action_update_or_remove_offer]),
        Event.BETTER_HAL:                    (State.COMPUTE_BEST_OFFER, []),
        Event.BETTER_HAT:                    (State.COMPUTE_BEST_OFFER, []),
        Event.LOST_HAL:                      (State.HOLDING_DOWN, [action_start_timer_on_lost_hal]),
        Event.LOST_HAT:                      (State.COMPUTE_BEST_OFFER, []),
    }

    _state_holding_down_transitions = {
        Event.CHANGE_LOCAL_CONFIGURED_LEVEL: (State.COMPUTE_BEST_OFFER, [action_store_level]),
        Event.NEIGHBOR_OFFER:                (None, [action_update_or_remove_offer]),
        Event.BETTER_HAL:                    (None, []),
        Event.BETTER_HAT:                    (None, []),
        Event.LOST_HAL:                      (None, []),
        Event.LOST_HAT:                      (None, []),
        Event.COMPUTATION_DONE:              (None, []),
        Event.HOLD_DOWN_EXPIRED:             (State.COMPUTE_BEST_OFFER, [action_purge_offers]),
    }

    _state_compute_best_offer_transitions = {
        Event.CHANGE_LOCAL_CONFIGURED_LEVEL: (None, [action_store_level, action_level_compute]),
        Event.NEIGHBOR_OFFER:                (None, [action_update_or_remove_offer]),
        Event.BETTER_HAL:                    (None, [action_level_compute]),
        Event.BETTER_HAT:                    (None, [action_level_compute]),
        Event.LOST_HAL:                      (State.HOLDING_DOWN, [action_start_timer_on_lost_hal]),
        Event.LOST_HAT:                      (None, [action_level_compute]),
        Event.COMPUTATION_DONE:              (State.UPDATING_CLIENTS, []),
    }

    _transitions = {
        State.UPDATING_CLIENTS: _state_updating_clients_transitions,
        State.HOLDING_DOWN: _state_holding_down_transitions,
        State.COMPUTE_BEST_OFFER: _state_compute_best_offer_transitions
    }

    _state_entry_actions = {
        State.UPDATING_CLIENTS:     [action_update_all_lie_fsms],
        State.COMPUTE_BEST_OFFER:   [action_stop_hold_down_timer, action_level_compute]
    }

    fsm_definition = fsm.FsmDefinition(
        state_enum=State,
        event_enum=Event,
        transitions=_transitions,
        state_entry_actions=_state_entry_actions,
        initial_state=State.COMPUTE_BEST_OFFER,
        verbose_events=verbose_events)

    def __init__(self, parent_engine, config, force_passive):
        # TODO: process state_thrift_services_port field in config
        # TODO: process config_thrift_services_port field in config
        # TODO: process v4prefixes field in config
        # TODO: process v6prefixes field in config
        self._engine = parent_engine
        self._config = config
        self._node_nr = Node._next_node_nr
        Node._next_node_nr += 1
        self._name = self.get_config_attribute('name', self.generate_name())
        self._passive = force_passive or self.get_config_attribute('passive', False)
        self._running = self.is_running()
        self._system_id = self.get_config_attribute('systemid', self.generate_system_id())
        self._log_id = self._name
        self._log = logging.getLogger('node')
        # TODO: Make sure formating of log message is deferred everywhere, not just direct calls
        self._log.info("[%s] Create node", self._log_id)
        self._configured_level_symbol = self.get_config_attribute('level', 'undefined')
        parse_result = self.parse_level_symbol(self._configured_level_symbol)
        assert parse_result is not None, "Configuration validation should have caught this"
        (configured_level, leaf_only, leaf_2_leaf, top_of_fabric_flag) = parse_result
        self._configured_level = configured_level
        self._leaf_only = leaf_only
        self._leaf_2_leaf = leaf_2_leaf
        self._top_of_fabric_flag = top_of_fabric_flag
        self._interfaces = sortedcontainers.SortedDict()
        self._rx_lie_ipv4_mcast_address = self.get_config_attribute(
            'rx_lie_mcast_address', constants.DEFAULT_LIE_IPV4_MCAST_ADDRESS)
        self._tx_lie_ipv4_mcast_address = self.get_config_attribute(
            'tx_lie_mcast_address', constants.DEFAULT_LIE_IPV4_MCAST_ADDRESS)
        self._rx_lie_ipv6_mcast_address = self.get_config_attribute(
            'rx_lie_v6_mcast_address', constants.DEFAULT_LIE_IPV6_MCAST_ADDRESS)
        self._tx_lie_ipv6_mcast_address = self.get_config_attribute(
            'tx_lie_v6_mcast_address', constants.DEFAULT_LIE_IPV6_MCAST_ADDRESS)
        self._rx_lie_port = self.get_config_attribute('rx_lie_port', constants.DEFAULT_LIE_PORT)
        self._tx_lie_port = self.get_config_attribute('tx_lie_port', constants.DEFAULT_LIE_PORT)
        # TODO: make lie-send-interval configurable
        self._lie_send_interval_secs = constants.DEFAULT_LIE_SEND_INTERVAL_SECS
        self._rx_tie_port = self.get_config_attribute('rx_tie_port', constants.DEFAULT_TIE_PORT)
        self._derived_level = None
        self._rx_offers = {}
        self._tx_offers = {}
        self._highest_available_level = None
        self._highest_adjacency_three_way = None
        self._fsm_log = self._log.getChild("fsm")
        self._holdtime = 1
        self._next_interface_id = 1
        if 'interfaces' in config:
            for interface_config in self._config['interfaces']:
                self.create_interface(interface_config)
        self._fsm = fsm.Fsm(
            definition=self.fsm_definition,
            action_handler=self,
            log=self._fsm_log,
            log_id=self._log_id)
        self._hold_down_timer = timer.Timer(
            interval=self.DEFAULT_HOLD_DOWN_TIME,
            expire_function=lambda: self._fsm.push_event(self.Event.HOLD_DOWN_EXPIRED),
            periodic=False,
            start=False)
        self._fsm.start()

    def generate_system_id(self):
        mac_address = uuid.getnode()
        pid = os.getpid()
        system_id = (
            ((mac_address & 0xffffffffff) << 24) |
            (pid & 0xffff) << 8 |
            (self._node_nr & 0xff))
        return system_id

    def generate_name(self):
        return socket.gethostname().split('.')[0] + str(self._node_nr)

    @staticmethod
    def parse_level_symbol(level_symbol):
        # Parse the "level symbolic value" which can be:
        # - undefined => This node uses ZTP to determine it's level value
        # - leaf => This node is hard-configured to be a leaf (not using leaf-2-leaf procedures)
        # - leaf-to-leaf => This node is hard-configured to be a leaf (does use leaf-2-leaf
        #   procedures)
        # - superspine => This node is hard-configured to be a superspine (level value 24)
        # - integer value => This node is hard-configured to be the specified level (0 means leaf)
        # This function returns
        #  - None if the level_symbol is invalid (i.e. one of the above)
        #  - (configured_level, leaf_only, leaf_2_leaf, top_of_fabric_flag) is level_symbol is valid
        if level_symbol == 'undefined':
            return (None, False, False, False)
        elif level_symbol == 'leaf':
            return (None, True, False, False)
        elif level_symbol == 'leaf-2-leaf':
            return (None, True, True, False)
        elif level_symbol == 'superspine':
            return (None, False, False, True)
        elif isinstance(level_symbol, int):
            return (level_symbol, level_symbol == 0, False, True)
        else:
            return None

    def level_value(self):
        if self._configured_level is not None:
            return self._configured_level
        elif self._top_of_fabric_flag:
            return common.constants.default_superspine_level
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

    def record_tx_offer(self, tx_offer):
        self._tx_offers[tx_offer.interface_name] = tx_offer

    def send_not_a_ztp_offer_on_intf(self, interface_name):
        # If ZTP is not enabled (typically because the level is hard-configured), our level value
        # is never derived from someone else's offer, so never send a poison reverse to anyone.
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
        # Is "Zero Touch Provisiniong (ZTP)" aka "automatic level derivation" aka "level
        # determination procedure" aka "auto configuration" active? The criteria that determine
        # whether ZTP is enabled are spelled out in the first paragraph of section 4.2.9.4.
        if self._configured_level is not None:
            return False
        elif self._top_of_fabric_flag:
            return False
        elif self._leaf_only:
            return False
        else:
            return True

    def is_running(self):
        if self._engine.active_nodes == constants.ActiveNodes.ONLY_PASSIVE_NODES:
            running = self._passive
        elif self._engine.active_nodes == constants.ActiveNodes.ALL_NODES_EXCEPT_PASSIVE_NODES:
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
        self._interfaces[interface_name] = interface.Interface(self, interface_config)

    def cli_detailed_attributes(self):
        return [
            ["Name", self._name],
            ["Passive", self._passive],
            ["Running", self.is_running()],
            ["System ID", utils.system_id_str(self._system_id)],
            ["Configured Level", self._configured_level_symbol],
            ["Leaf Only", self._leaf_only],
            ["Leaf 2 Leaf", self._leaf_2_leaf],
            ["Top of Fabric Flag", self._top_of_fabric_flag],
            ["Zero Touch Provisioning (ZTP) Enabled", self.zero_touch_provisioning_enabled()],
            ["ZTP FSM State", self._fsm.state.name],
            ["ZTP Hold Down Timer", self._hold_down_timer.remaining_time_str()],
            ["Highest Available Level (HAL)", self._highest_available_level],
            ["Highest Adjacency Three-way (HAT)", self._highest_adjacency_three_way],
            ["Level Value", self.level_value_str()],
            ["Receive LIE IPv4 Multicast Address", self._rx_lie_ipv4_mcast_address],
            ["Transmit LIE IPv4 Multicast Address", self._tx_lie_ipv4_mcast_address],
            ["Receive LIE IPv6 Multicast Address", self._rx_lie_ipv6_mcast_address],
            ["Transmit LIE IPv6 Multicast Address", self._tx_lie_ipv6_mcast_address],
            ["Receive LIE Port", self._rx_lie_port],
            ["Transmit LIE Port", self._tx_lie_port],
            ["LIE Send Interval", "{} secs".format(self._lie_send_interval_secs)],
            ["Receive TIE Port", self._rx_tie_port]
        ]

    def allocate_interface_id(self):
        # We assume an i32 is never going to wrap (i.e. no more than ~2M interfaces)
        interface_id = self._next_interface_id
        self._next_interface_id += 1
        return interface_id

    @staticmethod
    def cli_summary_headers():
        return [
            ["Node", "Name"],
            ["System", "ID"],
            ["Running"]]

    def cli_summary_attributes(self):
        return [
            self._name,
            utils.system_id_str(self._system_id),
            self._running]

    @staticmethod
    def cli_level_headers():
        return [
            ["Node", "Name"],
            ["System", "ID"],
            ["Running"],
            ["Configured", "Level"],
            ["Level", "Value"]]

    def cli_level_attributes(self):
        if self._running:
            return [
                self._name,
                utils.system_id_str(self._system_id),
                self._running,
                self._configured_level_symbol,
                self.level_value_str()]
        else:
            return [
                self._name,
                utils.system_id_str(self._system_id),
                self._running,
                self._configured_level_symbol,
                '?']

    def command_show_node(self, cli_session):
        cli_session.print("Node:")
        tab = table.Table(separators=False)
        tab.add_rows(self.cli_detailed_attributes())
        cli_session.print(tab.to_string())
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
        tab = self._fsm.history_table(verbose)
        cli_session.print(tab.to_string())

    def command_show_interfaces(self, cli_session):
        # TODO: Report neighbor uptime (time in THREE_WAY state)
        tab = table.Table()
        tab.add_row(interface.Interface.cli_summary_headers())
        for intf in self._interfaces.values():
            tab.add_row(intf.cli_summary_attributes())
        cli_session.print(tab.to_string())

    def command_show_interface(self, cli_session, parameters):
        interface_name = parameters['interface']
        if not interface_name in self._interfaces:
            cli_session.print("Error: interface {} not present".format(interface_name))
            return
        inteface_attributes = self._interfaces[interface_name].cli_detailed_attributes()
        tab = table.Table(separators=False)
        tab.add_rows(inteface_attributes)
        cli_session.print("Interface:")
        cli_session.print(tab.to_string())
        neighbor_attributes = self._interfaces[interface_name].cli_detailed_neighbor_attrs()
        if neighbor_attributes:
            tab = table.Table(separators=False)
            tab.add_rows(neighbor_attributes)
            cli_session.print("Neighbor:")
            cli_session.print(tab.to_string())

    def command_show_intf_fsm_hist(self, cli_session, parameters, verbose):
        interface_name = parameters['interface']
        if not interface_name in self._interfaces:
            cli_session.print("Error: interface {} not present".format(interface_name))
            return
        shown_interface = self._interfaces[interface_name]
        tab = shown_interface.fsm.history_table(verbose)
        cli_session.print(tab.to_string())

    def command_set_interface_failure(self, cli_session, parameters):
        interface_name = parameters['interface']
        if not interface_name in self._interfaces:
            cli_session.print("Error: interface {} not present".format(interface_name))
            return
        failure = parameters['failure'].lower()
        if failure not in ["ok", "rx-failed", "tx-failed", "failed"]:
            cli_session.print("Error: unknown failure {} (valid values are: "
                              "ok, failed, rx-failed, tx-failed)".format(failure))
            return
        tx_fail = failure in ["failed", "tx-failed"]
        rx_fail = failure in ["failed", "rx-failed"]
        self._interfaces[interface_name].set_failure(tx_fail, rx_fail)

    @property
    def name(self):
        return self._name

    # TODO: get rid of these properties, more complicated than needed. Just remote _ instead
    @property
    def system_id(self):
        return self._system_id

    @property
    def configured_level(self):
        return self._configured_level

    @property
    def lie_ipv4_mcast_address(self):
        return self._rx_lie_ipv4_mcast_address

    @property
    def lie_ipv6_mcast_address(self):
        return self._rx_lie_ipv6_mcast_address

    @property
    def lie_destination_port(self):
        return self._tx_lie_port

    @property
    def rx_tie_port(self):
        return self._rx_tie_port

    @property
    def lie_send_interval_secs(self):
        return self._lie_send_interval_secs

    @property
    def running(self):
        return self._running

    @property
    def engine(self):
        return self._engine

    @property
    def highest_adjacency_three_way(self):
        return self._highest_adjacency_three_way

    @property
    def leaf_2_leaf(self):
        return self._leaf_2_leaf

    @property
    def log(self):
        return self._log

    @property
    def log_id(self):
        return self._log_id

    @property
    def fsm(self):
        return self._fsm
