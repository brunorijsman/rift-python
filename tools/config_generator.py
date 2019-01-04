#!/usr/bin/env python3

import argparse
import os
import pprint
import stat

import sys
import cerberus
import yaml

META_CONFIG = None
ARGS = None

DEFAULT_NR_IPV4_LOOPBACKS = 1

NODE_SCHEMA = {
    'type': 'dict',
    'schema': {
        'nr-ipv4-loopbacks': {'type': 'integer', 'min': 0, 'default': DEFAULT_NR_IPV4_LOOPBACKS}
    }
}

SCHEMA = {
    'nr-leaf-nodes-per-pod': {'required': True, 'type': 'integer', 'min': 1},
    'nr-pods': {'required': False, 'type': 'integer', 'min': 1, 'default': 1},
    'nr-spine-nodes-per-pod': {'required': True, 'type': 'integer', 'min': 1},
    'nr-superspine-nodes': {'required': False, 'type': 'integer', 'min': 1},
    'leafs': NODE_SCHEMA,
    'spines': NODE_SCHEMA
}

SOUTH = 1
NORTH = 2

LEAF_LEVEL = 0
SPINE_LEVEL = 1
SUPERSPINE_LEVEL = 2

GLOBAL_X_OFFSET = 10
GLOBAL_Y_OFFSET = 10
SUPERSPINE_TO_POD_Y_INTERVAL = 140
GROUP_X_INTERVAL = 30
GROUP_X_SPACER = 24
GROUP_Y_SPACER = 24
GROUP_X_TEXT_OFFSET = 8
GROUP_Y_TEXT_OFFSET = 16
GROUP_LINE_COLOR = "black"
GROUP_FILL_COLOR = "#F0F0F0"
NODE_X_SIZE = 100
NODE_Y_SIZE = 50
NODE_X_INTERVAL = 20
NODE_Y_INTERVAL = 100
NODE_LINE_COLOR = "black"
NODE_FILL_COLOR = "silver"
LINK_COLOR = "black"
LINK_WIDTH = "1"
LINK_HIGHLIGHT_WIDTH = "3"
INTF_COLOR = "black"
INTF_RADIUS = "3"
INTF_HIGHLIGHT_RADIUS = "5"
HIGHLIGHT_COLOR = "red"

END_OF_SVG = """
<script type="text/javascript"><![CDATA[

function CreateNodeHighlightFunc(node) {
    return function() {
        rect = node.getElementsByClassName('node-rect')[0]
        rect.setAttribute("fill", "HIGHLIGHT_COLOR")
    }
}

function CreateNodeNormalFunc(node) {
    return function() {
        rect = node.getElementsByClassName('node-rect')[0]
        rect.setAttribute("fill", "NODE_FILL_COLOR")
    }
}

var nodes = document.getElementsByClassName('node');
for (var i = 0; i < nodes.length; i++) {
    node = nodes[i]
    node.addEventListener('mouseover', CreateNodeHighlightFunc(node));
    node.addEventListener('mouseout', CreateNodeNormalFunc(node));
}

function CreateLinkHighlightFunc(link) {
    return function() {
        line = link.getElementsByClassName('link-line')[0]
        line.setAttribute("style", "stroke:HIGHLIGHT_COLOR;stroke-width:LINK_HIGHLIGHT_WIDTH")
        for (var i = 0; i < 2; i++) {
            intf = link.getElementsByClassName('intf')[i]
            intf.setAttribute("style", "stroke:HIGHLIGHT_COLOR")
            intf.setAttribute("fill", "HIGHLIGHT_COLOR")
            intf.setAttribute("r", "INTF_HIGHLIGHT_RADIUS")
        }
    }
}

function CreateLinkNormalFunc(link) {
    return function() {
        line = link.getElementsByClassName('link-line')[0]
        line.setAttribute("style", "stroke:LINK_COLOR;stroke-width:LINK_WIDTH")
        for (var i = 0; i < 2; i++) {
            intf = link.getElementsByClassName('intf')[i]
            intf.setAttribute("style", "stroke:INTF_COLOR")
            intf.setAttribute("fill", "INTF_COLOR")
            intf.setAttribute("r", "INTF_RADIUS")
        }
    }
}

var links = document.getElementsByClassName('link');
for (var i = 0; i < links.length; i++) {
    link = links[i]
    link.addEventListener('mouseover', CreateLinkHighlightFunc(link));
    link.addEventListener('mouseout', CreateLinkNormalFunc(link));
}

]]></script>

</svg>
"""

END_OF_SVG = END_OF_SVG.replace("NODE_LINE_COLOR", NODE_LINE_COLOR)
END_OF_SVG = END_OF_SVG.replace("NODE_FILL_COLOR", NODE_FILL_COLOR)
END_OF_SVG = END_OF_SVG.replace("LINK_COLOR", LINK_COLOR)
END_OF_SVG = END_OF_SVG.replace("LINK_WIDTH", LINK_WIDTH)
END_OF_SVG = END_OF_SVG.replace("LINK_HIGHLIGHT_WIDTH", LINK_HIGHLIGHT_WIDTH)
END_OF_SVG = END_OF_SVG.replace("INTF_COLOR", INTF_COLOR)
END_OF_SVG = END_OF_SVG.replace("INTF_RADIUS", INTF_RADIUS)
END_OF_SVG = END_OF_SVG.replace("INTF_HIGHLIGHT_RADIUS", INTF_HIGHLIGHT_RADIUS)
END_OF_SVG = END_OF_SVG.replace("HIGHLIGHT_COLOR", HIGHLIGHT_COLOR)

def generate_ipv4_address_str(byte1, byte2, byte3, byte4, offset):
    assert offset <= 65535
    byte4 += offset
    byte3 += byte4 // 256
    byte4 %= 256
    byte2 += byte3 // 256
    byte3 %= 256
    byte1 += byte2 // 256
    byte2 %= 256
    ip_address_str = "{}.{}.{}.{}".format(byte1, byte2, byte3, byte4)
    return ip_address_str

class Group:

    def __init__(self, fabric, name, group_index, only_instance, y_pos, y_size):
        self.fabric = fabric
        self.name = name
        self.group_index = group_index
        self.only_instance = only_instance
        self.given_y_pos = y_pos
        self.given_y_size = y_size
        self.x_center_shift = 0
        self.nodes = []
        self.nodes_by_level = {}
        self.links = []

    def create_node(self, name, level, index_in_level, y_pos):
        node = Node(self, name, level, index_in_level, y_pos)
        # TODO: Move adding of loopbacks to here
        self.nodes.append(node)
        if level not in self.nodes_by_level:
            self.nodes_by_level[level] = []
        self.nodes_by_level[level].append(node)
        return node

    def create_link(self, from_node, to_node):
        link = Link(from_node, to_node)
        self.links.append(link)
        return link

    def node_name(self, base_name, node_index_in_level):
        if self.only_instance:
            return base_name + "-" + str(node_index_in_level + 1)
        else:
            return base_name + "-" + str(self.group_index + 1) + "-" + str(node_index_in_level + 1)

    def write_config_to_file(self, file, netns):
        for node in self.nodes:
            node.write_config_to_file(file, netns)

    def write_netns_configs_and_scripts(self):
        for node in self.nodes:
            node.write_netns_configs_and_scripts()

    # TODO: Split this in phase1 and phase2 at a higher level
    def write_netns_start_scr_to_file(self, file):
        for link in self.links:
            link.write_netns_start_scr_to_file(file)
        for node in self.nodes:
            node.write_netns_start_scr_to_file_1(file)
        for node in self.nodes:
            node.write_netns_start_scr_to_file_2(file)

    def write_graphics_to_file(self, file):
        x_pos = self.x_pos()
        y_pos = self.y_pos()
        x_size = self.x_size()
        y_size = self.y_size()
        file.write('<rect '
                   'x="{}" '
                   'y="{}" '
                   'width="{}" '
                   'height="{}" '
                   'fill="{}" '
                   'style="stroke:{}" '
                   '></rect>'
                   .format(x_pos, y_pos, x_size, y_size, GROUP_FILL_COLOR, GROUP_LINE_COLOR))
        if not self.only_instance:
            x_pos += GROUP_X_TEXT_OFFSET
            y_pos += GROUP_Y_TEXT_OFFSET
            file.write('<text '
                       'x="{}" '
                       'y="{}" '
                       'style="font-family:monospace;stroke:{}">'
                       '{}'
                       '</text>\n'
                       .format(x_pos, y_pos, GROUP_LINE_COLOR, self.name))
        for node in self.nodes:
            node.write_graphics_to_file(file)
        for link in self.links:
            link.write_graphics_to_file(file)

    def x_pos(self):
        # X position of top-left corner of rectangle representing the group
        x_pos = GLOBAL_X_OFFSET
        x_pos += self.group_index * (self.x_size() + GROUP_X_INTERVAL)
        x_pos += self.x_center_shift
        return x_pos

    def y_pos(self):
        return self.given_y_pos

    def nr_nodes_in_widest_level(self):
        result = 0
        for nodes_in_level_list in self.nodes_by_level.values():
            nr_nodes_in_level = len(nodes_in_level_list)
            result = max(result, nr_nodes_in_level)
        return result

    def x_size(self):
        width_nodes = self.nr_nodes_in_widest_level()
        width = width_nodes * NODE_X_SIZE
        width += (width_nodes - 1) * NODE_X_INTERVAL
        width += 2 * GROUP_X_SPACER   # TODO: Change to GROUP_X_SPACER
        return width

    def y_size(self):
        return self.given_y_size

    def first_node_x_pos(self, level):
        width_nodes = self.nr_nodes_in_widest_level()
        missing_nodes = width_nodes - len(self.nodes_by_level[level])
        padding_width = missing_nodes * (NODE_X_SIZE + NODE_X_INTERVAL) // 2
        return self.x_pos() + padding_width + GROUP_X_SPACER

    def nr_levels(self):
        return len(self.nodes_by_level)

class Pod(Group):

    def __init__(self, fabric, pod_name, pod_index, only_pod, y_pos):
        y_size = 2 * NODE_Y_SIZE + NODE_Y_INTERVAL + 2 * GROUP_Y_SPACER
        Group.__init__(self, fabric, pod_name, pod_index, only_pod, y_pos, y_size)
        self.leaf_nodes = []
        self.spine_nodes = []
        self.nr_leaf_nodes = META_CONFIG['nr-leaf-nodes-per-pod']
        # TODO: Make nr-ipv4-loopbacks a global knob
        if 'leafs' in META_CONFIG:
            self.leaf_nr_ipv4_loopbacks = META_CONFIG['leafs']['nr-ipv4-loopbacks']
        else:
            self.leaf_nr_ipv4_loopbacks = DEFAULT_NR_IPV4_LOOPBACKS
        self.nr_spine_nodes = META_CONFIG['nr-spine-nodes-per-pod']
        if 'spines' in META_CONFIG:
            self.spine_nr_ipv4_loopbacks = META_CONFIG['spines']['nr-ipv4-loopbacks']
        else:
            self.spine_nr_ipv4_loopbacks = DEFAULT_NR_IPV4_LOOPBACKS
        self.nr_superspine_nodes = 0
        self.create_leaf_nodes()
        self.create_spine_nodes()
        self.create_leaf_spine_links()

    def create_leaf_nodes(self):
        y_pos = self.y_pos() + GROUP_Y_SPACER + NODE_Y_SIZE + NODE_Y_INTERVAL
        for index in range(0, self.nr_leaf_nodes):
            node_name = self.node_name("leaf", index)
            node = self.create_node(node_name, LEAF_LEVEL, index, y_pos)
            node.add_ipv4_loopbacks(self.leaf_nr_ipv4_loopbacks)
            self.leaf_nodes.append(node)

    def create_spine_nodes(self):
        y_pos = self.y_pos() + GROUP_Y_SPACER
        for index in range(0, self.nr_spine_nodes):
            node_name = self.node_name("spine", index)
            node = self.create_node(node_name, SPINE_LEVEL, index, y_pos)
            node.add_ipv4_loopbacks(self.spine_nr_ipv4_loopbacks)
            self.spine_nodes.append(node)

    def create_leaf_spine_links(self):
        for leaf_node in self.leaf_nodes:
            for spine_node in self.spine_nodes:
                _link = self.create_link(leaf_node, spine_node)

class Plane(Group):

    def __init__(self, fabric, plane_name, plane_index, only_plane, y_pos):
        y_size = NODE_Y_SIZE + 2 * GROUP_Y_SPACER
        Group.__init__(self, fabric, plane_name, plane_index, only_plane, y_pos, y_size)
        self.superspine_nodes = []
        self.superspine_spine_links = []
        self.nr_leaf_nodes = 0
        self.nr_spine_nodes = 0
        self.nr_superspine_nodes = META_CONFIG['nr-superspine-nodes']
        # TODO: Make nr-ipv4-loopbacks a global knob
        self.superspine_nr_ipv4_loopbacks = 1
        self.create_superspine_nodes()

    def create_superspine_nodes(self):
        y_pos = self.y_pos() + GROUP_Y_SPACER
        for index in range(0, self.nr_superspine_nodes):
            node_name = self.node_name("super", index)   # TODO: Index per group type
            node = self.create_node(node_name, SUPERSPINE_LEVEL, index, y_pos)
            node.add_ipv4_loopbacks(self.superspine_nr_ipv4_loopbacks)
            self.superspine_nodes.append(node)

class Node:

    next_node_id = 1

    def __init__(self, group, name, level, index_in_level, y_pos):
        self.group = group
        self.name = name
        self.node_id = Node.next_node_id
        Node.next_node_id += 1
        self.level = level
        self.index_in_level = index_in_level
        self.given_y_pos = y_pos
        self.rx_lie_mcast_addr = generate_ipv4_address_str(224, 0, 1, 0, self.node_id)
        self.interfaces = []
        self.ipv4_prefixes = []
        self.lo_addr = generate_ipv4_address_str(88, 0, 0, 0, 1) + "/32"
        self.config_file_name = None

    def add_ipv4_loopbacks(self, count):
        for index in range(1, count+1):
            offset = self.node_id * 256 + index
            address = generate_ipv4_address_str(88, 0, 0, 0, offset)
            mask = "32"
            metric = "1"
            prefix = (address, mask, metric)
            self.ipv4_prefixes.append(prefix)

    def create_interface(self):
        intf_index = len(self.interfaces) + 1
        interface = Interface(self, intf_index)
        self.interfaces.append(interface)
        return interface

    def interface_dir_index(self, interface):
        # Of all the interfaces on the node in the same direction as the given interface, what
        # is the index of the interface? Is it the 0th, the 1st, the 2nd, etc. interface in that
        # particular direction? Note that the index is zero-based.
        index = 0
        for check_interface in self.interfaces:
            if check_interface == interface:
                return index
            if check_interface.direction == interface.direction:
                index += 1
        return None

    def interface_dir_count(self, direction):
        # How many interfaces in the given direction does this node have?
        count = 0
        for interface in self.interfaces:
            if interface.direction == direction:
                count += 1
        return count

    def write_config_to_file(self, file, netns):
        if netns:
            print("shards:", file=file)
            print("  - id: 0", file=file)
            print("    nodes:", file=file)
        print("      - name: " + self.name, file=file)
        print("        level: " + str(self.level), file=file)
        print("        systemid: " + str(self.node_id), file=file)
        if not netns:
            print("        rx_lie_mcast_address: " + self.rx_lie_mcast_addr, file=file)
        print("        interfaces:", file=file)
        for intf in self.interfaces:
            description = "{} -> {}".format(intf.fq_name(), intf.peer_intf.fq_name())
            if netns:
                print("          - name: " + intf.veth_name(), file=file)
            else:
                print("          - name: " + intf.name(), file=file)
            print("            # " + description, file=file)
            print("            rx_lie_port: " + str(intf.rx_lie_port), file=file)
            print("            tx_lie_port: " + str(intf.tx_lie_port), file=file)
            print("            rx_tie_port: " + str(intf.rx_tie_port), file=file)
        print("        v4prefixes:", file=file)
        for prefix in self.ipv4_prefixes:
            (address, mask, metric) = prefix
            print("          - address: " + address, file=file)
            print("            mask: " + mask, file=file)
            print("            metric: " + metric, file=file)

    def write_netns_configs_and_scripts(self):
        self.write_netns_config()
        self.write_netns_connect_script()

    def write_netns_config(self):
        dir_name = getattr(ARGS, 'output-file-or-dir')
        file_name = dir_name + '/' + self.name + ".yaml"
        self.config_file_name = os.path.realpath(file_name)
        try:
            with open(file_name, 'w') as file:
                self.write_config_to_file(file, netns=True)
        except IOError:
            fatal_error('Could not open output node configuration file "{}"'.format(file_name))

    def write_netns_connect_script(self):
        dir_name = getattr(ARGS, 'output-file-or-dir')
        file_name = "{}/connect-{}.sh".format(dir_name, self.name)
        try:
            with open(file_name, 'w') as file:
                ns_name = "netns-" + str(self.node_id)
                port_file = "/tmp/rift-python-telnet-port-" + self.name
                print("ip netns exec {} telnet localhost $(cat {})".format(ns_name, port_file),
                      file=file)
        except IOError:
            fatal_error('Could not open start script file "{}"'.format(file_name))
        try:
            existing_stat = os.stat(file_name)
            os.chmod(file_name, existing_stat.st_mode | stat.S_IXUSR)
        except IOError:
            fatal_error('Could name make "{}" executable'.format(file_name))

    def write_netns_start_scr_to_file_1(self, file):
        progress = ("Create netns for node {}".format(self.name))
        print('echo "{}"'.format(progress), file=file)
        ns_name = "netns-" + str(self.node_id)
        print("ip netns add {}".format(ns_name), file=file)
        addr = self.lo_addr
        print("ip netns exec {} ip link set dev lo up".format(ns_name), file=file)
        print("ip netns exec {} ip addr add {} dev lo".format(ns_name, addr), file=file)
        for intf in self.interfaces:
            veth = intf.veth_name()
            addr = intf.addr
            print("ip link set {} netns {}".format(veth, ns_name), file=file)
            print("ip netns exec {} ip link set dev {} up".format(ns_name, veth), file=file)
            print("ip netns exec {} ip addr add {} dev {}".format(ns_name, addr, veth), file=file)

    def write_netns_start_scr_to_file_2(self, file):
        progress = ("Start RIFT-Python engine for node {}".format(self.name))
        print('echo "{}"'.format(progress), file=file)
        ns_name = "netns-" + str(self.node_id)
        port_file = "/tmp/rift-python-telnet-port-" + self.name
        print("ip netns exec {} python3 rift --multicast-loopback-disable "
              "--telnet-port-file {} {} < /dev/null &"
              .format(ns_name, port_file, self.config_file_name), file=file)

    def write_graphics_to_file(self, file):
        x_pos = self.x_pos()
        y_pos = self.y_pos()
        file.write('<g class="node">\n')
        file.write('<rect '
                   'x="{}" '
                   'y="{}" '
                   'width="{}" '
                   'height="{}" '
                   'fill="{}" '
                   'style="stroke:{}" '
                   'class="node-rect" '
                   '></rect>'
                   .format(x_pos, y_pos, NODE_X_SIZE, NODE_Y_SIZE, NODE_FILL_COLOR,
                           NODE_LINE_COLOR))
        y_pos += NODE_Y_SIZE // 2
        x_pos += NODE_X_SIZE // 10
        file.write('<text '
                   'x="{}" '
                   'y="{}" '
                   'style="font-family:monospace; dominant-baseline:central; stroke:{}">'
                   '{}'
                   '</text>\n'
                   .format(x_pos, y_pos, NODE_LINE_COLOR, self.name))
        file.write('</g>\n')

    def x_pos(self):
        # X position of top-left corner of rectangle representing the node
        x_delta = self.index_in_level * (NODE_X_SIZE + NODE_X_INTERVAL)
        return self.group.first_node_x_pos(self.level) + x_delta

    def y_pos(self):
        # Y position of top-left corner of rectangle representing the node
        return self.given_y_pos

class Interface:

    next_interface_id = 1

    def __init__(self, node, intf_index):
        self.node = node
        self.intf_id = Interface.next_interface_id  # Globally unique identifier for interface
        Interface.next_interface_id += 1
        self.intf_index = intf_index  # Local index for interface, unique within scope of node
        self.peer_intf = None
        self.direction = None
        self.rx_lie_port = None
        self.tx_lie_port = None
        self.rx_tie_port = None
        self.addr = None

    def set_peer_intf(self, peer_intf):
        self.peer_intf = peer_intf
        peer_node = peer_intf.node
        if peer_node.level < self.node.level:
            self.direction = SOUTH
        else:
            self.direction = NORTH
        self.rx_lie_port = 20000 + self.intf_id
        self.tx_lie_port = 20000 + self.peer_intf.intf_id
        self.rx_tie_port = 10000 + self.intf_id
        lower = min(self.intf_id, self.peer_intf.intf_id)
        upper = max(self.intf_id, self.peer_intf.intf_id)
        self.addr = "99.{}.{}.{}/24".format(lower, upper, self.intf_id)

    def name(self):
        return "if" + str(self.intf_index)

    def fq_name(self):
        return self.node.name + ":" + self.name()

    def veth_name(self):
        return "veth" + "-" + str(self.intf_id) + "-" + str(self.peer_intf.intf_id)

    def write_graphics_to_file(self, file):
        x_pos = self.x_pos()
        y_pos = self.y_pos()
        file.write('<circle '
                   'cx="{}" '
                   'cy="{}" '
                   'r="{}" '
                   'style="stroke:{};fill:{}" '
                   'class="intf">'
                   '</circle>\n'
                   .format(x_pos, y_pos, INTF_RADIUS, INTF_COLOR, INTF_COLOR))

    def x_pos(self):
        # X position of center of circle representing interface
        node_intf_dir_count = self.node.interface_dir_count(self.direction)
        intf_dir_index = self.node.interface_dir_index(self)
        intf_x_dist = NODE_X_SIZE / (node_intf_dir_count + 1)
        return self.node.x_pos() + intf_x_dist * (intf_dir_index + 1)

    def y_pos(self):
        # Y position of center of circle representing interface
        if self.direction == NORTH:
            return self.node.y_pos()
        else:
            return self.node.y_pos() + NODE_Y_SIZE

class Link:

    def __init__(self, node1, node2):
        self.intf1 = node1.create_interface()
        self.intf2 = node2.create_interface()
        self.intf1.set_peer_intf(self.intf2)
        self.intf2.set_peer_intf(self.intf1)

    def write_netns_start_scr_to_file(self, file):
        progress = ("Create veth pair for link from {} to {}"
                    .format(self.intf1.fq_name(), self.intf2.fq_name()))
        print('echo "{}"'.format(progress), file=file)
        veth1_name = self.intf1.veth_name()
        veth2_name = self.intf2.veth_name()
        print("ip link add dev {} type veth peer name {}".format(veth1_name, veth2_name), file=file)

    def write_graphics_to_file(self, file):
        x_pos1 = self.intf1.x_pos()
        y_pos1 = self.intf1.y_pos()
        x_pos2 = self.intf2.x_pos()
        y_pos2 = self.intf2.y_pos()
        file.write('<g class="link">\n')
        file.write('<line '
                   'x1="{}" '
                   'y1="{}" '
                   'x2="{}" '
                   'y2="{}" '
                   'style="stroke:{};" '
                   'class="link-line">'
                   '</line>\n'
                   .format(x_pos1, y_pos1, x_pos2, y_pos2, LINK_COLOR))
        self.intf1.write_graphics_to_file(file)
        self.intf2.write_graphics_to_file(file)
        file.write('</g>\n')

class Fabric:

    def __init__(self):
        self.nr_pods = META_CONFIG['nr-pods']
        self.pods = []
        self.planes = []
        pods_y_pos = GLOBAL_Y_OFFSET
        # Only generate superspine nodes and planes if there is more than one pod
        if self.nr_pods > 1:
            nr_planes = 1   # TODO: Implement multi-plane
            only_plane = (nr_planes == 1)
            planes_y_pos = GLOBAL_Y_OFFSET
            pods_y_pos += NODE_Y_SIZE + SUPERSPINE_TO_POD_Y_INTERVAL
            for index in range(0, nr_planes):
                plane_name = "plane-" + str(index + 1)
                pod = Plane(self, plane_name, index, only_plane, planes_y_pos)
                self.planes.append(pod)
        # Generate the pods with leaf and spine nodes within them
        only_pod = (self.nr_pods == 1)
        for index in range(0, self.nr_pods):
            pod_name = "pod-" + str(index + 1)
            pod = Pod(self, pod_name, index, only_pod, pods_y_pos)
            self.pods.append(pod)
        # Center the pods and planes
        pod_x_center_shift = (self.x_size() - self.pods_total_x_size()) // 2
        for pod in self.pods:
            pod.x_center_shift = pod_x_center_shift
        plane_x_center_shift = (self.x_size() - self.planes_total_x_size()) // 2
        for plane in self.planes:
            plane.x_center_shift = plane_x_center_shift
        # Generate the links between the superspine nodes and the spine nodes
        if self.planes:
            # TODO: Add support for multi-plane
            self.create_links_single_plane()

    def create_links_single_plane(self):
        # Superspine to spine links (single plane)
        assert len(self.planes) == 1
        plane = self.planes[0]
        for superspine_node in plane.nodes:
            for pod in self.pods:
                for spine_node in pod.nodes_by_level[SPINE_LEVEL]:
                    _link = plane.create_link(superspine_node, spine_node)

    def write_config(self):
        file_name = getattr(ARGS, 'output-file-or-dir')
        if file_name is None:
            self.write_config_to_file(sys.stdout, netns=False)
        else:
            try:
                with open(file_name, 'w') as file:
                    self.write_config_to_file(file, netns=False)
            except IOError:
                fatal_error('Could not open output configuration file "{}"'.format(file_name))

    def write_config_to_file(self, file, netns):
        print("shards:", file=file)
        print("  - id: 0", file=file)
        print("    nodes:", file=file)
        for pod in self.pods:
            pod.write_config_to_file(file, netns)
        for plane in self.planes:
            plane.write_config_to_file(file, netns)

    def write_netns_configs_and_scripts(self):
        dir_name = getattr(ARGS, 'output-file-or-dir')
        if dir_name is None:
            fatal_error("Output directory name is missing (mandatory for --netns)")
        try:
            os.mkdir(dir_name)
        except FileExistsError:
            fatal_error("Output directory '{}' already exists".format(dir_name))
        except IOError:
            fatal_error("Could not create output directory '{}'".format(dir_name))
        for pod in self.pods:
            pod.write_netns_configs_and_scripts()
        self.write_netns_start_script()

    def write_netns_start_script(self):
        dir_name = getattr(ARGS, 'output-file-or-dir')
        file_name = dir_name + "/start.sh"
        try:
            with open(file_name, 'w') as file:
                self.write_netns_start_scr_to_file(file)
        except IOError:
            fatal_error('Could not open start script file "{}"'.format(file_name))
        try:
            existing_stat = os.stat(file_name)
            os.chmod(file_name, existing_stat.st_mode | stat.S_IXUSR)
        except IOError:
            fatal_error('Could not make "{}" executable'.format(file_name))

    def write_progress_msg(self, file, message):
        print('echo "{}"'.format(message), file=file)

    def write_netns_start_scr_to_file(self, file):
        for pod in self.pods:
            pod.write_netns_start_scr_to_file(file)

    def write_graphics(self):
        file_name = ARGS.graphics_file
        assert file_name is not None
        try:
            with open(file_name, 'w') as file:
                self.write_graphics_to_file(file)
        except IOError:
            fatal_error('Could not open start graphics file "{}"'.format(file_name))

    def write_graphics_to_file(self, file):
        self.svg_start(file)
        for pod in self.pods:
            pod.write_graphics_to_file(file)
        for plane in self.planes:
            plane.write_graphics_to_file(file)
        self.svg_end(file)

    def svg_start(self, file):
        file.write('<svg '
                   'xmlns="http://www.w3.org/2000/svg '
                   'xmlns:xlink="http://www.w3.org/1999/xlink" '
                   'width=1000000 '
                   'height=1000000 '
                   'id="tooltip-svg">\n')

    def svg_end(self, file):
        file.write(END_OF_SVG)

    def pods_total_x_size(self):
        total_x_size = 0
        for pod in self.pods:
            total_x_size += pod.x_size() + GROUP_X_INTERVAL
        if total_x_size > 0:
            total_x_size -= GROUP_X_INTERVAL
        return total_x_size

    def planes_total_x_size(self):
        total_x_size = 0
        for plane in self.planes:
            total_x_size += plane.x_size() + GROUP_X_INTERVAL
        if total_x_size > 0:
            total_x_size -= GROUP_X_INTERVAL
        return total_x_size

    def x_size(self):
        return max(self.pods_total_x_size(), self.planes_total_x_size())

def parse_meta_configuration(file_name):
    try:
        with open(file_name, 'r') as stream:
            try:
                config = yaml.load(stream)
            except yaml.YAMLError as exception:
                raise exception
    except IOError:
        fatal_error('Could not open input meta-configuration file "{}"'.format(file_name))
    validator = cerberus.Validator()
    if not validator.validate(config, SCHEMA):
        pretty_printer = pprint.PrettyPrinter()
        pretty_printer.pprint(validator.errors)
        exit(1)
    return validator.normalized(config)

def validate_meta_configuration():
    nr_pods = META_CONFIG['nr-pods']
    if 'nr-superspine-nodes' in META_CONFIG:
        nr_superspine_nodes = META_CONFIG['nr-superspine-nodes']
    else:
        nr_superspine_nodes = None
    if (nr_pods > 1) and (nr_superspine_nodes is None):
        fatal_error("nr-superspine-nodes must be configured if number of PODs > 1")
    if (nr_pods == 1) and (nr_superspine_nodes is not None):
        fatal_error("nr-superspine-nodes must not be configured if there is only one POD")

def parse_command_line_arguments():
    parser = argparse.ArgumentParser(description='RIFT configuration fabric')
    parser.add_argument(
        'input-meta-config-file',
        help='Input meta-configuration file name')
    parser.add_argument(
        'output-file-or-dir',
        nargs='?',
        help='Output file or directory name')
    parser.add_argument(
        '-n', '--netns-per-node',
        action="store_true",
        help='Use network namespace per node')
    parser.add_argument(
        '-g', '--graphics-file',
        help='Output file name for graphical representation')
    args = parser.parse_args()
    return args

def fatal_error(error_msg):
    print(error_msg, file=sys.stderr)
    sys.exit(1)

def main():
    # pylint:disable=global-statement
    global ARGS
    global META_CONFIG
    ARGS = parse_command_line_arguments()
    input_file_name = getattr(ARGS, 'input-meta-config-file')
    META_CONFIG = parse_meta_configuration(input_file_name)
    validate_meta_configuration()
    fabric = Fabric()
    if ARGS.netns_per_node:
        fabric.write_netns_configs_and_scripts()
    else:
        fabric.write_config()
    if ARGS.graphics_file is not None:
        fabric.write_graphics()

if __name__ == "__main__":
    main()
