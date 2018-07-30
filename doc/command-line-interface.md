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

Go to the top of the directory where the rift-python repository was cloned (in this example we assume it was cloned into your home directory):

<pre>
$ <b>cd ${HOME}/rift-python</b>
</pre>

Make sure your virtual environment (that was created during the installation process) is activated:

<pre>
$ <b>source env/bin/activate</b>
(env) $ 
</pre>

Start the rift-python package:

<pre>
(env) $ <b>python rift-python</b>
Command Line Interface (CLI) available on port 61375
</pre>

Optionally you may pass a topology YAML file as a command-line argument:

<pre>
(env) $ <b>python rift-python topology/two_by_two_by_two_ztp.yaml</b>
Command Line Interface (CLI) available on port 61377
</pre>


When you start the Python RIFT protocol engine, it reports a port number that you can use to connect one or more CLI 
sessions.

You can connect to the Command Line Interface (CLI) using a Telnet client. Assuming you are connecting from the same 
device as where the RIFT engine is running, the hostname is localhost. 

<pre>
$ <b>telnet localhost 61375 </b>
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
| Superspine Flag                       | True             |
| Zero Touch Provisioning (ZTP) Enabled | False            |
| ZTP FSM State                         | UPDATING_CLIENTS |
| ZTP Hold Down Timer                   | Stopped          |
| Highest Available Level (HAL)         | None             |
| Highest Adjacency Three-way (HAT)     | None             |
| Level Value                           | 1                |
| Multicast Loop                        | True             |
| Receive LIE IPv4 Multicast Address    | 224.0.0.81       |
| Transmit LIE IPv4 Multicast Address   | 224.0.0.120      |
| Receive LIE IPv6 Multicast Address    | FF02::0078       |
| Transmit LIE IPv6 Multicast Address   | FF02::0078       |
| Receive LIE Port                      | 20102            |
| Transmit LIE Port                     | 10000            |
| LIE Send Interval                     | 1.0 secs         |
| Receive TIE Port                      | 10001            |
+---------------------------------------+------------------+

Received Offers:
+-------------+-----------+-------+-----------------+-----------+-------+------------+---------+--------------------------+
| Interface   | System ID | Level | Not A ZTP Offer | State     | Best  | Best 3-Way | Removed | Removed Reason           |
+-------------+-----------+-------+-----------------+-----------+-------+------------+---------+--------------------------+
| if_101_1    | 1         | 24    | True            | ONE_WAY   | False | False      | True    | Not a ZTP offer flag set |
+-------------+-----------+-------+-----------------+-----------+-------+------------+---------+--------------------------+
| if_101_1001 | 1001      | 0     | True            | THREE_WAY | False | False      | True    | Not a ZTP offer flag set |
+-------------+-----------+-------+-----------------+-----------+-------+------------+---------+--------------------------+
| if_101_1002 | 1002      | 0     | True            | THREE_WAY | False | False      | True    | Not a ZTP offer flag set |
+-------------+-----------+-------+-----------------+-----------+-------+------------+---------+--------------------------+
| if_101_2    | 2         | 2     | True            | THREE_WAY | False | False      | True    | Not a ZTP offer flag set |
+-------------+-----------+-------+-----------------+-----------+-------+------------+---------+--------------------------+

Sent Offers:
+-------------+-----------+-------+-----------------+-----------+
| Interface   | System ID | Level | Not A ZTP Offer | State     |
+-------------+-----------+-------+-----------------+-----------+
| if_101_1    | None      | 1     | False           | ONE_WAY   |
+-------------+-----------+-------+-----------------+-----------+
| if_101_1001 | 1001      | 1     | False           | THREE_WAY |
+-------------+-----------+-------+-----------------+-----------+
| if_101_1002 | 1002      | 1     | False           | THREE_WAY |
+-------------+-----------+-------+-----------------+-----------+
| if_101_2    | 2         | 1     | False           | THREE_WAY |
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

