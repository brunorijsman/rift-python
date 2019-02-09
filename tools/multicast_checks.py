#!/usr/bin/env python3

import ctypes
import platform
import select
import socket
import struct
import time

import netifaces

# TODO: Avoid duplicate code in udp_rx_handler

# pylint:disable=no-member

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

# Check whether this IP_MULTICAST_LOOP socket option is needed in this environment (it depends
# on the behavior of the router to which this host is connected)
# See http://bit.ly/multicast-duplication for more details
#
def ipv4_loopback_needed():
    return _loopback_needed(ipv6=False)

def ipv6_loopback_needed():
    ## return True
    return _loopback_needed(ipv6=True)

def _loopback_needed(ipv6):
    # If we receive a single copy when loopback is disabled, then we need to disable loopback
    if _copies_received(ipv6, False) == 1:
        return False
    # We receive zero copies with loopback disabled. Make sure we do receive a single copy with
    # loopback enabled.
    copies = _copies_received(ipv6, True)
    if copies == 1:
        return True
    elif copies == 0:
        assert False, "We don't receive multicast packet with or without IP_MULTICAST_LOOP"
    else:
        assert False, "Unexpected IP_MULTICAST_LOOP behavior"
    return False  # To make Pylint happy

def _copies_received(ipv6, loopback_enabled):
    if ipv6:
        (txsock, rxsock) = _create_ipv6_sockets(loopback_enabled)
    else:
        (txsock, rxsock) = _create_ipv4_sockets(loopback_enabled)
    # Allow some time for the IGMP join (group membership) messages to be sent and processed
    time.sleep(1.0)
    # Send a single test multicast message
    tx_message = b"test"
    txsock.send(tx_message)
    # Count how many times that one message is received. If loopback is disabled, it could be 0
    # times or 1 time. If loopback is enabled, it could be 0, 1, or 2 times.
    count = 0
    rx_message = _receive_packet_with_timeout(rxsock, 0.1)
    if rx_message:
        assert rx_message == tx_message
        count += 1
    if loopback_enabled:
        rx_message = _receive_packet_with_timeout(rxsock, 0.1)
        if rx_message:
            assert rx_message == tx_message
            count += 1
    # Close sockets and return count
    rxsock.close()
    txsock.close()
    return count

def _create_ipv4_sockets(loopback_enabled):
    # Open a multicast send socket, with IP_MULTICAST_LOOP enabled or disabled as requested.
    mcast_address = "224.0.1.195"
    port = 49501
    group = (mcast_address, port)
    txsock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    txsock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    if loopback_enabled:
        txsock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_LOOP, 1)
    else:
        txsock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_LOOP, 0)
    txsock.connect(group)
    # Open a multicast receive socket and join the group
    rxsock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    req = struct.pack("=4sl", socket.inet_aton(mcast_address), socket.INADDR_ANY)
    rxsock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, req)
    rxsock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    rxsock.bind(group)
    return (txsock, rxsock)

def _create_ipv6_sockets(loopback_enabled):
    # Open a multicast send socket, with IP_MULTICAST_LOOP enabled or disabled as requested.
    intf_name = find_ethernet_interface()
    intf_index = socket.if_nametoindex(intf_name)
    mcast_address = "ff02::abcd:99"
    port = 30000
    group = (mcast_address, port)
    txsock = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    txsock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    txsock.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_MULTICAST_IF, intf_index)
    if loopback_enabled:
        txsock.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_MULTICAST_LOOP, 1)
    else:
        txsock.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_MULTICAST_LOOP, 0)
    txsock.connect(group)
    # Open a multicast receive socket and join the group
    rxsock = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    req = struct.pack("=16si", socket.inet_pton(socket.AF_INET6, mcast_address), intf_index)
    if platform.system() == "Darwin":
        rxsock.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_JOIN_GROUP, req)
    else:
        rxsock.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_ADD_MEMBERSHIP, req)
    rxsock.bind(("::", port))
    return (txsock, rxsock)

def _receive_packet_with_timeout(rxsock, timeout):
    rxsock.setblocking(0)
    rx_ready, _, _ = select.select([rxsock], [], [], timeout)
    if rx_ready:
        rx_message = rxsock.recv(4096)
        return rx_message
    else:
        return None

def find_ethernet_interface():
    for intf_name in netifaces.interfaces():
        addresses = netifaces.ifaddresses(intf_name)
        if netifaces.AF_INET in addresses:
            ipv4_addresses = addresses[netifaces.AF_INET]
            for ipv4_address in ipv4_addresses:
                if 'broadcast' in ipv4_address:
                    return intf_name
    assert False, "Cannot find ethernet interface to perform loopback test"
    return None

if __name__ == "__main__":
    print("Testing on interface:", find_ethernet_interface())
    print("IPv4 loopback needed:", ipv4_loopback_needed())
    print("IPv6 loopback needed:", ipv6_loopback_needed())
