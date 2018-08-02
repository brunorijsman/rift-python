import os
import sys

import sortedcontainers

import scheduler

# TODO: Make cursor up and down keys work... (implement a real Telnet/SSH server)

class CliSessionHandler:

    def __init__(self, sock, rx_fd, tx_fd, parse_tree, command_handler, prompt):
        # Socket is None for interactive sessions that use stdin and stdout. For network connections
        # it is something else than None; we never use the socket, but we need to store it anyway
        # to prevent the socket from being garbage collected causing the connection to be closed.
        self._sock = sock
        self._rx_fd = rx_fd
        self._tx_fd = tx_fd
        self._parse_tree = parse_tree
        self._command_handler = command_handler
        self._prompt = prompt
        self._str = ""
        scheduler.SCHEDULER.register_handler(self, True, False)
        self.send_prompt()

    def close(self):
        scheduler.SCHEDULER.unregister_handler(self)
        # If this was the interactive (stdin/stdout) CLI session, exit the RIFT engine as well
        if self._sock == None:
            sys.exit(0)

    def rx_fd(self):
        return self._rx_fd

    def tx_fd(self):
        return self._tx_fd

    def print(self, message, add_newline=True):
        if add_newline:
            message += '\n'
        os.write(self._tx_fd, message.encode('utf-8'))

    def print_help(self, parse_subtree):
        self.print_help_recursion("", parse_subtree)

    # TODO: Mention parameter name for "show interface help"
    # TODO: Handle "show interfaces help" in a better way
    def print_help_recursion(self, command_str, parse_subtree):
        if callable(parse_subtree):
            self.print(command_str)
        else:
            sorted_parse_subtree = sortedcontainers.SortedDict(parse_subtree)
            for match_str, new_parse_subtree in sorted_parse_subtree.items():
                if match_str == '':
                    new_command_str = command_str
                elif match_str[0] == '$':
                    new_command_str = command_str + "{0} <{0}> ".format(match_str[1:])
                else:
                    new_command_str = command_str + match_str + " "
                self.print_help_recursion(new_command_str, new_parse_subtree)

    def parse_command(self, command):
        tokens = command.split()
        return self.parse_tokens(tokens, self._parse_tree, {})

    def consume_token(self, tokens):
        if tokens:
            token = tokens[0]
            tokens = tokens[1:]
        else:
            token = None
        return (token, tokens)

    def parse_tokens(self, tokens, parse_subtree, parameters):
        if tokens == []:
            # We have consumed all tokens in the command.
            if callable(parse_subtree):
                # We have also reached a leaf in the parse tree. Call the command handler function.
                command_function = parse_subtree
                if parameters:
                    command_function(self._command_handler, self, parameters)
                else:
                    command_function(self._command_handler, self)
            elif '' in parse_subtree:
                # There is a branch in parse tree for "no more input". Follow that branch.
                new_parse_subtree = parse_subtree['']
                self.parse_tokens(tokens, new_parse_subtree, parameters)
            else:
                # There should have been more to parse. Generate an error
                self.print("Missing input, possible completions:")
                self.print_help(parse_subtree)
                return
        else:
            # Parse the next token
            (token, tokens) = self.consume_token(tokens)
            if (token is not None) and callable(parse_subtree):
                # We have more tokens, but we have reached a leaf of the parse tree. Report error.
                self.print("Unexpected extra input: {}".format(token))
                return
            if (token in ["help", "?"]):
                # Token is context-sensitive help. Show help and stop.
                self.print_help(parse_subtree)
                return
            if token in parse_subtree:
                # Token is a keyword. Keep going.
                parse_subtree = parse_subtree[token]
            elif '$' + token in parse_subtree:
                # Token is a parameter. Store parameter and keep going.
                parse_subtree = parse_subtree['$' + token]
                parameter_name = token
                (token, tokens) = self.consume_token(tokens)
                if token is None:
                    self.print("Missing value for parameter {}".format(parameter_name))
                    return
                parameters[parameter_name] = token
            else:
                # Token is neither a keyword nor a parameter. Generate an error.
                self.print("Unrecognized input {}, expected:".format(token))
                self.print_help(parse_subtree)
                return
            self.parse_tokens(tokens, parse_subtree, parameters)

    def send_prompt(self):
        self.print(self._prompt + "> ", False)

    def ready_to_read(self):
        data = os.read(self._rx_fd, 1024)
        if not data:
            # Remote side closed session
            scheduler.SCHEDULER.unregister_handler(self)
            os.close(self._rx_fd)
            if self._tx_fd != self._rx_fd:
                os.close(self._tx_fd)
            self._rx_fd = None
            self._tx_fd = None
            return
        try:
            self._str += data.decode('utf-8').replace('\r', '')
        except UnicodeDecodeError:
            # Could not parse UTF-8, ignore input
            return
        while '\n'in self._str:
            split = self._str.split('\n', 1)
            command = split[0]
            self._str = split[1]
            if command != '':
                self.parse_command(command)
            self.send_prompt()

    def set_prompt(self, prompt):
        self._prompt = prompt
