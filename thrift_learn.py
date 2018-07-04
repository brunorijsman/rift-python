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
