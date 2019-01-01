#!/usr/bin/env python3

import argparse
import os
import pprint
import stat

import sys
import cerberus
import yaml

NEXT_NODE_ID = 1
NEXT_INTERFACE_ID = 1
NODES = {}
INTERFACES = {}

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

class Node:

    def __init__(self, name, node_id, level):
        self.name = name
        self.node_id = node_id
        self.level = level
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

    def create_interface(self, intf_id, peer_intf_id):
        # pylint:disable=global-statement
        global INTERFACES
        intf_index = len(self.interfaces) + 1
        interface = Interface(intf_id, intf_index, self.node_id, peer_intf_id)
        self.interfaces.append(interface)
        INTERFACES[intf_id] = interface

class Interface:

    def __init__(self, intf_id, intf_index, node_id, peer_intf_id):
        self.intf_id = intf_id          # Globally unique identifier for interface
        self.intf_index = intf_index    # Index for interface, locally unique within scope of node
        self.node_id = node_id
        self.peer_intf_id = peer_intf_id
        self.rx_lie_port = 20000 + intf_id
        self.tx_lie_port = 20000 + peer_intf_id
        self.rx_tie_port = 10000 + intf_id
        lower = min(intf_id, peer_intf_id)
        upper = max(intf_id, peer_intf_id)
        self.addr = "99.{}.{}.{}/24".format(lower, upper, intf_id)

    def name(self):
        return "if" + str(self.intf_index)

    def fq_name(self):
        return NODES[self.node_id].name + ":" + self.name()

    def veth_name(self):
        return "veth" + "-" + str(self.intf_id) + "-" + str(self.peer_intf_id)

def create_node(name, level):
    # pylint:disable=global-statement
    global NEXT_NODE_ID
    global NODES
    node = Node(name, NEXT_NODE_ID, level)
    NEXT_NODE_ID += 1
    NODES[node.node_id] = node
    return node

def create_link_between_nodes(node1, node2):
    # pylint:disable=global-statement
    global NEXT_INTERFACE_ID
    global INTERFACES
    intf_1_id = NEXT_INTERFACE_ID
    NEXT_INTERFACE_ID += 1
    intf_2_id = NEXT_INTERFACE_ID
    NEXT_INTERFACE_ID += 1
    node1.create_interface(intf_1_id, intf_2_id)
    node2.create_interface(intf_2_id, intf_1_id)

def write_configuration(args):
    if args.netns_per_node:
        write_netns_config(args)
    else:
        write_ports_config(args)

def write_ports_config(args):
    file_name = getattr(args, 'output-file-or-dir')
    if file_name is None:
        write_ports_config_to_file(sys.stdout)
    else:
        try:
            with open(file_name, 'w') as file:
                write_ports_config_to_file(file)
        except IOError:
            fatal_error('Could not open output configuration file "{}"'.format(file_name))

def write_ports_config_to_file(file):
    # pylint:disable=global-statement
    global NODES
    global INTERFACES
    print("shards:", file=file)
    print("  - id: 0", file=file)
    print("    nodes:", file=file)
    for node in NODES.values():
        write_node_config_to_file(node, file, netns=False)

def write_netns_config(args):
    # pylint:disable=global-statement
    global NODES
    dir_name = getattr(args, 'output-file-or-dir')
    if dir_name is None:
        fatal_error("Output directory name is missing (mandatory for --netns)")
    try:
        os.mkdir(dir_name)
    except FileExistsError:
        fatal_error("Output directory '{}' already exists".format(dir_name))
    except IOError:
        fatal_error("Could not create output directory '{}'".format(dir_name))
    for node in NODES.values():
        write_netns_node_config(args, node)
    write_netns_start(args)
    write_netns_connect(args)

def write_netns_node_config(args, node):
    dir_name = getattr(args, 'output-file-or-dir')
    file_name = dir_name + '/' + node.name + ".yaml"
    node.config_file_name = os.path.realpath(file_name)
    try:
        with open(file_name, 'w') as file:
            write_netns_node_config_to_file(node, file)
    except IOError:
        fatal_error('Could not open output node configuration file "{}"'.format(file_name))

def write_netns_node_config_to_file(node, file):
    print("shards:", file=file)
    print("  - id: 0", file=file)
    print("    nodes:", file=file)
    write_node_config_to_file(node, file, netns=True)

def write_netns_start(args):
    dir_name = getattr(args, 'output-file-or-dir')
    file_name = dir_name + "/start.sh"
    try:
        with open(file_name, 'w') as file:
            write_netns_start_to_file(file)
    except IOError:
        fatal_error('Could not open start script file "{}"'.format(file_name))
    try:
        existing_stat = os.stat(file_name)
        os.chmod(file_name, existing_stat.st_mode | stat.S_IXUSR)
    except IOError:
        fatal_error('Could name make "{}" executable'.format(file_name))

def write_progress_msg(file, step, total_steps, message):
    percent = step * 100 // total_steps
    percent_str = "[{:03d}]".format(percent)
    print('echo "{} {}"'.format(percent_str, message), file=file)

def write_netns_start_to_file(file):
    # pylint:disable=global-statement
    global NODES
    global INTERFACES
    already_created = []
    total_steps = len(INTERFACES) + len(NODES)
    step = 0
    for intf in INTERFACES.values():
        peer_intf = INTERFACES[intf.peer_intf_id]
        intf_veth = intf.veth_name()
        peer_veth = peer_intf.veth_name()
        step += 1
        if intf_veth not in already_created:
            write_progress_msg(file, step, total_steps,
                               "Create veth pair {} - {}".format(intf_veth, peer_veth))
            print("ip link add dev {} type veth peer name {}".format(intf_veth, peer_veth),
                  file=file)
            already_created.append(peer_veth)
    for node in NODES.values():
        ns_name = "netns-" + str(node.node_id)
        step += 1
        write_progress_msg(file, step, total_steps, "Create netns {}".format(ns_name))
        print("ip netns add {}".format(ns_name), file=file)
        addr = node.lo_addr
        print("ip netns exec {} ip link set dev lo up".format(ns_name), file=file)
        print("ip netns exec {} ip addr add {} dev lo".format(ns_name, addr), file=file)
        for intf in node.interfaces:
            veth = intf.veth_name()
            addr = intf.addr
            print("ip link set {} netns {}".format(veth, ns_name), file=file)
            print("ip netns exec {} ip link set dev {} up".format(ns_name, veth), file=file)
            print("ip netns exec {} ip addr add {} dev {}".format(ns_name, addr, veth), file=file)
    for node in NODES.values():
        ns_name = "netns-" + str(node.node_id)
        port_file = "/tmp/rift-python-telnet-port-" + node.name
        print("ip netns exec {} python3 rift --multicast-loopback-disable "
              "--telnet-port-file {} {} < /dev/null &"
              .format(ns_name, port_file, node.config_file_name), file=file)

def write_netns_connect(args):
    # pylint:disable=global-statement
    global NODES
    dir_name = getattr(args, 'output-file-or-dir')
    for node in NODES.values():
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

def write_node_config_to_file(node, file, netns):
    print("      - name: " + node.name, file=file)
    print("        level: " + str(node.level), file=file)
    print("        systemid: " + str(node.node_id), file=file)
    if not netns:
        print("        rx_lie_mcast_address: " + node.rx_lie_mcast_addr, file=file)
    print("        interfaces:", file=file)
    for interface in node.interfaces:
        remote_interface = INTERFACES[interface.peer_intf_id]
        description = "{} -> {}".format(interface.fq_name(), remote_interface.fq_name())
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
    args = parser.parse_args()
    return args

def generate_configuration(meta_config):
    # Currently, Clos is the only supported topology
    generate_clos_configuration(meta_config)

def generate_clos_configuration(meta_config):
    leaf_nodes = generate_clos_leafs(meta_config)
    spine_nodes = generate_clos_spines(meta_config)
    generate_clos_leaf_spine_links(leaf_nodes, spine_nodes)

def generate_clos_leafs(meta_config):
    nr_leaf_nodes = meta_config['nr-leaf-nodes']
    if 'leafs' in meta_config:
        nr_ipv4_loopbacks = meta_config['leafs']['nr-ipv4-loopbacks']
    else:
        nr_ipv4_loopbacks = DEFAULT_NR_IPV4_LOOPBACKS
    leaf_nodes = []
    for index in range(1, nr_leaf_nodes+1):
        name = "leaf" + str(index)
        leaf_node = create_node(name, level=0)
        leaf_node.add_ipv4_loopbacks(nr_ipv4_loopbacks)
        leaf_nodes.append(leaf_node)
    return leaf_nodes

def generate_clos_spines(meta_config):
    nr_spine_nodes = meta_config['nr-spine-nodes']
    if 'spines' in meta_config:
        nr_ipv4_loopbacks = meta_config['spines']['nr-ipv4-loopbacks']
    else:
        nr_ipv4_loopbacks = DEFAULT_NR_IPV4_LOOPBACKS
    spine_nodes = []
    for index in range(1, nr_spine_nodes+1):
        name = "spine" + str(index)
        spine_node = create_node(name, level=1)
        spine_node.add_ipv4_loopbacks(nr_ipv4_loopbacks)
        spine_nodes.append(spine_node)
    return spine_nodes

def generate_clos_leaf_spine_links(leaf_nodes, spine_nodes):
    # Connect leaf nodes to spine nodes
    for leaf_node in leaf_nodes:
        for spine_node in spine_nodes:
            create_link_between_nodes(leaf_node, spine_node)

def fatal_error(error_msg):
    print(error_msg, file=sys.stderr)
    sys.exit(1)

def main():
    args = parse_command_line_arguments()
    input_file_name = getattr(args, 'input-meta-config-file')
    meta_config = parse_meta_configuration(input_file_name)
    generate_configuration(meta_config)
    write_configuration(args)

if __name__ == "__main__":
    main()
