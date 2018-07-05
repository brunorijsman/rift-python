from node import Node
from interface import Interface
from socket_scheduler import socket_scheduler

# TODO: Support multiple (configurable) interfaces per RIFT instance

class Rift:

    def __init__(self):
        self._node = Node()
        self._interface = Interface('en0', self._node)

    def run(self):
        socket_scheduler.run()

if __name__ == "__main__":
    rift = Rift()
    rift.run()