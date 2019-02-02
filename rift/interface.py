# pylint:disable=too-many-lines

import collections
import enum
import logging
import random
import socket

import constants
import fsm
import neighbor
import offer
import packet_common
import table
import timer
import udp_rx_handler
import utils

import common.constants
import common.ttypes
import encoding.ttypes

USE_SIMPLE_REQUEST_FILTERING = True

# TODO: LIEs arriving with a TTL larger than 1 MUST be ignored.

# TODO: Implement configuration of POD numbers

# TODO: Send LIE packets with network control precedence.

# TODO: Have a mechanism to detect that an interface comes into / goes out of existence

# TODO: Have a mechanism to detect IPv4 or IPv6 address changes on an interface

class Interface:

    UNDEFINED_OR_ANY_POD = 0

    SERVICE_QUEUES_INTERVAL = 1.0

    def generate_advertised_name(self):
        return self._node.name + '-' + self.name

    def get_mtu(self):
        # TODO: Find a portable (or even non-portable) way to get the interface MTU
        # TODO: Find a way to be informed whenever the interface MTU changes
        # TODO: Check the hard-coded MTU value: 1400 or 1500
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
        rx_flood_port = self._rx_flood_port
        tx_flood_port = self.neighbor.flood_port
        # Use whatever IPv4 or IPv6 address we see first for the neighbor, preferring the IPv4
        # address if we know both.
        if self.neighbor.ipv4_address is not None:
            self.rx_info("Start IPv4 flooding: receive on port %d, send to address %s port %d",
                         rx_flood_port, self.neighbor.ipv4_address, tx_flood_port)
            self._flood_rx_ipv4_handler = udp_rx_handler.UdpRxHandler(
                interface_name=self.physical_interface_name,
                local_port=rx_flood_port,
                remote_address="0.0.0.0",  # TODO: Permissive... use neighbor address?
                receive_function=self.receive_flood_message,
                log=self._rx_log,
                log_id=self._log_id)
            self._flood_tx_ipv4_socket = self.create_socket_ipv4_tx_ucast(
                remote_address=self.neighbor.ipv4_address,
                port=tx_flood_port)
        else:
            assert self.neighbor.ipv6_address is not None
            scoped_ipv6_address = self.neighbor.ipv6_address
            if "%" not in self.neighbor.ipv6_address:
                scoped_ipv6_address += "%" + self.physical_interface_name
            self.rx_info("Start IPv6 flooding: receive on port %d, send to address %s port %d",
                         rx_flood_port, scoped_ipv6_address, tx_flood_port)
            self._flood_rx_ipv6_handler = udp_rx_handler.UdpRxHandler(
                interface_name=self.physical_interface_name,
                local_port=rx_flood_port,
                remote_address="::",  # TODO: Permissive... use neighbor address?
                receive_function=self.receive_flood_message,
                log=self._rx_log,
                log_id=self._log_id)
            self._flood_tx_ipv6_socket = self.create_socket_ipv6_tx_ucast(
                remote_address=scoped_ipv6_address,
                port=tx_flood_port)
        # Periodically start sending TIE packets and TIRE packets
        self._service_queues_timer.start()
        # Update the node TIEs originated by this node to include this neighbor
        self._node.regenerate_my_node_ties()
        # Update the south prefix TIE: we may have to start or stop originating a default route
        self._node.regenerate_my_south_prefix_tie()
        # We don't blindly send all TIEs to the neighbor because he might already have them. Instead
        # we send a TIDE packet right now. If our neighbor is missing a TIE that is in our database
        # he will request it after he receives the TIDE packet.
        self._node.send_tides_on_interface(self)

    def action_stop_flooding(self):
        # Stop sending TIE, TIRE, and TIDE packets to this neighbor
        self.rx_info("Stop flooding")
        self._service_queues_timer.stop()
        self.clear_all_queues()
        self._flood_rx_ipv4_handler.close()
        self._flood_rx_ipv4_handler = None
        self._flood_tx_ipv4_socket.close()
        self._flood_tx_ipv4_socket = None
        # Update the node TIEs originated by this node to exclude this neighbor. We have to pass
        # interface_going_down to regenerate_my_node_ties because the state of this interface is
        # still THREE_WAY at this point.
        self._node.regenerate_my_node_ties(interface_going_down=self)
        # Update the south prefix TIE: we may have to start or stop originating a default route
        self._node.regenerate_my_south_prefix_tie(interface_going_down=self)

    def log_tx_protocol_packet(self, level, sock, prelude, protocol_packet):
        if not self._tx_log.isEnabledFor(level):
            return
        packet_str = str(protocol_packet)
        type_str = self.protocol_packet_type(protocol_packet)
        if sock.family == socket.AF_INET:
            fam_str = "IPv4"
        else:
            assert sock.family == socket.AF_INET6
            fam_str = "IPv6"
        to_str = str(sock.getpeername())
        self._tx_log.log(level, "[%s] %s %s %s %s to %s" %
                         (self._log_id, prelude, fam_str, type_str, packet_str, to_str))

    def log_rx_protocol_packet(self, level, from_info, prelude, protocol_packet):
        if not self._rx_log.isEnabledFor(level):
            return
        if protocol_packet:
            packet_str = str(protocol_packet)
        else:
            packet_str = "?"
        type_str = self.protocol_packet_type(protocol_packet)
        if len(from_info) == 2:
            fam_str = "IPv4"
        else:
            assert len(from_info) == 4
            fam_str = "IPv6"
        from_str = str(from_info)
        self._rx_log.log(level, "[%s] %s %s %s %s from %s" %
                         (self._log_id, prelude, fam_str, type_str, packet_str, from_str))

    @staticmethod
    def protocol_packet_type(protocol_packet):
        types = []
        if protocol_packet.content.lie:
            types.append("LIE")
        if protocol_packet.content.tie:
            types.append("TIE")
        if protocol_packet.content.tide:
            types.append("TIDE")
        if protocol_packet.content.tire:
            types.append("TIRE")
        if types:
            return "+".join(types)
        else:
            return "No-Content"

    def send_protocol_packet(self, protocol_packet, flood):
        if flood:
            if self._flood_tx_ipv4_socket:
                socks = [self._flood_tx_ipv4_socket]
            else:
                assert self._flood_tx_ipv6_socket
                socks = [self._flood_tx_ipv6_socket]
        else:
            socks = [self._lie_tx_ipv4_socket, self._lie_tx_ipv6_socket]
        encoded_protocol_packet = packet_common.encode_protocol_packet(protocol_packet)
        for sock in socks:
            if sock is not None:
                if self._tx_fail:
                    self.log_tx_protocol_packet(logging.DEBUG, sock,
                                                "Simulated failure sending", protocol_packet)
                else:
                    try:
                        self.log_tx_protocol_packet(logging.DEBUG, sock, "Send", protocol_packet)
                        sock.send(encoded_protocol_packet)
                    except socket.error as error:
                        prelude = "Error {} sending".format(str(error))
                        self.log_tx_protocol_packet(logging.ERROR, sock, prelude, protocol_packet)

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
            local_id=self.local_id,
            flood_port=self._rx_flood_port,
            link_mtu_size=self._mtu,
            neighbor=lie_neighbor,
            pod=self._pod,
            nonce=Interface.generate_nonce(),
            capabilities=capabilities,
            holdtime=3,
            not_a_ztp_offer=self._node.send_not_a_ztp_offer_on_intf(self.name),
            you_are_flood_repeater=self._floodred_active,
            label=None)
        packet_content = encoding.ttypes.PacketContent(lie=lie_packet)
        protocol_packet = encoding.ttypes.ProtocolPacket(packet_header, packet_content)
        self.send_protocol_packet(protocol_packet, flood=False)
        tx_offer = offer.TxOffer(
            self.name,
            self._node.system_id,
            packet_header.level,
            lie_packet.not_a_ztp_offer,
            self.fsm.state)
        self._node.record_tx_offer(tx_offer)
        # If this was the first time that we sent out a LIE with you_are_flood_repeater=True,
        # inform the node that activation has been completed.
        if self._floodred_active and not self._floodred_active_confirmed:
            self._node.floodred_intf_activated(self)
            self._floodred_active_confirmed = True

    def action_cleanup(self):
        self.neighbor = None

    def check_reflection(self):
        # Does the received LIE packet (which is now stored in _neighbor) report us as the neighbor?
        if self.neighbor.neighbor_system_id != self._node.system_id:
            self.info("Neighbor does not report us as neighbor (system-id %s instead of %s",
                      utils.system_id_str(self.neighbor.neighbor_system_id),
                      utils.system_id_str(self._node.system_id))
            return False
        if self.neighbor.neighbor_link_id != self.local_id:
            self.info("Neighbor does not report us as neighbor (link-id %s instead of %s",
                      self.neighbor.neighbor_link_id, self.local_id)
            return False
        return True

    def check_three_way(self):
        # Section B.1.5
        # CHANGE: This is a little bit different from the specification
        # (see comment [CheckThreeWay])
        if self.fsm.state == self.State.ONE_WAY:
            pass
        elif self.fsm.state == self.State.TWO_WAY:
            if self.neighbor.neighbor_system_id is None:
                pass
            elif self.check_reflection():
                self.fsm.push_event(self.Event.VALID_REFLECTION)
            else:
                self.fsm.push_event(self.Event.MULTIPLE_NEIGHBORS)
        else: # state is THREE_WAY
            if self.neighbor.neighbor_system_id is None:
                self.fsm.push_event(self.Event.NEIGHBOR_DROPPED_REFLECTION)
            elif self.check_reflection():
                pass
            else:
                self.fsm.push_event(self.Event.MULTIPLE_NEIGHBORS)

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
            self.info(msg)
        return minor_change

    def send_offer_to_ztp_fsm(self, offering_neighbor):
        offer_for_ztp = offer.RxOffer(
            self.name,
            offering_neighbor.system_id,
            offering_neighbor.level,
            offering_neighbor.not_a_ztp_offer,
            self.fsm.state)
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
            self.rx_error(problem)
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
        # pylint:disable=too-many-statements
        (protocol_packet, from_info) = event_data
        from_address = from_info[0]
        from_port = from_info[1]
        # TODO: This is a simplistic way of implementing the hold timer. Use a real timer instead.
        self._time_ticks_since_lie_received = 0
        # Sections B.1.4.1 and B.1.4.2
        new_neighbor = neighbor.Neighbor(protocol_packet, from_address, from_port)
        (accept, rule, offer_to_ztp, warning) = self.is_received_lie_acceptable(protocol_packet)
        if not accept:
            self._lie_accept_or_reject = "Rejected"
            self._lie_accept_or_reject_rule = rule
            if warning:
                self.rx_warning("Received LIE packet rejected: %s", rule)
            else:
                self.rx_info("Received LIE packet rejected: %s", rule)
            self.action_cleanup()
            if offer_to_ztp:
                self.send_offer_to_ztp_fsm(new_neighbor)
                self.fsm.push_event(self.Event.UNACCEPTABLE_HEADER)
            return
        self._lie_accept_or_reject = "Accepted"
        self._lie_accept_or_reject_rule = rule
        # Section B.1.4.3
        # Note: We send an offer to the ZTP state machine directly from here instead of pushing an
        # UPDATE_ZTP_OFFER event (see deviation DEV-2 in doc/deviations)
        self.send_offer_to_ztp_fsm(new_neighbor)
        if not self.neighbor:
            self.info("New neighbor detected with system-id %s",
                      utils.system_id_str(protocol_packet.header.sender))
            self.neighbor = new_neighbor
            self.fsm.push_event(self.Event.NEW_NEIGHBOR)
            self.check_three_way()
            return
        # Section B.1.4.3.1
        if new_neighbor.system_id != self.neighbor.system_id:
            self.info("Neighbor system-id changed from %s to %s",
                      utils.system_id_str(self.neighbor.system_id),
                      utils.system_id_str(new_neighbor.system_id))
            self.fsm.push_event(self.Event.MULTIPLE_NEIGHBORS)
            return
        # Section B.1.4.3.2
        if new_neighbor.level != self.neighbor.level:
            self.info("Neighbor level changed from %s to %s", self.neighbor.level,
                      new_neighbor.level)
            self.fsm.push_event(self.Event.NEIGHBOR_CHANGED_LEVEL)
            return
        # Section B.1.4.3.3
        if new_neighbor.ipv4_address is not None:
            # We received an IPv4 LIE.
            new_neighbor.ipv6_address = self.neighbor.ipv6_address
            if self.neighbor.ipv4_address is None:
                self.neighbor.ipv4_address = new_neighbor.ipv4_address
                reason = ("Neighbor on interface {} got new IPv4 address {}"
                          .format(self.name, new_neighbor.ipv4_address))
                self._node.trigger_spf(reason)
            elif self.neighbor.ipv4_address != new_neighbor.ipv4_address:
                self.info("Neighbor IPv4 address changed from %s to %s",
                          self.neighbor.ipv4_address, new_neighbor.ipv4_address)
                self.fsm.push_event(self.Event.NEIGHBOR_CHANGED_ADDRESS)
                return
        else:
            # We received an IPv6 LIE.
            assert new_neighbor.ipv6_address is not None
            new_neighbor.ipv4_address = self.neighbor.ipv4_address
            if self.neighbor.ipv6_address is None:
                self.neighbor.ipv6_address = new_neighbor.ipv6_address
                reason = ("Neighbor on interface {} got new IPv6 address {}"
                          .format(self.name, new_neighbor.ipv6_address))
                self._node.trigger_spf(reason)
            elif self.neighbor.ipv6_address != new_neighbor.ipv6_address:
                self.info("Neighbor IPv6 address changed from %s to %s",
                          self.neighbor.ipv6_address, new_neighbor.ipv6_address)
                self.fsm.push_event(self.Event.NEIGHBOR_CHANGED_ADDRESS)
                return
        # Section B.1.4.3.4
        if self.check_minor_change(new_neighbor):
            self.fsm.push_event(self.Event.NEIGHBOR_CHANGED_MINOR_FIELDS)
        self.neighbor = new_neighbor
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
            self.fsm.push_event(self.Event.HOLD_TIME_EXPIRED)

    def action_hold_time_expired(self):
        self._node.expire_offer(self.name)

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

    def info(self, msg, *args):
        self._log.info("[%s] %s" % (self._log_id, msg), *args)

    def warning(self, msg, *args):
        self._log.warning("[%s] %s" % (self._log_id, msg), *args)

    def rx_debug(self, msg, *args):
        self._rx_log.debug("[%s] %s" % (self._log_id, msg), *args)

    def rx_info(self, msg, *args):
        self._rx_log.info("[%s] %s" % (self._log_id, msg), *args)

    def rx_warning(self, msg, *args):
        self._rx_log.warning("[%s] %s" % (self._log_id, msg), *args)

    def rx_error(self, msg, *args):
        self._rx_log.error("[%s] %s" % (self._log_id, msg), *args)

    def tx_debug(self, msg, *args):
        self._tx_log.debug("[%s] %s" % (self._log_id, msg), *args)

    def __init__(self, node, config):
        # pylint:disable=too-many-statements
        # TODO: process bandwidth field in config
        self._node = node
        self._engine = node.engine
        self.name = config['name']
        self._log_id = node.log_id + "-{}".format(self.name)
        self._log = node.log.getChild("if")
        if self._engine.simulated_interfaces and self._engine.physical_interface_name:
            self.physical_interface_name = self._engine.physical_interface_name
        else:
            self.physical_interface_name = self.name
        # TODO: Make the default metric/bandwidth depend on the speed of the interface
        self._metric = self.get_config_attribute(config, 'metric',
                                                 common.constants.default_bandwidth)
        self._advertised_name = self.generate_advertised_name()
        self._ipv4_address = utils.interface_ipv4_address(self.physical_interface_name)
        self._ipv6_address = utils.interface_ipv6_address(self.physical_interface_name)
        try:
            self._interface_index = socket.if_nametoindex(self.physical_interface_name)
        except IOError as err:
            self.warning("Could determine index of interface %s: %s",
                         self.physical_interface_name, err)
            self._interface_index = None
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
        self._rx_flood_port = self.get_config_attribute(config, 'rx_tie_port',
                                                        constants.DEFAULT_TIE_PORT)
        self._rx_fail = False
        self._tx_fail = False
        self.info("Create interface")
        self._rx_log = self._log.getChild("rx")
        self._tx_log = self._log.getChild("tx")
        self._fsm_log = self._log.getChild("fsm")
        self.local_id = node.allocate_interface_id()
        self._mtu = self.get_mtu()
        self._pod = self.UNDEFINED_OR_ANY_POD
        self.neighbor = None
        self._time_ticks_since_lie_received = None
        self._lie_accept_or_reject = "No LIE Received"
        self._lie_accept_or_reject_rule = "-"
        self._lie_tx_ipv4_socket = None
        self._lie_tx_ipv6_socket = None
        self._lie_rx_ipv4_handler = None
        self._lie_rx_ipv6_handler = None
        self._flood_tx_ipv4_socket = None
        self._flood_tx_ipv6_socket = None
        self._flood_rx_ipv4_handler = None
        self._flood_rx_ipv6_handler = None
        # The following queues (ties_tx, ties_rtx, ties_req, are ties_ack) are ordered dictionaries.
        # The value is the header of the TIE. The index is the TIE-ID want to have two headers with
        # same TIE-ID in the queue. The ordering is needed because we want to service the entries
        # in the queue in the same order in which they were added (FIFO).
        # TODO: For _ties_rtx, add time to retransmit to retransmit queue
        self._ties_tx = collections.OrderedDict()
        self._ties_rtx = collections.OrderedDict()
        self._ties_req = collections.OrderedDict()
        self._ties_ack = collections.OrderedDict()
        self._floodred_active = False
        self._floodred_active_confirmed = False
        self.fsm = fsm.Fsm(
            definition=self.fsm_definition,
            action_handler=self,
            log=self._fsm_log,
            log_id=self._log_id)
        if self._node.running:
            self.run()
            self.fsm.start()

    def run(self):
        self._lie_tx_ipv4_socket = self.create_socket_ipv4_tx_mcast(
            multicast_address=self._tx_lie_ipv4_mcast_address,
            port=self._tx_lie_port,
            loopback=self._node.engine.ipv4_multicast_loopback)
        self._lie_tx_ipv6_socket = self.create_socket_ipv6_tx_mcast(
            multicast_address=self._tx_lie_ipv6_mcast_address,
            port=self._tx_lie_port,
            loopback=self._node.engine.ipv6_multicast_loopback)
        self._lie_rx_ipv4_handler = udp_rx_handler.UdpRxHandler(
            interface_name=self.physical_interface_name,
            local_port=self._rx_lie_port,
            remote_address=self._rx_lie_ipv4_mcast_address,
            receive_function=self.receive_lie_message,
            log=self._rx_log,
            log_id=self._log_id)
        self._lie_rx_ipv6_handler = udp_rx_handler.UdpRxHandler(
            interface_name=self.physical_interface_name,
            local_port=self._rx_lie_port,
            remote_address=self._rx_lie_ipv6_mcast_address,
            receive_function=self.receive_lie_message,
            log=self._rx_log,
            log_id=self._log_id)
        self._flood_rx_ipv4_handler = None
        self._flood_tx_ipv4_socket = None
        self._one_second_timer = timer.Timer(
            1.0,
            lambda: self.fsm.push_event(self.Event.TIMER_TICK))
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

    def receive_message_common(self, message, from_info):
        protocol_packet = packet_common.decode_protocol_packet(message)
        if protocol_packet is None:
            self.log_rx_protocol_packet(logging.ERROR, from_info,
                                        "Could not decode", protocol_packet)
            return None
        if self._rx_fail:
            self.log_rx_protocol_packet(logging.DEBUG, from_info,
                                        "Simulated failure receiving", protocol_packet)
            return None
        if protocol_packet.header.sender == self._node.system_id:
            self.log_rx_protocol_packet(logging.DEBUG, from_info,
                                        "Ignore looped receive", protocol_packet)
            return None
        self.log_rx_protocol_packet(logging.DEBUG, from_info, "Receive", protocol_packet)
        if not protocol_packet.content:
            self.log_rx_protocol_packet(logging.WARNING, from_info,
                                        "Received contentless", protocol_packet)
            return None
        if protocol_packet.header.major_version != constants.RIFT_MAJOR_VERSION:
            self.rx_error("Received different major protocol version from %s (local version %d, "
                          "remote version %d)", from_info, constants.RIFT_MAJOR_VERSION,
                          protocol_packet.header.major_version)
            return None
        return protocol_packet

    def receive_lie_message(self, message, from_info):
        protocol_packet = self.receive_message_common(message, from_info)
        if protocol_packet is None:
            return
        if protocol_packet.content.lie:
            event_data = (protocol_packet, from_info)
            self.fsm.push_event(self.Event.LIE_RECEIVED, event_data)
        else:
            self.rx_warning("Received packet without LIE content on LIE port (ignored)")
        if protocol_packet.content.tie:
            self.rx_warning("Received TIE packet on LIE port (ignored)")
        if protocol_packet.content.tide:
            self.rx_warning("Received TIDE packet on LIE port (ignored)")
        if protocol_packet.content.tire:
            self.rx_warning("Received TIRE packet on LIE port (ignored)")

    def receive_flood_message(self, message, from_info):
        protocol_packet = self.receive_message_common(message, from_info)
        if protocol_packet is None:
            return
        flood_content = False
        if protocol_packet.content.tie is not None:
            self.process_received_tie_packet(protocol_packet.content.tie)
            flood_content = True
        if protocol_packet.content.tide:
            self.process_received_tide_packet(protocol_packet.content.tide)
            flood_content = True
        if protocol_packet.content.tire:
            self.process_received_tire_packet(protocol_packet.content.tire)
            flood_content = True
        if protocol_packet.content.lie:
            self.rx_warning("Received LIE packet on flood port (ignored)")
        else:
            if not flood_content:
                self.rx_warning("Received packet without TIE/TIDE/TIRE content on flood port "
                                "(ignored)")

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
        self.rx_debug("Receive TIE packet %s", tie_packet)
        result = self._node.process_received_tie_packet(tie_packet)
        (start_sending_tie_header, ack_tie_header) = result
        if start_sending_tie_header is not None:
            self.try_to_transmit_tie(start_sending_tie_header)
        if ack_tie_header is not None:
            self.ack_tie(ack_tie_header)

    def process_received_tide_packet(self, tide_packet):
        result = self._node.process_received_tide_packet(tide_packet)
        (request_tie_headers, start_sending_tie_headers, stop_sending_tie_headers) = result
        for tie_header in start_sending_tie_headers:
            self.try_to_transmit_tie(tie_header)
        for tie_header in request_tie_headers:
            self.request_tie(tie_header)
        for tie_header in stop_sending_tie_headers:
            self.remove_from_all_queues(tie_header)

    def process_received_tire_packet(self, tire_packet):
        self.rx_debug("Receive TIRE packet %s", tire_packet)
        result = self._node.process_received_tire_packet(tire_packet)
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
            return constants.DIR_NORTH
        elif self.neighbor.level < my_level:
            return constants.DIR_SOUTH
        else:
            return constants.DIR_EAST_WEST

    def is_flood_reduced(self, _tie_header):
        # TODO: Implement this
        return False

    # The basic idea for the next two functions (is_request_allowed_...) is that we should not
    # request any TIEs from our neighbor if the neighbor is not allowed to send the TIE to us
    # according to the scoping rules. If have two different implementations of this.

    # This is the first implementation of is_request_allowed. It follows the letter of the draft
    # specification.
    #
    def is_request_allowed_complex(self, tie_header, i_am_top_of_fabric):
        neighbor_direction = self.neighbor_direction()
        if neighbor_direction == constants.DIR_SOUTH:
            dir_str = "S"
        elif neighbor_direction == constants.DIR_NORTH:
            dir_str = "N"
        elif neighbor_direction == constants.DIR_EAST_WEST:
            dir_str = "EW"
        else:
            dir_str = "?"
        if neighbor_direction == constants.DIR_EAST_WEST:
            # If this node is top of fabric, then apply north scope rules, otherwise apply south
            # scope rules
            if i_am_top_of_fabric:
                neighbor_direction = constants.DIR_NORTH
            else:
                neighbor_direction = constants.DIR_SOUTH
            # Fall-through to next if block is intentional
        if neighbor_direction == constants.DIR_SOUTH:
            # Request all N-TIEs ...
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
        if neighbor_direction == constants.DIR_NORTH:
            # Request all S-TIEs
            if tie_header.tieid.direction == common.ttypes.TieDirectionType.South:
                return (True, "to {}: include all S-TIEs".format(dir_str))
            # Exclude everything else
            return (False, "to {}: exclude".format(dir_str))
        # Cannot determine direction of neighbor. Exclude.
        return (False, "to {}: exclude".format(dir_str))

    # This is the simplified implementation of s_request_allowed as described in "the solution to
    # oscillation #2" in slide deck http://bit.ly/rift-flooding-oscillations-v1. During the RIFT
    # core team conference call on 19 Oct 2018, Tony reported it was his intent to apply the same
    # logic. However, this seems like a simpler (and less error prone) way to achieve that.
    #
    def is_request_allowed_simple(self, tie_header, _i_am_top_of_fabric):
        return self._node.flood_allowed_from_nbr_to_node(
            tie_header,
            self.neighbor_direction(),
            self.neighbor.system_id,
            self.neighbor.level,
            self.neighbor.top_of_fabric(),
            self._node.system_id)

    def is_request_allowed(self, tie_header, i_am_top_of_fabric):
        if USE_SIMPLE_REQUEST_FILTERING:
            return self.is_request_allowed_simple(tie_header, i_am_top_of_fabric)
        else:
            return self.is_request_allowed_complex(tie_header, i_am_top_of_fabric)

    def is_request_filtered(self, tie_header):
        # The logic is more more easy to follow and mirrors the language of the flooding scope
        # rules (table 3) more closely if we ask the opposite question: is the request allowed?
        (allowed, reason) = self.is_request_allowed(tie_header, self._node.top_of_fabric())
        filtered = not allowed
        return (filtered, reason)

    def is_flood_filtered(self, tie_header):
        (allowed, reason) = self._node.is_flood_allowed(
            tie_header=tie_header,
            to_node_direction=self.neighbor_direction(),
            to_node_system_id=self.neighbor.system_id,
            from_node_system_id=self._node.system_id,
            from_node_level=self._node.level_value(),
            from_node_is_top_of_fabric=self._node.top_of_fabric())
        filtered = not allowed
        return (filtered, reason)

    def add_to_ties_tx(self, tie_header):
        # If the TIE is not already on the send queue or if the TIE is a newer version than what's
        # already on the send queue, then send it immediately instead of (in addition to, really)
        # waiting for the next service timer.
        if tie_header.tieid not in self._ties_tx:
            send_now = True
        elif tie_header.seq_nr > self._ties_tx[tie_header.tieid].seq_nr:
            send_now = True
        else:
            send_now = False
        self._ties_tx[tie_header.tieid] = tie_header
        if send_now:
            db_tie = self._node.find_tie(tie_header.tieid)
            if db_tie is not None:
                packet_header = encoding.ttypes.PacketHeader(
                    sender=self._node.system_id,
                    level=self._node.level_value())
                packet_content = encoding.ttypes.PacketContent()
                protocol_packet = encoding.ttypes.ProtocolPacket(
                    header=packet_header,
                    content=packet_content)
                protocol_packet.content.tie = db_tie
                self.send_protocol_packet(protocol_packet, flood=True)

    def try_to_transmit_tie(self, tie_header):
        (filtered, reason) = self.is_flood_filtered(tie_header)
        outcome = "filtered" if filtered else "allowed"
        self.tx_debug("Transmit TIE %s is %s because %s", tie_header, outcome, reason)
        if not filtered:
            self.remove_from_ties_rtx(tie_header)
            if tie_header.tieid in self._ties_ack:
                ack_header = self._ties_ack[tie_header.tieid]
                if ack_header.seq_nr < tie_header.seq_nr:
                    # ACK for older TIE is in queue, remove ACK from queue and send newer TIE
                    self.remove_from_ties_ack(ack_header)
                    self.add_to_ties_tx(tie_header)
                else:
                    # ACK for newer TIE in in queue, keep ACK and don't send this older TIE
                    pass
            else:
                # No ACK in queue, send this TIE
                self.add_to_ties_tx(tie_header)

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
        self.tx_debug("Request TIE %s is %s in TIRE because %s", tie_header, outcome, reason)
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
        # We always send an ACK for every TIE header on the ACK queue. I.e. we always ACK the TIEs
        # that we received and accepted.
        for tie_header in self._ties_ack.values():
            packet_common.add_tie_header_to_tire(tire_packet, tie_header)
        packet_content = encoding.ttypes.PacketContent(tire=tire_packet)
        packet_header = encoding.ttypes.PacketHeader(
            sender=self._node.system_id,
            level=self._node.level_value())
        protocol_packet = encoding.ttypes.ProtocolPacket(
            header=packet_header,
            content=packet_content)
        self.send_protocol_packet(protocol_packet, flood=True)

    def service_ties_req(self):
        tire_packet = packet_common.make_tire_packet()
        for tie_header in self._ties_req.values():
            # We don't request a TIE from our neighbor if the flooding scope rules say that the
            # neighbor is not allowed to flood the TIE to us. Why? Because the neighbor is allowed
            # to advertise extra TIEs in the TIDE, and if we request them we will get an
            # oscillation.
            (allowed, _reason) = self._node.flood_allowed_from_nbr_to_node(
                tie_header,
                self.neighbor_direction(),
                self.neighbor.system_id,
                self.neighbor.level,
                self.neighbor.top_of_fabric(),
                self._node.system_id)
            if allowed:
                packet_common.add_tie_header_to_tire(tire_packet, tie_header)
            else:
                # TODO: log message
                pass
        packet_content = encoding.ttypes.PacketContent(tire=tire_packet)
        packet_header = encoding.ttypes.PacketHeader(
            sender=self._node.system_id,
            level=self._node.level_value())
        protocol_packet = encoding.ttypes.ProtocolPacket(
            header=packet_header,
            content=packet_content)
        self.send_protocol_packet(protocol_packet, flood=True)

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
            db_tie = self._node.find_tie(tie_id)
            if db_tie is not None:
                protocol_packet.content.tie = db_tie
                self.send_protocol_packet(protocol_packet, flood=True)

    def service_ties_tx(self):
        self.service_ties_queue(self._ties_tx)

    def service_ties_rtx(self):
        self.service_ties_queue(self._ties_rtx)

    @property
    def state_name(self):
        if self.fsm.state is None:
            return ""
        else:
            return self.fsm.state.name

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
                self.name,
                self.neighbor.name,
                utils.system_id_str(self.neighbor.system_id),
                self.state_name]
        else:
            return [
                self.name,
                "",
                "",
                self.state_name]

    def cli_detailed_attributes(self):
        if self._floodred_active:
            if self._floodred_active_confirmed:
                flood_repeater_str = "True"
            else:
                flood_repeater_str = "Pending"
        else:
            flood_repeater_str = "False"
        return [
            ["Interface Name", self.name],
            ["Physical Interface Name", self.physical_interface_name],
            ["Advertised Name", self._advertised_name],
            ["Interface IPv4 Address", self._ipv4_address],
            ["Interface IPv6 Address", self._ipv6_address],
            ["Interface Index", self._interface_index],
            ["Metric", self._metric],
            ["LIE Recieve IPv4 Multicast Address", self._rx_lie_ipv4_mcast_address],
            ["LIE Receive IPv6 Multicast Address", self._rx_lie_ipv6_mcast_address],
            ["LIE Receive Port", self._rx_lie_port],
            ["LIE Transmit IPv4 Multicast Address", self._tx_lie_ipv4_mcast_address],
            ["LIE Transmit IPv6 Multicast Address", self._tx_lie_ipv6_mcast_address],
            ["LIE Transmit Port", self._tx_lie_port],
            ["Flooding Receive Port", self._rx_flood_port],
            ["System ID", utils.system_id_str(self._node.system_id)],
            ["Local ID", self.local_id],
            ["MTU", self._mtu],
            ["POD", self._pod],
            ["Failure", self.failure_str()],
            ["State", self.state_name],
            ["Received LIE Accepted or Rejected", self._lie_accept_or_reject],
            ["Received LIE Accept or Reject Reason", self._lie_accept_or_reject_rule],
            ["Neighbor", "True" if self.neighbor else "False"],
            ["Flood Repeater", flood_repeater_str]
        ]

    def cli_detailed_neighbor_attrs(self):
        if self.neighbor:
            return self.neighbor.cli_detailed_attributes()
        else:
            return None

    @staticmethod
    def add_socket_to_table(tab, traffic, direction, family, sock):
        local_name = sock.getsockname()
        local_address = local_name[0]
        local_port = local_name[1]
        try:
            remote_name = sock.getpeername()
            remote_address = remote_name[0]
            remote_port = remote_name[1]
        except OSError:
            # Receive UDP sockets trow an OSError if they are not connected
            remote_address = "Any"
            remote_port = "Any"
        tab.add_row([traffic,
                     direction,
                     family,
                     str(local_address),
                     local_port,
                     str(remote_address),
                     remote_port])
        return tab

    def sockets_table(self):
        tab = table.Table()
        tab.add_row([
            "Traffic",
            "Direction",
            "Family",
            "Local Address",
            "Local Port",
            "Remote Address",
            "Remote Port"])
        if self._lie_rx_ipv4_handler and self._lie_rx_ipv4_handler.sock:
            self.add_socket_to_table(tab, "LIEs", "Receive", "IPv4", self._lie_rx_ipv4_handler.sock)
        if self._lie_rx_ipv6_handler and self._lie_rx_ipv6_handler.sock:
            self.add_socket_to_table(tab, "LIEs", "Receive", "IPv6", self._lie_rx_ipv6_handler.sock)
        if self._lie_tx_ipv4_socket:
            self.add_socket_to_table(tab, "LIEs", "Send", "IPv4", self._lie_tx_ipv4_socket)
        if self._lie_tx_ipv6_socket:
            self.add_socket_to_table(tab, "LIEs", "Send", "IPv6", self._lie_tx_ipv6_socket)
        if self._flood_rx_ipv4_handler and self._flood_rx_ipv4_handler.sock:
            self.add_socket_to_table(tab, "Flooding", "Receive", "IPv4",
                                     self._flood_rx_ipv4_handler.sock)
        if self._flood_rx_ipv6_handler and self._flood_rx_ipv6_handler.sock:
            self.add_socket_to_table(tab, "Flooding", "Receive", "IPv6",
                                     self._flood_rx_ipv6_handler.sock)
        if self._flood_tx_ipv4_socket:
            self.add_socket_to_table(tab, "Flooding", "Send", "IPv4", self._flood_tx_ipv4_socket)
        if self._flood_tx_ipv6_socket:
            self.add_socket_to_table(tab, "Flooding", "Send", "IPv6", self._flood_tx_ipv6_socket)
        return tab

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

    # TODO: Set TTL as follows:
    # ttl_bin = struct.pack('@i', MYTTL)
    # if addrinfo[0] == socket.AF_INET: # IPv4
    #     s.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl_bin)
    # else:
    #     s.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_MULTICAST_HOPS, ttl_bin)

    # TODO: Set TOS and Priority

    @staticmethod
    def enable_addr_and_port_reuse(sock):
        # Ignore exceptions because not all operating systems support these. If not setting the
        # REUSE... option causes trouble, that will be caught later on.
        try:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        except AttributeError:
            pass
        try:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        except AttributeError:
            pass

    def socket_connect(self, sock, address, port):
        try:
            sock.connect((address, port))
            return True
        except IOError as err:
            self.warning("Could not connect UDP socket to address %s port %d: %s",
                         address, port, err)
        return False

    def create_socket_ipv4_tx_mcast(self, multicast_address, port, loopback):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        except IOError as err:
            self.warning("Could not create IPv4 UDP socket: %s", err)
            return None
        self.enable_addr_and_port_reuse(sock)
        if self._ipv4_address is not None:
            try:
                sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_IF,
                                socket.inet_aton(self._ipv4_address))
            except IOError as err:
                self.warning("Could not set IPv6 multicast interface address %s: %s",
                             self._ipv4_address, err)
                return None
        try:
            loop_value = 1 if loopback else 0
            sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_LOOP, loop_value)
        except IOError as err:
            self.warning("Could not set IPv4 multicast loopback value %d: %s", loop_value, err)
            return None
        try:
            sock.connect((multicast_address, port))
        except IOError as err:
            self.warning("Could not connect UDP socket to address %s port %d: %s",
                         multicast_address, port, err)
            return None
        return sock

    def create_socket_ipv4_tx_ucast(self, remote_address, port):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        except IOError as err:
            self.warning("Could not create IPv4 UDP socket: %s", err)
            return None
        self.enable_addr_and_port_reuse(sock)
        try:
            sock.connect((remote_address, port))
        except IOError as err:
            self.warning("Could not connect UDP socket to address %s port %d: %s",
                         remote_address, port, err)
            return None
        return sock

    def create_socket_ipv6_tx_mcast(self, multicast_address, port, loopback):
        if self._interface_index is None:
            self.warning("Could not create IPv6 multicast TX socket: unknown interface index")
            return None
        try:
            sock = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        except IOError as err:
            self.warning("Could not create IPv6 UDP socket: %s", err)
            return None
        self.enable_addr_and_port_reuse(sock)
        try:
            sock.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_MULTICAST_IF, self._interface_index)
        except IOError as err:
            self.warning("Could not set IPv6 multicast interface index %d: %s",
                         self._interface_index, err)
            return None
        try:
            loop_value = 1 if loopback else 0
            sock.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_MULTICAST_LOOP, loop_value)
        except IOError as err:
            self.warning("Could not set IPv6 multicast loopback value %d: %s", loop_value, err)
            return None
        try:
            sock.connect((multicast_address, port))
        except IOError as err:
            self.warning("Could not connect UDP socket to address %s port %d: %s",
                         multicast_address, port, err)
            return None
        return sock

    def create_socket_ipv6_tx_ucast(self, remote_address, port):
        try:
            sock = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        except IOError as err:
            self.warning("Could not create IPv6 UDP socket: %s", err)
            return None
        self.enable_addr_and_port_reuse(sock)
        try:
            sock_addr = socket.getaddrinfo(remote_address, port, socket.AF_INET6,
                                           socket.SOCK_DGRAM)[0][4]
            sock.connect(sock_addr)
        except IOError as err:
            self.warning("Could not connect UDP socket to address %s port %d: %s",
                         remote_address, port, err)
            return None
        return sock

    def activate_flood_repeater(self):
        assert not self._floodred_active
        self._floodred_active = True
        self._floodred_active_confirmed = False

    def deactivate_flood_repeater(self):
        assert self._floodred_active
        self._floodred_active = False
        self._floodred_active_confirmed = False
