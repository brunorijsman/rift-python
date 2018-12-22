#!/usr/bin/env python3

import argparse
import pprint

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
        self.rx_lie_mcast_address = generate_ipv4_address_str(224, 0, 1, 0, node_id)
        self.interfaces = []
        self.ipv4_prefixes = []

    def add_ipv4_loopbacks(self, count):
        for index in range(1, count+1):
            offset = self.node_id * 256 + index
            address = generate_ipv4_address_str(1, 0, 0, 0, offset)
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

    def name(self):
        return "if" + str(self.intf_index)

    def fq_name(self):
        return NODES[self.node_id].name + ":" + self.name()

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

def write_configuration():
    # pylint:disable=global-statement
    global NODES
    global INTERFACES
    print("shards:")
    print("  - id: 0")
    print("    nodes:")
    for node in NODES.values():
        print("      - name: " + node.name)
        print("        level: " + str(node.level))
        print("        systemid: " + str(node.node_id))
        print("        rx_lie_mcast_address: " + node.rx_lie_mcast_address)
        print("        interfaces:")
        for interface in node.interfaces:
            remote_interface = INTERFACES[interface.peer_intf_id]
            description = "{} -> {}".format(interface.fq_name(), remote_interface.fq_name())
            print("          - name: " + interface.name())
            print("            # " + description)
            print("            rx_lie_port: " + str(interface.rx_lie_port))
            print("            tx_lie_port: " + str(interface.tx_lie_port))
            print("            rx_tie_port: " + str(interface.rx_tie_port))
        print("        v4prefixes:")
        for prefix in node.ipv4_prefixes:
            (address, mask, metric) = prefix
            print("          - address: " + address)
            print("            mask: " + mask)
            print("            metric: " + metric)

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

def parse_meta_configuration(filename):
    with open(filename, 'r') as stream:
        try:
            config = yaml.load(stream)
        except yaml.YAMLError as exception:
            raise exception
    validator = cerberus.Validator()
    if not validator.validate(config, SCHEMA):
        pretty_printer = pprint.PrettyPrinter()
        pretty_printer.pprint(validator.errors)
        exit(1)

    return config

def parse_command_line_arguments():
    parser = argparse.ArgumentParser(description='RIFT configuration generator')
    parser.add_argument('configfile', help='Meta-configuration filename')
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
    # Write the resulting generated configuration (topology) file
    write_configuration()

def main():
    args = parse_command_line_arguments()
    meta_config = parse_meta_configuration(args.configfile)
    generate_configuration(meta_config)

if __name__ == "__main__":
    main()
