import ipaddress
import socket
import struct
import scheduler

class UdpReceiveHandler:

    MAXIMUM_MESSAGE_SIZE = 65535

    # TODO: Reorder parameters
    def __init__(self, remote_address, port, receive_function, local_address):
        self._local_address = local_address
        self._remote_address = remote_address
        self._port = port
        self._receive_function = receive_function
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # TODO: SO_REUSEPORT is not portable
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        self._sock.bind((remote_address, port))
        # If remote address is multicast, join the group
        if ipaddress.IPv4Address(remote_address).is_multicast:
            if self._local_address:
                req = struct.pack("=4s4s", socket.inet_aton(remote_address),
                                  socket.inet_aton(self._local_address))
            else:
                req = struct.pack("=4sl", socket.inet_aton(remote_address), socket.INADDR_ANY)
            self._sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, req)
        scheduler.SCHEDULER.register_handler(self, True, False)

    def close(self):
        scheduler.SCHEDULER.unregister_handler(self)
        self._sock.close()

    def rx_fd(self):
        return self._sock.fileno()

    def ready_to_read(self):
        message, from_address_and_port = self._sock.recvfrom(self.MAXIMUM_MESSAGE_SIZE)
        self._receive_function(message, from_address_and_port)
