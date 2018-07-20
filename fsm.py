import collections
import time

import table

# TODO: Check completeness of FSM
# TODO: Report superfluous transitions (same effect in every state)
# TODO: Report could-be-implicit transitions (no effect: no actions, no pushed events, back to same state)
# TODO: Report implicit transitions
# TODO: Have a flag to report only "interesting" transitions (e.g. no periodic time ticks)

_MAX_RECORDS = 25

def _action_to_name(action):
    action_name = action.__name__
    if action_name.startswith("action_"):
        action_name = action_name[len("action_"):]
    return action_name

def _event_to_name(event):
    return event.name

def _state_to_name(state):
    if state == None:
        # In the FSM, to-state None means no state change, so treat that special
        return 'None'
    else:
        return state.name

class FsmDefinition:

    def __init__(self, state_enum, event_enum, transitions, state_entry_actions, initial_state):
        self.state_enum = state_enum
        self.event_enum = event_enum
        self.transitions = transitions
        self.state_entry_actions = state_entry_actions
        self.initial_state = initial_state

    # Everything in this class below here is concerned with producing a human-readable textual representation of the FSM

    def states_table(self):
        tab = table.Table()
        tab.add_row(['State'])
        for state in self.state_enum:
            tab.add_row([state.name])
        return tab

    def events_table(self):
        tab = table.Table()
        tab.add_row(['Event'])
        for event in self.event_enum:
            tab.add_row([event.name])
        return tab

    def transition_table(self, report_missing = False):
        tab = table.Table()
        tab.add_row(['From state', 'Event', 'To state', 'Actions', 'Push events'])
        for from_state in self.state_enum:
            if from_state in self.transitions:
                from_state_transitions = self.transitions[from_state]
            else:
                from_state_transitions = []
            self._add_from_transitions_to_table(tab, from_state, from_state_transitions, report_missing)
        return tab

    def state_entry_actions_table(self):
        tab = table.Table()
        tab.add_row(['State', 'Actions'])
        for state in self.state_entry_actions:
            actions = self.state_entry_actions[state]
            action_names = list(map(_action_to_name, actions))
            if action_names == []:
                action_names = '-'
            tab.add_row([state.name, action_names])
        return tab

    def _add_from_transitions_to_table(self, table, from_state, from_state_transitions, report_missing):
        for event in self.event_enum:
            if event in from_state_transitions:
                transition = from_state_transitions[event]
                self._add_transition_to_table(table, from_state, event, transition)
            else:
                if report_missing:
                    self._add_missing_transition_to_table(table, from_state, event)

    def _add_transition_to_table(self, table, from_state, event, transition):
        from_state_name = from_state.name
        event_name = event.name
        to_state = transition[0]
        if to_state == None:
            to_state_name = "-"
        else:
            to_state_name = to_state.name
        actions = transition[1]
        action_names = list(map(_action_to_name, actions))
        if action_names == []:
            action_names = '-'
        if len(transition) > 2:
            push_events = transition[2]
        else:
            push_events = []
        push_event_names = list(map(_event_to_name, push_events))
        if push_event_names == []:
            push_event_names = '-'
        table.add_row([from_state_name, event_name, to_state_name, action_names, push_event_names])

    def _add_missing_transition_to_table(self, table, from_state, event):
        from_state_name = from_state.name
        event_name = event.name
        table.add_row([from_state_name, event_name, '* MISSING *', 
            Table.Format.EXTEND_LEFT_CELL, Table.Format.EXTEND_LEFT_CELL])

    def command_show_fsm(self, cli_session):
        self.command_show_states(cli_session)
        self.command_show_events(cli_session)
        self.command_show_transitions(cli_session)
        self.command_show_state_entry_actions(cli_session)

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

    def command_show_state_entry_actions(self, cli_session):
        cli_session.print("State entry actions:")
        tab = self.state_entry_actions_table()
        cli_session.print(tab.to_string())

class FsmRecord:

    _next_seq_nr = 1

    def __init__(self, fsm, from_state, event):
        self.seq_nr = FsmRecord._next_seq_nr
        FsmRecord._next_seq_nr += 1
        self.time = time.time()
        self.fsm = fsm
        self.from_state = from_state
        self.event = event
        self.actions_and_pushed_events = []
        self.to_state = None
        self.implicit = False

class Fsm:

    _event_queue = collections.deque()

    def info(self, msg):
        if self._log:
            self._log.info("[{}] {}".format(self._log_id, msg))

    def warning(self, msg):
        if self._log:
            self._log.warning("[{}] {}".format(self._log_id, msg))

    def __init__(self, definition, action_handler, log, log_id):
        self._definition = definition
        self._log = log
        self._log_id = log_id
        self._state_enum = definition.state_enum
        self._event_enum = definition.event_enum
        self._transitions = definition.transitions
        self._state_entry_actions = definition.state_entry_actions
        self._state = definition.initial_state
        self._action_handler = action_handler
        self._records = collections.deque([], _MAX_RECORDS)
        self._current_record = None
        self.info("Create FSM, state={}".format(self._state.name))
        self.invoke_state_entry_actions(self._state)

    def push_event(self, event, event_data = None):
        self.info("FSM push event, event={}".format(event.name))
        fsm = self
        event_tuple = (fsm, event, event_data)
        self._event_queue.append(event_tuple)
        if self._current_record:
            self._current_record.actions_and_pushed_events.append(event.name)

    @staticmethod 
    def process_queued_events():
        while Fsm._event_queue:
            event_tuple = Fsm._event_queue.popleft()
            fsm = event_tuple[0]
            event = event_tuple[1]
            event_data = event_tuple[2]
            fsm.process_event(event, event_data)

    def invoke_actions(self, actions, type_of_action, event_data = None):
        for action in actions:
            self.info("FSM invoke {} action, action={}".format(type_of_action, _action_to_name(action)))
            if self._current_record:
                self._current_record.actions_and_pushed_events.append(_action_to_name(action))
            if event_data:
                action(self._action_handler, event_data)
            else:
                action(self._action_handler)

    def invoke_state_entry_actions(self, state):
        if state in self._state_entry_actions:
            self.invoke_actions(self._state_entry_actions[state], "state-entry")

    def process_event(self, event, event_data):
        if event_data:
            self.info("FSM process event, state={} event={} event_data={}".format(
                self._state.name, event.name, event_data))
        else:
            self.info("FSM process event, state={} event={}".format(self._state.name, event.name))
        assert self._current_record == None
        from_state = self._state
        self._current_record = FsmRecord(self, from_state, event)
        if from_state in self._transitions:
            from_state_transitions = self._transitions[from_state]
        else:
            from_state_transitions = []
        if event in from_state_transitions:
            transition = from_state_transitions[event]
            to_state = transition[0]
            actions = transition[1]
            if len(transition) > 2:
                push_events = transition[2]
            else:
                push_events = []
            self.invoke_actions(actions, "state-transition", event_data)
            for push_event in push_events:
                self.push_event(push_event)
            if to_state != None:
                self.info("FSM transition from state {} to state {}".format(from_state.name, to_state.name))
                self._state = to_state
                self._current_record.to_state = to_state
                self.invoke_state_entry_actions(to_state)
        else:
            self.warning("FSM missing transition, state={} event={}".format(self._state.name, event.name))
            self._current_record.implicit = True
        self._records.appendleft(self._current_record)
        self._current_record = None

    def history_table(self):
        tab = table.Table()
        tab.add_row([
            ['Sequence', 'Nr'],
            ['Time', 'Delta'], 
            ['From', 'State'], 
            'Event', 
            ['Actions and', 'Pushed Events'], 
            ['To', 'State'],
            ['Implicit']])
        prev_time = time.time()
        for record in self._records:
            time_delta = prev_time - record.time
            tab.add_row([
                record.seq_nr,
                "{:06f}".format(time_delta),
                _state_to_name(record.from_state), 
                _event_to_name(record.event),
                record.actions_and_pushed_events,
                _state_to_name(record.to_state), 
                record.implicit])
            prev_time = record.time
        return tab
