import socket
import struct
import scheduler

# TODO: We currently bind the UDP socket to a particular interface by binding the socket to the
#       IPv4 address of the interface.
#       - Also need to support IPv6
#       - What about unnumbered interfaces? Can we support those (using the address of the loopback,
#         as the source address, but only receiving packets on the specified interface)? I would
#         like to use SO_BINDTODEVICE but that is not portable (available on Linux but not MacOS X)

class McastReceiveHandler:

    MAXIMUM_MESSAGE_SIZE = 65535

    def __init__(self, _interface_name, mcast_ipv4_address, port, loopback, receive_function,
                 interface_ipv4_address):
        self._interface_ipv4_address = interface_ipv4_address
        self._mcast_ipv4_address = mcast_ipv4_address
        self._port = port
        self._receive_function = receive_function
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # TODO: SO_REUSEPORT is not supported on all OSs
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        self._sock.bind((mcast_ipv4_address, port))   # TODO: Should we bind to the mcast address?
        if self._interface_ipv4_address:
            req = struct.pack("=4s4s", socket.inet_aton(mcast_ipv4_address),
                              socket.inet_aton(self._interface_ipv4_address)) # TODO: Is this right?
        else:
            req = struct.pack("=4sl", socket.inet_aton(mcast_ipv4_address), socket.INADDR_ANY)
        self._sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, req)
        if loopback:
            self._sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_LOOP, 1)
        scheduler.SCHEDULER.register_handler(self, True, False)

    def close(self):
        scheduler.SCHEDULER.unregister_handler(self)
        self._sock.close()

    def socket(self):
        return self._sock

    def ready_to_read(self):
        message, from_address_and_port = self._sock.recvfrom(self.MAXIMUM_MESSAGE_SIZE)
        self._receive_function(message, from_address_and_port)
