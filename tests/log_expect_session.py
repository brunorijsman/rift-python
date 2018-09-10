import datetime
import os
import traceback
import tools.log_record

class LogExpectSession:

    def __init__(self):
        log_file_name = "rift.log"
        results_file_name = "log_expect.log"
        if "RIFT_TEST_RESULTS_DIR" in os.environ:
            results_file_name = os.environ["RIFT_TEST_RESULTS_DIR"] + "/" + results_file_name
            log_file_name = os.environ["RIFT_TEST_RESULTS_DIR"] + "/" + log_file_name
        self._log_file_name = log_file_name
        self._log_file = None
        self._results_file = open(results_file_name, 'w')
        self._line_nr = 0
        self._last_timestamp = None

    def open(self):
        self._log_file = open(self._log_file_name, "r")
        self._line_nr = 0
        self._results_file.write("Open LogExpectSession\n\n")

    def close(self):
        self._log_file.close()
        self._results_file.write("Close LogExpectSession\n\n")

    def expect_failure(self, msg):
        self._results_file.write(msg + "\n\n")
        # Generate a call stack in rift_expect.log for easier debugging
        # But pytest call stacks are very deep, so only show the "interesting" lines
        for line in traceback.format_stack():
            if "tests/" in line:
                self._results_file.write(line.strip())
                self._results_file.write("\n")
        assert False, msg + " (see log_expect.log for details)"

    def write_fsm_record(self, record):
        msg = ("Observed FSM transition:\n"
               "  log-line-nr = {}\n"
               "  sequence-nr = {}\n"
               "  from-state = {}\n"
               "  event = {}\n"
               "  actions-and-pushed-events = {}\n"
               "  to-state = {}\n"
               "  implicit = {}\n"
               "\n").format(self._line_nr,
                            record.sequence_nr,
                            record.from_state,
                            record.event,
                            record.actions_and_pushed_events,
                            record.to_state,
                            record.implicit)
        self._results_file.write(msg)

    def get_next_fsm_record_for_target(self, target_id):
        while True:
            line = self._log_file.readline()
            if not line:
                return None
            self._line_nr += 1
            record = tools.log_record.LogRecord(self._line_nr, line)
            if record.type == "transition" and record.target_id == target_id:
                self.write_fsm_record(record)
                return record

    def fsm_expect(self, target_id, from_state, event, to_state, skip_events=None, max_delay=None):
        msg = ("Expecting FSM transition:\n"
               "  target-id = {}\n"
               "  from-state = {}\n"
               "  event = {}\n"
               "  to-state = {}\n"
               "  skip-events = {}\n"
               "\n").format(target_id,
                            from_state,
                            event,
                            to_state,
                            skip_events)
        self._results_file.write(msg)
        while True:
            record = self.get_next_fsm_record_for_target(target_id)
            if not record:
                msg = "Did not find FSM transition for {}".format(target_id)
                self.expect_failure(msg)
            if skip_events and record.event in skip_events:
                continue
            if record.from_state != from_state:
                msg = ("FSM transition has from-state {} instead of expected from-state {}"
                       .format(record.from_state, from_state))
                self.expect_failure(msg)
            if record.event != event:
                msg = ("FSM transition has event {} instead of expected event {}"
                       .format(record.event, event))
                self.expect_failure(msg)
            if record.to_state != to_state:
                msg = ("FSM transition has to-state {} instead of expected to-state {}"
                       .format(record.to_state, to_state))
                self.expect_failure(msg)
            timestamp = datetime.datetime.strptime(record.timestamp, "%Y-%m-%d %H:%M:%S,%f")
            if max_delay:
                if not self._last_timestamp:
                    msg = "Maxdelay specified in fsm_expect, but no previous event"
                    self.expect_failure(msg)
                delta = timestamp - self._last_timestamp
                delta_seconds = delta.total_seconds() + delta.microseconds / 1000000.0
                if delta_seconds > max_delay:
                    msg = ("Actual delay {} exceeds maximum delay {}"
                           .format(delta_seconds, max_delay))
                    self.expect_failure(msg)
            self._last_timestamp = timestamp
            self._results_file.write("Found expected log transition\n\n")
            return record

    def fsm_find(self, target_id, from_state, event, to_state):
        msg = ("Finding FSM transition:\n"
               "  target-id = {}\n"
               "  from-state = {}\n"
               "  event = {}\n"
               "  to-state = {}\n"
               "\n").format(target_id,
                            from_state,
                            event,
                            to_state)
        self._results_file.write(msg)
        while True:
            record = self.get_next_fsm_record_for_target(target_id)
            if not record:
                msg = "Did not find FSM transition for {}".format(target_id)
                self.expect_failure(msg)
            if (record.from_state == from_state and
                    record.event == event and
                    record.to_state == to_state):
                self._results_file.write("Found expected log transition\n\n")
                return record

    def write_cli_record(self, record):
        msg = ("Observed CLI command:\n"
               "  log-line-nr = {}\n"
               "  cli-command = {}\n"
               "\n").format(self._line_nr, record.cli_command)
        self._results_file.write(msg)

    def get_next_cli_record(self):
        while True:
            line = self._log_file.readline()
            if not line:
                return None
            self._line_nr += 1
            record = tools.log_record.LogRecord(self._line_nr, line)
            if record.type == "cli":
                self.write_cli_record(record)
                return record

    def skip_to_cli_command(self, cli_command):
        msg = ("Searching for CLI command:\n"
               "  cli-command = {}\n"
               "\n").format(cli_command)
        self._results_file.write(msg)
        while True:
            record = self.get_next_cli_record()
            if not record:
                self.expect_failure("Did not find CLI command")
            if record.cli_command != cli_command:
                continue
            self._results_file.write("Skipped to CLI command\n\n")
            return record

    def check_lie_fsm_3way(self, node, interface):
        # Check that an adjacency comes up to the 3-way between a pair of nodes where both nodes
        # have a hard-configured level.
        target_id = node + "-" + interface
        self.open()
        self.fsm_expect(
            target_id=target_id,
            from_state="ONE_WAY",
            event="LIE_RECEIVED",
            to_state="None",
            skip_events=["TIMER_TICK", "SEND_LIE"])
        self.fsm_expect(
            target_id=target_id,
            from_state="ONE_WAY",
            event="NEW_NEIGHBOR",
            to_state="TWO_WAY",
            skip_events=["TIMER_TICK", "SEND_LIE"])
        self.fsm_expect(
            target_id=target_id,
            from_state="TWO_WAY",
            event="SEND_LIE",
            to_state="None",
            skip_events=["TIMER_TICK"],
            max_delay=0.1)      # Our LIE should be triggered
        # Note: if the remote side receives the LIE packet that we just sent out above, we should
        # receive a LIE "quickly" which the SEND_LIE event on the remote node is triggered by the
        # RECEIVE_LIE event. I had a max_delay of 0.1 in the expect below to check for that.
        # However, in some environments it takes some time for the initial IGMP joins to be
        # processed. The remote node may not receive the LIE which we sent out above, in which case
        # one ore more timer ticks are needed. I had to remove the max_delay.
        self.fsm_expect(
            target_id=target_id,
            from_state="TWO_WAY",
            event="LIE_RECEIVED",
            to_state="None",
            skip_events=["TIMER_TICK", "SEND_LIE"])
        # For the same reason as described above, the remote node may send us multiple LIE messages
        # before it sees the first LIE message sent from this node. Thus, we need to ignore
        # additional LIE_RECEIVED events while looking for the expected VALID_REFLECTION event.
        self.fsm_expect(
            target_id=target_id,
            from_state="TWO_WAY",
            event="VALID_REFLECTION",
            to_state="THREE_WAY",
            skip_events=["TIMER_TICK", "SEND_LIE", "LIE_RECEIVED"])
        self.close()

    def check_lie_fsm_1way_bad_level(self, node, interface):
        # Check that an adjacency is stuck in 1-way because the header is persistently unacceptable
        # because both this node and the remote node have hard-configured levels that
        # are more than one level apart.
        # We look for the first UNACCEPTABLE_HEADER and then look for 2 more to make sure it is not
        # transient.
        target_id = node + "-" + interface
        self.open()
        self.fsm_find(
            target_id=target_id,
            from_state="ONE_WAY",
            event="UNACCEPTABLE_HEADER",
            to_state="ONE_WAY")
        self.fsm_expect(
            target_id=target_id,
            from_state="ONE_WAY",
            event="UNACCEPTABLE_HEADER",
            to_state="ONE_WAY",
            skip_events=["TIMER_TICK", "SEND_LIE", "LIE_RECEIVED"])
        self.fsm_expect(
            target_id=target_id,
            from_state="ONE_WAY",
            event="UNACCEPTABLE_HEADER",
            to_state="ONE_WAY",
            skip_events=["TIMER_TICK", "SEND_LIE", "LIE_RECEIVED"])
        self.close()

    def check_lie_fsm_3way_with_ztp(self, node, interface):
        # Check that an adjacency comes up to the 3-way between this node and the remote node on
        # the other side of the specified interface.
        # This is assuming that one node or both nodes start out with level undefined, and that
        # ZTP is used to eventually negotiate a level for one or both nodes.
        # See also comments in check_lie_fsm_3way to understand some of the finer timing gotchas
        target_id = node + "-" + interface
        self.open()
        self.fsm_expect(
            target_id=target_id,
            from_state="ONE_WAY",
            event="LIE_RECEIVED",
            to_state="None",
            skip_events=["TIMER_TICK", "SEND_LIE"])
        # Initially, until an offer is accepted, one or both nodes will have level undefined and
        # hence do not advertise a level in the LIE messages that they send. In this phase *both*
        # nodes will reject all received LIE messages. One side will reject them because the
        # received LIE message does not have a level, the other side will reject received LIE
        # messages because it itself has level undefined. Either way, the net result is that we
        # a series of zero or more LIE_RECEIVED events, each followed by an UNACCEPTABLE_HEADER
        # event. Eventually, and offer is accepted which is seen as a NEW_NEIGHBOR event.
        self.fsm_expect(
            target_id=target_id,
            from_state="ONE_WAY",
            event="NEW_NEIGHBOR",
            to_state="TWO_WAY",
            skip_events=["TIMER_TICK", "SEND_LIE", "LIE_RECEIVED", "UNACCEPTABLE_HEADER"])
        self.fsm_expect(
            target_id=target_id,
            from_state="TWO_WAY",
            event="SEND_LIE",
            to_state="None",
            skip_events=["TIMER_TICK"],
            max_delay=0.1)
        self.fsm_expect(
            target_id=target_id,
            from_state="TWO_WAY",
            event="LIE_RECEIVED",
            to_state="None",
            skip_events=["TIMER_TICK", "SEND_LIE"])
        self.fsm_expect(
            target_id=target_id,
            from_state="TWO_WAY",
            event="VALID_REFLECTION",
            to_state="THREE_WAY",
            skip_events=["TIMER_TICK", "SEND_LIE", "LIE_RECEIVED"])
        self.close()

    def check_lie_fsm_timeout_to_1way(self, node, interface, failure_command):
        # Check that after an interface fails, the adjacency times out and transitions from
        # 3-way to 1-way.
        target_id = node + "-" + interface
        self.open()
        self.skip_to_cli_command(failure_command)
        self.fsm_expect(
            target_id=target_id,
            from_state="THREE_WAY",
            event="HOLD_TIME_EXPIRED",
            to_state="ONE_WAY",
            skip_events=["TIMER_TICK", "SEND_LIE"])
        self.close()
