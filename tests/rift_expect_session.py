import time
import pexpect
import pytest

class RiftExpectSession:

    START_CONVERGENCE_SECS = 3.0    # TODO: Can this be faster?

    EXPECT_TIMEOUT = 1.0

    def __init__(self, topology_file, converge_secs=START_CONVERGENCE_SECS):
        command_line = ("coverage run --parallel-mode rift --interactive topology/{}.yaml"
                        .format(topology_file))
        self._logfile = open('expect.log', 'ab')
        self._expect_session = pexpect.spawn(command_line, logfile=self._logfile)
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

    def expect(self, pattern, timeout=EXPECT_TIMEOUT):
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

    def table_expect(self, pattern, timeout=EXPECT_TIMEOUT):
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
    