import logging
import os
import socket
import sortedcontainers
import uuid

import cli_listen_handler
import interface
import table

# TODO: Add hierarchical configuration with inheritance
# TODO: Add support for non-configured levels
#       - Allow configured_level to be None
#       - In which case the Level Determination Procedure (section 4.2.9.4 of draft-ietf-rift-rift-02)
#         must be used
# TODO: Command line argument and/or configuration option for CLI port

class Node:

    DEFAULT_LIE_IPV4_MULTICAST_ADDRESS = '224.0.0.120'
    DEFAULT_LIE_IPV6_MULTICAST_ADDRESS = 'FF02::0078'     # TODO: Add IPv6 support
    DEFAULT_LIE_DESTINATION_PORT = 10000    # TODO: Change to 911 (needs root privs)
    DEFAULT_LIE_SEND_INTERVAL_SECS = 1.0    # TODO: What does the draft say?

    DEFAULT_TIE_DESTINATION_PORT = 10001    # TODO: Change to 912 (needs root privs)

    def command_show_node(self, cli_session):
        tab = table.Table(separators = False)
        tab.add_rows(self.cli_detailed_attributes())
        cli_session.print(tab.to_string())

    def command_show_interfaces(self, cli_session):
        # TODO: Report neighbor uptime (time in THREE_WAY state)
        tab = table.Table()
        tab.add_row(interface.Interface.cli_summary_headers())
        for intf in self._interfaces.values():
            tab.add_row(intf.cli_summary_attributes())
        cli_session.print(tab.to_string())

    def command_show_interface(self, cli_session, parameters):
        interface_name = parameters['interface-name']
        if not interface_name in self._interfaces:
            cli_session.print("Error: interface {} not present".format(interface_name))
            return
        inteface_attributes = self._interfaces[interface_name].cli_detailed_attributes()
        tab = table.Table(separators = False)
        tab.add_rows(inteface_attributes)
        cli_session.print("Interface:")
        cli_session.print(tab.to_string())
        neighbor_attributes = self._interfaces[interface_name].cli_detailed_neighbor_attributes()
        if neighbor_attributes:
            tab = table.Table(separators = False)
            tab.add_rows(neighbor_attributes)
            cli_session.print("Neighbor:")
            cli_session.print(tab.to_string())

    command_tree = {
        "show": {
            "node": command_show_node,
            "interfaces": command_show_interfaces,
            "interface": {
                "<interface-name>": command_show_interface,
            }
        }
    }

    @staticmethod
    def _system_id():
        mac_address = uuid.getnode()
        pid = os.getpid()
        system_id = ((mac_address & 0xffffffffff) << 24) | (pid & 0xffff)
        return system_id

    def __init__(self, config):
        # TODO: process passive field in config
        # TODO: process level field in config
        # TODO: process systemid field in config
        # TODO: process rx_lie_mcast_address field in config
        # TODO: process rx_lie_v6_mcast_address field in config
        # TODO: process rx_lie_port field in config
        # TODO: process tx_lie_port field in config
        # TODO: process state_thrift_services_port field in config
        # TODO: process config_thrift_services_port field in config
        # TODO: process v4prefixes field in config
        # TODO: process v6prefixes field in config
        self._config = config
        self._name = config['name']
        self._system_id = Node._system_id()
        self._log_id = "{:016x}".format(self._system_id)
        self._log = logging.getLogger("node")
        self._log.info("[{}] Create node".format(self._log_id))
        self._configured_level = 0
        self._next_interface_id = 1
        self._interfaces = sortedcontainers.SortedDict()
        self._multicast_loop = True      # TODO: make configurable
        self._lie_ipv4_multicast_address = self.DEFAULT_LIE_IPV4_MULTICAST_ADDRESS
        self._lie_ipv6_multicast_address = self.DEFAULT_LIE_IPV6_MULTICAST_ADDRESS
        self._lie_destination_port = self.DEFAULT_LIE_DESTINATION_PORT
        self._lie_send_interval_secs = self.DEFAULT_LIE_SEND_INTERVAL_SECS
        self._tie_destination_port = self.DEFAULT_TIE_DESTINATION_PORT
        self._cli_listen_handler = cli_listen_handler.CliListenHandler(self.command_tree, self, self._log_id)
        if 'interfaces' in config:
            for interface_config in self._config['interfaces']:
                self.create_interface(interface_config)

    def create_interface(self, interface_config):
        interface_name = interface_config['name']
        self._interfaces[interface_name] = interface.Interface(self, interface_config)

    def cli_detailed_attributes(self):
        return [
            ["Name", self._name],
            ["System ID", "{:016x}".format(self._system_id)],
            ["Configured Level", self._configured_level],
            ["Multicast Loop", self._multicast_loop],
            ["LIE IPv4 Multicast Address", self._lie_ipv4_multicast_address],
            ["LIE IPv6 Multicast Address", self._lie_ipv6_multicast_address],
            ["LIE Destination Port", self._lie_destination_port],
            ["LIE Send Interval", "{} secs".format(self._lie_send_interval_secs)],
            ["TIE Destination Port", self._tie_destination_port],
        ]

    def allocate_interface_id(self):
        # We assume an i32 is never going to happen (i.e. no more than ~2M interfaces)
        interface_id = self._next_interface_id
        self._next_interface_id += 1
        return interface_id

    # TODO: get rid of these properties, more complicated than needed. Just remote _ instead
    @property
    def system_id(self):
        return self._system_id

    @property
    def configured_level(self):
        return self._configured_level

    @property
    def advertised_level(self):
        # TODO: Handle configured_level == None (see TODO at top of file)
        return self.configured_level

    @property
    def lie_ipv4_multicast_address(self):
        return self._lie_ipv4_multicast_address

    @property
    def lie_ipv6_multicast_address(self):
        return self._lie_ipv6_multicast_address

    @property
    def lie_destination_port(self):
        return self._lie_destination_port

    @property
    def lie_send_interval_secs(self):
        return self._lie_send_interval_secs

    @property
    def tie_destination_port(self):
        return self._tie_destination_port

    @property
    def multicast_loop(self):
        return self._multicast_loop
