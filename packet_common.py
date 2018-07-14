import sys
sys.path.append('gen-py')

# TODO: Add IPv6 support
# TODO: Handle receiving malformed packets (i.e. decoding errors)

from thrift.protocol import TBinaryProtocol
from thrift.transport import TTransport
from encoding.ttypes import PacketHeader, ProtocolPacket

RIFT_MAJOR_VERSION = 11
RIFT_MINOR_VERSION = 0

# What follows are some horrible hacks to deal with the fact that Thrift only support signed 16, 32, and 64 bit numbers
# and not unsigned 16, 32, and 64 bit numbers. The RIFT specification has several fields are intended to contain an 
# unsigned 16, 32 or 64 bit number, but that are actually specified as a signed 32 or 64 bit number. Just look for the 
# following text in the specification:
#   MUST be interpreted in implementation as unsigned ...
# where ... can be 8 bits, or 1
#   MUST be interpreted in implementation as unsigned 16 bits
#   MUST be interpreted in implementation as unsigned 32 bits
#   MUST be interpreted in implementation as unsigned 64 bits
#
# 
# does not support unsigned 32 bit number or
# unsigned 64 bit numbers. We need to encode

# def encode_i64(u64):
# !TODO: Continue from here after I implement the passive flag

def create_packet_header(node):
    packet_header = PacketHeader(
        major_version = RIFT_MAJOR_VERSION,
        minor_version = RIFT_MINOR_VERSION,
        sender = node.system_id,
        level = node.advertised_level
    )
    return packet_header

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



