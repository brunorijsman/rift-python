import os
import socket
import random
from enum import Enum, unique
from fcntl import ioctl
from multicast_send_handler import MulticastSendHandler
from multicast_receive_handler import MulticastReceiveHandler
from timer import Timer
from packet_common import create_packet_header, encode_protocol_packet, decode_protocol_packet
from encoding.ttypes import PacketHeader, PacketContent, NodeCapabilities, LIEPacket, ProtocolPacket
from common.ttypes import LeafIndications
from fsm import FiniteStateMachine

# TODO: make it possible to enable or disable RIFT on a per interface basis
# TODO: send and receive LIE message on a per interface basis
# TODO: Bind the socket to the interface (send and receive packets on that specific interface)
# TODO: LIEs arriving with a TTL larger than 1 MUST be ignored.
# TODO: Find a way to detect MTU changes on an interface
# TODO: Currently, adjacencies are tied to interfaces, so I don't have a separate class for Adjacencies.
#       That may change if multipoint interfaces are supported
# TODO: Implement configuration of POD numbers
# TODO: Use propper Python logging instead of prints

class Interface:

    UNDEFINED_OR_ANY_POD = 0

    @staticmethod
    def generate_long_name(short_name, system_id):
        hostname = socket.gethostname()
        pid = os.getpid() 
        if not hostname:
            hostname = format(system_id, 'x')
        return hostname + '-' + format(pid) + '-' + short_name

    @staticmethod
    def get_mtu(interface_name):
        # TODO: Find a portable (or even non-portable) way to get the interface MTU
        # TODO: Find a way to be informed whenever the interface MTU changes
        mtu = 1500
        return mtu

    @staticmethod
    def generate_nonce():
        # 63 bits instead of 64 because nonce field is a signed i64
        nonce = random.getrandbits(63)
        return nonce

    @unique
    class State(Enum):
        ONE_WAY = 1
        TWO_WAY = 2
        THREE_WAY = 3

    @unique
    class Event(Enum):
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
        UNACCEPTABLE_HEADER = 12
        HOLD_TIME_EXPIRED = 13
        MULTIPLE_NEIGHBORS = 14
        LIE_CORRUPT = 15
        SEND_LIE = 16
        UPDATE_ZTP_OFFER = 17

    def action_store_hal(self):
        # TODO
        pass

    def action_store_hat(self):
        # TODO
        pass

    def action_store_hals(self):
        # TODO
        pass

    def action_send_offer_to_ztp_fsm(self):
        # TODO
        pass

    def action_update_level(self):
        # TODO
        pass

    def action_send_lie(self):
        packet_header = create_packet_header(self._node)
        capabilities = NodeCapabilities(
            flood_reduction = True,
            leaf_indications = LeafIndications.leaf_only_and_leaf_2_leaf_procedures)
        lie_packet = LIEPacket(
            name = self._long_name,
            local_id = self._local_id,
            flood_port = self._node.tie_destination_port,
            link_mtu_size = self._mtu,
            neighbor = None,
            pod = self._pod,
            nonce = Interface.generate_nonce(),
            capabilities = capabilities,
            holdtime = 3,
            not_a_ztp_offer = False,
            you_are_not_flood_repeater = False,
            label = None)
        packet_content = PacketContent(lie = lie_packet)
        protocol_packet = ProtocolPacket(packet_header, packet_content)
        encoded_protocol_packet = encode_protocol_packet(protocol_packet)
        self._multicast_send_handler.send_message(encoded_protocol_packet)
        self.info(self._tx_log, "Send LIE {}".format(protocol_packet))

    def action_process_lie(self):
        # TODO
        pass

    def action_check_hold_timer_expired(self):
        # TODO
        pass

    state_one_way_transitions = {
        Event.TIMER_TICK: (None, [], [Event.SEND_LIE]),
        Event.LEVEL_CHANGED: (State.ONE_WAY, [action_update_level], [Event.SEND_LIE]),
        Event.HAL_CHANGED: (None, [action_store_hal]),
        Event.HAT_CHANGED: (None, [action_store_hat]),
        Event.HALS_CHANGED: (None, [action_store_hals]),
        Event.LIE_RECEIVED: (None, [action_process_lie]),
        Event.NEW_NEIGHBOR: (State.TWO_WAY, [], [Event.SEND_LIE]),
        Event.UNACCEPTABLE_HEADER: (State.ONE_WAY, []),
        Event.HOLD_TIME_EXPIRED: (None, []),
        Event.SEND_LIE: (None, [action_send_lie]),
        Event.UPDATE_ZTP_OFFER: (None, [action_send_offer_to_ztp_fsm])
    }

    state_two_way_transitions = {
        Event.TIMER_TICK: (None, [action_check_hold_timer_expired], [Event.SEND_LIE]),
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
        Event.HOLD_TIME_EXPIRED: (State.ONE_WAY, []),
        Event.MULTIPLE_NEIGHBORS: (State.ONE_WAY, []),
        Event.LIE_CORRUPT: (State.ONE_WAY, []),             # This transition is not in draft
        Event.SEND_LIE: (None, [action_send_lie]),
        Event.UPDATE_ZTP_OFFER: (None, [action_send_offer_to_ztp_fsm]),
     }
     
    state_three_way_transitions = {
        Event.TIMER_TICK: (None, [action_check_hold_timer_expired], [Event.SEND_LIE]),
        Event.LEVEL_CHANGED: (State.ONE_WAY, [action_update_level]),
        Event.HAL_CHANGED: (None, [action_store_hal]),
        Event.HAT_CHANGED: (None, [action_store_hat]),
        Event.HALS_CHANGED: (None, [action_store_hals]),
        Event.LIE_RECEIVED: (None, [action_process_lie]),
        Event.NEIGHBOR_DROPPED_REFLECTION: (State.TWO_WAY, []),
        Event.NEIGHBOR_CHANGED_LEVEL: (State.ONE_WAY, []),
        Event.NEIGHBOR_CHANGED_ADDRESS: (State.ONE_WAY, []),
        Event.UNACCEPTABLE_HEADER: (State.ONE_WAY, []),
        Event.HOLD_TIME_EXPIRED: (State.ONE_WAY, []),
        Event.MULTIPLE_NEIGHBORS: (State.ONE_WAY, []),
        Event.LIE_CORRUPT: (State.ONE_WAY, []),             # This transition is not in draft
        Event.SEND_LIE: (None, [action_send_lie]),
        Event.UPDATE_ZTP_OFFER: (None, [action_send_offer_to_ztp_fsm])
    }

    transitions = {
        State.ONE_WAY: state_one_way_transitions,
        State.TWO_WAY: state_two_way_transitions,
        State.THREE_WAY: state_three_way_transitions
    }

    def info(self, logger, msg):
        logger.info("[{}] {}".format(self._log_id, msg))

    def __init__(self, short_name, node):
        self._node = node
        self._short_name = short_name
        self._long_name = Interface.generate_long_name(short_name, node.system_id)
        self._log_id = node._log_id + "-{}".format(short_name)
        self._log = node._log.getChild("if")
        self.info(self._log, "Create interface")
        self._rx_log = self._log.getChild("rx")
        self._tx_log = self._log.getChild("tx")
        self._fsm_log = self._log.getChild("fsm")
        self._local_id = node.allocate_interface_id()
        self._mtu = Interface.get_mtu(short_name)
        self._pod = self.UNDEFINED_OR_ANY_POD
        self._fsm = FiniteStateMachine(
            state_enum = self.State, 
            event_enum = self.Event, 
            transitions = self.transitions, 
            initial_state = self.State.ONE_WAY,
            action_handler = self,
            log = self._fsm_log,
            log_id = self._log_id)
        self._multicast_send_handler = MulticastSendHandler(
            node.lie_ipv4_multicast_address, 
            node.lie_destination_port)
        self._multicast_receive_handler = MulticastReceiveHandler(
            node.lie_ipv4_multicast_address, 
            node.lie_destination_port,
            self.receive_multicast_message)
        self._one_second_timer = Timer(1.0, lambda: self._fsm.push_event(self.Event.TIMER_TICK))

    def receive_multicast_message(self, message):
        protocol_packet = decode_protocol_packet(message)
        self.info(self._rx_log, "Receive {}".format(protocol_packet))
        # TODO: Dispatch, depending on message type
