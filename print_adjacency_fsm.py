from argparse import ArgumentParser
from fsm import FiniteStateMachine
from interface import Interface

parser = ArgumentParser(description='Print adjacency Finite State Machine (FSM)')
parser.add_argument('--report-missing', action='store_true', help='Report missing transitions')
args = parser.parse_args()

fsm = FiniteStateMachine(
        state_enum = Interface.State, 
        event_enum = Interface.Event, 
        transitions = Interface.transitions, 
        initial_state = Interface.State.ONE_WAY,
        action_handler = None,
        log = None,
        log_id = None)
fsm.print_transition_table(args.report_missing)
exit(0)