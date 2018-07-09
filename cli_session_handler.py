import socket
from scheduler import scheduler

class CliSessionHandler:

    def __init__(self, sock, remote_address, command_tree, prompt):
        self._sock = sock
        self._sock.setblocking(0)
        self._remote_address = remote_address
        self._command_tree = command_tree
        self._prompt = prompt
        self._str = ""
        scheduler.register_handler(self, True, False)
        self.send_prompt()

    def send_prompt(self):
        full_prompt = self._prompt + "> "
        self._sock.send(full_prompt.encode('utf-8'))

    def socket(self):
        return self._sock

    def execute_command(self, command, sock):
        # TODO: ### Continue from here
        print("execute command {}".format(command))

    def ready_to_read(self):
        data = self._sock.recv(1024)
        if not data:
            # Remote side closed session
            scheduler.unregister_handler(self)
            self._sock.close()
            return
        self._str += data.decode('utf-8').replace('\r', '')
        while '\n'in self._str:
            split = self._str.split('\n', 1)
            command = split[0]
            self._str = split[1]
            self.execute_command(command, self._sock)
            self.send_prompt()
