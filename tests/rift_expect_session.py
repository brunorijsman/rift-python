import time
import pexpect
import pytest

class RiftExpectSession:

    start_converge_secs = 3.0

    expect_timeout = 1.0

    def __init__(self, topology_file, converge_secs=start_converge_secs):
        rift_cmd = ("rift "
                    "--interactive "
                    "--log-level debug "
                    "topology/{}.yaml"
                    .format(topology_file))
        cmd = "coverage run --parallel-mode {}".format(rift_cmd)
        self._logfile = open('expect.log', 'ab')
        self._expect_session = pexpect.spawn(cmd, logfile=self._logfile)
        time.sleep(converge_secs)
        self.wait_prompt()

    def stop(self):
        # Attempt graceful exit
        self._expect_session.sendline("exit")
        # Give some time for coverage to write .coverage results file
        time.sleep(1.0)
        # Terminate it forcefully, in case the graceful exit did not work for some reason
        self._expect_session.terminate(force=True)

    def sendline(self, line):
        self._expect_session.sendline(line)

    def expect(self, pattern, timeout=expect_timeout):
        msg = "*** Expect: {}\n".format(pattern)
        self._logfile.write(msg.encode())
        try:
            self._expect_session.expect(pattern, timeout)
        except pexpect.TIMEOUT:
            # Report the failure outside of this block, otherwise pytest reports a huge callstack
            failed = True
        else:
            failed = False
        if failed:
            pytest.fail('Timeout expecting "{} (see expect.log for details)"'.format(pattern))

    def table_expect(self, pattern, timeout=expect_timeout):
        # Allow multiple spaces at end of each cell, even if only one was asked for
        pattern = pattern.replace(" |", " +|")
        # The | character is a literal end-of-cell, not a regexp OR
        pattern = pattern.replace("|", "[|]")
        return self.expect(pattern, timeout)

    def wait_prompt(self, node_name=None):
        if node_name is None:
            self.expect(".*> ")
        else:
            self.expect("{}> ".format(node_name))

    def check_adjacency_3way(self, node, interface, other_node, other_interface):
        # Construct full interface names as reported in LIE packets
        other_full_name = other_node + "-" + other_interface
        # Go to the node that we want to check
        self.sendline("set node {}".format(node))
        self.wait_prompt(node)
        # Show interfaces reports the adjacency with the other node as THREE_WAY
        self.sendline("show interfaces")
        self.table_expect("| {} +| {} +| .* +| THREE_WAY +|".format(interface, other_full_name))
        self.wait_prompt(node)
        # Show interface <interface-name> reports the adjacency with the other node as THREE_WAY
        self.sendline("show interface {}".format(interface))
        self.table_expect("Interface:")
        self.table_expect("| Interface Name | {} |".format(interface))
        self.table_expect("| State | THREE_WAY |")
        self.table_expect("| Received LIE Accepted or Rejected | Accepted |")
        self.table_expect("Neighbor:")
        self.table_expect("| Name | {} |".format(other_full_name))
        self.wait_prompt(node)

    def check_rx_offer(self, node, interface, system_id, level, not_a_ztp_offer, state, best,
                       best_3way, removed, removed_reason):
        # Go to the node that we want to check
        self.sendline("set node {}".format(node))
        # Show node reports the offers
        self.sendline("show node")
        # Look for the expected offer
        expected_offer = "| {} | {} | {} | {} | {} | {} | {} | {} | {} |".format(
            interface, system_id, level, not_a_ztp_offer, state, best, best_3way, removed,
            removed_reason)
        self.table_expect("Received Offers:")
        self.table_expect(expected_offer)
        self.wait_prompt(node)

    def check_tx_offer(self, node, interface, system_id, level, not_a_ztp_offer, state):
        # Go to the node that we want to check
        self.sendline("set node {}".format(node))
        # Show node reports the offers
        self.sendline("show node")
        # Look for the expected offer
        expected_offer = "| {} | {} | {} | {} | {} |".format(interface, system_id, level,
                                                             not_a_ztp_offer, state)
        self.table_expect("Sent Offers:")
        self.table_expect(expected_offer)
        self.wait_prompt(node)

    def check_level(self, node, configured_level, level_value):
        # Show nodes level reports the levels
        self.sendline("show nodes level")
        # Look for the expected offer
        expected_level = "| {} | .* | .* | {} | {} |".format(node, configured_level, level_value)
        self.table_expect(expected_level)
        self.wait_prompt()
