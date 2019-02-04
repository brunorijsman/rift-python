import logging
import random
import os
import sys

import sortedcontainers

import cli_listen_handler
import cli_session_handler
import interface
import netifaces
import node
import scheduler
import table

# TODO: Make sure that there is always at least one node (and hence always a current node)

class Engine:

    def __init__(self, passive_nodes, run_which_nodes, interactive, telnet_port_file,
                 ipv4_multicast_loopback, ipv6_multicast_loopback, log_level, config):
        log_file_name = "rift.log"  # TODO: Make this configurable
        if "RIFT_TEST_RESULTS_DIR" in os.environ:
            log_file_name = os.environ["RIFT_TEST_RESULTS_DIR"] + "/" + log_file_name
        logging.basicConfig(
            filename=log_file_name,
            format='%(asctime)s:%(levelname)s:%(name)s:%(message)s',
            level=log_level)
        self._run_which_nodes = run_which_nodes
        self._interactive = interactive
        self._telnet_port_file = telnet_port_file
        self.ipv4_multicast_loopback = ipv4_multicast_loopback
        self.ipv6_multicast_loopback = ipv6_multicast_loopback
        self._config = config
        if self.nr_nodes() > 1:
            self._stand_alone = False
            self.simulated_interfaces = True
            self.physical_interface_name = self.default_physical_interface()
        else:
            self._stand_alone = True
            self.simulated_interfaces = False
            self.physical_interface_name = None
        self.tx_src_address = self.read_global_configuration(config, 'tx_src_address', '')
        self.floodred_enabled = self.read_global_configuration(config, 'flooding_reduction', True)
        self.floodred_system_random = random.randint(0, 0xffffffffffffffff)
        self._nodes = sortedcontainers.SortedDict()
        self.create_configuration(passive_nodes)
        cli_log = logging.getLogger('cli')
        if self._nodes:
            first_node = self._nodes.peekitem(0)[1]
        else:
            first_node = None
        if self._interactive:
            self._cli_listen_handler = None
            self._interactive_cli_session_handler = cli_session_handler.CliSessionHandler(
                sock=None,
                rx_fd=sys.stdin.fileno(),
                tx_fd=sys.stdout.fileno(),
                parse_tree=self.parse_tree,
                command_handler=self,
                log=cli_log,
                node=first_node)
        else:
            self._cli_listen_handler = cli_listen_handler.CliListenHandler(
                command_tree=self.parse_tree,
                command_handler=self,
                log=cli_log,
                default_node=first_node)
            self._interactive_cli_session_handler = None
            if self._telnet_port_file is None:
                print("Command Line Interface (CLI) available on port {}"
                      .format(self._cli_listen_handler.port))
            else:
                try:
                    with open(self._telnet_port_file, 'w') as file:
                        print(self._cli_listen_handler.port, file=file)
                except IOError:
                    pass # TODO: Log an error

    def default_physical_interface(self):
        # When simulated interfaces are disabled, the interface names on nodes correspond to real
        # interfaces on the host platform.
        # When simulated interface are enabled, the interface names on nodes are "fake" i.e. they do
        # not correspond to real interfaces on the host platform. All these simulated interfaces
        # actually run on a single real interface, referred to as the physical interface. Traffic to
        # and from different simulated interfaces are distinguished by using different multicast
        # addresses and port numbers for each simulated interface.
        # Pick the first interface with a broadcast IPv4 address (if any) as the default.
        for intf_name in netifaces.interfaces():
            addresses = netifaces.ifaddresses(intf_name)
            if netifaces.AF_INET in addresses:
                ipv4_addresses = addresses[netifaces.AF_INET]
                for ipv4_address in ipv4_addresses:
                    if 'broadcast' in ipv4_address:
                        return intf_name
        print("Cannot pick default physical interface: no broadcast interface found")
        sys.exit(1)

    def nr_nodes(self):
        total_nr_nodes = 0
        if 'shards' in self._config:
            for shard_config in self._config['shards']:
                if 'nodes' in shard_config:
                    for _node_config in shard_config['nodes']:
                        total_nr_nodes += 1
        return total_nr_nodes

    def read_global_configuration(self, config, attribute, default):
        if ('const' in config) and (config['const'] is not None) and (attribute in config['const']):
            return config['const'][attribute]
        else:
            return default

    def create_configuration(self, passive_nodes):
        if 'shards' in self._config:
            for shard_config in self._config['shards']:
                self.create_shard(shard_config, passive_nodes)

    def create_shard(self, shard_config, passive_nodes):
        if 'nodes' in shard_config:
            for node_config in shard_config['nodes']:
                if 'name' in node_config:
                    force_passive = node_config['name'] in passive_nodes
                else:
                    force_passive = False
                self.create_node(node_config, force_passive)

    def create_node(self, node_config, force_passive):
        new_node = node.Node(node_config, self, force_passive, self._stand_alone)
        self._nodes[new_node.name] = new_node

    def run(self):
        scheduler.SCHEDULER.run()

    def command_show_engine(self, cli_session):
        tab = table.Table(separators=False)
        tab.add_row(["Stand-alone", self._stand_alone])
        tab.add_row(["Interactive", self._interactive])
        tab.add_row(["Simulated Interfaces", self.simulated_interfaces])
        tab.add_row(["Physical Interface", self.physical_interface_name])
        tab.add_row(["Telnet Port File", self._telnet_port_file])
        tab.add_row(["IPv4 Multicast Loopback", self.ipv4_multicast_loopback])
        tab.add_row(["IPv6 Multicast Loopback", self.ipv6_multicast_loopback])
        tab.add_row(["Number of Nodes", self.nr_nodes()])
        tab.add_row(["Transmit Source Address", self.tx_src_address])
        tab.add_row(["Flooding Reduction", self.floodred_enabled])
        tab.add_row(["Flooding Reduction System Random", self.floodred_system_random])
        cli_session.print(tab.to_string())

    def command_show_flooding_reduction(self, cli_session):
        cli_session.current_node.command_show_flooding_reduction(cli_session)

    def command_show_intf_fsm_nvhis(self, cli_session, parameters):
        cli_session.current_node.command_show_intf_fsm_hist(cli_session, parameters, False)

    def command_show_intf_fsm_vhis(self, cli_session, parameters):
        cli_session.current_node.command_show_intf_fsm_hist(cli_session, parameters, True)

    def command_show_intf_queues(self, cli_session, parameters):
        cli_session.current_node.command_show_intf_queues(cli_session, parameters)

    def command_show_intf_sockets(self, cli_session, parameters):
        cli_session.current_node.command_show_intf_sockets(cli_session, parameters)

    def command_show_interface(self, cli_session, parameters):
        cli_session.current_node.command_show_interface(cli_session, parameters)

    def command_set_interface_failure(self, cli_session, parameters):
        cli_session.current_node.command_set_interface_failure(cli_session, parameters)

    def command_show_interfaces(self, cli_session):
        cli_session.current_node.command_show_interfaces(cli_session)

    def command_show_kernel_addresses(self, cli_session):
        cli_session.current_node.command_show_kernel_addresses(cli_session)

    def command_show_kernel_links(self, cli_session):
        cli_session.current_node.command_show_kernel_links(cli_session)

    def command_show_kernel_routes(self, cli_session):
        cli_session.current_node.command_show_kernel_routes(cli_session)

    def command_show_kernel_routes_tab(self, cli_session, parameters):
        cli_session.current_node.command_show_kernel_routes_tab(cli_session, parameters)

    def command_show_kernel_route_pref(self, cli_session, parameters):
        cli_session.current_node.command_show_kernel_route_pref(cli_session, parameters)

    def command_show_lie_fsm(self, cli_session):
        interface.Interface.fsm_definition.command_show_fsm(cli_session)

    def command_show_node(self, cli_session):
        cli_session.current_node.command_show_node(cli_session)

    def command_show_node_fsm_nvhis(self, cli_session):
        cli_session.current_node.command_show_node_fsm_history(cli_session, False)

    def command_show_node_fsm_vhis(self, cli_session):
        cli_session.current_node.command_show_node_fsm_history(cli_session, True)

    def command_show_nodes(self, cli_session):
        tab = table.Table()
        tab.add_row(node.Node.cli_summary_headers())
        for nod in self._nodes.values():
            tab.add_row(nod.cli_summary_attributes())
        cli_session.print(tab.to_string())

    def command_show_nodes_level(self, cli_session):
        tab = table.Table()
        tab.add_row(node.Node.cli_level_headers())
        for nod in self._nodes.values():
            tab.add_row(nod.cli_level_attributes())
        cli_session.print(tab.to_string())

    def command_show_route_prefix(self, cli_session, parameters):
        cli_session.current_node.command_show_route_prefix(cli_session, parameters)

    def command_show_route_prefix_owner(self, cli_session, parameters):
        cli_session.current_node.command_show_route_prefix_owner(cli_session, parameters)

    def command_show_routes(self, cli_session):
        cli_session.current_node.command_show_routes(cli_session)

    def command_show_forwarding(self, cli_session):
        cli_session.current_node.command_show_forwarding(cli_session)

    def command_show_forwarding_prefix(self, cli_session, parameters):
        cli_session.current_node.command_show_forwarding_prefix(cli_session, parameters)

    def command_show_spf(self, cli_session):
        cli_session.current_node.command_show_spf(cli_session)

    def command_show_spf_dir(self, cli_session, parameters):
        cli_session.current_node.command_show_spf_dir(cli_session, parameters)

    def command_show_spf_dir_dest(self, cli_session, parameters):
        cli_session.current_node.command_show_spf_dir_dest(cli_session, parameters)

    def command_show_tie_db(self, cli_session):
        cli_session.current_node.command_show_tie_db(cli_session)

    def command_show_ztp_fsm(self, cli_session):
        node.Node.fsm_definition.command_show_fsm(cli_session)

    def command_set_node(self, cli_session, parameters):
        node_name = parameters['node']
        if node_name in self._nodes:
            cli_session.set_current_node(self._nodes[node_name])
        else:
            cli_session.print("Node {} does not exist".format(node_name))

    def command_set_level(self, cli_session, parameters):
        level_symbol = parameters['level'].lower()
        parsed_level = node.Node.parse_level_symbol(level_symbol)
        if parsed_level is None:
            cli_session.print("Invalid level value (expected undefined, leaf, leaf-to-leaf, "
                              "top-of-fabric, or number)")
            return
        cli_session.current_node.fsm.push_event(node.Node.Event.CHANGE_LOCAL_CONFIGURED_LEVEL,
                                                level_symbol)

    def command_exit(self, cli_session):
        cli_session.close()

    def command_stop(self, cli_session):
        cli_session.close()
        sys.exit(0)

    parse_tree = {
        "exit": command_exit,
        "set": {
            "$interface": {
                "$failure": command_set_interface_failure
            },
            "$node": command_set_node,
            "$level": command_set_level,
        },
        "show": {
            "engine":command_show_engine,
            "flooding-reduction": command_show_flooding_reduction,
            "forwarding": {
                "": command_show_forwarding,
                "$prefix": command_show_forwarding_prefix,
            },
            "fsm": {
                "lie": command_show_lie_fsm,
                "ztp": command_show_ztp_fsm,
            },
            "$interface": {
                "": command_show_interface,
                "fsm": {
                    "history": command_show_intf_fsm_nvhis,
                    "verbose-history": command_show_intf_fsm_vhis,
                },
                "queues": command_show_intf_queues,
                "sockets": command_show_intf_sockets
            },
            "interfaces": command_show_interfaces,
            "kernel": {
                "addresses": command_show_kernel_addresses,
                "links": command_show_kernel_links,
                "routes": {
                    "": command_show_kernel_routes,
                    "$table": {
                        "": command_show_kernel_routes_tab,
                    },
                },
                "route": {
                    "$table": {
                        "$prefix": command_show_kernel_route_pref,
                    },
                },
            },
            "node": {
                "": command_show_node,
                "fsm": {
                    "history": command_show_node_fsm_nvhis,
                    "verbose-history": command_show_node_fsm_vhis,
                },
            },
            "nodes": {
                "": command_show_nodes,
                "level": command_show_nodes_level,
            },
            "route": {
                "$prefix": {
                    "": command_show_route_prefix,
                    "$owner": command_show_route_prefix_owner,
                },
            },
            "routes": {
                "": command_show_routes,
                "$prefix": {
                    "": command_show_route_prefix,
                    "$owner": command_show_route_prefix_owner,
                },
            },
            "spf": {
                "": command_show_spf,
                "$direction" : {
                    "": command_show_spf_dir,
                    "$destination": command_show_spf_dir_dest
                },
            },
            "tie-db": command_show_tie_db,
        },
        "stop": command_stop,
    }

    @property
    def active_nodes(self):
        return self._run_which_nodes
