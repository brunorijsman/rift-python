import re

class LogRecord:

    _record_regex = re.compile(r"(....-..-.. ..:..:..[^:]*):([^:]*):([^:]*):\[(.*?)\] (.*)$")
    _start_fsm_regex = re.compile(r"Start FSM, state=(.*)")
    _push_event_regex = re.compile(r"FSM push event, "
                                   "event=(.*)")
    _transition_regex = re.compile(r"FSM transition "
                                   "sequence-nr=(.*) "
                                   "from-state=(.*) "
                                   "event=(.*) "
                                   "actions-and-pushed-events=(.*) "
                                   "to-state=(.*) "
                                   "implicit=(.*)")
    _send_regex = re.compile(r"Send.*(ProtocolPacket.*)")
    _receive_regex = re.compile(r"Receive.*(ProtocolPacket.*)")
    _lie_packet_regex = re.compile(r".*lie=LIEPacket.*nonce=([0-9]*)")
    _tie_packet_regex = re.compile(r".*tie=TIEPacket")
    _tide_packet_regex = re.compile(r".*tide=TIDEPacket")
    _tire_packet_regex = re.compile(r".*tire=TIREPacket")
    _cli_command_regex = re.compile(r".*Execute CLI command \"(.*)\"")

    def __init__(self, tick, logline):
        self.tick = tick
        match_result = LogRecord._record_regex.search(logline)
        self.timestamp = match_result.group(1)
        self.severity = match_result.group(2)
        self.subsystem = match_result.group(3)
        self.target_id = match_result.group(4)
        self.target = None
        self.nonce = None
        self.msg = match_result.group(5)
        match_result = LogRecord._start_fsm_regex.match(self.msg)
        if match_result:
            self.type = "start-fsm"
            self.state = match_result.group(1)
            return
        match_result = LogRecord._push_event_regex.match(self.msg)
        if match_result:
            self.type = "push-event"
            self.event = match_result.group(1)
            return
        match_result = LogRecord._transition_regex.match(self.msg)
        if match_result:
            self.type = "transition"
            self.sequence_nr = match_result.group(1)
            self.from_state = match_result.group(2)
            self.event = match_result.group(3)
            self.actions_and_pushed_events = match_result.group(4)
            self.to_state = match_result.group(5)
            self.implicit = match_result.group(6)
            return
        match_result = LogRecord._send_regex.match(self.msg)
        if match_result:
            self.type = "send"
            self.packet = match_result.group(1)
            self.parse_packet_type()
            return
        match_result = LogRecord._receive_regex.match(self.msg)
        if match_result:
            self.type = "receive"
            self.packet = match_result.group(1)
            self.parse_packet_type()
            return
        match_result = LogRecord._cli_command_regex.match(self.msg)
        if match_result:
            self.type = "cli"
            self.cli_command = match_result.group(1)
            return
        self.type = "other"

    def parse_packet_type(self):
        match_result = LogRecord._lie_packet_regex.match(self.packet)
        if match_result:
            self.packet_type = "LIE"
            self.nonce = match_result.group(1)
            return
        match_result = LogRecord._tie_packet_regex.match(self.packet)
        if match_result:
            self.packet_type = "TIE"
            return
        match_result = LogRecord._tide_packet_regex.match(self.packet)
        if match_result:
            self.packet_type = "TIDE"
            return
        match_result = LogRecord._tire_packet_regex.match(self.packet)
        if match_result:
            self.packet_type = "TIRE"
            return
        self.packet_type = "UNKNOWN"
