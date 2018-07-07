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
# TODO: Find a way to detect MTU changes
# TODO: Currently, adjacencies are tied to interfaces, so I don't have a separate class for Adjacencies.
#       That may change if multipoint interfaces are supported
# TODO: Implement configuration of POD numbers
# TODO: Use propper Python logging instead of prints

class Interface:

    UNDEFINED_OR_ANY_POD = 0

    @unique
    class State(Enum):
        ONE_WAY = 1
        TWO_WAY = 2
        THREE_WAY = 3

    @unique
    class Event(Enum):
        SEND_LIE_TIMER_TICK = 1
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
        HOLD_TIMER_EXPIRED = 13
        MULTIPLE_NEIGHBORS = 14
        LIE_CORRUPT = 15
        SEND_LIE = 16
        UPDATE_ZTP_OFFER = 17

    def action_store_hal(self):
        pass

    def action_send_offer_to_ztp_fsm(self):
        pass

    state_one_way_transitions = {
        Event.SEND_LIE_TIMER_TICK: (
            None,
            [],
            [Event.SEND_LIE]
        ),
#        LEVEL_CHANGED:
        Event.HAL_CHANGED: (
            None,
            [action_store_hal]
        ),
#        HAT_CHANGED:
#        HALS_CHANGED:
#        LIE_RECEIVED:
#        NEW_NEIGHBOR:
#        VALID_REFLECTION:
#        NEIGHBOR_DROPPED_REFLECTION:
#        NEIGHBOR_CHANGED_LEVEL:
#        NEIGHBOR_CHANGED_ADDRESS:
#        UNACCEPTABLE_HEADER:
#        HOLD_TIMER_EXPIRED:
#        MULTIPLE_NEIGHBORS:
#        LIE_CORRUPT:
#        SEND_LIE:
#        UPDATE_ZTP_OFFER:
    }

    state_two_way_transitions = {
#         SEND_LIE_TIMER_TICK:
#         LEVEL_CHANGED:
        Event.HAL_CHANGED: (
            None,
            [action_store_hal]
        ),
#         HAT_CHANGED:
#         HALS_CHANGED:
#         LIE_RECEIVED:
#         NEW_NEIGHBOR:
#         VALID_REFLECTION:
#         NEIGHBOR_DROPPED_REFLECTION:
#         NEIGHBOR_CHANGED_LEVEL:
#         NEIGHBOR_CHANGED_ADDRESS:
#         UNACCEPTABLE_HEADER:
#         HOLD_TIMER_EXPIRED:
#         MULTIPLE_NEIGHBORS:
#         LIE_CORRUPT:
#         SEND_LIE:
        Event.UPDATE_ZTP_OFFER: (
            None,
            [action_send_offer_to_ztp_fsm]
        ),
     }
     
    state_three_way_transitions = {
#         SEND_LIE_TIMER_TICK:
#         LEVEL_CHANGED:
        Event.HAL_CHANGED: (
            None,
            [action_store_hal]
        ),
#         HAT_CHANGED:
#         HALS_CHANGED:
#         LIE_RECEIVED:
#         NEW_NEIGHBOR:
#         VALID_REFLECTION:
#         NEIGHBOR_DROPPED_REFLECTION:
#         NEIGHBOR_CHANGED_LEVEL:
#         NEIGHBOR_CHANGED_ADDRESS:
#         UNACCEPTABLE_HEADER:
#         HOLD_TIMER_EXPIRED:
#         MULTIPLE_NEIGHBORS:
#         LIE_CORRUPT:
#         SEND_LIE:
#         UPDATE_ZTP_OFFER:
    }

    transitions = {
        State.ONE_WAY: state_one_way_transitions,
        State.TWO_WAY: state_two_way_transitions,
        State.THREE_WAY: state_three_way_transitions
    }

    fsm = FiniteStateMachine(State, Event, transitions)

    @staticmethod
    def print_fsm(report_missing):
        pass

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

    def __init__(self, short_name, node):
        self._node = node
        self._short_name = short_name
        self._long_name = Interface.generate_long_name(short_name, node.system_id)
        self._local_id = node.allocate_interface_id()
        self._mtu = Interface.get_mtu(short_name)
        self._pod = self.UNDEFINED_OR_ANY_POD
        self._state = self.State.ONE_WAY
        self._multicast_send_handler = MulticastSendHandler(
            node.lie_ipv4_multicast_address, 
            node.lie_destination_port)
        self._multicast_receive_handler = MulticastReceiveHandler(
            node.lie_ipv4_multicast_address, 
            node.lie_destination_port,
            self.receive_multicast_message)
# TODO: put back
#        self._send_lie_timer = Timer(
#            node.lie_send_interval_secs,
#            lambda: self.process_event(SEND_LIE_TIMER_TICK))

    def create_lie_protocol_packet(self):
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
        return protocol_packet

    def receive_multicast_message(self, message):
        protocol_packet = decode_protocol_packet(message)
        # TODO: Dispatch, depending on message type
        print("Received Protocol Packet {}".format(protocol_packet))

    def action_send_lie(self):
        protocol_packet = self.create_lie_protocol_packet()
        encoded_protocol_packet = encode_protocol_packet(protocol_packet)
        self._multicast_send_handler.send_message(encoded_protocol_packet)
        print("Action send-lie {}".format(protocol_packet))

    def transition_to_state(self, state):
        print("Transition from state {} to state {}".format(state_to_string(self._state), state_to_string(state)))
        self._state = state

#    def process_event(self, event):
#        print("In state {} process event {}".format(state_to_string(self._state), to_string(event))
#        if (self._state == STATE_ONE_WAY):
#            self.state_one_way_process_event(event)
#        else if (self._state == STATE_ONE_WAY):
#            self.state_two_way_process_event(event)
#        else if (self._state == STATE_THREE_WAY):
#            self.state_three_way_process_event(event)
#        else:  
#            assert False, "Interface in unknown state {}".format(self._state)


