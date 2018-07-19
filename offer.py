import utils
import common.constants

# TODO: Should we rename this to adjacency? The current draft mixes terms neighbor and adjacency.

# Note: I made this a separate class, so that it will be easier to have multiple neighbors (adjacencies) on a single
#       interface if and when the draft gets uptdate to support mulitple neighbors (adjacencies) on a multi-point LAN.

# TODO: Store both IPv4 and IPv6 address of neighbor

class Offer:

    def __init__(self, lie_protocol_packet, neighbor_address, neighbor_port):
        self.system_id = lie_protocol_packet.header.sender
        self.level = lie_protocol_packet.header.level
        self.address = neighbor_address
        self.port = neighbor_port
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
        self.not_a_ztp_offer = lie.not_a_ztp_offer

    def is_a_ztp_offer(self):
        if self.level == None:
            return False
        if self.level == common.constants.leaf_level:
            return False
        if self.not_a_ztp_offer:
            return False
        return True


    def cli_detailed_attributes(self):
        # TODO: Report capabilities (is it possible to report the unknown ones too?"
        if self.neighbor_system_id:
            your_system_id_str = utils.system_id_str(self.neighbor_system_id)
        else:
            your_system_id_str = ""
        if self.neighbor_link_id:
            your_link_id_str = "{}".format(self.neighbor_link_id)
        else:
            your_link_id_str = ""
        attributes = [
            ["Name", self.name],
            ["System ID", utils.system_id_str(self.system_id)],
            ["IPv4 Address", self.address],
            ["LIE UDP Source Port", self.port],
            ["Link ID", self.local_id],
            ["Level", self.level],
            ["Flood UDP Port", self.flood_port],
            ["MTU", self.link_mtu_size],
            ["POD", self.pod],
            ["Hold Time", self.holdtime],
            ["Not a ZTP Offer", self.not_a_ztp_offer],
            ["You Are Not a ZTP Flood Repeater", self.not_a_ztp_offer],
            ["Your System ID", your_system_id_str],
        ]
        return attributes