import socket
from scheduler import scheduler
from cli_session_handler import CliSessionHandler

# TODO: Add IPv6 support

class CliListenHandler:

    def __init__(self, command_tree, prompt, port = 0):
        self._command_tree = command_tree
        self._prompt = prompt
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)     # TODO: Not supported on all OSs
        self._sock.bind(('', port))
        self._sock.listen()
        self._port = self._sock.getsockname()[1]
        scheduler.register_handler(self, True, False)
        print("Command Line Interface (CLI) available on port {}".format(self._port))

    def __del__(self):
        scheduler.unregister_handler(self)
        self._sock.close()

    def socket(self):
        return self._sock

    def ready_to_read(self):
        (session_sock, session_remote_address) = self._sock.accept()
        cli_session_handler = CliSessionHandler(
            session_sock, 
            session_remote_address, 
            self._command_tree,
            self._prompt)
