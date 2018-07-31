import enum
import fsm

class Dog:

    class State(enum.Enum):
        SITTING = 1
        BARKING = 2
        WAGGING_TAIL = 3

    class Event(enum.Enum):
        SEE_SQUIRL = 1
        PET = 2
        WAIT = 3

    verbose_events = [Event.WAIT]

    def action_jump(self):
        pass

    def action_growl(self):
        pass

    def action_bark(self):
        pass

    def action_lick(self):
        pass

    def action_sit(self):
        pass

    _state_sitting_transitions = {
        Event.SEE_SQUIRL: (State.BARKING, [action_growl, action_jump]),
        Event.PET       : (None, [action_lick])
    }

    _state_barking_transitions = {
        Event.PET : (State.WAGGING_TAIL, []),
        Event.WAIT: (State.BARKING, [action_bark])
    }

    _state_wagging_tail_transitions = {
        Event.SEE_SQUIRL: (State.BARKING, [action_growl]),
        Event.PET       : (State.SITTING, [])
    }

    _state_entry_actions = {
        State.SITTING: [action_sit],
        State.BARKING: [action_bark]
    }

    _transitions = {
        State.SITTING: _state_sitting_transitions,
        State.BARKING: _state_barking_transitions,
        State.WAGGING_TAIL: _state_wagging_tail_transitions
    }

    fsm_definition = fsm.FsmDefinition(
        state_enum=State,
        event_enum=Event,
        transitions=_transitions,
        state_entry_actions=_state_entry_actions,
        initial_state=State.SITTING,
        verbose_events=verbose_events)

def test_fsm_definition_states_table():
    assert (Dog.fsm_definition.states_table().to_string() ==
        "+--------------+\n"
        "| State        |\n"
        "+--------------+\n"
        "| SITTING      |\n"
        "+--------------+\n"
        "| BARKING      |\n"
        "+--------------+\n"
        "| WAGGING_TAIL |\n"
        "+--------------+\n")

def test_fsm_definition_events_table():
    assert (Dog.fsm_definition.events_table().to_string() ==
        "+------------+---------+\n"
        "| Event      | Verbose |\n"
        "+------------+---------+\n"
        "| SEE_SQUIRL | False   |\n"
        "+------------+---------+\n"
        "| PET        | False   |\n"
        "+------------+---------+\n"
        "| WAIT       | True    |\n"
        "+------------+---------+\n")