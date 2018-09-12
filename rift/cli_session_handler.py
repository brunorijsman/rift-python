import os
import sys
import string
import sortedcontainers

import scheduler
import constants

# TODO: Make cursor up and down keys work... (implement a real Telnet/SSH server)

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
        self.info("Open CLI session")
        self._str = ""
        self._command_buffer = ["" for i in range(constants.HISTORY)]
        self._command = ""
        self._position = 0
        self._linemode = True
        self._end_line = "\n"

        scheduler.SCHEDULER.register_handler(self, True, False)
        self.send_prompt()

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
        # If this was the interactive (stdin/stdout) CLI session, exit the RIFT engine as well
        if self._sock is None:
            sys.exit(0)

    def rx_fd(self):
        return self._rx_fd

    def tx_fd(self):
        return self._tx_fd

    def print(self, message, add_newline=True):
        if add_newline:
            message += '\n'
        os.write(self._tx_fd, message.encode('utf-8'))

    def print_r(self, message, add_newline=True):
        if not self._linemode:
            message += '\r'
        self.print(message, add_newline)

    def print_help(self, parse_subtree):
        self.print_help_recursion("", parse_subtree)

    # TODO: Mention parameter name for "show interface help"
    # TODO: Handle "show interfaces help" in a better way
    def print_help_recursion(self, command_str, parse_subtree):
        if callable(parse_subtree):
            self.print_r(command_str)
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
                self.print_r("Missing input, possible completions:")
                self.print_help(parse_subtree)
                return
        else:
            # Parse the next token
            (token, tokens) = self.consume_token(tokens)
            if (token is not None) and callable(parse_subtree):
                # We have more tokens, but we have reached a leaf of the parse tree. Report error.
                self.print_r("Unexpected extra input: {}".format(token))
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
                    self.print_r("Missing value for parameter {}". \
                                 format(parameter_name))
                    return
                parameters[parameter_name] = token
            else:
                # Token is neither a keyword nor a parameter. Generate an error.
                self.print_r("Unrecognized input {}, expected:".format(token))
                self.print_help(parse_subtree)
                return
            self.parse_tokens(tokens, parse_subtree, parameters)

    def current_node_name(self):
        if self._current_node:
            return self._current_node.name
        else:
            return ""

    def send_prompt(self):
        if self._linemode:
            self.print(self.current_node_name() + "> ", False)
        else:
            self.print(self.current_node_name() + "] ", False)


    def send_raw(self, cmd):
        pat = bytes.fromhex(cmd)
        os.write(self._tx_fd, pat)

    def history_buff(self, char):
        if char == constants.ESC_UP:
            if self._command != "":
                self._command_buffer.append(self._command)
            self._command = self._command_buffer.pop(0)
            if len(self._command_buffer) < constants.HISTORY:
                self._command_buffer.insert(int(constants.HISTORY/2), "")
                # command_buffer always has HISTORY elements
        else:
            if self._command != "":
                self._command_buffer.insert(0, self._command)
            self._command = self._command_buffer.pop()
            if len(self._command_buffer) < constants.HISTORY:
                self._command_buffer.insert(int(constants.HISTORY/2), "")
                # command_buffer always has HISTORY elements

    # This handles arrows, delete and backspace but occasionally
    # a character can follow a control sequence.This case is not handled.   I suppose
    # the same can happen a character then a control sequence but you can fix
    # extraneous characters by editing.
    def handle_esc(self, chars):
        if chars[1] == constants.LEFT_SQB:  # "[" but cant use character
            # Up arrow & down arrow
            if chars[2] == constants.ESC_UP or chars[2] == constants.ESC_DN:
                self.print('\r', False)
                self.print_r((len(self._command) + 10) * " ", False)
                self.history_buff(chars[2])
                self.print(self.current_node_name() + "] " + self._command, False)
                self._position = len(self._command)
            elif chars[2] == constants.ESC_RT:
                if self._command and self._position < len(self._command):
                    self._position += 1
                    # Echo back RT arrow but chars might have extraneous chars
                    pat = bytes.fromhex(constants.RIGHT_ARROW)
                    self._sock.send(pat)
            elif chars[2] == constants.ESC_LT:
                if self._position > 0:
                    self._position -= 1
                    pat = bytes.fromhex(constants.LEFT_ARROW)
                    self._sock.send(pat)
            # Delete is a sequence of 4 chars ESC [ 3 ~
            elif chars[2] == constants.DEL_SEQ_3:
                if chars[3] == constants.DEL_SEQ_TILDE:
                    if self._command  and self._position < len(self._command):
                        if len(self._command) > self._position:
                            self.print_r(self._command[(self._position + 1):] + " ", False)
                            self.print(self.current_node_name() + "] " + \
                                       self._command[:self._position], False)
                            self._command = self._command[:self._position] + \
                                            self._command[(self._position + 1):]
                        else:
                            self.print('\r' +  self.current_node_name() + "] " + \
                                        self._command[:self._position], False)
                            self._command = self._command[:self._position]
        # F1 toggles line mode.
        elif chars[1] == constants.CAP_O:
            if chars[2] == constants.CAP_P:  # F1 Key
                if self._linemode:
                    # Magic to Character mode"
                    # Literally tell telnet "IAC DO LINEMODE SUB Negotiation Linemode IAC WILL ECHO"
                    self.send_raw('FFFD22FFFA220100FFF0FFFB01')
                    self._linemode = False
                    self._end_line = "\r\n"
                    # It appears telnet does something funky and will not accept chars
                    # until the user hits return when changing to character mode
                else:
                    # SINCE FFFD22 has been sent this is enough
                    self.send_raw('FFFA220101FFF0FFFC01')
                    self._linemode = True
                    self._end_line = "\n"
                self._position = 0 # Purge the command if any
                self._command = ""
                self.print_r("")
                self.send_prompt()

    def handle_backspace(self):
        if self._position > 0:
            pat = bytes.fromhex(constants.BKSP_OVERWRITE) # Backspace, space and backspace
            self._sock.send(pat)
            self._position -= 1
            # Now pull any character that are to the right
            if len(self._command) > (self._position + 1):
                self.print_r(self._command[(self._position + 1):] + " ", False)
                self.print(self.current_node_name() + "] " + \
                           self._command[:self._position], False)
                self._command = self._command[:self._position] + \
                                    self._command[(self._position + 1):]
            else:
                self.print('\r' +  self.current_node_name() + "] " + \
                           self._command[:self._position], False)
                self._command = self._command[:self._position]

    def build_n_display_command(self, char):
        if not self._command:
            self._command = char
        else:
            # This code handles inserts as well as characters at the end
            self._command = self._command[:self._position] + \
                                          char + \
                                          self._command[self._position:]
            # This code prints characters after then backs up to the insert position
            if self._command[self._position+1:]:
                self.print(self._command[self._position+1:], False)
                # backspace left arrow works too but is a 3 byte sequence
                pat = bytes.fromhex('08')
                for _ in range(len(self._command[self._position+1:])):
                    self._sock.send(pat)

    # Simple history buffer
    def update_history(self):
        if self._command != "":
            # Delete from middle and push on front this allows up and down arrows
            # for recent commands but the history is half the size
            self._command_buffer.pop(int(constants.HISTORY/2))
            self._command_buffer.insert(0, self._command)
            self._str = self._command + '\n'
        self._position = 0 # Done Editing
        self._command = ""

    def ready_to_read(self):

        chars = os.read(self._rx_fd, 1024)
        if not chars:
            # Remote side closed session
            scheduler.SCHEDULER.unregister_handler(self)
            os.close(self._rx_fd)
            if self._tx_fd != self._rx_fd:
                os.close(self._tx_fd)
            self._rx_fd = None
            self._tx_fd = None
            return
        #initially we are in 8 - bit mode.
        if chars[0] == constants.COMMAND:
            #command sequence ignored although this tells us remote capabilities.
            return
        elif chars[0] == constants.ESC: # ESC
            self.handle_esc(chars)
            return
        # Backspace is DEL in my setup
        elif chars[0] == constants.BS or chars[0] == constants.DEL:
            self.handle_backspace()
            return
        # Below here is "normal text" 7-bit Ascii
        try:
            temp_str = chars.decode("utf-8", "ignore")  # type: string
        except UnicodeDecodeError:
            # Could not parse UTF-8, ignore input
            return
        last_char = False
        if not self._linemode:
            #Building character by character
            for char in temp_str:
                if char in string.printable:
                    if char == '\r': #Everything after \r ignored.
                        last_char = True
                        if self._command != "":
                            self._str = self._command
                        else:
                            self._str = "\r\n" #mimic empty for help
                        break
                    self.print(char, False) # Print current char
                    self.build_n_display_command(char)
                    self._position += 1
        else: # Linemode = True
            self._str = temp_str # Whole Command(s) in _str
        # Only execute the follwing on a complete command
        if self._linemode or last_char:
            if last_char:
                self.print_r("")
                self.update_history()
            # Process Commands
            while '\n' in self._str:
                split = self._str.split('\n', 1)
                command = split[0]
                self._str = split[1]
                if command != '':
                    self.info("Execute CLI command \"{}\"".format(command))
                    self.parse_command(command)
                self.send_prompt()

    def set_current_node(self, node):
        self._current_node = node

    @property
    def current_node(self):
        return self._current_node

    def current_end_line(self):
        return self._end_line
