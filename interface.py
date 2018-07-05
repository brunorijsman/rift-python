import os
import socket
from multicast_send_handler import MulticastSendHandler
from multicast_receive_handler import MulticastReceiveHandler
from timer import Timer
from packet_common import create_packet_header, encode_protocol_packet, decode_protocol_packet
from encoding.ttypes import PacketHeader, PacketContent, LIEPacket, ProtocolPacket

# TODO: make it possible to enable or disable RIFT on a per interface basis
# TODO: send and receive LIE message on a per interface basis
# TODO: Bind the socket to the interface (send and receive packets on that specific interface)
# TODO: LIEs arriving with a TTL larger than 1 MUST be ignored.

class Interface:

    @staticmethod
    def generate_long_name(short_name, system_id):
        hostname = socket.gethostname()
        pid = os.getpid() 
        if not hostname:
            hostname = format(system_id, 'x')
        return hostname + '-' + format(pid) + '-' + short_name

    def __init__(self, short_name, node):
        self._short_name = short_name
        self._long_name = Interface.generate_long_name(short_name, node.system_id)
        self._node = node
        self._multicast_send_handler = MulticastSendHandler(
            node.lie_ipv4_multicast_address, 
            node.lie_destination_port)
        self._multicast_receive_handler = MulticastReceiveHandler(
            node.lie_ipv4_multicast_address, 
            node.lie_destination_port,
            self.receive_multicast_message)
        self._send_timer = Timer(
            node.lie_send_interval_secs,
            self.send_lie_protocol_packet)

    def create_lie_protocol_packet(self):
        packet_header = create_packet_header(self._node)
        # TODO use information in config to create LIE Packet
        lie_packet = LIEPacket(
            name = self._long_name,
            local_id = None,
            flood_port = 912,        # TODO: Is this the right default?
            link_mtu_size = 1400,
            neighbor = None,
            pod = 0,
            nonce = None,
            capabilities = None,
            holdtime = 3,            # TODO: Should this be hold_time?
            not_a_ztp_offer = False,
            you_are_not_flood_repeater = False,
            label = None)
        packet_content = PacketContent(lie = lie_packet)
        protocol_packet = ProtocolPacket(packet_header, packet_content)
        return protocol_packet

    def send_lie_protocol_packet(self):
        protocol_packet = self.create_lie_protocol_packet()
        encoded_protocol_packet = encode_protocol_packet(protocol_packet)
        self._multicast_send_handler.send_message(encoded_protocol_packet)
        print("Sent LIE Protocol Packet {}".format(protocol_packet))

    def receive_multicast_message(self, message):
        protocol_packet = decode_protocol_packet(message)
        # TODO: Dispatch, depending on message type
        print("Received Protocol Packet {}".format(protocol_packet))

