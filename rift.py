import os
from multicast_send_handler import MulticastSendHandler
from multicast_receive_handler import MulticastReceiveHandler
from timer import Timer
from socket_scheduler import socket_scheduler

# TODO: support more than one interface (introduce a RiftInterface class)
# TODO: make it possible to enable or disable RIFT on a per interface basis
# TODO: send and receive LIE message on a per interface basis

# TODO: Change port to 911 (need root permissions for that)
# TODO: Change multicast address to 224.0.0.120 (
# TODO: - But for some reason that doesn't work on my mac...
# TODO: - 224.0.0.120 is local network, 224.0.1.120 is inter network block... 
# TODO: - Maybe I need to turn loopback on?

class Rift:

    DEFAULT_LIE_IPV4_MULTICAST_ADDRESS = '224.0.1.120'    # TODO: Change to 224.0.0.120
    DEFAULT_LIE_IPV6_MULTICAST_ADDRESS = 'FF02::0078'     # TODO: Add IPv6 support
    DEFAULT_LIE_DESTINATION_PORT = 10000    # TODO: Change to 911 (needs root privs)
    DEFAULT_LIE_SEND_INTERVAL_SECS = 1.0    # TODO: What does the draft say?

    def __init__(self):
        self._lie_ipv4_multicast_address = self.DEFAULT_LIE_IPV4_MULTICAST_ADDRESS
        self._lie_ipv6_multicast_address = self.DEFAULT_LIE_IPV6_MULTICAST_ADDRESS
        self._lie_destination_port = self.DEFAULT_LIE_DESTINATION_PORT
        self._lie_send_interval_secs = self.DEFAULT_LIE_SEND_INTERVAL_SECS

    def receive_multicast_message(self, message):
        # TODO: decode and process the LIE message
        print("Receive {}".format(message))

    def send_lie_message(self):
        # TODO: send a real LIE message instead of this place holder message
        message = 'Message sent by PID ' + str(os.getpid())
        self._multicast_send_handler.send_message(message)
        print("Sent {}".format(message))

    def run(self):
        self._multicast_send_handler = MulticastSendHandler(
            self._lie_ipv4_multicast_address, 
            self._lie_destination_port)
        self._multicast_receive_handler = MulticastReceiveHandler(
            self._lie_ipv4_multicast_address, 
            self._lie_destination_port,
            self.receive_multicast_message)
        self._send_timer = Timer(
            self._lie_send_interval_secs,
            self.send_lie_message)
        socket_scheduler.run()

if __name__ == "__main__":
    rift = Rift()
    rift.run()