#!/usr/bin/env python3

# pylint:disable=wrong-import-position
import sys
sys.path.append("tests")

import os
import re
import shutil

import rift_expect_session

def process_file():
    doc_file = "doc/command-line-interface.md"
    tmp_file = "doc/command-line-interface.md.new"
    backup_file = "doc/command-line-interface.md.bak"
    res = rift_expect_session.RiftExpectSession("two_by_two_by_two")
    start_regex = re.compile(".*<!-- OUTPUT-START: (.*)> (.*) -->.*")
    end_regex = re.compile(".*<!-- OUTPUT-END -->.*")
    with open('doc/command-line-interface.md', 'rt') as in_file, \
        open('doc/command-line-interface.md.new', 'wt') as out_file:
        skipping = False
        for line in in_file:
            start_match = start_regex.match(line)
            end_match = end_regex.match(line)
            if start_match:
                print(line, file=out_file, end='')
                node = start_match.group(1)
                command = start_match.group(2)
                insert_command_output(out_file, res, node, command)
                skipping = True
            elif end_match:
                print(line, file=out_file, end='')
                skipping = False
            elif not skipping:
                print(line, file=out_file, end='')
    res.stop()
    shutil.copyfile(doc_file, backup_file)
    shutil.copyfile(tmp_file, doc_file)
    os.remove(tmp_file)

def insert_command_output(out_file, res, node, command):
    print("Gathered output for:", command)
    set_node = "set node {}".format(node)
    res.sendline(set_node)
    res.expect(set_node)
    res.wait_prompt(node)
    res.sendline("{}".format(command))
    res.expect(command)
    output = res.wait_prompt(node)
    if output is None:
        print("Could not gather output of command: {}> {}".format(node, command))
        sys.exit(1)
    output = output.decode()
    output = output.split("\r\n")
    while output[0] == '':
        del output[0]
    while output[-1] == '':
        del output[-1]
    for line in output:
        print(line, file=out_file)

if __name__ == "__main__":
    process_file()
