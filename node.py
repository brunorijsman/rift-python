import logging
import os
import socket
import sortedcontainers
import uuid

import rift
import constants
import interface
import table
import utils

# TODO: Add support for non-configured levels
#       - Allow configured_level to be None
#       - In which case the Level Determination Procedure (section 4.2.9.4 of draft-ietf-rift-rift-02)
#         must be used

# TODO: Command line argument and/or configuration option for CLI port

class Node:

    _next_node_nr = 1

    def generate_system_id(self):
        mac_address = uuid.getnode()
        pid = os.getpid()
        system_id = ((mac_address & 0xffffffffff) << 24) | (pid & 0xffff) << 8 | (self._node_nr & 0xff)
        return system_id

    def generate_name(self):
        return socket.gethostname().split('.')[0] + str(self._node_nr)

    def __init__(self, rift, config):
        # TODO: process passive field in config
        # TODO: process level field in config
        # TODO: process systemid field in config
        # TODO: process state_thrift_services_port field in config
        # TODO: process config_thrift_services_port field in config
        # TODO: process v4prefixes field in config
        # TODO: process v6prefixes field in config
        self._rift = rift
        self._config = config
        self._node_nr = Node._next_node_nr
        Node._next_node_nr += 1
        self._name = self.get_config_attribute(config, 'name', self.generate_name())
        self._passive = self.get_config_attribute(config, 'passive', False)
        self._running = self.is_running()
        self._system_id = self.get_config_attribute(config, 'systemid', self.generate_system_id())
        self._log_id = utils.system_id_str(self._system_id)
        self._log = logging.getLogger('node')
        self._log.info("[{}] Create node".format(self._log_id))
        self._configured_level = 0
        self._next_interface_id = 1
        self._interfaces = sortedcontainers.SortedDict()
        self._mcast_loop = True      # TODO: make configurable
        self._rx_lie_ipv4_mcast_address = self.get_config_attribute(
            config, 'rx_lie_mcast_address', constants.DEFAULT_LIE_IPV4_MCAST_ADDRESS)
        self._tx_lie_ipv4_mcast_address = self.get_config_attribute(
            config, 'tx_lie_mcast_address', constants.DEFAULT_LIE_IPV4_MCAST_ADDRESS)
        self._rx_lie_ipv6_mcast_address = self.get_config_attribute(
            config, 'rx_lie_v6_mcast_address', constants.DEFAULT_LIE_IPV6_MCAST_ADDRESS)
        self._tx_lie_ipv6_mcast_address = self.get_config_attribute(
            config, 'tx_lie_v6_mcast_address', constants.DEFAULT_LIE_IPV6_MCAST_ADDRESS)
        self._rx_lie_port = self.get_config_attribute(config, 'rx_lie_port', constants.DEFAULT_LIE_PORT)
        self._tx_lie_port = self.get_config_attribute(config, 'tx_lie_port', constants.DEFAULT_LIE_PORT)
        self._lie_send_interval_secs = constants.DEFAULT_LIE_SEND_INTERVAL_SECS   # TODO: make configurable
        self._rx_tie_port = self.get_config_attribute(config, 'rx_tie_port', constants.DEFAULT_TIE_PORT)
        if 'interfaces' in config:
            for interface_config in self._config['interfaces']:
                self.create_interface(interface_config)

    def is_running(self):
        if self._rift.active_nodes == rift.Rift.ActiveNodes.ONLY_PASSIVE_NODES:
            running = self._passive
        elif self._rift.active_nodes == rift.Rift.ActiveNodes.ALL_NODES_EXCEPT_PASSIVE_NODES:
            running = not self._passive
        else:
            running = True
        return running

    def get_config_attribute(self, config, attribute, default):
        if attribute in config:
            return config[attribute]
        else:
            return default

    def create_interface(self, interface_config):
        interface_name = interface_config['name']
        self._interfaces[interface_name] = interface.Interface(self, interface_config)

    def cli_detailed_attributes(self):
        return [
            ["Name", self._name],
            ["Passive", self._passive],
            ["Running", self.is_running()],
            ["System ID", utils.system_id_str(self._system_id)],
            ["Configured Level", self._configured_level],
            ["Multicast Loop", self._mcast_loop],
            ["Receive LIE IPv4 Multicast Address", self._rx_lie_ipv4_mcast_address],
            ["Transmit LIE IPv4 Multicast Address", self._tx_lie_ipv4_mcast_address],
            ["Receive LIE IPv6 Multicast Address", self._rx_lie_ipv6_mcast_address],
            ["Transmit LIE IPv6 Multicast Address", self._tx_lie_ipv6_mcast_address],
            ["Receive LIE Port", self._rx_lie_port],
            ["Transmit LIE Port", self._tx_lie_port],
            ["LIE Send Interval", "{} secs".format(self._lie_send_interval_secs)],
            ["Receive TIE Port", self._rx_tie_port]
        ]

    def allocate_interface_id(self):
        # We assume an i32 is never going to happen (i.e. no more than ~2M interfaces)
        interface_id = self._next_interface_id
        self._next_interface_id += 1
        return interface_id

    @staticmethod
    def cli_summary_headers():
        return [
            ["Node", "Name"],
            ["System", "ID"],
            ["Running"]]

    def cli_summary_attributes(self):
        return [
            self._name,
            utils.system_id_str(self._system_id),
            self._running]

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

    @property
    def name(self):
        return self._name

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
    def lie_ipv4_mcast_address(self):
        return self._rx_lie_ipv4_mcast_address

    @property
    def lie_ipv6_mcast_address(self):
        return self._rx_lie_ipv6_mcast_address

    @property
    def lie_destination_port(self):
        return self._tx_lie_port

    @property
    def lie_send_interval_secs(self):
        return self._lie_send_interval_secs

    @property
    def mcast_loop(self):
        return self._mcast_loop

    @property
    def running(self):
        return self._running

    @property
    def rift(self):
        return self._rift
