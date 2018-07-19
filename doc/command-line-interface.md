# Command Line Interface (CLI) Reference

* [Connect to the CLI](#connect-to-the-cli)
* [Entering CLI commands](#entering-cli-commands)
* [Command Line Interface Commands](#command-line-interface-commands)
  * [set node](#set-node)
  * [show fsm](#show-fsm)
  * [show interfaces](#show-interfaces)
  * [show interface](#show-interface)
  * [show interfaces](#show-interfaces)
  * [show node](#show-node)
  * [show nodes](#show-nodes)

## Connect to the CLI

You can connect to the Command Line Interface (CLI) using a Telnet client. Assuming you are connecting from the same 
device as where the RIFT engine is running, the hostname is localhost. The port should be the port number that RIFT 
reported when it was started:

<pre>
$ <b>telnet localhost 55018</b>
Trying 127.0.0.1...
Connected to localhost.
Escape character is '^]'.
Brunos-MacBook1> 
</pre>

You should get a prompt containing the name of the RIFT node. In this example the name of the RIFT node is 
"Brunos-MacBook1".

By default (i.e. if no configuration file is specified) a single instance of the RIFT protocol engine (a single 
so-called RIFT node) is started. And by default, the name of that single RIFT node is equal to the hostname of the 
computer on which the RIFT node is running.

## Entering CLI Commands

You can enter CLI commands at the CLI prompt. For example, try entering the <b>help</b> command:

<pre>
Brunos-MacBook1> <b>help</b>
set node &lt;node&gt;
show interface &lt;interface&gt;
show fsm lie 
show fsm ztp 
show interfaces 
show node 
show nodes 
</pre>

(You may see more commands in the help output if you are running a more recent version of the code.)

Unfortunately, the CLI does not yet support using cursor-up or cursor-down or ctrl-p or ctrl-n to go the the previous 
or next command in the command history. It does also not support tab command completion; all commands must be entered 
in full manually. And you can also not yet use ? for context-sensitive help. These features will be added in a 
future version.

## Command Line Interface Commands

### set node

The "<b>set node</b><i>node-name</i>" command changes the currently active RIFT node to the node with the specified 
RIFT node name:

<pre>
agg_101> set node core_1
core_1> 
</pre>

Note: you can get a list of RIFT nodes present in the current RIFT protocol engine using the <b>show nodes</b> command.

### show fsm

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

### show interface

The "<b>show interface</b><i>interface-name</i>" command reports more detailed information about a single interface. Note that "interface" is singular without an s.

Here is an example of the output when there is no neighbor (note that the state of the interface is ONE_WAY):

<pre>
Brunos-MacBook1> <b>show interface en0</b>
Interface:
+-------------------------------------+---------------------+
| Interface Name                      | en0                 |
| Advertised Name                     | Brunos-MacBook1-en0 |
| Interface IPv4 Address              | 192.168.2.163       |
| Metric                              | 100                 |
| Receive LIE IPv4 Multicast Address  | 224.0.0.120         |
| Transmit LIE IPv4 Multicast Address | 224.0.0.120         |
| Receive LIE IPv6 Multicast Address  | FF02::0078          |
| Transmit LIE IPv6 Multicast Address | FF02::0078          |
| Receive LIE Port                    | 10000               |
| Transmit LIE Port                   | 10000               |
| Receive TIE Port                    | 10001               |
| System ID                           | 667f3a2b1a721f01    |
| Local ID                            | 1                   |
| MTU                                 | 1500                |
| POD                                 | 0                   |
| State                               | ONE_WAY             |
| Neighbor                            | No                  |
+-------------------------------------+---------------------+
</pre>

Here is an example of the output when there is a neighbor (note that the state of the interface is THREE_WAY):

<pre>
Brunos-MacBook1> <b>show interface en0</b>
Interface:
+-------------------------------------+---------------------+
| Interface Name                      | en0                 |
| Advertised Name                     | Brunos-MacBook1-en0 |
| Interface IPv4 Address              | 192.168.2.163       |
| Metric                              | 100                 |
| Receive LIE IPv4 Multicast Address  | 224.0.0.120         |
| Transmit LIE IPv4 Multicast Address | 224.0.0.120         |
| Receive LIE IPv6 Multicast Address  | FF02::0078          |
| Transmit LIE IPv6 Multicast Address | FF02::0078          |
| Receive LIE Port                    | 10000               |
| Transmit LIE Port                   | 10000               |
| Receive TIE Port                    | 10001               |
| System ID                           | 667f3a2b1a721f01    |
| Local ID                            | 1                   |
| MTU                                 | 1500                |
| POD                                 | 0                   |
| State                               | THREE_WAY           |
| Neighbor                            | Yes                 |
+-------------------------------------+---------------------+

Neighbor:
+----------------------------------+---------------------+
| Name                             | Brunos-MacBook1-en0 |
| System ID                        | 667f3a2b1a73cb01    |
| IPv4 Address                     | 192.168.2.163       |
| LIE UDP Source Port              | 55048               |
| Link ID                          | 1                   |
| Level                            | 0                   |
| Flood UDP Port                   | 10001               |
| MTU                              | 1500                |
| POD                              | 0                   |
| Hold Time                        | 3                   |
| Not a ZTP Offer                  | False               |
| You Are Not a ZTP Flood Repeater | False               |
| Your System ID                   | 667f3a2b1a721f01    |
| Your Local ID                    | 1                   |
+----------------------------------+---------------------+
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

### show nodes

The "<b>show nodes</b>" command (node is multiple with an s) lists all RIFT nodes present in the current RIFT
protocol engine:

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

