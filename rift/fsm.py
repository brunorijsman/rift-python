import collections
import time

import sortedcontainers

import table
import stats
import utils

_MAX_RECORDS = 100

def _action_to_name(action):
    action_name = action.__name__
    if action_name.startswith("action_"):
        action_name = action_name[len("action_"):]
    return action_name

def _event_to_name(event):
    if event is None:
        # Event None is used to record the state entry actions when the FSM is started
        return "None"
    else:
        return event.name

def _state_to_name(state):
    if state is None:
        # In the FSM, to-state None means no state change, so treat that special
        return "None"
    else:
        return state.name

class FsmDefinition:

    def __init__(self, state_enum, event_enum, transitions, initial_state,
                 state_actions=None, verbose_events=None):
        self.state_enum = state_enum
        self.event_enum = event_enum
        self.transitions = transitions
        self.initial_state = initial_state
        if state_actions is None:
            self.state_actions = {}
        else:
            self.state_actions = state_actions
        if verbose_events is None:
            self.verbose_events = []
        else:
            self.verbose_events = verbose_events

    @staticmethod
    def parse_transition(transition):
        to_state = transition[0]
        actions = transition[1]
        if len(transition) > 2:
            push_events = transition[2]
        else:
            push_events = []
        return (to_state, actions, push_events)

    # Everything in this class below here is concerned with producing a human-readable textual
    # representation of the FSM

    def states_table(self):
        tab = table.Table()
        tab.add_row(["State"])
        for state in self.state_enum:
            tab.add_row([state.name])
        return tab

    def events_table(self):
        tab = table.Table()
        tab.add_row(["Event", "Verbose"])
        for event in self.event_enum:
            verbose = (event in self.verbose_events)
            tab.add_row([event.name, verbose])
        return tab

    def transition_table(self, report_missing=False):
        tab = table.Table()
        tab.add_row(["From state", "Event", "To state", "Actions", "Push events"])
        for from_state in self.state_enum:
            if from_state in self.transitions:
                from_state_transitions = self.transitions[from_state]
            else:
                from_state_transitions = []
            self._add_from_transitions_to_table(tab, from_state, from_state_transitions,
                                                report_missing)
        return tab

    def state_actions_table(self):
        # Make sure table is sorted by state for deterministic output (needed for testing)
        sorted_state_actions = sortedcontainers.SortedDict()
        for state in self.state_actions:
            (entry_actions, exit_actions) = self.state_actions[state]
            entry_action_names = list(map(_action_to_name, entry_actions))
            if not entry_action_names:
                entry_action_names = "-"
            exit_action_names = list(map(_action_to_name, exit_actions))
            if not exit_action_names:
                exit_action_names = "-"
            sorted_state_actions[state.name] = (entry_action_names, exit_action_names)
        tab = table.Table()
        tab.add_row(["State", "Entry Actions", "Exit Actions"])
        for state_name in sorted_state_actions:
            (entry_action_names, exit_action_names) = sorted_state_actions[state_name]
            tab.add_row([state_name, entry_action_names, exit_action_names])
        return tab

    def _add_from_transitions_to_table(self, tab, from_state, from_state_transitions,
                                       report_missing):
        for event in self.event_enum:
            if event in from_state_transitions:
                transition = from_state_transitions[event]
                self._add_transition_to_table(tab, from_state, event, transition)
            else:
                if report_missing:
                    self._add_missing_transition_to_table(tab, from_state, event)

    def _add_transition_to_table(self, tab, from_state, event, transition):
        from_state_name = from_state.name
        event_name = event.name
        (to_state, actions, push_events) = FsmDefinition.parse_transition(transition)
        action_names = list(map(_action_to_name, actions))
        if to_state is None:
            to_state_name = "-"
        else:
            to_state_name = to_state.name
        action_names = list(map(_action_to_name, actions))
        if not action_names:
            action_names = "-"
        push_event_names = list(map(_event_to_name, push_events))
        if not push_event_names:
            push_event_names = "-"
        tab.add_row([from_state_name, event_name, to_state_name, action_names, push_event_names])

    def _add_missing_transition_to_table(self, tab, from_state, event):
        from_state_name = from_state.name
        event_name = event.name
        tab.add_row([from_state_name, event_name, "* MISSING *",
                     table.Table.Format.EXTEND_LEFT_CELL, table.Table.Format.EXTEND_LEFT_CELL])

    def command_show_fsm(self, cli_session):
        self.command_show_states(cli_session)
        self.command_show_events(cli_session)
        self.command_show_transitions(cli_session)
        self.command_show_state_actions(cli_session)

    def command_show_states(self, cli_session):
        cli_session.print("States:")
        tab = self.states_table()
        cli_session.print(tab.to_string())

    def command_show_events(self, cli_session):
        cli_session.print("Events:")
        tab = self.events_table()
        cli_session.print(tab.to_string())

    def command_show_transitions(self, cli_session):
        cli_session.print("Transitions:")
        tab = self.transition_table()
        cli_session.print(tab.to_string())

    def command_show_state_actions(self, cli_session):
        cli_session.print("State entry actions:")
        tab = self.state_actions_table()
        cli_session.print(tab.to_string())

class FsmRecord:

    _next_seq_nr = 1

    def __init__(self, fsm, from_state, event, verbose, queue_time):
        self.fsm = fsm
        self.seq_nr = FsmRecord._next_seq_nr
        FsmRecord._next_seq_nr += 1
        self.time = time.monotonic()
        self.queue_time = queue_time
        self.processing_time = None
        self.skipped = 0
        self.from_state = from_state
        self.event = event
        self.verbose = verbose
        self.actions_and_pushed_events = []
        self.to_state = None
        self.implicit = False

    def log_str(self):
        log_msg = ("FSM transition sequence-nr={} from-state={} event={} "
                   "actions-and-pushed-events={} to-state={} implicit={}").format(
                       self.seq_nr,
                       _state_to_name(self.from_state),
                       _event_to_name(self.event),
                       ",".join(self.actions_and_pushed_events),
                       _state_to_name(self.to_state),
                       self.implicit)
        return log_msg

class Fsm:

    # See DEV-7 in doc/deviations.md for meaning of _event_queue vs _chained_event_queue

    _event_queue = collections.deque()

    _chained_event_queue = collections.deque()

    def info(self, msg, *args):
        if self._log:
            self._log.info("[%s] %s" % (self._log_id, msg), *args)

    def info_or_debug(self, debug, msg, *args):
        if self._log:
            if debug:
                self._log.debug("[%s] %s" % (self._log_id, msg), *args)
            else:
                self._log.info("[%s] %s" % (self._log_id, msg), *args)

    def __init__(self, definition, action_handler, log, log_id, sum_stats_group=None):
        self._definition = definition
        self._log = log
        self._log_id = log_id
        self._state_enum = definition.state_enum
        self._event_enum = definition.event_enum
        self._transitions = definition.transitions
        self._state_actions = definition.state_actions
        self._verbose_events = definition.verbose_events
        self._state = None
        self._last_state_change_time = time.time()
        self._action_handler = action_handler
        self._records = collections.deque([], _MAX_RECORDS)
        self._verbose_records = collections.deque([], _MAX_RECORDS)
        self._current_record = None
        self._verbose_records_skipped = 0
        self._stats_group = stats.Group(sum_stats_group)
        self._event_counters = {}
        self._init_event_counters()             # Indexed by event
        self._state_entry_counters = {}         # Indexed by state
        self._state_exit_counters = {}          # Indexed by state
        self._transition_counters = {}          # Indexed by (from_state, to_state)
        self._event_transition_counters = {}    # Indexed by (from_state, event, to_state)
        self.info("Create FSM")

    def _init_event_counters(self):
        for event in self._event_enum:
            counter = stats.Counter(self._stats_group, "Events " + _event_to_name(event), "Event")
            self._event_counters[event] = counter

    def start(self):
        self._state = self._definition.initial_state
        self._last_state_change_time = time.time()
        self.info("Start FSM, state=%s", self._state.name)
        # Record start state and start state entry actions as from-state=None, and event=None
        self._current_record = FsmRecord(self, None, None, False, 0.0)
        start_time = time.monotonic()
        self._current_record.to_state = self._state
        self.state_entry_actions_and_counter(self._state)
        self._current_record.processing_time = time.monotonic() - start_time
        self.store_current_record()

    def push_event(self, event, event_data=None):
        fsm = self
        event_tuple = (fsm, event, event_data, time.monotonic())
        if self._current_record is not None:
            # We are pushing an event to an FSM which is in the middle of executing a transaction.
            # We conclude that the FSM is executing an action which pushes an event back to the same
            # FSM instance, hence it is a chained event. (This logic only holds in a single-threaded
            # application, which is what we currently have.)
            self._chained_event_queue.append(event_tuple)
            self._current_record.actions_and_pushed_events.append(event.name)
        else:
            # Normal (external) event
            self._event_queue.append(event_tuple)
            verbose = (event in self._verbose_events)
            self.info_or_debug(verbose, "FSM push event, event=%s", event.name)

    @staticmethod
    def events_pending():
        return Fsm._chained_event_queue or Fsm._event_queue

    @staticmethod
    def process_queued_events():
        while True:
            if Fsm._chained_event_queue:
                event_tuple = Fsm._chained_event_queue.popleft()
            elif Fsm._event_queue:
                event_tuple = Fsm._event_queue.popleft()
            else:
                return
            fsm = event_tuple[0]
            event = event_tuple[1]
            event_data = event_tuple[2]
            schedule_time = event_tuple[3]
            fsm.process_event(event, event_data, schedule_time)

    def invoke_actions(self, actions, event_data=None):
        for action in actions:
            if self._current_record:
                self._current_record.actions_and_pushed_events.append(_action_to_name(action))
            if event_data:
                action(self._action_handler, event_data)
            else:
                action(self._action_handler)

    def state_entry_actions_and_counter(self, state):
        # Update state entry counter
        if state not in self._state_entry_counters:
            description = "Enter {}".format(_state_to_name(state))
            self._state_entry_counters[state] = stats.Counter(self._stats_group, description,
                                                              "Entry", "Entries")
        self._state_entry_counters[state].increase()
        # Invoke the state entry actions
        if state in self._state_actions:
            (state_entry_actions, _) = self._state_actions[state]
            self.invoke_actions(state_entry_actions)

    def state_exit_actions_and_counter(self, state):
        # Update state exit counter
        if state not in self._state_exit_counters:
            description = "Exit {}".format(_state_to_name(state))
            self._state_exit_counters[state] = stats.Counter(self._stats_group, description, "Exit")
        self._state_exit_counters[state].increase()
        # Invoke the state exit actions
        if state in self._state_actions:
            (_, state_exit_actions) = self._state_actions[state]
            self.invoke_actions(state_exit_actions)

    def store_current_record(self):
        record = self._current_record
        assert record is not None
        self._verbose_records.appendleft(record)
        if record.verbose:
            self._verbose_records_skipped += 1
        else:
            record.skipped = self._verbose_records_skipped
            self._verbose_records_skipped = 0
            self._records.appendleft(record)
        # TODO check for will log before calling log_str
        self.info_or_debug(record.verbose, record.log_str())
        # Also count the transition for statistics. We create a counter on the fly the first time
        # a particular transition (from-state, to-state) has been seen to avoid have N^2 counters
        # where N is the number of states.
        to_state = record.to_state
        if to_state is None:
            to_state = record.from_state
        pair = (record.from_state, to_state)
        if pair not in self._transition_counters:
            description = "Transitions {} -> {}".format(_state_to_name(record.from_state),
                                                        _state_to_name(to_state))
            self._transition_counters[pair] = stats.Counter(self._stats_group,
                                                            description,
                                                            "Transition")
        self._transition_counters[pair].increase()
        triple = (record.from_state, record.event, to_state)
        if triple not in self._event_transition_counters:
            description = ("Event-Transitions {} -[{}]-> {}"
                           .format(_state_to_name(record.from_state),
                                   _event_to_name(record.event),
                                   _state_to_name(to_state)))
            self._event_transition_counters[triple] = stats.Counter(self._stats_group,
                                                                    description,
                                                                    "Transition")
        self._event_transition_counters[triple].increase()
        self._current_record = None

    def process_event(self, event, event_data, schedule_time):
        assert self._current_record is None
        self._event_counters[event].increase()
        from_state = self._state
        verbose = (event in self._verbose_events)
        queue_time = time.monotonic() - schedule_time
        self._current_record = FsmRecord(self, from_state, event, verbose, queue_time)
        start_time = time.monotonic()
        if from_state in self._transitions:
            from_state_transitions = self._transitions[from_state]
        else:
            from_state_transitions = []
        if event in from_state_transitions:
            transition = from_state_transitions[event]
            (to_state, actions, push_events) = FsmDefinition.parse_transition(transition)
            self.invoke_actions(actions, event_data)
            for push_event in push_events:
                self.push_event(push_event, None)
            if to_state is not None:
                self._current_record.to_state = to_state
                if to_state != self._state:
                    self.state_exit_actions_and_counter(self._state)
                    self._state = to_state
                    self._last_state_change_time = time.time()
                    self.state_entry_actions_and_counter(to_state)
        else:
            self._current_record.implicit = True
        self._current_record.processing_time = time.monotonic() - start_time
        self.store_current_record()

    def history_table(self, verbose):
        tab = table.Table()
        row = [["Sequence", "Nr"],
               ["Time", "Since", "First"],
               ["Time", "Since", "Prev"],
               ["Queue", "Time"],
               ["Processing", "Time"]]
        if not verbose:
            row.append(["Verbose", "Skipped"])
        row.extend([["From", "State"],
                    "Event",
                    ["Actions and", "Pushed Events"],
                    ["To", "State"],
                    ["Implicit"]])
        tab.add_row(row)
        if verbose:
            records_to_show = self._verbose_records
        else:
            records_to_show = self._records
        if not records_to_show:
            return tab
        first_time = records_to_show[-1].time
        for index, record in enumerate(records_to_show):
            time_since_first = record.time - first_time
            try:
                prev_time = records_to_show[index + 1].time
                time_since_prev = record.time - prev_time
                time_since_prev_str = "{:06f}".format(time_since_prev)
            except IndexError:
                time_since_prev_str = ""
            row = [record.seq_nr,
                   "{:06f}".format(time_since_first),
                   time_since_prev_str,
                   "{:06f}".format(record.queue_time),
                   "{:06f}".format(record.processing_time)]
            if not verbose:
                row.append(record.skipped)
            row.extend([_state_to_name(record.from_state),
                        _event_to_name(record.event),
                        record.actions_and_pushed_events,
                        _state_to_name(record.to_state),
                        record.implicit])
            tab.add_row(row)
            prev_time = record.time
        return tab

    def stats_table(self, exclude_zero):
        return self._stats_group.table(exclude_zero, sort_by_description=True)

    def clear_stats(self):
        self._stats_group.clear()

    @property
    def state(self):
        return self._state

    def number_of_state_entries(self, state):
        if state in self._state_entry_counters:
            return self._state_entry_counters[state].value()
        else:
            return 0

    def number_of_state_exits(self, state):
        if state in self._state_exit_counters:
            return self._state_exit_counters[state].value()
        else:
            return 0

    def time_in_current_state_str(self):
        secs_in_current_state = time.time() - self._last_state_change_time
        return utils.secs_to_dmhs_str(secs_in_current_state)
