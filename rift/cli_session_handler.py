import os
import sys

import scheduler

# TODO: Implement SSH server
# TODO: Add context sensitive help, immediately when ? is pressed
# TODO: Add tab and space completion
# TODO: Add control right/left arrow for end/start of line (VT100 escape sequence)

READ_CHUNK_SIZE = 1024

MAX_HISTORY = 100

CONTROL_A = 1
CONTROL_E = 5
BELL = 7
LINE_FEED = 10
CARRIAGE_RETURN = 13
ESCAPE = 27
SPACE = 32
DELETE = 127

TELNET_NULL = 0
TELNET_OPTION_ECHO = 1
TELNET_OPTION_SUPPRESS_GO_AHEAD = 3
TELNET_WILL = 251
TELNET_WONT = 252
TELNET_DO = 253
TELNET_DONT = 254
TELNET_INTERPRET_AS_COMMAND = 255

VT100_LEFT_SQUARE_BRACKET = 91
VT100_CURSOR_UP = 65
VT100_CURSOR_DOWN = 66
VT100_CURSOR_RIGHT = 67
VT100_CURSOR_LEFT = 68
VT100_ERASE_TO_END_OF_LINE = 75

class CliSessionHandler:

    def __init__(self, sock, rx_fd, tx_fd, parse_tree, command_handler, log, node):
        # Socket is None for interactive sessions that use stdin and stdout. For network connections
        # it is something else than None; we never use the socket, but we need to store it anyway
        # to prevent the socket from being garbage collected causing the connection to be closed.
        self._sock = sock
        self._rx_fd = rx_fd
        self._tx_fd = tx_fd
        self._parse_tree = parse_tree
        self._command_handler = command_handler
        self._log = log
        self._current_node = node
        self._input_bytes_buffer = bytes()
        self._command_buffer = bytes()
        self._command_buffer_pos = 0
        self._command_history = []
        self._command_history_pos = None
        self._next_commands = []
        self.info("Open CLI session")
        self._telnet = (sock is not None)
        self._telnet_suppress_go_ahead = False
        self._telnet_echo = False
        if self._telnet:
            self.send_will_suppress_go_ahead()
            self.send_will_echo()
        scheduler.SCHEDULER.register_handler(self, True, False)
        self.print_prompt()

    def peername(self):
        if self._sock:
            return self._sock.getpeername()[0] + ":" + str(self._sock.getpeername()[1])
        else:
            return "local"

    def info(self, msg):
        self._log.info("[%s] %s: %s", self.current_node_name(), self.peername(), msg)

    def close(self):
        self.info("Close CLI session")
        scheduler.SCHEDULER.unregister_handler(self)
        os.close(self._rx_fd)
        if self._tx_fd != self._rx_fd:
            os.close(self._tx_fd)
        self._rx_fd = None
        self._tx_fd = None
        # If this was the interactive (stdin/stdout) CLI session, exit the RIFT engine as well
        if self._sock is None:
            sys.exit(0)

    def rx_fd(self):
        return self._rx_fd

    def tx_fd(self):
        return self._tx_fd

    def print(self, message, add_newline=True):
        if self._tx_fd is None:
            return
        if add_newline:
            message += '\n'
        if self._telnet_echo:
            fixed_message = message.replace('\n', '\r\n')
        else:
            fixed_message = message
        os.write(self._tx_fd, fixed_message.encode('utf-8'))

    def print_help(self, parse_subtree):
        self.print_help_recursion("", parse_subtree)

    @staticmethod
    def token_key(item):
        token = item[0]
        if (len(token) > 1) and (token[0] == "$"):
            return token[1:]
        else:
            return token

    # TODO: Mention parameter name for "show interface help"
    # TODO: Handle "show interfaces help" in a better way
    def print_help_recursion(self, command_str, parse_subtree):
        if callable(parse_subtree):
            self.print(command_str)
        else:
            for match_str, new_parse_subtree in sorted(parse_subtree.items(), key=self.token_key):
                if match_str == '':
                    new_command_str = command_str
                elif match_str[0] == '$':
                    new_command_str = command_str + "{0} <{0}> ".format(match_str[1:])
                else:
                    new_command_str = command_str + match_str + " "
                self.print_help_recursion(new_command_str, new_parse_subtree)

    def parse_command(self, command):
        tokens = command.split()
        if tokens:
            self.parse_tokens(tokens, self._parse_tree, {})

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

    def current_node_name(self):
        if self._current_node:
            return self._current_node.name
        else:
            return ""

    def print_prompt(self):
        self.print(self.current_node_name() + "> ", False)

    def refresh_command_from_pos(self):
        self.send_erase_to_end_of_line()
        positions = len(self._command_buffer[self._command_buffer_pos:])
        self.send_bytes(self._command_buffer[self._command_buffer_pos:])
        self.send_cursor_left(positions)

    def replace_command(self, new_command):
        self.process_cursor_to_start_of_line()
        self.send_erase_to_end_of_line()
        self._command_buffer = new_command
        self.send_bytes(self._command_buffer)
        self._command_buffer_pos = len(self._command_buffer)

    def send_will_suppress_go_ahead(self):
        msg = bytes([TELNET_INTERPRET_AS_COMMAND, TELNET_WILL, TELNET_OPTION_SUPPRESS_GO_AHEAD])
        self.send_bytes(msg)

    def send_will_echo(self):
        msg = bytes([TELNET_INTERPRET_AS_COMMAND, TELNET_WILL, TELNET_OPTION_ECHO])
        self.send_bytes(msg)

    def send_cursor_left(self, positions=1):
        if positions == 0:
            return
        msg = (bytes([ESCAPE, VT100_LEFT_SQUARE_BRACKET]) +
               str(positions).encode() +
               bytes([VT100_CURSOR_LEFT]))
        self.send_bytes(msg)

    def send_cursor_right(self, positions=1):
        if positions == 0:
            return
        msg = (bytes([ESCAPE, VT100_LEFT_SQUARE_BRACKET]) +
               str(positions).encode() +
               bytes([VT100_CURSOR_RIGHT]))
        self.send_bytes(msg)

    def send_bell(self):
        self.send_byte(BELL)

    def send_erase_to_end_of_line(self):
        msg = bytes([ESCAPE, VT100_LEFT_SQUARE_BRACKET, VT100_ERASE_TO_END_OF_LINE])
        self.send_bytes(msg)

    def send_byte(self, byte):
        self.send_bytes(bytes([byte]))

    def send_bytes(self, msg):
        if self._tx_fd is None:
            return
        os.write(self._tx_fd, msg)

    def echo_byte(self, byte):
        if self._telnet_echo:
            self.send_bytes(bytes([byte]))

    def echo_bytes(self, byte_list):
        if self._telnet_echo:
            self.send_bytes(bytes(byte_list))

    def set_current_node(self, node):
        self._current_node = node

    @property
    def current_node(self):
        return self._current_node

    def ready_to_read(self):
        new_input_bytes = os.read(self._rx_fd, READ_CHUNK_SIZE)
        if not new_input_bytes:
            # Remote side closed session
            self.close()
            return
        self._input_bytes_buffer += new_input_bytes
        self.parse_input_bytes()

    def parse_input_bytes(self):
        need_more_input = False
        while not need_more_input and self._input_bytes_buffer:
            byte = self._input_bytes_buffer[0]
            self._input_bytes_buffer = self._input_bytes_buffer[1:]
            if byte == TELNET_NULL:
                pass
            elif byte == LINE_FEED:
                need_more_input = self.process_line_feed()
            elif byte == CARRIAGE_RETURN:
                need_more_input = self.process_carriage_return()
            elif byte == CONTROL_A:
                need_more_input = self.process_cursor_to_start_of_line()
            elif byte == CONTROL_E:
                need_more_input = self.process_cursor_to_end_of_line()
            elif byte == TELNET_INTERPRET_AS_COMMAND:
                need_more_input = self.process_telnet_command()
            elif byte == DELETE:
                need_more_input = self.process_delete()
            elif byte == ESCAPE:
                need_more_input = self.process_escape()
            else:
                need_more_input = self.process_other(byte)
            if need_more_input:
                # Byte was not consumed, put it back
                self._input_bytes_buffer = bytes([byte]) + self._input_bytes_buffer

    def process_line_feed(self):
        return self.process_end_of_line()

    def process_carriage_return(self):
        if not self._input_bytes_buffer:
            # We need to read more bytes to complete the CR+LF pair
            return True
        line_feed = self._input_bytes_buffer[0]
        if line_feed == LINE_FEED:
            self._input_bytes_buffer = self._input_bytes_buffer[1:]
        return self.process_end_of_line()

    def process_end_of_line(self):
        self.echo_bytes([CARRIAGE_RETURN, LINE_FEED])
        try:
            command = self._command_buffer.decode("utf-8", "ignore")
        except UnicodeDecodeError:
            self.print("UTF-8 decode of command failed")
        else:
            self.info("Execute CLI command \"{}\"".format(command))
            self.parse_command(command)
            self.print_prompt()
        if self._command_buffer:
            self._command_history.append(self._command_buffer)
            while len(self._command_history) > MAX_HISTORY:
                self._command_history = self._command_history[1:]
            self._command_history_pos = None
        self._command_buffer = bytes()
        self._command_buffer_pos = 0
        return False

    def process_telnet_command(self):
        if len(self._input_bytes_buffer) < 2:
            # We need to receive more bytes before we can parse the Telnet command
            return True
        telnet_command = self._input_bytes_buffer[0]
        telnet_option = self._input_bytes_buffer[1]
        self._input_bytes_buffer = self._input_bytes_buffer[2:]
        if telnet_command == TELNET_DO:
            if telnet_option == TELNET_OPTION_SUPPRESS_GO_AHEAD:
                self._telnet_suppress_go_ahead = True
            if telnet_option == TELNET_OPTION_ECHO:
                self._telnet_echo = True
        elif telnet_command == TELNET_DONT:
            if telnet_option == TELNET_OPTION_SUPPRESS_GO_AHEAD:
                self._telnet_suppress_go_ahead = False
            if telnet_option == TELNET_OPTION_ECHO:
                self._telnet_echo = False
        return False

    def process_delete(self):
        pos = self._command_buffer_pos
        if pos > 0:
            before = self._command_buffer[0:pos-1]
            after = self._command_buffer[pos:]
            self._command_buffer = before + after
            self._command_buffer_pos -= 1
            self.send_cursor_left()
            self.refresh_command_from_pos()
        else:
            self.send_bell()
        return False

    def process_escape(self):
        # We only support VT100 escape sequences of the form ESCAPE + [ + letter
        if len(self._input_bytes_buffer) < 2:
            # Need at least two characters after the ESCAPE
            return True
        vt100_char_1 = self._input_bytes_buffer[0]
        vt100_char_2 = self._input_bytes_buffer[1]
        self._input_bytes_buffer = self._input_bytes_buffer[2:]
        if vt100_char_1 != VT100_LEFT_SQUARE_BRACKET:
            return False
        if vt100_char_2 == VT100_CURSOR_LEFT:
            self.process_cursor_left()
        elif vt100_char_2 == VT100_CURSOR_RIGHT:
            self.process_cursor_right()
        elif vt100_char_2 == VT100_CURSOR_UP:
            self.process_prev_history()
        elif vt100_char_2 == VT100_CURSOR_DOWN:
            self.process_next_history()
        return False

    def process_cursor_left(self):
        if self._command_buffer_pos > 0:
            self._command_buffer_pos -= 1
            self.send_cursor_left()
        else:
            self.send_bell()

    def process_cursor_right(self):
        if self._command_buffer_pos < len(self._command_buffer):
            self._command_buffer_pos += 1
            self.send_cursor_right()
        else:
            self.send_bell()

    def process_cursor_to_start_of_line(self):
        if self._command_buffer_pos > 0:
            positions = self._command_buffer_pos
            self.send_cursor_left(positions)
            self._command_buffer_pos = 0
        return False

    def process_cursor_to_end_of_line(self):
        if self._command_buffer_pos < len(self._command_buffer):
            positions = len(self._command_buffer) - self._command_buffer_pos
            self.send_cursor_right(positions)
            self._command_buffer_pos = len(self._command_buffer)
        return False

    def process_prev_history(self):
        if self._command_history == []:
            self.send_bell()
            return
        if self._command_history_pos is None:
            self._command_history_pos = len(self._command_history)
            if self._command_buffer:
                self._command_history.append(self._command_buffer)
        if self._command_history_pos == 0:
            self.send_bell()
            return
        self._command_history_pos -= 1
        self.replace_command(self._command_history[self._command_history_pos])

    def process_next_history(self):
        if self._command_history_pos is None:
            self.send_bell()
            return
        self._command_history_pos += 1
        if self._command_history_pos >= len(self._command_history):
            self._command_history_pos = None
            self.replace_command(bytes())
        else:
            self.replace_command(self._command_history[self._command_history_pos])

    def process_other(self, byte):
        if self._command_buffer_pos >= len(self._command_buffer):
            self.echo_byte(byte)
            self._command_buffer += bytes([byte])
            self._command_buffer_pos += 1
        else:
            pos = self._command_buffer_pos
            before = self._command_buffer[0:pos]
            after = self._command_buffer[pos:]
            self._command_buffer = before + bytes([byte]) + after
            self.refresh_command_from_pos()
            self._command_buffer_pos += 1
            self.send_cursor_right()
        return False
