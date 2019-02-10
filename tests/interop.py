#!/usr/bin/env python

import datetime
import os
import shutil
import subprocess
import yaml
import re

TEST_CASES = [("test_sys_2n_l0_l1.py", "2n_l0_l1.yaml", ["node1"]),
              ("test_sys_2n_l0_l1.py", "2n_l0_l1.yaml", ["node2"]),
              ("test_sys_2n_l0_l2.py", "2n_l0_l2.yaml", ["node1"]),
              ("test_sys_2n_l0_l2.py", "2n_l0_l2.yaml", ["node2"]),
              ("test_sys_2n_l1_l3.py", "2n_l1_l3.yaml", ["node1"]),
              ("test_sys_2n_l1_l3.py", "2n_l1_l3.yaml", ["node2"]),
              ("test_sys_3n_l0_l1_l2.py", "3n_l0_l1_l2.yaml", ["node1"]),
              ("test_sys_3n_l0_l1_l2.py", "3n_l0_l1_l2.yaml", ["node2"]),
              ("test_sys_3n_l0_l1_l2.py", "3n_l0_l1_l2.yaml", ["node3"]),
              ("test_sys_3n_l0_l1_l2.py", "3n_l0_l1_l2.yaml", ["node1", "node2"]),
              ("test_sys_3n_l0_l1_l2.py", "3n_l0_l1_l2.yaml", ["node2", "node3"]),
              ("test_sys_3n_l0_l1_l2.py", "3n_l0_l1_l2.yaml", ["node1", "node3"]),
              ("test_sys_2n_un_l1.py", "2n_un_l1.yaml", ["node1"]),
              ("test_sys_2n_un_l1.py", "2n_un_l1.yaml", ["node2"]),
              ("test_sys_2n_un_l2.py", "2n_un_l2.yaml", ["node1"]),
              ("test_sys_2n_un_l2.py", "2n_un_l2.yaml", ["node2"]),
              ("test_sys_2n_un_l0.py", "2n_un_l0.yaml", ["node1"]),
              ("test_sys_2n_un_l0.py", "2n_un_l0.yaml", ["node2"])]

def read_config(filename):
    with open(filename, 'r') as in_file:
        return yaml.load(in_file)

def write_config(filename, config):
    with open(filename, 'w') as out_file:
        yaml.dump(config, out_file, default_flow_style=False)

def fatal_error(msg):
    print(msg)
    exit(1)

def create_dir(dir_name):
    try:
        if not os.path.exists(dir_name):
            os.makedirs(dir_name)
    except OSError:
        fatal_error('Error: Creating directory ' + dir_name)

def mark_non_juniper_nodes_passive(config, juniper_nodes):
    for shard in config['shards']:
        for node in shard['nodes']:
            node_name = node['name']
            if node_name not in juniper_nodes:
                node['passive'] = True
            else:
                if 'passive' in node:
                    del node['passive']

def fixup_config_for_juniper(config):
    next_rx_lie_port = 21000
    next_rx_flood_port = 22000
    for shard in config['shards']:
        for node in shard['nodes']:
            if 'rx_lie_port' in node:
                node_rx_lie_port = node['rx_lie_port']
            else:
                # Version 0.6 of Juniper RIFT crashes if there is no rx_lie_port at the node level,
                # even if each interface has an rx_lie_port of its own. Work-around: generate a
                # dummy rx_lie_port for the node. It will safely be ignored because all of our
                # topologies have an rx_lie_port for each interface.
                node['rx_lie_port'] = next_rx_lie_port
                next_rx_lie_port += 1
            for intf in node['interfaces']:
                if ('rx_lie_port' not in intf) and node_rx_lie_port:
                    intf['rx_lie_port'] = node_rx_lie_port
                if 'rx_tie_port' not in intf:
                    # If the interface does not have a rx_tie_port, generate one.
                    intf['rx_tie_port'] = next_rx_flood_port
                    next_rx_flood_port += 1

def write_juniper_config(config_file_name, juniper_nodes, results_dir):
    config = read_config(config_file_name)
    mark_non_juniper_nodes_passive(config, juniper_nodes)
    fixup_config_for_juniper(config)
    juniper_config_file_name = "juniper-" + os.path.basename(config_file_name)
    juniper_config_file_name = os.path.join(results_dir, juniper_config_file_name)
    write_config(juniper_config_file_name, config)
    return juniper_config_file_name

def check_juniper_rift_in_path():
    if shutil.which("rift-environ") is None:
        fatal_error("Cannot find Juniper RIFT (rift-environ) in PATH")
        pass
    # run it and check version
    output = subprocess.check_output(["rift-environ",
                                        "--version"], universal_newlines=True)
    # print (output)
    regex = re.compile(r"^.*ersion: *(\d+)\.(\d+).*", re.RegexFlag.IGNORECASE | re.RegexFlag.MULTILINE)
    major = re.search(regex, output)
    if not major or not major.group(1):
        fatal_error("Cannot detect major version of Juniper RIFT")
        pass
    minor = major.group(2)
    major = major.group(1)
    if int(major) != 0 or int(minor) != 9:
        fatal_error("Wrong Major/Minor version of Juniper RIFT")
        pass
    pass

def check_pytest_in_path():
    if shutil.which("pytest") is None:
        fatal_error("Cannot find pytest in PATH")

def start_juniper_rift(juniper_config_file_name, test_results_dir):
    juniper_log_file_name = test_results_dir + "/juniper-rift.log"
    juniper_log_file = open(juniper_log_file_name, 'w')
    juniper_process = subprocess.Popen(["rift-environ",
                                        "-c",
                                        "-C", "node",
                                        "-C", "peering",
                                        "-C", "lies",
                                        "-C", "flood",
                                        "-C", "lsdb",
                                        "-C", "interface_manager",
                                        "-C", "path_computation",
                                        "-C", "flood_reduction",
                                        "-C", "rib",
                                        "-C", "fib",
                                        "-C", "southbound_prefixes",
                                        "-C", "thrift_services",
                                        "-C", "zero_touch_provisioning",
                                        "-vvvv",
                                        "-R", "999999",
                                        "topology", juniper_config_file_name],
                                       stdout=juniper_log_file,
                                       stderr=juniper_log_file)
    return juniper_process, juniper_log_file

def start_pytest(test_script_name, juniper_nodes, test_results_dir):
    passive_nodes = ",".join(juniper_nodes)
    env = os.environ
    env["RIFT_PASSIVE_NODES"] = passive_nodes
    env["RIFT_TEST_RESULTS_DIR"] = test_results_dir
    pytest_log_file_name = test_results_dir + "/pytest.log"
    pytest_log_file = open(pytest_log_file_name, 'w')
    pytest_process = subprocess.Popen(["pytest", "tests/" + test_script_name],
                                      env=env,
                                      stdin=pytest_log_file,
                                      stdout=pytest_log_file)
    return pytest_process, pytest_log_file

def run_test_case(test, config, juniper_nodes, results_dir):
    test_id = os.path.basename(config).replace(".yaml", "") + "-" + "-".join(juniper_nodes)
    test_results_dir = results_dir + "/" + test_id
    create_dir(test_results_dir)
    print(test_id + "... ", end="", flush=True)
    juniper_config_file_name = write_juniper_config(config, juniper_nodes, test_results_dir)
    juniper_process, juniper_log_file = start_juniper_rift(juniper_config_file_name,
                                                           test_results_dir)
    pytest_process, pytest_log_file = start_pytest(test, juniper_nodes, test_results_dir)
    success = pytest_process.wait() == 0
    result = "Pass" if success else "Fail"
    print(result)
    juniper_process.kill()
    juniper_log_file.close()
    pytest_log_file.close()

def run_all_test_cases(results_dir):
    for (test, config, juniper_nodes) in TEST_CASES:
        config = "topology/" + config
        run_test_case(test, config, juniper_nodes, results_dir)

def main():
    check_juniper_rift_in_path()
    check_pytest_in_path()
    results_dir = "interop-results-" + datetime.datetime.now().strftime("%Y-%m-%d-%H:%M:%S.%f")
    create_dir(results_dir)
    run_all_test_cases(results_dir)

if __name__ == "__main__":
    main()
