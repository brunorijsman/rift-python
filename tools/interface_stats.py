#!/usr/bin/env python3

import argparse
import subprocess
import sys
import time

DEFAULT = '\033[0m'
RED = '\u001b[31m'
GREEN = '\u001b[32m'

ARGS = None
BASELINE_SECS = 10.0

MAX_RATE = 5.0

def parse_command_line_arguments():
    parser = argparse.ArgumentParser(description='Interface statistics')
    parser.add_argument('source-ns', help='Ping source namespace name')
    parser.add_argument('dest-ns', help='Ping destination namespace name')
    parser.add_argument('stats-ns', help='Interface statistics namespace name')
    args = parser.parse_args()
    return args

def fatal_error(error_msg):
    print(error_msg, file=sys.stderr)
    sys.exit(1)

def baseline_stats(stats_ns):
    if not namespace_exists(stats_ns):
        fatal_error('Statistics namespace "{}" does not exist'.format(stats_ns))
    print("Statistics during {:.1f} second baseline test:\n".format(BASELINE_SECS))
    if_stats_before = measure_if_stats(stats_ns)
    time.sleep(BASELINE_SECS)
    if_stats_after = measure_if_stats(stats_ns)
    report_interface_stats(stats_ns, if_stats_before, if_stats_after)
    print()

def ping_interface_stats(source_ns, dest_ns, stats_ns):
    if not namespace_exists(source_ns):
        fatal_error('Source namespace "{}" does not exist'.format(source_ns))
    if not namespace_exists(dest_ns):
        fatal_error('Destination namespace "{}" does not exist'.format(dest_ns))
    if not namespace_exists(stats_ns):
        fatal_error('Statistics namespace "{}" does not exist'.format(stats_ns))
    print("Statistics during ping test:\n")
    source_lo_addr = get_loopback_address(source_ns)
    dest_lo_addr = get_loopback_address(dest_ns)
    if_stats_before = measure_if_stats(stats_ns)
    (packets_transmitted, packets_received) = ping(source_ns, source_lo_addr, dest_lo_addr)
    if_stats_after = measure_if_stats(stats_ns)
    report_interface_stats(stats_ns, if_stats_before, if_stats_after)
    print()
    print("Source name space        :", source_ns)
    print("Destination name space   :", dest_ns)
    print("Statistics name space    :", stats_ns)
    print("Source address           :", source_lo_addr)
    print("Destination address      :", dest_lo_addr)
    print("Ping packets transmitted :", packets_transmitted)
    print("Ping packets received    :", packets_received)
    drops = packets_transmitted - packets_received
    color = GREEN if drops == 0 else RED
    print("Ping packets lost        : {}{}{}".format(color, drops, DEFAULT))

def report_interface_stats(stats_ns, if_stats_before, if_stats_after):
    (time_before, counters_before) = if_stats_before
    (time_after, counters_after) = if_stats_after
    if_names = list(counters_before.keys())
    if_names.sort()
    print("Namespace           Interface           TX packets  TX Rate     RX packets  RX rate")
    print("------------------  ------------------  ----------  ----------  ----------  ----------")
    for if_name in if_names:
        delta_secs = time_after - time_before
        rx_packets = counters_after[if_name][0] - counters_before[if_name][0]
        tx_packets = counters_after[if_name][1] - counters_before[if_name][1]
        if delta_secs > 0.0001:
            rx_rate = float(rx_packets) / delta_secs
            tx_rate = float(tx_packets) / delta_secs
            rx_color = GREEN if rx_rate <= MAX_RATE else RED
            tx_color = GREEN if tx_rate <= MAX_RATE else RED
            rx_rate = "{:.1f}".format(rx_rate)
            tx_rate = "{:.1f}".format(tx_rate)
        else:
            rx_rate = "-"
            tx_rate = "-"
            rx_color = DEFAULT
            tx_color = DEFAULT
        print("{:18s}  {:18s}  {:>10d}  {}{:>10s}{}  {:>10d}  {}{:>10s}{}"
              .format(stats_ns, if_name,
                      tx_packets, tx_color, tx_rate, DEFAULT,
                      rx_packets, rx_color, rx_rate, DEFAULT))

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
    counters = {}
    lines = output.splitlines()
    while True:
        if not lines:
            return (time.time(), counters)
        line = lines.pop(0)
        if "Link encap" not in line:
            continue
        if_name = line.split()[0]
        while True:
            if not lines:
                fatal_error("Missing RX or TX stats in output of ifconfig")
            line = lines.pop(0)
            if "RX packets" in line:
                rx_packets = int(line.split()[1].split(":")[1])
            if "TX packets" in line:
                tx_packets = int(line.split()[1].split(":")[1])
                counters[if_name] = (rx_packets, tx_packets)
                break

def ping(ns_name, source_lo_addr, dest_lo_addr):
    try:
        result = subprocess.run(['ip', 'netns', 'exec', ns_name, 'ping', '-f', '-W1', '-c10',
                                 '-I', source_lo_addr, dest_lo_addr],
                                stdout=subprocess.PIPE)
    except FileNotFoundError:
        fatal_error('"ping" command not found')
    output = result.stdout.decode('ascii')
    lines = output.splitlines()
    for line in lines:
        if "packets transmitted" in line:
            split_line = line.split()
            packets_transmitted = int(split_line[0])
            packets_received = int(split_line[3])
            return (packets_transmitted, packets_received)
    fatal_error('Could not determine ping statistics for namespace "{}"'.format(ns_name))
    return None  # Never reached

def get_loopback_address(ns_name):
    try:
        result = subprocess.run(['ip', 'netns', 'exec', ns_name, 'ip', 'addr', 'show', 'dev', 'lo'],
                                stdout=subprocess.PIPE)
    except FileNotFoundError:
        fatal_error('"ip" command not found')
    output = result.stdout.decode('ascii')
    lines = output.splitlines()
    for line in lines:
        if "inet " in line and "scope global" in line:
            prefix = line.split()[1]
            address = prefix.split('/')[0]
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
    baseline_stats(stats_ns)
    ping_interface_stats(source_ns, dest_ns, stats_ns)

if __name__ == "__main__":
    main()
