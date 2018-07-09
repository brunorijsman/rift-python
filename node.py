import logging
import os
import uuid
from cli_listen_handler import CliListenHandler

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

    command_tree = []

    @staticmethod
    def _system_id():
        mac_address = uuid.getnode()
        pid = os.getpid()
        system_id = ((mac_address & 0xffffffffff) << 24) | (pid & 0xffff)
        return system_id

    def __init__(self):
        self._system_id = Node._system_id()
        self._log_id = "{:016x}".format(self._system_id)
        self._log = logging.getLogger("node")
        self._log.info("[{}] Create node".format(self._log_id))
        self._configured_level = 0
        self._next_interface_id = 1
        self._multicast_loop = True      # TODO: make configurable
        self._lie_ipv4_multicast_address = self.DEFAULT_LIE_IPV4_MULTICAST_ADDRESS
        self._lie_ipv6_multicast_address = self.DEFAULT_LIE_IPV6_MULTICAST_ADDRESS
        self._lie_destination_port = self.DEFAULT_LIE_DESTINATION_PORT
        self._lie_send_interval_secs = self.DEFAULT_LIE_SEND_INTERVAL_SECS
        self._tie_destination_port = self.DEFAULT_TIE_DESTINATION_PORT
        self._cli_listen_handler = CliListenHandler(self.command_tree, self._log_id)

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
