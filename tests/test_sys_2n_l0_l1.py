import time
import pexpect
import pytest

EXPECT_TIMEOUT = 3.0

def start_rift(topology, converge_secs=1.0):
    command_line = "python rift --interactive topology/{}.yaml".format(topology)
    rift = pexpect.spawn(command_line)
    time.sleep(converge_secs)
    wait_prompt(rift)
    return rift

def expect(rift, pattern):
    try:
        rift.expect(pattern, timeout=EXPECT_TIMEOUT)
    except pexpect.TIMEOUT:
        # Report the failure outside of this block, otherwise pytest reports a huge callstack
        failed = True
    else:
        failed = False
    if failed:
        pytest.fail('Timeout expecting "{}"'.format(pattern))

def wait_prompt(rift, node_name=None):
    if node_name is None:
        rift.expect("^.*> ")
    else:
        rift.expect("^{}> ".format(node_name))

def test_basic():
    _rift = start_rift("2n_l0_l1")
    # expect(rift, "Not getting this")
    # rift.sendline("show interfaces")
    # rift.expect("| if1 +| node2-if1 +| 2 +| THREE_WAY +|")
    # print("Got interface in 3way!")
    # rift.expect("node1> ")
    # print("Got prompt!")
