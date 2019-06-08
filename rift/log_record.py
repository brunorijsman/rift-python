import re

# pylint: disable=wildcard-import
# pylint: disable=unused-wildcard-import
from common.ttypes import *
from encoding.ttypes import *
import packet_common

packet_common.add_missing_methods_to_thrift()

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
    _send_regex = re.compile(r"Send ([^ ]*) ([^ ]*) from ([^ ]*) to ([^ ]*) (packet-nr=.*)$")
    _receive_regex = re.compile(r"Receive ([^ ]*) ([^ ]*) from ([^ ]*) (packet-nr=.*)$")
    _envelope_regex = re.compile(r"(packet-nr=.*) protocol-packet=(.*)$")
    _packet_nr_regex = re.compile(r"packet-nr=([0-9]*) .*$")
    _cli_command_regex = re.compile(r".*Execute CLI command \"(.*)\"")

    def __init__(self, tick, logline):
        self.tick = tick
        match_result = LogRecord._record_regex.search(logline)
        self.timestamp = match_result.group(1)
        self.severity = match_result.group(2)
        self.subsystem = match_result.group(3)
        self.target_id = match_result.group(4)
### TODO        self.target = None
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
            self.packet_family = match_result.group(1)
            self.packet_type = match_result.group(2)
            self.source = match_result.group(3)
            self.dest = match_result.group(4)
            self.packet = match_result.group(5)
            self.decode_packet()
            return
        match_result = LogRecord._receive_regex.match(self.msg)
        if match_result:
            self.type = "receive"
            self.packet_family = match_result.group(1)
            self.packet_type = match_result.group(2)
            self.source = match_result.group(3)
            self.packet = match_result.group(4)
            self.decode_packet()
            return
        match_result = LogRecord._cli_command_regex.match(self.msg)
        if match_result:
            self.type = "cli"
            self.cli_command = match_result.group(1)
            return
        if self.severity in ["WARNING", "ERROR", "CRITICAL"]:
            self.type = "log"
            return
        self.type = "other"

    def decode_packet(self):
        match_result = LogRecord._envelope_regex.match(self.packet)
        self.envelope = match_result.group(1)
        self.protocol_packet = match_result.group(2)
        match_result = LogRecord._packet_nr_regex.match(self.envelope)
        self.packet_nr = match_result.group(1)
        self.msg_id = self.source + "-" + self.packet_type + "-" + self.packet_nr
        decodable_protocol_packet = self.protocol_packet
        decodable_protocol_packet.replace("\\", "\\\\")
        # pylint: disable=eval-used
        # Yeah, yeah, yeah,  don't freak out about eval; this is just a debugging tool.
        self.decoded_packet = (self.packet_family, eval(decodable_protocol_packet))
