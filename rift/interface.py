# pylint:disable=too-many-lines

import collections
import enum
import random
import socket

import constants
import fsm
import neighbor
import offer
import packet_common
import table
import timer
import udp_receive_handler
import udp_send_handler
import utils

import common.constants
import common.ttypes
import encoding.ttypes

# TODO: LIEs arriving with a TTL larger than 1 MUST be ignored.

# TODO: Implement configuration of POD numbers

# TODO: Send LIE packets with network control precedence.

# TODO: Add IPv6 support

# TODO: Have a mechanism to detect that an interface comes into / goes out of existence

# TODO: Have a mechanism to detect IPv4 or IPv6 address changes on an interface

class Interface:

    UNDEFINED_OR_ANY_POD = 0

    SERVICE_QUEUES_INTERVAL = 1.0

    def generate_advertised_name(self):
        return self._node.name + '-' + self._interface_name

    def get_mtu(self):
        # TODO: Find a portable (or even non-portable) way to get the interface MTU
        # TODO: Find a way to be informed whenever the interface MTU changes
        #!!! mtu = 1500
        mtu = 1400
        return mtu

    @staticmethod
    def generate_nonce():
        # 63 bits instead of 64 because nonce field is a signed i64
        nonce = random.getrandbits(63)
        return nonce

    class State(enum.Enum):
        ONE_WAY = 1
        TWO_WAY = 2
        THREE_WAY = 3

    class Event(enum.Enum):
        TIMER_TICK = 1
        LEVEL_CHANGED = 2
        HAL_CHANGED = 3
        HAT_CHANGED = 4
        HALS_CHANGED = 5
        LIE_RECEIVED = 6
        NEW_NEIGHBOR = 7
        VALID_REFLECTION = 8
        NEIGHBOR_DROPPED_REFLECTION = 9
        NEIGHBOR_CHANGED_LEVEL = 10
        NEIGHBOR_CHANGED_ADDRESS = 11
        NEIGHBOR_CHANGED_MINOR_FIELDS = 12
        UNACCEPTABLE_HEADER = 13
        HOLD_TIME_EXPIRED = 14
        MULTIPLE_NEIGHBORS = 15
        LIE_CORRUPT = 16
        SEND_LIE = 17

    verbose_events = [Event.TIMER_TICK, Event.LIE_RECEIVED, Event.SEND_LIE]

    def action_store_hal(self):
        # TODO: Need to implement ZTP state machine first
        pass

    def action_store_hat(self):
        # TODO: Need to implement ZTP state machine first
        pass

    def action_store_hals(self):
        # TODO: Need to implement ZTP state machine first
        pass

    def action_update_level(self):
        # TODO: Need to implement ZTP state machine and/or configuration first
        pass

    def action_start_flooding(self):
        # Start sending TIE, TIRE, and TIDE packets to this neighbor
        rx_flood_port = self._rx_tie_port
        tx_flood_port = self.neighbor.flood_port
        self.info(self._rx_log, ("Start flooding: receive on port {}, send on port {}"
                                 .format(rx_flood_port, tx_flood_port)))
        # TODO: the local addresses below should be the interface address, not the engine addresses
        self._flood_receive_handler = udp_receive_handler.UdpReceiveHandler(
            remote_address=self.neighbor.address,
            port=rx_flood_port,
            receive_function=self.receive_flood_message,
            local_address=self._node.engine.tx_src_address)
        self._flood_send_handler = udp_send_handler.UdpSendHandler(
            interface_name=self._interface_name,
            remote_address=self.neighbor.address,
            port=tx_flood_port,
            local_address=self._node.engine.tx_src_address)
            # TODO: This can't be the interface address since it is per engine
        # Periodically start sending TIE packets and TIRE packets
        self._service_queues_timer.start()
        # Update the node TIEs originated by this node to include this neighbor
        self._node.regenerate_all_node_ties()
        # We don't blindly send all TIEs to the neighbor because he might already have them. Instead
        # we send a TIDE packet right now. If our neighbor is missing a TIE that is in our database
        # he will request it after he receives the TIDE packet.
        self._node.send_tides_on_interface(self)

    def action_stop_flooding(self):
        # Stop sending TIE, TIRE, and TIDE packets to this neighbor
        self.info(self._rx_log, "Stop flooding")
        self._service_queues_timer.stop()
        self.clear_all_queues()
        self._flood_receive_handler.close()
        self._flood_receive_handler = None
        self._flood_send_handler.close()
        self._flood_send_handler = None
        # Update the node TIEs originated by this node to exclude this neighbor. We have to pass
        # interface_going_down to regenerate_all_node_ties because the state of this interface is
        # still THREE_WAY at this point.
        self._node.regenerate_all_node_ties(interface_going_down=self)

    def send_protocol_packet(self, protocol_packet, flood, dont_change):
        encoded_protocol_packet = packet_common.encode_protocol_packet(protocol_packet, dont_change)
        if flood:
            handler = self._flood_send_handler
        else:
            handler = self._lie_send_handler
        to_str = "{}:{}".format(handler.remote_address, handler.port)
        if self._tx_fail:
            self.debug(self._tx_log, "Simulated send failure {} to {}"
                       .format(protocol_packet, to_str))
        else:
            try:
                handler.send_message(encoded_protocol_packet)
            except socket.error as error:
                self.error(self._tx_log, "Error \"{}\" sending {} to {}"
                           .format(error, protocol_packet, to_str))
                return
            self.debug(self._tx_log, "Send {} to {}".format(protocol_packet, to_str))

    def action_send_lie(self):
        packet_header = encoding.ttypes.PacketHeader(
            sender=self._node.system_id,
            level=self._node.level_value())
        capabilities = encoding.ttypes.NodeCapabilities(
            flood_reduction=True,
            hierarchy_indications=
            common.ttypes.HierarchyIndications.leaf_only_and_leaf_2_leaf_procedures)
        if self.neighbor:
            neighbor_system_id = self.neighbor.system_id
            neighbor_link_id = self.neighbor.local_id
            lie_neighbor = encoding.ttypes.Neighbor(neighbor_system_id, neighbor_link_id)
        else:
            neighbor_system_id = None
            lie_neighbor = None
        lie_packet = encoding.ttypes.LIEPacket(
            name=self._advertised_name,
            local_id=self._local_id,
            flood_port=self._rx_tie_port,
            link_mtu_size=self._mtu,
            neighbor=lie_neighbor,
            pod=self._pod,
            nonce=Interface.generate_nonce(),
            capabilities=capabilities,
            holdtime=3,
            not_a_ztp_offer=self._node.send_not_a_ztp_offer_on_intf(self._interface_name),
            you_are_flood_repeater=True,     # TODO: Set you_are_not_flood_repeater
            label=None)
        packet_content = encoding.ttypes.PacketContent(lie=lie_packet)
        protocol_packet = encoding.ttypes.ProtocolPacket(packet_header, packet_content)
        self.send_protocol_packet(protocol_packet, flood=False, dont_change=False)
        tx_offer = offer.TxOffer(
            self._interface_name,
            self._node.system_id,
            packet_header.level,
            lie_packet.not_a_ztp_offer,
            self._fsm.state)
        self._node.record_tx_offer(tx_offer)

    def action_cleanup(self):
        self.neighbor = None

    def check_reflection(self):
        # Does the received LIE packet (which is now stored in _neighbor) report us as the neighbor?
        if self.neighbor.neighbor_system_id != self._node.system_id:
            self.info(self._log,
                      "Neighbor does not report us as neighbor (system-id {:16x} instead of {:16x}"
                      .format(self.neighbor.neighbor_system_id, self._node.system_id))
            return False
        if self.neighbor.neighbor_link_id != self._local_id:
            self.info(self._log, "Neighbor does not report us as neighbor (link-id {} instead of {}"
                      .format(self.neighbor.neighbor_link_id, self._local_id))
            return False
        return True

    def check_three_way(self):
        # Section B.1.5
        # CHANGE: This is a little bit different from the specification
        # (see comment [CheckThreeWay])
        if self._fsm.state == self.State.ONE_WAY:
            pass
        elif self._fsm.state == self.State.TWO_WAY:
            if self.neighbor.neighbor_system_id is None:
                pass
            elif self.check_reflection():
                self._fsm.push_event(self.Event.VALID_REFLECTION)
            else:
                self._fsm.push_event(self.Event.MULTIPLE_NEIGHBORS)
        else: # state is THREE_WAY
            if self.neighbor.neighbor_system_id is None:
                self._fsm.push_event(self.Event.NEIGHBOR_DROPPED_REFLECTION)
            elif self.check_reflection():
                pass
            else:
                self._fsm.push_event(self.Event.MULTIPLE_NEIGHBORS)

    def check_minor_change(self, new_neighbor):
        # TODO: what if link_mtu_size changes?
        # TODO: what if pod changes?
        # TODO: what if capabilities changes?
        # TODO: what if holdtime changes?
        # TODO: what if not_a_ztp_offer changes?
        # TODO: what if you_are_flood_repeater changes?
        # TODO: what if label changes?
        minor_change = False
        if new_neighbor.flood_port != self.neighbor.flood_port:
            msg = ("Neighbor flood-port changed from {} to {}"
                   .format(self.neighbor.flood_port, new_neighbor.flood_port))
            minor_change = True
        elif new_neighbor.name != self.neighbor.name:
            msg = ("Neighbor name changed from {} to {}"
                   .format(self.neighbor.name, new_neighbor.name))
            minor_change = True
        elif new_neighbor.local_id != self.neighbor.local_id:
            msg = ("Neighbor local-id changed from {} to {}"
                   .format(self.neighbor.local_id, new_neighbor.local_id))
            minor_change = True
        if minor_change:
            self.info(self._log, msg)
        return minor_change

    def send_offer_to_ztp_fsm(self, offering_neighbor):
        offer_for_ztp = offer.RxOffer(
            self._interface_name,
            offering_neighbor.system_id,
            offering_neighbor.level,
            offering_neighbor.not_a_ztp_offer,
            self._fsm.state)
        self._node.fsm.push_event(self._node.Event.NEIGHBOR_OFFER, offer_for_ztp)

    def this_node_is_leaf(self):
        return self._node.level_value() == common.constants.leaf_level

    def hat_not_greater_remote_level(self, remote_level):
        if self._node.highest_adjacency_three_way is None:
            return True
        return self._node.highest_adjacency_three_way <= remote_level

    def both_nodes_support_leaf_2_leaf(self, protocol_packet):
        header = protocol_packet.header
        lie = protocol_packet.content.lie
        if not self.this_node_is_leaf():
            # This node is not a leaf
            return False
        if header.level != 0:
            # Remote node is not a leaf
            return False
        if not self._node.leaf_2_leaf:
            # This node does not support leaf-2-leaf
            return False
        if lie.capabilities is None:
            # Remote node does not support leaf-2-leaf
            return False
        if (lie.capabilities.hierarchy_indications !=
                common.ttypes.HierarchyIndications.leaf_only_and_leaf_2_leaf_procedures):
            # Remote node does not support leaf-2-leaf
            return False
        return True

    def neither_leaf_and_ldiff_one(self, protocol_packet):
        # Neither node is leaf and the level difference is at most one
        header = protocol_packet.header
        if self.this_node_is_leaf():
            # This node is leaf
            return False
        if header.level == 0:
            # Remote node is leaf
            return False
        assert self._node.level_value() is not None
        assert header.level is not None
        if abs(header.level - self._node.level_value()) > 1:
            # Level difference is greater than 1
            return False
        return True

    def is_received_lie_acceptable(self, protocol_packet):
        # Check whether a received LIE message is acceptable for the purpose of progressing towards
        # a 3-way adjacency. This implements the rules specified in sections B.1.4.1 and B.1.4.2 of
        # the specification.
        # DEV-4: This also implements the rules specified in the 8 bullet points in section 4.2.2,
        # some of which are also present in section B.1.4 and some of which are missing from section
        # B.1.4.
        # The return value of this function is (accept, rule, offer_to_ztp, warning) where
        # - accept: True if the received LIE message is acceptable, False if not
        # - rule: A short human-readable string describing the rule used to accept or reject the
        #   LIE message
        # - offer_to_ztp: True if an offer should be sent to the ZTP FSM. Note that we even send
        #   offers to the the ZTP FSM for most rejected LIE messages, and the ZTP FSM stores these
        #   as "removed offers" for debugging.
        # - warning: If True, log a warning message, if False, log an info message.
        #
        # TODO: Add counters for each of these conditions
        #
        header = protocol_packet.header
        lie = protocol_packet.content.lie
        if not header:
            return (False, "Missing header", False, True)
        if header.major_version != constants.RIFT_MAJOR_VERSION:
            # Note: we never get here, since this is caught earlier receive_message_common
            # Section B.1.4.1 (1st OR clause) / section 4.2.2.2
            problem = ("Different major protocol version (local version {}, remote version {})"
                       .format(constants.RIFT_MAJOR_VERSION, header.major_version))
            self.error(self._rx_log, problem)
            return (False, problem, False, True)
        if not self.is_valid_received_system_id(header.sender):
            # Section B.1.4.1 (3rd OR clause) / section 4.2.2.2
            return (False, "Invalid system ID", False, True)
        if self._node.system_id == header.sender:
            # Section 4.2.2.5 (DEV-4: rule is missing in section B.1.4)
            return (False, "Remote system ID is same as local system ID (loop)", False, False)
        if self._mtu != lie.link_mtu_size:
            # Section 4.2.2.6
            return (False, "MTU mismatch", False, True)
        if header.level is None:
            # Section B.1.4.2 (1st OR clause) / section 4.2.2.7
            return (False, "Remote level (in received LIE) is undefined", True, False)
        if self._node.level_value() is None:
            # Section B.1.4.2 (2nd OR clause) / section 4.2.2.7
            return (False, "My level is undefined", True, False)
        if ((self._pod != self.UNDEFINED_OR_ANY_POD) and
                (lie.pod != self.UNDEFINED_OR_ANY_POD) and
                (self._pod != lie.pod)):
            # Section 4.2.2.1 (DEV-4: rule is missing in section B.1.4)
            return (False, "PoD mismatch", True, True)
        if self._mtu != lie.link_mtu_size:
            # Section 4.2.2.6 (DEV-4: rule is missing in section B.1.4)
            return (False, "MTU mismatch", True, True)
        # DEV-4: The following rules are correctly specified in 4.2.2.8 and incorrectly in B.1.4.2
        if self.this_node_is_leaf() and self.hat_not_greater_remote_level(header.level):
            # Section 4.2.2.8 (1st OR clause) / DEV-4:Different in section B.1.4.2 (3rd OR clause)
            return (True, "This node is leaf and HAT not greater than remote level", True, False)
        if not self.this_node_is_leaf() and (header.level == 0):
            # Section 4.2.2.8 (2nd OR clause) / DEV-4: Missing in section B.1.4
            return (True, "This node is not leaf and neighbor is leaf", True, False)
        if self.both_nodes_support_leaf_2_leaf(protocol_packet):
            # Section 4.2.2.8 (3rd OR clause) / DEV-4: Missing in section B.1.4
            return (True, "Both nodes are leaf and support leaf-2-leaf", True, False)
        if self.neither_leaf_and_ldiff_one(protocol_packet):
            # Section 4.2.2.8 (4th OR clause) / DEV-4:Different in section B.1.4.3.2 (4th OR clause)
            return (True, "Neither node is leaf and level difference is at most one", True, False)
        return (False, "Level mismatch", True, True)

    def action_process_lie(self, event_data):
        (protocol_packet, (from_address, from_port)) = event_data
        # TODO: This is a simplistic way of implementing the hold timer. Use a real timer instead.
        self._time_ticks_since_lie_received = 0
        # Sections B.1.4.1 and B.1.4.2
        new_neighbor = neighbor.Neighbor(protocol_packet, from_address, from_port)
        (accept, rule, offer_to_ztp, warning) = self.is_received_lie_acceptable(protocol_packet)
        if not accept:
            self._lie_accept_or_reject = "Rejected"
            self._lie_accept_or_reject_rule = rule
            if warning:
                self.warning(self._rx_log, "Received LIE packet rejected: {}".format(rule))
            else:
                self.info(self._rx_log, "Received LIE packet rejected: {}".format(rule))
            self.action_cleanup()
            if offer_to_ztp:
                self.send_offer_to_ztp_fsm(new_neighbor)
                self._fsm.push_event(self.Event.UNACCEPTABLE_HEADER)
            return
        self._lie_accept_or_reject = "Accepted"
        self._lie_accept_or_reject_rule = rule
        # Section B.1.4.3
        # Note: We send an offer to the ZTP state machine directly from here instead of pushing an
        # UPDATE_ZTP_OFFER event (see deviation DEV-2 in doc/deviations)
        self.send_offer_to_ztp_fsm(new_neighbor)
        if not self.neighbor:
            self.info(self._log, "New neighbor detected with system-id {}"
                      .format(utils.system_id_str(protocol_packet.header.sender)))
            self.neighbor = new_neighbor
            self._fsm.push_event(self.Event.NEW_NEIGHBOR)
            self.check_three_way()
            return
        # Section B.1.4.3.1
        if new_neighbor.system_id != self.neighbor.system_id:
            self.info(self._log, "Neighbor system-id changed from {} to {}"
                      .format(utils.system_id_str(self.neighbor.system_id),
                              utils.system_id_str(new_neighbor.system_id)))
            self._fsm.push_event(self.Event.MULTIPLE_NEIGHBORS)
            return
        # Section B.1.4.3.2
        if new_neighbor.level != self.neighbor.level:
            self.info(self._log, "Neighbor level changed from {} to {}"
                      .format(self.neighbor.level, new_neighbor.level))
            self._fsm.push_event(self.Event.NEIGHBOR_CHANGED_LEVEL)
            return
        # Section B.1.4.3.3
        if new_neighbor.address != self.neighbor.address:
            self.info(self._log, "Neighbor address changed from {} to {}"
                      .format(self.neighbor.address, new_neighbor.address))
            self._fsm.push_event(self.Event.NEIGHBOR_CHANGED_ADDRESS)
            return
        # Section B.1.4.3.4
        if self.check_minor_change(new_neighbor):
            self._fsm.push_event(self.Event.NEIGHBOR_CHANGED_MINOR_FIELDS)
        self.neighbor = new_neighbor      # TODO: The draft does not specify this, but it is needed
        # Section B.1.4.3.5
        self.check_three_way()

    def action_check_hold_time_expired(self):
        # TODO: This is a (too) simplistic way of managing timers in the draft; use an explicit
        # timer.
        # If time_ticks_since_lie_received is None, it means the timer is not running
        if self._time_ticks_since_lie_received is None:
            return
        self._time_ticks_since_lie_received += 1
        if self.neighbor and self.neighbor.holdtime:
            holdtime = self.neighbor.holdtime
        else:
            holdtime = common.constants.default_lie_holdtime
        if self._time_ticks_since_lie_received >= holdtime:
            self._fsm.push_event(self.Event.HOLD_TIME_EXPIRED)

    def action_hold_time_expired(self):
        self._node.expire_offer(self._interface_name)

    _state_one_way_transitions = {
        Event.TIMER_TICK: (None, [], [Event.SEND_LIE]),
        Event.LEVEL_CHANGED: (State.ONE_WAY, [action_update_level], [Event.SEND_LIE]),
        Event.HAL_CHANGED: (None, [action_store_hal]),
        Event.HAT_CHANGED: (None, [action_store_hat]),
        Event.HALS_CHANGED: (None, [action_store_hals]),
        Event.LIE_RECEIVED: (None, [action_process_lie]),
        Event.NEW_NEIGHBOR: (State.TWO_WAY, [], [Event.SEND_LIE]),
        Event.UNACCEPTABLE_HEADER: (State.ONE_WAY, []),
        Event.HOLD_TIME_EXPIRED: (None, [action_hold_time_expired]),
        Event.SEND_LIE: (None, [action_send_lie]),
        # Removed. See deviation DEV-2 in doc/deviations.md. TODO: remove line completely.
        # Event.UPDATE_ZTP_OFFER: (None, [action_send_offer_to_ztp_fsm])
    }

    _state_two_way_transitions = {
        Event.TIMER_TICK: (None, [action_check_hold_time_expired], [Event.SEND_LIE]),
        Event.LEVEL_CHANGED: (State.ONE_WAY, [action_update_level]),
        Event.HAL_CHANGED: (None, [action_store_hal]),
        Event.HAT_CHANGED: (None, [action_store_hat]),
        Event.HALS_CHANGED: (None, [action_store_hals]),
        Event.HALS_CHANGED: (None, [action_store_hals]),
        Event.LIE_RECEIVED: (None, [action_process_lie]),
        Event.VALID_REFLECTION: (State.THREE_WAY, []),
        Event.NEIGHBOR_CHANGED_LEVEL: (State.ONE_WAY, []),
        Event.NEIGHBOR_CHANGED_ADDRESS: (State.ONE_WAY, []),
        Event.UNACCEPTABLE_HEADER: (State.ONE_WAY, []),
        Event.HOLD_TIME_EXPIRED: (State.ONE_WAY, [action_hold_time_expired]),
        Event.MULTIPLE_NEIGHBORS: (State.ONE_WAY, []),
        Event.LIE_CORRUPT: (State.ONE_WAY, []),             # This transition is not in draft
        Event.SEND_LIE: (None, [action_send_lie])}

    _state_three_way_transitions = {
        Event.TIMER_TICK: (None, [action_check_hold_time_expired], [Event.SEND_LIE]),
        Event.LEVEL_CHANGED: (State.ONE_WAY, [action_update_level]),
        Event.HAL_CHANGED: (None, [action_store_hal]),
        Event.HAT_CHANGED: (None, [action_store_hat]),
        Event.HALS_CHANGED: (None, [action_store_hals]),
        Event.LIE_RECEIVED: (None, [action_process_lie]),
        Event.NEIGHBOR_DROPPED_REFLECTION: (State.TWO_WAY, []),
        Event.NEIGHBOR_CHANGED_LEVEL: (State.ONE_WAY, []),
        Event.NEIGHBOR_CHANGED_ADDRESS: (State.ONE_WAY, []),
        Event.UNACCEPTABLE_HEADER: (State.ONE_WAY, []),
        Event.HOLD_TIME_EXPIRED: (State.ONE_WAY, [action_hold_time_expired]),
        Event.MULTIPLE_NEIGHBORS: (State.ONE_WAY, []),
        Event.LIE_CORRUPT: (State.ONE_WAY, []),             # This transition is not in draft
        Event.SEND_LIE: (None, [action_send_lie]),
    }

    _transitions = {
        State.ONE_WAY: _state_one_way_transitions,
        State.TWO_WAY: _state_two_way_transitions,
        State.THREE_WAY: _state_three_way_transitions
    }

    _state_actions = {
        State.ONE_WAY  : ([action_cleanup, action_send_lie], []),
        State.THREE_WAY: ([action_start_flooding], [action_stop_flooding])
    }

    fsm_definition = fsm.FsmDefinition(
        state_enum=State,
        event_enum=Event,
        transitions=_transitions,
        initial_state=State.ONE_WAY,
        state_actions=_state_actions,
        verbose_events=verbose_events)

    # TODO: Use % formating for log messages
    # See https://stackoverflow.com/questions/34619790/pylint-message-logging-format-interpolation

    def debug(self, logger, msg):
        logger.debug("[{}] {}".format(self._log_id, msg))

    def info(self, logger, msg):
        logger.info("[{}] {}".format(self._log_id, msg))

    def warning(self, logger, msg):
        logger.warning("[{}] {}".format(self._log_id, msg))

    def error(self, logger, msg):
        logger.error("[{}] {}".format(self._log_id, msg))

    def __init__(self, node, config):
        # TODO: process bandwidth field in config
        self._node = node
        self._interface_name = config['name']
        # TODO: Make the default metric/bandwidth depend on the speed of the interface
        self._metric = self.get_config_attribute(config, 'metric',
                                                 common.constants.default_bandwidth)
        self._advertised_name = self.generate_advertised_name()
        self._log_id = node.log_id + "-{}".format(self._interface_name)
        self._ipv4_address = utils.interface_ipv4_address(self._interface_name,
                                                          self._node.engine.tx_src_address)
        self._rx_lie_ipv4_mcast_address = self.get_config_attribute(
            config, 'rx_lie_mcast_address', constants.DEFAULT_LIE_IPV4_MCAST_ADDRESS)
        self._tx_lie_ipv4_mcast_address = self.get_config_attribute(
            config, 'tx_lie_mcast_address', constants.DEFAULT_LIE_IPV4_MCAST_ADDRESS)
        self._rx_lie_ipv6_mcast_address = self.get_config_attribute(
            config, 'rx_lie_v6_mcast_address', constants.DEFAULT_LIE_IPV6_MCAST_ADDRESS)
        self._tx_lie_ipv6_mcast_address = self.get_config_attribute(
            config, 'tx_lie_v6_mcast_address', constants.DEFAULT_LIE_IPV6_MCAST_ADDRESS)
        self._rx_lie_port = self.get_config_attribute(config, 'rx_lie_port',
                                                      constants.DEFAULT_LIE_PORT)
        self._tx_lie_port = self.get_config_attribute(config, 'tx_lie_port',
                                                      constants.DEFAULT_LIE_PORT)
        self._rx_tie_port = self.get_config_attribute(config, 'rx_tie_port',
                                                      constants.DEFAULT_TIE_PORT)
        self._rx_fail = False
        self._tx_fail = False
        self._log = node.log.getChild("if")
        self.info(self._log, "Create interface")
        self._rx_log = self._log.getChild("rx")
        self._tx_log = self._log.getChild("tx")
        self._fsm_log = self._log.getChild("fsm")
        self._local_id = node.allocate_interface_id()
        self._mtu = self.get_mtu()
        self._pod = self.UNDEFINED_OR_ANY_POD
        self.neighbor = None
        self._time_ticks_since_lie_received = None
        self._lie_accept_or_reject = "No LIE Received"
        self._lie_accept_or_reject_rule = "-"
        self._lie_receive_handler = None
        self._flood_receive_handler = None
        self._flood_send_handler = None
        # The following queues (ties_tx, ties_rtx, ties_req, are ties_ack) are ordered dictionaries.
        # The value is the header of the TIE. The index is the TIE-ID want to have two headers with
        # same TIE-ID in the queue. The ordering is needed because we want to service the entries
        # in the queue in the same order in which they were added (FIFO).
        # TODO: For _ties_rtx, add time to retransmit to retransmit queue
        self._ties_tx = collections.OrderedDict()
        self._ties_rtx = collections.OrderedDict()
        self._ties_req = collections.OrderedDict()
        self._ties_ack = collections.OrderedDict()
        self._fsm = fsm.Fsm(
            definition=self.fsm_definition,
            action_handler=self,
            log=self._fsm_log,
            log_id=self._log_id)
        if self._node.running:
            self.run()
            self._fsm.start()

    def run(self):
        self._lie_send_handler = udp_send_handler.UdpSendHandler(
            interface_name=self._interface_name,
            remote_address=self._tx_lie_ipv4_mcast_address,
            port=self._tx_lie_port,
            local_address=self._node.engine.tx_src_address,
            multicast_loopback=self._node.engine.multicast_loopback)
        # TODO: Use source address
        (_, source_port) = self._lie_send_handler.source_address_and_port()
        self._lie_udp_source_port = source_port
        self._lie_receive_handler = udp_receive_handler.UdpReceiveHandler(
            remote_address=self._rx_lie_ipv4_mcast_address,
            port=self._rx_lie_port,
            receive_function=self.receive_lie_message,
            local_address=self._node.engine.tx_src_address)
        self._flood_receive_handler = None
        self._flood_send_handler = None
        self._one_second_timer = timer.Timer(
            1.0,
            lambda: self._fsm.push_event(self.Event.TIMER_TICK))
        self._service_queues_timer = timer.Timer(
            interval=self.SERVICE_QUEUES_INTERVAL,
            expire_function=self.service_queues,
            periodic=True,
            start=False)

    def get_config_attribute(self, config, attribute, default):
        if attribute in config:
            return config[attribute]
        else:
            return default

    def is_valid_received_system_id(self, system_id):
        if system_id == 0:
            return False
        return True

    def receive_message_common(self, message, from_address_and_port):
        (address, port) = from_address_and_port
        from_str = "{}:{}".format(address, port)
        protocol_packet = packet_common.decode_protocol_packet(message)
        if protocol_packet is None:
            self.error(self._rx_log,
                       "Could not decode message received from {}".format(from_str))
            return None
        if self._rx_fail:
            self.debug(self._rx_log, ("Simulated receive failure {} from {}"
                                      .format(protocol_packet, from_str)))
            return None
        if protocol_packet.header.sender == self._node.system_id:
            self.debug(self._rx_log, ("Looped receive {} from {}"
                                      .format(protocol_packet, from_str)))
            return None
        self.debug(self._rx_log, ("Receive {} from {}"
                                  .format(protocol_packet, from_str)))
        if not protocol_packet.content:
            self.warning(self._rx_log, ("Received packet without content from {}"
                                        .format(from_str)))
            return None
        if protocol_packet.header.major_version != constants.RIFT_MAJOR_VERSION:
            self.error(self._rx_log, ("Received different major protocol version from {} "
                                      "(local version {}, remote version {})"
                                      .format(from_str,
                                              constants.RIFT_MAJOR_VERSION,
                                              protocol_packet.header.major_version)))
            return None
        return protocol_packet

    def receive_lie_message(self, message, from_address_and_port):
        protocol_packet = self.receive_message_common(message, from_address_and_port)
        if protocol_packet is None:
            return
        if protocol_packet.content.lie:
            event_data = (protocol_packet, from_address_and_port)
            self._fsm.push_event(self.Event.LIE_RECEIVED, event_data)
        if protocol_packet.content.tie:
            self.warning(self._rx_log, "Received TIE packet on LIE port (ignored)")
        if protocol_packet.content.tide:
            self.warning(self._rx_log, "Received TIDE packet on LIE port (ignored)")
        if protocol_packet.content.tire:
            self.warning(self._rx_log, "Received TIRE packet on LIE port (ignored)")

    def receive_flood_message(self, message, from_address_and_port):
        protocol_packet = self.receive_message_common(message, from_address_and_port)
        if protocol_packet is None:
            return
        if protocol_packet.content.tie is not None:
            self.process_received_tie_packet(protocol_packet.content.tie)
        if protocol_packet.content.tide:
            self.process_received_tide_packet(protocol_packet.content.tide)
        if protocol_packet.content.tire:
            self.process_received_tire_packet(protocol_packet.content.tire)
        if protocol_packet.content.lie:
            self.warning(self._rx_log, "Received LIE packet on flood port (ignored)")

    def set_failure(self, tx_fail, rx_fail):
        self._tx_fail = tx_fail
        self._rx_fail = rx_fail

    def failure_str(self):
        if self._tx_fail:
            if self._rx_fail:
                return "failed"
            else:
                return "tx-failed"
        else:
            if self._rx_fail:
                return "rx-failed"
            else:
                return "ok"

    def process_received_tie_packet(self, tie_packet):
        self.debug(self._rx_log, "Receive TIE packet {}".format(tie_packet))
        result = self._node.tie_db.process_received_tie_packet(tie_packet, self._node.system_id)
        (start_sending_tie_header, ack_tie_header) = result
        if start_sending_tie_header is not None:
            self.try_to_transmit_tie(start_sending_tie_header)
        if ack_tie_header is not None:
            self.ack_tie(ack_tie_header)

    def process_received_tide_packet(self, tide_packet):
        result = self._node.tie_db.process_received_tide_packet(tide_packet)
        (request_tie_headers, start_sending_tie_headers, stop_sending_tie_headers) = result
        for tie_header in start_sending_tie_headers:
            self.try_to_transmit_tie(tie_header)
        for tie_header in request_tie_headers:
            self.request_tie(tie_header)
        for tie_header in stop_sending_tie_headers:
            self.remove_from_all_queues(tie_header)

    def process_received_tire_packet(self, tire_packet):
        self.debug(self._rx_log, "Receive TIRE packet {}".format(tire_packet))
        result = self._node.tie_db.process_received_tire_packet(tire_packet)
        (request_tie_headers, start_sending_tie_headers, acked_tie_headers) = result
        for tie_header in start_sending_tie_headers:
            self.try_to_transmit_tie(tie_header)
        for tie_header in request_tie_headers:
            self.request_tie(tie_header)
        for tie_header in acked_tie_headers:
            self.tie_been_acked(tie_header)

    def neighbor_direction(self):
        if self.neighbor is None:
            return None
        my_level = self._node.level_value()
        if self.neighbor.level > my_level:
            return neighbor.Neighbor.Direction.NORTH
        elif self.neighbor.level < my_level:
            return neighbor.Neighbor.Direction.SOUTH
        else:
            return neighbor.Neighbor.Direction.EAST_WEST

    def is_flood_reduced(self, _tie_header):
        # TODO: Implement this
        return False

    def is_request_allowed(self, tie_header, i_am_top_of_fabric):
        neighbor_direction = self.neighbor_direction()
        if neighbor_direction == neighbor.Neighbor.Direction.SOUTH:
            dir_str = "S"
        elif neighbor_direction == neighbor.Neighbor.Direction.NORTH:
            dir_str = "N"
        elif neighbor_direction == neighbor.Neighbor.Direction.EAST_WEST:
            dir_str = "EW"
        else:
            dir_str = "?"
        if neighbor_direction == neighbor.Neighbor.Direction.EAST_WEST:
            # If this node is top of fabric, then apply north scope rules, otherwise apply south
            # scope rules
            if i_am_top_of_fabric:
                neighbor_direction = neighbor.Neighbor.Direction.NORTH
            else:
                neighbor_direction = neighbor.Neighbor.Direction.SOUTH
            # Fall-through to next if block is intentional
        if neighbor_direction == neighbor.Neighbor.Direction.SOUTH:
            # Include all N-TIEs ...
            if tie_header.tieid.direction == common.ttypes.TieDirectionType.North:
                return (True, "to {}: include all N-TIEs".format(dir_str))
            # ... and all peer's self-originated TIEs ...
            if tie_header.tieid.originator == self.neighbor.system_id:
                return (True, "to {}: include peer self-originated".format(dir_str))
            # ... and all Node S-TIEs
            if ((tie_header.tieid.tietype == common.ttypes.TIETypeType.NodeTIEType) and
                    (tie_header.tieid.direction == common.ttypes.TieDirectionType.South)):
                return (True, "to {}: include node S-TIE".format(dir_str))
            # Exclude everything else
            return (False, "to {}: exclude".format(dir_str))
        if neighbor_direction == neighbor.Neighbor.Direction.NORTH:
            # Include only if neighbor is originator of TIE
            if tie_header.tieid.originator == self.neighbor.system_id:
                return (True, "to {}: TIE originator is equal to peer".format(dir_str))
            # Exclude everything else
            return (False, "to {}: exclude".format(dir_str))
        # Cannot determine direction of neighbor. Exclude.
        return (False, "to {}: exclude".format(dir_str))

    def is_request_filtered(self, tie_header):
        # The logic is more more easy to follow and mirrors the language of the flooding scope
        # rules (table 3) more closely if we ask the opposite question: is the request allowed?
        (allowed, reason) = self.is_request_allowed(tie_header, self._node.top_of_fabric())
        filtered = not allowed
        return (filtered, reason)

    def is_flood_filtered(self, tie_header):
        (allowed, reason) = self._node.tie_db.is_flood_allowed(
            tie_header=tie_header,
            neighbor_direction=self.neighbor_direction(),
            neighbor_system_id=self.neighbor.system_id,
            my_system_id=self._node.system_id,
            my_level=self._node.level_value(),
            i_am_top_of_fabric=self._node.top_of_fabric())
        filtered = not allowed
        return (filtered, reason)

    def try_to_transmit_tie(self, tie_header):
        (filtered, reason) = self.is_flood_filtered(tie_header)
        outcome = "filtered" if filtered else "allowed"
        self.debug(self._tx_log, ("Transmit TIE {} is {} because {}"
                                  .format(tie_header, outcome, reason)))
        if not filtered:
            self.remove_from_ties_rtx(tie_header)
            if tie_header.tieid in self._ties_ack:
                ack_header = self._ties_ack[tie_header.tieid]
                if ack_header.seq_nr < tie_header.seq_nr:
                    # ACK for older TIE is in queue, remove ACK from queue and send newer TIE
                    self.remove_from_ties_ack(ack_header)
                    self._ties_tx[tie_header.tieid] = tie_header
                else:
                    # ACK for newer TIE in in queue, keep ACK and don't send this older TIE
                    pass
            else:
                # No ACK in queue, send this TIE
                self._ties_tx[tie_header.tieid] = tie_header

    def ack_tie(self, tie_header):
        self.remove_from_all_queues(tie_header)
        self._ties_ack[tie_header.tieid] = tie_header

    def tie_been_acked(self, tie_header):
        self.remove_from_all_queues(tie_header)

    def remove_from_all_queues(self, tie_header):
        self.remove_from_ties_tx(tie_header)
        self.remove_from_ties_rtx(tie_header)
        self.remove_from_ties_req(tie_header)
        self.remove_from_ties_ack(tie_header)

    def clear_all_queues(self):
        self._ties_tx.clear()
        self._ties_rtx.clear()
        self._ties_req.clear()
        self._ties_ack.clear()

    def remove_from_ties_tx(self, tie_header):
        try:
            del self._ties_tx[tie_header.tieid]
        except KeyError:
            pass

    def remove_from_ties_rtx(self, tie_header):
        try:
            del self._ties_rtx[tie_header.tieid]
        except KeyError:
            pass

    def remove_from_ties_req(self, tie_header):
        try:
            del self._ties_req[tie_header.tieid]
        except KeyError:
            pass

    def remove_from_ties_ack(self, tie_header):
        try:
            del self._ties_ack[tie_header.tieid]
        except KeyError:
            pass

    def request_tie(self, tie_header):
        (filtered, reason) = self.is_request_filtered(tie_header)
        outcome = "excluded" if filtered else "included"
        self.debug(self._tx_log, ("Request TIE {} is {} in TIRE because {}"
                                  .format(tie_header, outcome, reason)))
        if not filtered:
            self.remove_from_all_queues(tie_header)
            self._ties_req[tie_header.tieid] = tie_header

    # TODO: Defined in spec, but never invoked
    def move_to_rtx_queue(self, tie_header):
        self.remove_from_ties_rtx(tie_header)
        self._ties_rtx[tie_header.tieid] = tie_header

    # TODO: Defined in spec, but never invoked
    def clear_requests(self, tie_header):
        self.remove_from_ties_req(tie_header)

    def service_queues(self):
        # TODO: For now, we have an extremely simplistic send queue service implementation. Once
        # per second we send all queued messages. Make this more sophisticated.
        if self._ties_ack:
            self.service_ties_ack()
        if self._ties_tx:
            self.service_ties_tx()
        if self._ties_rtx:
            self.service_ties_rtx()
        if self._ties_req:
            self.service_ties_req()

    def service_ties_ack(self):
        tire_packet = packet_common.make_tire_packet()
        for tie_header in self._ties_ack.values():
            packet_common.add_tie_header_to_tire(tire_packet, tie_header)
        packet_content = encoding.ttypes.PacketContent(tire=tire_packet)
        packet_header = encoding.ttypes.PacketHeader(
            sender=self._node.system_id,
            level=self._node.level_value())
        protocol_packet = encoding.ttypes.ProtocolPacket(
            header=packet_header,
            content=packet_content)
        self.send_protocol_packet(protocol_packet, flood=True, dont_change=False)

    def service_ties_queue(self, queue):
        # Note: we only look at the TIE-ID in the queue and not at the header. If we have a more
        # recent version of the TIE in the TIE-DB than the one requested, we send the one we have.
        packet_header = encoding.ttypes.PacketHeader(
            sender=self._node.system_id,
            level=self._node.level_value())
        packet_content = encoding.ttypes.PacketContent()
        protocol_packet = encoding.ttypes.ProtocolPacket(
            header=packet_header,
            content=packet_content)
        for tie_id in queue.keys():
            db_tie = self._node.tie_db.find_tie(tie_id)
            if db_tie is not None:
                protocol_packet.content.tie = db_tie
                self.send_protocol_packet(protocol_packet, flood=True, dont_change=True)

    def service_ties_tx(self):
        self.service_ties_queue(self._ties_tx)

    def service_ties_rtx(self):
        self.service_ties_queue(self._ties_rtx)

    def service_ties_req(self):
        tire_packet = packet_common.make_tire_packet()
        for tie_header in self._ties_req.values():
            packet_common.add_tie_header_to_tire(tire_packet, tie_header)
        packet_content = encoding.ttypes.PacketContent(tire=tire_packet)
        packet_header = encoding.ttypes.PacketHeader(
            sender=self._node.system_id,
            level=self._node.level_value())
        protocol_packet = encoding.ttypes.ProtocolPacket(
            header=packet_header,
            content=packet_content)
        self.send_protocol_packet(protocol_packet, flood=True, dont_change=False)

    @property
    def state_name(self):
        if self._fsm.state is None:
            return ""
        else:
            return self._fsm.state.name

    @property
    def fsm(self):
        return self._fsm

    @staticmethod
    def cli_summary_headers():
        return [
            ["Interface", "Name"],
            ["Neighbor", "Name"],
            ["Neighbor", "System ID"],
            ["Neighbor", "State"]]

    def cli_summary_attributes(self):
        if self.neighbor:
            return [
                self._interface_name,
                self.neighbor.name,
                utils.system_id_str(self.neighbor.system_id),
                self.state_name]
        else:
            return [
                self._interface_name,
                "",
                "",
                self.state_name]

    def cli_detailed_attributes(self):
        return [
            ["Interface Name", self._interface_name],
            ["Advertised Name", self._advertised_name],
            ["Interface IPv4 Address", self._ipv4_address],
            ["Metric", self._metric],
            ["Receive LIE IPv4 Multicast Address", self._rx_lie_ipv4_mcast_address],
            ["Transmit LIE IPv4 Multicast Address", self._tx_lie_ipv4_mcast_address],
            ["Receive LIE IPv6 Multicast Address", self._rx_lie_ipv6_mcast_address],
            ["Transmit LIE IPv6 Multicast Address", self._tx_lie_ipv6_mcast_address],
            ["Receive LIE Port", self._rx_lie_port],
            ["Transmit LIE Port", self._tx_lie_port],
            ["Receive TIE Port", self._rx_tie_port],
            ["System ID", utils.system_id_str(self._node.system_id)],
            ["Local ID", self._local_id],
            ["MTU", self._mtu],
            ["POD", self._pod],
            ["Failure", self.failure_str()],
            ["State", self.state_name],
            ["Received LIE Accepted or Rejected", self._lie_accept_or_reject],
            ["Received LIE Accept or Reject Reason", self._lie_accept_or_reject_rule],
            ["Neighbor", "True" if self.neighbor else "False"]
        ]

    def cli_detailed_neighbor_attrs(self):
        if self.neighbor:
            return self.neighbor.cli_detailed_attributes()
        else:
            return None

    def tie_headers_table_common(self, tie_headers):
        tab = table.Table()
        tab.add_row([
            "Direction",
            "Originator",
            "Type",
            "TIE Nr",
            "Seq Nr",
            ["Remaining", "Lifetime"],
            ["Origination", "Time"]])
        for tie_header in tie_headers.values():
            # TODO: Move direction_str etc. to packet_common
            tab.add_row([packet_common.direction_str(tie_header.tieid.direction),
                         tie_header.tieid.originator,
                         packet_common.tietype_str(tie_header.tieid.tietype),
                         tie_header.tieid.tie_nr,
                         tie_header.seq_nr,
                         tie_header.remaining_lifetime,
                         "-"])   # TODO: Report origination_time
        return tab

    def ties_tx_table(self):
        return self.tie_headers_table_common(self._ties_tx)

    def ties_rtx_table(self):
        return self.tie_headers_table_common(self._ties_rtx)

    def ties_req_table(self):
        return self.tie_headers_table_common(self._ties_req)

    def ties_ack_table(self):
        return self.tie_headers_table_common(self._ties_ack)
