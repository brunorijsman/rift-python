import enum
import socket

import scheduler

# TODO: Make cursor up and down keys work... (implement a real Telnet/SSH server)

class CliSessionHandler:

    def __init__(self, sock, remote_address, parse_tree, command_handler, prompt):
        self._sock = sock
        self._sock.setblocking(0)
        self._remote_address = remote_address
        self._parse_tree = parse_tree
        self._command_handler = command_handler
        self._prompt = prompt
        self._str = ""
        scheduler.scheduler.register_handler(self, True, False)
        self.send_prompt()

    def socket(self):
        return self._sock

    def print(self, str, add_newline = True):
        if add_newline:
            str += '\n'
        self._sock.send(str.encode('utf-8'))

    def print_help_recursion(self, command_str, match_subtree):
        if callable(match_subtree):
            self.print(command_str)
        else:
            for match_expression, new_match_subtree in match_subtree.items():
                new_command_str = command_str + match_expression + " "
                self.print_help_recursion(new_command_str, new_match_subtree)

    def print_help(self, match_subtree):
        self.print_help_recursion("", match_subtree)

    class MatchType(enum.Enum):
        MANDATORY_KEYWORD = 1
        OPTIONAL_KEYWORD = 2
        MANDATORY_PARAMETER = 3
        OPTIONAL_PARAMETER = 4

    class ParseResult(enum.Enum):
        SUCCESS = 1
        MISSING_MANDATORY_KEYWORD = 2
        MISSING_MANDATORY_PARAMETER = 3

    def split_parse_match_expression(self, parse_expression):
        if match_expression[0] == '[':
            if match_expression[1] == '<':
                return (self.MatchType.OPTIONAL_PARAMETER, match_expression[2:-2])
            else:
                return (self.MatchType.OPTIONAL_KEYWORD, match_expression[1:-1])
        else:
            if match_expression[0] == '<':
                return (self.MatchType.MANDATORY_PARAMETER, match_expression[1:-1])
            else:
                return (self.MatchType.MANDATORY_KEYWORD, match_expression)
        assert False, "Illegal parse expression {}".format(parse_expression)

    def tokens_match_parse_node(self, tokens, parse_match_expression, parse_action, parameters):
        # Which token in the input command are we trying to match (None if we have reached the end of the command)
        if tokens == []:
            first_token = tokens[0]
            rest_tokens = tokens[1:]
        else:
            first_token = None
            rest_tokens = []
        # What are we trying to match the token with (a keyword or a parameter, mandatory or optional)?
        (parse_match_type, parse_match_str) = self.split_parse_match_expression(parse_match_expression)
        if parse_match_type == self.MatchType.MANDATORY_KEYWORD:
            # Match against mandatory keyword: keyword must be there otherwise error
            if first_token == parse_match_str:
                return self.tokens_match_parse_action(rest_tokens, parse_action)
            else:
                return self.ParseResult.MISSING_MANDATORY_KEYWORD
        elif parse_match_type == self.MatchType.OPTIONAL_KEYWORD:
            # Match against optional keyword: if keyword is there we have a match, otherwise try skipping keyword
            if first_token == parse_match_str:
                return self.tokens_match_parse_action(rest_tokens, parse_action)
            else:
                return self.tokens_match_parse_action(tokens, parse_action)
        elif (parse_match_type == self.MatchType.MANDATORY_PARAMETER):
            # Match against mandatory parameter: if there is a token use it as parameter value, if not parse mismatch
            if first_token == None:
                return self.ParseResult.MISSING_MANDATORY_PARAMETER
            else:
                parameter_name = parse_match_str
                parameter_value = token
                parameters[parameter_name] = parameter_value
                return self.tokens_match_parse_action(rest_tokens, parse_action)
        elif (parse_match_type == self.MatchType.OPTIONAL_PARAMETER):
            # Match against optional parameter: if there is a token use it as parameter value, if not skip parameter
            if first_token == None:
                return self.tokens_match_parse_action(rest_tokens, parse_action)
            else:
                parameter_name = parse_match_str
                parameter_value = token
                parameters[parameter_name] = parameter_value
                return self.tokens_match_parse_action(rest_tokens, parse_action)
        else:
            assert False, "Unknown token match type {}".format(token_match_type)

    def tokens_match_parse_action(self, tokens, parse_action, parameters):
        # Given that the last token matched, figure out what to do next
        if callable(parse_action):
            # We have reached a leaf of the parse tree. If we have consumed all tokens, execute the action function.
            command_function = parse_action
            if parameters:
                command_function(self._command_handler, self, parameters)
            else:
                command_function(self._command_handler, self)
        else:
            # There is more to parse, so keep going.
            parse_tree = parse_action
            return self.tokens_match_parse_tree()

    def tokens_match_parse_tree(self, tokens, parse_tree, parameters):
        # Try to match the tokens to every branch in the tree. Stop on the first match, or error if no match.
        for match_expression, parse_action in parse_tree.items():
            if 




    def parse_command_recursion(self, words, command_subtree, parameters):
        if not words:
            if not self.no_more_input_to_parse(command_subtree, parameters):
                self.print('Missing input, valid completions:')
                self.print_help(command_subtree)
            return
        word = words[0]
        new_words = words[1:]
        if callable(command_subtree):
            self.print('Unexpected extra word "{}" at end of command'.format(word))
            return
        if word.lower() == "help":
            self.print_help(command_subtree)
            return
        for match_expression, match_subtree in command_subtree.items():
            (match_type, match_str) = self.parse_expression_to_parse_node
    (match_expression)
            if match_type == self.MatchType.MANDATORY_KEYWORD:
                if word == match_str:
                    self.parse_command_recursion(new_words, match_subtree, parameters)
                    return
            elif match_type == self.MatchType.OPTIONAL_KEYWORD:
                if word == match_str:
                    self.parse_command_recursion(new_words, match_subtree, parameters)
                    return
                # $$$ CONTINUE FROM HERE
            elif (match_type == self.MatchType.MANDATORY_PARAMETER):  #$$$
                parameter_name = match_str
                parameter_value = word
                parameters[parameter_name] = parameter_value
                self.parse_command_recursion(new_words, match_subtree, parameters)
                return
            elif  (match_type == self.MatchType.OPTIONAL_PARAMETER):
                pass  #$$$
        self.print('Unrecognized word "{}", valid completions:'.format(word))
        self.print_help(command_subtree)
            
    def no_more_input_to_parse(self, command_subtree, parameters):
        if callable(command_subtree):
            # The remaining subtree is a function; call that function (with parameters if there are any)
            command_function = command_subtree
            if parameters:
                command_function(self._command_handler, self, parameters)
            else:
                command_function(self._command_handler, self)
            # It's a match
            return True
        else:
            # Try all paths in the remaining subtree, until we find one that matches.
            for match_expression, match_subtree in command_subtree.items():
                (match_type, match_str) = self.parse_expression_to_parse_node
        (match_expression)
                if (match_type == self.MatchType.OPTIONAL_KEYWORD) or (match_type == self.MatchType.OPTIONAL_PARAMETER):
                    # Optional keywords and optional parameters are a match for no more input, so keep recursing
                    return self.no_more_input_to_parse(match_subtree, parameters)
            # We tried all possible paths but none of them matched empty input
            return False

    def parse_command(self, command):
        words = command.split()
        self.parse_command_recursion(words, self._parse_tree, {})

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
            if command != '':
                self.parse_command(command)
            self.send_prompt()

    def set_prompt(self, prompt):
        self._prompt = prompt
