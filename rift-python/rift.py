import enum
import logging
import sortedcontainers

import cli_listen_handler
import interface
import node
import scheduler
import table

# TODO: Make sure that there is always at least one node (and hence always a current node)

class Rift:

    class ActiveNodes(enum.Enum):
        ALL_NODES = 1
        ONLY_PASSIVE_NODES = 2
        ALL_NODES_EXCEPT_PASSIVE_NODES = 3

    def __init__(self, active_nodes, log_level, config):
        logging.basicConfig(
            filename='rift.log',
            format='%(asctime)s:%(levelname)s:%(name)s:%(message)s',
            level=log_level)
        self._active_nodes = active_nodes
        self._config = config
        self._tx_src_address = self.read_global_configuration(config, 'tx_src_address', '')
        self._nodes = sortedcontainers.SortedDict()
        self.create_configuration()
        if self._nodes:
            (first_name, first_node) = self._nodes.peekitem(0)
            self._cli_current_node = first_node
            self._cli_current_prompt = first_name
        else:
            self._cli_current_node = None
            self._cli_current_prompt = ''
        self._cli_listen_handler = (
            cli_listen_handler.CliListenHandler(self.parse_tree, self, self._cli_current_prompt))

    def read_global_configuration(self, config, attribute, default):
        if ('const' in config) and (config['const'] is not None) and (attribute in config['const']):
            return config['const'][attribute]
        else:
            return default

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
        scheduler.SCHEDULER.run()

    def command_show_lie_fsm(self, cli_session):
        interface.Interface.fsm_definition.command_show_fsm(cli_session)

    def command_show_ztp_fsm(self, cli_session):
        node.Node.fsm_definition.command_show_fsm(cli_session)

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

    def command_show_node(self, cli_session):
        self._cli_current_node.command_show_node(cli_session)

    def command_show_node_fsm_nvhis(self, cli_session):
        self._cli_current_node.command_show_node_fsm_history(cli_session, False)

    def command_show_node_fsm_vhis(self, cli_session):
        self._cli_current_node.command_show_node_fsm_history(cli_session, True)

    def command_show_interfaces(self, cli_session):
        self._cli_current_node.command_show_interfaces(cli_session)

    def command_show_interface(self, cli_session, parameters):
        self._cli_current_node.command_show_interface(cli_session, parameters)

    def command_show_intf_fsm_nvhis(self, cli_session, parameters):
        self._cli_current_node.command_show_intf_fsm_hist(cli_session, parameters, False)

    def command_show_intf_fsm_vhis(self, cli_session, parameters):
        self._cli_current_node.command_show_intf_fsm_hist(cli_session, parameters, True)

    def command_set_node(self, cli_session, parameters):
        node_name = parameters['node']
        if node_name in self._nodes:
            self._cli_current_node = self._nodes[node_name]
            self._cli_current_prompt = node_name
            cli_session.set_prompt(node_name)
        else:
            cli_session.print("Node {} does not exist".format(node_name))

    def command_set_level(self, cli_session, parameters):
        level_symbol = parameters['level'].lower()
        parsed_level = node.Node.parse_level_symbol(level_symbol)
        if parsed_level is None:
            cli_session.print("Invalid level value (expected undefined, leaf, leaf-to-leaf, "
                              "superspine, or number)")
            return
        self._cli_current_node.fsm.push_event(node.Node.Event.CHANGE_LOCAL_CONFIGURED_LEVEL,
                                              level_symbol)

    # TODO: Add exit command
    # TODO: Update documentation with current state of commands (including example output)
    parse_tree = {
        "set": {
            "$node": command_set_node,
            "$level": command_set_level,
        },
        "show": {
            "fsm": {
                "lie": command_show_lie_fsm,
                "ztp": command_show_ztp_fsm,
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
            "$interface": {
                "": command_show_interface,
                "fsm": {
                    "history": command_show_intf_fsm_nvhis,
                    "verbose-history": command_show_intf_fsm_vhis,
                }
            },
            "interfaces": command_show_interfaces,
        },
    }

    @property
    def active_nodes(self):
        return self._active_nodes

    @property
    def tx_src_address(self):
        return self._tx_src_address
