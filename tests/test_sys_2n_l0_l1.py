import time
import pexpect
import pytest

EXPECT_TIMEOUT = 3.0

def start_rift(topology, converge_secs=1.0):
    command_line = ("coverage run --parallel-mode rift --interactive topology/{}.yaml"
                    .format(topology))
    rift = pexpect.spawn(command_line)
    time.sleep(converge_secs)
    wait_prompt(rift)
    return rift

def stop_rift(rift):
    # Attempt graceful exit
    rift.sendline("exit")
    # Give some time for coverage to write .coverage results file
    time.sleep(1.0)
    # Terminate it forcefully, in case the graceful exit did not work for some reason
    rift.terminate(force=True)

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
    rift = start_rift("2n_l0_l1")
    # A very basic test for now: expect 3-way adjacency
    rift.sendline("show interfaces")
    rift.expect("| if1 +| node2-if1 +| 2 +| THREE_WAY +|")
    stop_rift(rift)
