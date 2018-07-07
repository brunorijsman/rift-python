from table import Table

# TODO: Add Table class for pretty-printing tables
# TODO: Check completeness of FSM

class FiniteStateMachine:

    def make_transition_table(self, report_missing = False):
        table = Table()
        table.add_row(['From state', 'Event', 'To state', 'Actions', 'Push events'])
        for from_state in self._state_enum:
            if from_state in self._transitions:
                from_state_transitions = self._transitions[from_state]
            else:
                from_state_transitions = []
            self.add_from_transitions_to_table(table, from_state, from_state_transitions, report_missing)
        return table

    def print_transition_table(self, report_missing = False):
        table = self.make_transition_table(report_missing)
        table.print()

    def add_from_transitions_to_table(self, table, from_state, from_state_transitions, report_missing):
        for event in self._event_enum:
            if event in from_state_transitions:
                transition = from_state_transitions[event]
                self.add_transition_to_table(table, from_state, event, transition)
            else:
                if report_missing:
                    self.add_missing_transition_to_table(table, from_state, event)

    def action_to_name(self, action):
        action_name = action.__name__
        if action_name.startswith("action_"):
            action_name = action_name[len("action_"):]
        return action_name

    def event_to_name(self, event):
        return event.name

    def add_transition_to_table(self, table, from_state, event, transition):
        from_state_name = from_state.name
        event_name = event.name
        to_state = transition[0]
        if to_state == None:
            to_state_name = "-"
        else:
            to_state_name = to_state.name
        actions = transition[1]
        action_names = list(map(self.action_to_name, actions))
        if action_names == []:
            action_names = '-'
        if len(transition) > 2:
            push_events = transition[2]
        else:
            push_events = []
        push_event_names = list(map(self.event_to_name, push_events))
        if push_event_names == []:
            push_event_names = '-'
        table.add_row([from_state_name, event_name, to_state_name, action_names, push_event_names])

    def add_missing_transition_to_table(self, table, from_state, event):
        from_state_name = from_state.name
        event_name = event.name
        table.add_row([from_state_name, event_name, '* MISSING *', Table.Format.EXTEND_LEFT_CELL, Table.Format.EXTEND_LEFT_CELL])

    def __init__(self, state_enum, event_enum, transitions):
        self._state_enum = state_enum
        self._event_enum = event_enum
        self._transitions = transitions
