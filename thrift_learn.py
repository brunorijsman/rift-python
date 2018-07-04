import sys
sys.path.append('gen-py')

from thrift.protocol import TBinaryProtocol
from thrift.transport import TTransport
from encoding.ttypes import LIEPacket

def encode(lie_packet):
    transport_out = TTransport.TMemoryBuffer()
    protocol_out = TBinaryProtocol.TBinaryProtocol(transport_out)
    lie_packet.write(protocol_out)
    encoded_msg = transport_out.getvalue()
    return encoded_msg

def decode(encoded_msg):
    transport_in = TTransport.TMemoryBuffer(encoded_msg)
    protocol_in = TBinaryProtocol.TBinaryProtocol(transport_in)
    lie_packet = LIEPacket()
    lie_packet.read(protocol_in)
    return lie_packet

lie_packet_before = LIEPacket(
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

print("Before encoding: ", lie_packet_before, "\n")

encoded_msg = encode(lie_packet_before)
print("Encoded message: ", encoded_msg, "\n")

lie_packet_after = decode(encoded_msg)
print("Adter decoding: ", lie_packet_after, "\n")

