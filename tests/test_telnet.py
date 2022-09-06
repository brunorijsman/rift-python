import os
import socket
import time

import pexpect
import pexpect.fdpexpect

import cli_session_handler

ONE = ord('1')

class TelnetSession:

    def __init__(self):
        rift_cmd = ("rift --log-level debug topology/one.yaml")
        cmd = "coverage run --parallel-mode {}".format(rift_cmd)
        results_file_name = "rift_expect.log"
        cli_results_file_name = "rift_telnet_expect.log"
        if "RIFT_TEST_RESULTS_DIR" in os.environ:
            path = os.environ["RIFT_TEST_RESULTS_DIR"] + "/"
            results_file_name = path + results_file_name
            cli_results_file_name = path + cli_results_file_name
        # pylint:disable=consider-using-with
        self._results_file = open(results_file_name, 'ab', encoding='utf-8')
        self._cli_results_file = open(cli_results_file_name, 'ab', encoding='utf-8')
        self._expect_session = pexpect.spawn(cmd, logfile=self._results_file)
        self._expect_session.expect("available on port ([0-9]+)", 5.0)
        self._cli_port = int(self._expect_session.match.group(1))
        self._cli_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._cli_socket.connect(("127.0.0.1", self._cli_port))
        self._cli_fd = self._cli_socket.fileno()
        self._cli_expect_session = pexpect.fdpexpect.fdspawn(self._cli_fd,
                                                             logfile=self._cli_results_file)

    def stop(self):
        # Terminate the Telnet session and stop RIFT
        self.send("stop\r")
        time.sleep(1.0)
        self._cli_socket.close()
        # Allow some time to write the .coverage file
        time.sleep(2.0)

    def log(self, msg):
        msg = "\n" + msg + "\n"
        self._cli_results_file.write(msg.encode())

    def checkpoint(self, check_name):
        self.log("***** CHECK: {} *****".format(check_name))

    def send(self, txt):
        self.log("SEND: " + txt)
        self._cli_socket.send(txt.encode())

    def expect(self, pattern):
        self.log("EXPECT: " + pattern)
        self._cli_expect_session.expect(pattern, 1.0)

    def special_to_bytes(self, special):
        tokens = special.split()
        values = []
        for token in tokens:
            if token == "iac":
                values += [cli_session_handler.TELNET_INTERPRET_AS_COMMAND]
            elif token == "will":
                values += [cli_session_handler.TELNET_WILL]
            elif token == "wont":
                values += [cli_session_handler.TELNET_WONT]
            elif token == "do":
                values += [cli_session_handler.TELNET_DO]
            elif token == "dont":
                values += [cli_session_handler.TELNET_DONT]
            elif token == "echo":
                values += [cli_session_handler.TELNET_OPTION_ECHO]
            elif token == "suppress-go-ahead":
                values += [cli_session_handler.TELNET_OPTION_SUPPRESS_GO_AHEAD]
            elif token == "up":
                values += [cli_session_handler.ESCAPE,
                           cli_session_handler.VT100_LEFT_SQUARE_BRACKET,
                           cli_session_handler.VT100_CURSOR_UP]
            elif token == "down":
                values += [cli_session_handler.ESCAPE,
                           cli_session_handler.VT100_LEFT_SQUARE_BRACKET,
                           cli_session_handler.VT100_CURSOR_DOWN]
            elif token == "left":
                values += [cli_session_handler.ESCAPE,
                           cli_session_handler.VT100_LEFT_SQUARE_BRACKET,
                           cli_session_handler.VT100_CURSOR_LEFT]
            elif token.startswith("left-"):
                positions_str = token[5:]
                values += ([cli_session_handler.ESCAPE,
                            cli_session_handler.VT100_LEFT_SQUARE_BRACKET] +
                           list(positions_str.encode()) +
                           [cli_session_handler.VT100_CURSOR_LEFT])
            elif token == "right":
                values += [cli_session_handler.ESCAPE,
                           cli_session_handler.VT100_LEFT_SQUARE_BRACKET,
                           cli_session_handler.VT100_CURSOR_RIGHT]
            elif token.startswith("right-"):
                positions_str = token[6:]
                values += ([cli_session_handler.ESCAPE,
                            cli_session_handler.VT100_LEFT_SQUARE_BRACKET] +
                           list(positions_str.encode()) +
                           [cli_session_handler.VT100_CURSOR_RIGHT])
            elif token == "bell":
                values += [cli_session_handler.BELL]
            elif token == "ctrl-a":
                values += [cli_session_handler.CONTROL_A]
            elif token == "ctrl-e":
                values += [cli_session_handler.CONTROL_E]
            elif token == "ctrl-n":
                values += [cli_session_handler.CONTROL_N]
            elif token == "ctrl-p":
                values += [cli_session_handler.CONTROL_P]
            elif token == "erase-to-eol":
                values += [cli_session_handler.ESCAPE,
                           cli_session_handler.VT100_LEFT_SQUARE_BRACKET,
                           cli_session_handler.VT100_ERASE_TO_END_OF_LINE]
            elif token == "del":
                values += [cli_session_handler.DELETE]
            elif token == "nul":
                values += [cli_session_handler.TELNET_NULL]
            else:
                assert False, "Unknown special token " + token
        return bytes(values)

    def send_special(self, special):
        self.log("SEND-SPECIAL: " + special)
        special_bytes = self.special_to_bytes(special)
        self._cli_socket.send(special_bytes)

    def expect_special(self, special):
        self.log("EXPECT-SPECIAL: " + special)
        special_bytes = self.special_to_bytes(special)
        self._cli_expect_session.expect_exact(special_bytes, 1.0)

    def wait_prompt(self):
        self.expect("node1> ")

def check_telnet_negotiation(session):
    session.checkpoint("check_telnet_negotiation")
    session.expect_special("iac will suppress-go-ahead")
    session.send_special("iac do suppress-go-ahead")
    session.expect_special("iac will echo")
    session.send_special("iac do echo")
    session.wait_prompt()

def check_help(session):
    session.checkpoint("check_help")
    session.send("help\n")
    # Check a few commands in the help output (not an exhaustive list)
    session.expect("exit")
    session.expect("set interface <interface> failure <failure>")
    session.expect("show interface <interface>")
    session.expect("show interface <interface> fsm history")
    session.expect("show tie-db")
    session.wait_prompt()

def check_enter_blank_line(session):
    session.checkpoint("check_enter_blank_line")
    session.send("\n")
    session.wait_prompt()

def check_command_no_parameters(session):
    # Test a command without any parameters: show interfaces
    session.checkpoint("check_command_no_parameters")
    session.send("show interfaces\n")
    session.expect("if1")
    session.expect("if2")
    session.wait_prompt()

def check_command_one_parameter(session):
    # Test a command with one parameters: show interface $interface
    session.checkpoint("check_command_one_parameter")
    session.send("show interface if1\n")
    session.expect("if1")
    session.wait_prompt()

def check_optional_keyword(session):
    # Test a command with optional keyword: show node [fsm history]
    session.checkpoint("check_optional_keyword")
    session.send("show node\n")
    session.expect("Node:")
    session.wait_prompt()
    session.send("show node fsm history\n")
    session.expect("Pushed Events")
    session.wait_prompt()

def check_missing_keyword(session):
    session.checkpoint("check_missing_keyword")
    session.send("show\n")
    session.expect("Missing input, possible completions")
    session.wait_prompt()

def check_unknown_keyword(session):
    session.checkpoint("check_unknown_keyword")
    session.send("show nonsense\n")
    session.expect('Unrecognized input "nonsense", expected')
    session.wait_prompt()

def check_extra_keyword(session):
    session.checkpoint("check_extra_keyword")
    session.send("show interfaces nonsense\n")
    session.expect("Unexpected extra input: nonsense")
    session.wait_prompt()

def check_missing_parameter(session):
    session.checkpoint("check_missing_parameter")
    session.send("show interface\n")
    session.expect("Missing value for parameter <interface>")
    session.wait_prompt()

def check_partial_keyword(session):
    session.checkpoint("check_partial_keyword")
    session.send("sh ro\n")
    session.expect("IPv4 Routes:")
    session.wait_prompt()

def check_partial_parameter(session):
    session.checkpoint("check_partial_parameter")
    session.send("sh fo fa ipv4\n")
    session.expect("IPv4 Routes:")
    session.wait_prompt()

def check_ambiguous_keyword(session):
    session.checkpoint("check_ambiguous_keyword")
    session.send("sh interface if1 s\n")
    session.expect('Ambiguous input "s", candidates:')
    session.wait_prompt()

def check_ambiguous_keyw_or_param(session):
    session.checkpoint("check_ambiguous_keyword_or_param")
    session.send("sh in\n")
    session.expect('Ambiguous input "in", candidates:')
    session.wait_prompt()

def test_telnet_commands():
    session = TelnetSession()
    check_telnet_negotiation(session)
    check_help(session)
    check_enter_blank_line(session)
    check_command_no_parameters(session)
    check_command_one_parameter(session)
    check_optional_keyword(session)
    check_missing_keyword(session)
    check_unknown_keyword(session)
    check_extra_keyword(session)
    check_missing_parameter(session)
    check_partial_keyword(session)
    check_partial_parameter(session)
    check_ambiguous_keyword(session)
    check_ambiguous_keyw_or_param(session)
    session.checkpoint("stop")
    session.stop()

def check_empty_history(session):
    session.checkpoint("check_empty_history")
    session.send_special("up")
    session.expect_special("bell")
    session.send_special("down")
    session.expect_special("bell")

def check_non_empty_history(session):
    # pylint:disable=too-many-statements
    session.checkpoint("check_non_empty_history")
    # Put a few (valid and non-valid) command in the history
    session.send("show interfaces\n")
    session.wait_prompt()
    session.send("show interface if1\n")
    session.wait_prompt()
    session.send("nonsense\n")
    session.wait_prompt()
    # Previous command (allowed) while cursor is at start of line
    session.send_special("up")
    session.expect_special("erase-to-eol")
    session.expect("nonsense")
    # Previous command (allowed) while cursor is at end of line
    session.send_special("up")
    session.expect_special("left-8 erase-to-eol")
    session.expect("show interface if1")
    # Move cursor to middle of line
    session.send_special("ctrl-a")
    session.expect_special("left-18")
    session.send_special("right right")
    session.expect_special("right-1 right-1")
    # Previous command (allowed) while cursor is in middle of line
    session.send_special("up")
    session.expect_special("left-2 erase-to-eol")
    session.expect("show interfaces")
    # Previous command (not allowed, have reached start of history)
    session.send_special("up")
    session.expect_special("bell")
    # Current command is still "show interfaces". Send enter to execute it.
    session.send("\n")
    session.expect("if1")
    session.expect("if2")
    session.wait_prompt()
    # The commands we just executed ("show interfaces") should be appended to the history
    session.send_special("up")
    session.expect_special("erase-to-eol")
    session.expect("show interfaces")
    # Previous command (allowed) while cursor is at end of line
    session.send_special("ctrl-p")
    session.expect_special("left-15 erase-to-eol")
    session.expect("nonsense")
    # Previous command (allowed) while cursor is at end of line
    session.send_special("up")
    session.expect_special("left-8 erase-to-eol")
    session.expect("show interface if1")
    # Previous command (allowed) while cursor is at end of line
    session.send_special("up")
    session.expect_special("left-18 erase-to-eol")
    session.expect("show interfaces")
    # Move cursor to beginning of line
    session.send_special("ctrl-a")
    session.expect_special("left-15")
    # Next command (allowed) while cursor is at start of line
    session.send_special("down")
    session.expect_special("erase-to-eol")
    session.expect("show interface if1")
    # Next command (allowed) while cursor is at end of line
    session.send_special("down")
    session.expect_special("left-18 erase-to-eol")
    session.expect("nonsense")
    # Move cursor to middle of line
    session.send_special("ctrl-a")
    session.expect_special("left-8")
    session.send_special("right right")
    session.expect_special("right-1 right-1")
    # Next command (allowed) while cursor is in middle of line
    session.send_special("down")
    session.expect_special("left-2 erase-to-eol")
    session.expect("show interfaces")
    # Next command (allowed) while cursor is at end of line
    session.send_special("down")
    session.expect_special("left-15 erase-to-eol")
    # Next command (not allowed, have reached end of history)
    session.send_special("ctrl-n")
    session.expect_special("bell")
    # Enter and execute a new command
    session.send("show tie-db\n")
    session.expect("TIE Nr")
    session.wait_prompt()
    # Next command (not allowed, not in history)
    session.send_special("down")
    session.expect_special("bell")
    # Enter partial command, up and down, complete and execute command
    session.send("show s")
    session.send_special("up")
    session.expect_special("left-6 erase-to-eol")
    session.expect("show tie-db")
    session.send_special("down")
    session.expect_special("left-11 erase-to-eol")
    session.expect("show s")
    session.send("pf")
    session.expect("pf")
    session.send("\n")
    session.expect("Predecessor")
    session.wait_prompt()

def test_telnet_history():
    session = TelnetSession()
    check_telnet_negotiation(session)
    check_empty_history(session)
    check_non_empty_history(session)
    session.checkpoint("stop")
    session.stop()

def check_line_move_left_right(session):
    session.checkpoint("check_line_move_left_right")
    session.send("help")
    session.expect("help")
    # Move left (allowed)
    session.send_special("left left left left")
    session.expect_special("left-1 left-1 left-1 left-1")
    # Move left (not allowed at beginning of line)
    session.send_special("left")
    session.expect_special("bell")
    # Move right (allowed)
    session.send_special("right right right right")
    session.expect_special("right-1 right-1 right-1 right-1")
    # Move right (not allowed at end of line)
    session.send_special("right")
    session.expect_special("bell")
    # Enter
    session.send("\n")
    session.wait_prompt()

def check_line_move_start_end(session):
    session.checkpoint("check_line_move_start_end")
    session.send("help")
    session.expect("help")
    # Move from end-of-line to start-of-line
    session.send_special("ctrl-a")
    session.expect_special("left-4")
    # Move from start-of-line to end-of-line
    session.send_special("ctrl-e")
    session.expect_special("right-4")
    # Move to middle of line
    session.send_special("left left")
    session.expect_special("left-1 left-1")
    # Move from middle to start-of-line
    session.send_special("ctrl-a")
    session.expect_special("left-2")
    # Move to middle of line
    session.send_special("right right")
    session.expect_special("right-1 right-1")
    # Move from middle to end-of-line
    session.send_special("ctrl-e")
    session.expect_special("right-2")
    # Enter
    session.send("\n")
    session.wait_prompt()

def test_telnet_line_move():
    session = TelnetSession()
    check_telnet_negotiation(session)
    check_line_move_left_right(session)
    check_line_move_start_end(session)
    session.checkpoint("stop")
    session.stop()

def check_end_of_line_cr(session):
    session.checkpoint("check_end_of_line_cr")
    session.send("show spf")
    session.expect("show spf")
    time.sleep(0.1)
    session.send("\r")
    time.sleep(0.1)
    session.send("\n")
    session.expect("Predecessor")
    session.wait_prompt()

def check_end_of_line_lf(session):
    session.checkpoint("check_end_of_line_lf")
    session.checkpoint("check_end_of_line_cr")
    session.send("show interfaces")
    session.expect("show interfaces")
    time.sleep(0.1)
    session.send("\n")
    session.expect("if1")
    session.expect("if2")
    session.wait_prompt()

def test_end_of_line():
    session = TelnetSession()
    check_telnet_negotiation(session)
    check_end_of_line_cr(session)
    check_end_of_line_lf(session)
    session.checkpoint("stop")
    session.stop()

def check_edit_add_chars_at_end(session):
    session.checkpoint("check_edit_add_chars_at_end")
    session.send("abc")
    session.expect("abc")
    session.send("def")
    session.expect("def")
    session.send("\n")
    session.wait_prompt()

def check_edit_add_chars_in_middle(session):
    session.checkpoint("check_edit_add_chars_in_middle")
    session.send("abcdef")
    session.expect("abcdef")
    session.send_special("left left left")
    session.expect_special("left-1 left-1 left-1")
    session.send("x")
    session.expect_special("erase-to-eol")
    session.expect("xdef")
    session.expect_special("left-4 right-1")
    session.send("y")
    session.expect_special("erase-to-eol")
    session.expect("ydef")
    session.expect_special("left-4 right-1")
    session.send("\n")
    session.wait_prompt()

def check_edit_add_chars_at_start(session):
    session.checkpoint("check_edit_add_chars_at_start")
    session.send("abc")
    session.expect("abc")
    session.send_special("left left left")
    session.expect_special("left-1 left-1 left-1")
    session.send("x")
    session.expect_special("erase-to-eol")
    session.expect("xabc")
    session.expect_special("left-4 right-1")
    session.send("y")
    session.expect_special("erase-to-eol")
    session.expect("yabc")
    session.expect_special("left-4 right-1")
    session.send("\n")
    session.wait_prompt()

def check_del_at_end(session):
    session.checkpoint("check_del_at_end")
    session.send("abc")
    session.expect("abc")
    session.send_special("left")
    session.expect_special("left-1")
    session.send_special("del")
    session.expect_special("left-1 erase-to-eol")
    session.expect("c")
    session.expect_special("left-1")
    session.send_special("del")
    session.expect_special("left-1 erase-to-eol")
    session.expect("c")
    session.expect_special("left-1")
    session.send_special("del")
    session.expect_special("bell")
    session.send("\n")
    session.wait_prompt()

def check_del_in_middle(session):
    session.checkpoint("check_del_in_middle")
    session.send("abc")
    session.expect("abc")
    session.send_special("del")
    session.expect_special("left-1 erase-to-eol")
    session.send_special("del")
    session.expect_special("left-1 erase-to-eol")
    session.send_special("del")
    session.expect_special("left-1 erase-to-eol")
    session.send_special("del")
    session.expect_special("bell")
    session.send("\n")
    session.wait_prompt()

def check_del_at_start(session):
    session.checkpoint("check_del_at_start")
    session.send("abc")
    session.expect("abc")
    session.send_special("ctrl-a")
    session.expect_special("left-3")
    session.send_special("del")
    session.expect_special("bell")
    session.send("\n")
    session.wait_prompt()

def test_edit():
    session = TelnetSession()
    check_telnet_negotiation(session)
    check_edit_add_chars_at_end(session)
    check_edit_add_chars_in_middle(session)
    check_edit_add_chars_at_start(session)
    check_del_at_end(session)
    check_del_in_middle(session)
    session.checkpoint("stop")
    session.stop()

def check_ignore_nul(session):
    session.checkpoint("check_ignore_nul")
    session.send("sh")
    session.expect("sh")
    session.send_special("nul")
    session.send("ow interfaces\n")
    session.expect("ow interfaces")
    session.expect("if1")
    session.expect("if2")
    session.wait_prompt()

def test_various():
    session = TelnetSession()
    check_telnet_negotiation(session)
    check_ignore_nul(session)
    session.checkpoint("stop")
    session.stop()
