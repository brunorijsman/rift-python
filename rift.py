from node import Node
from interface import Interface
from scheduler import scheduler

# TODO: Support multiple (configurable) interfaces per RIFT instance

class Rift:

    def __init__(self):
        self._node = Node()
        self._interface = Interface('en0', self._node)

    def run(self):
        scheduler.run()

if __name__ == "__main__":
    rift = Rift()
    rift.run()