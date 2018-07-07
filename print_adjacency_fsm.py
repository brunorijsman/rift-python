from argparse import ArgumentParser
from interface import Interface

parser = ArgumentParser(description='Print adjacency Finite State Machine (FSM)')
parser.add_argument('--report-missing', action='store_true', help='Report missing transitions')
args = parser.parse_args()

Interface.fsm.print_transition_table(args.report_missing)
exit(0)