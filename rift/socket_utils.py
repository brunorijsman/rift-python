# We join the multicast group on a particular local interface, identified by local_address.
# That means multicast packets received on that interface will be accepted. Note, however,
# that if there are multiple sockets S1, S2, S3, ... that have joined the same multicast group
# (same multicast address and same port) on different interfaces I1, I2, I3, ... then if we
# receive a multicast packet on ANY of the interfaces I1, I2, I3... then ALL the sockets S1,
# S2, S3, ... will be notified that a packet has been received. We use the IP_PKTINFO socket
# option to determine on which interface I the packet was *really* received and ignore the
# packet on all other sockets.

# We use the IP_PKTINFO ancillary data to determine on which interface the packet was
# *really* received, and we ignore the packet if this socket is not associated with that
# particular interface. See comment in create_rx_socket for additional details.

# Disable the loopback of sent multicast packets to listening sockets on the same host. We don't
# want this to happen because each beacon is listening on the same port and the same multicast
# address on potentially multiple interfaces. Each receive socket should only receive packets
# that were sent by the host on the other side of the interface, and not packet that were sent
# from the same host on a different interface. IP_MULTICAST_IF is enabled by default, so we have
# to explicitly disable it)

# TODO: Set TTL as follows:
# ttl_bin = struct.pack('@i', MYTTL)
# if addrinfo[0] == socket.AF_INET: # IPv4
#     s.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl_bin)
# else:
#     s.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_MULTICAST_HOPS, ttl_bin)

# TODO: Set TOS and Priority

import ctypes
import socket
import struct

import netifaces

###@@@
IPV4_MULTICAST_ADDR = "224.0.0.120"
IPV6_MULTICAST_ADDR = "FF02::A1F7"
MULTICAST_PORT = 911

###@@@
MAX_SIZE = 1024

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

def interface_ipv4_address(interface_name):
    interface_addresses = netifaces.interfaces()
    if not interface_name in netifaces.interfaces():
        return None
    interface_addresses = netifaces.ifaddresses(interface_name)
    if not netifaces.AF_INET in interface_addresses:
        return None
    address_str = interface_addresses[netifaces.AF_INET][0]['addr']
    return address_str

def interface_ipv6_address(interface_name, exclude_scope=False):
    interface_addresses = netifaces.interfaces()
    if not interface_name in netifaces.interfaces():
        return None
    interface_addresses = netifaces.ifaddresses(interface_name)
    if not netifaces.AF_INET6 in interface_addresses:
        return None
    address_str = interface_addresses[netifaces.AF_INET6][0]['addr']
    if exclude_scope:
        if "%" in address_str:
            address_str = address_str.split("%")[0]
    return address_str

def enable_addr_and_port_reuse(sock):
    try:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    except AttributeError:
        pass
    try:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
    except AttributeError:
        pass

def create_ipv4_mcast_rx_socket(interface_name):
    # pylint:disable=no-member
    local_address = interface_ipv4_address(interface_name)
    if local_address is None:
        return None
    sock = socket.socket(netifaces.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    enable_addr_and_port_reuse(sock)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_PKTINFO, 1)
    sock.bind((IPV4_MULTICAST_ADDR, MULTICAST_PORT))
    req = struct.pack("=4s4s", socket.inet_aton(IPV4_MULTICAST_ADDR),
                      socket.inet_aton(local_address))
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, req)
    return sock

def create_ipv6_mcast_rx_socket(interface_name):
    # pylint:disable=no-member
    sock = socket.socket(netifaces.AF_INET6, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    enable_addr_and_port_reuse(sock)
    sock.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_RECVPKTINFO, 1)
    sock.bind(("::", MULTICAST_PORT))
    interface_index = socket.if_nametoindex(interface_name)
    req = struct.pack("=16si", socket.inet_pton(netifaces.AF_INET6, IPV6_MULTICAST_ADDR),
                      interface_index)
    sock.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_ADD_MEMBERSHIP, req)
    return sock

def create_socket_ipv4_tx_mcast(interface_name, multicast_address, port, multicast_loopback):
    sock = socket.socket(netifaces.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    enable_addr_and_port_reuse(sock)
    sock.connect((multicast_address, port))
    local_address = interface_ipv4_address(interface_name)
    if local_address is not None:
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_IF, socket.inet_aton(local_address))
    loop_value = 1 if multicast_loopback else 0
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_LOOP, loop_value)
    return sock

def create_socket_ipv4_tx_ucast(remote_address, remote_port):
    sock = socket.socket(netifaces.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    enable_addr_and_port_reuse(sock)
    sock.connect((remote_address, remote_port))
    return sock

def create_ipv6_mcast_tx_socket(interface_name):
    sock = socket.socket(netifaces.AF_INET6, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    enable_addr_and_port_reuse(sock)
    interface_index = socket.if_nametoindex(interface_name)
    sock.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_MULTICAST_IF, interface_index)
    sock.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_MULTICAST_LOOP, 0)
    sock.connect((IPV6_MULTICAST_ADDR, MULTICAST_PORT))
    return sock

###@@@ Here or move?

# def receive(sock_info):
#     # pylint:disable=too-many-locals
#     (sock, interface_name, interface_index) = sock_info
#     ancillary_size = socket.CMSG_LEN(MAX_SIZE)
#     try:
#         message, ancillary_messages, _msg_flags, source = sock.recvmsg(MAX_SIZE, ancillary_size)
#         message_str = message.decode()
#     except Exception as exception:
#         report("exception {} while receiving on {}".format(exception, interface_name))
#     else:
#         rx_interface_index = None
#         for anc in ancillary_messages:
#             # pylint:disable=no-member
#             if anc[0] == socket.SOL_IP and anc[1] == socket.IP_PKTINFO:
#                 packet_info = in_pktinfo.from_buffer_copy(anc[2])
#                 rx_interface_index = packet_info.ipi_ifindex
#             elif anc[0] == socket.SOL_IPV6 and anc[1] == socket.IPV6_PKTINFO:
#                 packet_info = in6_pktinfo.from_buffer_copy(anc[2])
#                 rx_interface_index = packet_info.ipi6_ifindex
#         if rx_interface_index and (rx_interface_index != interface_index):
#             return
#         report("received {} on {} from {}".format(message_str, interface_name, source))

# def send(sock_info, message):
#     (sock, interface_name, _interface_index) = sock_info
#     try:
#         report("send {} on {} from {} to {}".format(message, interface_name, sock.getsockname(),
#                                                     sock.getpeername()))
#         sock.send(message.encode())
#     except Exception as exception:
#         report("exception {} while sending {} on {}".format(exception, message, interface_name))
