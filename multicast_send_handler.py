import socket
import struct
import utils
from scheduler import scheduler

class MulticastSendHandler:

    def __init__(self, interface_name, multicast_ipv4_address, port):
        self._multicast_ipv4_address = multicast_ipv4_address
        self._port = port
        self._interface_ipv4_address = utils.interface_ipv4_address(interface_name)
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        # TODO: should not be needed since TTL is 1 by default (check this before deleting it for real)
        # self._sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 1)   
        self._sock.setsockopt(socket.SOL_IP, socket.IP_MULTICAST_IF, socket.inet_aton(self._interface_ipv4_address))
        multicast_group = (self._multicast_ipv4_address, self._port)
        self._sock.connect(multicast_group)
        scheduler.register_handler(self, False, False)

    def close(self):
        scheduler.unregister_handler(self)
        self._sock.close()

    def socket(self):
        return self._sock

    def send_message(self, message):
        self._sock.send(message)

    def source_address_and_port(self):
        return self._sock.getsockname()

