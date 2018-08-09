import tools.log_record

class LogExpectSession:

    def __init__(self, log_file_name):
        self._log_file_name = log_file_name
        self._log_file = None
        self._expect_log_file = open('expect.log', 'ab')
        self._line_nr = 0

    def open(self):
        self._log_file = open(self._log_file_name, "r")
        self._line_nr = 0

    def close(self):
        self._log_file.close()

    def write_record_to_expect_log_file(self, record):
        msg = ("Observerd FSM transition:\n"
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
        self._expect_log_file.write(msg.encode())

    def get_next_fsm_record_for_target(self, target_id):
        while True:
            line = self._log_file.readline()
            if not line:
                return None
            self._line_nr += 1
            record = tools.log_record.LogRecord(self._line_nr, line)
            if record.type == "transition" and record.target_id == target_id:
                self.write_record_to_expect_log_file(record)
                return record

    def fsm_expect(self, target_id, from_state, event, to_state, skip_events=None):
        msg = ("Searching for FSM transition:\n"
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
        self._expect_log_file.write(msg.encode())
        while True:
            record = self.get_next_fsm_record_for_target(target_id)
            if not record:
                msg = "Did not find FSM transition for target-id {}".format(target_id)
                self._expect_log_file.write(msg.encode())
                assert False, msg
            if skip_events and record.event in skip_events:
                continue
            if record.from_state != from_state:
                msg = ("FSM transition has from-state {} instead of expected from-state {}"
                       .format(record.from_state, from_state))
                self._expect_log_file.write(msg.encode())
                assert False, msg
            if record.event != event:
                msg = ("FSM transition has event {} instead of expected event {}"
                       .format(record.event, event))
                self._expect_log_file.write(msg.encode())
                assert False, msg
            if record.to_state != to_state:
                msg = ("FSM transition has to-state {} instead of expected to-state {}"
                       .format(record.to_state, to_state))
                self._expect_log_file.write(msg.encode())
                assert False, msg
            msg = "Found expected FSM transition\n\n"
            self._expect_log_file.write(msg.encode())
            return record

    def check_lie_fsm_3way(self, system_id, interface):
        target_id = system_id + "-" + interface
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
            to_state="TWO_WAY")
        self.fsm_expect(
            target_id=target_id,
            from_state="TWO_WAY",
            event="SEND_LIE",
            to_state="None")
        self.fsm_expect(
            target_id=target_id,
            from_state="TWO_WAY",
            event="LIE_RECEIVED",
            to_state="None")
        self.fsm_expect(
            target_id=target_id,
            from_state="TWO_WAY",
            event="VALID_REFLECTION",
            to_state="THREE_WAY")
        self.close()
