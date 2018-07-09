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
        if lie.neighbor:
            self.neighbor_system_id = lie.neighbor.originator
            self.neighbor_link_id = lie.neighbor.remote_id
        else:
            self.neighbor_system_id = None
            self.neighbor_link_id = None
        self.pod = lie.pod
        self.capabilities = lie.capabilities
        self.holdtime = lie.holdtime
        self.not_a_ztp_offer = lie.not_a_ztp_offer
        self.you_are_not_flood_repeater = lie.you_are_not_flood_repeater
        self.label = lie.label
    
    def cli_detailed_attributes(self):
        # TODO: Report capabilities (is it possible to report the unknown ones too?"
        return [
            ["Name", self.name],
            ["System ID", "{:016x}".format(self.system_id)],
            ["Address", self.address],
            ["Link ID", self.local_id],
            ["Level", self.level],
            ["Flood Port", self.flood_port],
            ["MTU", self.link_mtu_size],
            ["POD", self.pod],
            ["Hold Time", self.holdtime],
            ["Not a ZTP Offer", self.not_a_ztp_offer],
            ["You Are Not a ZTP Flood Repeater", self.not_a_ztp_offer],
            ["Your System ID", "{:016x}".format(self.neighbor_system_id)],
            ["Your Local ID", self.neighbor_link_id],
        ]
        return interface_attributes