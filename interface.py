import os
from multicast_send_handler import MulticastSendHandler
from multicast_receive_handler import MulticastReceiveHandler
from timer import Timer

# TODO: make it possible to enable or disable RIFT on a per interface basis
# TODO: send and receive LIE message on a per interface basis
# TODO: Change port to 911 (need root permissions for that)
# TODO: Change multicast address to 224.0.0.120 (
# TODO: - But for some reason that doesn't work on my mac...
# TODO: - 224.0.0.120 is local network, 224.0.1.120 is inter network block... 
# TODO: - Maybe I need to turn loopback on?
# TODO: Bind the socket to the interface (send and receive packets on that specific interface)

class Interface:

    def __init__(self, name, config):
        self.name = name
        self.config = config
        self._multicast_send_handler = MulticastSendHandler(
            config.lie_ipv4_multicast_address, 
            config.lie_destination_port)
        self._multicast_receive_handler = MulticastReceiveHandler(
            config.lie_ipv4_multicast_address, 
            config.lie_destination_port,
            self.receive_multicast_message)
        self._send_timer = Timer(
            config.lie_send_interval_secs,
            self.send_lie_message)

    def receive_multicast_message(self, message):
        # TODO: decode and process the LIE message
        print("Receive {}".format(message))

    def send_lie_message(self):
        # TODO: send a real LIE message instead of this place holder message
        message = 'Message sent by PID ' + str(os.getpid())
        self._multicast_send_handler.send_message(message)
        print("Sent {}".format(message))
