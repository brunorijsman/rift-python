import ctypes
import ipaddress
import socket
import struct

import scheduler
import utils

# On having multiple sockets for the same multicast group and the same port on different
# interfaces:
#
# We join the multicast group on a particular local interface, identified by local_address.
# That means multicast packets received on that interface will be accepted. Note, however,
# that if there are multiple sockets S1, S2, S3, ... that have joined the same multicast group
# (same multicast address and same port) on different interfaces I1, I2, I3, ... then if we
# receive a multicast packet on ANY of the interfaces I1, I2, I3... then ALL the sockets S1,
# S2, S3, ... will be notified that a packet has been received. We use the IP_PKTINFO socket
# option to determine on which interface I the packet was *really* received and ignore the
# packet on all other sockets.
#
# We use the IP_PKTINFO ancillary data to determine on which interface the packet was
# *really* received, and we ignore the packet if this socket is not associated with that
# particular interface. See comment in create_rx_socket for additional details.

# The following sections of this code, namely those dealing with IP_PKTINFO and in_pktinfo are based
# on github project https://github.com/etingof/pysnmp, which is subject to the BSD 2-Clause
# "Simplified" License, which allows us to re-use the code, under the condition that the following
# copyright notice included:
# Copyright (c) 2005-2019, Ilya Etingof <etingof@gmail.com> All rights reserved.
# See https://github.com/etingof/pysnmp/blob/master/LICENSE.rst for the license of the copied code.

SYMBOLS = {
    'IP_PKTINFO': 8,
    'IP_TRANSPARENT': 19,
    'SOL_IPV6': 41,
    'IPV6_ADD_MEMBERSHIP': 20,
    'IPV6_RECVPKTINFO': 49,
}

# pylint:disable=invalid-name
uint32_t = ctypes.c_uint32

in_addr_t = uint32_t

class in_addr(ctypes.Structure):
    _fields_ = [('s_addr', in_addr_t)]

class in6_addr_U(ctypes.Union):
    _fields_ = [
        ('__u6_addr8', ctypes.c_uint8 * 16),
        ('__u6_addr16', ctypes.c_uint16 * 8),
        ('__u6_addr32', ctypes.c_uint32 * 4),
    ]

class in6_addr(ctypes.Structure):
    _fields_ = [
        ('__in6_u', in6_addr_U),
    ]

class in_pktinfo(ctypes.Structure):
    _fields_ = [
        ('ipi_ifindex', ctypes.c_int),
        ('ipi_spec_dst', in_addr),
        ('ipi_addr', in_addr),
    ]

class in6_pktinfo(ctypes.Structure):
    _fields_ = [
        ('ipi6_addr', in6_addr),
        ('ipi6_ifindex', ctypes.c_int),
    ]

for symbol in SYMBOLS:
    if not hasattr(socket, symbol):
        setattr(socket, symbol, SYMBOLS[symbol])

class UdpRxHandler:

    MAX_SIZE = 65535

    def __init__(self, interface_name, local_port, remote_address, receive_function, log, log_id):
        self._interface_name = interface_name
        self._local_port = local_port
        self._remote_address = remote_address
        self._receive_function = receive_function
        self._log = log
        self._log_id = log_id
        self._local_ipv4_address = utils.interface_ipv4_address(interface_name)
        self._local_ipv6_address = utils.interface_ipv6_address(interface_name)
        try:
            self._interface_index = socket.if_nametoindex(interface_name)
        except IOError as err:
            self.warning("Could determine index of interface %s: %s", interface_name, err)
            self._interface_index = None
        if self.is_ipv6_address(remote_address):
            if ipaddress.IPv6Address(remote_address).is_multicast:
                self.sock = self.create_socket_ipv6_rx_mcast()
            else:
                self.sock = self.create_socket_ipv6_rx_ucast()
        else:
            if ipaddress.IPv4Address(remote_address).is_multicast:
                self.sock = self.create_socket_ipv4_rx_mcast()
            else:
                self.sock = self.create_socket_ipv4_rx_ucast()
        scheduler.SCHEDULER.register_handler(self, True, False)

    @staticmethod
    def is_ipv6_address(address):
        try:
            socket.inet_pton(socket.AF_INET6, address)
        except socket.error:
            return False
        return True

    def warning(self, msg, *args):
        self._log.warning("[%s] %s" % (self._log_id, msg), *args)

    def close(self):
        scheduler.SCHEDULER.unregister_handler(self)
        self.sock.close()

    def rx_fd(self):
        return self.sock.fileno()

    def ready_to_read(self):
        ancillary_size = socket.CMSG_LEN(self.MAX_SIZE)
        try:
            message, ancillary_messages, _msg_flags, from_address_and_port = \
                self.sock.recvmsg(self.MAX_SIZE, ancillary_size)
        except IOError as err:
            self.warning("Socket receive failed: %s", err)
        else:
            rx_interface_index = None
            for anc in ancillary_messages:
                # pylint:disable=no-member
                if anc[0] == socket.SOL_IP and anc[1] == socket.IP_PKTINFO:
                    packet_info = in_pktinfo.from_buffer_copy(anc[2])
                    rx_interface_index = packet_info.ipi_ifindex
                elif anc[0] == socket.SOL_IPV6 and anc[1] == socket.IPV6_PKTINFO:
                    packet_info = in6_pktinfo.from_buffer_copy(anc[2])
                    rx_interface_index = packet_info.ipi6_ifindex
            if rx_interface_index and (rx_interface_index != self._interface_index):
                # Message received on "wrong" interface; ignore
                return
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
        try:
            # pylint:disable=no-member
            sock.setsockopt(socket.IPPROTO_IP, socket.IP_PKTINFO, 1)
        except IOError as err:
            # Warn, but keep going; this socket option is not supported on macOS
            self.warning("Could not set IP_PKTINFO socket option: %s", err)
        return sock

    def create_socket_ipv6_rx_common(self):
        try:
            sock = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        except IOError as err:
            self.warning("Could not create IPv6 UDP socket: %s", err)
            return None
        self.enable_addr_and_port_reuse(sock)
        try:
            sock.bind((self._remote_address, self._local_port))
        except IOError as err:
            self.warning("Could not bind UDP socket to address %s port %d: %s",
                         self._remote_address, self._local_port, err)
            return None
        return sock

    def create_socket_ipv6_rx_ucast(self):
        return self.create_socket_ipv6_rx_common()

    def create_socket_ipv6_rx_mcast(self):
        sock = self.create_socket_ipv6_rx_common()
        req = struct.pack("=16si", socket.inet_pton(socket.AF_INET6, self._remote_address),
                          self._interface_index)
        try:
            # pylint:disable=no-member
            sock.setsockopt(socket.IPPROTO_IP6, socket.IPV6_ADD_MEMBERSHIP, req)
        except IOError as err:
            self.warning("Could not join group %s for interface index %s: %s",
                         self._remote_address, self._interface_index, err)
            return None
        try:
            # pylint:disable=no-member
            sock.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_RECVPKTINFO, 1)
        except IOError as err:
            # Warn, but keep going; this socket option is not supported on macOS
            self.warning("Could not set IPV6_RECVPKTINFO socket option: %s", err)
        return sock
