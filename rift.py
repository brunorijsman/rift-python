from config import Config
from interface import Interface
from socket_scheduler import socket_scheduler

# TODO: Support multiple (configurable) interfaces per RIFT instance

class Rift:

    def __init__(self):
        self._config = Config()
        self._interface = Interface('en0', self._config)

    def run(self):
        socket_scheduler.run()

if __name__ == "__main__":
    rift = Rift()
    rift.run()