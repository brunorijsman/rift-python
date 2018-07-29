# Command Line Interface (CLI) Reference

* [Connect to the CLI](#connect-to-the-cli)
* [Entering CLI commands](#entering-cli-commands)
* [Command Line Interface Commands](#command-line-interface-commands)
  * [set level <i>level</i>](#set-level-level)
  * [set node <i>node</i>](#set-node-node)
  * [show interface <i>interface</i>](#show-interface-interface)
  * [show interface <i>interface</i> fsm history](#show-interface-interface-fsm-history)
  * [show interface <i>interface</i> fsm verbose-history](#show-interface-interface-fsm-verbose-history)
  * [show interfaces](#show-interfaces)
  * [show fsm <i>fsm</i>](#show-fsm-fsm)
  * [show interfaces](#show-interfaces)
  * [show node](#show-node)
  * [show node fsm history](#show-node-fsm-history)
  * [show node fsm verbose-history](#show-node-fsm-verbose-history)
  * [show nodes](#show-nodes)
  * [show nodes level](#show-nodes-level)

## Connect to the CLI

When you start the Python RIFT protocol engine, it reports a port number that you can use to connect one or more CLI 
sessions:

<pre>
(env) $ <b>python main.py two_by_two_by_two.yaml</b>
Command Line Interface (CLI) available on port 52036
</pre>

You can connect to the Command Line Interface (CLI) using a Telnet client. Assuming you are connecting from the same 
device as where the RIFT engine is running, the hostname is localhost. 

<pre>
$ <b>telnet localhost 52036</b>
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
set level &lt;level&gt; 
set node &lt;node&gt; 
show interface &lt;interface&gt; 
show interface &lt;interface&gt; fsm history 
show interface &lt;interface&gt; fsm verbose-history 
show fsm lie 
show fsm ztp 
show interfaces 
show node 
show node fsm history 
show node fsm verbose-history 
show nodes 
show nodes level 
</pre>

Unfortunately, the CLI does not yet support any of the following features:

* Command completion: you must manually enter the complete command; you cannot enter partial commands or use
tab to complete commands.

* Interactive command history: you cannot use cursor-up or cursor-down or ctrl-p or ctrl-n to go the 
the previous or next command in the command history. 

* Interactive context-senstive help: you can enter "help" or "?" and press enter at the end of a partial command
line to get context-senstive help. But after reading the help text, you must manually re-enter the command line. 

## Command Line Interface Commands

### set level <i>level</i>

The "<b>set level</b> <i>level</i>" command changes the level of the currently active RIFT node.

The valid values for the <i>level</i> parameter are <b>undefined</b>, <b>leaf</b>, <b>leaf-to-leaf</b>, 
<b>superspine</b>, or an integer non-negative number.

These <i>level</i> values are mapped to the paramaters in the protocol specification as follows:

| <i>level</i> value | LEAF_ONLY | LEAF_2_LEAF | SUPERSPINE_FLAG | CONFIGURED_LEVEL |
| --- | --- | --- | --- | --- |
| <b>undefined<b> | false | false | false | UNDEFINED_LEVEL |
| <b>leaf<b> | true | false | false | UNDEFINED_LEVEL (see note 1) |
| <b>leaf-to-leaf<b> | true | true | false | UNDEFINED_LEVEL (see note 1) |
| <b>superspine<b> | false | false | true | UNDEFINED_LEVEL (see note 2) |
| integer non-negative number | true if level = 0, false otherwise | false | false | level |

Note 1: Even if the CONFIGURED_LEVEL is UNDEFINED_LEVEL, nodes with the LEAF_ONLY flag set will advertise level 
leaf_level (= 0) in the sent LIE packets.

Note 2: Event if CONFIGURED_LEVEL is UNDEFINED_LEVEL, nodes with the SUPERSPINE_FLAG set will advertise level 
default_superspine_level (= 24) in the sent LIE packets.

Example:

<pre>
core_1> set level undefined
</pre>

### set node <i>node</i>

The "<b>set node</b> <i>node-name</i>" command changes the currently active RIFT node to the node with the specified 
RIFT node name:

Note: you can get a list of RIFT nodes present in the current RIFT protocol engine using the <b>show nodes</b> command.

Example:

<pre>
agg_101> set node core_1
core_1> 
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
Use the "<b>show interface</b> <i>interface</i> <b>fsm verbose-history</b>" command if you only want to see
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

### show fsm <i>fsm</i>

The "<b>show fsm</b> <i>fsm-name</i>" command shows the definition of the specified Finite State Machine (FSM).

Parameter <i>fsm-name</i> can be one of the following values:

* <b>lie</b>: Show the Link Information Element (LIE) FSM.
* <b>ztp</b>: Show the Zero Touch Provisioning (ZTP) FSM.

The output below is edited to make it shorter.

<pre>
agg_202> <b>show fsm lie</b>
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
+-------------------------------+
| Event                         |
+-------------------------------+
| TIMER_TICK                    |
+-------------------------------+
.                               .
.                               .
.                               .
+-------------------------------+
| SEND_LIE                      |
+-------------------------------+
| UPDATE_ZTP_OFFER              |
+-------------------------------+

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
| THREE_WAY  | UPDATE_ZTP_OFFER            | -         | send_offer_to_ztp_fsm   | -           |
+------------+-----------------------------+-----------+-------------------------+-------------+

State entry actions:
+---------+---------+
| State   | Actions |
+---------+---------+
| ONE_WAY | cleanup |
+---------+---------+
</pre>

### show interfaces

The "<b>show interfaces</b>" command reports a summary of all interfaces configured on the RIFT node. Note that "interfaces" is plural with an s. It only reports the interfaces on which RIFT is running; your device may have additional interfaces on which RIFT is not running.

<pre>
Brunos-MacBook1> <b>show interfaces</b>
+-----------+----------+-----------+----------+
| Interface | Neighbor | Neighbor  | Neighbor |
| Name      | Name     | System ID | State    |
+-----------+----------+-----------+----------+
| en0       |          |           | ONE_WAY  |
+-----------+----------+-----------+----------+
</pre>

In the above example, RIFT is running on interface en0 but there is no RIFT neighbor on that interface. The example below does have a RIFT neighbor and the adjacency to that neighbor is in state THREE_WAY:

<pre>
Brunos-MacBook1> <b>show interfaces</b>
+-----------+---------------------+------------------+-----------+
| Interface | Neighbor            | Neighbor         | Neighbor  |
| Name      | Name                | System ID        | State     |
+-----------+---------------------+------------------+-----------+
| en0       | Brunos-MacBook1-en0 | 667f3a2b1a737c01 | THREE_WAY |
+-----------+---------------------+------------------+-----------+
</pre>

### show node

The "<b>show node</b>" command (node is singular without an s) reports the details for the currently active RIFT node:

<pre>
Brunos-MacBook1> <b>show node</b>
+-------------------------------------+------------------+
| Name                                | Brunos-MacBook1  |
| Passive                             | False            |
| Running                             | True             |
| System ID                           | 667f3a2b1a721f01 |
| Configured Level                    | 0                |
| Multicast Loop                      | True             |
| Receive LIE IPv4 Multicast Address  | 224.0.0.120      |
| Transmit LIE IPv4 Multicast Address | 224.0.0.120      |
| Receive LIE IPv6 Multicast Address  | FF02::0078       |
| Transmit LIE IPv6 Multicast Address | FF02::0078       |
| Receive LIE Port                    | 10000            |
| Transmit LIE Port                   | 10000            |
| LIE Send Interval                   | 1.0 secs         |
| Receive TIE Port                    | 10001            |
+-------------------------------------+------------------+
</pre>

### show node fsm history

### show node fsm verbose-history

### show nodes

The "<b>show nodes</b>" command shows a summary of all RIFT nodes running in the
RIFT protocol engine:

<pre>
agg_101> <b>show nodes summary</b>
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

The "<b>show nodes summary</b>" command shows information on automatic level derivation procedures
for all RIFT nodes in the RIFT topology:

<pre>
agg_101> <b>show nodes level</b>
+-----------+--------+---------+------------+-----------+
| Node      | System | Running | Configured | Level     |
| Name      | ID     |         | Level      | Value     |
+-----------+--------+---------+------------+-----------+
| agg_101   | 101    | True    | undefined  | undefined |
+-----------+--------+---------+------------+-----------+
| agg_102   | 102    | True    | undefined  | undefined |
+-----------+--------+---------+------------+-----------+
| agg_201   | 201    | True    | undefined  | undefined |
+-----------+--------+---------+------------+-----------+
| agg_202   | 202    | True    | undefined  | undefined |
+-----------+--------+---------+------------+-----------+
| core_1    | 1      | True    | superspine | undefined |
+-----------+--------+---------+------------+-----------+
| core_2    | 2      | True    | superspine | undefined |
+-----------+--------+---------+------------+-----------+
| edge_1001 | 1001   | True    | leaf       | undefined |
+-----------+--------+---------+------------+-----------+
| edge_1002 | 1002   | True    | undefined  | undefined |
+-----------+--------+---------+------------+-----------+
| edge_2001 | 2001   | True    | undefined  | undefined |
+-----------+--------+---------+------------+-----------+
| edge_2002 | 2002   | True    | leaf       | undefined |
+-----------+--------+---------+------------+-----------+
</pre>

