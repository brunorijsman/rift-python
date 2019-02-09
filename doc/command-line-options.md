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
usage: rift [-h] [-p | -n] [-l LOG_LEVEL]
            [-i | --telnet-port-file TELNET_PORT_FILE]
            [--ipv4-multicast-loopback-disable]
            [--ipv6-multicast-loopback-disable]
            [configfile]

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
  --telnet-port-file TELNET_PORT_FILE
                        Write telnet port to the specified file
  --ipv4-multicast-loopback-disable
                        Disable IPv4 loopback on multicast send sockets
  --ipv6-multicast-loopback-disable
                        Disable IPv6 loopback on multicast send sockets
</pre>

## Configuration file (also known as topology file)

If you start the RIFT protocol engine without any command-line arguments it starts a single RIFT
node which runs on Ethernet interface "en0".

Note: en0 is the name of the Ethernet interface on a Macbook. A future version of the code will
automatically detect all Ethernet interfaces on the host platform.

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

## Stand-alone mode versus topology mode

If the RIFT engine is started without a topology file, or if the topology file only contains a
single node, then the RIFT engine runs in "stand-alone mode". The stand-alone mode is intended for
running RIFT in production networks.

If the RIFT engine is started with a topology file, and the topology file contains multiple nodes,
then the RIFT engine runs in "topology mode".  The topology node is intended for testing simulated
multi-node topologies.

## Simulated interfaces versus real interfaces

When the RIFT engine runs in stand-alone mode, all interfaces names in RIFT correspond to the
interface names of real Ethernet interfaces on the host platform.

When the RIFT engine runs in topology mode, all interfaces in RIFT are "simulated": the interface
names in RIFT are fictitious and do not correspond to the interface names of real Ethernet
interfaces on the host platform.

When the interfaces are simulated, a single real physical Ethernet interface is chosen on the host
platform, which is referred to as "the physical interface" (as opposed to simulated interfaces).

All RIFT packets that are sent from one simulated interface to another simulated interfaces are
in actuality sent over the one and only physical interface. Thus, one single physical interface
is used to simulate all simulated interfaces in the simulated RIFT topology. To separate traffic
on one simulated interface from traffic of another simulated interface on the same underlying
physical interface, it is necessary to conifgure separate multicast IP addresses per node, and
separate UDP ports per interface.

The topology mode allows a multi-node topology to be simulated in a single Python process. However,
using different multicast addresses and UDP ports makes the simulation somewhat unrealistic (many
subtle bugs are caused by running the same multicast group on multiple interfaces). Also, simulating
large topologies can be problematic because the Python RIFT engine is single-threaded. For these
reasons, we also provide the "topology_generator" tool with the "--netns-per-node" option that
can simulate multi-node topologies more realistically by running each RIFT node in a separate
Python process in its own network namespace, and by implementing the node-to-node Ethernet links
as virtual Ethernet (veth) pairs. See the documentation for the topology_generator tool for more
details.

## Interactive mode verus non-interactive mode

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

In interactive mode, when you exit the CLI running on stdin and stdout using either the "exit" or 
the "stop" command, the RIFT engine automatically stops. 

In both interactive and non-interactive mode, when you exit a Telnet CLI session using the "exit" 
command, the RIFT engine continues to run. But when you exit a Telnet CLI session using the "stop"
command, the RIFT engine stops.

## Telnet port file

As mentioned above, by default, when you start the RIFT engine, it reports a port number on which
it is listening for incoming Command Line Interface (CLI) sessions:

<pre>
(env) $ <b>python rift topology/two_by_two_by_two.yaml</b>
Command Line Interface (CLI) available on port 49697
</pre>

You can use the <b>--telnet-port-file</b> <i>filename</i> option to write this port number to a
file instead of reporting it on stdout. 
This is useful when using a script to connect to the RIFT engine.

For example, you can start the RIFT engine in the background:

<pre>
(env) $ <b>python rift --telnet-port-file /tmp/rift-telnet-port topology/two_by_two_by_two.yaml < /dev/null & </b>
[1] 20717
(env) $ 
</pre>

You can then connect to the RIFT engine as follows:

<pre>
(env) $ <b>telnet localhost $(cat /tmp/rift-telnet-port)</b>
Trying ::1...
telnet: connect to address ::1: Connection refused
Trying 127.0.0.1...
Connected to localhost.
Escape character is '^]'.
agg_101> 
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

When RIFT runs in topology mode, a packet that is sent from one simulated interface to another
simulated interface is actually sent over the underlying physical interface (typically "en0" on
macOS and "eth0" on Linux). Both the sending socket on the sending simulated interface and the
receiving socket on the receiving simulated interface are bound to the same underlying physical
interface.

For multicast to work correctly in this scenario, we may or may not need to enable "multicast
loopback" on the sending socket.

 * Usually, we need to enable multicast loopback on the socket. This will cause the kernel in the
   host platform take the multicast packet that are sent on a send socket and loop them back to
   receive sockets on the same physical interface.

 * However, sometims (this is not common) when the external router receives a multicast packet from
   the physical interface on the host, it will deliver it back to the same physical interface on the
   same host. In this case, we do not want to enable "multicast loopback" on the host (if we do,
   RIFT-Python will receive two copies of each sent multicast packet).

Thus, whether or not multicast loopback needs to be enabled depends on the make, model, and
configuration of router to which the host is connected. In particular, whether or not the router
correctly implements IGMP for IPv4 and/or MLD for IPv6. Many low-end home routers have buggy 
multicast implementations.

Note that multicast loopback can be enabled or disabled separately for IPv4 and IPv6.

* Enables multicast loopback for both IPv4 and IPv6 in topology mode.

* Disables multicast loopback for both IPv4 and IPv6 in stand-alone mode.

You can use the following command-line options to disable multicast loopback:

* The command-line option "--ipv4-multicast-loopback-disable" disables IPv4 multicast loopback.

* The command-line option "--ipv6-multicast-loopback-disable" disables IPv6 multicast loopback.

You can use the "multicast_checks" tool to probe your external router and to determine whether or
not multicast loopback is needed for topology mode:

<pre>
(env) $ <b>tools/multicast_checks.py</b>
Testing on interface: en0
IPv4 loopback needed: True
IPv6 loopback needed: True
</pre>

 This tool works as follows:

 * First, the tool disables loopback, sends a single multicast packet, and checks whether it
   receives one copy of the multicast packet on a different receiver socket on the same physical
  interface. If so, it means that multicast loopback is not needed (i.e. must be disabled).

 * Then the tool enables loopback, and again sends a single multcast packet. It verifies that it
   now receives exactly one copy of the multicast packet on a different receiver socket on the same physical interface.

 * Otherwise, i.e. if zero copies are received or if multiple copies are received in both cases,
   the tool reports "unexpected behavior".

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

## Reporting options

All the options discussed above (stand-alone mode vs topology-mode, interactive mode vs
non-interactive mode, etc.) can be viewed on a running RIFT-Python engine using the "show engine"
command:

<pre>
agg_101> <b>show engine</b>
+-------------------------+-----------+
| Stand-alone             | False     |
| Interactive             | True      |
| Simulated Interfaces    | True      |
| Physical Interface      | en0       |
| Telnet Port File        | None      |
| IPv4 Multicast Loopback | True      |
| IPv6 Multicast Loopback | True      |
| Number of Nodes         | 10        |
| Transmit Source Address | 127.0.0.1 |
+-------------------------+-----------+
</pre>