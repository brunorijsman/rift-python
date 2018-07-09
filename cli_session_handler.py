import socket
from scheduler import scheduler

# TODO: Finish implementation of optional keywords and test
# TODO: Make cursor up and down keys work...

class CliSessionHandler:

    def __init__(self, sock, remote_address, command_tree, command_handler, prompt):
        self._sock = sock
        self._sock.setblocking(0)
        self._remote_address = remote_address
        self._command_tree = command_tree
        self._command_handler = command_handler
        self._prompt = prompt
        self._str = ""
        scheduler.register_handler(self, True, False)
        self.send_prompt()

    def socket(self):
        return self._sock

    def print(self, str, add_newline = True):
        if add_newline:
            str += '\n'
        self._sock.send(str.encode('utf-8'))

    def print_help_recursion(self, command_str, command_subtree):
        for word, new_command_subtree in command_subtree.items():
            new_command_str = command_str + word + " "
            if callable(new_command_subtree):
                self.print(new_command_str)
            else:
                self.print_help_recursion(new_command_str, new_command_subtree)

    def print_help(self, command_subtree):
        self.print_help_recursion("", command_subtree)

    def default_command_function(self, remaining_command_subtree):
        # TODO: This will become more complex when we add support for optional arguments
        if callable(remaining_command_subtree):
            return remaining_command_subtree
        return None

    def no_more_input_to_parse(self, remaining_command_subtree, parameters):
        command_function = self.default_command_function(remaining_command_subtree)
        if command_function:
            if parameters:
                command_function(self._command_handler, self, parameters)
            else:
                command_function(self._command_handler, self)
        else:
            self.print('Missing input, valid completions:')
            self.print_help(remaining_command_subtree)

    def is_mandatory_keyword(self, match_str):
        return (not self.is_parameter(match_str)) and (not self.is_optional_keyword(match_str))

    def matches_mandatory_keyword(self, match_str, word):
        return match_str.lower() == word.lower()
    
    def is_optional_keyword(self, match_str):
        return match_str[0] == '['

    def matches_optional_keyword(self, match_str, word):
        assert match_str[0] == '['
        assert match_str[-1] == ']'
        keyword = match_str[1:-1]
        return keyword.lower() == word.lower()

    def is_parameter(self, match_str):
        return match_str[0] == '<'

    def parse_parameter(self, match_str, word):
        assert match_str[0] == '<'
        assert match_str[-1] == '>'
        parameter_name = match_str[1:-1]
        parameter_value = word
        return (parameter_name, parameter_value)

    def parse_command_recursion(self, words, command_subtree, parameters):
        if not words:
            self.no_more_input_to_parse(command_subtree, parameters)
            return
        word = words[0]
        new_words = words[1:]
        if callable(command_subtree):
            # TODO: Is there is exactly one extra word and it is help, invoke command help function
            self.print('Unexpected extra word "{}" at end of command'.format(word))
            return
        if word.lower() == "help":
            self.print_help(command_subtree)
            return
        for match_str, match_subtree in command_subtree.items():
            if self.is_mandatory_keyword(match_str) and self.matches_mandatory_keyword(match_str, word):
                self.parse_command_recursion(new_words, match_subtree, parameters)
                return
            if self.is_optional_keyword(match_str) and self.matches_optional_keyword(match_str, word):
                self.parse_command_recursion(new_words, match_subtree, parameters)
                return
            if self.is_parameter(match_str):
                key_value = self.parse_parameter(match_str, word)
                (param_name, param_value) = self.parse_parameter(match_str, word)
                parameters[param_name] = param_value
                self.parse_command_recursion(new_words, match_subtree, parameters)
                return
        self.print('Unrecognized word "{}", valid completions:'.format(word))
        self.print_help(command_subtree)
            
    def parse_command(self, command):
        words = command.split()
        self.parse_command_recursion(words, self._command_tree, {})

    def send_prompt(self):
        self.print(self._prompt + "> ", False)

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
            self.parse_command(command)
            self.send_prompt()
