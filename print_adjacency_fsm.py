from argparse import ArgumentParser
from node import Node
from interface import Interface

# TODO: report flags
#       i = implicit = there is no transition for event E in state S (implicitly do nothing)
#       d = do-nothing = there is a do-nothing transition for event E in state S back to state S
#       s = state-independent = the event E is handled exactly the same in every state S and goes back to S
# TODO: report state-entry actions

if __name__ == "__main__":

    parser = ArgumentParser(description='Print adjacency Finite State Machine (FSM)')
    parser.add_argument('--report-missing', action='store_true', help='Report missing transitions')
    args = parser.parse_args()

    node = Node()
    interface = Interface("dummy", node)

    interface._fsm.print_transition_table(args.report_missing)
    exit(0)