import argparse

import config
import rift

def parse_command_line_arguments():
    parser = argparse.ArgumentParser(description='Routing In Fat Trees (RIFT) protocol engine')
    parser.add_argument('configfile', nargs='?', default='', help='Configuration filename')
    passive_group = parser.add_mutually_exclusive_group()
    passive_group.add_argument('-p', '--passive', action="store_true", help='Run only the nodes marked as passive')
    passive_group.add_argument('-n', '--non-passive', action="store_true", 
        help='Run all nodes except those marked as passive')
    args = parser.parse_args()
    return args

def active_nodes(args):
    if args.passive:
        return rift.Rift.ActiveNodes.ONLY_PASSIVE_NODES
    elif args.non_passive:
        return rift.Rift.ActiveNodes.ALL_NODES_EXCEPT_PASSIVE_NODES
    else:
        return rift.Rift.ActiveNodes.ALL_NODES

if __name__ == "__main__":
    args = parse_command_line_arguments()
    config = config.parse_configuration(args.configfile)
    rift_object = rift.Rift(active_nodes(args), config)
    rift_object.run()