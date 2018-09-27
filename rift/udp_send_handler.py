import socket
import scheduler

class UdpSendHandler:

    def __init__(self, interface_name, remote_address, port, local_address,
                 multicast_loopback=None):
        self.interface_name = interface_name
        self.remote_address = remote_address
        self.port = port
        self.local_address = local_address
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.multicast_loopback = multicast_loopback
        if multicast_loopback is True:
            self.sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_LOOP, 1)
        elif multicast_loopback is False:
            self.sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_LOOP, 0)
        if self.local_address:
            self.sock.setsockopt(socket.SOL_IP, socket.IP_MULTICAST_IF,
                                 socket.inet_aton(self.local_address))
        self.sock.connect((self.remote_address, self.port))
        scheduler.SCHEDULER.register_handler(self, False, False)

    def close(self):
        scheduler.SCHEDULER.unregister_handler(self)
        self.sock.close()

    def tx_fd(self):
        return self.sock.fileno()

    def send_message(self, message):
        self.sock.send(message)

    def source_address_and_port(self):
        return self.sock.getsockname()
