#!/usr/bin/env python3

import argparse
import os
import pprint
import stat

import sys
import cerberus
import yaml

DEFAULT_NR_IPV4_LOOPBACKS = 1

NODE_SCHEMA = {
    'type': 'dict',
    'schema': {
        'nr-ipv4-loopbacks': {'type': 'integer', 'min': 0, 'default': DEFAULT_NR_IPV4_LOOPBACKS}
    }
}

SCHEMA = {
    'nr-leaf-nodes': {'required': True, 'type': 'integer', 'min': 0},
    'nr-spine-nodes': {'required': True, 'type': 'integer', 'min': 0},
    'leafs': NODE_SCHEMA,
    'spines': NODE_SCHEMA
}

SOUTH = 1
NORTH = 2

NODE_X_SIZE = 100
NODE_Y_SIZE = 50
NODE_X_INTERVAL = 20
NODE_Y_INTERVAL = 100
NODE_LINE_COLOR = "black"
NODE_FILL_COLOR = "lightgray"
LINK_COLOR = "black"
INTF_RADIUS = 3
INTF_COLOR = "black"

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

class Node:

    def __init__(self, name, node_id, level, index_in_level):
        self.name = name
        self.node_id = node_id
        self.level = level
        self.index_in_level = index_in_level
        self.rx_lie_mcast_addr = generate_ipv4_address_str(224, 0, 1, 0, node_id)
        self.interfaces = []
        self.ipv4_prefixes = []
        self.lo_addr = generate_ipv4_address_str(88, 0, 0, 0, 1) + "/32"

    def add_ipv4_loopbacks(self, count):
        for index in range(1, count+1):
            offset = self.node_id * 256 + index
            address = generate_ipv4_address_str(88, 0, 0, 0, offset)
            mask = "32"
            metric = "1"
            prefix = (address, mask, metric)
            self.ipv4_prefixes.append(prefix)

    def add_interface(self, interface):
        self.interfaces.append(interface)

class Interface:

    def __init__(self, node, intf_id, intf_index, peer_node, peer_intf_id):
        self.node = node
        self.intf_id = intf_id          # Globally unique identifier for interface
        self.intf_index = intf_index    # Index for interface, locally unique within scope of node
        self.peer_node = peer_node
        if peer_node.level < node.level:
            self.direction = SOUTH
        else:
            self.direction = NORTH
        self.peer_intf_id = peer_intf_id
        self.rx_lie_port = 20000 + intf_id
        self.tx_lie_port = 20000 + peer_intf_id
        self.rx_tie_port = 10000 + intf_id
        lower = min(intf_id, peer_intf_id)
        upper = max(intf_id, peer_intf_id)
        self.addr = "99.{}.{}.{}/24".format(lower, upper, intf_id)

    def name(self):
        return "if" + str(self.intf_index)

    def veth_name(self):
        return "veth" + "-" + str(self.intf_id) + "-" + str(self.peer_intf_id)

class Link:

    def __init__(self, intf1, intf2):
        self.intf1 = intf1
        self.intf2 = intf2

class Generator:

    def __init__(self, args, meta_config):
        self.args = args
        self.meta_config = meta_config
        self.next_node_id = 1
        self.next_interface_id = 1
        self.nodes = {}
        self.interfaces = {}
        self.links = []

    def produce_configuration(self):
        self.generate_configuration()
        self.write_configuration()
        if self.args.graphics_file is not None:
            self.write_graphics()

    def generate_configuration(self):
        # Currently, Clos is the only supported topology
        self.generate_clos_configuration()

    def generate_clos_configuration(self):
        leaf_nodes = self.generate_clos_leafs()
        spine_nodes = self.generate_clos_spines()
        self.generate_clos_leaf_spine_links(leaf_nodes, spine_nodes)

    def generate_clos_leafs(self):
        nr_leaf_nodes = self.meta_config['nr-leaf-nodes']
        if 'leafs' in self.meta_config:
            nr_ipv4_loopbacks = self.meta_config['leafs']['nr-ipv4-loopbacks']
        else:
            nr_ipv4_loopbacks = DEFAULT_NR_IPV4_LOOPBACKS
        leaf_nodes = []
        for index in range(0, nr_leaf_nodes):
            name = "leaf" + str(index+1)
            leaf_node = self.create_node(name, level=0, index_in_level=index)
            leaf_node.add_ipv4_loopbacks(nr_ipv4_loopbacks)
            leaf_nodes.append(leaf_node)
        return leaf_nodes

    def generate_clos_spines(self):
        nr_spine_nodes = self.meta_config['nr-spine-nodes']
        if 'spines' in self.meta_config:
            nr_ipv4_loopbacks = self.meta_config['spines']['nr-ipv4-loopbacks']
        else:
            nr_ipv4_loopbacks = DEFAULT_NR_IPV4_LOOPBACKS
        spine_nodes = []
        for index in range(0, nr_spine_nodes):
            name = "spine" + str(index+1)
            spine_node = self.create_node(name, level=1, index_in_level=index)
            spine_node.add_ipv4_loopbacks(nr_ipv4_loopbacks)
            spine_nodes.append(spine_node)
        return spine_nodes

    def generate_clos_leaf_spine_links(self, leaf_nodes, spine_nodes):
        # Connect leaf nodes to spine nodes
        for leaf_node in leaf_nodes:
            for spine_node in spine_nodes:
                self.create_link_between_nodes(leaf_node, spine_node)

    def create_node(self, name, level, index_in_level):
        node = Node(name, self.next_node_id, level, index_in_level)
        self.next_node_id += 1
        self.nodes[node.node_id] = node
        return node

    def create_interface(self, node, intf_id, peer_node, peer_intf_id):
        intf_index = len(node.interfaces) + 1
        interface = Interface(node, intf_id, intf_index, peer_node, peer_intf_id)
        node.add_interface(interface)
        self.interfaces[intf_id] = interface
        return interface

    def fq_intf_name(self, intf):
        return self.nodes[intf.node.node_id].name + ":" + intf.name()

    def create_link_between_nodes(self, node1, node2):
        intf1_id = self.next_interface_id
        self.next_interface_id += 1
        intf2_id = self.next_interface_id
        self.next_interface_id += 1
        intf1 = self.create_interface(node1, intf1_id, node2, intf2_id)
        intf2 = self.create_interface(node2, intf2_id, node1, intf1_id)
        link = Link(intf1, intf2)
        self.links.append(link)

    def write_configuration(self):
        if self.args.netns_per_node:
            self.write_netns_config()
        else:
            self.write_ports_config()

    def write_ports_config(self):
        file_name = getattr(self.args, 'output-file-or-dir')
        if file_name is None:
            self.write_ports_config_to_file(sys.stdout)
        else:
            try:
                with open(file_name, 'w') as file:
                    self.write_ports_config_to_file(file)
            except IOError:
                fatal_error('Could not open output configuration file "{}"'.format(file_name))

    def write_ports_config_to_file(self, file):
        print("shards:", file=file)
        print("  - id: 0", file=file)
        print("    nodes:", file=file)
        for node in self.nodes.values():
            self.write_node_config_to_file(node, file, netns=False)

    def write_netns_config(self):
        dir_name = getattr(self.args, 'output-file-or-dir')
        if dir_name is None:
            fatal_error("Output directory name is missing (mandatory for --netns)")
        try:
            os.mkdir(dir_name)
        except FileExistsError:
            fatal_error("Output directory '{}' already exists".format(dir_name))
        except IOError:
            fatal_error("Could not create output directory '{}'".format(dir_name))
        for node in self.nodes.values():
            self.write_netns_node_config(node)
        self.write_netns_start()
        self.write_netns_connect()

    def write_netns_node_config(self, node):
        dir_name = getattr(self.args, 'output-file-or-dir')
        file_name = dir_name + '/' + node.name + ".yaml"
        node.config_file_name = os.path.realpath(file_name)
        try:
            with open(file_name, 'w') as file:
                self.write_netns_node_config_to_file(node, file)
        except IOError:
            fatal_error('Could not open output node configuration file "{}"'.format(file_name))

    def write_netns_node_config_to_file(self, node, file):
        print("shards:", file=file)
        print("  - id: 0", file=file)
        print("    nodes:", file=file)
        self.write_node_config_to_file(node, file, netns=True)

    def write_netns_start(self):
        dir_name = getattr(self.args, 'output-file-or-dir')
        file_name = dir_name + "/start.sh"
        try:
            with open(file_name, 'w') as file:
                self.write_netns_start_to_file(file)
        except IOError:
            fatal_error('Could not open start script file "{}"'.format(file_name))
        try:
            existing_stat = os.stat(file_name)
            os.chmod(file_name, existing_stat.st_mode | stat.S_IXUSR)
        except IOError:
            fatal_error('Could name make "{}" executable'.format(file_name))

    def write_progress_msg(self, file, step, total_steps, message):
        percent = step * 100 // total_steps
        percent_str = "[{:03d}]".format(percent)
        print('echo "{} {}"'.format(percent_str, message), file=file)

    def write_netns_start_to_file(self, file):
        already_created = []
        total_steps = len(self.interfaces) + len(self.nodes)
        step = 0
        for intf in self.interfaces.values():
            peer_intf = self.interfaces[intf.peer_intf_id]
            intf_veth = intf.veth_name()
            peer_veth = peer_intf.veth_name()
            step += 1
            if intf_veth not in already_created:
                self.write_progress_msg(file, step, total_steps,
                                        "Create veth pair {} - {}".format(intf_veth, peer_veth))
                print("ip link add dev {} type veth peer name {}".format(intf_veth, peer_veth),
                      file=file)
                already_created.append(peer_veth)
        for node in self.nodes.values():
            ns_name = "netns-" + str(node.node_id)
            step += 1
            self.write_progress_msg(file, step, total_steps, "Create netns {} and start RIFT"
                                    .format(ns_name))
            print("ip netns add {}".format(ns_name), file=file)
            addr = node.lo_addr
            print("ip netns exec {} ip link set dev lo up".format(ns_name), file=file)
            print("ip netns exec {} ip addr add {} dev lo".format(ns_name, addr), file=file)
            for intf in node.interfaces:
                veth = intf.veth_name()
                addr = intf.addr
                print("ip link set {} netns {}".format(veth, ns_name), file=file)
                print("ip netns exec {} ip link set dev {} up".format(ns_name, veth), file=file)
                print("ip netns exec {} ip addr add {} dev {}".format(ns_name, addr, veth),
                      file=file)
        for node in self.nodes.values():
            ns_name = "netns-" + str(node.node_id)
            port_file = "/tmp/rift-python-telnet-port-" + node.name
            print("ip netns exec {} python3 rift --multicast-loopback-disable "
                  "--telnet-port-file {} {} < /dev/null &"
                  .format(ns_name, port_file, node.config_file_name), file=file)

    def write_netns_connect(self):
        dir_name = getattr(self.args, 'output-file-or-dir')
        for node in self.nodes.values():
            file_name = "{}/connect-{}.sh".format(dir_name, node.name)
            try:
                with open(file_name, 'w') as file:
                    ns_name = "netns-" + str(node.node_id)
                    port_file = "/tmp/rift-python-telnet-port-" + node.name
                    print("ip netns exec {} telnet localhost $(cat {})".format(ns_name, port_file),
                          file=file)
            except IOError:
                fatal_error('Could not open start script file "{}"'.format(file_name))
            try:
                existing_stat = os.stat(file_name)
                os.chmod(file_name, existing_stat.st_mode | stat.S_IXUSR)
            except IOError:
                fatal_error('Could name make "{}" executable'.format(file_name))

    def write_node_config_to_file(self, node, file, netns):
        print("      - name: " + node.name, file=file)
        print("        level: " + str(node.level), file=file)
        print("        systemid: " + str(node.node_id), file=file)
        if not netns:
            print("        rx_lie_mcast_address: " + node.rx_lie_mcast_addr, file=file)
        print("        interfaces:", file=file)
        for interface in node.interfaces:
            remote_interface = self.interfaces[interface.peer_intf_id]
            description = "{} -> {}".format(self.fq_intf_name(interface),
                                            self.fq_intf_name(remote_interface))
            if netns:
                print("          - name: " + interface.veth_name(), file=file)
            else:
                print("          - name: " + interface.name(), file=file)
            print("            # " + description, file=file)
            print("            rx_lie_port: " + str(interface.rx_lie_port), file=file)
            print("            tx_lie_port: " + str(interface.tx_lie_port), file=file)
            print("            rx_tie_port: " + str(interface.rx_tie_port), file=file)
        print("        v4prefixes:", file=file)
        for prefix in node.ipv4_prefixes:
            (address, mask, metric) = prefix
            print("          - address: " + address, file=file)
            print("            mask: " + mask, file=file)
            print("            metric: " + metric, file=file)

    def write_graphics(self):
        file_name = self.args.graphics_file
        assert file_name is not None
        try:
            with open(file_name, 'w') as file:
                self.write_graphics_to_file(file)
        except IOError:
            fatal_error('Could not open start graphics file "{}"'.format(file_name))

    def write_graphics_to_file(self, file):
        self.svg_start(file)
        for node in self.nodes.values():
            self.svg_node(file, node)
        for link in self.links:
            self.svg_link(file, link)
        self.svg_end(file)

    def svg_start(self, file):
        file.write('<svg '
                   'xmlns="http://www.w3.org/2000/svg '
                   'xmlns:xlink="http://www.w3.org/1999/xlink" '
                   'width=1000000 '
                   'height=1000000 '
                   'id="tooltip-svg">\n')

    def svg_end(self, file):
        file.write('</svg>\n')

    def svg_node_x(self, node):
        return node.index_in_level * (NODE_X_SIZE + NODE_X_INTERVAL)

    def svg_node_y(self, node):
        nr_levels = 2
        return (nr_levels - node.level - 1) * (NODE_Y_SIZE + NODE_Y_INTERVAL)

    def svg_intf_x(self, intf):
        node_intf_dir_count = 0    # Number of interfaces on node in same direction
        for check_intf in intf.node.interfaces:
            if check_intf.direction == intf.direction:
                node_intf_dir_count += 1
                if check_intf == intf:
                    intf_dir_index = node_intf_dir_count
        intf_x_dist = NODE_X_SIZE / (node_intf_dir_count + 1)
        return self.svg_node_x(intf.node) + intf_x_dist * intf_dir_index

    def svg_intf_y(self, intf):
        if intf.direction == NORTH:
            return self.svg_node_y(intf.node)
        else:
            return self.svg_node_y(intf.node) + NODE_Y_SIZE

    def svg_node(self, file, node):
        xpos = self.svg_node_x(node)
        ypos = self.svg_node_y(node)
        file.write('<g>\n')
        file.write('<rect '
                   'x="{}" '
                   'y="{}" '
                   'width="{}" '
                   'height="{}" '
                   'fill="{}" '
                   'style="stroke:{};" '
                   '></rect>'
                   .format(xpos, ypos, NODE_X_SIZE, NODE_Y_SIZE, NODE_FILL_COLOR, NODE_LINE_COLOR))
        ypos += NODE_Y_SIZE // 2
        xpos += NODE_X_SIZE // 10
        file.write('<text '
                   'x="{}" '
                   'y="{}" '
                   'style="font-family:monospace; dominant-baseline:central; stroke:{}">'
                   '{}'
                   '</text>\n'
                   .format(xpos, ypos, NODE_LINE_COLOR, node.name))
        file.write('</g>\n')

    def svg_link(self, file, link):
        xpos1 = self.svg_intf_x(link.intf1)
        ypos1 = self.svg_intf_y(link.intf1)
        xpos2 = self.svg_intf_x(link.intf2)
        ypos2 = self.svg_intf_y(link.intf2)
        file.write('<line '
                   'x1="{}" '
                   'y1="{}" '
                   'x2="{}" '
                   'y2="{}" '
                   'style="stroke:{};">'
                   '</line>\n'
                   .format(xpos1, ypos1, xpos2, ypos2, LINK_COLOR))
        self.svg_intf(file, link.intf1)
        self.svg_intf(file, link.intf2)

    def svg_intf(self, file, intf):
        xpos = self.svg_intf_x(intf)
        ypos = self.svg_intf_y(intf)
        file.write('<circle '
                   'cx="{}" '
                   'cy="{}" '
                   'r="{}" '
                   'style="stroke:{};fill:{}">'
                   '</circle>\n'
                   .format(xpos, ypos, INTF_RADIUS, INTF_COLOR, INTF_COLOR))

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

    return config

def parse_command_line_arguments():
    parser = argparse.ArgumentParser(description='RIFT configuration generator')
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
    args = parse_command_line_arguments()
    input_file_name = getattr(args, 'input-meta-config-file')
    meta_config = parse_meta_configuration(input_file_name)
    generator = Generator(args, meta_config)
    generator.produce_configuration()

if __name__ == "__main__":
    main()
