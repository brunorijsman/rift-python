# pylint:disable=too-many-lines

import collections
import datetime
import enum
import errno
import logging
import random
import socket

import constants
import fsm
import msg_queues
import neighbor
import offer
import packet_common
import stats
import table
import timer
import udp_rx_handler
import utils

import common.constants
import common.ttypes
import encoding.ttypes

from encoding.constants import protocol_minor_version

USE_SIMPLE_REQUEST_FILTERING = True

class PacketTrace:

    def __init__(self, direction, local_address, remote_address, packet_info):
        self.timestamp = datetime.datetime.now()
        self.direction = direction
        self.local_address = local_address
        self.remote_address = remote_address
        self.packet_info = packet_info

    def timestamp_str(self, prev_packet):
        meta_str = "direction=" + self.direction
        meta_str += "  timestamp={}".format(self.timestamp.strftime("%Y-%m-%d-%H:%M:%S.%f"))
        if prev_packet:
            second_since_prev_packet = (prev_packet.timestamp - self.timestamp).total_seconds()
            meta_str += "  seconds-since-prev={:.4f}".format(second_since_prev_packet)
        return meta_str

    def addresses_str(self):
        local_address_str = "{}:{}".format(self.local_address[0], self.local_address[1])
        remote_address_str = "{}:{}".format(self.remote_address[0], self.remote_address[1])
        return "local-address={}  remote_address={}".format(local_address_str, remote_address_str)

class Interface:

    UNDEFINED_OR_ANY_POD = 0

    INCREASE_TX_NONCE_LOCAL_HOLDDOWN_TIME = 60.0

    MAX_PACKET_TRACE = 20

    def generate_advertised_name(self):
        return self.node.name + ':' + self.name

    def get_mtu(self):
        mtu = 1400
        return mtu

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

    class NbrIsFRState(enum.Enum):
        NOT_APPLICABLE = 0  # Neighbor is not in state 3-way etc.
        FALSE = 1           # Neighbor is not flood repeater
        TRUE = 2            # Neighbor is flood repeater
        PENDING_FALSE = 3   # Neighbor has recently been elected to stop being a flood repeater;
                            # Pending until the new flood repeater is announced to the neighbor
                            # This is for graceful switch-over from old to new flood repeaters
        PENDING_TRUE = 4    # Neighbor has recently been elected to start being a flood repeater;
                            # Pending until we send the first LIE with you_are_flood_repeater=True

    @staticmethod
    def nbr_is_fr_str(state):
        if state == Interface.NbrIsFRState.NOT_APPLICABLE:
            return "Not Applicable"
        elif state == Interface.NbrIsFRState.FALSE:
            return "False"
        elif state == Interface.NbrIsFRState.TRUE:
            return "True"
        elif state == Interface.NbrIsFRState.PENDING_FALSE:
            return "False (Pending)"
        else:
            assert state == Interface.NbrIsFRState.PENDING_TRUE
            return "True (Pending)"

    @staticmethod
    def nbr_is_fr_bool(state):
        # Only send you_are_flood_repeater=True to neighbor in the following states:
        return state in [Interface.NbrIsFRState.TRUE,
                         Interface.NbrIsFRState.PENDING_TRUE,
                         Interface.NbrIsFRState.PENDING_FALSE]

    def action_store_hal(self):
        pass

    def action_store_hat(self):
        pass

    def action_store_hals(self):
        pass

    def action_update_level(self):
        pass

    def action_start_flooding(self):
        # Start sending TIE, TIRE, and TIDE packets to this neighbor
        rx_flood_port = self._rx_flood_port
        tx_flood_port = self.neighbor.flood_port
        # For sending flooding packets, use whatever IPv4 or IPv6 address we see first for the
        # neighbor, preferring the IPv4 address if we know both.
        if self.neighbor.ipv4_address is not None:
            self.rx_info("Start IPv4 flooding: send to address %s port %d",
                         self.neighbor.ipv4_address, tx_flood_port)
            self._flood_tx_ipv4_socket = self.create_socket_ipv4_tx_ucast(
                remote_address=self.neighbor.ipv4_address,
                port=tx_flood_port)
        else:
            assert self.neighbor.ipv6_address is not None
            scoped_ipv6_address = self.neighbor.ipv6_address
            if "%" not in self.neighbor.ipv6_address:
                scoped_ipv6_address += "%" + self.physical_interface_name
            self.rx_info("Start IPv6 flooding: send to address %s port %d",
                         scoped_ipv6_address, tx_flood_port)
            self._flood_tx_ipv6_socket = self.create_socket_ipv6_tx_ucast(
                remote_address=scoped_ipv6_address,
                port=tx_flood_port)
        # For *receiving* flooding packets, always listen on both IPv4 and also on IPv6 since we
        # don't know whether the same will choose to send on IPv4 or on IPv6
        self.rx_info("Start IPv4 flooding: receive on port %d", rx_flood_port)
        self._flood_rx_ipv4_handler = udp_rx_handler.UdpRxHandler(
            interface_name=self.physical_interface_name,
            local_port=rx_flood_port,
            ipv4=True,
            multicast_address=None,
            remote_address="0.0.0.0",
            receive_function=self.receive_flood_message,
            log=self._rx_log,
            log_id=self._log_id)
        self.rx_info("Start IPv6 flooding: receive on port %d", rx_flood_port)
        self._flood_rx_ipv6_handler = udp_rx_handler.UdpRxHandler(
            interface_name=self.physical_interface_name,
            local_port=rx_flood_port,
            ipv4=False,
            multicast_address=None,
            remote_address="::",
            receive_function=self.receive_flood_message,
            log=self._rx_log,
            log_id=self._log_id)
        # Update the node TIEs originated by this node to include this neighbor
        self.node.regenerate_my_node_ties()
        # Update the south prefix TIE: we may have to start or stop originating a default route
        self.node.regenerate_my_south_prefix_tie()
        # We don't blindly send all TIEs to the neighbor because he might already have them. Instead
        # we send a TIDE packet right now. If our neighbor is missing a TIE that is in our database
        # he will request it after he receives the TIDE packet.
        self.node.send_tides_on_interface(self)

    def action_stop_flooding(self):
        # Stop sending TIE, TIRE, and TIDE packets to this neighbor
        self.rx_info("Stop flooding")
        self._queues.clear_all_queues()
        if self._flood_rx_ipv4_handler:
            self._flood_rx_ipv4_handler.close()
            self._flood_rx_ipv4_handler = None
        if self._flood_tx_ipv4_socket:
            self._flood_tx_ipv4_socket.close()
            self._flood_tx_ipv4_socket = None
        if self._flood_rx_ipv6_handler:
            self._flood_rx_ipv6_handler.close()
            self._flood_rx_ipv6_handler = None
        if self._flood_tx_ipv6_socket:
            self._flood_tx_ipv6_socket.close()
            self._flood_tx_ipv6_socket = None
        # Update the node TIEs originated by this node to exclude this neighbor. We have to pass
        # interface_going_down to regenerate_my_node_ties because the state of this interface is
        # still THREE_WAY at this point.
        self.node.regenerate_my_node_ties(interface_going_down=self)
        # Update the south prefix TIE: we may have to start or stop originating a default route
        self.node.regenerate_my_south_prefix_tie(interface_going_down=self)

    def action_init_partially_conn(self):
        self.update_partially_connected()

    def action_clear_partially_conn(self):
        self.partially_connected = None
        self.partially_connected_causes = None

    def update_partially_connected(self):
        if self.neighbor_direction() != constants.DIR_SOUTH:
            return
        old_partially_connected = self.partially_connected
        if self.neighbor:
            (part_conn, part_conn_causes) = \
                self.node.check_sysid_partially_connected(self.neighbor.system_id)
            self.partially_connected = part_conn
            self.partially_connected_causes = part_conn_causes
        else:
            self.partially_connected = None
            self.partially_connected_causes = None
        if not old_partially_connected and self.partially_connected:
            self.info("Neighbor became partially connected")
            reason = "Neighbor {} became partially connected".format(self._log_id)
            self.node.trigger_spf(reason)
        if old_partially_connected and not self.partially_connected:
            self.info("Neighbor is no longer partially connected")
            reason = "Neighbor {} is no longer partially connected".format(self._log_id)
            self.node.trigger_spf(reason)

    def log_tx_protocol_packet(self, level, sock, prelude, packet_info):
        if not self._tx_log.isEnabledFor(level):
            return
        if sock.family == socket.AF_INET:
            fam_str = "IPv4"
            from_str = "from {}:{}".format(sock.getsockname()[0], sock.getsockname()[1])
            to_str = "to {}:{}".format(sock.getpeername()[0], sock.getpeername()[1])
        else:
            assert sock.family == socket.AF_INET6
            fam_str = "IPv6"
            from_str = "from [{}]:{}".format(sock.getsockname()[0], sock.getsockname()[1])
            to_str = "to [{}]:{}".format(sock.getpeername()[0], sock.getpeername()[1])
        type_str = self.protocol_packet_type(packet_info.protocol_packet)
        packet_str = str(packet_info)
        self._tx_log.log(level, "[%s] %s %s %s %s %s %s" %
                         (self._log_id, prelude, fam_str, type_str, from_str, to_str, packet_str))

    def log_rx_protocol_packet(self, log_level, prelude, packet_info):
        if not self._rx_log.isEnabledFor(log_level):
            return
        fam_str = constants.address_family_str(packet_info.address_family)
        from_str = packet_info.from_addr_port_str
        if packet_info.packet_type is None:
            type_str = ""
        else:
            type_str = constants.packet_type_str(packet_info.packet_type)
        packet_str = str(packet_info)
        self._rx_log.log(log_level, "[%s] %s %s %s %s %s" %
                         (self._log_id, prelude, fam_str, type_str, from_str, packet_str))

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
        packet_info = packet_common.encode_protocol_packet(protocol_packet, self.active_outer_key)
        self.send_packet_info(packet_info, flood)

    def send_packet_info(self, packet_info, flood):
        # In state oneway, send the undefined nonce as the reflected nonce
        if self.fsm.state == self.State.ONE_WAY:
            nonce_remote = 0
        else:
            nonce_remote = self._last_rx_lie_nonce_local
        packet_info.update_outer_sec_env_header(
            outer_key=self.active_outer_key,
            nonce_local=self.choose_tx_nonce_local(),
            nonce_remote=nonce_remote,
            remaining_lifetime=packet_info.remaining_tie_lifetime)
        protocol_packet = packet_info.protocol_packet
        if flood:
            if self._flood_tx_ipv4_socket:
                socks = [self._flood_tx_ipv4_socket]
            elif self._flood_tx_ipv6_socket:
                socks = [self._flood_tx_ipv6_socket]
            else:
                # It is normal not to have flooding sockets if we are not in state 3-way
                if self.fsm.state == self.State.THREE_WAY:
                    self.tx_warning("Could not send flood packet because interface has neither "
                                    "IPv4 nor IPv6 TX flood socket")
                return
        else:
            socks = []
            if self._lie_tx_ipv4_socket:
                socks.append(self._lie_tx_ipv4_socket)
            if self._lie_tx_ipv6_socket:
                socks.append(self._lie_tx_ipv6_socket)
        for sock in socks:
            if sock.family == socket.AF_INET:
                address_family = constants.ADDRESS_FAMILY_IPV4
            else:
                address_family = constants.ADDRESS_FAMILY_IPV6
            packet_nr = self.choose_tx_packet_nr(address_family, packet_info)
            packet_info.update_env_header(packet_nr)
            message_parts = packet_info.message_parts()
            nr_bytes = 0
            for part in message_parts:
                nr_bytes += len(part)
            if sock is not None:
                if self._tx_fail:
                    self.log_tx_protocol_packet(logging.DEBUG, sock,
                                                "Simulated failure sending", packet_info)
                    self.bump_tx_sim_errors_counter(sock, nr_bytes)
                else:
                    try:
                        sock.sendmsg(message_parts)
                        self.log_tx_protocol_packet(logging.DEBUG, sock, "Send", packet_info)
                        self.bump_tx_counters(protocol_packet, sock, nr_bytes)
                    except socket.error as error:
                        if error.errno == errno.ECONNREFUSED:
                            # It is common to get connection refused when trying to to send a UDP
                            # packet before we realize the receiver has closed it's socket.
                            severity = logging.INFO
                        else:
                            severity = logging.ERROR
                        prelude = "Error {} sending".format(str(error))
                        self.log_tx_protocol_packet(severity, sock, prelude, packet_info)
                        self.bump_tx_real_errors_counter(sock, nr_bytes)
                    else:
                        # Sucessfully sent packet; trace it
                        packet_trace = PacketTrace("TX", sock.getsockname(), sock.getpeername(),
                                                   packet_info)
                        self._packets.appendleft(packet_trace)

    def choose_tx_packet_nr(self, address_family, packet_info):
        if not packet_info.protocol_packet:
            return 0
        if packet_info.packet_type is None:
            return 0
        index = (address_family, packet_info.packet_type)
        packet_nr = self._next_tx_packet_nr[index]
        self._next_tx_packet_nr[index] += 1
        if self._next_tx_packet_nr[index] > 0xffff:
            self._next_tx_packet_nr[index] = 1
        return packet_nr

    def increase_tx_nonce_local(self):
        self._next_tx_nonce_local += 1
        if self._next_tx_nonce_local > 0xffff:
            self._next_tx_nonce_local = 1
            self._tx_nonce_local_wrapped = True

    def choose_tx_nonce_local(self):
        nonce_local = self._next_tx_nonce_local
        self._last_tx_nonce_local = nonce_local
        if not self._increase_tx_nonce_local_holddown_timer.running():
            self.increase_tx_nonce_local()
            self._increase_tx_nonce_local_holddown_timer.start()
        return nonce_local

    @staticmethod
    def bump_family_counter(sock, ipv4_counter, ipv6_counter, nr_bytes):
        if sock.family == socket.AF_INET:
            ipv4_counter.add([1, nr_bytes])
        else:
            assert sock.family == socket.AF_INET6
            ipv6_counter.add([1, nr_bytes])

    def bump_tx_counters(self, protocol_packet, sock, nr_bytes):
        if protocol_packet.content.lie:
            self.bump_family_counter(sock, self._tx_ipv4_lie_counter, self._tx_ipv6_lie_counter,
                                     nr_bytes)
        if protocol_packet.content.tie:
            self.bump_family_counter(sock, self._tx_ipv4_tie_counter, self._tx_ipv6_tie_counter,
                                     nr_bytes)
        if protocol_packet.content.tide:
            self.bump_family_counter(sock, self._tx_ipv4_tide_counter, self._tx_ipv6_tide_counter,
                                     nr_bytes)
        if protocol_packet.content.tire:
            self.bump_family_counter(sock, self._tx_ipv4_tire_counter, self._tx_ipv6_tire_counter,
                                     nr_bytes)

    def bump_rx_counters(self, protocol_packet, sock, nr_bytes):
        if protocol_packet.content.lie:
            self.bump_family_counter(sock, self._rx_ipv4_lie_counter, self._rx_ipv6_lie_counter,
                                     nr_bytes)
        if protocol_packet.content.tie:
            self.bump_family_counter(sock, self._rx_ipv4_tie_counter, self._rx_ipv6_tie_counter,
                                     nr_bytes)
        if protocol_packet.content.tide:
            self.bump_family_counter(sock, self._rx_ipv4_tide_counter, self._rx_ipv6_tide_counter,
                                     nr_bytes)
        if protocol_packet.content.tire:
            self.bump_family_counter(sock, self._rx_ipv4_tire_counter, self._rx_ipv6_tire_counter,
                                     nr_bytes)

    def bump_tx_real_errors_counter(self, sock, nr_bytes):
        self.bump_family_counter(sock, self._tx_ipv4_real_errors_counter,
                                 self._tx_ipv6_real_errors_counter, nr_bytes)

    def bump_rx_real_errors_counter(self, sock, nr_bytes):
        self.bump_family_counter(sock, self._rx_ipv4_real_errors_counter,
                                 self._rx_ipv6_real_errors_counter, nr_bytes)

    def bump_tx_sim_errors_counter(self, sock, nr_bytes):
        self.bump_family_counter(sock, self._tx_ipv4_sim_errors_counter,
                                 self._tx_ipv6_sim_errors_counter, nr_bytes)

    def bump_rx_sim_errors_counter(self, sock, nr_bytes):
        self.bump_family_counter(sock, self._rx_ipv4_sim_errors_counter,
                                 self._rx_ipv6_sim_errors_counter, nr_bytes)

    def action_send_lie(self):
        packet_header = encoding.ttypes.PacketHeader(
            sender=self.node.system_id,
            level=self.node.level_value())
        node_capabilities = encoding.ttypes.NodeCapabilities(
            protocol_minor_version=protocol_minor_version,
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
            node_capabilities=node_capabilities,
            holdtime=3,
            not_a_ztp_offer=self.node.send_not_a_ztp_offer_on_intf(self.name),
            you_are_flood_repeater=self.nbr_is_fr_bool(self.floodred_nbr_is_fr),
            label=None)
        packet_content = encoding.ttypes.PacketContent(lie=lie_packet)
        protocol_packet = encoding.ttypes.ProtocolPacket(packet_header, packet_content)
        self.send_protocol_packet(protocol_packet, flood=False)
        tx_offer = offer.TxOffer(
            self.name,
            self.node.system_id,
            packet_header.level,
            lie_packet.not_a_ztp_offer,
            self.fsm.state)
        self.node.record_tx_offer(tx_offer)
        if self.floodred_nbr_is_fr == self.NbrIsFRState.PENDING_TRUE:
            # This was the first time we send you_are_flood_repeater=True to the neighbor
            self.floodred_mark_sent_you_are_fr()

    def action_increase_tx_nonce_local(self):
        self.increase_tx_nonce_local()

    def floodred_mark_sent_you_are_fr(self):
        self.floodred_nbr_is_fr = self.NbrIsFRState.TRUE
        self.floodred_check_switchover_done()

    def floodred_check_switchover_done(self):
        # Are there any interfaces whose flood repeater state is still pending true?
        for intf in self.node.interfaces_by_name.values():
            if intf.floodred_nbr_is_fr == self.NbrIsFRState.PENDING_TRUE:
                return
        # No, nothing pending true. Now, change every interface that is in flood repeater state
        # pending false to false.
        for intf in self.node.interfaces_by_name.values():
            if intf.floodred_nbr_is_fr == self.NbrIsFRState.PENDING_FALSE:
                intf.floodred_nbr_is_fr = self.NbrIsFRState.FALSE

    def action_cleanup(self):
        self.neighbor = None

    def check_reflection(self):
        # Does the received LIE packet (which is now stored in _neighbor) report us as the neighbor?
        if self.neighbor.neighbor_system_id != self.node.system_id:
            self.info("Neighbor does not report us as neighbor (system-id %s instead of %s",
                      utils.system_id_str(self.neighbor.neighbor_system_id),
                      utils.system_id_str(self.node.system_id))
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
        self.node.fsm.push_event(self.node.Event.NEIGHBOR_OFFER, offer_for_ztp)

    def this_node_is_leaf(self):
        return self.node.level_value() == common.constants.leaf_level

    def hat_not_greater_remote_level(self, remote_level):
        if self.node.highest_adjacency_three_way is None:
            return True
        return self.node.highest_adjacency_three_way <= remote_level

    def both_nodes_support_leaf_2_leaf(self, protocol_packet):
        header = protocol_packet.header
        lie = protocol_packet.content.lie
        if not self.this_node_is_leaf():
            # This node is not a leaf
            return False
        if header.level != 0:
            # Remote node is not a leaf
            return False
        if not self.node.leaf_2_leaf:
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
        assert self.node.level_value() is not None
        assert header.level is not None
        if abs(header.level - self.node.level_value()) > 1:
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
        if self.node.system_id == header.sender:
            # Section 4.2.2.5 (DEV-4: rule is missing in section B.1.4)
            return (False, "Remote system ID is same as local system ID (loop)", False, False)
        if self._mtu != lie.link_mtu_size:
            # Section 4.2.2.6
            return (False, "MTU mismatch", False, True)
        if header.level is None:
            # Section B.1.4.2 (1st OR clause) / section 4.2.2.7
            return (False, "Remote level (in received LIE) is undefined", True, False)
        if self.node.level_value() is None:
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
                self.node.trigger_spf(reason)
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
                self.node.trigger_spf(reason)
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
        self.node.expire_offer(self.name)

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
        State.ONE_WAY  : (
            [action_cleanup,                        # State 1way entry actions
             action_send_lie],
            [action_increase_tx_nonce_local]),      # State 1way exit actions
        State.TWO_WAY  : (
            [],                                     # State 2way entry actions
            [action_increase_tx_nonce_local]),      # State 2way exit actions
        State.THREE_WAY: (
            [action_start_flooding,                 # State 3way entry actions
             action_init_partially_conn],
            [action_increase_tx_nonce_local,        # State 3way exit actions
             action_stop_flooding,
             action_clear_partially_conn])
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

    def tx_warning(self, msg, *args):
        self._tx_log.warning("[%s] %s" % (self._log_id, msg), *args)

    def __init__(self, parent_node, config):
        # pylint:disable=too-many-statements
        # TODO: process bandwidth field in config
        self.node = parent_node
        self._engine = parent_node.engine
        self.name = config['name']
        self._log_id = parent_node.log_id + ":{}".format(self.name)
        self._log = parent_node.log.getChild("if")
        if self._engine.simulated_interfaces and self._engine.physical_interface_name:
            self.physical_interface_name = self._engine.physical_interface_name
        else:
            self.physical_interface_name = self.name
        # TODO: Make the default metric/bandwidth depend on the speed of the interface
        ###@@@ The default is wrong -- that is the default for bandwidth
        self._metric = self.get_config_attribute(config, 'metric',
                                                 common.constants.default_bandwidth)
        self._advertised_name = self.generate_advertised_name()
        self._ipv4_address = utils.interface_ipv4_address(self.physical_interface_name)
        self._ipv6_address = utils.interface_ipv6_address(self.physical_interface_name)
        try:
            self._interface_index = socket.if_nametoindex(self.physical_interface_name)
        except (IOError, OSError) as err:
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
        self.local_id = parent_node.allocate_interface_id()
        self._mtu = self.get_mtu()
        self._pod = self.UNDEFINED_OR_ANY_POD
        self.neighbor = None
        self._next_tx_packet_nr = {}    # Indexed (address-family, packet-type)
        for address_family in constants.ADDRESS_FAMILIES:
            for packet_type in constants.PACKET_TYPES:
                index = (address_family, packet_type)
                self._next_tx_packet_nr[index] = 1
        self._last_rx_packet_nr = {}    # Indexed by (address-family, packet-type)
        self._next_tx_nonce_local = random.randint(1, 65535)
        self._last_tx_nonce_local = None
        self._increase_tx_nonce_local_holddown_timer = timer.Timer(
            interval=self.INCREASE_TX_NONCE_LOCAL_HOLDDOWN_TIME,
            expire_function=None,
            periodic=False,
            start=False)
        self._tx_nonce_local_wrapped = False
        self._last_rx_lie_nonce_local = 0
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
        self._queues = msg_queues.MsgQueues(self)
        self._packets = collections.deque([], self.MAX_PACKET_TRACE)
        self.floodred_nbr_is_fr = self.NbrIsFRState.NOT_APPLICABLE
        self.partially_connected = None
        self.partially_connected_causes = None
        key_id = self.get_config_attribute(config, 'active_authentication_key', None)
        if key_id is None:
            self.active_outer_key = self.node.active_outer_key
            self.active_outer_key_src = self.node.active_outer_key_src
        else:
            self.active_outer_key = self.node.key_id_to_key(key_id)
            self.active_outer_key_src = "Interface Active Key"
        key_ids = self.get_config_attribute(config, 'accept_authentication_keys', None)
        if key_ids is None:
            self.accept_outer_keys = self.node.accept_outer_keys
            self.accept_outer_keys_src = self.node.accept_outer_keys_src
        else:
            self.accept_outer_keys = self.node.key_ids_to_keys(key_ids)
            self.accept_outer_keys_src = "Interface Accept Keys"
        self._traffic_stats_group = stats.Group(self.node.intf_traffic_stats_group)
        pab = ["Packet", "Byte"]
        stg = self._traffic_stats_group
        self._tx_errors_counter = stats.MultiCounter(None, "Total TX Errors", pab)
        self._rx_errors_counter = stats.MultiCounter(None, "Total RX Errors", pab)
        self._errors_counter = stats.MultiCounter(None, "Total RX Decode Errors", pab)
        self._error_to_counter = {}
        self._security_errors_counter = stats.MultiCounter(None, "Total Authentication Errors", pab)
        self._tx_packets_counter = stats.MultiCounter(None, "Total TX Packets", pab)
        self._rx_packets_counter = stats.MultiCounter(None, "Total RX Packets", pab)
        self._tx_ipv6_counter = stats.MultiCounter(None, "Total TX IPv6 Packets", pab)
        self._rx_ipv6_counter = stats.MultiCounter(None, "Total RX IPv6 Packets", pab)
        self._tx_ipv4_counter = stats.MultiCounter(None, "Total TX IPv4 Packets", pab)
        self._rx_ipv4_counter = stats.MultiCounter(None, "Total RX IPv4 Packets", pab)
        self._tx_flooding_counter = stats.MultiCounter(
            None, "Total TX Flooding Packets", pab,
            sum_counters=[self._tx_packets_counter])
        self._rx_flooding_counter = stats.MultiCounter(
            None, "Total RX Flooding Packets", pab,
            sum_counters=[self._rx_packets_counter])
        self._tx_tire_counter = stats.MultiCounter(
            None, "Total TX TIRE Packets", pab,
            sum_counters=[self._tx_flooding_counter])
        self._rx_tire_counter = stats.MultiCounter(
            None, "Total RX TIRE Packets", pab,
            sum_counters=[self._rx_flooding_counter])
        self._tx_tide_counter = stats.MultiCounter(
            None, "Total TX TIDE Packets", pab,
            sum_counters=[self._tx_flooding_counter])
        self._rx_tide_counter = stats.MultiCounter(
            None, "Total RX TIDE Packets", pab,
            sum_counters=[self._rx_flooding_counter])
        self._tx_tie_counter = stats.MultiCounter(
            None, "Total TX TIE Packets", pab,
            sum_counters=[self._tx_flooding_counter])
        self._rx_tie_counter = stats.MultiCounter(
            None, "Total RX TIE Packets", pab,
            sum_counters=[self._rx_flooding_counter])
        self._tx_lie_counter = stats.MultiCounter(
            None, "Total TX LIE Packets", pab,
            sum_counters=[self._tx_packets_counter])
        self._rx_lie_counter = stats.MultiCounter(
            None, "Total RX LIE Packets", pab,
            sum_counters=[self._rx_packets_counter])
        self._rx_ipv4_lie_counter = stats.MultiCounter(
            stg, "RX IPv4 LIE Packets", pab,
            sum_counters=[self._rx_lie_counter, self._rx_ipv4_counter])
        self._tx_ipv4_lie_counter = stats.MultiCounter(
            stg, "TX IPv4 LIE Packets", pab,
            sum_counters=[self._tx_lie_counter, self._tx_ipv4_counter])
        self._rx_ipv4_tie_counter = stats.MultiCounter(
            stg, "RX IPv4 TIE Packets", pab,
            sum_counters=[self._rx_tie_counter, self._rx_ipv4_counter])
        self._tx_ipv4_tie_counter = stats.MultiCounter(
            stg, "TX IPv4 TIE Packets", pab,
            sum_counters=[self._tx_tie_counter, self._tx_ipv4_counter])
        self._rx_ipv4_tide_counter = stats.MultiCounter(
            stg, "RX IPv4 TIDE Packets", pab,
            sum_counters=[self._rx_tide_counter, self._rx_ipv4_counter])
        self._tx_ipv4_tide_counter = stats.MultiCounter(
            stg, "TX IPv4 TIDE Packets", pab,
            sum_counters=[self._tx_tide_counter, self._tx_ipv4_counter])
        self._rx_ipv4_tire_counter = stats.MultiCounter(
            stg, "RX IPv4 TIRE Packets", pab,
            sum_counters=[self._rx_tire_counter, self._rx_ipv4_counter])
        self._tx_ipv4_tire_counter = stats.MultiCounter(
            stg, "TX IPv4 TIRE Packets", pab,
            sum_counters=[self._tx_tire_counter, self._tx_ipv4_counter])
        self._rx_ipv4_real_errors_counter = stats.MultiCounter(
            stg, "RX IPv4 Real Errors", pab,
            sum_counters=[self._rx_errors_counter])
        self._tx_ipv4_real_errors_counter = stats.MultiCounter(
            stg, "TX IPv4 Real Errors", pab,
            sum_counters=[self._tx_errors_counter])
        self._rx_ipv4_sim_errors_counter = stats.MultiCounter(
            stg, "RX IPv4 Simulated Errors", pab,
            sum_counters=[self._rx_errors_counter])
        self._tx_ipv4_sim_errors_counter = stats.MultiCounter(
            stg, "TX IPv4 Simulated Errors", pab,
            sum_counters=[self._tx_errors_counter])
        self._rx_ipv6_lie_counter = stats.MultiCounter(
            stg, "RX IPv6 LIE Packets", pab,
            sum_counters=[self._rx_lie_counter, self._rx_ipv6_counter])
        self._tx_ipv6_lie_counter = stats.MultiCounter(
            stg, "TX IPv6 LIE Packets", pab,
            sum_counters=[self._tx_lie_counter, self._tx_ipv6_counter])
        self._rx_ipv6_tie_counter = stats.MultiCounter(
            stg, "RX IPv6 TIE Packets", pab,
            sum_counters=[self._rx_tie_counter, self._rx_ipv6_counter])
        self._tx_ipv6_tie_counter = stats.MultiCounter(
            stg, "TX IPv6 TIE Packets", pab,
            sum_counters=[self._tx_tie_counter, self._tx_ipv6_counter])
        self._rx_ipv6_tide_counter = stats.MultiCounter(
            stg, "RX IPv6 TIDE Packets", pab,
            sum_counters=[self._rx_tide_counter, self._rx_ipv6_counter])
        self._tx_ipv6_tide_counter = stats.MultiCounter(
            stg, "TX IPv6 TIDE Packets", pab,
            sum_counters=[self._tx_tide_counter, self._tx_ipv6_counter])
        self._rx_ipv6_tire_counter = stats.MultiCounter(
            stg, "RX IPv6 TIRE Packets", pab,
            sum_counters=[self._rx_tire_counter, self._rx_ipv6_counter])
        self._tx_ipv6_tire_counter = stats.MultiCounter(
            stg, "TX IPv6 TIRE Packets", pab,
            sum_counters=[self._tx_tire_counter, self._tx_ipv6_counter])
        self._rx_ipv6_real_errors_counter = stats.MultiCounter(
            stg, "RX IPv6 Real Errors", pab,
            sum_counters=[self._rx_errors_counter])
        self._tx_ipv6_real_errors_counter = stats.MultiCounter(
            stg, "TX IPv6 Real Errors", pab,
            sum_counters=[self._tx_errors_counter])
        self._rx_ipv6_sim_errors_counter = stats.MultiCounter(
            stg, "RX IPv6 Simulated Errors", pab,
            sum_counters=[self._rx_errors_counter])
        self._tx_ipv6_sim_errors_counter = stats.MultiCounter(
            stg, "TX IPv6 Simulated Errors", pab,
            sum_counters=[self._tx_errors_counter])
        self._rx_lie_counter.add_to_group(stg)
        self._tx_lie_counter.add_to_group(stg)
        self._rx_tie_counter.add_to_group(stg)
        self._tx_tie_counter.add_to_group(stg)
        self._rx_tide_counter.add_to_group(stg)
        self._tx_tide_counter.add_to_group(stg)
        self._rx_tire_counter.add_to_group(stg)
        self._tx_tire_counter.add_to_group(stg)
        self._rx_flooding_counter.add_to_group(stg)
        self._tx_flooding_counter.add_to_group(stg)
        self._rx_ipv4_counter.add_to_group(stg)
        self._tx_ipv4_counter.add_to_group(stg)
        self._rx_ipv6_counter.add_to_group(stg)
        self._tx_ipv6_counter.add_to_group(stg)
        self._rx_packets_counter.add_to_group(stg)
        self._tx_packets_counter.add_to_group(stg)
        self._rx_errors_counter.add_to_group(stg)
        self._tx_errors_counter.add_to_group(stg)
        # Counters for rx message decoding errors
        for decode_error in packet_common.PacketInfo.DECODE_ERRORS:
            counter = stats.MultiCounter(stg, "RX " + decode_error, pab,
                                         sum_counters=[self._errors_counter])
            self._error_to_counter[decode_error] = counter
        self._errors_counter.add_to_group(stg)
        # Counters for received packets with wrong packet-nr
        self._total_misorders_counter = stats.Counter(None, "Total RX Misorders", "Packet")
        self._ipv4_misorders_counter = stats.Counter(None, "Total RX IPv4 Misorders", "Packet")
        self._ipv6_misorders_counter = stats.Counter(None, "Total RX IPv6 Misorders", "Packet")
        self._misorder_counters = {}
        for packet_type in constants.PACKET_TYPES:
            for address_family in constants.ADDRESS_FAMILIES:
                index = (address_family, packet_type)
                counter_name = "RX {} {} Misorders".format(
                    constants.address_family_str(address_family),
                    constants.packet_type_str(packet_type))
                if address_family == constants.ADDRESS_FAMILY_IPV4:
                    af_sum_counter = self._ipv4_misorders_counter
                else:
                    af_sum_counter = self._ipv6_misorders_counter
                self._misorder_counters[index] = stats.Counter(
                    stg, counter_name, "Packet",
                    sum_counters=[af_sum_counter, self._total_misorders_counter])
        self._ipv4_misorders_counter.add_to_group(stg)
        self._ipv6_misorders_counter.add_to_group(stg)
        self._total_misorders_counter.add_to_group(stg)
        # Counters for security errors
        self._security_stats_group = stats.Group(self.node.intf_security_stats_group)
        stg = self._security_stats_group
        for auth_error in packet_common.PacketInfo.AUTHENTICATION_ERRORS:
            counter = stats.MultiCounter(stg, auth_error, pab,
                                         sum_counters=[self._security_errors_counter])
            self._error_to_counter[auth_error] = counter
        self._security_errors_counter.add_to_group(stg)
        self._outer_auth_ok_counter = stats.MultiCounter(
            stg, "Non-empty outer fingerprint accepted", pab)
        self._origin_auth_ok_counter = stats.MultiCounter(
            stg, "Non-empty origin fingerprint accepted", pab)
        self._outer_empty_auth_ok_counter = stats.MultiCounter(
            stg, "Empty outer fingerprint accepted", pab)
        self._origin_empty_auth_ok_counter = stats.MultiCounter(
            stg, "Empty origin fingerprint accepted", pab)

        self.fsm = fsm.Fsm(
            definition=self.fsm_definition,
            action_handler=self,
            log=self._fsm_log,
            log_id=self._log_id,
            sum_stats_group=self.node.intf_lie_fsm_stats_group)
        if self.node.running:
            self.run()
            self.fsm.start()

    def run(self):
        self._lie_tx_ipv4_socket = self.create_socket_ipv4_tx_mcast(
            multicast_address=self._tx_lie_ipv4_mcast_address,
            port=self._tx_lie_port,
            loopback=self.node.engine.ipv4_multicast_loopback)
        self._lie_tx_ipv6_socket = self.create_socket_ipv6_tx_mcast(
            multicast_address=self._tx_lie_ipv6_mcast_address,
            port=self._tx_lie_port,
            loopback=self.node.engine.ipv6_multicast_loopback)
        self._lie_rx_ipv4_handler = udp_rx_handler.UdpRxHandler(
            interface_name=self.physical_interface_name,
            local_port=self._rx_lie_port,
            ipv4=True,
            multicast_address=self._rx_lie_ipv4_mcast_address,
            remote_address=None,
            receive_function=self.receive_lie_message,
            log=self._rx_log,
            log_id=self._log_id)
        self._lie_rx_ipv6_handler = udp_rx_handler.UdpRxHandler(
            interface_name=self.physical_interface_name,
            local_port=self._rx_lie_port,
            ipv4=False,
            multicast_address=self._rx_lie_ipv6_mcast_address,
            remote_address=None,
            receive_function=self.receive_lie_message,
            log=self._rx_log,
            log_id=self._log_id)
        self._flood_rx_ipv4_handler = None
        self._flood_tx_ipv4_socket = None
        self._one_second_timer = timer.Timer(
            1.0,
            lambda: self.fsm.push_event(self.Event.TIMER_TICK))

    def get_config_attribute(self, config, attribute, default):
        if attribute in config:
            return config[attribute]
        else:
            return default

    def is_valid_received_system_id(self, system_id):
        if system_id == 0:
            return False
        return True

    def receive_message_common(self, message, from_info, sock):
        nr_bytes = len(message)
        packet_info = packet_common.decode_message(
            rx_intf=self,
            from_info=from_info,
            message=message,
            active_outer_key=self.active_outer_key,
            accept_outer_keys=self.accept_outer_keys,
            active_origin_key=self.node.active_origin_key,
            accept_origin_keys=self.node.accept_origin_keys)
        if packet_info.error:
            self.log_and_count_error(packet_info, nr_bytes)
            return None
        self.count_auth_okay(packet_info, nr_bytes)
        protocol_packet = packet_info.protocol_packet
        if self._rx_fail:
            self.log_rx_protocol_packet(logging.DEBUG, "Simulated failure receiving", packet_info)
            self.bump_rx_sim_errors_counter(sock, nr_bytes)
            return None
        if protocol_packet.header.sender == self.node.system_id:
            self.log_rx_protocol_packet(logging.DEBUG, "Ignore looped receive", packet_info)
            return None
        # Note: we must update the last RX nonce local, even if we reject the packet because the
        # reflected nonce is too far out of sync. If not, we will never get back into sync after
        # a temporary loss of connectivy in which the nonces drift out of sync.
        self.update_last_rx_lie_nonce_local(packet_info)
        self.check_reflected_nonce(packet_info)
        if packet_info.error:
            self.log_and_count_error(packet_info, nr_bytes)
            return None
        if not protocol_packet.content:
            self.log_rx_protocol_packet(logging.WARNING, "Received contentless", packet_info)
            return None
        self.log_rx_protocol_packet(logging.DEBUG, "Receive", packet_info)
        if protocol_packet.header.major_version != constants.RIFT_MAJOR_VERSION:
            self.rx_error("Received different major protocol version from %s (local version %d, "
                          "remote version %d)", from_info, constants.RIFT_MAJOR_VERSION,
                          protocol_packet.header.major_version)
            return None
        self.check_rx_packet_nr(packet_info)
        packet_trace = PacketTrace("RX", sock.getsockname(), from_info, packet_info)
        self._packets.appendleft(packet_trace)
        return packet_info

    def log_and_count_error(self, packet_info, nr_bytes):
        msg = packet_info.error
        if packet_info.error_details:
            msg += " (" + packet_info.error_details + ")"
        self.log_rx_protocol_packet(logging.ERROR, msg, packet_info)
        counter = self._error_to_counter.get(packet_info.error)
        if counter:
            counter.add([1, nr_bytes])

    def count_auth_okay(self, packet_info, nr_bytes):
        if packet_info.outer_key_id == 0:
            counter = self._outer_empty_auth_ok_counter
        else:
            counter = self._outer_auth_ok_counter
        counter.add([1, nr_bytes])
        if packet_info.origin_sec_env_header:
            if packet_info.origin_key_id == 0:
                counter = self._origin_empty_auth_ok_counter
            else:
                counter = self._origin_auth_ok_counter
            counter.add([1, nr_bytes])

    def update_last_rx_lie_nonce_local(self, packet_info):
        if packet_info.protocol_packet and packet_info.protocol_packet.content.lie:
            self._last_rx_lie_nonce_local = packet_info.nonce_local

    def check_reflected_nonce(self, packet_info):
        max_delta = common.constants.maximum_valid_nonce_delta
        sent_nonce = self._last_tx_nonce_local
        reflected_nonce = packet_info.nonce_remote
        if reflected_nonce == 0:
            # Neighbor did not reflect a valid nonce.
            # This is allowed if we are not in state three-way
            # This also allowed in the beginning (first maximum_valid_nonce_delta sent nonces)
            if self.fsm.state != self.State.THREE_WAY:
                accepted = True
            elif self._tx_nonce_local_wrapped:
                accepted = False
            else:
                accepted = sent_nonce <= max_delta
        elif reflected_nonce <= sent_nonce:
            delta = sent_nonce - reflected_nonce
            accepted = delta <= max_delta
        else:
            # Reflected nonce is greater than sent nonce. Could still be okay in case of wrap-around
            if self._tx_nonce_local_wrapped:
                unwrapped_sent_nonce = sent_nonce + 0xffff
                delta = unwrapped_sent_nonce - reflected_nonce
                accepted = 0 <= delta <= max_delta
            else:
                accepted = False
        if not accepted:
            packet_info.error = packet_common.PacketInfo.ERR_REFLECTED_NONCE_OUT_OF_SYNC
            packet_info.error_details = "Last sent nonce is {}, reflected nonce is {}".format(
                sent_nonce, reflected_nonce)

    def check_rx_packet_nr(self, packet_info):
        if packet_info.packet_nr == 0:
            return
        index = (packet_info.address_family, packet_info.packet_type)
        if index in self._last_rx_packet_nr:
            last_rx_packet_nr = self._last_rx_packet_nr[index]
            expected_rx_packet_nr = last_rx_packet_nr + 1
            if expected_rx_packet_nr > 0xffff:
                expected_rx_packet_nr = 1
            if packet_info.packet_nr != expected_rx_packet_nr:
                self._misorder_counters[index].increase()
        self._last_rx_packet_nr[index] = packet_info.packet_nr

    def receive_lie_message(self, message, from_info, sock):
        packet_info = self.receive_message_common(message, from_info, sock)
        if packet_info is None:
            return
        protocol_packet = packet_info.protocol_packet
        if protocol_packet.content.lie:
            # TODO: Verify inner nonce is outer nonce
            event_data = (protocol_packet, from_info)
            self.fsm.push_event(self.Event.LIE_RECEIVED, event_data)
        else:
            # TODO: Missing contents for port counter
            self.rx_warning("Received packet without LIE content on LIE port (ignored)")
        if protocol_packet.content.tie:
            # TODO: Wrong contents for port counter
            self.rx_warning("Received TIE packet on LIE port (ignored)")
        if protocol_packet.content.tide:
            self.rx_warning("Received TIDE packet on LIE port (ignored)")
        if protocol_packet.content.tire:
            self.rx_warning("Received TIRE packet on LIE port (ignored)")
        self.bump_rx_counters(protocol_packet, sock, len(message))

    def receive_flood_message(self, message, from_info, sock):
        packet_info = self.receive_message_common(message, from_info, sock)
        if packet_info is None:
            return
        protocol_packet = packet_info.protocol_packet
        flood_content = False
        if protocol_packet.content.tie is not None:
            self.process_rx_tie_packet_info(packet_info)
            flood_content = True
        if protocol_packet.content.tide:
            self.process_rx_tide_packet(protocol_packet.content.tide)
            flood_content = True
        if protocol_packet.content.tire:
            self.process_rx_tire_packet(protocol_packet.content.tire)
            flood_content = True
        if protocol_packet.content.lie:
            # TODO: Wrong contents for port counter
            self.rx_warning("Received LIE packet on flood port (ignored)")
        else:
            if not flood_content:
                # TODO: Missing contents for port counter
                self.rx_warning("Received packet without TIE/TIDE/TIRE content on flood port "
                                "(ignored)")
        self.bump_rx_counters(protocol_packet, sock, len(message))

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

    def process_rx_tie_packet_info(self, tie_packet_info):
        tie_packet = tie_packet_info.protocol_packet.content.tie
        self.rx_debug("Receive TIE packet %s", tie_packet)
        result = self.node.process_rx_tie_packet_info(tie_packet_info)
        (start_sending_tie_header, ack_tie_header) = result
        if start_sending_tie_header is not None:
            self.try_to_transmit_tie(start_sending_tie_header)
        if ack_tie_header is not None:
            tie_header_lifetime = packet_common.expand_tie_header_with_lifetime(
                ack_tie_header,
                tie_packet_info.remaining_tie_lifetime)
            self.ack_tie(tie_header_lifetime)

    def process_rx_tide_packet(self, tide_packet):
        result = self.node.process_rx_tide_packet(tide_packet)
        (request_tie_headers, start_sending_tie_headers, stop_sending_tie_headers) = result
        for tie_header in start_sending_tie_headers:
            self.try_to_transmit_tie(tie_header)
        for tie_header in request_tie_headers:
            self.request_tie(tie_header)
        for tie_header in stop_sending_tie_headers:
            self._queues.remove_from_all_queues(tie_header.tieid)

    def process_rx_tire_packet(self, tire_packet):
        self.rx_debug("Receive TIRE packet %s", tire_packet)
        result = self.node.process_rx_tire_packet(tire_packet)
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
        # Cannot determine current node level, we can't infer the neighbor direction
        my_level = self.node.level_value()
        if my_level is None:
            return None
        if self.neighbor.level > my_level:
            return constants.DIR_NORTH
        elif self.neighbor.level < my_level:
            return constants.DIR_SOUTH
        else:
            return constants.DIR_EAST_WEST

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

    # This is the simplified implementation of is_request_allowed as described in "the solution to
    # oscillation #2" in slide deck http://bit.ly/rift-flooding-oscillations-v1. During the RIFT
    # core team conference call on 19 Oct 2018, Tony reported it was his intent to apply the same
    # logic. However, this seems like a simpler (and less error prone) way to achieve that.
    #
    def is_request_allowed_simple(self, tie_header, _i_am_top_of_fabric):
        return self.node.flood_allowed_from_nbr_to_node(
            tie_header=tie_header,
            neighbor_direction=self.neighbor_direction(),
            neighbor_system_id=self.neighbor.system_id,
            neighbor_level=self.neighbor.level,
            neighbor_is_top_of_fabric=self.neighbor.top_of_fabric(),
            node_system_id=self.node.system_id)

    def is_request_allowed(self, tie_header, i_am_top_of_fabric):
        if USE_SIMPLE_REQUEST_FILTERING:
            return self.is_request_allowed_simple(tie_header, i_am_top_of_fabric)
        else:
            return self.is_request_allowed_complex(tie_header, i_am_top_of_fabric)

    def is_request_filtered(self, tie_header):
        # The logic is more more easy to follow and mirrors the language of the flooding scope
        # rules (table 3) more closely if we ask the opposite question: is the request allowed?
        (allowed, reason) = self.is_request_allowed(tie_header, self.node.top_of_fabric())
        filtered = not allowed
        return (filtered, reason)

    def is_flood_filtered(self, tie_header):
        (allowed, reason) = self.node.is_flood_allowed(
            tie_header=tie_header,
            to_node_direction=self.neighbor_direction(),
            to_node_system_id=self.neighbor.system_id,
            from_node_system_id=self.node.system_id,
            from_node_level=self.node.level_value(),
            from_node_is_top_of_fabric=self.node.top_of_fabric())
        filtered = not allowed
        return (filtered, reason)

    def try_to_transmit_tie(self, tie_header):
        (filtered, reason) = self.is_flood_filtered(tie_header)
        outcome = "filtered" if filtered else "allowed"
        self.tx_debug("Transmit TIE %s is %s because %s", tie_header, outcome, reason)
        if not filtered:
            ack_header_lifetime = self._queues.search_tie_ack_queue(tie_header.tieid)
            if ack_header_lifetime:
                if ack_header_lifetime.header.seq_nr < tie_header.seq_nr:
                    # ACK for older TIE is in queue, remove ACK from queue and send newer TIE
                    self._queues.remove_from_tie_ack_queue(ack_header_lifetime.header.tieid)
                    self.tx_tie(tie_header)
                else:
                    # ACK for newer TIE or same seq-nr TIE in in queue, keep ACK and don't send
                    # this older TIE
                    pass
            else:
                # No ACK in queue, send this TIE
                self.tx_tie(tie_header)

    def tx_tie(self, tie_header):
        self._queues.add_to_tie_queue(tie_header)

    def ack_tie(self, tie_header_lifetime):
        assert tie_header_lifetime.__class__ == encoding.ttypes.TIEHeaderWithLifeTime
        tie_id = tie_header_lifetime.header.tieid
        self._queues.remove_from_tie_queue(tie_id)
        self._queues.remove_from_tie_req_queue(tie_id)
        self._queues.add_to_tie_ack_queue(tie_header_lifetime)

    def tie_been_acked(self, tie_header):
        self._queues.remove_from_all_queues(tie_header.tieid)

    def remove_tie_from_all_queues(self, tie_id):
        self._queues.remove_from_all_queues(tie_id)

    def request_tie(self, tie_header):
        assert tie_header.__class__ == encoding.ttypes.TIEHeader
        (filtered, reason) = self.is_request_filtered(tie_header)
        outcome = "excluded" if filtered else "included"
        self.tx_debug("Request TIE %s is %s in TIRE because %s", tie_header, outcome, reason)
        if not filtered:
            tie_id = tie_header.tieid
            self._queues.remove_from_tie_queue(tie_id)
            self._queues.remove_from_tie_ack_queue(tie_id)
            self._queues.add_to_tie_req_queue(tie_header)

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

    @staticmethod
    def cli_floodred_summary_headers():
        return [
            ["Interface", "Name"],
            ["Neighbor", "Interface", "Name"],
            ["Neighbor", "System ID"],
            ["Neighbor", "State"],
            ["Neighbor", "Direction"],
            ["Neighbor is", "Flood Repeater", "for This Node"],
            ["This Node is", "Flood Repeater", "for Neighbor"]]

    def cli_floodred_summary_attributes(self):
        if self.neighbor_direction() != constants.DIR_SOUTH:
            i_am_fr_str = "Not Applicable"
        elif self.neighbor:
            i_am_fr_str = str(self.neighbor.you_are_flood_repeater)
        else:
            i_am_fr_str = ""
        if self.neighbor:
            neighbor_sysid = utils.system_id_str(self.neighbor.system_id)
            neighbor_name = self.neighbor.name
            neighbor_dir = constants.direction_str(self.neighbor_direction())
        else:
            neighbor_sysid = ''
            neighbor_name = ''
            neighbor_dir = ''
        return [
            self.name,
            neighbor_name,
            neighbor_sysid,
            self.state_name,
            neighbor_dir,
            self.nbr_is_fr_str(self.floodred_nbr_is_fr),
            i_am_fr_str
        ]

    def partially_connected_str(self):
        if self.partially_connected is None:
            return "N/A"
        if not self.partially_connected:
            return "False"
        return "True"

    def partially_connected_causes_str(self):
        if self.partially_connected is None:
            return ""
        if not self.partially_connected:
            return ""
        causes = []
        count = 0
        for sysid in self.partially_connected_causes:
            count += 1
            if count <= 3:
                causes.append(self.node.node_descr(sysid))
        if count > 3:
            causes.append("and {} more".format(count - 3))
        return causes

    def cli_details_table(self):
        tab = table.Table(separators=False)
        tab.add_rows([
            ["Interface Name", self.name],
            ["Physical Interface Name", self.physical_interface_name],
            ["Advertised Name", self._advertised_name],
            ["Interface IPv4 Address", self._ipv4_address],
            ["Interface IPv6 Address", self._ipv6_address],
            ["Interface Index", self._interface_index],
            ["Metric", self._metric],
            ["LIE Receive IPv4 Multicast Address", self._rx_lie_ipv4_mcast_address],
            ["LIE Receive IPv6 Multicast Address", self._rx_lie_ipv6_mcast_address],
            ["LIE Receive Port", self._rx_lie_port],
            ["LIE Transmit IPv4 Multicast Address", self._tx_lie_ipv4_mcast_address],
            ["LIE Transmit IPv6 Multicast Address", self._tx_lie_ipv6_mcast_address],
            ["LIE Transmit Port", self._tx_lie_port],
            ["Flooding Receive Port", self._rx_flood_port],
            ["System ID", utils.system_id_str(self.node.system_id)],
            ["Local ID", self.local_id],
            ["MTU", self._mtu],
            ["POD", self._pod],
            ["Failure", self.failure_str()],
            ["State", self.state_name],
            ["Received LIE Accepted or Rejected", self._lie_accept_or_reject],
            ["Received LIE Accept or Reject Reason", self._lie_accept_or_reject_rule],
            ["Neighbor is Flood Repeater", self.nbr_is_fr_str(self.floodred_nbr_is_fr)],
            ["Neighbor is Partially Connected", self.partially_connected_str()],
            ["Nodes Causing Partial Connectivity", self.partially_connected_causes_str()]
        ])
        return tab

    def cli_neighbor_details_table(self):
        if self.neighbor:
            return self.neighbor.cli_details_table()
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

    @staticmethod
    def key_id_str(key):
        if key is None:
            return "None"
        if key.key_id is None:
            return "None"
        return str(key.key_id)

    def intf_outer_keys_table(self):
        tab = table.Table()
        tab.add_row(["Key",
                     "Key ID(s)",
                     "Configuration Source"])
        tab.add_row(["Active Outer Key",
                     self.node.key_str(self.active_outer_key),
                     self.active_outer_key_src])
        tab.add_row(["Accept Outer Keys",
                     self.node.keys_str(self.accept_outer_keys),
                     self.accept_outer_keys_src])
        return tab

    def nonces_table(self):
        tab = table.Table()
        tab.add_row(["Last Received LIE Nonce", self._last_rx_lie_nonce_local])
        tab.add_row(["Last Sent Nonce", self._last_tx_nonce_local])
        if self._increase_tx_nonce_local_holddown_timer.running():
            next_inc = self._increase_tx_nonce_local_holddown_timer.remaining_time_str()
        else:
            next_inc = "Next Packet"
        tab.add_row(["Next Sent Nonce Increase", next_inc])
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

    def traffic_stats_table(self, exclude_zero):
        return self._traffic_stats_group.table(exclude_zero)

    def security_stats_table(self, exclude_zero):
        return self._security_stats_group.table(exclude_zero)

    def lie_fsm_stats_table(self, exclude_zero):
        return self.fsm.stats_table(exclude_zero)

    def clear_stats(self):
        self._traffic_stats_group.clear()
        self.fsm.clear_stats()

    def send_tides_table(self):
        tab = table.Table()
        tab.add_row(self.cli_tides_summary_headers())
        # TODO: Make this code common with Node.send_tides_on_interface (avoid code duplication)
        if self.fsm.state == self.State.THREE_WAY:
            tide_packet = self.node.generate_tide_packet(
                neighbor_direction=self.neighbor_direction(),
                neighbor_system_id=self.neighbor.system_id,
                neighbor_level=self.neighbor.level,
                neighbor_is_top_of_fabric=self.neighbor.top_of_fabric(),
                my_level=self.node.level_value(),
                i_am_top_of_fabric=self.node.top_of_fabric())
            tab.add_row(self.cli_tides_summary_attributes(tide_packet))
        return tab

    @staticmethod
    def cli_tides_summary_headers():
        return [
            ["Start", "Range"],
            ["End", "Range"],
            "Direction",
            "Originator",
            "Type",
            "TIE Nr",
            "Seq Nr",
            ["Remaining", "Lifetime"],
            ["Origination", "Time"]]

    def cli_tides_summary_attributes(self, tide_packet):
        directions = []
        originators = []
        types = []
        tie_nrs = []
        seq_nrs = []
        remaining_lifetimes = []
        origination_times = []
        for header_lifetime in tide_packet.headers:
            header = header_lifetime.header
            directions.append(packet_common.direction_str(header.tieid.direction))
            originators.append(header.tieid.originator)
            types.append(packet_common.tietype_str(header.tieid.tietype))
            tie_nrs.append(header.tieid.tie_nr)
            seq_nrs.append(header.seq_nr)
            remaining_lifetimes.append(header_lifetime.remaining_lifetime)
            origination_times.append('-')   # TODO: Report origination_time
        return [
            packet_common.tie_id_str(tide_packet.start_range),
            packet_common.tie_id_str(tide_packet.end_range),
            directions,
            originators,
            types,
            tie_nrs,
            seq_nrs,
            remaining_lifetimes,
            origination_times]

    def tie_headers_table_cmn(self, tie_headers):
        tab = table.Table()
        tab.add_row([
            "Direction",
            "Originator",
            "Type",
            "TIE Nr",
            "Seq Nr"])
        for tie_header in tie_headers.values():
            tab.add_row([packet_common.direction_str(tie_header.tieid.direction),
                         tie_header.tieid.originator,
                         packet_common.tietype_str(tie_header.tieid.tietype),
                         tie_header.tieid.tie_nr,
                         tie_header.seq_nr])
        return tab

    def tie_headers_lifetime_table_cmn(self, tie_headers_with_lifetime):
        tab = table.Table()
        tab.add_row([
            "Direction",
            "Originator",
            "Type",
            "TIE Nr",
            "Seq Nr",
            ["Remaining", "Lifetime"]])
        for tie_header_lifetime in tie_headers_with_lifetime.values():
            header = tie_header_lifetime.header
            lifetime = tie_header_lifetime.remaining_lifetime
            tab.add_row([packet_common.direction_str(header.tieid.direction),
                         header.tieid.originator,
                         packet_common.tietype_str(header.tieid.tietype),
                         header.tieid.tie_nr,
                         header.seq_nr,
                         lifetime])
        return tab

    @staticmethod
    def word_wrap(long_line, width):
        wrapped_lines = []
        words = long_line.split()
        current_line = ""
        while words:
            word = words[0]
            words = words[1:]
            room_for_space = 0 if current_line == "" else 1
            if len(current_line) + room_for_space + len(word) > width:
                wrapped_lines.append(current_line)
                current_line = word
            else:
                if current_line != "":
                    current_line += " "
                current_line += word
        if current_line != "":
            wrapped_lines.append(current_line)
        return wrapped_lines

    def command_show_intf_packets(self, cli_session):
        cli_session.print("Last {} Packets Sent and Received on Interface:"
                          .format(self.MAX_PACKET_TRACE))
        tab = table.Table()
        prev_packet = None
        for packet in self._packets:
            lines = self.word_wrap(str(packet.packet_info), 130)
            lines = [packet.timestamp_str(prev_packet), packet.addresses_str(), ""] + lines
            tab.add_row([lines])
            prev_packet = packet
        cli_session.print(tab.to_string())

    def command_show_intf_queues(self, cli_session):
        self._queues.command_show_intf_queues(cli_session)

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
            scoped_ipv6_multicast_address = (
                str(multicast_address) + '%' + self.physical_interface_name)
            sock_addr = socket.getaddrinfo(scoped_ipv6_multicast_address, port,
                                           socket.AF_INET6, socket.SOCK_DGRAM)[0][4]
            sock.connect(sock_addr)
        except (IOError, OSError) as err:
            self.warning("Could not connect UDP socket to address %s port %d: %s",
                         scoped_ipv6_multicast_address, port, err)
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

    def activate_flood_repeater(self, force=False):
        # Returns True if activation is pending, False if not
        if self.floodred_nbr_is_fr == self.NbrIsFRState.TRUE:
            return False
        if force:
            self.floodred_nbr_is_fr = self.NbrIsFRState.TRUE
            return False
        self.floodred_nbr_is_fr = self.NbrIsFRState.PENDING_TRUE
        return True

    def deactivate_flood_repeater(self):
        # Returns True if de-activation is pending, False if not
        if self.floodred_nbr_is_fr == self.NbrIsFRState.FALSE:
            return False
        if self.floodred_nbr_is_fr == self.NbrIsFRState.NOT_APPLICABLE:
            self.floodred_nbr_is_fr = self.NbrIsFRState.FALSE
            return False
        self.floodred_nbr_is_fr = self.NbrIsFRState.PENDING_FALSE
        self.floodred_check_switchover_done()
        still_pending = (self.floodred_nbr_is_fr == self.NbrIsFRState.PENDING_FALSE)
        return still_pending

    def auth_error_counters(self):
        counters = []
        for auth_error in packet_common.PacketInfo.AUTHENTICATION_ERRORS:
            counters.append(self._error_to_counter[auth_error])
        return counters
