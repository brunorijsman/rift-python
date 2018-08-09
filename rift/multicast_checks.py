import select
import socket
import struct
import time

# Check whether this IP_MULTICAST_LOOP socket option is needed in this environment (it depends
# on the behavior of the router to which this host is connected)
# See http://bit.ly/multicast-duplication for more details
#
def loopback_needed():
    # If we receive a single copy when loopback is disabled, then we need to disable loopback
    if copies_received(False) == 1:
        return False
    # We receive zero copies with loopback disabled. Make sure we do receive a single copy with
    # loopback enabled.
    copies = copies_received(True)
    if copies == 1:
        return True
    elif copies == 0:
        assert False, "We don't receive multicast packet with or without IP_MULTICAST_LOOP"
    else:
        assert False, "Unexpected IP_MULTICAST_LOOP behavior"
    return False  # To make Pylint happy

def copies_received(loopback_enabled):
    # Open a multicast send socket, with IP_MULTICAST_LOOP enabled or disabled as requested.
    mcast_ipv4_address = "224.0.1.1"
    port = 20001
    group = (mcast_ipv4_address, port)
    txsock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    if loopback_enabled:
        txsock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_LOOP, 1)
    else:
        txsock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_LOOP, 0)
    txsock.connect(group)
    # Open a multicast receive socket and join the group
    rxsock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    req = struct.pack("=4sl", socket.inet_aton(mcast_ipv4_address), socket.INADDR_ANY)
    rxsock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, req)
    rxsock.bind(group)
    # Allow some time for the IGMP join (group membership) messages to be sent and processed
    time.sleep(1.0)
    # Send a single test multicast message
    tx_message = b"test"
    txsock.send(tx_message)
    # Count how many times that one message is received. If loopback is disabled, it could be 0
    # times or 1 time. If loopback is enabled, it could be 0, 1, or 2 times.
    count = 0
    rx_message = receive_packet_with_timeout(rxsock, 0.1)
    if rx_message:
        assert rx_message == tx_message
        count += 1
    if loopback_enabled:
        rx_message = receive_packet_with_timeout(rxsock, 0.1)
        if rx_message:
            assert rx_message == tx_message
            count += 1
    # Close sockets and return count
    rxsock.close()
    txsock.close()
    return count

def receive_packet_with_timeout(rxsock, timeout):
    rxsock.setblocking(0)
    rx_ready, _, _ = select.select([rxsock], [], [], timeout)
    if rx_ready:
        rx_message = rxsock.recv(4096)
        return rx_message
    else:
        return None
