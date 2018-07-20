import enum
import logging
import os
import socket
import sortedcontainers
import uuid

import constants
import fsm
import interface
import rift
import table
import timer
import utils

# TODO: Command line argument and/or configuration option for CLI port

class Offer:

    def __init__(self, system_id, level, state):
        self.system_id = system_id
        self.level = level
        self.state = state

class Node:

    _next_node_nr = 1

    ZTP_MIN_NUMBER_OF_PEER_FOR_LEVEL = 3

    class State(enum.Enum):
        UPDATING_CLIENTS = 1
        HOLDING_DOWN = 2
        COMPUTE_BEST_OFFER = 3

    class Event(enum.Enum):
        CHANGE_LOCAL_LEAF_INDICATIONS = 1
        CHANGE_LOCAL_CONFIGURED_LEVEL = 2
        NEIGHBOR_OFFER = 3
        WITHDRAW_NEIGHBOR_OFFER = 4
        BETTER_HAL = 5
        BETTER_HAT = 6
        LOST_HAL = 7
        LOST_HAT = 8
        COMPUTATION_DONE = 9
        HOLDDOWN_EXPIRED = 10
        SHORT_TICK_TIMER = 11

    # on  LOST_HAT in ComputeBestOffer finishes in ComputeBestOffer:  LEVEL_COMPUTE
    # on    NeighborOffer in ComputeBestOffer    finishes in ComputeBestOffer: action_update_or_remove_offer
    #     if NeighborOffer.no_level_offered
    #           then REMOVE_OFFER
    #           else  if level > leaf
    #                   then UPDATE_OFFER
    #                   else REMOVE_OFFER
    # on    BetterHAL in ComputeBestOffer    finishes in ComputeBestOffer:    LEVEL_COMPUTE
    # on    ShortTic in COMPUTE_BEST_OFFER    finishes in COMPUTE_BEST_OFFER:
    # on BetterHAT in ComputeBestOffer finishes in ComputeBestOffer: LEVEL_COMPUTE
    # on WithdrawNeighborOffer in ComputeBestOffer finishes in ComputeBestOffer: REMOVE_OFFER
    # on ChangeLocalLeafIndications in ComputeBestOffer finishes in   ComputeBestOffer: action_store_leaf_flag,action_level_compute
    # on ComputationDone in ComputeBestOffer    finishes in    UpdatingClients: NO_ACTION
    # on ChangeLocalConfiguredLevel in ComputeBestOffer finishes in ComputeBestOffer:  action_store_level, action_level_compute
    # on LostHAL in ComputeBestOffer finishes in HoldingDown: action_update_holddown_timer_on_lost_hal
    #     if any    southbound    adjacencies    present
    #         then     update    holddown    timer    to    normal duration
    #         else fire holddown timer immediately


    # on  LOST_HAT  in                  HOLDING_DOWN   finishes in  HOLDING_DOWN:   NO_ACTION
    # on  LOST_HAL  in                  HOLDING_DOWN   finishes in  HOLDING_DOWN:   NO_ACTION
    # on  BETTER_HAT in                 HOLDING_DOWN   finishes in  HoldingDown:    NO_ACTION
    # on  ChangeLocalConfiguredLevel in HOLDING_DOWN   finishes in  ComputeBestOffer: STORE_LEVEL
    # on  HoldDownExpired in            HOLDING_DOWN   inishes in   ComputeBestOffer:    PURGE_OFFERS
    # on  ShortTic in                   HOLDING_DOWN   finishes in  HOLDING_DOWN:   action_check_hold_time_expired
    #    if HOLDDOWN_TIMER_EXPIRED
    #           then PUSH_EVENT   HOLDDOWN_EXPIRED
    # on NeighborOffer in               HoldingDown    finishes in  HoldingDown:       action_update_or_remove_offer
    #     if no level offered REMOVE_OFFER else
    #     if level > leaf then UPDATE_OFFER else REMOVE_OFFER
    # on BetterHAL in                   HoldingDown finishes in     HoldingDown: NO_ACTION
    # on WithdrawNeighborOffer in       HoldingDown finishes in     HoldingDown:      REMOVE_OFFER
    # on ChangeLocalLeafIndications in  HoldingDown finishes in     ComputeBestOffer: action_store_leaf_flag
    # on ComputationDone in             HoldingDown finishes in     HoldingDown: NO_ACTION

    # on    CHANGE_LOCAL_LEAF_INDICATIONS in  UpdatingClients    finishes in        ComputeBestOffer: STORE_LEAF_FLAGS
    # on    LOST_HAT in                       UpdatingClients    finishes in        ComputeBestOffer: NO_ACTION
    # on    BetterHAT in                      UpdatingClients  finishes in          ComputeBestOffer: NO_ACTION
    # on    ShortTic in                       UPDATING_CLIENTS    finishes in       UPDATING_CLIENTS:
    # on    LostHAL in                        UpdatingClients    finishes in        HOLDING_DOWN: action_update_holddown_timer_on_lost_hal
    #     if any southbound adjacencies present
    #         then update holddown timer to normal duration
    #         else fire   holddown    timer    immediately
    # on    NeighborOffer in                   UpdatingClients    finishes in       UpdatingClients: action_update_or_remove_offer
    #     if no level offered REMOVE_OFFER else
    #     if level > leaf then UPDATE_OFFER else REMOVE_OFFER
    # on ChangeLocalConfiguredLevel in          UpdatingClients finishes in         ComputeBestOffer: action_store_level
    # on BetterHAL in                           UpdatingClients finishes in         ComputeBestOffer: NO_ACTION
    # on WithdrawNeighborOffer in               UpdatingClients finishes in         UpdatingClients: REMOVE_OFFER


    # on Entry into UpdatingClients: action_update_all_lie_fsm_with_computation_results
    # on Entry into ComputeBestOffer: LEVEL_COMPUTE

   #  Following words are used for well known procedures:
   # 1.  PUSH Event: pushes an event to be executed by the FSM upon exit  of this action
   # 2.  COMPARE_OFFERS: checks whether based on current offers and held    last results the events
   #        BetterHAL/LostHAL/BetterHAT/LostHAT are       necessary and returns them
   # 3.  UPDATE_OFFER: store current offer and COMPARE_OFFERS, PUSH   according events
   # 4.  LEVEL_COMPUTE: compute best offered or configured level and HAL/  HAT, if anything changed PUSH ComputationDone
   # 5.  REMOVE_OFFER: remove the according offer and COMPARE_OFFERS, PUSH       according events
   # 6.  PURGE_OFFERS: REMOVE_OFFER for all held offers, COMPARE OFFERS,       PUSH according events

    # LEVEL_VALUE:  In ZTP case the original definition of "level" in   Section 2.1 is both extended and relaxed.  First, level is defined
    # now as LEVEL_VALUE and is the first defined value of    CONFIGURED_LEVEL followed by DERIVED_LEVEL.  Second, it is
    # possible for nodes to be more than one level apart to form adjacencies if any of the nodes is at least LEAF_ONLY.

    # Valid Offered Level (VOL):  A neighbor's level received on a valid  LIE (i.e. passing all checks for adjacency formation while  disregarding all clauses
    # involving level values) persisting for the duration of the holdtime interval on the LIE.  Observe that   offers from nodes offering level value of 0 do
    # not constitute VOLs  (since no valid DERIVED_LEVEL can be obtained from those).  Offers from LIEs with `not_a_ztp_offer` being true are not VOLs either.

    # Highest Available Level (HAL):  Highest defined level value seen from  all VOLs received.
    # Highest Adjacency Three Way (HAT):  Highest neigbhor level of all the   formed three way adjacencies for the node.

    #4.2.9.4.Level Determination Procedure

    # A node starting up with UNDEFINED_VALUE (i.e. without a
    # CONFIGURED_LEVEL or any leaf or superspine flag) MUST follow those
    # additional procedures:

    # 1.  It advertises its LEVEL_VALUE on all LIEs (observe that this can
    # be UNDEFINED_LEVEL which in terms of the schema is simply an
    # omitted optional value).

    # 2.  It chooses on an ongoing basis from all VOLs the value of
    # MAX(HAL-1,0) as its DERIVED_LEVEL.  The node then starts to
    # advertise this derived level.

    # 3.  A node that lost all adjacencies with HAL value MUST hold down
    # computation of new DERIVED_LEVEL for a short period of time
    # unless it has no VOLs from southbound adjacencies.  After the
    # holddown expired, it MUST discard all received offers, recompute
    # DERIVED_LEVEL and announce it to all neighbors.

    # 4.  A node MUST reset any adjacency that has changed the level it is
    # offering and is in three way state.

    # 5.  A node that changed its defined level value MUST readvertise its
    # own TIEs (since the new `PacketHeader` will contain a different
    # level than before).  Sequence number of each TIE MUST be
    # increased.

    # 6.  After a level has been derived the node MUST set the
    # `not_a_ztp_offer` on LIEs towards all systems extending a VOL for
    # HAL.

    # A node starting with LEVEL_VALUE being 0 (i.e. it assumes a leaf
    # function by being configured with the appropriate flags or has a
    # CONFIGURED_LEVEL of 0) MUST follow those additional procedures:

    # 1.  It computes HAT per procedures above but does NOT use it to
    # compute DERIVED_LEVEL.  HAT is used to limit adjacency formation
    # per Section 4.2.2.

    # on LostHAT in ComputeBestOffer finishes in ComputeBestOffer:
    #       LEVEL_COMPUTE

    def remove_offer(self, offer):
        # TODO: additional index by system_id
        for level in self._al.keys():
            if offer.system_id in self._al[level]:
                del self._al[level][offer.system_id]

    def update_offer(self, offer):
        self.remove_offer(offer)
        if not offer.level in self._al:
            self._al[offer.level]= {}
        self._al[offer.level][offer.system_id] = offer
        self.compare_offers()

    def is_leaf(self):
        # TODO: What does this mean exactly?
        return self._leaf_only

    def level_compute(self):
        # TODO: Finish this
        if len(self._al) == 0:
            self._hal = None
            return
        self._hal = max(self._al.keys())
        if not self._i_am_leaf:
            return
        highest_level = None
        for level in self._al.keys():
            if len(self._al[level]) >=  Ztp.ZTP_MIN_NUMBER_OF_PEER_FOR_LEVEL:
                if highest_level == None:
                    highest_level = level
                elif level >= highest_level:
                    highest_level = level
                else:
                    pass
        if highest_level != None and highest_level != 0:
            self._hal = highest_level

    def compare_offers(self):
        old_hal = self._hal
        self.level_compute()
        # TODO: Trigger if _hal changed

    def action_no_action(self):
        pass

    def action_level_compute(self):
        self.level_compute()

    def action_store_leaf_flags(self, leaf_flags):
        # TODO: on ChangeLocalLeafIndications in UpdatingClients finishes in ComputeBestOffer: store leaf flags
        pass

    def action_update_or_remove_offer(self, offer):
        # TODO:
        #          if no level offered REMOVE_OFFER else
        #          if level > leaf then UPDATE_OFFER else REMOVE_OFFER
        if offer.not_a_ztp_offer:
            return
        if offer.level is None:
            self.remove_offer(offer)
        if offer.level > common.constants.leaf_level:
            self.update_offer(offer)
        else:
            self.remove_offer(offer)

    def action_store_level(self, level):
        self._configured_level = level

    def action_purge_offers(self):
        self._al = {}
        self.compare_offers()

    def action_remove_offer(self, offer):
        level = 0
        while level in self._al:
            if offer.system_id in self._al[level]:
                del self._al[level][offer.system_id]

    def action_check_hold_time_expired(self):
        # TODO
        pass

    def action_update_all_lie_fsm_with_computation_results(self):
        # TODO
        pass

    def action_update_holddown_timer_on_lost_hal(self):
        # TODO:
        # if any southbound adjacencies present
        #   then update holddown timer to normal duration
        #   else fire   holddown    timer    immediately
        pass

    _state_updating_clients_transitions = {
        Event.CHANGE_LOCAL_LEAF_INDICATIONS:    (State.COMPUTE_BEST_OFFER, [action_store_leaf_flags]),
        Event.LOST_HAT:                         (State.COMPUTE_BEST_OFFER, [action_no_action]),
        Event.BETTER_HAT:                       (State.COMPUTE_BEST_OFFER, [action_no_action]),
        Event.SHORT_TICK_TIMER:                 (None, [action_no_action]),
        Event.LOST_HAL:                         (State.HOLDING_DOWN, [action_update_holddown_timer_on_lost_hal]),
        Event.NEIGHBOR_OFFER:                   (None, [action_update_or_remove_offer]),
        Event.CHANGE_LOCAL_CONFIGURED_LEVEL:    (State.COMPUTE_BEST_OFFER, [action_store_level]),
        Event.BETTER_HAL:                       (State.COMPUTE_BEST_OFFER, [action_no_action]),
        Event.WITHDRAW_NEIGHBOR_OFFER:          (None, [action_remove_offer]),
    }

    _state_holding_down_transitions = {
        Event.LOST_HAT:                         (None, [action_no_action]),
        Event.LOST_HAL:                         (None, [action_no_action]),
        Event.BETTER_HAT:                       (None, [action_no_action]),
        Event.CHANGE_LOCAL_CONFIGURED_LEVEL:    (State.COMPUTE_BEST_OFFER,[action_store_level]),
        Event.HOLDDOWN_EXPIRED:                 (State.COMPUTE_BEST_OFFER,[action_purge_offers]),
        Event.SHORT_TICK_TIMER:                 (None, [action_check_hold_time_expired]),
        Event.NEIGHBOR_OFFER:                   (None, [action_update_or_remove_offer]),
        Event.BETTER_HAL:                       (None, [action_no_action]),
        Event.WITHDRAW_NEIGHBOR_OFFER:          (None, [action_remove_offer]),
        Event.CHANGE_LOCAL_LEAF_INDICATIONS:    (State.COMPUTE_BEST_OFFER, [action_store_leaf_flags]),
        Event.COMPUTATION_DONE:                 (None, [action_no_action])
    }

    _state_compute_best_offer_transitions = {
        Event.LOST_HAT:                         (None, [action_level_compute]),
        Event.NEIGHBOR_OFFER:                   (None, [action_update_or_remove_offer]),
        Event.BETTER_HAL:                       (None, [action_level_compute]),
        Event.SHORT_TICK_TIMER:                 (None, [action_no_action]),
        Event.COMPUTATION_DONE:                 (State.UPDATING_CLIENTS, [action_no_action]),
        Event.CHANGE_LOCAL_CONFIGURED_LEVEL:    (None, [action_store_level, action_level_compute]),
        Event.LOST_HAL:                         (State.HOLDING_DOWN, [action_update_holddown_timer_on_lost_hal]),
        Event.BETTER_HAT:                       (None, [action_level_compute]),
        Event.WITHDRAW_NEIGHBOR_OFFER:          (None, [action_remove_offer]),
        Event.CHANGE_LOCAL_LEAF_INDICATIONS:    (None, [action_store_leaf_flags, action_level_compute])
    }

    _transitions = {
        State.UPDATING_CLIENTS: _state_updating_clients_transitions,
        State.HOLDING_DOWN: _state_holding_down_transitions,
        State.COMPUTE_BEST_OFFER: _state_compute_best_offer_transitions
    }

    _state_entry_actions = {
        State.UPDATING_CLIENTS:     [action_update_all_lie_fsm_with_computation_results],
        State.COMPUTE_BEST_OFFER:   [action_level_compute]
    }

    fsm_definition = fsm.FsmDefinition(
        state_enum = State, 
        event_enum = Event, 
        transitions = _transitions, 
        state_entry_actions = _state_entry_actions,
        initial_state = State.COMPUTE_BEST_OFFER)    

    def __init__(self, rift, config):
        # TODO: process level field in config
        # TODO: process systemid field in config
        # TODO: process state_thrift_services_port field in config
        # TODO: process config_thrift_services_port field in config
        # TODO: process v4prefixes field in config
        # TODO: process v6prefixes field in config
        self._rift = rift
        self._config = config
        self._node_nr = Node._next_node_nr
        Node._next_node_nr += 1
        self._name = self.get_config_attribute('name', self.generate_name())
        self._passive = self.get_config_attribute('passive', False)
        self._running = self.is_running()
        self._system_id = self.get_config_attribute('systemid', self.generate_system_id())
        self._log_id = utils.system_id_str(self._system_id)
        self._log = logging.getLogger('node')
        self._log.info("[{}] Create node".format(self._log_id))
        self.parse_level_config()
        self._interfaces = sortedcontainers.SortedDict()
        self._mcast_loop = True      # TODO: make configurable
        self._rx_lie_ipv4_mcast_address = self.get_config_attribute('rx_lie_mcast_address', constants.DEFAULT_LIE_IPV4_MCAST_ADDRESS)
        self._tx_lie_ipv4_mcast_address = self.get_config_attribute('tx_lie_mcast_address', constants.DEFAULT_LIE_IPV4_MCAST_ADDRESS)
        self._rx_lie_ipv6_mcast_address = self.get_config_attribute('rx_lie_v6_mcast_address', constants.DEFAULT_LIE_IPV6_MCAST_ADDRESS)
        self._tx_lie_ipv6_mcast_address = self.get_config_attribute('tx_lie_v6_mcast_address', constants.DEFAULT_LIE_IPV6_MCAST_ADDRESS)
        self._rx_lie_port = self.get_config_attribute('rx_lie_port', constants.DEFAULT_LIE_PORT)
        self._tx_lie_port = self.get_config_attribute('tx_lie_port', constants.DEFAULT_LIE_PORT)
        self._lie_send_interval_secs = constants.DEFAULT_LIE_SEND_INTERVAL_SECS   # TODO: make configurable
        self._rx_tie_port = self.get_config_attribute('rx_tie_port', constants.DEFAULT_TIE_PORT)
        self._derived_level = None
        self._al = {}    # TODO: Change name into something more meaningful
        self._hal = None
        self._fsm_log = self._log.getChild("fsm")
        # TODO: Take ztp hold time from init file
        self._holdtime = 1
        # TODO: Add where a leaf comes from
        self._next_interface_id = 1
        if 'interfaces' in config:
            for interface_config in self._config['interfaces']:
                self.create_interface(interface_config)
        self._fsm = fsm.Fsm(
            definition = self.fsm_definition,
            action_handler = self,
            log = self._fsm_log,
            log_id = self._log_id)
        self._one_second_timer = timer.Timer(1.0, lambda: self._fsm.push_event(self.Event.SHORT_TICK_TIMER))

    def info(self, logger, msg):
        logger.info("[{}] {}".format(self._node._log_id, msg))   # TODO: Make node._log_id public

    def warning(self, logger, msg):
        logger.warning("[{}] {}".format(self._node._log_id, msg))

    def generate_system_id(self):
        mac_address = uuid.getnode()
        pid = os.getpid()
        system_id = ((mac_address & 0xffffffffff) << 24) | (pid & 0xffff) << 8 | (self._node_nr & 0xff)
        return system_id

    def generate_name(self):
        return socket.gethostname().split('.')[0] + str(self._node_nr)

    def configured_level_str(self):
        return self.get_config_attribute('level', 'undefined')

    def parse_level_config(self):
        level_config = self.configured_level_str()
        if level_config == 'undefined':
            self._configured_level = None
            self._leaf_only = False
            self._leaf_2_leaf = False
            self._superspine_flag = False
        elif level_config == 'leaf':
            self._configured_level = None    # TODO: or 0?
            self._leaf_only = True
            self._leaf_2_leaf = False
            self._superspine_flag = False
        elif level_config == 'leaf-2-leaf':
            self._configured_level = None
            self._leaf_only = True
            self._leaf_2_leaf = True
            self._superspine_flag = False
        elif level_config == 'superspine':
            self._configured_level = None
            self._leaf_only = True
            self._leaf_2_leaf = True
            self._superspine_flag = False
        elif isinstance(level_config, int):
            self._configured_level = level_config
            self._leaf_only = False
            self._leaf_2_leaf = False
            self._superspine_flag = False
        else:
            # Should have been caught earlier by config validation.
            assert False, "Invalid level {}".format(level_config)

    def level_value(self):
        if self._configured_level != None:
            return self._configured_level
        else:
            return self._derived_level

    def level_value_str(self):
        level_value = self.level_value()
        if level_value == None:
            return 'undefined'
        else:
            return str(level_value)

    def perform_level_determination_procedure(self):
        return (self._configured_level != None) or self._leaf_only or self._leaf_2_leaf or self._superspine_flag

    def is_running(self):
        if self._rift.active_nodes == rift.Rift.ActiveNodes.ONLY_PASSIVE_NODES:
            running = self._passive
        elif self._rift.active_nodes == rift.Rift.ActiveNodes.ALL_NODES_EXCEPT_PASSIVE_NODES:
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
            ["Configured Level", self._configured_level],
            ["Leaf Only", self._leaf_only],
            ["Leaf 2 Leaf", self._leaf_2_leaf],
            ["Superspine Flag", self._superspine_flag],
            ["Level Value", self.level_value()],
            ["Perform Level Determination Procedure", self.perform_level_determination_procedure()],
            ["Multicast Loop", self._mcast_loop],
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
                self.configured_level_str(),
                self.level_value_str()]
        else:
            return [
                self._name,
                utils.system_id_str(self._system_id),
                self._running,
                self.configured_level_str(),
                '?']

    def command_show_node(self, cli_session):
        tab = table.Table(separators = False)
        tab.add_rows(self.cli_detailed_attributes())
        cli_session.print(tab.to_string())

    def command_show_node_fsm_history(self, cli_session):
        tab = self._fsm.history_table()
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
        tab = table.Table(separators = False)
        tab.add_rows(inteface_attributes)
        cli_session.print("Interface:")
        cli_session.print(tab.to_string())
        neighbor_attributes = self._interfaces[interface_name].cli_detailed_neighbor_attributes()
        if neighbor_attributes:
            tab = table.Table(separators = False)
            tab.add_rows(neighbor_attributes)
            cli_session.print("Neighbor:")
            cli_session.print(tab.to_string())

    def command_show_interface_fsm_history(self, cli_session, parameters):
        interface_name = parameters['interface']
        if not interface_name in self._interfaces:
            cli_session.print("Error: interface {} not present".format(interface_name))
            return
        interface = self._interfaces[interface_name]
        tab = interface._fsm.history_table()
        cli_session.print(tab.to_string())

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
    def lie_send_interval_secs(self):
        return self._lie_send_interval_secs

    @property
    def mcast_loop(self):
        return self._mcast_loop

    @property
    def running(self):
        return self._running
