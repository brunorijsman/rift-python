import ctypes
import errno
import platform
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

MACOS = platform.system() == "Darwin"

SYMBOLS = {
    'IP_TRANSPARENT': 19,
    'SOL_IPV6': 41,
    'IPV6_ADD_MEMBERSHIP': 20,
}

if not MACOS:
    SYMBOLS['IP_PKTINFO'] = 8
    SYMBOLS['IPV6_RECVPKTINFO'] = 49

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

    def __init__(self, interface_name, local_port, ipv4, multicast_address, remote_address,
                 receive_function, log, log_id, use_broadcast=False):
        self._interface_name = interface_name
        self._local_port = local_port
        self._ipv4 = ipv4                             # IPv4 if True, IPv6 if False
        self._remote_address = remote_address
        self._multicast_address = multicast_address   # Unicast socket if None
        self._receive_function = receive_function
        self._log = log
        self._log_id = log_id
        self._local_ipv4_address, _mask = utils.interface_ipv4_address(interface_name)
        self._local_ipv6_address = utils.interface_ipv6_address(interface_name)
        try:
            self._interface_index = socket.if_nametoindex(interface_name)
        except (IOError, OSError) as err:
            self.warning("Could determine index of interface %s: %s", interface_name, err)
            self._interface_index = None
        if ipv4:
            if self._multicast_address:
                self.sock = self.create_socket_ipv4_rx_mcast(use_broadcast)
            else:
                self.sock = self.create_socket_ipv4_rx_ucast()
        else:
            if self._multicast_address:
                self.sock = self.create_socket_ipv6_rx_mcast()
            else:
                self.sock = self.create_socket_ipv6_rx_ucast()
        if self.sock:
            scheduler.SCHEDULER.register_handler(self)

    def warning(self, msg, *args):
        self._log.warning("[%s] %s" % (self._log_id, msg), *args)

    def close(self):
        scheduler.SCHEDULER.unregister_handler(self)
        if self.sock is not None:
            self.sock.close()
            self.sock = None

    def rx_fd(self):
        if self.sock:
            return self.sock.fileno()
        else:
            return None

    def ready_to_read(self):
        while True:
            ancillary_size = socket.CMSG_LEN(self.MAX_SIZE)
            try:
                message, ancillary_messages, _msg_flags, from_info = \
                    self.sock.recvmsg(self.MAX_SIZE, ancillary_size)
            except (IOError, OSError) as err:
                if err.args[0] != errno.EWOULDBLOCK:
                    self.warning("Socket receive failed: %s", err)
                return
            if not MACOS:
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
            self._receive_function(message, from_info, self.sock)

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

    def create_socket_ipv4_rx_ucast(self):
        if self._local_ipv4_address is None:
            self.warning("Could not create IPv4 UDP socket: don't have a local address")
            return None
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        except (IOError, OSError) as err:
            self.warning("Could not create IPv4 UDP socket: %s", err)
            return None
        self.enable_addr_and_port_reuse(sock)
        try:
            sock.bind((self._local_ipv4_address, self._local_port))
        except (IOError, OSError) as err:
            self.warning("Could not bind IPv4 UDP socket to address %s port %d: %s",
                         self._local_ipv4_address, self._local_port, err)
            return None
        try:
            sock.setblocking(0)
        except (IOError, OSError) as err:
            self.warning("Could set unicast receive IPv4 UDP to non-blocking mode: %s", err)
            return None
        return sock

    def create_socket_ipv4_rx_mcast(self,use_broadcast):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        except (IOError, OSError) as err:
            self.warning("Could not create IPv4 UDP socket: %s", err)
            return None
        self.enable_addr_and_port_reuse(sock)
        try:
            sock.bind((self._multicast_address, self._local_port))
        except (IOError, OSError) as err:
            self.warning("Could not bind IPv4 UDP socket to address %s port %d: %s",
                         self._multicast_address, self._local_port, err)
            return None
        if sock is None:
            return None
        if not use_broadcast:
            if self._local_ipv4_address:
                req = struct.pack("=4s4s", socket.inet_aton(self._multicast_address),
                                  socket.inet_aton(self._local_ipv4_address))
            else:
                req = struct.pack("=4sl", socket.inet_aton(self._multicast_address), socket.INADDR_ANY)
            try:
                sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, req)
            except (IOError, OSError) as err:
                self.warning("Could not join IPv4 group %s for local address %s: %s",
                             self._multicast_address, self._local_ipv4_address, err)
                return None
        if not MACOS:
            try:
                # pylint:disable=no-member
                sock.setsockopt(socket.IPPROTO_IP, socket.IP_PKTINFO, 1)
            except (IOError, OSError) as err:
                # Warn, but keep going; this socket option is not supported on macOS
                self.warning("Could not set IP_PKTINFO socket option: %s", err)
        try:
            sock.setblocking(0)
        except (IOError, OSError) as err:
            self.warning("Could set multicast receive IPv4 UDP to non-blocking mode: %s", err)
            return None
        return sock

    def create_socket_ipv6_rx_ucast(self):
        if self._local_ipv6_address is None:
            self.warning("Could not create IPv6 UDP socket: don't have a local address")
            return None
        try:
            sock = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        except (IOError, OSError) as err:
            self.warning("Could not create IPv6 UDP socket: %s", err)
            return None
        self.enable_addr_and_port_reuse(sock)
        try:
            sockaddr = socket.getaddrinfo(self._local_ipv6_address,
                                          self._local_port,
                                          socket.AF_INET6,
                                          socket.SOCK_DGRAM)[0][4]
            sock.bind(sockaddr)
        except (IOError, OSError) as err:
            self.warning("Could not bind IPv6 UDP socket to address %s port %d: %s",
                         self._local_ipv6_address, self._local_port, err)
            return None
        try:
            sock.setblocking(0)
        except (IOError, OSError) as err:
            self.warning("Could set unicast receive IPv6 UDP to non-blocking mode: %s", err)
            return None
        return sock

    def create_socket_ipv6_rx_mcast(self):
        if self._interface_index is None:
            self.warning("Could not create IPv6 multicast receive socket: "
                         "unknown interface index")
            return None
        try:
            sock = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        except (IOError, OSError) as err:
            self.warning("Could not create IPv6 UDP socket: %s", err)
            return None
        self.enable_addr_and_port_reuse(sock)
        try:
            scoped_ipv6_multicast_address = (
                str(self._multicast_address) + '%' + self._interface_name)
            sockaddr = socket.getaddrinfo(scoped_ipv6_multicast_address,
                                          self._local_port,
                                          socket.AF_INET6,
                                          socket.SOCK_DGRAM)[0][4]
            sock.bind(sockaddr)
        except (IOError, OSError) as err:
            self.warning("Could not bind IPv6 UDP socket to address %s port %d: %s",
                         self._multicast_address, self._local_port, err)
            return None
        try:
            # pylint:disable=no-member
            req = struct.pack("=16si", socket.inet_pton(socket.AF_INET6, self._multicast_address),
                              self._interface_index)
            if MACOS:
                sock.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_JOIN_GROUP, req)
            else:
                sock.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_ADD_MEMBERSHIP, req)
        except (IOError, OSError) as err:
            self.warning("Could not join IPv6 group %s for interface index %s: %s",
                         self._multicast_address, self._interface_index, err)
            return None
        if not MACOS:
            try:
                # pylint:disable=no-member
                sock.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_RECVPKTINFO, 1)
            except (IOError, OSError) as err:
                # Warn, but keep going; this socket option is not supported on macOS
                self.warning("Could not set IPV6_RECVPKTINFO socket option: %s", err)
        try:
            sock.setblocking(0)
        except (IOError, OSError) as err:
            self.warning("Could set multicast receive IPv6 UDP to non-blocking mode: %s", err)
            return None
        return sock
