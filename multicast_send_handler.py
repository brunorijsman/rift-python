import socket
import struct
from socket_scheduler import socket_scheduler

class MulticastSendHandler:

    def __init__(self, multicast_address, port):
        self._multicast_address = multicast_address
        self._port = port
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        ttl = struct.pack('b', 1)
        self._sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl)
        loop = struct.pack('b', 0)
        self._sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_LOOP, loop)
        socket_scheduler.register_handler(self, False, False)

    def __del__(self):
        socket_scheduler.unregister_handler(self)
        self._sock.close()

    def socket(self):
        return self._sock

    def send_message(self, message):
        multicast_group = (self._multicast_address, self._port)
        self._sock.sendto(message.encode(), multicast_group)
