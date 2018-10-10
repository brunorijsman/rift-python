import enum
import re

import pytest

import fsm

# pylint: disable=redefined-outer-name
@pytest.fixture
def dog():

    # The "dog" finite state machine:
    #
    #                 +-----------------------------------------------+
    #                 |                                               |
    #                 V                                               |
    #  +------------------------------+                               |
    #  | State         : SITTING      |------+ Event         : PET    |
    #  | Entry Actions : sit          |      | Actions       : lick   |
    #  | Exit Actions  : -            |<-----+ Chained Event : -      |
    #  +------------------------------+                               |
    #                 |                                               |
    #                 | Event         : SEE_SQUIRREL                  |
    #                 | Actions       : growl, jump                   |
    #                 | Chained Event : WAIT                          |
    #                 V                                               |
    #  +------------------------------+                               |
    #  | State         : BARKING      |------+ Event         : WAIT   |
    #  | Entry Actions : bark         |      | Actions       : bark   |
    #  | Exit Actions  : poop         |<-----+ Chained Event : -      |
    #  +------------------------------+                               |
    #    |                          ^                                 |
    #    | Event         : PET      | Event         : SEE_SQUIRREL    |
    #    | Actions       : -        | Actions       : growl           |
    #    | Chained Event : -        | Chained Event : -               |
    #    V                          |                                 |
    #  +------------------------------+                               |
    #  | State         : WAGGING_TAIL |                               |
    #  | Entry Actions : -            |                               |
    #  | Exit Actions  : -            |                               | Event         : PET
    #  +------------------------------+                               | Actions       : -
    #                 |                                               | Chained Event : -
    #                 +-----------------------------------------------+

    class Dog:

        class State(enum.Enum):
            SITTING = 1
            BARKING = 2
            WAGGING_TAIL = 3

        class Event(enum.Enum):
            SEE_SQUIRREL = 1
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

        def action_poop(self):
            self.poops += 1

        _state_sitting_transitions = {
            Event.SEE_SQUIRREL: (State.BARKING, [action_growl, action_jump], [Event.WAIT]),
            Event.PET         : (None, [action_lick])
        }

        _state_barking_transitions = {
            Event.PET : (State.WAGGING_TAIL, []),
            Event.WAIT: (State.BARKING, [action_bark])
        }

        _state_wagging_tail_transitions = {
            Event.SEE_SQUIRREL: (State.BARKING, [action_growl]),
            Event.PET         : (State.SITTING, [])
        }

        _state_actions = {
            State.SITTING: ([action_sit], []),
            State.BARKING: ([action_bark], [action_poop])
        }

        _transitions = {
            State.SITTING     : _state_sitting_transitions,
            State.BARKING     : _state_barking_transitions,
            State.WAGGING_TAIL: _state_wagging_tail_transitions
        }

        fsm_definition = fsm.FsmDefinition(
            state_enum=State,
            event_enum=Event,
            transitions=_transitions,
            initial_state=State.SITTING,
            state_actions=_state_actions,
            verbose_events=verbose_events)

        def __init__(self):
            self.reset_action_counters()
            self.fsm_instance = fsm.Fsm(
                definition=self.fsm_definition,
                action_handler=self,
                log=None,
                log_id=None)

        @property
        def total_actions(self):
            return self.jumps + self.growls + self.barks + self.licks + self.sits + self.poops

        def reset_action_counters(self):
            self.jumps = 0
            self.growls = 0
            self.barks = 0
            self.licks = 0
            self.sits = 0
            self.poops = 0

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
            "+--------------+---------+\n"
            "| Event        | Verbose |\n"
            "+--------------+---------+\n"
            "| SEE_SQUIRREL | False   |\n"
            "+--------------+---------+\n"
            "| PET          | False   |\n"
            "+--------------+---------+\n"
            "| WAIT         | True    |\n"
            "+--------------+---------+\n")

def test_transition_table(dog):
    assert (dog.fsm_definition.transition_table().to_string() ==
            "+--------------+--------------+--------------+---------+-------------+\n"
            "| From state   | Event        | To state     | Actions | Push events |\n"
            "+--------------+--------------+--------------+---------+-------------+\n"
            "| SITTING      | SEE_SQUIRREL | BARKING      | growl   | WAIT        |\n"
            "|              |              |              | jump    |             |\n"
            "+--------------+--------------+--------------+---------+-------------+\n"
            "| SITTING      | PET          | -            | lick    | -           |\n"
            "+--------------+--------------+--------------+---------+-------------+\n"
            "| BARKING      | PET          | WAGGING_TAIL | -       | -           |\n"
            "+--------------+--------------+--------------+---------+-------------+\n"
            "| BARKING      | WAIT         | BARKING      | bark    | -           |\n"
            "+--------------+--------------+--------------+---------+-------------+\n"
            "| WAGGING_TAIL | SEE_SQUIRREL | BARKING      | growl   | -           |\n"
            "+--------------+--------------+--------------+---------+-------------+\n"
            "| WAGGING_TAIL | PET          | SITTING      | -       | -           |\n"
            "+--------------+--------------+--------------+---------+-------------+\n")

def test_state_actions_table(dog):
    print(dog.fsm_definition.state_actions_table().to_string())
    assert (dog.fsm_definition.state_actions_table().to_string() ==
            "+---------+---------------+--------------+\n"
            "| State   | Entry Actions | Exit Actions |\n"
            "+---------+---------------+--------------+\n"
            "| BARKING | bark          | poop         |\n"
            "+---------+---------------+--------------+\n"
            "| SITTING | sit           | -            |\n"
            "+---------+---------------+--------------+\n")

def test_history_table(dog):
    dog.fsm_instance.start()
    fsm.Fsm.process_queued_events()
    dog.fsm_instance.push_event(dog.Event.PET)
    fsm.Fsm.process_queued_events()
    print(dog.fsm_instance.history_table(verbose=True).to_string())
    pattern = (
        ".----------.----------.---------.---------.-------.---------------.---------.----------.\n"
        ". Sequence . Time     . Verbose . From    . Event . Actions and   . To      . Implicit .\n"
        ". Nr       . Delta    . Skipped . State   .       . Pushed Events . State   .          .\n"
        ".----------.----------.---------.---------.-------.---------------.---------.----------.\n"
        ". 2        . ........ . 0       . SITTING . PET   . lick          . None    . False    .\n"
        ".----------.----------.---------.---------.-------.---------------.---------.----------.\n"
        ". 1        . ........ . 0       . None    . None  . sit           . SITTING . False    .\n"
        ".----------.----------.---------.---------.-------.---------------.---------.----------.\n"
    )
    print(re.match(pattern, dog.fsm_instance.history_table(verbose=True).to_string()))
    assert re.match(pattern, dog.fsm_instance.history_table(verbose=True).to_string())

def test_fsm_basic(dog):
    dog.fsm_instance.start()
    # Check initial state
    assert dog.fsm_instance.state == dog.State.SITTING
    # The state entry action sit for initial state sitting should have been executed
    assert dog.sits == 1
    assert dog.total_actions == 1
    dog.reset_action_counters()
    # Since there are no events queued, nothing should happen when we process queued events
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
    # Event SEE_SQUIRREL in state SITTING => action growl, action jump, push WAIT, state BARKING
    # State entry action for state BARKING => action bark
    # Event WAIT in state BARKING => action bark, state BARKING
    # Note: going from state BARKING back to BARKING, neither entry nor exit actions are executed
    dog.fsm_instance.push_event(dog.Event.SEE_SQUIRREL)
    fsm.Fsm.process_queued_events()
    assert dog.fsm_instance.state == dog.State.BARKING
    assert dog.growls == 1
    assert dog.jumps == 1
    assert dog.barks == 2
    assert dog.total_actions == 4
    dog.reset_action_counters()
    # Event PET in state BARKING => state WAGGING_TAIL
    # State exit action for state BARKING => action poop
    dog.fsm_instance.push_event(dog.Event.PET)
    fsm.Fsm.process_queued_events()
    assert dog.fsm_instance.state == dog.State.WAGGING_TAIL
    assert dog.poops == 1
    assert dog.total_actions == 1
    dog.reset_action_counters()
