import common.constants
import table
import utils

# TODO: Store both IPv4 and IPv6 address of neighbor

class Neighbor:

    def __init__(self, lie_protocol_packet, neighbor_address, neighbor_port):
        self.system_id = lie_protocol_packet.header.sender
        self.level = lie_protocol_packet.header.level
        if utils.is_valid_ipv4_address(neighbor_address):
            self.ipv4_address = neighbor_address
            self.ipv6_address = None
        else:
            self.ipv4_address = None
            self.ipv6_address = neighbor_address
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
        self.node_capabilities = lie.node_capabilities
        self.link_capabilites = lie.link_capabilities
        self.holdtime = lie.holdtime
        self.not_a_ztp_offer = lie.not_a_ztp_offer
        self.you_are_flood_repeater = lie.you_are_flood_repeater
        self.label = lie.label

    def top_of_fabric(self):
        # TODO: Not wrong per-se, but we need to implement the TOP_OF_FABRIC logic and update
        # ZTP accordingly. Also look at capabilities.hierarchy_indications.
        return self.level == common.constants.top_of_fabric_level

    def cli_details_table(self):
        # TODO: Report capabilities (is it possible to report the unknown ones too?"
        # TODO: Report neighbor direction in show command
        if self.neighbor_system_id:
            your_system_id_str = utils.system_id_str(self.neighbor_system_id)
        else:
            your_system_id_str = ""
        if self.neighbor_link_id:
            your_link_id_str = "{}".format(self.neighbor_link_id)
        else:
            your_link_id_str = ""
        tab = table.Table(separators=False)
        tab.add_rows([
            ["Name", self.name],
            ["System ID", utils.system_id_str(self.system_id)],
            ["IPv4 Address", self.ipv4_address],
            ["IPv6 Address", self.ipv6_address],
            ["LIE UDP Source Port", self.port],
            ["Link ID", self.local_id],
            ["Level", self.level],
            ["Flood UDP Port", self.flood_port],
            ["MTU", self.link_mtu_size],
            ["POD", self.pod],
            ["Hold Time", self.holdtime],
            ["Not a ZTP Offer", self.not_a_ztp_offer],
            ["You are Flood Repeater", self.you_are_flood_repeater],
            ["Your System ID", your_system_id_str],
            ["Your Local ID", your_link_id_str],
        ])
        return tab
