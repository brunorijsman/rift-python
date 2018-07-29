# Command-Line Options

## Starting the RIFT protocol engine

Enter the following command to start the RIFT protocol engine:

<pre>
(env) $ <b>python main.py</b>
Command Line Interface (CLI) available on port 52456
</pre>

Note: you need to setup a Python virtual environment as explained in the 
[installation instructions](installation.md) before starting the RIFT protocol engine.

As explained in the [Command Line Interface (CLI)](command-line-interface.md) documentation,
you can Telnet to the reported port number (52456 in the above example) to access the CLI.

Press Control-C to stop the RIFT protocol engine:

<pre>
(env) $ python main.py
Command Line Interface (CLI) available on port 52456
<b>^C</b>
Traceback (most recent call last):
  File "main.py", line 47, in <module>
    rift_object.run()
  File "/Users/brunorijsman/rift-python/rift.py", line 61, in run
    scheduler.scheduler.run()
  File "/Users/brunorijsman/rift-python/scheduler.py", line 32, in run
    rx_ready, tx_ready, _ = select.select(self._rx_sockets, self._tx_sockets, [], timeout)
KeyboardInterrupt
</pre>

## Help

The command-line option "<b>-h</b>" or "<b>--help</b>" displays help text about the available command-line options:

Example:

<pre>
(env) $ <b>python main.py --help</b>
usage: main.py [-h] [-p | -n] [-l LOG_LEVEL] [configfile]

Routing In Fat Trees (RIFT) protocol engine

positional arguments:
  configfile            Configuration filename

optional arguments:
  -h, --help            show this help message and exit
  -p, --passive         Run only the nodes marked as passive
  -n, --non-passive     Run all nodes except those marked as passive
  -l LOG_LEVEL, --log-level LOG_LEVEL
                        Log level (debug, info, warning, error, critical)
</pre>

## Configuration file

If you start the RIFT protocol engine without any command-line arguments it starts a single RIFT
node which runs on Ethernet interface "en0".

Note: en0 is the name of the Ethernet interface on a Macbook. A future version of the code will pick the default 
Ethernet interface in a more portable way.

You can provide the name of a configuration file when you start the RIFT protocol engine:

<pre>
(env) $ <b>python main.py two_by_two_by_two.yaml</b>
Command Line Interface (CLI) available on port 49178
</pre>

The configuration file specifies a specifies the configuration attributes for the RIFT protocol instance, including 
the attribute of the RIFT node and the RIFT interfaces.

It is also possible to configure multiple RIFT nodes in the configurion file. This is used to build simulated
network topologies that can be tested on a single physical computer. In the above example, the configurion
file "two_by_two_by_two.yaml" contains 10 simulated nodes with names core_1, core_2, agg_101, agg_102, etc.

TODO: Document the syntax of the configuration file.

## Passive and non-passive

The command-line option "<b>-p</b>" or "<b>--passive</b>" runs only those RIFT nodes in the configuration file that
are marked as "passive".

The command-line option "<b>-n</b>" or "<b>--non-passive</b>" runs only those RIFT nodes in the configuration file that
are *not* marked as "passive".

These two command line options are intended for interoperability testing between Python RIFT (this implmentation) and
other implementations that also understand the same configuration file format, such as the Juniper RIFT implementation.
Both implementation can read the same configuration file; one implementation can run the passive nodes and the other
implementation can run the non-passive nodes.

<pre>
(env) $ <b>python main.py --passive two_by_two_by_two_ztp.yaml</b>
Command Line Interface (CLI) available on port 52482
</pre>

## Logging

The RIFT protocol engine writes log messages to the file rift.log in the same directory as where the RIFT protocol 
engine was started.

Note: when the RIFT protocol engine starts, it does not erase the existing rift.log file, it just appends to it.
If you log at level DEBUG (see below) the rift.log file can become extremely large and fill up your disk. It is 
recommended to configure log rotation (e.g. using Linux logrotate).

It is useful to monitor the log file as the RIFT protocol engine is running using the <b>tail -f</b> command:

<pre>
(env) $ <b>tail -f rift.log</b>
2018-07-29 13:03:20,682:INFO:node.fsm:[2001] Start FSM, state=COMPUTE_BEST_OFFER
2018-07-29 13:03:20,682:INFO:node.fsm:[2001] FSM push event, event=COMPUTATION_DONE
2018-07-29 13:03:20,682:INFO:node:[2002] Create node
2018-07-29 13:03:20,682:INFO:node.if:[2002-if_2002_201] Create interface
2018-07-29 13:03:20,682:INFO:node.if.fsm:[2002-if_2002_201] Create FSM
2018-07-29 13:03:20,682:INFO:node.if:[2002-if_2002_202] Create interface
2018-07-29 13:03:20,682:INFO:node.if.fsm:[2002-if_2002_202] Create FSM
2018-07-29 13:03:20,683:INFO:node.fsm:[2002] Create FSM
2018-07-29 13:03:20,683:INFO:node.fsm:[2002] Start FSM, state=COMPUTE_BEST_OFFER
2018-07-29 13:03:20,683:INFO:node.fsm:[2002] FSM push event, event=COMPUTATION_DONE
2018-07-29 13:05:38,323:INFO:node:[1] Create node
2018-07-29 13:05:38,324:INFO:node.if:[1-if_1_101] Create interface
2018-07-29 13:05:38,324:INFO:node.if.fsm:[1-if_1_101] Create FSM
2018-07-29 13:05:38,324:INFO:node.if:[1-if_1_102] Create interface
2018-07-29 13:05:38,325:INFO:node.if.fsm:[1-if_1_102] Create FSM
...
</pre>

By default, the RIFT protocol engine only writes log messages at severity INFO and higher to the log file.
This eliminates log messages at severity DEBUG which are used to report very common non-interesting events such
timer tick processing, receiving and sending periodic messages, etc.

The command-line option "<b>-l</b> <i>LOG_LEVEL</i>" or "<b>--log-level</b> <i>LOG_LEVEL</i>" logs messages at the 
specified <i>LOG_LEVEL</i> or higher. Valid values for <i>LOG_LEVEL</i> are <b>debug</b>, <b>info</b>,
<b>warning</b>, <b>error</b>, or <b>critical</b>.








