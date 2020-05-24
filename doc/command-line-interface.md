# Command Line Interface (CLI) Reference

* [Connect to the CLI](#connect-to-the-cli)
* [Entering CLI commands](#entering-cli-commands)
* [Command Line Interface Commands](#command-line-interface-commands)
  * [clear engine statistics](#clear-engine-statistics)
  * [clear interface <i>interface</i> statistics](#clear-interface-interface-statistics)
  * [clear node statistics](#clear-node-statistics)
  * [exit](#exit)
  * [set interface <i>interface</i> failure <i>failure</i>](#set-interface-interface-failure-failure)
  * [set level <i>level</i>](#set-level-level)
  * [set node <i>node</i>](#set-node-node)
  * [show disaggregation](#show-disaggregation)
  * [show engine](#show-engine)
  * [show engine statistics](#show-engine-statistics)
  * [show engine statistics exclude-zero](#show-engine-statistics-exclude-zero)
  * [show flooding-reduction](#show-flooding-reduction)
  * [show forwarding](#show-forwarding)
  * [show forwarding family <i>family</i>](#show-forwarding-family-family)
  * [show forwarding prefix <i>prefix</i>](#show-forwarding-prefix-prefix)
  * [show fsm <i>fsm</i>](#show-fsm-fsm)
  * [show interface <i>interface</i>](#show-interface-interface)
  * [show interface <i>interface</i> fsm history](#show-interface-interface-fsm-history)
  * [show interface <i>interface</i> fsm verbose-history](#show-interface-interface-fsm-verbose-history)
  * [show interface <i>interface</i> queues](#show-interface-interface-queues)
  * [show interface <i>interface</i> sockets](#show-interface-interface-sockets)
  * [show interface <i>interface</i> statistics](#show-interface-interface-statistics)
  * [show interface <i>interface</i> statistics exclude-zero](#show-interface-interface-statistics-exclude-zero)
  * [show interfaces](#show-interfaces)
  * [show kernel addresses](#show-kernel-addresses)
  * [show kernel links](#show-kernel-links)
  * [show kernel routes](#show-kernel-routes)
  * [show kernel routes table <i>table</i>](#show-kernel-routes-table-table)
  * [show kernel routes table <i>table</i> prefix <i>prefix</i>](#show-kernel-routes-table-table-prefix-prefix)
  * [show node](#show-node)
  * [show node fsm history](#show-node-fsm-history)
  * [show node fsm verbose-history](#show-node-fsm-verbose-history)
  * [show node statistics](#show-node-statistics)
  * [show node statistics exclude-zero](#show-node-statistics-exclude-zero)
  * [show nodes](#show-nodes)
  * [show nodes level](#show-nodes-level)
  * [show routes](#show-routes)
  * [show routes family <i>family</i>](#show-routes-family-family)
  * [show routes prefix <i>prefix</i>](#show-routes-prefix-prefix)
  * [show routes prefix <i>prefix</i> owner <i>owner</i>](#show-routes-prefix-prefix-owner-owner)
  * [show spf](#show-spf)
  * [show spf direction <i>direction</i>](#show-spf-direction-direction)
  * [show spf direction <i>direction</i> destination <i>destination</i>](#show-spf-direction-direction-destination-destination)
  * [show tie-db](#show-tie-db)
  * [show tie-db direction <i>direction</i>](#show-tie-db-direction-direction)
  * [show tie-db direction <i>direction</i> originator <i>originator</i>](#show-tie-db-direction-direction-originator)
  * [show tie-db direction <i>direction</i> originator <i>originator</i> tie-type <i>tie-type</i>](#show-tie-db-direction-direction-originator-tie-type-tie-type)
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

<!-- OUTPUT-START: agg_101> help -->
<pre>
agg_101> <b>help</b>
clear engine statistics 
clear interface &lt;interface&gt; statistics 
clear node statistics 
exit 
help 
set interface &lt;interface&gt; failure &lt;failure&gt; 
set level &lt;level&gt; 
set node &lt;node&gt; 
show disaggregation 
show engine 
show engine statistics 
show engine statistics exclude-zero 
show flooding-reduction 
show forwarding 
show forwarding family &lt;family&gt; 
show forwarding prefix &lt;prefix&gt; 
show fsm lie 
show fsm ztp 
show interface &lt;interface&gt; 
show interface &lt;interface&gt; fsm history 
show interface &lt;interface&gt; fsm verbose-history 
show interface &lt;interface&gt; queues 
show interface &lt;interface&gt; security 
show interface &lt;interface&gt; sockets 
show interface &lt;interface&gt; statistics 
show interface &lt;interface&gt; statistics exclude-zero 
show interface &lt;interface&gt; tides 
show interfaces 
show kernel addresses 
show kernel links 
show kernel routes 
show kernel routes table &lt;table&gt; 
show kernel routes table &lt;table&gt; prefix &lt;prefix&gt; 
show node 
show node fsm history 
show node fsm verbose-history 
show node statistics 
show node statistics exclude-zero 
show nodes 
show nodes level 
show routes 
show routes family &lt;family&gt; 
show routes prefix &lt;prefix&gt; 
show routes prefix &lt;prefix&gt; owner &lt;owner&gt; 
show security 
show spf 
show spf direction &lt;direction&gt; 
show spf direction &lt;direction&gt; destination &lt;destination&gt; 
show tie-db 
show tie-db direction &lt;direction&gt; 
show tie-db direction &lt;direction&gt; originator &lt;originator&gt; 
show tie-db direction &lt;direction&gt; originator &lt;originator&gt; tie-type &lt;tie-type&gt; 
stop
</pre>
<!-- OUTPUT-END -->

If you are connected to the CLI using Telnet, you can use the following keys for editing:

* Cursor-Left: Move cursor on character left.

* Cursor-Right: Move cursor on character right

* Cursor-Up or Control-P: Go to the previous command in command history.

* Cursor-Down or Control-N: Go to the next command in command history.

* Control-A: Move cursor to the start of the line.

* Control-E: Move cursor to the end of the line.

* Question mark: Context-sensitive help.

The CLI does not yet support the following features:

* Tab to complete commands.

## Command Line Interface Commands

### clear engine statistics

The "<b>clear engine statistics</b>" command clears (i.e. resets to zero) all the statistics of the
RIFT-Python engine.

<!-- OUTPUT-START: agg_101> clear engine statistics -->
<pre>
agg_101> <b>clear engine statistics</b>
</pre>
<!-- OUTPUT-END -->

See also: [show engine statistics](#show-engine-statistics), 
[show engine statistics exclude-zero](#show-engine-statistics-exclude-zero)

### clear interface <i>interface</i> statistics

The "<b>clear interface</b> <i>interface</i> <b>statistics</b>" command clears (i.e. resets to zero)
all the statistics of the specified interface.

<!-- OUTPUT-START: agg_101> clear interface if_101_1 statistics -->
<pre>
agg_101> <b>clear interface if_101_1 statistics</b>
</pre>
<!-- OUTPUT-END -->

See also: [show interface <i>interface</i> statistics](#show-interface-interface-statistics),
[show interface <i>interface</i> statistics exclude-zero](#show-interface-interface-statistics-exclude-zero)

### clear node statistics

The "<b>clear node statistics</b>" clears (i.e. resets to zero) all the statistics of the current
node.

<!-- OUTPUT-START: agg_101> clear node statistics -->
<pre>
agg_101> <b>clear node statistics</b>
</pre>
<!-- OUTPUT-END -->

See also: [show node statistics](#show-node-statistics),
[show node statistics exclude-zero](#show-interface-interface-statistics-exclude-zero)

### exit

The "<b>exit</b> command closes the CLI session.

Example:

<pre>
(env) $ python rift topology/two_by_two_by_two.yaml
Command Line Interface (CLI) available on port 50102
</pre>

<!-- OUTPUT-MANUAL: agg_101> exit -->
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

The "<b>set interface</b> <i>interface</i> <b>failure</b> <i>failure</i>" command enables or
disables a simulated failure of an interface.

The <i>failure</i> parameter can be one of the following:

| <i>failure</i> | Meaning |
| --- | --- |
| ok | The interface is OK. There is no failure. |
| failed | There is a bi-directional failure on the interface. Both sent and received packets are dropped. |
| tx-failed | There is a uni-directional failure on the interface. Sent (TX) packets are dropped. Received (RX) packets are delivered. |
| rx-failed | There is a uni-directional failure on the interface. Sent (TX) packets are delivered. Received (RX) packets are dropped. |

Example:

<!-- OUTPUT-START: agg_101> set interface if1 failure failed -->
<pre>
agg_101> <b>set interface if1 failure failed</b>
Error: interface if1 not present
</pre>
<!-- OUTPUT-END -->

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

<!-- OUTPUT-START: agg_101> set level undefined -->
<pre>
agg_101> <b>set level undefined</b>
</pre>
<!-- OUTPUT-END -->

### set node <i>node</i>

The "<b>set node</b> <i>node-name</i>" command changes the currently active RIFT node to the node with the specified 
RIFT node name:

Note: you can get a list of RIFT nodes present in the current RIFT protocol engine using the <b>show nodes</b> command.

Example:

<!-- OUTPUT-MANUAL: agg_101> set node core_1 -->
<pre>
agg_101> <b>set node core_1</b>
core_1> 
</pre>

### show disaggregation

The "<b>show disaggregation</b>" command all information related to automatic disaggregation.

It reports several tables:

 * The **Same Level Nodes** table reports which other nodes at the same level this node is aware of.
   It also reports which north-bound and south-bound adjacencies those nodes have. And finally
   it reports which south-bound adjacencies those nodes are missing as compared to this node.
   A missing south-bound adjacency triggers positive disaggregation.

 * The **Partially Connected Interfaces** table reports which interfaces are partially connected
   (i.e. the neighbor is not connected to the full set of same-level nodes) and which nodes
   they are missing connectivity to.

 * The **Positive Disaggregation TIEs** table report all positive disaggregation TIEs, both
   received ones and originated ones.

 * The **Negative Disaggregation TIEs** table report all negative disaggregation TIEs, both
   received ones and originated ones.

<!-- OUTPUT-START: agg_101> show disaggregation -->
<pre>
agg_101> <b>show disaggregation</b>
Same Level Nodes:
+-----------+-------------+-------------+-------------+-------------+
| Node      | North-bound | South-bound | Missing     | Extra       |
| System ID | Adjacencies | Adjacencies | South-bound | South-bound |
|           |             |             | Adjacencies | Adjacencies |
+-----------+-------------+-------------+-------------+-------------+
| 102       | 1           | 1001        |             |             |
|           |             | 1002        |             |             |
+-----------+-------------+-------------+-------------+-------------+
</pre>
<!-- OUTPUT-END -->

### show engine

The "<b>show engine</b>" command shows the status of the RIFT engine, i.e. global information
that applies to all nodes running in the RIFT engine.

Example:

<!-- OUTPUT-START: agg_101> show engine -->
<pre>
agg_101> <b>show engine</b>
+----------------------------------+----------------------+
| Stand-alone                      | False                |
| Interactive                      | True                 |
| Simulated Interfaces             | True                 |
| Physical Interface               | ens5                 |
| Telnet Port File                 | None                 |
| IPv4 Multicast Loopback          | True                 |
| IPv6 Multicast Loopback          | True                 |
| Number of Nodes                  | 10                   |
| Transmit Source Address          | 127.0.0.1            |
| Flooding Reduction Enabled       | True                 |
| Flooding Reduction Redundancy    | 2                    |
| Flooding Reduction Similarity    | 2                    |
| Flooding Reduction System Random | 15383359451983110645 |
+----------------------------------+----------------------+
</pre>
<!-- OUTPUT-END -->

### show engine statistics

The "<b>show engine statistics</b>" command shows all the statistics for the RIFT-Python
engine.

Example:

<!-- OUTPUT-START: agg_101> show engine statistics -->
<pre>
agg_101> <b>show engine statistics</b>
All Node ZTP FSMs:
+------------------------------------------------------------------------------------------+----------------+------------------------+-------------------+
| Description                                                                              | Value          | Last Rate              | Last Change       |
|                                                                                          |                | Over Last 10 Changes   |                   |
+------------------------------------------------------------------------------------------+----------------+------------------------+-------------------+
| Events CHANGE_LOCAL_CONFIGURED_LEVEL                                                     | 1 Event        |                        | 0d 00h:00m:00.31s |
+------------------------------------------------------------------------------------------+----------------+------------------------+-------------------+
| Events NEIGHBOR_OFFER                                                                    | 48 Events      | 397.05 Events/Sec      | 0d 00h:00m:00.22s |
+------------------------------------------------------------------------------------------+----------------+------------------------+-------------------+
| Events BETTER_HAL                                                                        | 0 Events       |                        |                   |
+------------------------------------------------------------------------------------------+----------------+------------------------+-------------------+
| Events BETTER_HAT                                                                        | 0 Events       |                        |                   |
+------------------------------------------------------------------------------------------+----------------+------------------------+-------------------+
.                                                                                          .                .                        .                   .
.                                                                                          .                .                        .                   .
+------------------------------------------------------------------------------------------+----------------+------------------------+-------------------+
| Event-Transitions UPDATING_CLIENTS -[CHANGE_LOCAL_CONFIGURED_LEVEL]-&gt; COMPUTE_BEST_OFFER | 1 Transition   |                        | 0d 00h:00m:00.31s |
+------------------------------------------------------------------------------------------+----------------+------------------------+-------------------+

All Interfaces Traffic:
+---------------------------+-------------------------+-----------------------------------------+-------------------+
| Description               | Value                   | Last Rate                               | Last Change       |
|                           |                         | Over Last 10 Changes                    |                   |
+---------------------------+-------------------------+-----------------------------------------+-------------------+
| RX IPv4 LIE Packets       | 24 Packets, 4068 Bytes  | 145.50 Packets/Sec, 24993.91 Bytes/Sec  | 0d 00h:00m:00.22s |
+---------------------------+-------------------------+-----------------------------------------+-------------------+
| TX IPv4 LIE Packets       | 28 Packets, 4648 Bytes  | 142.80 Packets/Sec, 24529.95 Bytes/Sec  | 0d 00h:00m:00.23s |
+---------------------------+-------------------------+-----------------------------------------+-------------------+
| RX IPv4 TIE Packets       | 0 Packets, 0 Bytes      |                                         |                   |
+---------------------------+-------------------------+-----------------------------------------+-------------------+
| TX IPv4 TIE Packets       | 0 Packets, 0 Bytes      |                                         |                   |
+---------------------------+-------------------------+-----------------------------------------+-------------------+
.                           .                         .                                         .                   .
.                           .                         .                                         .                   .
+---------------------------+-------------------------+-----------------------------------------+-------------------+
| Total RX Misorders        | 0 Packets               |                                         |                   |
+---------------------------+-------------------------+-----------------------------------------+-------------------+

All Interfaces Security:
+------------------------------------------------+-------------------------+----------------------------------------+-------------------+
| Description                                    | Value                   | Last Rate                              | Last Change       |
|                                                |                         | Over Last 10 Changes                   |                   |
+------------------------------------------------+-------------------------+----------------------------------------+-------------------+
| Missing outer security envelope                | 0 Packets, 0 Bytes      |                                        |                   |
+------------------------------------------------+-------------------------+----------------------------------------+-------------------+
| Zero outer key id not accepted                 | 0 Packets, 0 Bytes      |                                        |                   |
+------------------------------------------------+-------------------------+----------------------------------------+-------------------+
| Non-zero outer key id not accepted             | 0 Packets, 0 Bytes      |                                        |                   |
+------------------------------------------------+-------------------------+----------------------------------------+-------------------+
| Incorrect outer fingerprint                    | 0 Packets, 0 Bytes      |                                        |                   |
+------------------------------------------------+-------------------------+----------------------------------------+-------------------+
.                                                .                         .                                        .                   .
.                                                .                         .                                        .                   .
+------------------------------------------------+-------------------------+----------------------------------------+-------------------+
| Empty origin fingerprint accepted              | 0 Packets, 0 Bytes      |                                        |                   |
+------------------------------------------------+-------------------------+----------------------------------------+-------------------+

All Interface LIE FSMs:
+------------------------------------------------------------+----------------+------------------------+-------------------+
| Description                                                | Value          | Last Rate              | Last Change       |
|                                                            |                | Over Last 10 Changes   |                   |
+------------------------------------------------------------+----------------+------------------------+-------------------+
| Events TIMER_TICK                                          | 28 Events      | 143.00 Events/Sec      | 0d 00h:00m:00.23s |
+------------------------------------------------------------+----------------+------------------------+-------------------+
| Events LEVEL_CHANGED                                       | 0 Events       |                        |                   |
+------------------------------------------------------------+----------------+------------------------+-------------------+
| Events HAL_CHANGED                                         | 0 Events       |                        |                   |
+------------------------------------------------------------+----------------+------------------------+-------------------+
| Events HAT_CHANGED                                         | 0 Events       |                        |                   |
+------------------------------------------------------------+----------------+------------------------+-------------------+
.                                                            .                .                        .                   .
.                                                            .                .                        .                   .
+------------------------------------------------------------+----------------+------------------------+-------------------+
| Event-Transitions TWO_WAY -[TIMER_TICK]-&gt; TWO_WAY          | 0 Transitions  |                        |                   |
+------------------------------------------------------------+----------------+------------------------+-------------------+
</pre>
<!-- OUTPUT-END -->

### show engine statistics exclude-zero

The "<b>show engine statistics</b>" command shows all the statistics for the RIFT-Python
engine, excluding any zero statistics.

Example:

<!-- OUTPUT-START: agg_101> show engine statistics exclude-zero -->
<pre>
agg_101> <b>show engine statistics exclude-zero</b>
All Node ZTP FSMs:
+------------------------------------------------------------------------------------------+----------------+------------------------+-------------------+
| Description                                                                              | Value          | Last Rate              | Last Change       |
|                                                                                          |                | Over Last 10 Changes   |                   |
+------------------------------------------------------------------------------------------+----------------+------------------------+-------------------+
| Events CHANGE_LOCAL_CONFIGURED_LEVEL                                                     | 1 Event        |                        | 0d 00h:00m:00.42s |
+------------------------------------------------------------------------------------------+----------------+------------------------+-------------------+
| Events NEIGHBOR_OFFER                                                                    | 48 Events      | 397.05 Events/Sec      | 0d 00h:00m:00.33s |
+------------------------------------------------------------------------------------------+----------------+------------------------+-------------------+
| Events COMPUTATION_DONE                                                                  | 1 Event        |                        | 0d 00h:00m:00.42s |
+------------------------------------------------------------------------------------------+----------------+------------------------+-------------------+
| Transitions COMPUTE_BEST_OFFER -&gt; UPDATING_CLIENTS                                       | 1 Transition   |                        | 0d 00h:00m:00.42s |
+------------------------------------------------------------------------------------------+----------------+------------------------+-------------------+
.                                                                                          .                .                        .                   .
.                                                                                          .                .                        .                   .
+------------------------------------------------------------------------------------------+----------------+------------------------+-------------------+
| Event-Transitions UPDATING_CLIENTS -[CHANGE_LOCAL_CONFIGURED_LEVEL]-&gt; COMPUTE_BEST_OFFER | 1 Transition   |                        | 0d 00h:00m:00.42s |
+------------------------------------------------------------------------------------------+----------------+------------------------+-------------------+

All Interfaces Traffic:
+---------------------------+-------------------------+-----------------------------------------+-------------------+
| Description               | Value                   | Last Rate                               | Last Change       |
|                           |                         | Over Last 10 Changes                    |                   |
+---------------------------+-------------------------+-----------------------------------------+-------------------+
| RX IPv4 LIE Packets       | 24 Packets, 4068 Bytes  | 145.50 Packets/Sec, 24993.91 Bytes/Sec  | 0d 00h:00m:00.34s |
+---------------------------+-------------------------+-----------------------------------------+-------------------+
| TX IPv4 LIE Packets       | 28 Packets, 4648 Bytes  | 142.80 Packets/Sec, 24529.95 Bytes/Sec  | 0d 00h:00m:00.34s |
+---------------------------+-------------------------+-----------------------------------------+-------------------+
| RX IPv4 TIDE Packets      | 24 Packets, 13768 Bytes | 158.91 Packets/Sec, 66828.48 Bytes/Sec  | 0d 00h:00m:00.32s |
+---------------------------+-------------------------+-----------------------------------------+-------------------+
| TX IPv4 TIDE Packets      | 24 Packets, 13768 Bytes | 147.89 Packets/Sec, 62196.87 Bytes/Sec  | 0d 00h:00m:00.33s |
+---------------------------+-------------------------+-----------------------------------------+-------------------+
.                           .                         .                                         .                   .
.                           .                         .                                         .                   .
+---------------------------+-------------------------+-----------------------------------------+-------------------+
| Total TX Packets          | 80 Packets, 23064 Bytes | 371.94 Packets/Sec, 101167.15 Bytes/Sec | 0d 00h:00m:00.33s |
+---------------------------+-------------------------+-----------------------------------------+-------------------+

All Interfaces Security:
+----------------------------------+-------------------------+----------------------------------------+-------------------+
| Description                      | Value                   | Last Rate                              | Last Change       |
|                                  |                         | Over Last 10 Changes                   |                   |
+----------------------------------+-------------------------+----------------------------------------+-------------------+
| Empty outer fingerprint accepted | 72 Packets, 21904 Bytes | 357.61 Packets/Sec, 97271.20 Bytes/Sec | 0d 00h:00m:00.33s |
+----------------------------------+-------------------------+----------------------------------------+-------------------+

All Interface LIE FSMs:
+---------------------------------------------------------+----------------+------------------------+-------------------+
| Description                                             | Value          | Last Rate              | Last Change       |
|                                                         |                | Over Last 10 Changes   |                   |
+---------------------------------------------------------+----------------+------------------------+-------------------+
| Events TIMER_TICK                                       | 28 Events      | 143.00 Events/Sec      | 0d 00h:00m:00.34s |
+---------------------------------------------------------+----------------+------------------------+-------------------+
| Events LIE_RECEIVED                                     | 48 Events      | 393.77 Events/Sec      | 0d 00h:00m:00.34s |
+---------------------------------------------------------+----------------+------------------------+-------------------+
| Events SEND_LIE                                         | 28 Events      | 142.99 Events/Sec      | 0d 00h:00m:00.34s |
+---------------------------------------------------------+----------------+------------------------+-------------------+
| Transitions ONE_WAY -&gt; ONE_WAY                          | 8 Transitions  | 85.42 Transitions/Sec  | 0d 00h:00m:00.40s |
+---------------------------------------------------------+----------------+------------------------+-------------------+
.                                                         .                .                        .                   .
.                                                         .                .                        .                   .
+---------------------------------------------------------+----------------+------------------------+-------------------+
| Event-Transitions THREE_WAY -[SEND_LIE]-&gt; THREE_WAY     | 24 Transitions | 142.74 Transitions/Sec | 0d 00h:00m:00.34s |
+---------------------------------------------------------+----------------+------------------------+-------------------+
</pre>
<!-- OUTPUT-END -->

### show flooding-reduction

The "<b>show flooding-reduction</b>" command shows information about flooding reduction.
Specifically, it shows which parent routers have been elected as Flood Repeaters (FRs) including
additional information to understand the steps in the algorithm for the election.

Example:

<!-- OUTPUT-START: agg_101> show flooding-reduction -->
<pre>
agg_101> <b>show flooding-reduction</b>
Parents:
+-----------+-----------+-----------------+-------------+------------+----------+
| Interface | Parent    | Parent          | Grandparent | Similarity | Flood    |
| Name      | System ID | Interface       | Count       | Group      | Repeater |
|           |           | Name            |             |            |          |
+-----------+-----------+-----------------+-------------+------------+----------+
| if_101_1  | 1         | core_1:if_1_101 | 0           | 1: 0-0     | False    |
+-----------+-----------+-----------------+-------------+------------+----------+

Grandparents:
+-------------+--------+-------------+-------------+
| Grandparent | Parent | Flood       | Redundantly |
| System ID   | Count  | Repeater    | Covered     |
|             |        | Adjacencies |             |
+-------------+--------+-------------+-------------+

Interfaces:
+-------------+-----------------------+-----------+-----------+-----------+----------------+----------------+
| Interface   | Neighbor              | Neighbor  | Neighbor  | Neighbor  | Neighbor is    | This Node is   |
| Name        | Interface             | System ID | State     | Direction | Flood Repeater | Flood Repeater |
|             | Name                  |           |           |           | for This Node  | for Neighbor   |
+-------------+-----------------------+-----------+-----------+-----------+----------------+----------------+
| if_101_1    | core_1:if_1_101       | 1         | THREE_WAY | North     | False          | Not Applicable |
+-------------+-----------------------+-----------+-----------+-----------+----------------+----------------+
| if_101_1001 | edge_1001:if_1001_101 | 1001      | THREE_WAY | South     | Not Applicable | True           |
+-------------+-----------------------+-----------+-----------+-----------+----------------+----------------+
| if_101_1002 | edge_1002:if_1002_101 | 1002      | THREE_WAY | South     | Not Applicable | True           |
+-------------+-----------------------+-----------+-----------+-----------+----------------+----------------+
| if_101_2    |                       |           | ONE_WAY   |           | Not Applicable | Not Applicable |
+-------------+-----------------------+-----------+-----------+-----------+----------------+----------------+
</pre>
<!-- OUTPUT-END -->

### show forwarding

The "<b>show forwarding</b>" command shows all routes in the Forwarding Information Base (FIB) of 
the current node. It shows both the IPv4 FIB and the IPv6 FIB.

Example:

<!-- OUTPUT-START: agg_101> show forwarding -->
<pre>
agg_101> <b>show forwarding</b>
IPv4 Routes:
+---------------+---------------------------+
| Prefix        | Next-hops                 |
+---------------+---------------------------+
| 0.0.0.0/0     | if_101_1 172.31.15.176    |
+---------------+---------------------------+
| 1.1.1.0/24    | if_101_1001 172.31.15.176 |
+---------------+---------------------------+
| 1.1.2.0/24    | if_101_1001 172.31.15.176 |
+---------------+---------------------------+
| 1.1.3.0/24    | if_101_1001 172.31.15.176 |
+---------------+---------------------------+
.               .                           .
.               .                           .
+---------------+---------------------------+
| 99.99.99.0/24 | if_101_1002 172.31.15.176 |
|               | if_101_1001 172.31.15.176 |
+---------------+---------------------------+

IPv6 Routes:
+--------+----------------------------------+
| Prefix | Next-hops                        |
+--------+----------------------------------+
| ::/0   | if_101_1 fe80::84a:2ff:fe78:2746 |
+--------+----------------------------------+
</pre>
<!-- OUTPUT-END -->

### show forwarding family <i>family</i>

The "<b>show forwarding family</b> <i>family</i>" command shows the routes of a given address family
in the Forwarding Information Base (FIB) of the current node.

The <i>family</i> parameter can be "<b>ipv4</b>" or "<b>ipv6</b>"

Example:

<!-- OUTPUT-START: agg_101> show forwarding family ipv4 -->
<pre>
agg_101> <b>show forwarding family ipv4</b>
IPv4 Routes:
+---------------+---------------------------+
| Prefix        | Next-hops                 |
+---------------+---------------------------+
| 0.0.0.0/0     | if_101_1 172.31.15.176    |
+---------------+---------------------------+
| 1.1.1.0/24    | if_101_1001 172.31.15.176 |
+---------------+---------------------------+
| 1.1.2.0/24    | if_101_1001 172.31.15.176 |
+---------------+---------------------------+
| 1.1.3.0/24    | if_101_1001 172.31.15.176 |
+---------------+---------------------------+
.               .                           .
.               .                           .
+---------------+---------------------------+
| 99.99.99.0/24 | if_101_1002 172.31.15.176 |
|               | if_101_1001 172.31.15.176 |
+---------------+---------------------------+
</pre>
<!-- OUTPUT-END -->

### show forwarding prefix <i>prefix</i>

The "<b>show forwarding prefix</b> <i>prefix</i>" command shows the route for a given prefix in the
Forwarding Information Base (FIB) of the current node.

Parameter <i>prefix</i> must be an IPv4 prefix or an IPv6 prefix

Example:

<!-- OUTPUT-START: agg_101> show forwarding prefix ::/0 -->
<pre>
agg_101> <b>show forwarding prefix ::/0</b>
+--------+----------------------------------+-----------+
| Prefix | Owner                            | Next-hops |
+--------+----------------------------------+-----------+
| ::/0   | if_101_1 fe80::84a:2ff:fe78:2746 |
+--------+----------------------------------+-----------+
</pre>
<!-- OUTPUT-END -->

### show fsm <i>fsm</i>

The "<b>show fsm</b> <i>fsm</i>" command shows the definition of the specified Finite State Machine (FSM).

Parameter <i>fsm</i> specifies the name of the FSM and can be one of the following values:

* <b>lie</b>: Show the Link Information Element (LIE) FSM.
* <b>ztp</b>: Show the Zero Touch Provisioning (ZTP) FSM.

Example:

<!-- OUTPUT-START: agg_101> show fsm lie -->
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
| HAT_CHANGED                   | False   |
+-------------------------------+---------+
.                               .         .
.                               .         .
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
| ONE_WAY    | HAT_CHANGED                 | -         | store_hat               | -           |
+------------+-----------------------------+-----------+-------------------------+-------------+
.            .                             .           .                         .             .
.            .                             .           .                         .             .
+------------+-----------------------------+-----------+-------------------------+-------------+
| THREE_WAY  | SEND_LIE                    | -         | send_lie                | -           |
+------------+-----------------------------+-----------+-------------------------+-------------+

State entry actions:
+-----------+---------------------+-------------------------+
| State     | Entry Actions       | Exit Actions            |
+-----------+---------------------+-------------------------+
| ONE_WAY   | cleanup             | increase_tx_nonce_local |
|           | send_lie            |                         |
+-----------+---------------------+-------------------------+
| THREE_WAY | start_flooding      | increase_tx_nonce_local |
|           | init_partially_conn | stop_flooding           |
|           |                     | clear_partially_conn    |
+-----------+---------------------+-------------------------+
| TWO_WAY   | -                   | increase_tx_nonce_local |
+-----------+---------------------+-------------------------+
</pre>
<!-- OUTPUT-END -->

<!-- OUTPUT-START: agg_101> show fsm ztp -->
<pre>
agg_101> <b>show fsm ztp</b>
States:
+--------------------+
| State              |
+--------------------+
| UPDATING_CLIENTS   |
+--------------------+
| HOLDING_DOWN       |
+--------------------+
| COMPUTE_BEST_OFFER |
+--------------------+

Events:
+-------------------------------+---------+
| Event                         | Verbose |
+-------------------------------+---------+
| CHANGE_LOCAL_CONFIGURED_LEVEL | False   |
+-------------------------------+---------+
| NEIGHBOR_OFFER                | True    |
+-------------------------------+---------+
| BETTER_HAL                    | False   |
+-------------------------------+---------+
| BETTER_HAT                    | False   |
+-------------------------------+---------+
.                               .         .
.                               .         .
+-------------------------------+---------+
| HOLD_DOWN_EXPIRED             | False   |
+-------------------------------+---------+

Transitions:
+--------------------+-------------------------------+--------------------+-------------------------+-------------+
| From state         | Event                         | To state           | Actions                 | Push events |
+--------------------+-------------------------------+--------------------+-------------------------+-------------+
| UPDATING_CLIENTS   | CHANGE_LOCAL_CONFIGURED_LEVEL | COMPUTE_BEST_OFFER | store_level             | -           |
+--------------------+-------------------------------+--------------------+-------------------------+-------------+
| UPDATING_CLIENTS   | NEIGHBOR_OFFER                | -                  | update_or_remove_offer  | -           |
+--------------------+-------------------------------+--------------------+-------------------------+-------------+
| UPDATING_CLIENTS   | BETTER_HAL                    | COMPUTE_BEST_OFFER | -                       | -           |
+--------------------+-------------------------------+--------------------+-------------------------+-------------+
| UPDATING_CLIENTS   | BETTER_HAT                    | COMPUTE_BEST_OFFER | -                       | -           |
+--------------------+-------------------------------+--------------------+-------------------------+-------------+
.                    .                               .                    .                         .             .
.                    .                               .                    .                         .             .
+--------------------+-------------------------------+--------------------+-------------------------+-------------+
| COMPUTE_BEST_OFFER | COMPUTATION_DONE              | UPDATING_CLIENTS   | -                       | -           |
+--------------------+-------------------------------+--------------------+-------------------------+-------------+

State entry actions:
+--------------------+----------------------+--------------+
| State              | Entry Actions        | Exit Actions |
+--------------------+----------------------+--------------+
| COMPUTE_BEST_OFFER | stop_hold_down_timer | -            |
|                    | level_compute        |              |
+--------------------+----------------------+--------------+
| UPDATING_CLIENTS   | update_all_lie_fsms  | -            |
+--------------------+----------------------+--------------+
</pre>
<!-- OUTPUT-END -->

### show interface <i>interface</i>

The "<b>show interface</b> <i>interface</i>" command reports more detailed information about a single interface.
If there is a neighbor on the interface, the command also shows details about that neighbor.

The <i>interface</i> parameter is the name of an interface of the current node. You can get a list of interfaces of the
current node using the <b>show interfaces</b> command.

Example of an interface which does have a neighbor (adjacency in state THREE_WAY):

<!-- OUTPUT-START: agg_101> show interface if_101_1 -->
<pre>
agg_101> <b>show interface if_101_1</b>
Interface:
+--------------------------------------+----------------------------------------------------------+
| Interface Name                       | if_101_1                                                 |
| Physical Interface Name              | ens5                                                     |
| Advertised Name                      | agg_101:if_101_1                                         |
| Interface IPv4 Address               | 172.31.15.176                                            |
| Interface IPv6 Address               | fe80::84a:2ff:fe78:2746%ens5                             |
| Interface Index                      | 2                                                        |
| Metric                               | 1                                                        |
| LIE Receive IPv4 Multicast Address   | 224.0.0.81                                               |
| LIE Receive IPv6 Multicast Address   | FF02::0078                                               |
| LIE Receive Port                     | 20001                                                    |
| LIE Transmit IPv4 Multicast Address  | 224.0.0.71                                               |
| LIE Transmit IPv6 Multicast Address  | FF02::0078                                               |
| LIE Transmit Port                    | 20002                                                    |
| Flooding Receive Port                | 20004                                                    |
| System ID                            | 101                                                      |
| Local ID                             | 1                                                        |
| MTU                                  | 1400                                                     |
| POD                                  | 0                                                        |
| Failure                              | ok                                                       |
| State                                | THREE_WAY                                                |
| Received LIE Accepted or Rejected    | Accepted                                                 |
| Received LIE Accept or Reject Reason | Neither node is leaf and level difference is at most one |
| Neighbor is Flood Repeater           | False                                                    |
| Neighbor is Partially Connected      | N/A                                                      |
| Nodes Causing Partial Connectivity   |                                                          |
+--------------------------------------+----------------------------------------------------------+

Neighbor:
+------------------------+------------------------------+
| Name                   | core_1:if_1_101              |
| System ID              | 1                            |
| IPv4 Address           | 172.31.15.176                |
| IPv6 Address           | fe80::84a:2ff:fe78:2746%ens5 |
| LIE UDP Source Port    | 44309                        |
| Link ID                | 1                            |
| Level                  | 24                           |
| Flood UDP Port         | 20003                        |
| MTU                    | 1400                         |
| POD                    | 0                            |
| Hold Time              | 3                            |
| Not a ZTP Offer        | False                        |
| You are Flood Repeater | False                        |
| Your System ID         | 101                          |
| Your Local ID          | 1                            |
+------------------------+------------------------------+
</pre>
<!-- OUTPUT-END -->

### show interface <i>interface</i> fsm history

The "<b>show interface</b> <i>interface</i> <b>fsm history</b>" command shows the 25 most recent "interesting" 
executed events for the Link Information Element (LIE) Finite State Machine (FSM) associated with the interface. 
The most recent event is at the top.

This command only shows the "interesting" events, i.e. it does not show any events that are marked as "verbose"
by the "<b>show fsm lie</b>" command. 
Use the "<b>show interface</b> <i>interface</i> <b>fsm verbose-history</b>" command if you want to see all events.

Example:

<!-- OUTPUT-START: agg_101> show interface if_101_1001 fsm history -->
<pre>
agg_101> <b>show interface if_101_1001 fsm history</b>
+----------+-----------+---------+---------+---------------------+-------------------------+-----------+----------+
| Sequence | Time      | Verbose | From    | Event               | Actions and             | To        | Implicit |
| Nr       | Delta     | Skipped | State   |                     | Pushed Events           | State     |          |
+----------+-----------+---------+---------+---------------------+-------------------------+-----------+----------+
| 217      | 10.287634 | 2       | TWO_WAY | VALID_REFLECTION    | increase_tx_nonce_local | THREE_WAY | False    |
|          |           |         |         |                     | start_flooding          |           |          |
|          |           |         |         |                     | init_partially_conn     |           |          |
+----------+-----------+---------+---------+---------------------+-------------------------+-----------+----------+
| 214      | 0.001316  | 3       | ONE_WAY | NEW_NEIGHBOR        | SEND_LIE                | TWO_WAY   | False    |
|          |           |         |         |                     | increase_tx_nonce_local |           |          |
+----------+-----------+---------+---------+---------------------+-------------------------+-----------+----------+
| 68       | 0.862582  | 1       | ONE_WAY | UNACCEPTABLE_HEADER |                         | ONE_WAY   | False    |
+----------+-----------+---------+---------+---------------------+-------------------------+-----------+----------+
| 66       | 0.000375  | 1       | ONE_WAY | UNACCEPTABLE_HEADER |                         | ONE_WAY   | False    |
+----------+-----------+---------+---------+---------------------+-------------------------+-----------+----------+
| 9        | 0.172668  | 0       | None    | None                | cleanup                 | ONE_WAY   | False    |
|          |           |         |         |                     | send_lie                |           |          |
+----------+-----------+---------+---------+---------------------+-------------------------+-----------+----------+
</pre>
<!-- OUTPUT-END -->

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

<!-- OUTPUT-START: agg_101> show interface if_101_1001 fsm verbose-history -->
<pre>
agg_101> <b>show interface if_101_1001 fsm verbose-history</b>
+----------+----------+---------+-----------+--------------+-------------------------+-------+----------+
| Sequence | Time     | Verbose | From      | Event        | Actions and             | To    | Implicit |
| Nr       | Delta    | Skipped | State     |              | Pushed Events           | State |          |
+----------+----------+---------+-----------+--------------+-------------------------+-------+----------+
| 1958     | 0.333019 | 0       | THREE_WAY | LIE_RECEIVED | process_lie             | None  | False    |
+----------+----------+---------+-----------+--------------+-------------------------+-------+----------+
| 1957     | 0.000147 | 0       | THREE_WAY | LIE_RECEIVED | process_lie             | None  | False    |
+----------+----------+---------+-----------+--------------+-------------------------+-------+----------+
| 1884     | 0.094534 | 0       | THREE_WAY | SEND_LIE     | send_lie                | None  | False    |
+----------+----------+---------+-----------+--------------+-------------------------+-------+----------+
| 1883     | 0.000093 | 0       | THREE_WAY | TIMER_TICK   | check_hold_time_expired | None  | False    |
|          |          |         |           |              | SEND_LIE                |       |          |
+----------+----------+---------+-----------+--------------+-------------------------+-------+----------+
.          .          .         .           .              .                         .       .          .
.          .          .         .           .              .                         .       .          .
+----------+----------+---------+-----------+--------------+-------------------------+-------+----------+
| 1044     | 0.910886 | 0       | THREE_WAY | LIE_RECEIVED | process_lie             | None  | False    |
+----------+----------+---------+-----------+--------------+-------------------------+-------+----------+
</pre>
<!-- OUTPUT-END -->

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

<!-- OUTPUT-START: agg_101> show interface if_101_1 queues -->
<pre>
agg_101> <b>show interface if_101_1 queues</b>
Transmit queue:
+-----------+------------+------+--------+--------+-------+
| Direction | Originator | Type | TIE Nr | Seq Nr | Send  |
|           |            |      |        |        | Delay |
+-----------+------------+------+--------+--------+-------+

Request queue:
+-----------+------------+------+--------+--------+-----------+-------+
| Direction | Originator | Type | TIE Nr | Seq Nr | Remaining | Send  |
|           |            |      |        |        | Lifetime  | Delay |
+-----------+------------+------+--------+--------+-----------+-------+

Acknowledge queue:
+-----------+------------+------+--------+--------+-----------+-------+
| Direction | Originator | Type | TIE Nr | Seq Nr | Remaining | Send  |
|           |            |      |        |        | Lifetime  | Delay |
+-----------+------------+------+--------+--------+-----------+-------+
</pre>
<!-- OUTPUT-END -->

### show interface <i>interface</i> security

The "<b>show interface</b> <i>interface</i> <b>security</b>" command shows the security parameters
(e.g. configured key identifiers) and security statistics for the given interface.

Example:

<!-- OUTPUT-START: agg_101> show interface if_101_1 security -->
<pre>
agg_101> <b>show interface if_101_1 security</b>
Outer Keys:
+-------------------+-----------+----------------------+
| Key               | Key ID(s) | Configuration Source |
+-------------------+-----------+----------------------+
| Active Outer Key  | None      | Node Active Key      |
+-------------------+-----------+----------------------+
| Accept Outer Keys |           | Node Accept Keys     |
+-------------------+-----------+----------------------+

Nonces:
+--------------------------+----------------+
| Last Received LIE Nonce  | 44601          |
+--------------------------+----------------+
| Last Sent Nonce          | 48367          |
+--------------------------+----------------+
| Next Sent Nonce Increase | 48.353941 secs |
+--------------------------+----------------+

Security Statistics:
+------------------------------------------------+-------------------------+--------------------------------------+-------------------+
| Description                                    | Value                   | Last Rate                            | Last Change       |
|                                                |                         | Over Last 10 Changes                 |                   |
+------------------------------------------------+-------------------------+--------------------------------------+-------------------+
| Missing outer security envelope                | 0 Packets, 0 Bytes      |                                      |                   |
+------------------------------------------------+-------------------------+--------------------------------------+-------------------+
| Zero outer key id not accepted                 | 0 Packets, 0 Bytes      |                                      |                   |
+------------------------------------------------+-------------------------+--------------------------------------+-------------------+
| Non-zero outer key id not accepted             | 0 Packets, 0 Bytes      |                                      |                   |
+------------------------------------------------+-------------------------+--------------------------------------+-------------------+
| Incorrect outer fingerprint                    | 0 Packets, 0 Bytes      |                                      |                   |
+------------------------------------------------+-------------------------+--------------------------------------+-------------------+
.                                                .                         .                                      .                   .
.                                                .                         .                                      .                   .
+------------------------------------------------+-------------------------+--------------------------------------+-------------------+
| Empty origin fingerprint accepted              | 3 Packets, 794 Bytes    | 14.96 Packets/Sec, 4083.22 Bytes/Sec | 0d 00h:00m:10.23s |
+------------------------------------------------+-------------------------+--------------------------------------+-------------------+
</pre>
<!-- OUTPUT-END -->

### show interface <i>interface</i> sockets

The "<b>show interface</b> <i>interface</i> <b>sockets</b>" command shows the sockets that the 
current node has opened for sending and receiving packets.

Example:

<!-- OUTPUT-START: agg_101> show interface if_101_1 sockets -->
<pre>
agg_101> <b>show interface if_101_1 sockets</b>
+----------+-----------+--------+------------------------------+------------+----------------+-------------+
| Traffic  | Direction | Family | Local Address                | Local Port | Remote Address | Remote Port |
+----------+-----------+--------+------------------------------+------------+----------------+-------------+
| LIEs     | Receive   | IPv4   | 224.0.0.81                   | 20001      | Any            | Any         |
+----------+-----------+--------+------------------------------+------------+----------------+-------------+
| LIEs     | Receive   | IPv6   | ff02::78%ens5                | 20001      | Any            | Any         |
+----------+-----------+--------+------------------------------+------------+----------------+-------------+
| LIEs     | Send      | IPv4   | 172.31.15.176                | 42050      | 224.0.0.71     | 20002       |
+----------+-----------+--------+------------------------------+------------+----------------+-------------+
| LIEs     | Send      | IPv6   | fe80::84a:2ff:fe78:2746%ens5 | 51707      | ff02::78%ens5  | 20002       |
+----------+-----------+--------+------------------------------+------------+----------------+-------------+
.          .           .        .                              .            .                .             .
.          .           .        .                              .            .                .             .
+----------+-----------+--------+------------------------------+------------+----------------+-------------+
| Flooding | Send      | IPv4   | 172.31.15.176                | 35165      | 172.31.15.176  | 20003       |
+----------+-----------+--------+------------------------------+------------+----------------+-------------+
</pre>
<!-- OUTPUT-END -->

### show interface <i>interface</i> statistics

The "<b>show interface <i>interface</i> statistics</b>" command shows all the statistics for the 
speficied interface.

Example:

<!-- OUTPUT-START: agg_101> show interface if_101_1 statistics -->
<pre>
agg_101> <b>show interface if_101_1 statistics</b>
Traffic:
+---------------------------+-----------------------+-------------------------------------+-------------------+
| Description               | Value                 | Last Rate                           | Last Change       |
|                           |                       | Over Last 10 Changes                |                   |
+---------------------------+-----------------------+-------------------------------------+-------------------+
| RX IPv4 LIE Packets       | 2 Packets, 332 Bytes  | 1.00 Packets/Sec, 166.00 Bytes/Sec  | 0d 00h:00m:00.89s |
+---------------------------+-----------------------+-------------------------------------+-------------------+
| TX IPv4 LIE Packets       | 2 Packets, 334 Bytes  | 1.01 Packets/Sec, 168.37 Bytes/Sec  | 0d 00h:00m:00.86s |
+---------------------------+-----------------------+-------------------------------------+-------------------+
| RX IPv4 TIE Packets       | 0 Packets, 0 Bytes    |                                     |                   |
+---------------------------+-----------------------+-------------------------------------+-------------------+
| TX IPv4 TIE Packets       | 0 Packets, 0 Bytes    |                                     |                   |
+---------------------------+-----------------------+-------------------------------------+-------------------+
.                           .                       .                                     .                   .
.                           .                       .                                     .                   .
+---------------------------+-----------------------+-------------------------------------+-------------------+
| Total RX Misorders        | 0 Packets             |                                     |                   |
+---------------------------+-----------------------+-------------------------------------+-------------------+

Security:
+------------------------------------------------+-------------------------+--------------------------------------+-------------------+
| Description                                    | Value                   | Last Rate                            | Last Change       |
|                                                |                         | Over Last 10 Changes                 |                   |
+------------------------------------------------+-------------------------+--------------------------------------+-------------------+
| Missing outer security envelope                | 0 Packets, 0 Bytes      |                                      |                   |
+------------------------------------------------+-------------------------+--------------------------------------+-------------------+
| Zero outer key id not accepted                 | 0 Packets, 0 Bytes      |                                      |                   |
+------------------------------------------------+-------------------------+--------------------------------------+-------------------+
| Non-zero outer key id not accepted             | 0 Packets, 0 Bytes      |                                      |                   |
+------------------------------------------------+-------------------------+--------------------------------------+-------------------+
| Incorrect outer fingerprint                    | 0 Packets, 0 Bytes      |                                      |                   |
+------------------------------------------------+-------------------------+--------------------------------------+-------------------+
.                                                .                         .                                      .                   .
.                                                .                         .                                      .                   .
+------------------------------------------------+-------------------------+--------------------------------------+-------------------+
| Empty origin fingerprint accepted              | 3 Packets, 794 Bytes    | 14.96 Packets/Sec, 4083.22 Bytes/Sec | 0d 00h:00m:10.44s |
+------------------------------------------------+-------------------------+--------------------------------------+-------------------+

LIE FSM:
+------------------------------------------------------------+---------------+----------------------+-------------------+
| Description                                                | Value         | Last Rate            | Last Change       |
|                                                            |               | Over Last 10 Changes |                   |
+------------------------------------------------------------+---------------+----------------------+-------------------+
| Event-Transitions None -[None]-&gt; ONE_WAY                   | 0 Transitions |                      |                   |
+------------------------------------------------------------+---------------+----------------------+-------------------+
| Event-Transitions ONE_WAY -[LIE_RECEIVED]-&gt; ONE_WAY        | 0 Transitions |                      |                   |
+------------------------------------------------------------+---------------+----------------------+-------------------+
| Event-Transitions ONE_WAY -[NEW_NEIGHBOR]-&gt; TWO_WAY        | 0 Transitions |                      |                   |
+------------------------------------------------------------+---------------+----------------------+-------------------+
| Event-Transitions ONE_WAY -[SEND_LIE]-&gt; ONE_WAY            | 0 Transitions |                      |                   |
+------------------------------------------------------------+---------------+----------------------+-------------------+
.                                                            .               .                      .                   .
.                                                            .               .                      .                   .
+------------------------------------------------------------+---------------+----------------------+-------------------+
| Transitions TWO_WAY -&gt; TWO_WAY                             | 0 Transitions |                      |                   |
+------------------------------------------------------------+---------------+----------------------+-------------------+
</pre>
<!-- OUTPUT-END -->

### show interface <i>interface</i> statistics exclude-zero

The "<b>show interface <i>interface</i> statistics</b>" command shows all the statistics for the 
specified interface, excluding any zero statistics.

Example:

<!-- OUTPUT-START: agg_101> show interface if_101_1 statistics exclude-zero -->
<pre>
agg_101> <b>show interface if_101_1 statistics exclude-zero</b>
Traffic:
+---------------------------+-----------------------+-------------------------------------+-------------------+
| Description               | Value                 | Last Rate                           | Last Change       |
|                           |                       | Over Last 10 Changes                |                   |
+---------------------------+-----------------------+-------------------------------------+-------------------+
| RX IPv4 LIE Packets       | 3 Packets, 498 Bytes  | 1.00 Packets/Sec, 165.97 Bytes/Sec  | 0d 00h:00m:00.00s |
+---------------------------+-----------------------+-------------------------------------+-------------------+
| TX IPv4 LIE Packets       | 2 Packets, 334 Bytes  | 1.01 Packets/Sec, 168.37 Bytes/Sec  | 0d 00h:00m:00.97s |
+---------------------------+-----------------------+-------------------------------------+-------------------+
| RX IPv4 TIDE Packets      | 1 Packet, 927 Bytes   |                                     | 0d 00h:00m:01.97s |
+---------------------------+-----------------------+-------------------------------------+-------------------+
| TX IPv4 TIDE Packets      | 1 Packet, 503 Bytes   |                                     | 0d 00h:00m:01.95s |
+---------------------------+-----------------------+-------------------------------------+-------------------+
.                           .                       .                                     .                   .
.                           .                       .                                     .                   .
+---------------------------+-----------------------+-------------------------------------+-------------------+
| Total TX Packets          | 5 Packets, 1171 Bytes | 4.03 Packets/Sec, 1012.17 Bytes/Sec | 0d 00h:00m:00.97s |
+---------------------------+-----------------------+-------------------------------------+-------------------+

Security:
+-----------------------------------+-------------------------+--------------------------------------+-------------------+
| Description                       | Value                   | Last Rate                            | Last Change       |
|                                   |                         | Over Last 10 Changes                 |                   |
+-----------------------------------+-------------------------+--------------------------------------+-------------------+
| Empty outer fingerprint accepted  | 57 Packets, 11047 Bytes | 2.27 Packets/Sec, 568.35 Bytes/Sec   | 0d 00h:00m:00.00s |
+-----------------------------------+-------------------------+--------------------------------------+-------------------+
| Empty origin fingerprint accepted | 3 Packets, 794 Bytes    | 14.96 Packets/Sec, 4083.22 Bytes/Sec | 0d 00h:00m:10.55s |
+-----------------------------------+-------------------------+--------------------------------------+-------------------+

LIE FSM:
+---------------------------------------------------------+----------------+----------------------+-------------------+
| Description                                             | Value          | Last Rate            | Last Change       |
|                                                         |                | Over Last 10 Changes |                   |
+---------------------------------------------------------+----------------+----------------------+-------------------+
| Event-Transitions THREE_WAY -[LIE_RECEIVED]-&gt; THREE_WAY | 6 Transitions  | 2.50 Transitions/Sec | 0d 00h:00m:00.00s |
+---------------------------------------------------------+----------------+----------------------+-------------------+
| Event-Transitions THREE_WAY -[SEND_LIE]-&gt; THREE_WAY     | 2 Transitions  | 1.01 Transitions/Sec | 0d 00h:00m:00.97s |
+---------------------------------------------------------+----------------+----------------------+-------------------+
| Event-Transitions THREE_WAY -[TIMER_TICK]-&gt; THREE_WAY   | 2 Transitions  | 1.01 Transitions/Sec | 0d 00h:00m:00.97s |
+---------------------------------------------------------+----------------+----------------------+-------------------+
| Events LIE_RECEIVED                                     | 6 Events       | 2.50 Events/Sec      | 0d 00h:00m:00.00s |
+---------------------------------------------------------+----------------+----------------------+-------------------+
.                                                         .                .                      .                   .
.                                                         .                .                      .                   .
+---------------------------------------------------------+----------------+----------------------+-------------------+
| Transitions THREE_WAY -&gt; THREE_WAY                      | 10 Transitions | 4.50 Transitions/Sec | 0d 00h:00m:00.00s |
+---------------------------------------------------------+----------------+----------------------+-------------------+
</pre>
<!-- OUTPUT-END -->

### show interface <i>interface</i> tides

The "<b>show interface</b> <i>interface</i> <b>tides</b>" command shows the TIDE packets that the node is
currently periodically sending on the specified interface.

Example:

<!-- OUTPUT-START: agg_101> show interface if_101_1 tides -->
<pre>
agg_101> <b>show interface if_101_1 tides</b>
Send TIDEs:
+----------------+-------------------------------------------------+-----------+------------+--------+--------+--------+-----------+-------------+
| Start          | End                                             | Direction | Originator | Type   | TIE Nr | Seq Nr | Remaining | Origination |
| Range          | Range                                           |           |            |        |        |        | Lifetime  | Time        |
+----------------+-------------------------------------------------+-----------+------------+--------+--------+--------+-----------+-------------+
| South:0:Node:0 | North:18446744073709551615:Key-Value:4294967295 | South     | 1          | Node   | 1      | 5      | 604789    | -           |
|                |                                                 | South     | 1          | Prefix | 2      | 1      | 604789    | -           |
|                |                                                 | North     | 101        | Node   | 1      | 4      | 604789    | -           |
|                |                                                 | North     | 1001       | Node   | 1      | 3      | 604789    | -           |
|                |                                                 | North     | 1001       | Prefix | 2      | 1      | 604788    | -           |
|                |                                                 | North     | 1002       | Node   | 1      | 3      | 604789    | -           |
|                |                                                 | North     | 1002       | Prefix | 2      | 1      | 604788    | -           |
+----------------+-------------------------------------------------+-----------+------------+--------+--------+--------+-----------+-------------+
</pre>
<!-- OUTPUT-END -->


### show interfaces

The "<b>show interfaces</b>" command reports a summary of all RIFT interfaces (i.e. interfaces on which RIFT is running)
on the currently active RIFT node. 

Use the "<b>show interface</b> <i>interface</i>" to see all details about any particular interface.

<!-- OUTPUT-START: agg_101> show interfaces -->
<pre>
agg_101> <b>show interfaces</b>
+-------------+-----------------------+-----------+-----------+
| Interface   | Neighbor              | Neighbor  | Neighbor  |
| Name        | Name                  | System ID | State     |
+-------------+-----------------------+-----------+-----------+
| if_101_1    | core_1:if_1_101       | 1         | THREE_WAY |
+-------------+-----------------------+-----------+-----------+
| if_101_1001 | edge_1001:if_1001_101 | 1001      | THREE_WAY |
+-------------+-----------------------+-----------+-----------+
| if_101_1002 | edge_1002:if_1002_101 | 1002      | THREE_WAY |
+-------------+-----------------------+-----------+-----------+
| if_101_2    |                       |           | ONE_WAY   |
+-------------+-----------------------+-----------+-----------+
</pre>
<!-- OUTPUT-END -->

### show kernel addresses

The "<b>show kernel addresses</b>" command reports a summary of all addresses in the Linux kernel
on which the RIFT engine is running.

<!-- OUTPUT-START: agg_101> show kernel addresses -->
<pre>
agg_101> <b>show kernel addresses</b>
Kernel Addresses:
+-----------+-------------------------+---------------+---------------+---------+
| Interface | Address                 | Local         | Broadcast     | Anycast |
| Name      |                         |               |               |         |
+-----------+-------------------------+---------------+---------------+---------+
| lo        | 127.0.0.1               | 127.0.0.1     |               |         |
+-----------+-------------------------+---------------+---------------+---------+
| ens5      | 172.31.15.176           | 172.31.15.176 | 172.31.15.255 |         |
+-----------+-------------------------+---------------+---------------+---------+
|           | ::1                     |               |               |         |
+-----------+-------------------------+---------------+---------------+---------+
|           | fe80::84a:2ff:fe78:2746 |               |               |         |
+-----------+-------------------------+---------------+---------------+---------+
</pre>
<!-- OUTPUT-END -->

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

<!-- OUTPUT-START: agg_101> show kernel links -->
<pre>
agg_101> <b>show kernel links</b>
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
| ens5      | 2         | 0a:4a:02:78:27:46 | ff:ff:ff:ff:ff:ff |           | 9001  | UP        |
|           |           |                   |                   |           |       | BROADCAST |
|           |           |                   |                   |           |       | RUNNING   |
|           |           |                   |                   |           |       | MULTICAST |
|           |           |                   |                   |           |       | LOWER_UP  |
+-----------+-----------+-------------------+-------------------+-----------+-------+-----------+
</pre>
<!-- OUTPUT-END -->

If this command is executed on a platform that does not support the Netlink interface to the
kernel routing table (i.e. any non-Linux platform including BSD and macOS) the following error
message is reported:

<pre>
agg_101> <b>show kernel links</b>
Kernel networking not supported on this platform
</pre>

### show kernel routes table <i>table</i> prefix <i>prefix</i>

The "<b>show kernel routes table</b> <i>table</i> <b>prefix</b> <i>prefix</i>" command reports the
details of a single route in the route table in the Linux kernel on which the RIFT engine is running.

Parameter <i>table</i> must be <b>local</b>, <b>main</b>, <b>default</b>, <b>unspecified</b>, or
a number in the range 0-255.

Parameter <i>prefix</i> must be an IPv4 prefix or an IPv6 prefix

<!-- OUTPUT-START: agg_101> show kernel routes table main prefix 99.99.1.0/24 -->
<pre>
agg_101> <b>show kernel routes table main prefix 99.99.1.0/24</b>
Prefix "99.99.1.0/24" in table "Main" not present in kernel route table
</pre>
<!-- OUTPUT-END -->

If this command is executed on a platform that does not support the Netlink interface to the
kernel routing table (i.e. any non-Linux platform including BSD and macOS) the following error
message is reported:

<pre>
agg_101> <b>show kernel routes table main prefix 0.0.0.0/0</b>
Kernel networking not supported on this platform
</pre>

### show kernel routes

The "<b>show kernel routes</b>" command reports a summary of
all routes in the Linux kernel on which the RIFT engine is running.

<!-- OUTPUT-START: agg_101> show kernel routes -->
<pre>
agg_101> <b>show kernel routes</b>
Kernel Routes:
+-------------+---------+-----------------------------+-------------+----------+-----------+------------+--------+
| Table       | Address | Destination                 | Type        | Protocol | Outgoing  | Gateway    | Weight |
|             | Family  |                             |             |          | Interface |            |        |
+-------------+---------+-----------------------------+-------------+----------+-----------+------------+--------+
| Unspecified | IPv6    | ::/0                        | Unreachable | Kernel   | lo        |            |        |
+-------------+---------+-----------------------------+-------------+----------+-----------+------------+--------+
| Unspecified | IPv6    | ::/0                        | Unreachable | Kernel   | lo        |            |        |
+-------------+---------+-----------------------------+-------------+----------+-----------+------------+--------+
| Main        | IPv4    | 0.0.0.0/0                   | Unicast     | Boot     | ens5      | 172.31.0.1 |        |
+-------------+---------+-----------------------------+-------------+----------+-----------+------------+--------+
| Main        | IPv4    | 172.31.0.0/20               | Unicast     | Kernel   | ens5      |            |        |
+-------------+---------+-----------------------------+-------------+----------+-----------+------------+--------+
.             .         .                             .             .          .           .            .        .
.             .         .                             .             .          .           .            .        .
+-------------+---------+-----------------------------+-------------+----------+-----------+------------+--------+
| Local       | IPv6    | ff00::/8                    | Unicast     | Boot     | ens5      |            |        |
+-------------+---------+-----------------------------+-------------+----------+-----------+------------+--------+
</pre>
<!-- OUTPUT-END -->

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

<!-- OUTPUT-START: agg_101> show kernel routes table main -->
<pre>
agg_101> <b>show kernel routes table main</b>
Kernel Routes:
+-------+---------+---------------+---------+----------+-----------+------------+--------+
| Table | Address | Destination   | Type    | Protocol | Outgoing  | Gateway    | Weight |
|       | Family  |               |         |          | Interface |            |        |
+-------+---------+---------------+---------+----------+-----------+------------+--------+
| Main  | IPv4    | 0.0.0.0/0     | Unicast | Boot     | ens5      | 172.31.0.1 |        |
+-------+---------+---------------+---------+----------+-----------+------------+--------+
| Main  | IPv4    | 172.31.0.0/20 | Unicast | Kernel   | ens5      |            |        |
+-------+---------+---------------+---------+----------+-----------+------------+--------+
| Main  | IPv6    | fe80::/64     | Unicast | Kernel   | ens5      |            |        |
+-------+---------+---------------+---------+----------+-----------+------------+--------+
</pre>
<!-- OUTPUT-END -->

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

<!-- OUTPUT-START: agg_101> show node -->
<pre>
agg_101> <b>show node</b>
Node:
+---------------------------------------+------------------+
| Name                                  | agg_101          |
| Passive                               | False            |
| Running                               | True             |
| System ID                             | 101              |
| Configured Level                      | undefined        |
| Leaf Only                             | False            |
| Leaf 2 Leaf                           | False            |
| Top of Fabric Flag                    | False            |
| Zero Touch Provisioning (ZTP) Enabled | True             |
| ZTP FSM State                         | UPDATING_CLIENTS |
| ZTP Hold Down Timer                   | Stopped          |
| ZTP Hold Down Timer                   | Stopped          |
| Highest Available Level (HAL)         | 24               |
| Highest Adjacency Three-way (HAT)     | 24               |
| Level Value                           | 23               |
| Receive LIE IPv4 Multicast Address    | 224.0.0.81       |
| Transmit LIE IPv4 Multicast Address   | 224.0.0.120      |
| Receive LIE IPv6 Multicast Address    | FF02::0078       |
| Transmit LIE IPv6 Multicast Address   | FF02::0078       |
| Receive LIE Port                      | 20102            |
| Transmit LIE Port                     | 10000            |
| LIE Send Interval                     | 1.0 secs         |
| Receive TIE Port                      | 10001            |
| Kernel Route Table                    | 3                |
| Originating South-bound Default Route | True             |
| Flooding Reduction Enabled            | True             |
| Flooding Reduction Redundancy         | 2                |
| Flooding Reduction Similarity         | 2                |
| Flooding Reduction Node Random        | 58548            |
+---------------------------------------+------------------+

Received Offers:
+-------------+-----------+-------+-----------------+-----------+-------+------------+---------+----------------+
| Interface   | System ID | Level | Not A ZTP Offer | State     | Best  | Best 3-Way | Removed | Removed Reason |
+-------------+-----------+-------+-----------------+-----------+-------+------------+---------+----------------+
| if_101_1    | 1         | 24    | False           | THREE_WAY | True  | True       | False   |                |
+-------------+-----------+-------+-----------------+-----------+-------+------------+---------+----------------+
| if_101_1001 | 1001      | 0     | False           | THREE_WAY | False | False      | True    | Level is leaf  |
+-------------+-----------+-------+-----------------+-----------+-------+------------+---------+----------------+
| if_101_1002 | 1002      | 0     | False           | THREE_WAY | False | False      | True    | Level is leaf  |
+-------------+-----------+-------+-----------------+-----------+-------+------------+---------+----------------+

Sent Offers:
+-------------+-----------+-------+-----------------+-----------+
| Interface   | System ID | Level | Not A ZTP Offer | State     |
+-------------+-----------+-------+-----------------+-----------+
| if_101_1    | 101       | 23    | True            | THREE_WAY |
+-------------+-----------+-------+-----------------+-----------+
| if_101_1001 | 101       | 23    | False           | THREE_WAY |
+-------------+-----------+-------+-----------------+-----------+
| if_101_1002 | 101       | 23    | False           | THREE_WAY |
+-------------+-----------+-------+-----------------+-----------+
| if_101_2    | 101       | 23    | False           | ONE_WAY   |
+-------------+-----------+-------+-----------------+-----------+
</pre>
<!-- OUTPUT-END -->

### show node fsm history

The "<b>show node fsm history</b>" command shows the 25 most recent "interesting" 
executed events for the Zero Touch Provisioning (ZTP) Finite State Machine (FSM) associated with the currently
active node. The most recent event is at the top.

This command only shows the "interesting" events, i.e. it does not show any events that are marked as "verbose"
by the "<b>show fsm ztp</b>" command. 
Use the "<b>show node fsm verbose-history</b>" command if you want to see all events.

Example:

<!-- OUTPUT-START: agg_101> show node fsm history -->
<pre>
agg_101> <b>show node fsm history</b>
+----------+----------+---------+--------------------+-------------------------------+----------------------+--------------------+----------+
| Sequence | Time     | Verbose | From               | Event                         | Actions and          | To                 | Implicit |
| Nr       | Delta    | Skipped | State              |                               | Pushed Events        | State              |          |
+----------+----------+---------+--------------------+-------------------------------+----------------------+--------------------+----------+
| 1768     | 2.874761 | 0       | COMPUTE_BEST_OFFER | COMPUTATION_DONE              | update_all_lie_fsms  | UPDATING_CLIENTS   | False    |
+----------+----------+---------+--------------------+-------------------------------+----------------------+--------------------+----------+
| 1767     | 0.000358 | 49      | UPDATING_CLIENTS   | CHANGE_LOCAL_CONFIGURED_LEVEL | store_level          | COMPUTE_BEST_OFFER | False    |
|          |          |         |                    |                               | stop_hold_down_timer |                    |          |
|          |          |         |                    |                               | level_compute        |                    |          |
|          |          |         |                    |                               | COMPUTATION_DONE     |                    |          |
+----------+----------+---------+--------------------+-------------------------------+----------------------+--------------------+----------+
| 479      | 8.101029 | 0       | COMPUTE_BEST_OFFER | COMPUTATION_DONE              | update_all_lie_fsms  | UPDATING_CLIENTS   | False    |
+----------+----------+---------+--------------------+-------------------------------+----------------------+--------------------+----------+
| 478      | 0.000278 | 12      | UPDATING_CLIENTS   | BETTER_HAT                    | stop_hold_down_timer | COMPUTE_BEST_OFFER | False    |
|          |          |         |                    |                               | level_compute        |                    |          |
|          |          |         |                    |                               | COMPUTATION_DONE     |                    |          |
+----------+----------+---------+--------------------+-------------------------------+----------------------+--------------------+----------+
.          .          .         .                    .                               .                      .                    .          .
.          .          .         .                    .                               .                      .                    .          .
+----------+----------+---------+--------------------+-------------------------------+----------------------+--------------------+----------+
| 11       | 0.146269 | 0       | None               | None                          | stop_hold_down_timer | COMPUTE_BEST_OFFER | False    |
|          |          |         |                    |                               | level_compute        |                    |          |
|          |          |         |                    |                               | COMPUTATION_DONE     |                    |          |
+----------+----------+---------+--------------------+-------------------------------+----------------------+--------------------+----------+
</pre>
<!-- OUTPUT-END -->

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

<!-- OUTPUT-START: agg_101> show node fsm verbose-history -->
<pre>
agg_101> <b>show node fsm verbose-history</b>
+----------+----------+---------+--------------------+-------------------------------+------------------------+--------------------+----------+
| Sequence | Time     | Verbose | From               | Event                         | Actions and            | To                 | Implicit |
| Nr       | Delta    | Skipped | State              |                               | Pushed Events          | State              |          |
+----------+----------+---------+--------------------+-------------------------------+------------------------+--------------------+----------+
| 2160     | 0.080684 | 0       | UPDATING_CLIENTS   | NEIGHBOR_OFFER                | update_or_remove_offer | None               | False    |
+----------+----------+---------+--------------------+-------------------------------+------------------------+--------------------+----------+
| 2159     | 0.000083 | 0       | UPDATING_CLIENTS   | NEIGHBOR_OFFER                | update_or_remove_offer | None               | False    |
+----------+----------+---------+--------------------+-------------------------------+------------------------+--------------------+----------+
| 2128     | 0.832035 | 0       | UPDATING_CLIENTS   | NEIGHBOR_OFFER                | update_or_remove_offer | None               | False    |
+----------+----------+---------+--------------------+-------------------------------+------------------------+--------------------+----------+
| 2127     | 0.000087 | 0       | UPDATING_CLIENTS   | NEIGHBOR_OFFER                | update_or_remove_offer | None               | False    |
+----------+----------+---------+--------------------+-------------------------------+------------------------+--------------------+----------+
.          .          .         .                    .                               .                        .                    .          .
.          .          .         .                    .                               .                        .                    .          .
+----------+----------+---------+--------------------+-------------------------------+------------------------+--------------------+----------+
| 1654     | 0.015543 | 0       | UPDATING_CLIENTS   | NEIGHBOR_OFFER                | update_or_remove_offer | None               | False    |
+----------+----------+---------+--------------------+-------------------------------+------------------------+--------------------+----------+
</pre>
<!-- OUTPUT-END -->

### show node statistics

The "<b>show node statistics</b>" command shows all the statistics for the current node.

Example:

<!-- OUTPUT-START: agg_101> show node statistics -->
<pre>
agg_101> <b>show node statistics</b>
Node ZTP FSM:
+------------------------------------------------------------------------------------------+----------------+----------------------+-------------------+
| Description                                                                              | Value          | Last Rate            | Last Change       |
|                                                                                          |                | Over Last 10 Changes |                   |
+------------------------------------------------------------------------------------------+----------------+----------------------+-------------------+
| Event-Transitions COMPUTE_BEST_OFFER -[COMPUTATION_DONE]-&gt; UPDATING_CLIENTS              | 1 Transition   |                      | 0d 00h:00m:03.09s |
+------------------------------------------------------------------------------------------+----------------+----------------------+-------------------+
| Event-Transitions None -[None]-&gt; COMPUTE_BEST_OFFER                                      | 0 Transitions  |                      |                   |
+------------------------------------------------------------------------------------------+----------------+----------------------+-------------------+
| Event-Transitions UPDATING_CLIENTS -[BETTER_HAL]-&gt; COMPUTE_BEST_OFFER                    | 0 Transitions  |                      |                   |
+------------------------------------------------------------------------------------------+----------------+----------------------+-------------------+
| Event-Transitions UPDATING_CLIENTS -[BETTER_HAT]-&gt; COMPUTE_BEST_OFFER                    | 0 Transitions  |                      |                   |
+------------------------------------------------------------------------------------------+----------------+----------------------+-------------------+
.                                                                                          .                .                      .                   .
.                                                                                          .                .                      .                   .
+------------------------------------------------------------------------------------------+----------------+----------------------+-------------------+
| Transitions UPDATING_CLIENTS -&gt; UPDATING_CLIENTS                                         | 24 Transitions | 9.08 Transitions/Sec | 0d 00h:00m:00.04s |
+------------------------------------------------------------------------------------------+----------------+----------------------+-------------------+

Node Interfaces Traffic:
+---------------------------+------------------------+-------------------------------------+-------------------+
| Description               | Value                  | Last Rate                           | Last Change       |
|                           |                        | Over Last 10 Changes                |                   |
+---------------------------+------------------------+-------------------------------------+-------------------+
| RX IPv4 LIE Packets       | 12 Packets, 2040 Bytes | 3.01 Packets/Sec, 511.61 Bytes/Sec  | 0d 00h:00m:00.04s |
+---------------------------+------------------------+-------------------------------------+-------------------+
| TX IPv4 LIE Packets       | 16 Packets, 2608 Bytes | 4.49 Packets/Sec, 735.94 Bytes/Sec  | 0d 00h:00m:00.15s |
+---------------------------+------------------------+-------------------------------------+-------------------+
| RX IPv4 TIE Packets       | 0 Packets, 0 Bytes     |                                     |                   |
+---------------------------+------------------------+-------------------------------------+-------------------+
| TX IPv4 TIE Packets       | 0 Packets, 0 Bytes     |                                     |                   |
+---------------------------+------------------------+-------------------------------------+-------------------+
.                           .                        .                                     .                   .
.                           .                        .                                     .                   .
+---------------------------+------------------------+-------------------------------------+-------------------+
| Total RX Misorders        | 0 Packets              |                                     |                   |
+---------------------------+------------------------+-------------------------------------+-------------------+

Node Interfaces Security:
+------------------------------------------------+------------------------+-------------------------------------+-------------------+
| Description                                    | Value                  | Last Rate                           | Last Change       |
|                                                |                        | Over Last 10 Changes                |                   |
+------------------------------------------------+------------------------+-------------------------------------+-------------------+
| Missing outer security envelope                | 0 Packets, 0 Bytes     |                                     |                   |
+------------------------------------------------+------------------------+-------------------------------------+-------------------+
| Zero outer key id not accepted                 | 0 Packets, 0 Bytes     |                                     |                   |
+------------------------------------------------+------------------------+-------------------------------------+-------------------+
| Non-zero outer key id not accepted             | 0 Packets, 0 Bytes     |                                     |                   |
+------------------------------------------------+------------------------+-------------------------------------+-------------------+
| Incorrect outer fingerprint                    | 0 Packets, 0 Bytes     |                                     |                   |
+------------------------------------------------+------------------------+-------------------------------------+-------------------+
.                                                .                        .                                     .                   .
.                                                .                        .                                     .                   .
+------------------------------------------------+------------------------+-------------------------------------+-------------------+
| Empty origin fingerprint accepted              | 0 Packets, 0 Bytes     |                                     |                   |
+------------------------------------------------+------------------------+-------------------------------------+-------------------+

Node Interface LIE FSMs:
+------------------------------------------------------------+----------------+-----------------------+-------------------+
| Description                                                | Value          | Last Rate             | Last Change       |
|                                                            |                | Over Last 10 Changes  |                   |
+------------------------------------------------------------+----------------+-----------------------+-------------------+
| Event-Transitions None -[None]-&gt; ONE_WAY                   | 0 Transitions  |                       |                   |
+------------------------------------------------------------+----------------+-----------------------+-------------------+
| Event-Transitions ONE_WAY -[LIE_RECEIVED]-&gt; ONE_WAY        | 0 Transitions  |                       |                   |
+------------------------------------------------------------+----------------+-----------------------+-------------------+
| Event-Transitions ONE_WAY -[NEW_NEIGHBOR]-&gt; TWO_WAY        | 0 Transitions  |                       |                   |
+------------------------------------------------------------+----------------+-----------------------+-------------------+
| Event-Transitions ONE_WAY -[SEND_LIE]-&gt; ONE_WAY            | 4 Transitions  | 1.00 Transitions/Sec  | 0d 00h:00m:00.16s |
+------------------------------------------------------------+----------------+-----------------------+-------------------+
.                                                            .                .                       .                   .
.                                                            .                .                       .                   .
+------------------------------------------------------------+----------------+-----------------------+-------------------+
| Transitions TWO_WAY -&gt; TWO_WAY                             | 0 Transitions  |                       |                   |
+------------------------------------------------------------+----------------+-----------------------+-------------------+
</pre>
<!-- OUTPUT-END -->

### show node statistics exclude-zero

The "<b>show engine statistics</b>" command shows all the statistics for the current node, excluding
any zero statistics.

Example:

<!-- OUTPUT-START: agg_101> show node statistics exclude-zero -->
<pre>
agg_101> <b>show node statistics exclude-zero</b>
Node ZTP FSM:
+------------------------------------------------------------------------------------------+----------------+----------------------+-------------------+
| Description                                                                              | Value          | Last Rate            | Last Change       |
|                                                                                          |                | Over Last 10 Changes |                   |
+------------------------------------------------------------------------------------------+----------------+----------------------+-------------------+
| Event-Transitions COMPUTE_BEST_OFFER -[COMPUTATION_DONE]-&gt; UPDATING_CLIENTS              | 1 Transition   |                      | 0d 00h:00m:03.20s |
+------------------------------------------------------------------------------------------+----------------+----------------------+-------------------+
| Event-Transitions UPDATING_CLIENTS -[CHANGE_LOCAL_CONFIGURED_LEVEL]-&gt; COMPUTE_BEST_OFFER | 1 Transition   |                      | 0d 00h:00m:03.20s |
+------------------------------------------------------------------------------------------+----------------+----------------------+-------------------+
| Event-Transitions UPDATING_CLIENTS -[NEIGHBOR_OFFER]-&gt; UPDATING_CLIENTS                  | 24 Transitions | 9.08 Transitions/Sec | 0d 00h:00m:00.15s |
+------------------------------------------------------------------------------------------+----------------+----------------------+-------------------+
| Events CHANGE_LOCAL_CONFIGURED_LEVEL                                                     | 1 Event        |                      | 0d 00h:00m:03.20s |
+------------------------------------------------------------------------------------------+----------------+----------------------+-------------------+
.                                                                                          .                .                      .                   .
.                                                                                          .                .                      .                   .
+------------------------------------------------------------------------------------------+----------------+----------------------+-------------------+
| Transitions UPDATING_CLIENTS -&gt; UPDATING_CLIENTS                                         | 24 Transitions | 9.08 Transitions/Sec | 0d 00h:00m:00.15s |
+------------------------------------------------------------------------------------------+----------------+----------------------+-------------------+

Node Interfaces Traffic:
+---------------------------+------------------------+-------------------------------------+-------------------+
| Description               | Value                  | Last Rate                           | Last Change       |
|                           |                        | Over Last 10 Changes                |                   |
+---------------------------+------------------------+-------------------------------------+-------------------+
| RX IPv4 LIE Packets       | 12 Packets, 2040 Bytes | 3.01 Packets/Sec, 511.61 Bytes/Sec  | 0d 00h:00m:00.15s |
+---------------------------+------------------------+-------------------------------------+-------------------+
| TX IPv4 LIE Packets       | 16 Packets, 2608 Bytes | 4.49 Packets/Sec, 735.94 Bytes/Sec  | 0d 00h:00m:00.26s |
+---------------------------+------------------------+-------------------------------------+-------------------+
| RX IPv4 TIDE Packets      | 6 Packets, 3442 Bytes  | 2.34 Packets/Sec, 1176.01 Bytes/Sec | 0d 00h:00m:01.13s |
+---------------------------+------------------------+-------------------------------------+-------------------+
| TX IPv4 TIDE Packets      | 6 Packets, 3442 Bytes  | 2.49 Packets/Sec, 1465.57 Bytes/Sec | 0d 00h:00m:01.25s |
+---------------------------+------------------------+-------------------------------------+-------------------+
.                           .                        .                                     .                   .
.                           .                        .                                     .                   .
+---------------------------+------------------------+-------------------------------------+-------------------+
| Total TX Packets          | 38 Packets, 8658 Bytes | 9.13 Packets/Sec, 1494.81 Bytes/Sec | 0d 00h:00m:00.26s |
+---------------------------+------------------------+-------------------------------------+-------------------+

Node Interfaces Security:
+----------------------------------+------------------------+-------------------------------------+-------------------+
| Description                      | Value                  | Last Rate                           | Last Change       |
|                                  |                        | Over Last 10 Changes                |                   |
+----------------------------------+------------------------+-------------------------------------+-------------------+
| Empty outer fingerprint accepted | 30 Packets, 7522 Bytes | 9.04 Packets/Sec, 1768.17 Bytes/Sec | 0d 00h:00m:00.15s |
+----------------------------------+------------------------+-------------------------------------+-------------------+

Node Interface LIE FSMs:
+---------------------------------------------------------+----------------+-----------------------+-------------------+
| Description                                             | Value          | Last Rate             | Last Change       |
|                                                         |                | Over Last 10 Changes  |                   |
+---------------------------------------------------------+----------------+-----------------------+-------------------+
| Event-Transitions ONE_WAY -[SEND_LIE]-&gt; ONE_WAY         | 4 Transitions  | 1.00 Transitions/Sec  | 0d 00h:00m:00.27s |
+---------------------------------------------------------+----------------+-----------------------+-------------------+
| Event-Transitions ONE_WAY -[TIMER_TICK]-&gt; ONE_WAY       | 4 Transitions  | 1.00 Transitions/Sec  | 0d 00h:00m:00.27s |
+---------------------------------------------------------+----------------+-----------------------+-------------------+
| Event-Transitions THREE_WAY -[LIE_RECEIVED]-&gt; THREE_WAY | 24 Transitions | 9.06 Transitions/Sec  | 0d 00h:00m:00.15s |
+---------------------------------------------------------+----------------+-----------------------+-------------------+
| Event-Transitions THREE_WAY -[SEND_LIE]-&gt; THREE_WAY     | 12 Transitions | 3.00 Transitions/Sec  | 0d 00h:00m:00.26s |
+---------------------------------------------------------+----------------+-----------------------+-------------------+
.                                                         .                .                       .                   .
.                                                         .                .                       .                   .
+---------------------------------------------------------+----------------+-----------------------+-------------------+
| Transitions THREE_WAY -&gt; THREE_WAY                      | 48 Transitions | 75.24 Transitions/Sec | 0d 00h:00m:00.15s |
+---------------------------------------------------------+----------------+-----------------------+-------------------+
</pre>
<!-- OUTPUT-END -->

### show nodes

The "<b>show nodes</b>" command shows a summary of all RIFT nodes running in the RIFT protocol engine.

You can make anyone of the listed nodes the currently active node using the "<b>set node</b> <i>node</i>" command.

Example:

<!-- OUTPUT-START: agg_101> show nodes -->
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
.           .        .         .
.           .        .         .
+-----------+--------+---------+
| edge_2002 | 2002   | True    |
+-----------+--------+---------+
</pre>
<!-- OUTPUT-END -->

### show nodes level

The "<b>show nodes level</b>" command shows information on automatic level derivation procedures
for all RIFT nodes in the RIFT topology:

Example:

<!-- OUTPUT-START: agg_101> show nodes level -->
<pre>
agg_101> <b>show nodes level</b>
+-----------+--------+---------+---------------+-------+
| Node      | System | Running | Configured    | Level |
| Name      | ID     |         | Level         | Value |
+-----------+--------+---------+---------------+-------+
| agg_101   | 101    | True    | undefined     | 23    |
+-----------+--------+---------+---------------+-------+
| agg_102   | 102    | True    | undefined     | 23    |
+-----------+--------+---------+---------------+-------+
| agg_201   | 201    | True    | undefined     | 23    |
+-----------+--------+---------+---------------+-------+
| agg_202   | 202    | True    | undefined     | 23    |
+-----------+--------+---------+---------------+-------+
.           .        .         .               .       .
.           .        .         .               .       .
+-----------+--------+---------+---------------+-------+
| edge_2002 | 2002   | True    | 0             | 0     |
+-----------+--------+---------+---------------+-------+
</pre>
<!-- OUTPUT-END -->

### show routes

The "<b>show routes</b>" command shows all routes in the Routing Information Base (RIB) of the
current node. It shows both the IPv4 RIB and the IPv6 RIB.

Example:

<!-- OUTPUT-START: agg_101> show routes -->
<pre>
agg_101> <b>show routes</b>
IPv4 Routes:
+---------------+-----------+---------------------------+
| Prefix        | Owner     | Next-hops                 |
+---------------+-----------+---------------------------+
| 0.0.0.0/0     | North SPF | if_101_1 172.31.15.176    |
+---------------+-----------+---------------------------+
| 1.1.1.0/24    | South SPF | if_101_1001 172.31.15.176 |
+---------------+-----------+---------------------------+
| 1.1.2.0/24    | South SPF | if_101_1001 172.31.15.176 |
+---------------+-----------+---------------------------+
| 1.1.3.0/24    | South SPF | if_101_1001 172.31.15.176 |
+---------------+-----------+---------------------------+
.               .           .                           .
.               .           .                           .
+---------------+-----------+---------------------------+
| 99.99.99.0/24 | South SPF | if_101_1001 172.31.15.176 |
|               |           | if_101_1002 172.31.15.176 |
+---------------+-----------+---------------------------+

IPv6 Routes:
+--------+-----------+----------------------------------+
| Prefix | Owner     | Next-hops                        |
+--------+-----------+----------------------------------+
| ::/0   | North SPF | if_101_1 fe80::84a:2ff:fe78:2746 |
+--------+-----------+----------------------------------+
</pre>
<!-- OUTPUT-END -->

### show routes family <i>family</i>

The "<b>show routes family</b> <i>family</i>" command shows the routes of a given address family in
the Routing Information Base (RIB) of the current node.

The <i>family</i> parameter can be "<b>ipv4</b>" or "<b>ipv6</b>"

Example:

<!-- OUTPUT-START: agg_101> show routes family ipv4 -->
<pre>
agg_101> <b>show routes family ipv4</b>
IPv4 Routes:
+---------------+-----------+---------------------------+
| Prefix        | Owner     | Next-hops                 |
+---------------+-----------+---------------------------+
| 0.0.0.0/0     | North SPF | if_101_1 172.31.15.176    |
+---------------+-----------+---------------------------+
| 1.1.1.0/24    | South SPF | if_101_1001 172.31.15.176 |
+---------------+-----------+---------------------------+
| 1.1.2.0/24    | South SPF | if_101_1001 172.31.15.176 |
+---------------+-----------+---------------------------+
| 1.1.3.0/24    | South SPF | if_101_1001 172.31.15.176 |
+---------------+-----------+---------------------------+
.               .           .                           .
.               .           .                           .
+---------------+-----------+---------------------------+
| 99.99.99.0/24 | South SPF | if_101_1001 172.31.15.176 |
|               |           | if_101_1002 172.31.15.176 |
+---------------+-----------+---------------------------+
</pre>
<!-- OUTPUT-END -->

### show routes prefix <i>prefix</i>

The "<b>show routes prefix</b> <i>prefix</i>" command shows the routes for a given prefix in the
Routing Information Base (RIB) of the current node.

Parameter <i>prefix</i> must be an IPv4 prefix or an IPv6 prefix

Example:

<!-- OUTPUT-START: agg_101> show routes prefix ::/0 -->
<pre>
agg_101> <b>show routes prefix ::/0</b>
+--------+-----------+----------------------------------+
| Prefix | Owner     | Next-hops                        |
+--------+-----------+----------------------------------+
| ::/0   | North SPF | if_101_1 fe80::84a:2ff:fe78:2746 |
+--------+-----------+----------------------------------+
</pre>
<!-- OUTPUT-END -->

### show routes prefix <i>prefix</i> owner <i>owner</i>

The "<b>show routes prefix</b> <i>prefix</i> <b>owner</b> <i>owner</i>" command shows the routes for
a given prefix and a given owner in the Routing Information Base (RIB) of the current node.

Parameter <i>prefix</i> must be an IPv4 prefix or an IPv6 prefix.

Parameter <i>owner</i> must be <b>south-spf</b> or <b>north-spf</b>.

Example:

<!-- OUTPUT-START: agg_101> show routes prefix ::/0 owner north-spf -->
<pre>
agg_101> <b>show routes prefix ::/0 owner north-spf</b>
+--------+-----------+----------------------------------+
| Prefix | Owner     | Next-hops                        |
+--------+-----------+----------------------------------+
| ::/0   | North SPF | if_101_1 fe80::84a:2ff:fe78:2746 |
+--------+-----------+----------------------------------+
</pre>
<!-- OUTPUT-END -->

### show security

The "<b>show security</b>" shows the configuration and statistics for security:

 * The list of configured keys, the active key, and the accepted keys.

<!-- OUTPUT-START: agg_101> show security -->
<pre>
agg_101> <b>show security</b>
Security Keys:
+--------+-----------+--------+
| Key ID | Algorithm | Secret |
+--------+-----------+--------+
| 0      | null      |        |
+--------+-----------+--------+

Origin Keys:
+--------------------+-----------+
| Key                | Key ID(s) |
+--------------------+-----------+
| Active Origin Key  | None      |
+--------------------+-----------+
| Accept Origin Keys |           |
+--------------------+-----------+

Security Statistics:
+------------------------------------------------+------------------------+-------------------------------------+-------------------+
| Description                                    | Value                  | Last Rate                           | Last Change       |
|                                                |                        | Over Last 10 Changes                |                   |
+------------------------------------------------+------------------------+-------------------------------------+-------------------+
| Missing outer security envelope                | 0 Packets, 0 Bytes     |                                     |                   |
+------------------------------------------------+------------------------+-------------------------------------+-------------------+
| Zero outer key id not accepted                 | 0 Packets, 0 Bytes     |                                     |                   |
+------------------------------------------------+------------------------+-------------------------------------+-------------------+
| Non-zero outer key id not accepted             | 0 Packets, 0 Bytes     |                                     |                   |
+------------------------------------------------+------------------------+-------------------------------------+-------------------+
| Incorrect outer fingerprint                    | 0 Packets, 0 Bytes     |                                     |                   |
+------------------------------------------------+------------------------+-------------------------------------+-------------------+
.                                                .                        .                                     .                   .
.                                                .                        .                                     .                   .
+------------------------------------------------+------------------------+-------------------------------------+-------------------+
| Empty origin fingerprint accepted              | 0 Packets, 0 Bytes     |                                     |                   |
+------------------------------------------------+------------------------+-------------------------------------+-------------------+
</pre>
<!-- OUTPUT-END -->

### show spf

The "<b>show spf</b>" command shows the results of the most recent Shortest Path First (SPF) execution for the current node.

Note: the SPF algorithm is also known as the Dijkstra algorithm.

Example:

<!-- OUTPUT-START: agg_101> show spf -->
<pre>
agg_101> <b>show spf</b>
SPF Statistics:
+---------------+----+
| SPF Runs      | 4  |
+---------------+----+
| SPF Deferrals | 18 |
+---------------+----+

South SPF Destinations:
+------------------+------+---------+-------------+------+--------------+---------------------------+-------------------------------------+
| Destination      | Cost | Is Leaf | Predecessor | Tags | Disaggregate | IPv4 Next-hops            | IPv6 Next-hops                      |
|                  |      |         | System IDs  |      |              |                           |                                     |
+------------------+------+---------+-------------+------+--------------+---------------------------+-------------------------------------+
| 101 (agg_101)    | 0    | False   |             |      |              |                           |                                     |
+------------------+------+---------+-------------+------+--------------+---------------------------+-------------------------------------+
| 1001 (edge_1001) | 1    | True    | 101         |      |              | if_101_1001 172.31.15.176 | if_101_1001 fe80::84a:2ff:fe78:2746 |
+------------------+------+---------+-------------+------+--------------+---------------------------+-------------------------------------+
| 1002 (edge_1002) | 1    | True    | 101         |      |              | if_101_1002 172.31.15.176 | if_101_1002 fe80::84a:2ff:fe78:2746 |
+------------------+------+---------+-------------+------+--------------+---------------------------+-------------------------------------+
| 1.1.1.0/24       | 2    | True    | 1001        |      |              | if_101_1001 172.31.15.176 | if_101_1001 fe80::84a:2ff:fe78:2746 |
+------------------+------+---------+-------------+------+--------------+---------------------------+-------------------------------------+
.                  .      .         .             .      .              .                           .                                     .
.                  .      .         .             .      .              .                           .                                     .
+------------------+------+---------+-------------+------+--------------+---------------------------+-------------------------------------+
| 99.99.99.0/24    | 2    | True    | 1001        | 9992 |              | if_101_1001 172.31.15.176 | if_101_1001 fe80::84a:2ff:fe78:2746 |
|                  |      |         | 1002        | 9991 |              | if_101_1002 172.31.15.176 | if_101_1002 fe80::84a:2ff:fe78:2746 |
+------------------+------+---------+-------------+------+--------------+---------------------------+-------------------------------------+

North SPF Destinations:
+---------------+------+---------+-------------+------+--------------+------------------------+----------------------------------+
| Destination   | Cost | Is Leaf | Predecessor | Tags | Disaggregate | IPv4 Next-hops         | IPv6 Next-hops                   |
|               |      |         | System IDs  |      |              |                        |                                  |
+---------------+------+---------+-------------+------+--------------+------------------------+----------------------------------+
| 1 (core_1)    | 1    | False   | 101         |      |              | if_101_1 172.31.15.176 | if_101_1 fe80::84a:2ff:fe78:2746 |
+---------------+------+---------+-------------+------+--------------+------------------------+----------------------------------+
| 101 (agg_101) | 0    | False   |             |      |              |                        |                                  |
+---------------+------+---------+-------------+------+--------------+------------------------+----------------------------------+
| 0.0.0.0/0     | 2    | False   | 1           |      |              | if_101_1 172.31.15.176 | if_101_1 fe80::84a:2ff:fe78:2746 |
+---------------+------+---------+-------------+------+--------------+------------------------+----------------------------------+
| ::/0          | 2    | False   | 1           |      |              | if_101_1 172.31.15.176 | if_101_1 fe80::84a:2ff:fe78:2746 |
+---------------+------+---------+-------------+------+--------------+------------------------+----------------------------------+

South SPF (with East-West Links) Destinations:
+-------------+------+---------+-------------+------+--------------+----------------+----------------+
| Destination | Cost | Is Leaf | Predecessor | Tags | Disaggregate | IPv4 Next-hops | IPv6 Next-hops |
|             |      |         | System IDs  |      |              |                |                |
+-------------+------+---------+-------------+------+--------------+----------------+----------------+
</pre>
<!-- OUTPUT-END -->

### show spf direction <i>direction</i>

The "<b>show spf direction</b> <i>direction</i>" command shows the results of the most recent Shortest Path First (SPF) execution for the current node in the specified direction.

Parameter <i>direction</i> must be <b>south</b> or <b>north</b>

Example:

<!-- OUTPUT-START: agg_101> show spf direction north -->
<pre>
agg_101> <b>show spf direction north</b>
North SPF Destinations:
+---------------+------+---------+-------------+------+--------------+------------------------+----------------------------------+
| Destination   | Cost | Is Leaf | Predecessor | Tags | Disaggregate | IPv4 Next-hops         | IPv6 Next-hops                   |
|               |      |         | System IDs  |      |              |                        |                                  |
+---------------+------+---------+-------------+------+--------------+------------------------+----------------------------------+
| 1 (core_1)    | 1    | False   | 101         |      |              | if_101_1 172.31.15.176 | if_101_1 fe80::84a:2ff:fe78:2746 |
+---------------+------+---------+-------------+------+--------------+------------------------+----------------------------------+
| 101 (agg_101) | 0    | False   |             |      |              |                        |                                  |
+---------------+------+---------+-------------+------+--------------+------------------------+----------------------------------+
| 0.0.0.0/0     | 2    | False   | 1           |      |              | if_101_1 172.31.15.176 | if_101_1 fe80::84a:2ff:fe78:2746 |
+---------------+------+---------+-------------+------+--------------+------------------------+----------------------------------+
| ::/0          | 2    | False   | 1           |      |              | if_101_1 172.31.15.176 | if_101_1 fe80::84a:2ff:fe78:2746 |
+---------------+------+---------+-------------+------+--------------+------------------------+----------------------------------+
</pre>
<!-- OUTPUT-END -->

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

<!-- OUTPUT-START: agg_101> show spf direction north destination ::/0 -->
<pre>
agg_101> <b>show spf direction north destination ::/0</b>
+-------------+------+---------+-------------+------+--------------+------------------------+----------------------------------+
| Destination | Cost | Is Leaf | Predecessor | Tags | Disaggregate | IPv4 Next-hops         | IPv6 Next-hops                   |
|             |      |         | System IDs  |      |              |                        |                                  |
+-------------+------+---------+-------------+------+--------------+------------------------+----------------------------------+
| ::/0        | 2    | False   | 1           |      |              | if_101_1 172.31.15.176 | if_101_1 fe80::84a:2ff:fe78:2746 |
+-------------+------+---------+-------------+------+--------------+------------------------+----------------------------------+
</pre>
<!-- OUTPUT-END -->

Example:

<!-- OUTPUT-START: agg_101> show spf direction north destination 5 -->
<pre>
agg_101> <b>show spf direction north destination 5</b>
Destination 5 not present
</pre>
<!-- OUTPUT-END -->

### show tie-db

The "<b>show tie-db</b>" command shows the contents of the Topology Information Element Database (TIE-DB) for the current node.

Note: the TIE-DB is also known as the Link-State Database (LSDB)

Example:

<!-- OUTPUT-START: agg_101> show tie-db -->
<pre>
agg_101> <b>show tie-db</b>
+-----------+------------+--------+--------+--------+----------+-------------------------+
| Direction | Originator | Type   | TIE Nr | Seq Nr | Lifetime | Contents                |
+-----------+------------+--------+--------+--------+----------+-------------------------+
| South     | 1          | Node   | 1      | 5      | 604787   | Name: core_1            |
|           |            |        |        |        |          | Level: 24               |
|           |            |        |        |        |          | Capabilities:           |
|           |            |        |        |        |          |   Flood reduction: True |
|           |            |        |        |        |          | Neighbor: 101           |
|           |            |        |        |        |          |   Level: 23             |
|           |            |        |        |        |          |   Cost: 1               |
|           |            |        |        |        |          |   Bandwidth: 100 Mbps   |
|           |            |        |        |        |          |   Link: 1-1             |
|           |            |        |        |        |          | Neighbor: 102           |
|           |            |        |        |        |          |   Level: 23             |
|           |            |        |        |        |          |   Cost: 1               |
|           |            |        |        |        |          |   Bandwidth: 100 Mbps   |
|           |            |        |        |        |          |   Link: 2-1             |
|           |            |        |        |        |          | Neighbor: 201           |
|           |            |        |        |        |          |   Level: 23             |
|           |            |        |        |        |          |   Cost: 1               |
|           |            |        |        |        |          |   Bandwidth: 100 Mbps   |
|           |            |        |        |        |          |   Link: 3-1             |
|           |            |        |        |        |          | Neighbor: 202           |
|           |            |        |        |        |          |   Level: 23             |
|           |            |        |        |        |          |   Cost: 1               |
|           |            |        |        |        |          |   Bandwidth: 100 Mbps   |
|           |            |        |        |        |          |   Link: 4-1             |
+-----------+------------+--------+--------+--------+----------+-------------------------+
| South     | 1          | Prefix | 2      | 1      | 604787   | Prefix: 0.0.0.0/0       |
|           |            |        |        |        |          |   Metric: 1             |
|           |            |        |        |        |          | Prefix: ::/0            |
|           |            |        |        |        |          |   Metric: 1             |
+-----------+------------+--------+--------+--------+----------+-------------------------+
| South     | 101        | Node   | 1      | 4      | 604787   | Name: agg_101           |
|           |            |        |        |        |          | Level: 23               |
|           |            |        |        |        |          | Capabilities:           |
|           |            |        |        |        |          |   Flood reduction: True |
|           |            |        |        |        |          | Neighbor: 1             |
|           |            |        |        |        |          |   Level: 24             |
|           |            |        |        |        |          |   Cost: 1               |
|           |            |        |        |        |          |   Bandwidth: 100 Mbps   |
|           |            |        |        |        |          |   Link: 1-1             |
|           |            |        |        |        |          | Neighbor: 1001          |
|           |            |        |        |        |          |   Level: 0              |
|           |            |        |        |        |          |   Cost: 1               |
|           |            |        |        |        |          |   Bandwidth: 100 Mbps   |
|           |            |        |        |        |          |   Link: 3-1             |
|           |            |        |        |        |          | Neighbor: 1002          |
|           |            |        |        |        |          |   Level: 0              |
|           |            |        |        |        |          |   Cost: 1               |
|           |            |        |        |        |          |   Bandwidth: 100 Mbps   |
|           |            |        |        |        |          |   Link: 4-1             |
+-----------+------------+--------+--------+--------+----------+-------------------------+
| South     | 101        | Prefix | 2      | 1      | 604787   | Prefix: 0.0.0.0/0       |
|           |            |        |        |        |          |   Metric: 1             |
|           |            |        |        |        |          | Prefix: ::/0            |
|           |            |        |        |        |          |   Metric: 1             |
+-----------+------------+--------+--------+--------+----------+-------------------------+
.           .            .        .        .        .          .                         .
.           .            .        .        .        .          .                         .
+-----------+------------+--------+--------+--------+----------+-------------------------+
| North     | 1002       | Prefix | 2      | 1      | 604786   | Prefix: 1.2.1.0/24      |
|           |            |        |        |        |          |   Metric: 1             |
|           |            |        |        |        |          | Prefix: 1.2.2.0/24      |
|           |            |        |        |        |          |   Metric: 1             |
|           |            |        |        |        |          | Prefix: 1.2.3.0/24      |
|           |            |        |        |        |          |   Metric: 1             |
|           |            |        |        |        |          | Prefix: 1.2.4.0/24      |
|           |            |        |        |        |          |   Metric: 1             |
|           |            |        |        |        |          | Prefix: 99.99.99.0/24   |
|           |            |        |        |        |          |   Metric: 1             |
|           |            |        |        |        |          |   Tag: 9992             |
+-----------+------------+--------+--------+--------+----------+-------------------------+
</pre>
<!-- OUTPUT-END -->


### show tie-db direction <i>direction</i>

The "<b>show tie-db direction <i>direction</i></b>" command shows all the TIEs in the Topology 
Information Element Database (TIE-DB) for the current node and the given direction.

Parameter <i>direction</i> must be one of the following: south or north.

Example:

<!-- OUTPUT-START: agg_101> show tie-db direction south -->
<pre>
agg_101> <b>show tie-db direction south</b>
+-----------+------------+--------+--------+--------+----------+-------------------------+
| Direction | Originator | Type   | TIE Nr | Seq Nr | Lifetime | Contents                |
+-----------+------------+--------+--------+--------+----------+-------------------------+
| South     | 1          | Node   | 1      | 5      | 604787   | Name: core_1            |
|           |            |        |        |        |          | Level: 24               |
|           |            |        |        |        |          | Capabilities:           |
|           |            |        |        |        |          |   Flood reduction: True |
|           |            |        |        |        |          | Neighbor: 101           |
|           |            |        |        |        |          |   Level: 23             |
|           |            |        |        |        |          |   Cost: 1               |
|           |            |        |        |        |          |   Bandwidth: 100 Mbps   |
|           |            |        |        |        |          |   Link: 1-1             |
|           |            |        |        |        |          | Neighbor: 102           |
|           |            |        |        |        |          |   Level: 23             |
|           |            |        |        |        |          |   Cost: 1               |
|           |            |        |        |        |          |   Bandwidth: 100 Mbps   |
|           |            |        |        |        |          |   Link: 2-1             |
|           |            |        |        |        |          | Neighbor: 201           |
|           |            |        |        |        |          |   Level: 23             |
|           |            |        |        |        |          |   Cost: 1               |
|           |            |        |        |        |          |   Bandwidth: 100 Mbps   |
|           |            |        |        |        |          |   Link: 3-1             |
|           |            |        |        |        |          | Neighbor: 202           |
|           |            |        |        |        |          |   Level: 23             |
|           |            |        |        |        |          |   Cost: 1               |
|           |            |        |        |        |          |   Bandwidth: 100 Mbps   |
|           |            |        |        |        |          |   Link: 4-1             |
+-----------+------------+--------+--------+--------+----------+-------------------------+
| South     | 1          | Prefix | 2      | 1      | 604787   | Prefix: 0.0.0.0/0       |
|           |            |        |        |        |          |   Metric: 1             |
|           |            |        |        |        |          | Prefix: ::/0            |
|           |            |        |        |        |          |   Metric: 1             |
+-----------+------------+--------+--------+--------+----------+-------------------------+
| South     | 101        | Node   | 1      | 4      | 604787   | Name: agg_101           |
|           |            |        |        |        |          | Level: 23               |
|           |            |        |        |        |          | Capabilities:           |
|           |            |        |        |        |          |   Flood reduction: True |
|           |            |        |        |        |          | Neighbor: 1             |
|           |            |        |        |        |          |   Level: 24             |
|           |            |        |        |        |          |   Cost: 1               |
|           |            |        |        |        |          |   Bandwidth: 100 Mbps   |
|           |            |        |        |        |          |   Link: 1-1             |
|           |            |        |        |        |          | Neighbor: 1001          |
|           |            |        |        |        |          |   Level: 0              |
|           |            |        |        |        |          |   Cost: 1               |
|           |            |        |        |        |          |   Bandwidth: 100 Mbps   |
|           |            |        |        |        |          |   Link: 3-1             |
|           |            |        |        |        |          | Neighbor: 1002          |
|           |            |        |        |        |          |   Level: 0              |
|           |            |        |        |        |          |   Cost: 1               |
|           |            |        |        |        |          |   Bandwidth: 100 Mbps   |
|           |            |        |        |        |          |   Link: 4-1             |
+-----------+------------+--------+--------+--------+----------+-------------------------+
| South     | 101        | Prefix | 2      | 1      | 604787   | Prefix: 0.0.0.0/0       |
|           |            |        |        |        |          |   Metric: 1             |
|           |            |        |        |        |          | Prefix: ::/0            |
|           |            |        |        |        |          |   Metric: 1             |
+-----------+------------+--------+--------+--------+----------+-------------------------+
| South     | 102        | Node   | 1      | 4      | 604788   | Name: agg_102           |
|           |            |        |        |        |          | Level: 23               |
|           |            |        |        |        |          | Capabilities:           |
|           |            |        |        |        |          |   Flood reduction: True |
|           |            |        |        |        |          | Neighbor: 1             |
|           |            |        |        |        |          |   Level: 24             |
|           |            |        |        |        |          |   Cost: 1               |
|           |            |        |        |        |          |   Bandwidth: 100 Mbps   |
|           |            |        |        |        |          |   Link: 1-2             |
|           |            |        |        |        |          | Neighbor: 1001          |
|           |            |        |        |        |          |   Level: 0              |
|           |            |        |        |        |          |   Cost: 1               |
|           |            |        |        |        |          |   Bandwidth: 100 Mbps   |
|           |            |        |        |        |          |   Link: 3-2             |
|           |            |        |        |        |          | Neighbor: 1002          |
|           |            |        |        |        |          |   Level: 0              |
|           |            |        |        |        |          |   Cost: 1               |
|           |            |        |        |        |          |   Bandwidth: 100 Mbps   |
|           |            |        |        |        |          |   Link: 4-2             |
+-----------+------------+--------+--------+--------+----------+-------------------------+
</pre>
<!-- OUTPUT-END -->

### show tie-db direction <i>direction</i> originator <i>originator</i>

The "<b>show tie-db direction <i>direction</i></b>" command shows all the TIEs in the Topology 
Information Element Database (TIE-DB) for the current node and the given direction and
the given originator.

Parameter <i>direction</i> must be one of the following: south or north.

Parameter <i>originator</i> must be an integer between 0 and 18446744073709551615.

Example:

<!-- OUTPUT-START: agg_101> show tie-db direction south originator 1 -->
<pre>
agg_101> <b>show tie-db direction south originator 1</b>
+-----------+------------+--------+--------+--------+----------+-------------------------+
| Direction | Originator | Type   | TIE Nr | Seq Nr | Lifetime | Contents                |
+-----------+------------+--------+--------+--------+----------+-------------------------+
| South     | 1          | Node   | 1      | 5      | 604787   | Name: core_1            |
|           |            |        |        |        |          | Level: 24               |
|           |            |        |        |        |          | Capabilities:           |
|           |            |        |        |        |          |   Flood reduction: True |
|           |            |        |        |        |          | Neighbor: 101           |
|           |            |        |        |        |          |   Level: 23             |
|           |            |        |        |        |          |   Cost: 1               |
|           |            |        |        |        |          |   Bandwidth: 100 Mbps   |
|           |            |        |        |        |          |   Link: 1-1             |
|           |            |        |        |        |          | Neighbor: 102           |
|           |            |        |        |        |          |   Level: 23             |
|           |            |        |        |        |          |   Cost: 1               |
|           |            |        |        |        |          |   Bandwidth: 100 Mbps   |
|           |            |        |        |        |          |   Link: 2-1             |
|           |            |        |        |        |          | Neighbor: 201           |
|           |            |        |        |        |          |   Level: 23             |
|           |            |        |        |        |          |   Cost: 1               |
|           |            |        |        |        |          |   Bandwidth: 100 Mbps   |
|           |            |        |        |        |          |   Link: 3-1             |
|           |            |        |        |        |          | Neighbor: 202           |
|           |            |        |        |        |          |   Level: 23             |
|           |            |        |        |        |          |   Cost: 1               |
|           |            |        |        |        |          |   Bandwidth: 100 Mbps   |
|           |            |        |        |        |          |   Link: 4-1             |
+-----------+------------+--------+--------+--------+----------+-------------------------+
| South     | 1          | Prefix | 2      | 1      | 604787   | Prefix: 0.0.0.0/0       |
|           |            |        |        |        |          |   Metric: 1             |
|           |            |        |        |        |          | Prefix: ::/0            |
|           |            |        |        |        |          |   Metric: 1             |
+-----------+------------+--------+--------+--------+----------+-------------------------+
</pre>
<!-- OUTPUT-END -->

### show tie-db direction <i>direction</i> originator <i>originator</i> tie-type <i>tie-type</i>

The "<b>show tie-db direction <i>direction</i></b>" command shows all the TIEs in the Topology 
Information Element Database (TIE-DB) for the current node and the given direction and
the given originator and the given tie-type.

Parameter <i>direction</i> must be one of the following: south or north.

Parameter <i>originator</i> must be an integer between 0 and 18446744073709551615.

Parameter <i>tie-type</i> must be one of the following: node, prefix, pos-dis-prefix, 
neg-dis-prefix, ext-prefix, pg-prefix, or key-value.

Example:

<!-- OUTPUT-START: agg_101> show tie-db direction south originator 1 tie-type node -->
<pre>
agg_101> <b>show tie-db direction south originator 1 tie-type node</b>
+-----------+------------+------+--------+--------+----------+-------------------------+
| Direction | Originator | Type | TIE Nr | Seq Nr | Lifetime | Contents                |
+-----------+------------+------+--------+--------+----------+-------------------------+
| South     | 1          | Node | 1      | 5      | 604787   | Name: core_1            |
|           |            |      |        |        |          | Level: 24               |
|           |            |      |        |        |          | Capabilities:           |
|           |            |      |        |        |          |   Flood reduction: True |
|           |            |      |        |        |          | Neighbor: 101           |
|           |            |      |        |        |          |   Level: 23             |
|           |            |      |        |        |          |   Cost: 1               |
|           |            |      |        |        |          |   Bandwidth: 100 Mbps   |
|           |            |      |        |        |          |   Link: 1-1             |
|           |            |      |        |        |          | Neighbor: 102           |
|           |            |      |        |        |          |   Level: 23             |
|           |            |      |        |        |          |   Cost: 1               |
|           |            |      |        |        |          |   Bandwidth: 100 Mbps   |
|           |            |      |        |        |          |   Link: 2-1             |
|           |            |      |        |        |          | Neighbor: 201           |
|           |            |      |        |        |          |   Level: 23             |
|           |            |      |        |        |          |   Cost: 1               |
|           |            |      |        |        |          |   Bandwidth: 100 Mbps   |
|           |            |      |        |        |          |   Link: 3-1             |
|           |            |      |        |        |          | Neighbor: 202           |
|           |            |      |        |        |          |   Level: 23             |
|           |            |      |        |        |          |   Cost: 1               |
|           |            |      |        |        |          |   Bandwidth: 100 Mbps   |
|           |            |      |        |        |          |   Link: 4-1             |
+-----------+------------+------+--------+--------+----------+-------------------------+
</pre>
<!-- OUTPUT-END -->

### stop

The "<b>stop</b> command closes the CLI session and terminates the RIFT engine.

Note: The <b>stop</b> command is similar to the <b>exit</b> command, except that the <b>exit</b>
command leaves the RIFT engine running when executed from a Telnet session.

Example:

<pre>
(env) $ python rift topology/two_by_two_by_two.yaml
Command Line Interface (CLI) available on port 50102
</pre>

<!-- OUTPUT-MANUAL: agg_101> stop -->
<pre>
$ telnet localhost 50102
Trying 127.0.0.1...
Connected to localhost.
Escape character is '^]'.
agg_101> <b>stop</b>
$ 
</pre>
