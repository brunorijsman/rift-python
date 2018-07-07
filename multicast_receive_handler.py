import socket
import struct
from scheduler import scheduler

class MulticastReceiveHandler:

    MAXIMUM_MESSAGE_SIZE = 65535

    def __init__(self, multicast_address, port, receive_function):
        self._multicast_address = multicast_address
        self._port = port
        self._receive_function = receive_function
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)     # TODO: Not supported on all OSs
        self._sock.bind((multicast_address, port))
        req = struct.pack("4sl", socket.inet_aton(multicast_address), socket.INADDR_ANY)
        self._sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, req)
        self._sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_LOOP, 1)   # TODO: Should not be needed; this is the default
        scheduler.register_handler(self, True, False)

    def __del__(self):
        scheduler.unregister_handler(self)
        self._sock.close()

    def socket(self):
        return self._sock

    def ready_to_read(self):
        message = self._sock.recv(self.MAXIMUM_MESSAGE_SIZE)
        self._receive_function(message)
