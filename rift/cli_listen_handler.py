import socket
import scheduler
from cli_session_handler import CliSessionHandler

# TODO: Add IPv6 support

class CliListenHandler:

    def __init__(self, command_tree, command_handler, prompt, port=0):
        self._command_tree = command_tree
        self._command_handler = command_handler
        self._prompt = prompt
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # TODO: SO_REUSEPORT is not supported on all OSs
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        self._sock.bind(('', port))
        self._sock.listen()
        self._port = self._sock.getsockname()[1]
        scheduler.SCHEDULER.register_handler(self, True, False)
        print("Command Line Interface (CLI) available on port {}".format(self._port))

    def close(self):
        scheduler.SCHEDULER.unregister_handler(self)
        self._sock.close()

    def rx_fd(self):
        return self._sock.fileno()

    def tx_fd(self):
        return self._sock.fileno()

    def ready_to_read(self):
        (session_sock, _session_remote_address) = self._sock.accept()
        CliSessionHandler(
            sock=session_sock,
            rx_fd=session_sock.fileno(),
            tx_fd=session_sock.fileno(),
            parse_tree=self._command_tree,
            command_handler=self._command_handler,
            prompt=self._prompt)
