import enum
import pytest

import fsm

# pylint: disable=redefined-outer-name
@pytest.fixture
def dog():

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
            self.jumps += 1

        def action_growl(self):
            self.growls += 1

        def action_bark(self):
            self.barks += 1

        def action_lick(self):
            self.licks += 1

        def action_sit(self):
            self.sits += 1

        _state_sitting_transitions = {
            Event.SEE_SQUIRL: (State.BARKING, [action_growl, action_jump], [Event.WAIT]),
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

        def __init__(self):
            self.reset_action_counters()
            self.fsm_instance = fsm.Fsm(
                definition=self.fsm_definition,
                action_handler=self,
                log=None,                   # TODO: Testing logging output
                log_id=None)

        @property
        def total_actions(self):
            return self.jumps + self.growls + self.barks + self.licks + self.sits

        def reset_action_counters(self):
            self.jumps = 0
            self.growls = 0
            self.barks = 0
            self.licks = 0
            self.sits = 0

    return Dog()

def test_states_table(dog):
    assert (dog.fsm_definition.states_table().to_string() ==
            "+--------------+\n"
            "| State        |\n"
            "+--------------+\n"
            "| SITTING      |\n"
            "+--------------+\n"
            "| BARKING      |\n"
            "+--------------+\n"
            "| WAGGING_TAIL |\n"
            "+--------------+\n")

def test_events_table(dog):
    assert (dog.fsm_definition.events_table().to_string() ==
            "+------------+---------+\n"
            "| Event      | Verbose |\n"
            "+------------+---------+\n"
            "| SEE_SQUIRL | False   |\n"
            "+------------+---------+\n"
            "| PET        | False   |\n"
            "+------------+---------+\n"
            "| WAIT       | True    |\n"
            "+------------+---------+\n")

def test_fsm_basic(dog):
    dog.fsm_instance.start()
    # Check initial state
    assert dog.fsm_instance.state == dog.State.SITTING
    # The state entry action sit for initial state sitting should have been executed
    assert dog.sits == 1
    assert dog.total_actions == 1
    dog.reset_action_counters()
    # Since there are no events queud, nothing should happen when we process queued events
    fsm.Fsm.process_queued_events()
    assert dog.fsm_instance.state == dog.State.SITTING
    assert dog.total_actions == 0
    dog.reset_action_counters()
    # Event PET in state SITTING => action lick, state SITTING
    dog.fsm_instance.push_event(dog.Event.PET)
    fsm.Fsm.process_queued_events()
    assert dog.fsm_instance.state == dog.State.SITTING
    assert dog.licks == 1
    assert dog.total_actions == 1
    dog.reset_action_counters()
    # Event SEE_SQUIRL in state SITTING => action growl, action jump, push WAIT, state BARKING
    # State entry action for state BARKING => action bark
    # Event WAIT in state BARKING => action bark, state BARKING
    dog.fsm_instance.push_event(dog.Event.SEE_SQUIRL)
    fsm.Fsm.process_queued_events()
    assert dog.fsm_instance.state == dog.State.BARKING
    assert dog.growls == 1
    assert dog.jumps == 1
    assert dog.barks == 2
    assert dog.total_actions == 4
    dog.reset_action_counters()
