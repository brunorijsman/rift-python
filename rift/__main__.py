import argparse
import logging
import os

import config
import constants
import engine
import packet_common

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
    parser.add_argument(
        'configfile',
        nargs='?',
        default='',
        help='Configuration filename')
    passive_group = parser.add_mutually_exclusive_group()
    passive_group.add_argument(
        '-p',
        '--passive',
        action="store_true",
        help='Run only the nodes marked as passive')
    passive_group.add_argument(
        '-n',
        '--non-passive',
        action="store_true",
        help='Run all nodes except those marked as passive')
    parser.add_argument(
        '-l',
        '--log-level',
        type=log_level,
        default='info',
        help='Log level (debug, info, warning, error, critical)')
    telnet_group = parser.add_mutually_exclusive_group()
    telnet_group.add_argument(
        '-i',
        '--interactive',
        action="store_true",
        help='Start Command Line Interface (CLI) on stdin/stdout instead of port')
    telnet_group.add_argument(
        '--telnet-port-file',
        help='Write telnet port to the specified file')
    parser.add_argument(
        '--ipv4-multicast-loopback-disable', action="store_true",
        help='Disable IPv4 loopback on multicast send sockets')
    parser.add_argument(
        '--ipv6-multicast-loopback-disable', action="store_true",
        help='Disable IPv6 loopback on multicast send sockets')
    args = parser.parse_args()
    return args

def parse_environment_variables(args):
    args.passive_nodes = os.getenv("RIFT_PASSIVE_NODES", "").split(",")

def run_which_nodes(parsed_args):
    if parsed_args.passive:
        return constants.ActiveNodes.ONLY_PASSIVE_NODES
    elif parsed_args.non_passive:
        return constants.ActiveNodes.ALL_NODES_EXCEPT_PASSIVE_NODES
    else:
        return constants.ActiveNodes.ALL_NODES

def ipv4_multicast_loopback(parsed_args):
    if parsed_args.ipv4_multicast_loopback_disable:
        return False
    else:
        return True

def ipv6_multicast_loopback(parsed_args):
    if parsed_args.ipv6_multicast_loopback_disable:
        return False
    else:
        return True

def main():
    args = parse_command_line_arguments()
    parse_environment_variables(args)
    parsed_config = config.parse_configuration(args.configfile)
    packet_common.add_missing_methods_to_thrift()
    eng = engine.Engine(run_which_nodes=run_which_nodes(args),
                        passive_nodes=args.passive_nodes,
                        interactive=args.interactive,
                        telnet_port_file=args.telnet_port_file,
                        ipv4_multicast_loopback=ipv4_multicast_loopback(args),
                        ipv6_multicast_loopback=ipv6_multicast_loopback(args),
                        log_level=args.log_level,
                        config=parsed_config)
    eng.run()

if __name__ == "__main__":
    main()
