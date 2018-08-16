# Automated Testing

## Testing Framework

Python RIFT includes a very extensive framework for fully automated testing.

There are three types of tests:

* Unit tests, which test the functionality of an individual Python module.

* System tests, which test the RIFT protocol behavior for a group of RIFT nodes in a topology.

* Interoperability tests, which test the interoperability between Python RIFT and other RIFT implementations (currently only Juniper RIFT).

Furthermore, Python RIFT uses [pylint](https://www.pylint.org/) to check the Python code for issues.

All tests can be run manually; details are provided below.

[Travis Continuous Integration (CI)](https://travis-ci.org/brunorijsman/rift-python) is used to also run pylint, all unit tests, and all system tests automatically on each github commit.

During all of the tests, the --cov option in pytest is used to measure code coverage. The code coverage results are collected and graphically reported in [codecov](https://codecov.io/gh/brunorijsman/rift-python).

## Pre-Commit Check

It is strongly recommended to run tools/pre-commit-checks before every commit to make sure that pylint, the unit tests, and the system tests will pass. Look for the `All good; you can commit.` message at the end.

<pre>
(env) $ <b>tools/pre-commit-checks</b>

--------------------------------------------------------------------
Your code has been rated at 10.00/10 (previous run: 10.00/10, +0.00)


--------------------------------------------------------------------
Your code has been rated at 10.00/10 (previous run: 10.00/10, +0.00)

======================================================= test session starts ========================================================
platform darwin -- Python 3.5.1, pytest-3.6.4, py-1.5.4, pluggy-0.7.1
rootdir: /Users/brunorijsman/rift-python, inifile:
plugins: cov-2.5.1
collected 13 items                                                                                                                 

tests/test_fsm.py ...                                                                                                        [ 23%]
tests/test_sys_2n_l0_l1.py .                                                                                                 [ 30%]
tests/test_sys_2n_l0_l2.py .                                                                                                 [ 38%]
tests/test_sys_2n_l1_l3.py .                                                                                                 [ 46%]
tests/test_sys_2n_un_l1.py .                                                                                                 [ 53%]
tests/test_sys_3n_l0_l1_l2.py .                                                                                              [ 61%]
tests/test_sys_cli_commands.py .                                                                                             [ 69%]
tests/test_table.py ....                                                                                                     [100%]

---------- coverage: platform darwin, python 3.5.1-final-0 -----------
Name                             Stmts   Miss  Cover
----------------------------------------------------
rift/__main__.py                    56     10    82%
rift/cli_listen_handler.py          28     19    32%
[...]
tests/test_sys_cli_commands.py      96      0   100%
tests/test_table.py                 32      0   100%
----------------------------------------------------
TOTAL                             2609    354    86%


==================================================== 13 passed in 99.27 seconds ====================================================
All good; you can commit.
</pre>

This currently takes about 2 minutes to complete, but that time will grow as the number of system tests increases.

## Pylint

Python RIFT uses [pylint](https://www.pylint.org/) to check all production code and all testing code for issues.

If you followed the [installation instructions](installation.md), you will have already installed pylint. If not, use pip to install it:

<pre>
$ <b>pip install pylint</b>
</pre>

To lint your code manually, use the following command. In this example we check the rift directory (where I have purposely introduce a warning). You also need to check the tests directory and the tools directory.

<pre>
(env) $ <b>pylint rift</b>
************* Module rift.config
rift/config.py:265:34: C0303: Trailing whitespace (trailing-whitespace)

-------------------------------------------------------------------
Your code has been rated at 9.99/10 (previous run: 10.00/10, -0.01)
</pre>

A perfect score (which is what you needs) looks like this:

<pre>
(env) $ pylint rift

--------------------------------------------------------------------
Your code has been rated at 10.00/10 (previous run: 10.00/10, +0.00)
</pre>

Many Python code editors (I use Visual Studio Code) have a plugin to automatically detect and report pylint warning as you enter the code. I strongly recommend using such a plugin.

Python RIFT is very pedantic about not allowig any pylint issues. Pylint is run on every github commit, and even a single warning will cause a build failure to be declared.

The pylintrc file in the home directory disables a small number of pylint warnings, and documents why they are disabled. Furtermore, a few Python files contain `# pylint: disable=...` comments to disable specific warnings, but this should be used very sparingly.

## Unit Tests

The unit tests use [pytest](https://docs.pytest.org/en/latest/) to test an individual Python module.

The unit tests are stored in the tests directory, and start with the test\_ prefix (but not the test\_sys\_ prefix, those are system tests).

Use the following command to run an individual unit test:

<pre>
(env) $ <b>pytest tests/test_fsm.py</b>
======================================================= test session starts ========================================================
platform darwin -- Python 3.5.1, pytest-3.6.4, py-1.5.4, pluggy-0.7.1
rootdir: /Users/brunorijsman/rift-python, inifile:
plugins: cov-2.5.1
collected 3 items                                                                                                                  

tests/test_fsm.py ...                                                                                                        [100%]

===================================================== 3 passed in 0.05 seconds =====================================================
</pre>

Use the following command to run all unit tests as well as all system tests (it is currently not possibly to run just the unit tests):

<pre>
(env) $ <b>pytest tests</b>
======================================================= test session starts ========================================================
platform darwin -- Python 3.5.1, pytest-3.6.4, py-1.5.4, pluggy-0.7.1
rootdir: /Users/brunorijsman/rift-python, inifile:
plugins: cov-2.5.1
collected 13 items                                                                                                                 

tests/test_fsm.py ...                                                                                                        [ 23%]
tests/test_sys_2n_l0_l1.py .                                                                                                 [ 30%]
tests/test_sys_2n_l0_l2.py .                                                                                                 [ 38%]
tests/test_sys_2n_l1_l3.py .                                                                                                 [ 46%]
tests/test_sys_2n_un_l1.py .                                                                                                 [ 53%]
tests/test_sys_3n_l0_l1_l2.py .                                                                                              [ 61%]
tests/test_sys_cli_commands.py .                                                                                             [ 69%]
tests/test_table.py ....                                                                                                     [100%]

==================================================== 13 passed in 98.54 seconds ====================================================
</pre>

Note: the reported percentages are the code coverage percentages. However, it is much easier to look at code coverage using [codecov](https://codecov.io/gh/brunorijsman/rift-python) after the code has been committed to github.

## Diagnosing Unit Test Failures

If a unit test fails, you will get output that looks similar to this (in this example, I modified the test case to make if fail on purpose):

<pre>
(env) $ pytest tests/test_fsm.py 
======================================================= test session starts ========================================================
platform darwin -- Python 3.5.1, pytest-3.6.4, py-1.5.4, pluggy-0.7.1
rootdir: /Users/brunorijsman/rift-python, inifile:
plugins: cov-2.5.1
collected 3 items                                                                                                                  

tests/test_fsm.py ..F                                                                                                        [100%]

============================================================= FAILURES =============================================================
__________________________________________________________ test_fsm_basic __________________________________________________________

dog = <tests.test_fsm.dog.<locals>.Dog object at 0x1055dd0f0>

    def test_fsm_basic(dog):
        dog.fsm_instance.start()
        # Check initial state
        assert dog.fsm_instance.state == dog.State.SITTING
        # The state entry action sit for initial state sitting should have been executed
        assert dog.sits == 1
        assert dog.total_actions == 1
        dog.reset_action_counters()
        # Since there are no events queud, nothing should happen when we process queued events
        fsm.Fsm.process_queued_events()
>       assert dog.fsm_instance.state == dog.State.BARKING
E       AssertionError: assert <State.SITTING: 1> == <State.BARKING: 2>
E        +  where <State.SITTING: 1> = <fsm.Fsm object at 0x1055dd128>.state
E        +    where <fsm.Fsm object at 0x1055dd128> = <tests.test_fsm.dog.<locals>.Dog object at 0x1055dd0f0>.fsm_instance
E        +  and   <State.BARKING: 2> = <enum 'State'>.BARKING
E        +    where <enum 'State'> = <tests.test_fsm.dog.<locals>.Dog object at 0x1055dd0f0>.State

tests/test_fsm.py:128: AssertionError
================================================ 1 failed, 2 passed in 0.13 seconds ================================================
</pre>

The line `tests/test_fsm.py:128: AssertionError` reports that there was an assertion failure (i.e. an unexpected outcome of the test case) on line 128 of file test_fsm.py.

The line `assert dog.fsm_instance.state == dog.State.BARKING` is the line of code in the test that failed.

The line `AssertionError: assert <State.SITTING: 1> == <State.BARKING: 2>` reports what the expected value and what the actual value was.

Some Python code editors (including Visual Studio Code, which I use) allow you to run test cases in the editor with a debugger so you can set breakpoints and inspect variables. This hugely helps in writing test cases and debugging test failures.``

## System Tests

The system tests create a topology of multiple RIFT nodes, and use [Python Expect](https://pexpect.readthedocs.io/en/stable/) in combination with pytest to verify whether all nodes in the topology behave as expected using the following mechanisms:

* Use *show* commands in the Command Line Interface (CLI) session to observe the state of the system (nodes, interfaces, etc.) after initial convergence and after some event (e.g. a link failure) occurred. The *show* commands in RIFT-Python provide extremely detailed output specifically for the purpose of enabling automated testing.

* Use *set* commands in the Command Line Interface (CLI) session to perform actions such as simulating a uni-directional or bi-directional link failure.

* Analyze the logs to determine whether various events (e.g. finite state machine transitions) occurred when they were expected to occur. The debug-level RIFT-Python logging is very detailed and very structured specifically for the purpose of enabling automated testing. 

The [tests directory in RIFT-Python](https://github.com/brunorijsman/rift-python/tree/master/tests) contains two helper modules (rift\_expect\_session.py and log\_expect\_session) to ease the task of writing automated tests.

The unit tests are stored in the tests directory, and start with the test\_sys\_ prefix. The naming convention for the system test files indicates the number of nodes and the level of the nodes. For example `2n_un_l1` means a topology with 2 nodes, where one node has level undefined and the other node has level 1.

Use the following command to run an individual system test:

<pre>
(env) $ pytest tests/test_sys_2n_l0_l1.py 
======================================================= test session starts ========================================================
platform darwin -- Python 3.5.1, pytest-3.6.4, py-1.5.4, pluggy-0.7.1
rootdir: /Users/brunorijsman/rift-python, inifile:
plugins: cov-2.5.1
collected 1 item                                                                                                                   

tests/test_sys_2n_l0_l1.py .                                                                                                 [100%]

==================================================== 1 passed in 18.62 seconds =====================================================
</pre>

Use the following command to run all system tests as well as all unit tests (it is currently not possibly to run just the system tests):

<pre>
(env) $ <b>pytest tests</b>
======================================================= test session starts ========================================================
platform darwin -- Python 3.5.1, pytest-3.6.4, py-1.5.4, pluggy-0.7.1
rootdir: /Users/brunorijsman/rift-python, inifile:
plugins: cov-2.5.1
collected 13 items                                                                                                                 

tests/test_fsm.py ...                                                                                                        [ 23%]
tests/test_sys_2n_l0_l1.py .                                                                                                 [ 30%]
tests/test_sys_2n_l0_l2.py .                                                                                                 [ 38%]
tests/test_sys_2n_l1_l3.py .                                                                                                 [ 46%]
tests/test_sys_2n_un_l1.py .                                                                                                 [ 53%]
tests/test_sys_3n_l0_l1_l2.py .                                                                                              [ 61%]
tests/test_sys_cli_commands.py .                                                                                             [ 69%]
tests/test_table.py ....                                                                                                     [100%]

==================================================== 13 passed in 98.54 seconds ====================================================
</pre>

## Diagnosing System Test Failures (Unexpected Show Command Output)

If a system test fails, you might get output that looks similar to this (in this example, I modified the test case to make if fail on purpose):

<pre>
(env) $ pytest tests/test_sys_2n_l0_l1.py 
======================================================= test session starts ========================================================
platform darwin -- Python 3.5.1, pytest-3.6.4, py-1.5.4, pluggy-0.7.1
rootdir: /Users/brunorijsman/rift-python, inifile:
plugins: cov-2.5.1
collected 1 item                                                                                                                   

tests/test_sys_2n_l0_l1.py F                                                                                                 [100%]

============================================================= FAILURES =============================================================
__________________________________________________________ test_2n_l0_l1 ___________________________________________________________

    def test_2n_l0_l1():
        passive_nodes = os.getenv("RIFT_PASSIVE_NODES", "").split(",")
        # Bring topology up
        res = RiftExpectSession("2n_l0_l1")
        les = LogExpectSession("rift.log")
        # Check that adjacency reaches 3-way, check offers, check levels
        if "node1" not in passive_nodes:
>           check_rift_node1_intf_up(res)

tests/test_sys_2n_l0_l1.py:175: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
tests/test_sys_2n_l0_l1.py:43: in check_rift_node1_intf_up
    interface="if1")
tests/rift_expect_session.py:91: in check_adjacency_1way
    self.table_expect("| {} | | .* | ONE_WAY |".format(interface))
tests/rift_expect_session.py:77: in table_expect
    return self.expect(pattern, timeout)
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

self = <rift_expect_session.RiftExpectSession object at 0x1056e9cf8>, pattern = '[|] if1 +[|] +[|] .* +[|] ONE_WAY +[|]'
timeout = 1.0

    def expect(self, pattern, timeout=expect_timeout):
        msg = "\n\n*** Expect: {}\n\n".format(pattern)
        self._logfile.write(msg.encode())
        try:
            self._expect_session.expect(pattern, timeout)
        except pexpect.TIMEOUT:
            # Report the failure outside of this block, otherwise pytest reports a huge callstack
            failed = True
        else:
            failed = False
        if failed:
            self.log_expect_failure()
>           pytest.fail('Timeout expecting "{} (see rift_expect.log for details)"'.format(pattern))
E           Failed: Timeout expecting "[|] if1 +[|] +[|] .* +[|] ONE_WAY +[|] (see rift_expect.log for details)"

tests/rift_expect_session.py:70: Failed
==================================================== 1 failed in 11.33 seconds =====================================================
(env) $ 
</pre>

In the above example, the line `see rift_expect.log for details` indicates that there was an unexpected output from a CLI show command.

If you open the file `rift_expect.log` and scroll to the bottom, you might see something similar to this:

<pre>
[... many lines skipped ...]

*** Expect: [|] if1 +[|] +[|] .* +[|] ONE_WAY +[|]

show interfaces
+-----------+-----------+-----------+-----------+
| Interface | Neighbor  | Neighbor  | Neighbor  |
| Name      | Name      | System ID | State     |
+-----------+-----------+-----------+-----------+
| if1       | node2-if1 | 2         | THREE_WAY |
+-----------+-----------+-----------+-----------+

node1> 

*** Did not find expected pattern

File "/Users/brunorijsman/rift-python/tests/test_sys_2n_l0_l1.py", line 175, in test_2n_l0_l1
    check_rift_node1_intf_up(res)
File "/Users/brunorijsman/rift-python/tests/test_sys_2n_l0_l1.py", line 43, in check_rift_node1_intf_up
    interface="if1")
File "tests/rift_expect_session.py", line 91, in check_adjacency_1way
    self.table_expect("| {} | | .* | ONE_WAY |".format(interface))
File "tests/rift_expect_session.py", line 77, in table_expect
    return self.expect(pattern, timeout)
File "tests/rift_expect_session.py", line 69, in expect
    self.log_expect_failure()
File "tests/rift_expect_session.py", line 53, in log_expect_failure
    for line in traceback.format_stack():
</pre>

This line shows a regular expression with the expected output:

<pre>
*** Expect: [|] if1 +[|] +[|] .* +[|] ONE_WAY +[|]
</pre>

This line shows the actual output. Here we see that we actually got `THREE_WAY` instead of the expected `ONE_WAY`:

<pre>
show interfaces
+-----------+-----------+-----------+-----------+
| Interface | Neighbor  | Neighbor  | Neighbor  |
| Name      | Name      | System ID | State     |
+-----------+-----------+-----------+-----------+
| if1       | node2-if1 | 2         | THREE_WAY |
+-----------+-----------+-----------+-----------+
</pre>

The following lines show the call stack where the test failure occured:

<pre>
File "/Users/brunorijsman/rift-python/tests/test_sys_2n_l0_l1.py", line 175, in test_2n_l0_l1
    check_rift_node1_intf_up(res)
File "/Users/brunorijsman/rift-python/tests/test_sys_2n_l0_l1.py", line 43, in check_rift_node1_intf_up
    interface="if1")
File "tests/rift_expect_session.py", line 91, in check_adjacency_1way
    self.table_expect("| {} | | .* | ONE_WAY |".format(interface))
File "tests/rift_expect_session.py", line 77, in table_expect
    return self.expect(pattern, timeout)
File "tests/rift_expect_session.py", line 69, in expect
    self.log_expect_failure()
File "tests/rift_expect_session.py", line 53, in log_expect_failure
    for line in traceback.format_stack():
</pre>

Once again, just as in the unit test section, it is extremely helpful to use a Python Editor that allows you to use an interactive debugger with breakpoints and variable inspection to debug system test failures.

## Diagnosing System Test Failures (Unexpected FSM Transition)

Alternatively, if a system test fails, you might also get output that looks similar to this (once again, I modified the test case to make if fail on purpose):

<pre>
(env) $ pytest tests/test_sys_2n_l0_l1.py 
======================================================= test session starts ========================================================
platform darwin -- Python 3.5.1, pytest-3.6.4, py-1.5.4, pluggy-0.7.1
rootdir: /Users/brunorijsman/rift-python, inifile:
plugins: cov-2.5.1
collected 1 item                                                                                                                   

tests/test_sys_2n_l0_l1.py F                                                                                                 [100%]

============================================================= FAILURES =============================================================
__________________________________________________________ test_2n_l0_l1 ___________________________________________________________

    def test_2n_l0_l1():
        passive_nodes = os.getenv("RIFT_PASSIVE_NODES", "").split(",")
        # Bring topology up
        les = LogExpectSession("rift.log")
        res = RiftExpectSession("2n_l0_l1")
        # Check that adjacency reaches 3-way, check offers, check levels
        if "node1" not in passive_nodes:
            check_rift_node1_intf_up(res)
            check_log_node1_intf_up(les)
        if "node2" not in passive_nodes:
            check_rift_node2_intf_up(res)
>           check_log_node2_intf_up(les)

tests/test_sys_2n_l0_l1.py:179: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
tests/test_sys_2n_l0_l1.py:160: in check_log_node2_intf_up
    les.check_lie_fsm_1way_bad_level("node1", "if1")  #!!! 3way
tests/log_expect_session.py:230: in check_lie_fsm_1way_bad_level
    to_state="ONE_WAY")
tests/log_expect_session.py:132: in fsm_find
    self.expect_failure(msg)
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

self = <log_expect_session.LogExpectSession object at 0x1056cfdd8>, msg = 'Did not find FSM transition for target-id node1-if1'

    def expect_failure(self, msg):
        self._results_file.write(msg)
        # Generate a call stack in rift_expect.log for easier debugging
        # But pytest call stacks are very deep, so only show the "interesting" lines
        for line in traceback.format_stack():
            if "tests/" in line:
                self._results_file.write(line.strip())
                self._results_file.write("\n")
>       assert False, msg + " (see log_expect.log for details)"
E       AssertionError: Did not find FSM transition for target-id node1-if1 (see log_expect.log for details)

tests/log_expect_session.py:39: AssertionError
==================================================== 1 failed in 11.31 seconds =====================================================
(env) $ 
</pre>

In the above example, the line `see log_expect.log for details` indicates that there was an unexpected line in the log (usually an unexpected FSM transition).

If you open the file `log_expect.log ` and scroll to the bottom, you might see something similar to this:

<pre>
[... many lines skipped ...]

Finding FSM transition:
  target-id = node1-if1
  from-state = ONE_WAY
  event = UNACCEPTABLE_HEADER
  to-state = ONE_WAY

Observed FSM transition:
  log-line-nr = 22
  sequence-nr = 3
  from-state = ONE_WAY
  event = TIMER_TICK
  actions-and-pushed-events = SEND_LIE
  to-state = None
  implicit = False

[... many lines skipped ...]

Observed FSM transition:
  log-line-nr = 216
  sequence-nr = 87
  from-state = THREE_WAY
  event = LIE_RECEIVED
  actions-and-pushed-events = process_lie
  to-state = None
  implicit = False

Did not find FSM transition for node1-if1

File "/Users/brunorijsman/rift-python/tests/test_sys_2n_l0_l1.py", line 179, in test_2n_l0_l1
    check_log_node2_intf_up(les)
File "/Users/brunorijsman/rift-python/tests/test_sys_2n_l0_l1.py", line 160, in check_log_node2_intf_up
    les.check_lie_fsm_1way_bad_level("node1", "if1")  #!!! 3way
File "tests/log_expect_session.py", line 230, in check_lie_fsm_1way_bad_level
    to_state="ONE_WAY")
File "tests/log_expect_session.py", line 132, in fsm_find
    self.expect_failure(msg)
File "tests/log_expect_session.py", line 35, in expect_failure
    for line in traceback.format_stack():
</pre>

The following lines reports the FSM transition that the test case was looking for (here the word "finding" means that the FSM transition is expected to happen at any point in the future, and the word "expecting" means that the FSM transition is expected to be the very next transition for that FSM instance in the log):

<pre>
Finding FSM transition:
  target-id = node1-if1
  from-state = ONE_WAY
  event = UNACCEPTABLE_HEADER
  to-state = ONE_WAY
</pre>

The following lines report the FSM transitions that were actually observed. Note that this only reports transitions for the same FSM instance as the FSM instance of the expected transition. For example, if we are looking for an expected FSM transition on one particular interfaces, this will only report observed FSM transitions for that same interface and not FSM transitions for nodes or other interfaces.

<pre>
Observed FSM transition:
  log-line-nr = 22
  sequence-nr = 3
  from-state = ONE_WAY
  event = TIMER_TICK
  actions-and-pushed-events = SEND_LIE
  to-state = None
  implicit = False
</pre>

The following line reports that the expected FSM transition was not observed:

<pre>
Did not find FSM transition for node1-if1
</pre>

And finally, the following lines report the call stack for the test case failure:

<pre>
File "/Users/brunorijsman/rift-python/tests/test_sys_2n_l0_l1.py", line 179, in test_2n_l0_l1
    check_log_node2_intf_up(les)
File "/Users/brunorijsman/rift-python/tests/test_sys_2n_l0_l1.py", line 160, in check_log_node2_intf_up
    les.check_lie_fsm_1way_bad_level("node1", "if1")  #!!! 3way
File "tests/log_expect_session.py", line 230, in check_lie_fsm_1way_bad_level
    to_state="ONE_WAY")
File "tests/log_expect_session.py", line 132, in fsm_find
    self.expect_failure(msg)
File "tests/log_expect_session.py", line 35, in expect_failure
    for line in traceback.format_stack():
</pre>

## Interoperability Tests

The interoperability tests build upon the system tests. The interoperability tests run the exact same topologies and test cases as in the system tests, except that one or more RIFT-Python nodes are replaced by RIFT-Juniper nodes.

To run the interoperability tests, first make sure that the RIFT-Python executable (rift-environ) is in your search path (PATH). Then run the `test/interop.py' script:

<pre>
@@@
</pre>

This currently takes about 3 minutes to complete (but it will take longer when I introduce more test cases).

Each line of output reports whether or not a particular interop test case passed or failed.

The naming convention for interop test cases is the topology plus a list of nodes that are running as RIFT-Juniper nodes. For example, test case `2n_l0_l1-node2` is topology `2n_l0_l1` with node2 running as a RIFT-Juniper node. As another example, test case `3n_l0_l1_l2-node1-node2` is topology `3n_l0_l1_l2` where node1 and node2 are running as RIFT-Juniper nodes.

## Diagnosing Interoperability Test Failures

Running an interop test suite, creates a directory whose name is `interop-results` followed by a timestamp, for example `interop-results-2018-08-16-13:26:24.651390`. This directory contains one subdirectory for each interop test case in the suite, for example:

<pre>
(env) $ <b>ls -1 interop-results-2018-08-16-13\:26\:36.688356/</b>
2n_l0_l1-node1
2n_l0_l1-node2
2n_l0_l2-node1
2n_l0_l2-node2
2n_l1_l3-node1
2n_l1_l3-node2
2n_un_l1-node1
2n_un_l1-node2
3n_l0_l1_l2-node1
3n_l0_l1_l2-node1-node2
3n_l0_l1_l2-node2
3n_l0_l1_l2-node2-node3
3n_l0_l1_l2-node3
</pre>

Each of these subdirectories contains all the files necessary to debug why a particular test case failed:

<pre>
(env) $ <b>ls -1 interop-results-2018-08-16-13\:26\:36.688356/2n_l0_l1-node1</b>
juniper-2n_l0_l1.yaml
juniper-rift.log
pytest.log
rift_expect.log
</pre>

## Log Visualization Tool

Once you start testing non-trivial topologies, it becomes extremely difficult to read the log files and to undertand what is really happening.

The [Log Visualization Tool](log-visualization.md) converts a log file into a graphical ladder diagram, which is _much_ easier to understand.

## Temporary Files

The automated tests generate many temporary files:

* The `rift.log` file store the RIFT-Python logs
* The `rift.log.html` file store the RIFT-Python log visualization
* The `rift_expect.log` file stores information to help debug system test failures (unexpected CLI output)
* The `log_expect.log` file stores information to help debug system test failures (unexpected FSM transition in log)
* The `interop-results-*` directories contain information to help debug interop test failures
* The `.coverage.*` files store code coverage data

The script `tools/cleanup` cleans up all these temporary files. There is also a `.gitignore` file to ignore these files for git commits.

## Continuous Integration

I use [Travis Continuous Integration (CI)](https://travis-ci.org/brunorijsman/rift-python) For every commit, Travis CI automatically runs pylint, the full unit test suite, and the full system test suite. The interoperability test suite is not automatically run - it must be run manually.

I use [codecov](https://codecov.io/gh/brunorijsman/rift-python) for visualizing the code coverage results.

See [Continuous Integration](continuous-integration.md) for more details.