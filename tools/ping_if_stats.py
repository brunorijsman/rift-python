#!/usr/bin/env python3

import argparse
import subprocess
import sys

ARGS = None

def parse_command_line_arguments():
    parser = argparse.ArgumentParser(description='Ping interface statistics')
    parser.add_argument('source-ns', help='Ping source namespace name')
    parser.add_argument('dest-ns', help='Ping destination namespace name')
    parser.add_argument('stats-ns', help='Interface statistics namespace name')
    args = parser.parse_args()
    return args

def fatal_error(error_msg):
    print(error_msg, file=sys.stderr)
    sys.exit(1)

def ping_interface_stats(source_ns, dest_ns, stats_ns):
    if not namespace_exists(source_ns):
        fatal_error('Source namespace "{}" does not exist'.format(source_ns))
    if not namespace_exists(dest_ns):
        fatal_error('Destination namespace "{}" does not exist'.format(dest_ns))
    if not namespace_exists(stats_ns):
        fatal_error('Statistics namespace "{}" does not exist'.format(stats_ns))
    if_stats_before = measure_if_stats(stats_ns)
    print(if_stats_before)
    ping(source_ns, dest_ns)

def namespace_exists(ns_name):
    try:
        result = subprocess.run(['ip', 'netns', 'list'], stdout=subprocess.PIPE)
    except FileNotFoundError:
        fatal_error('"ip" command not found')
    output = result.stdout.decode('ascii')
    ns_list_with_ids = output.splitlines()
    ns_list = [ns.split()[0] for ns in  ns_list_with_ids]
    return ns_name in ns_list

def measure_if_stats(ns_name):
    try:
        result = subprocess.run(['ip', 'netns', 'exec', ns_name, 'ifconfig'],
                                stdout=subprocess.PIPE)
    except FileNotFoundError:
        fatal_error('"ifconfig" command not found')
    output = result.stdout.decode('ascii')
    if_stats = {}
    lines = output.splitlines()
    while True:
        if not lines:
            return if_stats
        line = lines.pop(0)
        if "Link encap" not in line:
            continue
        if_name = line.split()[0]
        while True:
            if not lines:
                fatal_error("Missing RX or TX stats in output of ifconfig")
            line = lines.pop(0)
            if "RX packets" in line:
                rx_packets = line.split()[1].split(":")[1]
            if "TX packets" in line:
                tx_packets = line.split()[1].split(":")[1]
                if_stats[if_name] = (rx_packets, tx_packets)
                break

def ping(source_ns, dest_ns):
    source_lo_addr = get_loopback_address(source_ns)
    print("source_lo_addr =", source_lo_addr)
    dest_ns = get_loopback_address(source_ns)
    print("dest_ns =", dest_ns)

def get_loopback_address(ns_name):
    try:
        result = subprocess.run(['ip', 'netns', 'exec', ns_name, 'ip', 'addr', 'show', 'dev', 'lo'],
                                stdout=subprocess.PIPE)
    except FileNotFoundError:
        fatal_error('"ip" command not found')
    output = result.stdout.decode('ascii')
    for line in output:
        if "inet " in line and "scope global" in line:
            address = line.split()[1]
            return address
    fatal_error('Could not determine loopback address for namespace "{}"'.format(ns_name))
    return None  # Never reached

def main():
    # pylint:disable=global-statement
    global ARGS
    ARGS = parse_command_line_arguments()
    source_ns = getattr(ARGS, 'source-ns')
    dest_ns = getattr(ARGS, 'dest-ns')
    stats_ns = getattr(ARGS, 'stats-ns')
    ping_interface_stats(source_ns, dest_ns, stats_ns)

if __name__ == "__main__":
    main()
