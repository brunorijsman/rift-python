# Command-Line Options

## Starting the RIFT protocol engine

Go to the top of the directory where the rift-python repository was cloned (in this example we
assume it was cloned into your home directory):

<pre>
$ <b>cd ${HOME}/rift-python</b>
</pre>

Make sure your virtual environment is activated. See [installation instructions](installation.md)
for instructions on how to setup your virtual environment.

<pre>
$ <b>source env/bin/activate</b>
(env) $ 
</pre>

Start the rift package:

<pre>
(env) $ <b>python rift</b>
Command Line Interface (CLI) available on port 61375
</pre>

As explained in the [Command Line Interface (CLI)](command-line-interface.md) documentation,
you can Telnet to the reported port number (61375 in the above example) to access the CLI.

Press Control-C to stop the RIFT protocol engine:

<pre>
(env) $ python rift
Command Line Interface (CLI) available on port 61375
<b>^C</b>
Traceback (most recent call last):
  File "main.py", line 47, in <module>
    rift_object.run()
  File "/Users/brunorijsman/rift/rift.py", line 61, in run
    scheduler.scheduler.run()
  File "/Users/brunorijsman/rift/scheduler.py", line 32, in run
    rx_ready, tx_ready, _ = select.select(self._rx_sockets, self._tx_sockets, [], timeout)
KeyboardInterrupt
</pre>

## Help

The command-line option "<b>-h</b>" or "<b>--help</b>" displays help text about the available
command-line options:

Example:

<pre>
(env) $ <b>python rift --help</b>
usage: rift [-h] [-p | -n] [-l LOG_LEVEL] [-i] [configfile]

Routing In Fat Trees (RIFT) protocol engine

positional arguments:
  configfile            Configuration filename

optional arguments:
  -h, --help            show this help message and exit
  -p, --passive         Run only the nodes marked as passive
  -n, --non-passive     Run all nodes except those marked as passive
  -l LOG_LEVEL, --log-level LOG_LEVEL
                        Log level (debug, info, warning, error, critical)
  -i, --interactive     Start Command Line Interface (CLI) on stdin/stdout
                        instead of port
  --multicast-loopback-enable
                        Enable IP_MULTICAST_LOOP option on multicast send
                        sockets
  --multicast-loopback-disable
                        Disable IP_MULTICAST_LOOP option on multicast send
                        sockets                        
</pre>

## Configuration file

If you start the RIFT protocol engine without any command-line arguments it starts a single RIFT
node which runs on Ethernet interface "en0".

Note: en0 is the name of the Ethernet interface on a Macbook. A future version of the code will
pick the default Ethernet interface in a more portable way.

You can provide the name of a configuration file when you start the RIFT protocol engine:

<pre>
(env) $ <b>python rift topology/two_by_two_by_two.yaml</b>
Command Line Interface (CLI) available on port 49178
</pre>

The configuration file specifies a specifies the configuration attributes for the RIFT protocol 
instance, including the attribute of the RIFT node and the RIFT interfaces.

It is also possible to configure multiple RIFT nodes in the configuration file. This is used to build
simulated network topologies that can be tested on a single physical computer. In the above example,
the configuration file "two_by_two_by_two.yaml" contains 10 simulated nodes with names core_1, core_2,
agg_101, agg_102, etc.

## Interactive mode

By default, when you start the RIFT engine, it reports a port number on which it is listening for
incoming Command Line Interface (CLI) sessions:

<pre>
(env) $ <b>python rift topology/two_by_two_by_two.yaml</b>
Command Line Interface (CLI) available on port 49697
</pre>

You can connect to the CLI using Telnet using the reported port:

<pre>
$ <b>telnet localhost 49697</b>
Trying ::1...
telnet: connect to address ::1: Connection refused
Trying 127.0.0.1...
Connected to localhost.
Escape character is '^]'.
agg_101> 
</pre>

This mode of operation is called the non-interactive mode because the RIFT engine does not 
interact directly with the user; all interactions happen through a Telnet session. As a result,
the RIFT engine can run as a daemon.

The command-line option "<b>-i</b>" or "<b>--interactive</b>" runs the RIFT engine in interactive
mode. In the interactive mode it is not possible to connect to the RIFT engine using Telnet;
instead the RIFT engine itself provides the CLI on stdin and stdout:

<pre>
(env) $ <b>python rift --interactive topology/two_by_two_by_two.yaml</b>
agg_101> 
</pre>

## Passive and non-passive nodes

The command-line option "<b>-p</b>" or "<b>--passive</b>" runs only those RIFT nodes in the
configuration file that are marked as "passive".

The command-line option "<b>-n</b>" or "<b>--non-passive</b>" runs only those RIFT nodes in the
configuration file that are *not* marked as "passive".

These two command line options are intended for interoperability testing between Python RIFT (this
implementation) and other implementations that also understand the same configuration file format,
such as the Juniper RIFT implementation. Both implementation can read the same configuration file;
one implementation can run the passive nodes and the other implementation can run the non-passive
nodes.

<pre>
(env) $ <b>python rift --passive topology/two_by_two_by_two_ztp.yaml</b>
Command Line Interface (CLI) available on port 52482
</pre>

## Multicast loopback

If the RIFT engine runs a multi-node topology on a single host, then every multicast packet which is sent by a node on the host needs to be received exactly once by another node running on the same host.

When a node sends a single multicast packet on a transmit socket, it may be received zero times, one time, or two times on a receive socket on the same host.

The exact behavior depends on a number of factors:

* Whether or not the IP\_MULTICAST\_LOOP socket option is enabled on the sending socket.

* The make, model, and configuration of router to which the host is connected.

* Possibly also the operating system running on the host.

See [this StackOverflow question](http://bit.ly/multicast-duplication) for more details.

By default, the RIFT code uses an auto-detection mechanism to figure out whether or not it needs to enable the IP\_MULTICAST\_LOOP flag on transmit sockets.

The auto-detect mechanism uses the following rules:

* First it disables the IP\_MULTICAST\_LOOP flag and sends a single multicast packet. It then checks how many copies of the multicast packet are received. If a single copy is received, it uses IP\_MULTICAST\_LOOP = disabled as the auto-detected value.

* Otherwise it enables the IP\_MULTICAST\_LOOP flag and sends a single multicast packet. It then checks how many copies of the multicast packet are received. If a single copy is received, it uses IP\_MULTICAST\_LOOP = enabled as the auto-detected value.

* If any other behavior is observed it generates an assertion failure with a message describing the observed behavior.

The auto-detection mechanism takes between 1 and 2 seconds to complete, which causes a noticeable delay during startup.

You can use the following command-line options to disable the auto-detection mechanism (and hence avoid the startup delay).

The command-line option "--multicast-loopback-enable" forces IP\_MULTICAST\_LOOP = enabled.

The command-line option "--multicast-loopback-disable" forces IP\_MULTICAST\_LOOP = disabled.

## Logging

The RIFT protocol engine writes log messages to the file rift.log in the same directory as where
the RIFT protocol engine was started.

Note: when the RIFT protocol engine starts, it does not erase the existing rift.log file, it just
appends to it. If you log at level DEBUG (see below) the rift.log file can become extremely large
and fill up your disk. It is recommended to configure log rotation (e.g. using Linux logrotate).

It is useful to monitor the log file as the RIFT protocol engine is running using the
<b>tail -f</b> command:

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

By default, the RIFT protocol engine only writes log messages at severity INFO and higher to the 
log file. This eliminates log messages at severity DEBUG which are used to report very common 
non-interesting events such timer tick processing, receiving and sending periodic messages, etc.

The command-line option "<b>-l</b> <i>LOG_LEVEL</i>" or "<b>--log-level</b> <i>LOG_LEVEL</i>" logs 
messages at the specified <i>LOG_LEVEL</i> or higher. Valid values for <i>LOG_LEVEL</i> are 
<b>debug</b>, <b>info</b>, <b>warning</b>, <b>error</b>, or <b>critical</b>.
