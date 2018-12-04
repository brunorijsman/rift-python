import re

# pylint: disable=W0401
# pylint: disable=W0614
from common.ttypes import *
from encoding.ttypes import *
import packet_common

packet_common.add_missing_methods_to_thrift()

# TODO: Remove this horrible hack.
# This is a horrible hack to work around the following problem. I am having huge problems getting
# my visualization tool to properly correlate sent message to received messages (i.e. to properly
# draw the lines from the sender to the receiver). As Tony has pointed out several times, Thrift
# encoding is not canonical. On top of that, even for the exact same binary message, two different
# Python processes may create different internal binary structures because Python dictionaries use
# non-deterministic hashes (this is by design - it is a security feature). The following code works
# around the problem: it converts a ProtocolPacket object into another object (nested tuples) which
# consistently hash to the same value, regardless of the order in which iterators visit member of
# dictionary or set. It does this by sorting non-deterministic containers and converting them to
# tuples. I have proposed adding a correlator field the transport header to solve the problem more
# fundamentally; if and when that happens we can remove this hack, and the need for packet decoding,
# and we can move the visualization tool back to the tools directory.
#
def make_deterministic_hashable(obj, top=True):
    # This function produces the same has for objects that contain dictionaries and that only differ
    # in the order in which the dict iterators visit the members of the dict.
    if not top:
        try:
            hash(obj)
        except TypeError:
            pass
        else:
            return obj
    if ("__module__" in obj.__dir__()) and (obj.__module__ in ["encoding.ttypes", "common.ttypes"]):
        tup = None
        for attr_name in sorted(obj.__dir__()):
            if str(attr_name).startswith("__"):
                continue
            if attr_name == "thrift_spec":
                continue
            attr_value = getattr(obj, attr_name)
            if callable(attr_value):
                continue
            attr_tup = (attr_name, make_deterministic_hashable(attr_value, False))
            if tup is None:
                tup = attr_tup
            else:
                tup = tup, attr_tup
        return tup
    if isinstance(obj, dict):
        tup = tuple((k, make_deterministic_hashable(v, False)) for (k, v) in sorted(obj.items()))
        return tup
    if hasattr(obj, '__iter__'):
        tup = tuple(make_deterministic_hashable(o, False) for o in obj)
        return tup
    assert False
    return None

ProtocolPacket.__hash__ = lambda self: hash(make_deterministic_hashable(self))

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
    _send_regex = re.compile(r"Send.*(ProtocolPacket.*) to .*$")
    _receive_regex = re.compile(r"Receive.*(ProtocolPacket.*) from .*$")
    _lie_packet_regex = re.compile(r".*lie=LIEPacket.*[^_]nonce=([0-9]*)")
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
            self.decode_packet()
            return
        match_result = LogRecord._receive_regex.match(self.msg)
        if match_result:
            self.type = "receive"
            self.packet = match_result.group(1)
            self.parse_packet_type()
            self.decode_packet()
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

    def decode_packet(self):
        decodable_packet = self.packet
        decodable_packet.replace("\\", "\\\\")
        # pylint: disable=W0123
        self.decoded_packet = eval(decodable_packet)
