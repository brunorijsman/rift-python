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

    def add_interface(self, interface):
        self.interfaces.append(interface)

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

    def veth_name(self):
        return "veth" + "-" + str(self.intf_id) + "-" + str(self.peer_intf_id)

class Generator:

    def __init__(self, args, meta_config):
        self.args = args
        self.meta_config = meta_config
        self.next_node_id = 1
        self.next_interface_id = 1
        self.nodes = {}
        self.interfaces = {}

    def create_node(self, name, level):
        node = Node(name, self.next_node_id, level)
        self.next_node_id += 1
        self.nodes[node.node_id] = node
        return node

    def create_interface(self, node, intf_id, peer_intf_id):
        intf_index = len(self.interfaces) + 1
        interface = Interface(intf_id, intf_index, node.node_id, peer_intf_id)
        node.add_interface(interface)
        self.interfaces[intf_id] = interface

    def fq_intf_name(self, intf):
        return self.nodes[intf.node_id].name + ":" + intf.name()

    def create_link_between_nodes(self, node1, node2):
        intf_1_id = self.next_interface_id
        self.next_interface_id += 1
        intf_2_id = self.next_interface_id
        self.next_interface_id += 1
        self.create_interface(node1, intf_1_id, intf_2_id)
        self.create_interface(node2, intf_2_id, intf_1_id)

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
        for index in range(1, nr_leaf_nodes+1):
            name = "leaf" + str(index)
            leaf_node = self.create_node(name, level=0)
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
        for index in range(1, nr_spine_nodes+1):
            name = "spine" + str(index)
            spine_node = self.create_node(name, level=1)
            spine_node.add_ipv4_loopbacks(nr_ipv4_loopbacks)
            spine_nodes.append(spine_node)
        return spine_nodes

    def generate_clos_leaf_spine_links(self, leaf_nodes, spine_nodes):
        # Connect leaf nodes to spine nodes
        for leaf_node in leaf_nodes:
            for spine_node in spine_nodes:
                self.create_link_between_nodes(leaf_node, spine_node)

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

def fatal_error(error_msg):
    print(error_msg, file=sys.stderr)
    sys.exit(1)

def main():
    args = parse_command_line_arguments()
    input_file_name = getattr(args, 'input-meta-config-file')
    meta_config = parse_meta_configuration(input_file_name)
    generator = Generator(args, meta_config)
    generator.generate_configuration()
    generator.write_configuration()

if __name__ == "__main__":
    main()
