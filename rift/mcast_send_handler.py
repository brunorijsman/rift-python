import socket
import scheduler

class McastSendHandler:

    def __init__(self, interface_name, mcast_ipv4_address, port, interface_ipv4_address,
                 multicast_loopback):
        self._interface_name = interface_name
        self._mcast_ipv4_address = mcast_ipv4_address
        self._port = port
        self._interface_ipv4_address = interface_ipv4_address
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self._multicast_loopback = multicast_loopback
        if multicast_loopback:
            self._sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_LOOP, 1)
        else:
            self._sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_LOOP, 0)
        # TODO: should not be needed since TTL is 1 by default (check this before deleting comment)
        # self._sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 1)
        if self._interface_ipv4_address:
            self._sock.setsockopt(socket.SOL_IP, socket.IP_MULTICAST_IF,
                                  socket.inet_aton(self._interface_ipv4_address))
        mcast_group = (self._mcast_ipv4_address, self._port)
        self._sock.connect(mcast_group)
        scheduler.SCHEDULER.register_handler(self, False, False)

    def close(self):
        scheduler.SCHEDULER.unregister_handler(self)
        self._sock.close()

    def tx_fd(self):
        return self._sock.fileno()

    def send_message(self, message):
        self._sock.send(message)

    def source_address_and_port(self):
        return self._sock.getsockname()
