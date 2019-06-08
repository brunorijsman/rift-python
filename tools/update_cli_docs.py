#!/usr/bin/env python3

# pylint:disable=wrong-import-position
import sys
sys.path.append("tests")

import argparse
import copy
import os
import platform
import re
import shutil

import rift_expect_session

def parse_command_line_arguments():
    parser = argparse.ArgumentParser(description='RIFT CLI documentation generator')
    parser.add_argument(
        '-c', '--check-only',
        action="store_true",
        help='Only check for missing documentation; don\'t generate documentation')
    args = parser.parse_args()
    return args

def process_file():
    doc_file = "doc/command-line-interface.md"
    tmp_file = "doc/command-line-interface.md.new"
    backup_file = "doc/command-line-interface.md.bak"
    res = rift_expect_session.RiftExpectSession("two_by_two_by_two", log_debug=False)
    processed_commands = []
    all_commands = gather_output(res, "agg_101", "help")
    start_regex = re.compile(".*<!-- OUTPUT-START: (.*)> (.*) -->.*")
    end_regex = re.compile(".*<!-- OUTPUT-END -->.*")
    manual_regex = re.compile(".*<!-- OUTPUT-MANUAL: (.*)> (.*) -->.*")
    with open('doc/command-line-interface.md', 'rt') as in_file, \
        open('doc/command-line-interface.md.new', 'wt') as out_file:
        skipping = False
        for line in in_file:
            start_match = start_regex.match(line)
            end_match = end_regex.match(line)
            manual_match = manual_regex.match(line)
            if start_match:
                print(line, file=out_file, end='')
                node = start_match.group(1)
                command = start_match.group(2)
                insert_command_output(out_file, res, node, command)
                processed_commands.append(command)
                skipping = True
            elif end_match:
                print(line, file=out_file, end='')
                skipping = False
            elif manual_match:
                print(line, file=out_file, end='')
                node = manual_match.group(1)
                command = manual_match.group(2)
                if not ARGS.check_only:
                    print("Manual:", command)
                processed_commands.append(command)
            elif not skipping:
                print(line, file=out_file, end='')
    res.stop()
    if not ARGS.check_only:
        shutil.copyfile(doc_file, backup_file)
        shutil.copyfile(tmp_file, doc_file)
    os.remove(tmp_file)
    return check_missing_commands(all_commands, processed_commands)

def insert_command_output(out_file, res, node, command):
    if not ARGS.check_only:
        print("Process:", command)
    output = gather_output(res, node, command)
    if output:
        output[0] = output[0].strip(' \r\n')
        if output[0] == '':
            del output[0]
    if output:
        output[-1] = output[-1].rstrip(' \r\n')
        if output[-1] == '':
            del output[-1]
    print("<pre>", file=out_file)
    print("{}> <b>{}</b>".format(node, command), file=out_file)
    summarize_tables(output, out_file)
    print("</pre>", file=out_file)

def gather_output(res, node, command):
    set_node = "set node {}".format(node)
    res.sendline(set_node)
    res.expect(set_node)
    res.wait_prompt(node)
    res.sendline("{}".format(command))
    res.expect(command)
    output = copy.deepcopy(res.wait_prompt(node))
    if output is None:
        print("Could not gather output of command: {}> {}".format(node, command))
        sys.exit(1)
    output = output.decode()
    output = output.split("\r\n")
    while output and output[0] == '':
        del output[0]
    while output and output[-1] == '':
        del output[-1]
    return output

def check_missing_commands(all_commands, processed_commands):
    something_missing = False
    for command in all_commands:
        command = command.strip(' \r\n').rstrip(' \r\n')
        if command == '':
            continue
        pattern = "^{}$".format(command)
        pattern = re.sub(r"<.*?>", ".*", pattern)
        covered = False
        for processed_command in processed_commands:
            if re.match(pattern, processed_command):
                covered = True
                break
        if not covered:
            print("MISSING: {}".format(command))
            something_missing = True
    return something_missing

def summarize_tables(output, out_file):
    in_table = False
    for raw_line in output:
        line = raw_line.replace("<", "&lt;").replace(">", "&gt;")
        if line.startswith("+---"):
            if in_table:
                rows.append(current_row_lines)
            else:
                in_table = True
                separator_line = line
                rows = []
            current_row_lines = []
        elif '|' in line:
            assert in_table
            current_row_lines.append(line)
        else:
            if in_table:
                print_table_summary(rows, separator_line, out_file)
                in_table = False
            print(line, file=out_file)
    if in_table:
        print_table_summary(rows, separator_line, out_file)

def print_table_summary(rows, separator_line, out_file):
    max_top_rows = 5
    row_nr = 0
    nr_rows = len(rows)
    dots_line = None
    for row in rows:
        if (row_nr < max_top_rows) or (row_nr == nr_rows-1):
            print(separator_line, file=out_file)
            for row_line in row:
                print(row_line, file=out_file)
        elif row_nr == max_top_rows:
            print(separator_line, file=out_file)
            dots_line = separator_line.replace('-', ' ').replace('+', '.')
            print(dots_line, file=out_file)
            print(dots_line, file=out_file)
        row_nr += 1
    print(separator_line, file=out_file)

if __name__ == "__main__":
    ARGS = parse_command_line_arguments()
    if not ARGS.check_only:
        if platform.system() != "Linux":
            print("Must be on Linux to generate documentation")
            exit(1)
    SOMETHING_MISSING = process_file()
    if SOMETHING_MISSING:
        exit(1)
    else:
        exit(0)
