#from encoding.ttypes import PacketHeader, PacketContent, ProtocolPacket, LIEPacket

# TODO: Should we rename this to adjacency? The current draft mixes terms neighbor and adjacency.

# Note: I made this a separate class, so that it will be easier to have multiple neighbors (adjacencies) on a single
#       interface if and when the draft gets uptdate to support mulitple neighbors (adjacencies) on a multi-point LAN.

# TODO: Store both IPv4 and IPv6 address of neighbor

class Neighbor:

    def __init__(self, lie_protocol_packet):
        self.system_id = lie_protocol_packet.header.sender
        self.level = lie_protocol_packet.header.level
        self.address = None                                 # TODO: use source address of received LIE packet
        lie = lie_protocol_packet.content.lie
        self.name = lie.name
        self.local_id = lie.local_id
        self.flood_port = lie.flood_port
        self.link_mtu_size = lie.link_mtu_size
        self.neighbor_system_id = lie.neighbor
        self.pod = lie.pod
        self.capabilities = lie.capabilities
        self.holdtime = lie.holdtime
        self.not_a_ztp_offer = lie.not_a_ztp_offer
        self.you_are_not_flood_repeater = lie.you_are_not_flood_repeater
        self.label = lie.label
