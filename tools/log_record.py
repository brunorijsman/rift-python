import re

class LogRecord:

    # TODO: Make private?
    record_regex = re.compile(r"(....-..-.. ..:..:..[^:]*):([^:]*):([^:]*):\[(.*)\] (.*)$")
    start_fsm_regex = re.compile(r"Start FSM, state=(.*)")
    push_event_regex = re.compile(r"FSM push event, "
                                  "event=(.*)")
    transition_regex = re.compile(r"FSM transition "
                                  "sequence-nr=(.*) "
                                  "from-state=(.*) "
                                  "event=(.*) "
                                  "actions-and-pushed-events=(.*) "
                                  "to-state=(.*) "
                                  "implicit=(.*)")
    send_regex = re.compile(r"Send.*(ProtocolPacket.*)")
    receive_regex = re.compile(r"Receive.*(ProtocolPacket.*)")
    lie_packet_regex = re.compile(r".*lie=LIEPacket.*nonce=([0-9]*)")
    cli_command_regex = re.compile(r".*Execute CLI command \"(.*)\"")

    def __init__(self, tick, logline):
        self.tick = tick
        match_result = LogRecord.record_regex.search(logline)
        self.timestamp = match_result.group(1)
        self.severity = match_result.group(2)
        self.subsystem = match_result.group(3)
        self.target_id = match_result.group(4)
        self.target = None
        self.msg = match_result.group(5)
        match_result = LogRecord.start_fsm_regex.match(self.msg)
        if match_result:
            self.type = "start-fsm"
            self.state = match_result.group(1)
            return
        match_result = LogRecord.push_event_regex.match(self.msg)
        if match_result:
            self.type = "push-event"
            self.event = match_result.group(1)
            return
        match_result = LogRecord.transition_regex.match(self.msg)
        if match_result:
            self.type = "transition"
            self.sequence_nr = match_result.group(1)
            self.from_state = match_result.group(2)
            self.event = match_result.group(3)
            self.actions_and_pushed_events = match_result.group(4)
            self.to_state = match_result.group(5)
            self.implicit = match_result.group(6)
            return
        match_result = LogRecord.send_regex.match(self.msg)
        if match_result:
            self.type = "send"
            self.packet = match_result.group(1)
            match_result = LogRecord.lie_packet_regex.match(self.packet)
            if match_result:
                self.packet_type = "LIE"
                self.nonce = match_result.group(1)
            return
        match_result = LogRecord.receive_regex.match(self.msg)
        if match_result:
            self.type = "receive"
            self.packet = match_result.group(1)
            match_result = LogRecord.lie_packet_regex.match(self.packet)
            if match_result:
                self.packet_type = "LIE"
                self.nonce = match_result.group(1)
            return
        match_result = LogRecord.cli_command_regex.match(self.msg)
        if match_result:
            self.type = "cli"
            self.cli_command = match_result.group(1)
            return
        self.type = "other"
