import ipaddress
import socket
import struct

import scheduler
import utils

class UdpRxHandler:

    MAXIMUM_MESSAGE_SIZE = 65535

    def __init__(self, interface_name, local_port, remote_address, receive_function, log, log_id):
        self._interface_name = interface_name
        self._local_port = local_port
        self._remote_address = remote_address
        self._receive_function = receive_function
        self._log = log
        self._log_id = log_id
        self._local_ipv4_address = utils.interface_ipv4_address(interface_name)
        if ipaddress.IPv4Address(remote_address).is_multicast:
            self.sock = self.create_socket_ipv4_rx_mcast()
        else:
            self.sock = self.create_socket_ipv4_rx_ucast()
        scheduler.SCHEDULER.register_handler(self, True, False)

    def warning(self, msg, *args):
        self._log.warning("[%s] %s" % (self._log_id, msg), *args)

    def close(self):
        scheduler.SCHEDULER.unregister_handler(self)
        self.sock.close()

    def rx_fd(self):
        return self.sock.fileno()

    def ready_to_read(self):
        message, from_address_and_port = self.sock.recvfrom(self.MAXIMUM_MESSAGE_SIZE)
        self._receive_function(message, from_address_and_port)

    @staticmethod
    def enable_addr_and_port_reuse(sock):
        # Ignore exceptions because not all operating systems support these. If not setting the
        # REUSE... option causes trouble, that will be caught later on.
        try:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        except AttributeError:
            pass
        try:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        except AttributeError:
            pass

    def create_socket_ipv4_rx_common(self):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        except IOError as err:
            self.warning("Could not create IPv4 UDP socket: %s", err)
            return None
        self.enable_addr_and_port_reuse(sock)
        try:
            sock.bind((self._remote_address, self._local_port))
        except IOError as err:
            self.warning("Could not bind UDP socket to address %s port %d: %s",
                         self._remote_address, self._local_port, err)
            return None
        return sock

    def create_socket_ipv4_rx_ucast(self):
        return self.create_socket_ipv4_rx_common()

    def create_socket_ipv4_rx_mcast(self):
        sock = self.create_socket_ipv4_rx_common()
        if self._local_ipv4_address:
            req = struct.pack("=4s4s", socket.inet_aton(self._remote_address),
                              socket.inet_aton(self._local_ipv4_address))
        else:
            req = struct.pack("=4sl", socket.inet_aton(self._remote_address), socket.INADDR_ANY)
        try:
            sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, req)
        except IOError as err:
            self.warning("Could not join group %s for local address %s: %s",
                         self._remote_address, self._local_ipv4_address, err)
            return None
        return sock
