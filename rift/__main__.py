import argparse
import logging

import config
import constants
import engine

def log_level(string):
    string = string.lower()
    if string == 'critical':
        return logging.CRITICAL
    elif string == 'error':
        return logging.ERROR
    elif string == 'warning':
        return logging.WARNING
    elif string == 'info':
        return logging.INFO
    elif string == 'debug':
        return logging.DEBUG
    else:
        msg = "{} is not a valid log level".format(string)
        raise argparse.ArgumentTypeError(msg)

def parse_command_line_arguments():
    parser = argparse.ArgumentParser(description='Routing In Fat Trees (RIFT) protocol engine')
    parser.add_argument('configfile', nargs='?', default='', help='Configuration filename')
    passive_group = parser.add_mutually_exclusive_group()
    passive_group.add_argument('-p', '--passive', action="store_true",
                               help='Run only the nodes marked as passive')
    passive_group.add_argument('-n', '--non-passive', action="store_true",
                               help='Run all nodes except those marked as passive')
    parser.add_argument('-l', '--log-level', type=log_level, default='info',
                        help='Log level (debug, info, warning, error, critical)')
    parser.add_argument('-i', '--interactive', action="store_true",
                        help='Start Command Line Interface (CLI) on stdin/stdout instead of port')
    parsed_args = parser.parse_args()
    return parsed_args

def active_nodes(parsed_args):
    if parsed_args.passive:
        return constants.ActiveNodes.ONLY_PASSIVE_NODES
    elif parsed_args.non_passive:
        return constants.ActiveNodes.ALL_NODES_EXCEPT_PASSIVE_NODES
    else:
        return constants.ActiveNodes.ALL_NODES

def main():
    args = parse_command_line_arguments()
    parsed_config = config.parse_configuration(args.configfile)
    eng = engine.Engine(active_nodes=active_nodes(args),
                        interactive=args.interactive,
                        log_level=args.log_level,
                        config=parsed_config)
    eng.run()

if __name__ == "__main__":
    main()
