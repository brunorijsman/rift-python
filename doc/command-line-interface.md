# Command Line Interface (CLI) Reference

* [Connect to the CLI](#connect-to-the-cli)
* [Entering CLI commands](#entering-cli-commands)
* [Command Line Interface Commands](#command-line-interface-commands)
  * [exit](#exit)
  * [set interface <i>interface</i> failure <i>failure</i>](#set-interface-interface-failure-failure)
  * [set level <i>level</i>](#set-level-level)
  * [set node <i>node</i>](#set-node-node)
  * [show engine](#show-engine)
  * [show forwarding](#show-forwarding)
  * [show forwarding prefix <i>prefix</i>](#show-forwarding-prefix-prefix)
  * [show fsm <i>fsm</i>](#show-fsm-fsm)
  * [show interface <i>interface</i>](#show-interface-interface)
  * [show interface <i>interface</i> fsm history](#show-interface-interface-fsm-history)
  * [show interface <i>interface</i> fsm verbose-history](#show-interface-interface-fsm-verbose-history)
  * [show interface <i>interface</i> queues](#show-interface-interface-queues)
  * [show interface <i>interface</i> sockets](#show-interface-interface-sockets)
  * [show interfaces](#show-interfaces)
  * [show kernel addresses](#show-kernel-addresses)
  * [show kernel links](#show-kernel-links)
  * [show kernel route table <i>table</i> prefix <i>prefix</i>](#show-kernel-route-table-table-prefix-prefix)
  * [show kernel routes](#show-kernel-routes)
  * [show kernel routes table <i>table</i>](#show-kernel-routes-table-table)
  * [show node](#show-node)
  * [show node fsm history](#show-node-fsm-history)
  * [show node fsm verbose-history](#show-node-fsm-verbose-history)
  * [show nodes](#show-nodes)
  * [show nodes level](#show-nodes-level)
  * [show route prefix <i>prefix</i>](#show-route-prefix-prefix)
  * [show route prefix <i>prefix</i> owner <i>owner</i>](#show-route-prefix-prefix-owner-owner)
  * [show routes](#show-routes)
  * [show spf](#show-spf)
  * [show spf direction <i>direction</i>](#show-spf-direction-direction)
  * [show spf direction <i>direction</i> destination <i>destination</i>](#show-spf-direction-direction-destination-destination)
  * [show tie-db](#show-tie-db)
  * [stop](#stop)

## Connect to the CLI

Go to the top of the directory where the rift-python repository was cloned (in this example we assume it was cloned into your home directory):

<pre>
$ <b>cd ${HOME}/rift-python</b>
</pre>

Make sure your virtual environment (that was created during the installation process) is activated:

<pre>
$ <b>source env/bin/activate</b>
(env) $ 
</pre>

Start the rift package:

<pre>
(env) $ <b>python rift</b>
Command Line Interface (CLI) available on port 61375
</pre>

Optionally you may pass a topology YAML file as a command-line argument:

<pre>
(env) $ <b>python rift topology/two_by_two_by_two.yaml</b>
Command Line Interface (CLI) available on port 61377
</pre>

When you start the Python RIFT protocol engine, it reports a port number that you can use to connect one or more CLI 
sessions.

You can connect to the Command Line Interface (CLI) using a Telnet client. Assuming you are connecting from the same 
device as where the RIFT engine is running, the hostname is localhost. 

<pre>
$ <b>telnet localhost 61377 </b>
Trying 127.0.0.1...
Connected to localhost.
Escape character is '^]'.
agg_101> 
</pre>

You should get a prompt containing the name of the current RIFT node. In this example the name of the current RIFT node
is "agg_101".

## Entering CLI Commands

You can enter CLI commands at the CLI prompt. For example, try entering the <b>help</b> command:

<pre>
agg_101> <b>help</b>
exit 
set interface &lt;interface&gt; failure &lt;failure&gt;
set level &lt;level&gt;
set node &lt;node&gt;
show engine
show forwarding
show forwarding prefix &lt;prefix&gt;
show fsm lie
show fsm ztp
show interface &lt;interface&gt;
show interface &lt;interface&gt; fsm history
show interface &lt;interface&gt; fsm verbose-history
show interface &lt;interface&gt; queues
show interface &lt;interface&gt; sockets
show interfaces
show kernel addresses
show kernel links
show kernel route table &lt;table> prefix &lt;prefix&gt;
show kernel routes
show kernel routes table &lt;table&gt;
show node 
show node fsm history 
show node fsm verbose-history 
show nodes 
show nodes level 
show route prefix &lt;prefix&gt;
show route prefix &lt;prefix&gt; owner &lt;owner&gt;
show routes 
show spf 
show spf direction &lt;direction&gt;
show spf direction &lt;direction&gt; destination &lt;destination&gt;
show tie-db 
stop 
</pre>

If you are connected to the CLI using Telnet, you can use the following keys for editing:

* Cursor-Left: Move cursor on character left.

* Cursor-Right: Move cursor on character right

* Cursor-Up or Control-P: Go to the previous command in command history.

* Cursor-Down or Control-N: Go to the next command in command history.

* Control-A: Move cursor to the start of the line.

* Control-E: Move cursor to the end of the line.


The CLI does not yet support any of the following features:

* Command completion: you must manually enter the complete command; you cannot enter partial commands or use
tab to complete commands.

* Interactive context-sensitive help: you can enter "help" or "?" and press enter at the end of a partial command
line to get context-sensitive help. But after reading the help text, you must manually re-enter the command line. 

## Command Line Interface Commands

### exit

The "<b>exit</b> command closes the CLI session.

Example:

<pre>
(env) $ python rift topology/two_by_two_by_two.yaml
Command Line Interface (CLI) available on port 50102
</pre>

<pre>
$ telnet localhost 50102
Trying 127.0.0.1...
Connected to localhost.
Escape character is '^]'.
agg_101> <b>exit</b>
agg_101> Connection closed by foreign host.
$ 
</pre>

Normally, the RIFT engine continues to run when a CLI session is closed. However, if the RIFT
engine was started interactively using the --interactive command line option, then exiting the
CLI also causes the RIFT engine to stop:

Example:

<pre>
(env) $ python rift --interactive topology/two_by_two_by_two.yaml
agg_101> <b>exit</b>
(env) $ 
</pre>

### set interface <i>interface</i> failure <i>failure</i>

The "<b>set interface</b> <i>interface</i> <b>failure</b> <i>failure</i>" enables or disables a simulated failure of an interface.

The <i>failure</i> parameter can be one of the following:

| <i>failure</i> | Meaning |
| --- | --- |
| ok | The interface is OK. There is no failure. |
| failed | There is a bi-directional failure on the interface. Both sent and received packets are dropped. |
| tx-failed | There is a uni-directional failure on the interface. Sent (TX) packets are dropped. Received (RX) packets are delivered. |
| rx-failed | There is a uni-directional failure on the interface. Sent (TX) packets are delivered. Received (RX) packets are dropped. |

Example:

<pre>
node1> <b>set interface if1 failure failed</b>
</pre>

### set level <i>level</i>

The "<b>set level</b> <i>level</i>" command changes the level of the currently active RIFT node.

The valid values for the <i>level</i> parameter are <b>undefined</b>, <b>leaf</b>, <b>leaf-to-leaf</b>, 
<b>superspine</b>, or an integer non-negative number.

These <i>level</i> values are mapped to the parameters in the protocol specification as follows:

| <i>level</i> value | LEAF_ONLY | LEAF_2_LEAF | TOP_OF_FABRIC_FLAG | CONFIGURED_LEVEL |
| --- | --- | --- | --- | --- |
| <b>undefined<b> | false | false | false | UNDEFINED_LEVEL |
| <b>leaf<b> | true | false | false | UNDEFINED_LEVEL (see note 1) |
| <b>leaf-to-leaf<b> | true | true | false | UNDEFINED_LEVEL (see note 1) |
| <b>superspine<b> | false | false | true | UNDEFINED_LEVEL (see note 2) |
| integer non-negative number | true if level = 0, false otherwise | false | false | level |

Note 1: Even if the CONFIGURED_LEVEL is UNDEFINED_LEVEL, nodes with the LEAF_ONLY flag set will advertise level 
leaf_level (= 0) in the sent LIE packets.

Note 2: Event if CONFIGURED_LEVEL is UNDEFINED_LEVEL, nodes with the TOP_OF_FABRIC_FLAG set will advertise level 
top_of_fabric_level (= 24) in the sent LIE packets.

Example:

<pre>
core_1> <b>set level undefined</b>
</pre>

### set node <i>node</i>

The "<b>set node</b> <i>node-name</i>" command changes the currently active RIFT node to the node with the specified 
RIFT node name:

Note: you can get a list of RIFT nodes present in the current RIFT protocol engine using the <b>show nodes</b> command.

Example:

<pre>
agg_101> <b>set node core_1</b>
core_1> 
</pre>

### show engine

The "<b>show engine</b>" command shows the status of the RIFT engine, i.e. global information
that applies to all nodes running in the RIFT engine.

Example:

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
| Flooding Reduction      | True      |
+-------------------------+-----------+
</pre>

### show forwarding

The "<b>show forwarding</b>" command shows all routes in the Forwarding Information Base (FIB) of 
the current node. It shows both the IPv4 FIB and the IPv6 FIB.

Example:

<pre>
agg_101> <b>show forwarding</b>
IPv4 Routes:
+---------------+-----------+-----------------------+
| Prefix        | Owner     | Next-hops             |
+---------------+-----------+-----------------------+
| 0.0.0.0/0     | North SPF | if_101_1 127.0.0.1    |
|               |           | if_101_2 127.0.0.1    |
+---------------+-----------+-----------------------+
| 1.1.1.0/24    | South SPF | if_101_1001 127.0.0.1 |
+---------------+-----------+-----------------------+
| 1.1.2.0/24    | South SPF | if_101_1001 127.0.0.1 |
+---------------+-----------+-----------------------+
| 1.1.3.0/24    | South SPF | if_101_1001 127.0.0.1 |
+---------------+-----------+-----------------------+
| 1.1.4.0/24    | South SPF | if_101_1001 127.0.0.1 |
+---------------+-----------+-----------------------+
| 1.2.1.0/24    | South SPF | if_101_1002 127.0.0.1 |
+---------------+-----------+-----------------------+
| 1.2.2.0/24    | South SPF | if_101_1002 127.0.0.1 |
+---------------+-----------+-----------------------+
| 1.2.3.0/24    | South SPF | if_101_1002 127.0.0.1 |
+---------------+-----------+-----------------------+
| 1.2.4.0/24    | South SPF | if_101_1002 127.0.0.1 |
+---------------+-----------+-----------------------+
| 99.99.99.0/24 | South SPF | if_101_1001 127.0.0.1 |
|               |           | if_101_1002 127.0.0.1 |
+---------------+-----------+-----------------------+

IPv6 Routes:
+--------+-----------+--------------------+
| Prefix | Owner     | Next-hops          |
+--------+-----------+--------------------+
| ::/0   | North SPF | if_101_1 127.0.0.1 |
|        |           | if_101_2 127.0.0.1 |
+--------+-----------+--------------------+
</pre>

### show forwarding prefix <i>prefix</i>

The "<b>show forwarding prefix</b> <i>prefix</i>" command shows the route for a given prefix in the
Forwarding Information Base (FIB) of the current node.

Parameter <i>prefix</i> must be an IPv4 prefix or an IPv6 prefix

Example:

<pre>
agg_101> <b>show forwarding prefix ::/0</b>
+--------+-----------+--------------------+
| Prefix | Owner     | Next-hops          |
+--------+-----------+--------------------+
| ::/0   | North SPF | if_101_1 127.0.0.1 |
|        |           | if_101_2 127.0.0.1 |
+--------+-----------+--------------------+
</pre>

### show fsm <i>fsm</i>

The "<b>show fsm</b> <i>fsm</i>" command shows the definition of the specified Finite State Machine (FSM).

Parameter <i>fsm</i> specifies the name of the FSM and can be one of the following values:

* <b>lie</b>: Show the Link Information Element (LIE) FSM.
* <b>ztp</b>: Show the Zero Touch Provisioning (ZTP) FSM.

Example:

<pre>
agg_101> <b>show fsm lie</b>
States:
+-----------+
| State     |
+-----------+
| ONE_WAY   |
+-----------+
| TWO_WAY   |
+-----------+
| THREE_WAY |
+-----------+

Events:
+-------------------------------+---------+
| Event                         | Verbose |
+-------------------------------+---------+
| TIMER_TICK                    | True    |
+-------------------------------+---------+
| LEVEL_CHANGED                 | False   |
+-------------------------------+---------+
| HAL_CHANGED                   | False   |
+-------------------------------+---------+
.                               .         .
.                               .         .
.                               .         .
+-------------------------------+---------+
| LIE_CORRUPT                   | False   |
+-------------------------------+---------+
| SEND_LIE                      | True    |
+-------------------------------+---------+

Transitions:
+------------+-----------------------------+-----------+-------------------------+-------------+
| From state | Event                       | To state  | Actions                 | Push events |
+------------+-----------------------------+-----------+-------------------------+-------------+
| ONE_WAY    | TIMER_TICK                  | -         | -                       | SEND_LIE    |
+------------+-----------------------------+-----------+-------------------------+-------------+
| ONE_WAY    | LEVEL_CHANGED               | ONE_WAY   | update_level            | SEND_LIE    |
+------------+-----------------------------+-----------+-------------------------+-------------+
| ONE_WAY    | HAL_CHANGED                 | -         | store_hal               | -           |
+------------+-----------------------------+-----------+-------------------------+-------------+
.            .                             .           .                         .             .
.            .                             .           .                         .             .
.            .                             .           .                         .             .
+------------+-----------------------------+-----------+-------------------------+-------------+
| THREE_WAY  | LIE_CORRUPT                 | ONE_WAY   | -                       | -           |
+------------+-----------------------------+-----------+-------------------------+-------------+
| THREE_WAY  | SEND_LIE                    | -         | send_lie                | -           |
+------------+-----------------------------+-----------+-------------------------+-------------+

State entry actions:
+---------+---------+
| State   | Actions |
+---------+---------+
| ONE_WAY | cleanup |
+---------+---------+
</pre>

### show interface <i>interface</i>

The "<b>show interface</b> <i>interface</i>" command reports more detailed information about a single interface.
If there is a neighbor on the interface, the command also shows details about that neighbor.

The <i>interface</i> parameter is the name of an interface of the current node. You can get a list of interfaces of the
current node using the <b>show interfaces</b> command.

Example of an interface which does have a neighbor (adjacency in state THREE_WAY):

<pre>
agg_101> <b>show interface if_101_1001</b>
Interface:
+--------------------------------------+--------------------------------------------+
| Interface Name                       | if_101_1001                                |
| Advertised Name                      | agg_101-if_101_1001                        |
| Interface IPv4 Address               | 127.0.0.1                                  |
| Metric                               | 1                                          |
| Receive LIE IPv4 Multicast Address   | 224.0.0.81                                 |
| Transmit LIE IPv4 Multicast Address  | 224.0.0.91                                 |
| Receive LIE IPv6 Multicast Address   | FF02::0078                                 |
| Transmit LIE IPv6 Multicast Address  | FF02::0078                                 |
| Receive LIE Port                     | 20033                                      |
| Transmit LIE Port                    | 20034                                      |
| Receive TIE Port                     | 20035                                      |
| System ID                            | 101                                        |
| Local ID                             | 3                                          |
| MTU                                  | 1500                                       |
| POD                                  | 0                                          |
| State                                | THREE_WAY                                  |
| Received LIE Accepted or Rejected    | Accepted                                   |
| Received LIE Accept or Reject Reason | This node is not leaf and neighbor is leaf |
| Neighbor                             | True                                       |
+--------------------------------------+--------------------------------------------+

Neighbor:
+----------------------------------+-----------------------+
| Name                             | edge_1001-if_1001_101 |
| System ID                        | 1001                  |
| IPv4 Address                     | 127.0.0.1             |
| LIE UDP Source Port              | 65344                 |
| Link ID                          | 1                     |
| Level                            | 0                     |
| Flood UDP Port                   | 10001                 |
| MTU                              | 1500                  |
| POD                              | 0                     |
| Hold Time                        | 3                     |
| Not a ZTP Offer                  | True                  |
| You Are Not a ZTP Flood Repeater | True                  |
| Your System ID                   | 101                   |
| Your Local ID                    | 3                     |
+----------------------------------+-----------------------+
</pre>

Example of an interface which does not have a neighbor (adjacency in state ONE_WAY):

<pre>
agg_101> <b>show interface if_101_1</b>
Interface:
+--------------------------------------+------------------+
| Interface Name                       | if_101_1         |
| Advertised Name                      | agg_101-if_101_1 |
| Interface IPv4 Address               | 127.0.0.1        |
| Metric                               | 1                |
| Receive LIE IPv4 Multicast Address   | 224.0.0.81       |
| Transmit LIE IPv4 Multicast Address  | 224.0.0.71       |
| Receive LIE IPv6 Multicast Address   | FF02::0078       |
| Transmit LIE IPv6 Multicast Address  | FF02::0078       |
| Receive LIE Port                     | 20001            |
| Transmit LIE Port                    | 20002            |
| Receive TIE Port                     | 20004            |
| System ID                            | 101              |
| Local ID                             | 1                |
| MTU                                  | 1500             |
| POD                                  | 0                |
| State                                | ONE_WAY          |
| Received LIE Accepted or Rejected    | Rejected         |
| Received LIE Accept or Reject Reason | Level mismatch   |
| Neighbor                             | False            |
+--------------------------------------+------------------+
</pre>

### show interface <i>interface</i> fsm history

The "<b>show interface</b> <i>interface</i> <b>fsm history</b>" command shows the 25 most recent "interesting" 
executed events for the Link Information Element (LIE) Finite State Machine (FSM) associated with the interface. 
The most recent event is at the top.

This command only shows the "interesting" events, i.e. it does not show any events that are marked as "verbose"
by the "<b>show fsm lie</b>" command. 
Use the "<b>show interface</b> <i>interface</i> <b>fsm verbose-history</b>" command if you want to see all events.

Example:

<pre>
agg_101> <b>show interface if_101_1001 fsm history</b>
+----------+-------------+---------+---------+------------------+---------------+-----------+----------+
| Sequence | Time        | Verbose | From    | Event            | Actions and   | To        | Implicit |
| Nr       | Delta       | Skipped | State   |                  | Pushed Events | State     |          |
+----------+-------------+---------+---------+------------------+---------------+-----------+----------+
| 313      | 2087.427679 | 2       | TWO_WAY | VALID_REFLECTION |               | THREE_WAY | False    |
+----------+-------------+---------+---------+------------------+---------------+-----------+----------+
| 223      | 0.017177    | 3       | ONE_WAY | NEW_NEIGHBOR     | SEND_LIE      | TWO_WAY   | False    |
+----------+-------------+---------+---------+------------------+---------------+-----------+----------+
</pre>

### show interface <i>interface</i> fsm verbose-history

The "<b>show interface</b> <i>interface</i> <b>fsm verbose-history</b>" command shows the 25 most recent
executed events for the Link Information Element (LIE) Finite State Machine (FSM) associated with the interface. 
The most recent event is at the top.

This command shows all events, including the events that are marked as verbose 
by the "<b>show fsm lie</b>" command. Because of this, the output tends to be dominated by non-interesting verbose
events such as timer ticks and the sending and receiving of periodic LIE messages.
Use the "<b>show interface</b> <i>interface</i> <b>fsm history</b>" command if you only want to see
"interesting" events.

Example:

<pre>
agg_101> <b>show interface if_101_1001 fsm verbose-history</b>
+----------+----------+---------+-----------+--------------+-------------------------+-------+----------+
| Sequence | Time     | Verbose | From      | Event        | Actions and             | To    | Implicit |
| Nr       | Delta    | Skipped | State     |              | Pushed Events           | State |          |
+----------+----------+---------+-----------+--------------+-------------------------+-------+----------+
| 316353   | 0.486001 | 0       | THREE_WAY | LIE_RECEIVED | process_lie             | None  | False    |
+----------+----------+---------+-----------+--------------+-------------------------+-------+----------+
| 316277   | 0.017974 | 0       | THREE_WAY | SEND_LIE     | send_lie                | None  | False    |
+----------+----------+---------+-----------+--------------+-------------------------+-------+----------+
| 316254   | 0.002745 | 0       | THREE_WAY | TIMER_TICK   | check_hold_time_expired | None  | False    |
|          |          |         |           |              | SEND_LIE                |       |          |
+----------+----------+---------+-----------+--------------+-------------------------+-------+----------+
.          .          .         .           .              .                         .       .          .
.          .          .         .           .              .                         .       .          .
.          .          .         .           .              .                         .       .          .
+----------+----------+---------+-----------+--------------+-------------------------+-------+----------+
| 315302   | 0.002144 | 0       | THREE_WAY | TIMER_TICK   | check_hold_time_expired | None  | False    |
|          |          |         |           |              | SEND_LIE                |       |          |
+----------+----------+---------+-----------+--------------+-------------------------+-------+----------+
| 315242   | 0.983821 | 0       | THREE_WAY | LIE_RECEIVED | process_lie             | None  | False    |
+----------+----------+---------+-----------+--------------+-------------------------+-------+----------+
</pre>

### show interface <i>interface</i> queues

The "<b>show interface</b> <i>interface</i> <b>queues</b>" command shows flooding queues:

| Queue name | Messages in queue |
| --- | --- |
| Transmit queue | The TIE headers that need to be transmitted in a TIE message over this interface |
| Retransmit queue | The TIE headers that need to be re-transmitted in a TIE message over this interface |
| Request queue | The TIE headers that need to be requested in a TIRE message over this interface |
| Acknowledge queue | The TIE headers that need to be acknowledged in a TIRE message over this interface |

When the flooding has converged, all queues are expected to be empty.
A queue that is persistently non-empty indicates a problem in flooding convergence.

Example:

<pre>
agg_101> <b>show interface if_101_1 queues</b>
Transmit queue:
+-----------+------------+------+--------+--------+-----------+-------------+
| Direction | Originator | Type | TIE Nr | Seq Nr | Remaining | Origination |
|           |            |      |        |        | Lifetime  | Time        |
+-----------+------------+------+--------+--------+-----------+-------------+

Retransmit queue:
+-----------+------------+------+--------+--------+-----------+-------------+
| Direction | Originator | Type | TIE Nr | Seq Nr | Remaining | Origination |
|           |            |      |        |        | Lifetime  | Time        |
+-----------+------------+------+--------+--------+-----------+-------------+

Request queue:
+-----------+------------+------+--------+--------+-----------+-------------+
| Direction | Originator | Type | TIE Nr | Seq Nr | Remaining | Origination |
|           |            |      |        |        | Lifetime  | Time        |
+-----------+------------+------+--------+--------+-----------+-------------+

Acknowledge queue:
+-----------+------------+------+--------+--------+-----------+-------------+
| Direction | Originator | Type | TIE Nr | Seq Nr | Remaining | Origination |
|           |            |      |        |        | Lifetime  | Time        |
+-----------+------------+------+--------+--------+-----------+-------------+
</pre>

### show interface <i>interface</i> sockets

The "<b>show interface</b> <i>interface</i> <b>sockets</b>" command shows the sockets that the 
current node has opened for sending and receiving packets.

Example:

<pre>
agg_101> <b>show interface if_101_1 sockets</b>
+----------+-----------+--------+---------------------------+------------+----------------+-------------+
| Traffic  | Direction | Family | Local Address             | Local Port | Remote Address | Remote Port |
+----------+-----------+--------+---------------------------+------------+----------------+-------------+
| LIEs     | Receive   | IPv4   | 224.0.0.81                | 20001      | Any            | Any         |
+----------+-----------+--------+---------------------------+------------+----------------+-------------+
| LIEs     | Receive   | IPv6   | ::                        | 20001      | Any            | Any         |
+----------+-----------+--------+---------------------------+------------+----------------+-------------+
| LIEs     | Send      | IPv4   | 192.168.2.100             | 54091      | 224.0.0.71     | 20002       |
+----------+-----------+--------+---------------------------+------------+----------------+-------------+
| LIEs     | Send      | IPv6   | fe80::184e:acd5:2cd7:cd3f | 54092      | ff02::78       | 20002       |
+----------+-----------+--------+---------------------------+------------+----------------+-------------+
| Flooding | Receive   | IPv4   | 0.0.0.0                   | 20004      | Any            | Any         |
+----------+-----------+--------+---------------------------+------------+----------------+-------------+
| Flooding | Send      | IPv4   | 192.168.2.100             | 53073      | 192.168.2.100  | 20003       |
+----------+-----------+--------+---------------------------+------------+----------------+-------------+
</pre>

### show interfaces

The "<b>show interfaces</b>" command reports a summary of all RIFT interfaces (i.e. interfaces on which RIFT is running)
on the currently active RIFT node. 

Use the "<b>show interface</b> <i>interface</i>" to see all details about any particular interface.

<pre>
agg_101> <b>show interfaces</b>
+-------------+-----------------------+-----------+-----------+
| Interface   | Neighbor              | Neighbor  | Neighbor  |
| Name        | Name                  | System ID | State     |
+-------------+-----------------------+-----------+-----------+
| if_101_1    |                       |           | ONE_WAY   |
+-------------+-----------------------+-----------+-----------+
| if_101_1001 | edge_1001-if_1001_101 | 1001      | THREE_WAY |
+-------------+-----------------------+-----------+-----------+
| if_101_1002 | edge_1002-if_1002_101 | 1002      | THREE_WAY |
+-------------+-----------------------+-----------+-----------+
| if_101_2    | core_2-if_2_101       | 2         | THREE_WAY |
+-------------+-----------------------+-----------+-----------+
</pre>

### show kernel addresses

The "<b>show kernel addresses</b>" command reports a summary of all addresses in the Linux kernel
on which the RIFT engine is running.

<pre>
real2> show kernel addresses
Kernel Addresses:
+-----------+---------------------------+-----------+-----------+---------+
| Interface | Address                   | Local     | Broadcast | Anycast |
| Name      |                           |           |           |         |
+-----------+---------------------------+-----------+-----------+---------+
| lo        | 127.0.0.1                 | 127.0.0.1 |           |         |
+-----------+---------------------------+-----------+-----------+---------+
| lo        | 88.88.2.1                 | 88.88.2.1 |           |         |
+-----------+---------------------------+-----------+-----------+---------+
| veth-a2   | 99.99.1.2                 | 99.99.1.2 |           |         |
+-----------+---------------------------+-----------+-----------+---------+
| veth-b2   | 99.99.2.2                 | 99.99.2.2 |           |         |
+-----------+---------------------------+-----------+-----------+---------+
</pre>

If this command is executed on a platform that does not support the Netlink interface to the
kernel routing table (i.e. any non-Linux platform including BSD and macOS) the following error
message is reported:

<pre>
agg_101> <b>show kernel addresses</b>
Kernel networking not supported on this platform
</pre>

### show kernel links

The "<b>show kernel links</b>" command reports a summary of all links in the Linux kernel
on which the RIFT engine is running.

<pre>
real2> <b>show kernel links</b>
Kernel Links:
+-----------+-----------+-------------------+-------------------+-----------+-------+-----------+
| Interface | Interface | Hardware          | Hardware          | Link Type | MTU   | Flags     |
| Name      | Index     | Address           | Broadcast         |           |       |           |
|           |           |                   | Address           |           |       |           |
+-----------+-----------+-------------------+-------------------+-----------+-------+-----------+
| lo        | 1         | 00:00:00:00:00:00 | 00:00:00:00:00:00 |           | 65536 | UP        |
|           |           |                   |                   |           |       | LOOPBACK  |
|           |           |                   |                   |           |       | RUNNING   |
|           |           |                   |                   |           |       | LOWER_UP  |
+-----------+-----------+-------------------+-------------------+-----------+-------+-----------+
| tunl0     | 2         | 00:00:00:00:08:00 | 00:00:00:00:c4:00 | 0         | 1480  | NOARP     |
+-----------+-----------+-------------------+-------------------+-----------+-------+-----------+
| ip6tnl0   | 3         | 00:00:00:00:00:00 | 00:00:00:00:00:00 | 0         | 1452  | NOARP     |
+-----------+-----------+-------------------+-------------------+-----------+-------+-----------+
| veth-a2   | 4         | b2:cd:9f:06:78:ab | ff:ff:ff:ff:ff:ff | 5         | 1500  | UP        |
|           |           |                   |                   |           |       | BROADCAST |
|           |           |                   |                   |           |       | RUNNING   |
|           |           |                   |                   |           |       | MULTICAST |
|           |           |                   |                   |           |       | LOWER_UP  |
+-----------+-----------+-------------------+-------------------+-----------+-------+-----------+
| veth-b2   | 6         | 0a:6b:39:ab:a9:e9 | ff:ff:ff:ff:ff:ff | 7         | 1500  | UP        |
|           |           |                   |                   |           |       | BROADCAST |
|           |           |                   |                   |           |       | RUNNING   |
|           |           |                   |                   |           |       | MULTICAST |
|           |           |                   |                   |           |       | LOWER_UP  |
+-----------+-----------+-------------------+-------------------+-----------+-------+-----------+
</pre>

If this command is executed on a platform that does not support the Netlink interface to the
kernel routing table (i.e. any non-Linux platform including BSD and macOS) the following error
message is reported:

<pre>
agg_101> <b>show kernel links</b>
Kernel networking not supported on this platform
</pre>

### show kernel route table <i>table</i> prefix <i>prefix</i>

The "<b>show kernel route table</b> <i>table</i> <b>prefix</b> <i>prefix</i>" command reports the
details of a single route in the route table in the Linux kernel on which the RIFT engine is running.

Parameter <i>table</i> must be <b>local</b>, <b>main</b>, <b>default</b>, <b>unspecified</b>, or
a number in the range 0-255.

Parameter <i>prefix</i> must be an IPv4 prefix or an IPv6 prefix

<pre>
real2> show kernel route table main prefix 99.99.1.0/24
+--------------------------+--------------+
| Table                    | Main         |
| Address Family           | IPv4         |
| Destination              | 99.99.1.0/24 |
| Type                     | Unicast      |
| Protocol                 | Kernel       |
| Scope                    | Link         |
| Next-hops                | veth-a2      |
| Priority                 |              |
| Preference               |              |
| Preferred Source Address | 99.99.1.2    |
| Source                   |              |
| Flow                     |              |
| Encapsulation Type       |              |
| Encapsulation            |              |
| Metrics                  |              |
| Type of Service          | 0            |
| Flags                    | 0            |
+--------------------------+--------------+
</pre>

If this command is executed on a platform that does not support the Netlink interface to the
kernel routing table (i.e. any non-Linux platform including BSD and macOS) the following error
message is reported:

<pre>
agg_101> <b>show kernel route table main prefix 0.0.0.0/0</b>
Kernel networking not supported on this platform
</pre>

### show kernel routes

The "<b>show kernel routes</b>" command reports a summary of
all routes in the Linux kernel on which the RIFT engine is running.

<pre>
real2> <b>show kernel routes</b>
Kernel Routes:
+-------------+---------+-------------------------------+-------------+----------+-----------+-----------+--------+
| Table       | Address | Destination                   | Type        | Protocol | Outgoing  | Gateway   | Weight |
|             | Family  |                               |             |          | Interface |           |        |
+-------------+---------+-------------------------------+-------------+----------+-----------+-----------+--------+
| Unspecified | IPv6    | ::/0                          | Unreachable | Kernel   | lo        |           |        |
+-------------+---------+-------------------------------+-------------+----------+-----------+-----------+--------+
| Unspecified | IPv6    | ::/0                          | Unreachable | Kernel   | lo        |           |        |
+-------------+---------+-------------------------------+-------------+----------+-----------+-----------+--------+
| Main        | IPv4    | 0.0.0.0/0                     | Unicast     | RIFT     | veth-a2   | 99.99.1.1 | 1      |
|             |         |                               |             |          | veth-b2   | 99.99.2.1 | 1      |
+-------------+---------+-------------------------------+-------------+----------+-----------+-----------+--------+
| Main        | IPv4    | 99.99.1.0/24                  | Unicast     | Kernel   | veth-a2   |           |        |
+-------------+---------+-------------------------------+-------------+----------+-----------+-----------+--------+
| Main        | IPv4    | 99.99.2.0/24                  | Unicast     | Kernel   | veth-b2   |           |        |
+-------------+---------+-------------------------------+-------------+----------+-----------+-----------+--------+
| Main        | IPv6    | fe80::/64                     | Unicast     | Kernel   | veth-a2   |           |        |
+-------------+---------+-------------------------------+-------------+----------+-----------+-----------+--------+
| Main        | IPv6    | fe80::/64                     | Unicast     | Kernel   | veth-b2   |           |        |
+-------------+---------+-------------------------------+-------------+----------+-----------+-----------+--------+
| Local       | IPv4    | 88.88.2.1/32                  | Local       | Kernel   | lo        |           |        |
+-------------+---------+-------------------------------+-------------+----------+-----------+-----------+--------+
.             .         .                               .             .          .           .           .        .
.             .         .                               .             .          .           .           .        .
.             .         .                               .             .          .           .           .        .
+-------------+---------+-------------------------------+-------------+----------+-----------+-----------+--------+
| Local       | IPv6    | ff00::/8                      | Unicast     | Boot     | veth-b2   |           |        |
+-------------+---------+-------------------------------+-------------+----------+-----------+-----------+--------+
</pre>

If this command is executed on a platform that does not support the Netlink interface to the
kernel routing table (i.e. any non-Linux platform including BSD and macOS) the following error
message is reported:

<pre>
agg_101> <b>show kernel routes</b>
Kernel networking not supported on this platform
</pre>

### show kernel routes table <i>table</i>

The "<b>show kernel routes table</b> <i>table</i>" command reports a summary of
all routes in a specific route table in the Linux kernel on which the RIFT engine is running.

Parameter <i>table</i> must be <b>local</b>, <b>main</b>, <b>default</b>, <b>unspecified</b>, or
a number in the range 0-255.

<pre>
real2> <b>show kernel routes table main</b>
Kernel Routes:
+-------+---------+--------------+---------+----------+-----------+-----------+--------+
| Table | Address | Destination  | Type    | Protocol | Outgoing  | Gateway   | Weight |
|       | Family  |              |         |          | Interface |           |        |
+-------+---------+--------------+---------+----------+-----------+-----------+--------+
| Main  | IPv4    | 0.0.0.0/0    | Unicast | RIFT     | veth-a2   | 99.99.1.1 | 1      |
|       |         |              |         |          | veth-b2   | 99.99.2.1 | 1      |
+-------+---------+--------------+---------+----------+-----------+-----------+--------+
| Main  | IPv4    | 99.99.1.0/24 | Unicast | Kernel   | veth-a2   |           |        |
+-------+---------+--------------+---------+----------+-----------+-----------+--------+
| Main  | IPv4    | 99.99.2.0/24 | Unicast | Kernel   | veth-b2   |           |        |
+-------+---------+--------------+---------+----------+-----------+-----------+--------+
| Main  | IPv6    | fe80::/64    | Unicast | Kernel   | veth-a2   |           |        |
+-------+---------+--------------+---------+----------+-----------+-----------+--------+
| Main  | IPv6    | fe80::/64    | Unicast | Kernel   | veth-b2   |           |        |
+-------+---------+--------------+---------+----------+-----------+-----------+--------+
</pre>

If this command is executed on a platform that does not support the Netlink interface to the
kernel routing table (i.e. any non-Linux platform including BSD and macOS) the following error
message is reported:

<pre>
agg_101> <b>show kernel routes table main</b>
Kernel networking not supported on this platform
</pre>

### show node

The "<b>show node</b>" command reports the details for the currently active RIFT node:

Example:

<pre>
agg_101> <b>show node</b>
Node:
+---------------------------------------+------------------+
| Name                                  | agg_101          |
| Passive                               | False            |
| Running                               | True             |
| System ID                             | 101              |
| Configured Level                      | 1                |
| Leaf Only                             | False            |
| Leaf 2 Leaf                           | False            |
| Top of Fabric Flag                    | True             |
| Zero Touch Provisioning (ZTP) Enabled | False            |
| ZTP FSM State                         | UPDATING_CLIENTS |
| ZTP Hold Down Timer                   | Stopped          |
| Highest Available Level (HAL)         | 2                |
| Highest Adjacency Three-way (HAT)     | 2                |
| Level Value                           | 1                |
| Receive LIE IPv4 Multicast Address    | 224.0.0.81       |
| Transmit LIE IPv4 Multicast Address   | 224.0.0.120      |
| Receive LIE IPv6 Multicast Address    | FF02::0078       |
| Transmit LIE IPv6 Multicast Address   | FF02::0078       |
| Receive LIE Port                      | 20102            |
| Transmit LIE Port                     | 10000            |
| LIE Send Interval                     | 1.0 secs         |
| Receive TIE Port                      | 10001            |
| Kernel Route Table                    | 3                |
| Flooding Reduction                    | True             |
+---------------------------------------+------------------+

Received Offers:
+-------------+-----------+-------+-----------------+-----------+-------+------------+---------+----------------+
| Interface   | System ID | Level | Not A ZTP Offer | State     | Best  | Best 3-Way | Removed | Removed Reason |
+-------------+-----------+-------+-----------------+-----------+-------+------------+---------+----------------+
| if_101_1    | 1         | 2     | False           | THREE_WAY | True  | True       | False   |                |
+-------------+-----------+-------+-----------------+-----------+-------+------------+---------+----------------+
| if_101_1001 | 1001      | 0     | False           | THREE_WAY | False | False      | True    | Level is leaf  |
+-------------+-----------+-------+-----------------+-----------+-------+------------+---------+----------------+
| if_101_1002 | 1002      | 0     | False           | THREE_WAY | False | False      | True    | Level is leaf  |
+-------------+-----------+-------+-----------------+-----------+-------+------------+---------+----------------+
| if_101_2    | 2         | 2     | False           | THREE_WAY | False | False      | False   |                |
+-------------+-----------+-------+-----------------+-----------+-------+------------+---------+----------------+

Sent Offers:
+-------------+-----------+-------+-----------------+-----------+
| Interface   | System ID | Level | Not A ZTP Offer | State     |
+-------------+-----------+-------+-----------------+-----------+
| if_101_1    | 101       | 1     | False           | THREE_WAY |
+-------------+-----------+-------+-----------------+-----------+
| if_101_1001 | 101       | 1     | False           | THREE_WAY |
+-------------+-----------+-------+-----------------+-----------+
| if_101_1002 | 101       | 1     | False           | THREE_WAY |
+-------------+-----------+-------+-----------------+-----------+
| if_101_2    | 101       | 1     | False           | THREE_WAY |
+-------------+-----------+-------+-----------------+-----------+
</pre>

### show node fsm history

The "<b>show node fsm history</b>" command shows the 25 most recent "interesting" 
executed events for the Zero Touch Provisioning (ZTP) Finite State Machine (FSM) associated with the currently
active node. The most recent event is at the top.

This command only shows the "interesting" events, i.e. it does not show any events that are marked as "verbose"
by the "<b>show fsm ztp</b>" command. 
Use the "<b>show node fsm verbose-history</b>" command if you want to see all events.

Example:

<pre>
agg_101> <b>show node fsm history</b>
+----------+-------------+---------+--------------------+-------------------+----------------------------------------------+--------------------+----------+
| Sequence | Time        | Verbose | From               | Event             | Actions and                                  | To                 | Implicit |
| Nr       | Delta       | Skipped | State              |                   | Pushed Events                                | State              |          |
+----------+-------------+---------+--------------------+-------------------+----------------------------------------------+--------------------+----------+
| 172980   | 2070.046668 | 0       | COMPUTE_BEST_OFFER | COMPUTATION_DONE  | no_action                                    | UPDATING_CLIENTS   | False    |
|          |             |         |                    |                   | update_all_lie_fsms_with_computation_results |                    |          |
+----------+-------------+---------+--------------------+-------------------+----------------------------------------------+--------------------+----------+
| 172979   | 0.000207    | 0       | HOLDING_DOWN       | HOLD_DOWN_EXPIRED | purge_offers                                 | COMPUTE_BEST_OFFER | False    |
|          |             |         |                    |                   | stop_hold_down_timer                         |                    |          |
|          |             |         |                    |                   | level_compute                                |                    |          |
|          |             |         |                    |                   | COMPUTATION_DONE                             |                    |          |
+----------+-------------+---------+--------------------+-------------------+----------------------------------------------+--------------------+----------+
| 172978   | 0.000187    | 0       | HOLDING_DOWN       | LOST_HAT          | no_action                                    | None               | False    |
+----------+-------------+---------+--------------------+-------------------+----------------------------------------------+--------------------+----------+
.          .             .         .                    .                   .                                              .                    .          .
.          .             .         .                    .                   .                                              .                    .          .
.          .             .         .                    .                   .                                              .                    .          .
+----------+-------------+---------+--------------------+-------------------+----------------------------------------------+--------------------+----------+
| 58       | 0.000430    | 2       | UPDATING_CLIENTS   | BETTER_HAL        | no_action                                    | COMPUTE_BEST_OFFER | False    |
|          |             |         |                    |                   | stop_hold_down_timer                         |                    |          |
|          |             |         |                    |                   | level_compute                                |                    |          |
|          |             |         |                    |                   | COMPUTATION_DONE                             |                    |          |
+----------+-------------+---------+--------------------+-------------------+----------------------------------------------+--------------------+----------+
| 3        | 0.013643    | 0       | COMPUTE_BEST_OFFER | COMPUTATION_DONE  | no_action                                    | UPDATING_CLIENTS   | False    |
|          |             |         |                    |                   | update_all_lie_fsms_with_computation_results |                    |          |
+----------+-------------+---------+--------------------+-------------------+----------------------------------------------+--------------------+----------+
</pre>

### show node fsm verbose-history

The "<b>show node fsm verbose-history</b>" command shows the 25 most recent
executed events for the Zero Touch Provisioning (ZTP) Finite State Machine (FSM) associated with the currently active
node. 
The most recent event is at the top.

This command shows all events, including the events that are marked as verbose 
by the "<b>show fsm ztp</b>" command. Because of this, the output tends to be dominated by non-interesting verbose
events such as processing periodic offers received from neighbors.
Use the "<b>show node fsm history</b>" command if you only want to see "interesting" events.

Example:

<pre>
agg_101> <b>show node fsm verbose-history</b>
+----------+----------+---------+------------------+----------------+------------------------+-------+----------+
| Sequence | Time     | Verbose | From             | Event          | Actions and            | To    | Implicit |
| Nr       | Delta    | Skipped | State            |                | Pushed Events          | State |          |
+----------+----------+---------+------------------+----------------+------------------------+-------+----------+
| 482554   | 0.215404 | 0       | UPDATING_CLIENTS | NEIGHBOR_OFFER | update_or_remove_offer | None  | False    |
+----------+----------+---------+------------------+----------------+------------------------+-------+----------+
| 482553   | 0.000034 | 0       | UPDATING_CLIENTS | NEIGHBOR_OFFER | update_or_remove_offer | None  | False    |
+----------+----------+---------+------------------+----------------+------------------------+-------+----------+
| 482476   | 0.014348 | 0       | UPDATING_CLIENTS | NEIGHBOR_OFFER | update_or_remove_offer | None  | False    |
+----------+----------+---------+------------------+----------------+------------------------+-------+----------+
.          .          .         .                  .                .                        .       .          .
.          .          .         .                  .                .                        .       .          .
.          .          .         .                  .                .                        .       .          .
+----------+----------+---------+------------------+----------------+------------------------+-------+----------+
| 481836   | 0.000660 | 0       | UPDATING_CLIENTS | NEIGHBOR_OFFER | update_or_remove_offer | None  | False    |
+----------+----------+---------+------------------+----------------+------------------------+-------+----------+
| 481736   | 0.997336 | 0       | UPDATING_CLIENTS | NEIGHBOR_OFFER | update_or_remove_offer | None  | False    |
+----------+----------+---------+------------------+----------------+------------------------+-------+----------+
</pre>

### show nodes

The "<b>show nodes</b>" command shows a summary of all RIFT nodes running in the RIFT protocol engine.

You can make anyone of the listed nodes the currently active node using the "<b>set node</b> <i>node</i>" command.

Example:

<pre>
agg_101> <b>show nodes</b>
+-----------+--------+---------+
| Node      | System | Running |
| Name      | ID     |         |
+-----------+--------+---------+
| agg_101   | 101    | True    |
+-----------+--------+---------+
| agg_102   | 102    | True    |
+-----------+--------+---------+
| agg_201   | 201    | True    |
+-----------+--------+---------+
| agg_202   | 202    | True    |
+-----------+--------+---------+
| core_1    | 1      | True    |
+-----------+--------+---------+
| core_2    | 2      | True    |
+-----------+--------+---------+
| edge_1001 | 1001   | True    |
+-----------+--------+---------+
| edge_1002 | 1002   | True    |
+-----------+--------+---------+
| edge_2001 | 2001   | True    |
+-----------+--------+---------+
| edge_2002 | 2002   | True    |
+-----------+--------+---------+
</pre>

### show nodes level

The "<b>show nodes level</b>" command shows information on automatic level derivation procedures
for all RIFT nodes in the RIFT topology:

Example:

<pre>
agg_101> <b>show nodes level</b>
+-----------+--------+---------+------------+-------+
| Node      | System | Running | Configured | Level |
| Name      | ID     |         | Level      | Value |
+-----------+--------+---------+------------+-------+
| agg_101   | 101    | True    | undefined  | 23    |
+-----------+--------+---------+------------+-------+
| agg_102   | 102    | True    | undefined  | 23    |
+-----------+--------+---------+------------+-------+
| agg_201   | 201    | True    | undefined  | 23    |
+-----------+--------+---------+------------+-------+
| agg_202   | 202    | True    | undefined  | 23    |
+-----------+--------+---------+------------+-------+
| core_1    | 1      | True    | superspine | 24    |
+-----------+--------+---------+------------+-------+
| core_2    | 2      | True    | superspine | 24    |
+-----------+--------+---------+------------+-------+
| edge_1001 | 1001   | True    | leaf       | 0     |
+-----------+--------+---------+------------+-------+
| edge_1002 | 1002   | True    | undefined  | 22    |
+-----------+--------+---------+------------+-------+
| edge_2001 | 2001   | True    | undefined  | 23    |
+-----------+--------+---------+------------+-------+
| edge_2002 | 2002   | True    | leaf       | 0     |
+-----------+--------+---------+------------+-------+
</pre>

### show route prefix <i>prefix</i>

The "<b>show route prefix</b> <i>prefix</i>" command shows the routes for a given prefix in the
Routing Information Base (RIB) of the current node.

Parameter <i>prefix</i> must be an IPv4 prefix or an IPv6 prefix

Example:

<pre>
agg_101> <b>show route prefix ::/0</b>
+--------+-----------+--------------------+
| Prefix | Owner     | Next-hops          |
+--------+-----------+--------------------+
| ::/0   | North SPF | if_101_1 127.0.0.1 |
|        |           | if_101_2 127.0.0.1 |
+--------+-----------+--------------------+
</pre>

### show route prefix <i>prefix</i> owner <i>owner</i>

The "<b>show route prefix</b> <i>prefix</i> <b>owner</b> <i>owner</i>" command shows the routes for
a given prefix and a given owner in the Routing Information Base (RIB) of the current node.

Parameter <i>prefix</i> must be an IPv4 prefix or an IPv6 prefix.

Parameter <i>owner</i> must be <b>south-spf</b> or <b>north-spf</b>.

Example:

<pre>
agg_101> <b>show route prefix ::/0 owner north-spf</b>
+--------+-----------+--------------------+
| Prefix | Owner     | Next-hops          |
+--------+-----------+--------------------+
| ::/0   | North SPF | if_101_1 127.0.0.1 |
|        |           | if_101_2 127.0.0.1 |
+--------+-----------+--------------------+
</pre>

### show routes

The "<b>show routes</b>" command shows all routes in the Routing Information Base (RIB) of the
current node. It shows both the IPv4 RIB and the IPv6 RIB.

Example:

<pre>
agg_101> <b>show routes</b>
IPv4 Routes:
+---------------+-----------+-----------------------+
| Prefix        | Owner     | Next-hops             |
+---------------+-----------+-----------------------+
| 0.0.0.0/0     | North SPF | if_101_1 127.0.0.1    |
|               |           | if_101_2 127.0.0.1    |
+---------------+-----------+-----------------------+
| 1.1.1.0/24    | South SPF | if_101_1001 127.0.0.1 |
+---------------+-----------+-----------------------+
| 1.1.2.0/24    | South SPF | if_101_1001 127.0.0.1 |
+---------------+-----------+-----------------------+
| 1.1.3.0/24    | South SPF | if_101_1001 127.0.0.1 |
+---------------+-----------+-----------------------+
| 1.1.4.0/24    | South SPF | if_101_1001 127.0.0.1 |
+---------------+-----------+-----------------------+
| 1.2.1.0/24    | South SPF | if_101_1002 127.0.0.1 |
+---------------+-----------+-----------------------+
| 1.2.2.0/24    | South SPF | if_101_1002 127.0.0.1 |
+---------------+-----------+-----------------------+
| 1.2.3.0/24    | South SPF | if_101_1002 127.0.0.1 |
+---------------+-----------+-----------------------+
| 1.2.4.0/24    | South SPF | if_101_1002 127.0.0.1 |
+---------------+-----------+-----------------------+
| 99.99.99.0/24 | South SPF | if_101_1001 127.0.0.1 |
|               |           | if_101_1002 127.0.0.1 |
+---------------+-----------+-----------------------+

IPv6 Routes:
+--------+-----------+--------------------+
| Prefix | Owner     | Next-hops          |
+--------+-----------+--------------------+
| ::/0   | North SPF | if_101_1 127.0.0.1 |
|        |           | if_101_2 127.0.0.1 |
+--------+-----------+--------------------+
</pre>

### show spf

The "<b>show spf</b>" command shows the results of the most recent Shortest Path First (SPF) execution for the current node.

Note: the SPF algorithm is also known as the Dijkstra algorithm.

Example:

<pre>
agg_101> <b>show spf</b>
SPF Statistics:
+---------------+----+
| SPF Runs      | 4  |
+---------------+----+
| SPF Deferrals | 19 |
+---------------+----+

South SPF Destinations:
+------------------+------+-------------+------+-----------------------+
| Destination      | Cost | Predecessor | Tags | Next-hops             |
|                  |      | System IDs  |      |                       |
+------------------+------+-------------+------+-----------------------+
| 101 (agg_101)    | 0    |             |      |                       |
+------------------+------+-------------+------+-----------------------+
| 1001 (edge_1001) | 1    | 101         |      | if_101_1001 127.0.0.1 |
+------------------+------+-------------+------+-----------------------+
| 1002 (edge_1002) | 1    | 101         |      | if_101_1002 127.0.0.1 |
+------------------+------+-------------+------+-----------------------+
| 1.1.1.0/24       | 2    | 1001        |      | if_101_1001 127.0.0.1 |
+------------------+------+-------------+------+-----------------------+
| 1.1.2.0/24       | 2    | 1001        |      | if_101_1001 127.0.0.1 |
+------------------+------+-------------+------+-----------------------+
| 1.1.3.0/24       | 2    | 1001        |      | if_101_1001 127.0.0.1 |
+------------------+------+-------------+------+-----------------------+
| 1.1.4.0/24       | 2    | 1001        |      | if_101_1001 127.0.0.1 |
+------------------+------+-------------+------+-----------------------+
| 1.2.1.0/24       | 2    | 1002        |      | if_101_1002 127.0.0.1 |
+------------------+------+-------------+------+-----------------------+
| 1.2.2.0/24       | 2    | 1002        |      | if_101_1002 127.0.0.1 |
+------------------+------+-------------+------+-----------------------+
| 1.2.3.0/24       | 2    | 1002        |      | if_101_1002 127.0.0.1 |
+------------------+------+-------------+------+-----------------------+
| 1.2.4.0/24       | 2    | 1002        |      | if_101_1002 127.0.0.1 |
+------------------+------+-------------+------+-----------------------+
| 99.99.99.0/24    | 2    | 1001        | 9992 | if_101_1001 127.0.0.1 |
|                  |      | 1002        | 9991 | if_101_1002 127.0.0.1 |
+------------------+------+-------------+------+-----------------------+

North SPF Destinations:
+---------------+------+-------------+------+--------------------+
| Destination   | Cost | Predecessor | Tags | Next-hops          |
|               |      | System IDs  |      |                    |
+---------------+------+-------------+------+--------------------+
| 1 (core_1)    | 1    | 101         |      | if_101_1 127.0.0.1 |
+---------------+------+-------------+------+--------------------+
| 2 (core_2)    | 1    | 101         |      | if_101_2 127.0.0.1 |
+---------------+------+-------------+------+--------------------+
| 101 (agg_101) | 0    |             |      |                    |
+---------------+------+-------------+------+--------------------+
| 0.0.0.0/0     | 2    | 1           |      | if_101_1 127.0.0.1 |
|               |      | 2           |      | if_101_2 127.0.0.1 |
+---------------+------+-------------+------+--------------------+
| ::/0          | 2    | 1           |      | if_101_1 127.0.0.1 |
|               |      | 2           |      | if_101_2 127.0.0.1 |
+---------------+------+-------------+------+--------------------+
</pre>

### show spf direction <i>direction</i>

The "<b>show spf direction</b> <i>direction</i>" command shows the results of the most recent Shortest Path First (SPF) execution for the current node in the specified direction.

Parameter <i>direction</i> must be <b>south</b> or <b>north</b>

Example:

<pre>
agg_101> <b>show spf direction north</b>
North SPF Destinations:
+---------------+------+-------------+------+--------------------+
| Destination   | Cost | Predecessor | Tags | Next-hops          |
|               |      | System IDs  |      |                    |
+---------------+------+-------------+------+--------------------+
| 1 (core_1)    | 1    | 101         |      | if_101_1 127.0.0.1 |
+---------------+------+-------------+------+--------------------+
| 2 (core_2)    | 1    | 101         |      | if_101_2 127.0.0.1 |
+---------------+------+-------------+------+--------------------+
| 101 (agg_101) | 0    |             |      |                    |
+---------------+------+-------------+------+--------------------+
| 0.0.0.0/0     | 2    | 1           |      | if_101_1 127.0.0.1 |
|               |      | 2           |      | if_101_2 127.0.0.1 |
+---------------+------+-------------+------+--------------------+
| ::/0          | 2    | 1           |      | if_101_1 127.0.0.1 |
|               |      | 2           |      | if_101_2 127.0.0.1 |
+---------------+------+-------------+------+--------------------+
</pre>

### show spf direction <i>direction</i> destination <i>destination</i>

The "<b>show spf direction</b> <i>direction</i> <b>destination</b> <i>destination</i>" command shows
the results of the most recent Shortest Path First (SPF) execution for the specified destination on
the current node in the specified direction.

Parameter <i>direction</i> must be <b>south</b> or <b>north</b>

Parameter <i>destination</i> must be one of the following:
 * The system-id of a node (an integer)
 * An IPv4 prefix
 * An IPv6 prefix

Example:

<pre>
agg_101> <b>show spf direction north destination ::/0</b>
+-------------+------+-------------+------+--------------------+
| Destination | Cost | Predecessor | Tags | Next-hops          |
|             |      | System IDs  |      |                    |
+-------------+------+-------------+------+--------------------+
| ::/0        | 2    | 1           |      | if_101_1 127.0.0.1 |
|             |      | 2           |      | if_101_2 127.0.0.1 |
+-------------+------+-------------+------+--------------------+
</pre>

Example:

<pre>
agg_101> <b>show spf direction north destination 5</b>
Destination 5 not present
</pre>

### show tie-db

The "<b>show tie-db</b>" command shows the contents of the Topology Information Element Database (TIE-DB) for the current node.

Note: the TIE-DB is also known as the Link-State Database (LSDB)

Example:

<pre>
agg_101> show tie-db
+-----------+------------+--------+--------+--------+----------+-----------------------+
| Direction | Originator | Type   | TIE Nr | Seq Nr | Lifetime | Contents              |
+-----------+------------+--------+--------+--------+----------+-----------------------+
| South     | 1          | Node   | 1      | 5      | 603378   | Name: core_1          |
|           |            |        |        |        |          | Level: 2              |
|           |            |        |        |        |          | Neighbor: 101         |
|           |            |        |        |        |          |   Level: 1            |
|           |            |        |        |        |          |   Cost: 1             |
|           |            |        |        |        |          |   Bandwidth: 100 Mbps |
|           |            |        |        |        |          |   Link: 1-1           |
|           |            |        |        |        |          | Neighbor: 102         |
|           |            |        |        |        |          |   Level: 1            |
|           |            |        |        |        |          |   Cost: 1             |
|           |            |        |        |        |          |   Bandwidth: 100 Mbps |
|           |            |        |        |        |          |   Link: 2-1           |
|           |            |        |        |        |          | Neighbor: 201         |
|           |            |        |        |        |          |   Level: 1            |
|           |            |        |        |        |          |   Cost: 1             |
|           |            |        |        |        |          |   Bandwidth: 100 Mbps |
|           |            |        |        |        |          |   Link: 3-1           |
|           |            |        |        |        |          | Neighbor: 202         |
|           |            |        |        |        |          |   Level: 1            |
|           |            |        |        |        |          |   Cost: 1             |
|           |            |        |        |        |          |   Bandwidth: 100 Mbps |
|           |            |        |        |        |          |   Link: 4-1           |
+-----------+------------+--------+--------+--------+----------+-----------------------+
| South     | 1          | Prefix | 1      | 1      | 603378   | Prefix: 0.0.0.0/0     |
|           |            |        |        |        |          |   Metric: 1           |
|           |            |        |        |        |          | Prefix: ::/0          |
|           |            |        |        |        |          |   Metric: 1           |
+-----------+------------+--------+--------+--------+----------+-----------------------+
.           .            .        .        .        .          .                       .
.           .            .        .        .        .          .                       .
.           .            .        .        .        .          .                       .
+-----------+------------+--------+--------+--------+----------+-----------------------+
| North     | 1002       | Prefix | 1      | 1      | 603378   | Prefix: 1.2.1.0/24    |
|           |            |        |        |        |          |   Metric: 1           |
|           |            |        |        |        |          | Prefix: 1.2.2.0/24    |
|           |            |        |        |        |          |   Metric: 1           |
|           |            |        |        |        |          | Prefix: 1.2.3.0/24    |
|           |            |        |        |        |          |   Metric: 1           |
|           |            |        |        |        |          | Prefix: 1.2.4.0/24    |
|           |            |        |        |        |          |   Metric: 1           |
|           |            |        |        |        |          | Prefix: 99.99.99.0/24 |
|           |            |        |        |        |          |   Metric: 1           |
|           |            |        |        |        |          |   Tag: 9992           |
+-----------+------------+--------+--------+--------+----------+-----------------------+
</pre>

### stop

The "<b>stop</b> command closes the CLI session and terminates the RIFT engine.

Note: The <b>stop</b> command is similar to the <b>exit</b> command, except that the <b>exit</b>
command leaves the RIFT engine running when executed from a Telnet session.

Example:

<pre>
(env) $ python rift topology/two_by_two_by_two.yaml
Command Line Interface (CLI) available on port 50102
</pre>

<pre>
$ telnet localhost 50102
Trying 127.0.0.1...
Connected to localhost.
Escape character is '^]'.
agg_101> <b>stop</b>
$ 
</pre>
