import enum
import logging
import socket
import sortedcontainers

import cli_listen_handler
import interface
import node
import scheduler
import table

class Rift:

    class ActiveNodes(enum.Enum):
        ALL_NODES = 1
        ONLY_PASSIVE_NODES = 2
        ALL_NODES_EXCEPT_PASSIVE_NODES = 3

    def __init__(self, active_nodes, config):
        logging.basicConfig(
            filename = 'rift.log', 
            format = '%(asctime)s:%(levelname)s:%(name)s:%(message)s', 
            level = logging.DEBUG)
        self._active_nodes = active_nodes
        self._config = config
        self._nodes = sortedcontainers.SortedDict()
        self.create_configuration()
        if self._nodes:
            (first_name, first_node) = self._nodes.peekitem(0)
            self._cli_current_node = first_node
            self._cli_current_prompt = first_name
        else:
            self._cli_current_node = None
            self._cli_current_prompt = ''
        self._cli_listen_handler = cli_listen_handler.CliListenHandler(self.parse_tree, self, self._cli_current_prompt)

    def create_configuration(self):
        if 'shards' in self._config:
            for shard_config in self._config['shards']:
                self.create_shard(shard_config)

    def create_shard(self, shard_config):
        if 'nodes' in shard_config:
            for node_config in shard_config['nodes']:
                self.create_node(node_config)

    def create_node(self, node_config):
        new_node = node.Node(self, node_config)
        self._nodes[new_node.name] = new_node

    def run(self):
        scheduler.scheduler.run()

    def command_show_lie_fsm(self, cli_session):
        interface.Interface.fsm_definition.command_show_fsm(cli_session)

    def command_show_ztp_fsm(self, cli_session):
        node.Node.fsm_definition.command_show_fsm(cli_session)

    def command_show_nodes(self, cli_session):
        tab = table.Table()
        tab.add_row(node.Node.cli_summary_headers())
        for n in self._nodes.values():
            tab.add_row(n.cli_summary_attributes())
        cli_session.print(tab.to_string())

    def command_show_nodes_level(self, cli_session):
        tab = table.Table()
        tab.add_row(node.Node.cli_level_headers())
        for n in self._nodes.values():
            tab.add_row(n.cli_level_attributes())
        cli_session.print(tab.to_string())

    def command_show_node(self, cli_session, parameters = None):
        if parameters and 'node-name' in parameters:
            node_name = paramters['node-name']
        else:
            node_name = self._cli_current_node
        if node_name:
            self._cli_current_node.command_show_node(cli_session)
        else:
            cli_session.print("No current node")

    def command_show_interfaces(self, cli_session):
        if self._cli_current_node:
            self._cli_current_node.command_show_interfaces(cli_session)
        else:
            cli_session.print("No current node")

    def command_show_interface(self, cli_session, parameters):
        if self._cli_current_node:
            self._cli_current_node.command_show_interface(cli_session, parameters)
        else:
            cli_session.print("No current node")

    def command_show_interface_fsm_history(self, cli_session, parameters):
        if self._cli_current_node:
            self._cli_current_node.command_show_interface_fsm_history(cli_session, parameters)
        else:
            cli_session.print("No current node")

    def command_set_node(self, cli_session, parameters):
        node_name = parameters['node']
        if node_name in self._nodes:
            self._cli_current_node = self._nodes[node_name]
            self._cli_current_prompt = node_name
            cli_session.set_prompt(node_name)
        else:
            cli_session.print("Node {} does not exist".format(node_name))

    # TODO: Add exit command
    parse_tree = {
        "set": {
            "$node": command_set_node
        },
        "show": {
            "fsm": {
                "lie": command_show_lie_fsm,
                "ztp": command_show_ztp_fsm,
            },
            "node": command_show_node,
            "nodes": {
                "": command_show_nodes,
                "level": command_show_nodes_level,
            },
            "$interface": {
                "": command_show_interface,
                "fsm-history": command_show_interface_fsm_history,
            },
            "interfaces": command_show_interfaces,
        },
    }

    @property
    def active_nodes(self):
        return self._active_nodes
