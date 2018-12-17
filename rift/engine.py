import logging
import os
import sys

import sortedcontainers

import cli_listen_handler
import cli_session_handler
import interface
import node
import scheduler
import table

# TODO: Make sure that there is always at least one node (and hence always a current node)

class Engine:

    def __init__(self, passive_nodes, run_which_nodes, interactive, multicast_loopback, log_level,
                 config):
        log_file_name = "rift.log"
        if "RIFT_TEST_RESULTS_DIR" in os.environ:
            log_file_name = os.environ["RIFT_TEST_RESULTS_DIR"] + "/" + log_file_name
        logging.basicConfig(
            filename=log_file_name,
            format='%(asctime)s:%(levelname)s:%(name)s:%(message)s',
            level=log_level)
        self._run_which_nodes = run_which_nodes
        self._interactive = interactive
        self._multicast_loopback = multicast_loopback
        self._config = config
        self._tx_src_address = self.read_global_configuration(config, 'tx_src_address', '')
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

    def read_global_configuration(self, config, attribute, default):
        if ('const' in config) and (config['const'] is not None) and (attribute in config['const']):
            return config['const'][attribute]
        else:
            return default

    def create_configuration(self, passive_nodes):
        if 'shards' in self._config:
            total_nr_nodes = 0
            for shard_config in self._config['shards']:
                if 'nodes' in shard_config:
                    for _node_config in shard_config['nodes']:
                        total_nr_nodes += 1
            stand_alone = (total_nr_nodes <= 1)
            for shard_config in self._config['shards']:
                self.create_shard(shard_config, passive_nodes, stand_alone)

    def create_shard(self, shard_config, passive_nodes, stand_alone):
        if 'nodes' in shard_config:
            for node_config in shard_config['nodes']:
                if 'name' in node_config:
                    force_passive = node_config['name'] in passive_nodes
                else:
                    force_passive = False
                self.create_node(node_config, force_passive, stand_alone)

    def create_node(self, node_config, force_passive, stand_alone):
        new_node = node.Node(node_config, self, force_passive, stand_alone)
        self._nodes[new_node.name] = new_node

    def run(self):
        scheduler.SCHEDULER.run()

    def command_show_intf_fsm_nvhis(self, cli_session, parameters):
        cli_session.current_node.command_show_intf_fsm_hist(cli_session, parameters, False)

    def command_show_intf_fsm_vhis(self, cli_session, parameters):
        cli_session.current_node.command_show_intf_fsm_hist(cli_session, parameters, True)

    def command_show_intf_queues(self, cli_session, parameters):
        cli_session.current_node.command_show_intf_queues(cli_session, parameters)

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

    def command_show_kernel_attribs(self, cli_session):
        cli_session.current_node.command_show_kernel_attribs(cli_session)

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
                "queues": command_show_intf_queues
            },
            "interfaces": command_show_interfaces,
            "kernel": {
                "addresses": command_show_kernel_addresses,
                "links": command_show_kernel_links,
                "netlink-attributes": command_show_kernel_attribs,
                "routes": {
                    "": command_show_kernel_routes,
                    "$table": {
                        "": command_show_kernel_routes_tab,
                        "$prefix": command_show_kernel_route_pref,
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

    @property
    def tx_src_address(self):
        return self._tx_src_address

    @property
    def multicast_loopback(self):
        return self._multicast_loopback
