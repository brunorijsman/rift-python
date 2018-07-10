import logging
from node import Node
from interface import Interface
from scheduler import scheduler

# TODO: Bind the send socket to a particular interface. We already did this for receive sockets
#       in multicast_receive_handler but not yet for send sockets.

class Rift:

    def __init__(self):
        logging.basicConfig(
            filename = 'rift.log', 
            format = '%(asctime)s:%(levelname)s:%(name)s:%(message)s', 
            level = logging.DEBUG)
        self._node = Node()
        interface_name = 'en0'
        self._interface = Interface(interface_name, self._node)
        self._node.register_interface(interface_name, self._interface)

    def run(self):
        scheduler.run() 

if __name__ == "__main__":
    rift = Rift()
    rift.run()