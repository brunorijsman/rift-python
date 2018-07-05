import sys
sys.path.append('gen-py')

# TODO: Add IPv6 support
# TODO: Handle receiving malformed packets (i.e. decoding errors)

from thrift.protocol import TBinaryProtocol
from thrift.transport import TTransport
from encoding.ttypes import PacketHeader, PacketContent, LIEPacket, ProtocolPacket

RIFT_MAJOR_VERSION = 11
RIFT_MINOR_VERSION = 0

def create_lie_protocol_packet(node):
    packet_header = PacketHeader(
        major_version = RIFT_MAJOR_VERSION,
        minor_version = RIFT_MINOR_VERSION,
        sender = node.system_id,
        level = node.advertised_level
    )
    # TODO use information in config to create LIE Packet
    lie_packet = LIEPacket(
        name = '',
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

def encode_protocol_packet(protocol_packet):
    transport_out = TTransport.TMemoryBuffer()
    protocol_out = TBinaryProtocol.TBinaryProtocol(transport_out)
    protocol_packet.write(protocol_out)
    encoded_protocol_packet = transport_out.getvalue()
    return encoded_protocol_packet

def decode_protocol_packet(encoded_protocol_packet):
    transport_in = TTransport.TMemoryBuffer(encoded_protocol_packet)
    protocol_in = TBinaryProtocol.TBinaryProtocol(transport_in)
    protocol_packet = ProtocolPacket()
    protocol_packet.read(protocol_in)
    return protocol_packet



