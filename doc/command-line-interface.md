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
  * [show interface <i>interface</i> packets](#show-interface-interface-packets)
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
show interface &lt;interface&gt; packets 
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
+---------------+-------------+------------------+-------------+-------------+
| Same-Level    | North-bound | South-bound      | Missing     | Extra       |
| Node          | Adjacencies | Adjacencies      | South-bound | South-bound |
|               |             |                  | Adjacencies | Adjacencies |
+---------------+-------------+------------------+-------------+-------------+
| agg_102 (102) | core_1 (1)  | edge_1001 (1001) |             |             |
|               |             | edge_1002 (1002) |             |             |
+---------------+-------------+------------------+-------------+-------------+

Partially Connected Interfaces:
+------+------------------------------------+
| Name | Nodes Causing Partial Connectivity |
+------+------------------------------------+

Positive Disaggregation TIEs:
+-----------+------------+------+--------+--------+----------+----------+
| Direction | Originator | Type | TIE Nr | Seq Nr | Lifetime | Contents |
+-----------+------------+------+--------+--------+----------+----------+

Negative Disaggregation TIEs:
+-----------+------------+------+--------+--------+----------+----------+
| Direction | Originator | Type | TIE Nr | Seq Nr | Lifetime | Contents |
+-----------+------------+------+--------+--------+----------+----------+
</pre>
<!-- OUTPUT-END -->

### show engine

The "<b>show engine</b>" command shows the status of the RIFT engine, i.e. global information
that applies to all nodes running in the RIFT engine.

Example:

<!-- OUTPUT-START: agg_101> show engine -->
<pre>
agg_101> <b>show engine</b>
+------------------------------------+--------------------+
| Stand-alone                        | False              |
| Interactive                        | True               |
| Simulated Interfaces               | True               |
| Physical Interface                 | eth0               |
| Telnet Port File                   | None               |
| IPv4 Multicast Loopback            | True               |
| IPv6 Multicast Loopback            | True               |
| Number of Nodes                    | 10                 |
| Transmit Source Address            | 127.0.0.1          |
| Flooding Reduction Enabled         | True               |
| Flooding Reduction Redundancy      | 2                  |
| Flooding Reduction Similarity      | 2                  |
| Flooding Reduction System Random   | 118041399331807045 |
| Timer slips &gt; 10ms                 | 0                  |
| Timer slips &gt; 100ms                | 0                  |
| Timer slips &gt; 1000ms               | 0                  |
| Max pending events processing time | 0.008028           |
| Max expired timers processing time | 0.014068           |
| Max select processing time         | 0.051124           |
| Max ready-to-read processing time  | 0.002698           |
+------------------------------------+--------------------+
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
+------------------------------------------------------------------------------------------+----------------+--------------------------+-------------------+
| Description                                                                              | Value          | Last Rate                | Last Change       |
|                                                                                          |                | Over Last 10 Changes     |                   |
+------------------------------------------------------------------------------------------+----------------+--------------------------+-------------------+
| Events CHANGE_LOCAL_CONFIGURED_LEVEL                                                     | 1 Event        |                          | 0d 00h:00m:00.37s |
+------------------------------------------------------------------------------------------+----------------+--------------------------+-------------------+
| Events NEIGHBOR_OFFER                                                                    | 48 Events      | 12901.14 Events/Sec      | 0d 00h:00m:00.05s |
+------------------------------------------------------------------------------------------+----------------+--------------------------+-------------------+
| Events BETTER_HAL                                                                        | 0 Events       |                          |                   |
+------------------------------------------------------------------------------------------+----------------+--------------------------+-------------------+
| Events BETTER_HAT                                                                        | 0 Events       |                          |                   |
+------------------------------------------------------------------------------------------+----------------+--------------------------+-------------------+
.                                                                                          .                .                          .                   .
.                                                                                          .                .                          .                   .
+------------------------------------------------------------------------------------------+----------------+--------------------------+-------------------+
| Event-Transitions UPDATING_CLIENTS -[CHANGE_LOCAL_CONFIGURED_LEVEL]-&gt; COMPUTE_BEST_OFFER | 1 Transition   |                          | 0d 00h:00m:00.37s |
+------------------------------------------------------------------------------------------+----------------+--------------------------+-------------------+

All Interfaces Traffic:
+---------------------------+-------------------------+------------------------------------------+-------------------+
| Description               | Value                   | Last Rate                                | Last Change       |
|                           |                         | Over Last 10 Changes                     |                   |
+---------------------------+-------------------------+------------------------------------------+-------------------+
| RX IPv4 LIE Packets       | 24 Packets, 4068 Bytes  | 186.59 Packets/Sec, 31928.17 Bytes/Sec   | 0d 00h:00m:00.06s |
+---------------------------+-------------------------+------------------------------------------+-------------------+
| TX IPv4 LIE Packets       | 28 Packets, 4648 Bytes  | 171.22 Packets/Sec, 29411.68 Bytes/Sec   | 0d 00h:00m:00.07s |
+---------------------------+-------------------------+------------------------------------------+-------------------+
| RX IPv4 TIE Packets       | 0 Packets, 0 Bytes      |                                          |                   |
+---------------------------+-------------------------+------------------------------------------+-------------------+
| TX IPv4 TIE Packets       | 0 Packets, 0 Bytes      |                                          |                   |
+---------------------------+-------------------------+------------------------------------------+-------------------+
.                           .                         .                                          .                   .
.                           .                         .                                          .                   .
+---------------------------+-------------------------+------------------------------------------+-------------------+
| Total RX Misorders        | 0 Packets               |                                          |                   |
+---------------------------+-------------------------+------------------------------------------+-------------------+

All Interfaces Security:
+------------------------------------------------+-------------------------+-----------------------------------------+-------------------+
| Description                                    | Value                   | Last Rate                               | Last Change       |
|                                                |                         | Over Last 10 Changes                    |                   |
+------------------------------------------------+-------------------------+-----------------------------------------+-------------------+
| Missing outer security envelope                | 0 Packets, 0 Bytes      |                                         |                   |
+------------------------------------------------+-------------------------+-----------------------------------------+-------------------+
| Zero outer key id not accepted                 | 0 Packets, 0 Bytes      |                                         |                   |
+------------------------------------------------+-------------------------+-----------------------------------------+-------------------+
| Non-zero outer key id not accepted             | 0 Packets, 0 Bytes      |                                         |                   |
+------------------------------------------------+-------------------------+-----------------------------------------+-------------------+
| Incorrect outer fingerprint                    | 0 Packets, 0 Bytes      |                                         |                   |
+------------------------------------------------+-------------------------+-----------------------------------------+-------------------+
.                                                .                         .                                         .                   .
.                                                .                         .                                         .                   .
+------------------------------------------------+-------------------------+-----------------------------------------+-------------------+
| Empty origin fingerprint accepted              | 0 Packets, 0 Bytes      |                                         |                   |
+------------------------------------------------+-------------------------+-----------------------------------------+-------------------+

All Interface LIE FSMs:
+------------------------------------------------------------+----------------+-------------------------+-------------------+
| Description                                                | Value          | Last Rate               | Last Change       |
|                                                            |                | Over Last 10 Changes    |                   |
+------------------------------------------------------------+----------------+-------------------------+-------------------+
| Events TIMER_TICK                                          | 28 Events      | 171.22 Events/Sec       | 0d 00h:00m:00.08s |
+------------------------------------------------------------+----------------+-------------------------+-------------------+
| Events LEVEL_CHANGED                                       | 0 Events       |                         |                   |
+------------------------------------------------------------+----------------+-------------------------+-------------------+
| Events HAL_CHANGED                                         | 0 Events       |                         |                   |
+------------------------------------------------------------+----------------+-------------------------+-------------------+
| Events HAT_CHANGED                                         | 0 Events       |                         |                   |
+------------------------------------------------------------+----------------+-------------------------+-------------------+
.                                                            .                .                         .                   .
.                                                            .                .                         .                   .
+------------------------------------------------------------+----------------+-------------------------+-------------------+
| Event-Transitions TWO_WAY -[TIMER_TICK]-&gt; TWO_WAY          | 0 Transitions  |                         |                   |
+------------------------------------------------------------+----------------+-------------------------+-------------------+
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
+------------------------------------------------------------------------------------------+----------------+--------------------------+-------------------+
| Description                                                                              | Value          | Last Rate                | Last Change       |
|                                                                                          |                | Over Last 10 Changes     |                   |
+------------------------------------------------------------------------------------------+----------------+--------------------------+-------------------+
| Events CHANGE_LOCAL_CONFIGURED_LEVEL                                                     | 1 Event        |                          | 0d 00h:00m:00.48s |
+------------------------------------------------------------------------------------------+----------------+--------------------------+-------------------+
| Events NEIGHBOR_OFFER                                                                    | 48 Events      | 12901.14 Events/Sec      | 0d 00h:00m:00.17s |
+------------------------------------------------------------------------------------------+----------------+--------------------------+-------------------+
| Events COMPUTATION_DONE                                                                  | 1 Event        |                          | 0d 00h:00m:00.48s |
+------------------------------------------------------------------------------------------+----------------+--------------------------+-------------------+
| Enter COMPUTE_BEST_OFFER                                                                 | 1 Entry        |                          | 0d 00h:00m:00.48s |
+------------------------------------------------------------------------------------------+----------------+--------------------------+-------------------+
.                                                                                          .                .                          .                   .
.                                                                                          .                .                          .                   .
+------------------------------------------------------------------------------------------+----------------+--------------------------+-------------------+
| Event-Transitions UPDATING_CLIENTS -[CHANGE_LOCAL_CONFIGURED_LEVEL]-&gt; COMPUTE_BEST_OFFER | 1 Transition   |                          | 0d 00h:00m:00.48s |
+------------------------------------------------------------------------------------------+----------------+--------------------------+-------------------+

All Interfaces Traffic:
+---------------------------+-------------------------+------------------------------------------+-------------------+
| Description               | Value                   | Last Rate                                | Last Change       |
|                           |                         | Over Last 10 Changes                     |                   |
+---------------------------+-------------------------+------------------------------------------+-------------------+
| RX IPv4 LIE Packets       | 24 Packets, 4068 Bytes  | 186.59 Packets/Sec, 31928.17 Bytes/Sec   | 0d 00h:00m:00.18s |
+---------------------------+-------------------------+------------------------------------------+-------------------+
| TX IPv4 LIE Packets       | 28 Packets, 4648 Bytes  | 171.22 Packets/Sec, 29411.68 Bytes/Sec   | 0d 00h:00m:00.19s |
+---------------------------+-------------------------+------------------------------------------+-------------------+
| RX IPv4 TIDE Packets      | 24 Packets, 13768 Bytes | 243.07 Packets/Sec, 113676.36 Bytes/Sec  | 0d 00h:00m:00.17s |
+---------------------------+-------------------------+------------------------------------------+-------------------+
| TX IPv4 TIDE Packets      | 24 Packets, 13768 Bytes | 153.11 Packets/Sec, 64389.57 Bytes/Sec   | 0d 00h:00m:00.18s |
+---------------------------+-------------------------+------------------------------------------+-------------------+
.                           .                         .                                          .                   .
.                           .                         .                                          .                   .
+---------------------------+-------------------------+------------------------------------------+-------------------+
| Total TX Packets          | 80 Packets, 23064 Bytes | 1424.91 Packets/Sec, 316330.19 Bytes/Sec | 0d 00h:00m:00.18s |
+---------------------------+-------------------------+------------------------------------------+-------------------+

All Interfaces Security:
+----------------------------------+-------------------------+-----------------------------------------+-------------------+
| Description                      | Value                   | Last Rate                               | Last Change       |
|                                  |                         | Over Last 10 Changes                    |                   |
+----------------------------------+-------------------------+-----------------------------------------+-------------------+
| Empty outer fingerprint accepted | 72 Packets, 21904 Bytes | 987.36 Packets/Sec, 317929.82 Bytes/Sec | 0d 00h:00m:00.17s |
+----------------------------------+-------------------------+-----------------------------------------+-------------------+

All Interface LIE FSMs:
+---------------------------------------------------------+----------------+-------------------------+-------------------+
| Description                                             | Value          | Last Rate               | Last Change       |
|                                                         |                | Over Last 10 Changes    |                   |
+---------------------------------------------------------+----------------+-------------------------+-------------------+
| Events TIMER_TICK                                       | 28 Events      | 171.22 Events/Sec       | 0d 00h:00m:00.19s |
+---------------------------------------------------------+----------------+-------------------------+-------------------+
| Events LIE_RECEIVED                                     | 48 Events      | 6286.22 Events/Sec      | 0d 00h:00m:00.17s |
+---------------------------------------------------------+----------------+-------------------------+-------------------+
| Events SEND_LIE                                         | 28 Events      | 171.22 Events/Sec       | 0d 00h:00m:00.19s |
+---------------------------------------------------------+----------------+-------------------------+-------------------+
| Transitions ONE_WAY -&gt; ONE_WAY                          | 8 Transitions  | 107.86 Transitions/Sec  | 0d 00h:00m:00.25s |
+---------------------------------------------------------+----------------+-------------------------+-------------------+
.                                                         .                .                         .                   .
.                                                         .                .                         .                   .
+---------------------------------------------------------+----------------+-------------------------+-------------------+
| Event-Transitions THREE_WAY -[SEND_LIE]-&gt; THREE_WAY     | 24 Transitions | 171.21 Transitions/Sec  | 0d 00h:00m:00.19s |
+---------------------------------------------------------+----------------+-------------------------+-------------------+
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
| 0.0.0.0/0     | if_101_1 172.31.22.163    |
+---------------+---------------------------+
| 1.1.1.0/24    | if_101_1001 172.31.22.163 |
+---------------+---------------------------+
| 1.1.2.0/24    | if_101_1001 172.31.22.163 |
+---------------+---------------------------+
| 1.1.3.0/24    | if_101_1001 172.31.22.163 |
+---------------+---------------------------+
.               .                           .
.               .                           .
+---------------+---------------------------+
| 99.99.99.0/24 | if_101_1001 172.31.22.163 |
|               | if_101_1002 172.31.22.163 |
+---------------+---------------------------+

IPv6 Routes:
+--------+----------------------------------+
| Prefix | Next-hops                        |
+--------+----------------------------------+
| ::/0   | if_101_1 fe80::1b:a5ff:fef5:ab56 |
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
| 0.0.0.0/0     | if_101_1 172.31.22.163    |
+---------------+---------------------------+
| 1.1.1.0/24    | if_101_1001 172.31.22.163 |
+---------------+---------------------------+
| 1.1.2.0/24    | if_101_1001 172.31.22.163 |
+---------------+---------------------------+
| 1.1.3.0/24    | if_101_1001 172.31.22.163 |
+---------------+---------------------------+
.               .                           .
.               .                           .
+---------------+---------------------------+
| 99.99.99.0/24 | if_101_1001 172.31.22.163 |
|               | if_101_1002 172.31.22.163 |
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
| ::/0   | if_101_1 fe80::1b:a5ff:fef5:ab56 |
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
| Physical Interface Name              | eth0                                                     |
| Advertised Name                      | agg_101:if_101_1                                         |
| Interface IPv4 Address               | 172.31.22.163                                            |
| Interface IPv6 Address               | fe80::1b:a5ff:fef5:ab56%eth0                             |
| Interface Index                      | 2                                                        |
| Metric                               | 1                                                        |
| LIE Receive IPv4 Multicast Address   | 224.0.0.81                                               |
| LIE Receive IPv6 Multicast Address   | FF02::A1F7                                               |
| LIE Receive Port                     | 20001                                                    |
| LIE Transmit IPv4 Multicast Address  | 224.0.0.71                                               |
| LIE Transmit IPv6 Multicast Address  | FF02::A1F7                                               |
| LIE Transmit Port                    | 20002                                                    |
| Flooding Receive Port                | 20004                                                    |
| System ID                            | 101                                                      |
| Local ID                             | 1                                                        |
| MTU                                  | 1400                                                     |
| POD                                  | 0                                                        |
| Failure                              | ok                                                       |
| State                                | THREE_WAY                                                |
| Time in State                        | 0d 00h:00m:10.07s                                        |
| Flaps                                | 0                                                        |
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
| IPv4 Address           | 172.31.22.163                |
| IPv6 Address           | fe80::1b:a5ff:fef5:ab56%eth0 |
| LIE UDP Source Port    | 45969                        |
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
+----------+----------+----------+----------+------------+---------+---------+---------------------+-------------------------+-----------+----------+
| Sequence | Time     | Time     | Queue    | Processing | Verbose | From    | Event               | Actions and             | To        | Implicit |
| Nr       | Since    | Since    | Time     | Time       | Skipped | State   |                     | Pushed Events           | State     |          |
|          | First    | Prev     |          |            |         |         |                     |                         |           |          |
+----------+----------+----------+----------+------------+---------+---------+---------------------+-------------------------+-----------+----------+
| 215      | 1.034668 | 0.001439 | 0.000099 | 0.006193   | 2       | TWO_WAY | VALID_REFLECTION    | increase_tx_nonce_local | THREE_WAY | False    |
|          |          |          |          |            |         |         |                     | start_flooding          |           |          |
|          |          |          |          |            |         |         |                     | init_partially_conn     |           |          |
+----------+----------+----------+----------+------------+---------+---------+---------------------+-------------------------+-----------+----------+
| 212      | 1.033229 | 0.873667 | 0.000080 | 0.000097   | 3       | ONE_WAY | NEW_NEIGHBOR        | SEND_LIE                | TWO_WAY   | False    |
|          |          |          |          |            |         |         |                     | increase_tx_nonce_local |           |          |
+----------+----------+----------+----------+------------+---------+---------+---------------------+-------------------------+-----------+----------+
| 68       | 0.159562 | 0.000450 | 0.000071 | 0.000008   | 1       | ONE_WAY | UNACCEPTABLE_HEADER |                         | ONE_WAY   | False    |
+----------+----------+----------+----------+------------+---------+---------+---------------------+-------------------------+-----------+----------+
| 66       | 0.159113 | 0.159113 | 0.000157 | 0.000008   | 1       | ONE_WAY | UNACCEPTABLE_HEADER |                         | ONE_WAY   | False    |
+----------+----------+----------+----------+------------+---------+---------+---------------------+-------------------------+-----------+----------+
| 9        | 0.000000 |          | 0.000000 | 0.000828   | 0       | None    | None                | cleanup                 | ONE_WAY   | False    |
|          |          |          |          |            |         |         |                     | send_lie                |           |          |
+----------+----------+----------+----------+------------+---------+---------+---------------------+-------------------------+-----------+----------+
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
+----------+-----------+----------+----------+------------+-----------+---------------------+-------------------------+-----------+----------+
| Sequence | Time      | Time     | Queue    | Processing | From      | Event               | Actions and             | To        | Implicit |
| Nr       | Since     | Since    | Time     | Time       | State     |                     | Pushed Events           | State     |          |
|          | First     | Prev     |          |            |           |                     |                         |           |          |
+----------+-----------+----------+----------+------------+-----------+---------------------+-------------------------+-----------+----------+
| 1958     | 11.087379 | 0.000159 | 0.000283 | 0.000061   | THREE_WAY | LIE_RECEIVED        | process_lie             | None      | False    |
+----------+-----------+----------+----------+------------+-----------+---------------------+-------------------------+-----------+----------+
| 1957     | 11.087220 | 0.086946 | 0.000695 | 0.000077   | THREE_WAY | LIE_RECEIVED        | process_lie             | None      | False    |
+----------+-----------+----------+----------+------------+-----------+---------------------+-------------------------+-----------+----------+
| 1884     | 11.000275 | 0.000106 | 0.000083 | 0.000861   | THREE_WAY | SEND_LIE            | send_lie                | None      | False    |
+----------+-----------+----------+----------+------------+-----------+---------------------+-------------------------+-----------+----------+
| 1883     | 11.000169 | 0.866544 | 0.000068 | 0.000020   | THREE_WAY | TIMER_TICK          | check_hold_time_expired | None      | False    |
|          |           |          |          |            |           |                     | SEND_LIE                |           |          |
+----------+-----------+----------+----------+------------+-----------+---------------------+-------------------------+-----------+----------+
.          .           .          .          .            .           .                     .                         .           .          .
.          .           .          .          .            .           .                     .                         .           .          .
+----------+-----------+----------+----------+------------+-----------+---------------------+-------------------------+-----------+----------+
| 9        | 0.000000  |          | 0.000000 | 0.000828   | None      | None                | cleanup                 | ONE_WAY   | False    |
|          |           |          |          |            |           |                     | send_lie                |           |          |
+----------+-----------+----------+----------+------------+-----------+---------------------+-------------------------+-----------+----------+
</pre>
<!-- OUTPUT-END -->

### show interface <i>interface</i> packets

The "<b>show interface</b> <i>interface</i> <b>packets</b>" command shows a fully decoded trace
of the 20 most recently sent and received RIFT packets on the interface.

Example:

<!-- OUTPUT-START: agg_101> show interface if_101_1 packets -->
<pre>
agg_101> <b>show interface if_101_1 packets</b>
Last 20 Packets Sent and Received on Interface:
+-----------------------------------------------------------------------------------------------------------------------------------+
| direction=TX  timestamp=2020-07-06-15:16:42.859717                                                                                |
| local-address=fe80::1b:a5ff:fef5:ab56%eth0:60659  remote_address=ff02::a1f7%eth0:20002                                            |
|                                                                                                                                   |
| packet-nr=13 outer-key-id=0 nonce-local=57459 nonce-remote=55263 remaining-lie-lifetime=all-ones outer-fingerprint-len=0          |
| protocol-packet=ProtocolPacket(content=PacketContent(lie=LIEPacket(link_mtu_size=1400, name='agg_101:if_101_1',                   |
| neighbor=Neighbor(originator=1, remote_id=1), link_bandwidth=100, not_a_ztp_offer=True, link_capabilities=None, flood_port=20004, |
| label=None, instance_name=None, local_id=1, you_are_flood_repeater=False, you_are_sending_too_quickly=False,                      |
| node_capabilities=NodeCapabilities(hierarchy_indications=1, flood_reduction=True, protocol_minor_version=0), holdtime=3, pod=0),  |
| tide=None, tie=None, tire=None), header=PacketHeader(level=23, sender=101, major_version=2, minor_version=0))                     |
+-----------------------------------------------------------------------------------------------------------------------------------+
| direction=TX  timestamp=2020-07-06-15:16:42.859558  seconds-since-prev=0.0002                                                     |
| local-address=172.31.22.163:59716  remote_address=224.0.0.71:20002                                                                |
|                                                                                                                                   |
| packet-nr=13 outer-key-id=0 nonce-local=57459 nonce-remote=55263 remaining-lie-lifetime=all-ones outer-fingerprint-len=0          |
| protocol-packet=ProtocolPacket(content=PacketContent(lie=LIEPacket(link_mtu_size=1400, name='agg_101:if_101_1',                   |
| neighbor=Neighbor(originator=1, remote_id=1), link_bandwidth=100, not_a_ztp_offer=True, link_capabilities=None, flood_port=20004, |
| label=None, instance_name=None, local_id=1, you_are_flood_repeater=False, you_are_sending_too_quickly=False,                      |
| node_capabilities=NodeCapabilities(hierarchy_indications=1, flood_reduction=True, protocol_minor_version=0), holdtime=3, pod=0),  |
| tide=None, tie=None, tire=None), header=PacketHeader(level=23, sender=101, major_version=2, minor_version=0))                     |
+-----------------------------------------------------------------------------------------------------------------------------------+
| direction=RX  timestamp=2020-07-06-15:16:42.841845  seconds-since-prev=0.0177                                                     |
| local-address=ff02::a1f7%eth0:20001  remote_address=fe80::1b:a5ff:fef5:ab56%eth0:45969                                            |
|                                                                                                                                   |
| packet-nr=13 outer-key-id=0 nonce-local=55263 nonce-remote=57459 remaining-lie-lifetime=all-ones outer-fingerprint-len=0          |
| protocol-packet=ProtocolPacket(content=PacketContent(lie=LIEPacket(link_mtu_size=1400, name='core_1:if_1_101',                    |
| neighbor=Neighbor(originator=101, remote_id=1), link_bandwidth=100, not_a_ztp_offer=False, link_capabilities=None,                |
| flood_port=20003, label=None, instance_name=None, local_id=1, you_are_flood_repeater=False, you_are_sending_too_quickly=False,    |
| node_capabilities=NodeCapabilities(hierarchy_indications=1, flood_reduction=True, protocol_minor_version=0), holdtime=3, pod=0),  |
| tide=None, tie=None, tire=None), header=PacketHeader(level=24, sender=1, major_version=2, minor_version=0))                       |
+-----------------------------------------------------------------------------------------------------------------------------------+
| direction=RX  timestamp=2020-07-06-15:16:42.841274  seconds-since-prev=0.0006                                                     |
| local-address=224.0.0.81:20001  remote_address=172.31.22.163:39540                                                                |
|                                                                                                                                   |
| packet-nr=13 outer-key-id=0 nonce-local=55263 nonce-remote=57459 remaining-lie-lifetime=all-ones outer-fingerprint-len=0          |
| protocol-packet=ProtocolPacket(content=PacketContent(lie=LIEPacket(link_mtu_size=1400, name='core_1:if_1_101',                    |
| neighbor=Neighbor(originator=101, remote_id=1), link_bandwidth=100, not_a_ztp_offer=False, link_capabilities=None,                |
| flood_port=20003, label=None, instance_name=None, local_id=1, you_are_flood_repeater=False, you_are_sending_too_quickly=False,    |
| node_capabilities=NodeCapabilities(hierarchy_indications=1, flood_reduction=True, protocol_minor_version=0), holdtime=3, pod=0),  |
| tide=None, tie=None, tire=None), header=PacketHeader(level=24, sender=1, major_version=2, minor_version=0))                       |
+-----------------------------------------------------------------------------------------------------------------------------------+
| direction=RX  timestamp=2020-07-06-15:16:41.914891  seconds-since-prev=0.9264                                                     |
| local-address=172.31.22.163:20004  remote_address=172.31.22.163:46215                                                             |
|                                                                                                                                   |
| packet-nr=6 outer-key-id=0 nonce-local=55263 nonce-remote=57459 remaining-lie-lifetime=all-ones outer-fingerprint-len=0           |
| protocol-packet=ProtocolPacket(content=PacketContent(lie=None,                                                                    |
| tide=TIDEPacket(headers=[TIEHeaderWithLifeTime(remaining_lifetime=604791, header=TIEHeader(seq_nr=5, tieid=TIEID(originator=1,    |
| tie_nr=1, direction=1, tietype=2), origination_lifetime=None, origination_time=None)),                                            |
| TIEHeaderWithLifeTime(remaining_lifetime=604791, header=TIEHeader(seq_nr=1, tieid=TIEID(originator=1, tie_nr=2, direction=1,      |
| tietype=3), origination_lifetime=None, origination_time=None)), TIEHeaderWithLifeTime(remaining_lifetime=604791,                  |
| header=TIEHeader(seq_nr=0, tieid=TIEID(originator=1, tie_nr=1, direction=2, tietype=2), origination_lifetime=None,                |
| origination_time=None)), TIEHeaderWithLifeTime(remaining_lifetime=604791, header=TIEHeader(seq_nr=4, tieid=TIEID(originator=101,  |
| tie_nr=1, direction=2, tietype=2), origination_lifetime=None, origination_time=None)),                                            |
| TIEHeaderWithLifeTime(remaining_lifetime=604791, header=TIEHeader(seq_nr=0, tieid=TIEID(originator=102, tie_nr=1, direction=2,    |
| tietype=2), origination_lifetime=None, origination_time=None)), TIEHeaderWithLifeTime(remaining_lifetime=604791,                  |
| header=TIEHeader(seq_nr=0, tieid=TIEID(originator=201, tie_nr=1, direction=2, tietype=2), origination_lifetime=None,              |
| origination_time=None)), TIEHeaderWithLifeTime(remaining_lifetime=604791, header=TIEHeader(seq_nr=0, tieid=TIEID(originator=202,  |
| tie_nr=1, direction=2, tietype=2), origination_lifetime=None, origination_time=None)),                                            |
| TIEHeaderWithLifeTime(remaining_lifetime=604792, header=TIEHeader(seq_nr=3, tieid=TIEID(originator=1001, tie_nr=1, direction=2,   |
| tietype=2), origination_lifetime=None, origination_time=None)), TIEHeaderWithLifeTime(remaining_lifetime=604791,                  |
| header=TIEHeader(seq_nr=1, tieid=TIEID(originator=1001, tie_nr=2, direction=2, tietype=3), origination_lifetime=None,             |
| origination_time=None)), TIEHeaderWithLifeTime(remaining_lifetime=604792, header=TIEHeader(seq_nr=3, tieid=TIEID(originator=1002, |
| tie_nr=1, direction=2, tietype=2), origination_lifetime=None, origination_time=None)),                                            |
| TIEHeaderWithLifeTime(remaining_lifetime=604791, header=TIEHeader(seq_nr=1, tieid=TIEID(originator=1002, tie_nr=2, direction=2,   |
| tietype=3), origination_lifetime=None, origination_time=None)), TIEHeaderWithLifeTime(remaining_lifetime=604792,                  |
| header=TIEHeader(seq_nr=0, tieid=TIEID(originator=2001, tie_nr=1, direction=2, tietype=2), origination_lifetime=None,             |
| origination_time=None)), TIEHeaderWithLifeTime(remaining_lifetime=604791, header=TIEHeader(seq_nr=0, tieid=TIEID(originator=2001, |
| tie_nr=2, direction=2, tietype=3), origination_lifetime=None, origination_time=None)),                                            |
| TIEHeaderWithLifeTime(remaining_lifetime=604792, header=TIEHeader(seq_nr=0, tieid=TIEID(originator=2002, tie_nr=1, direction=2,   |
| tietype=2), origination_lifetime=None, origination_time=None)), TIEHeaderWithLifeTime(remaining_lifetime=604791,                  |
| header=TIEHeader(seq_nr=0, tieid=TIEID(originator=2002, tie_nr=2, direction=2, tietype=3), origination_lifetime=None,             |
| origination_time=None))], end_range=TIEID(originator=18446744073709551615, tie_nr=4294967295, direction=2, tietype=7),            |
| start_range=TIEID(originator=0, tie_nr=0, direction=1, tietype=2)), tie=None, tire=None), header=PacketHeader(level=24, sender=1, |
| major_version=2, minor_version=0))                                                                                                |
+-----------------------------------------------------------------------------------------------------------------------------------+
.                                                                                                                                   .
.                                                                                                                                   .
+-----------------------------------------------------------------------------------------------------------------------------------+
| direction=RX  timestamp=2020-07-06-15:16:39.825046  seconds-since-prev=0.0006                                                     |
| local-address=224.0.0.81:20001  remote_address=172.31.22.163:39540                                                                |
|                                                                                                                                   |
| packet-nr=10 outer-key-id=0 nonce-local=55263 nonce-remote=57459 remaining-lie-lifetime=all-ones outer-fingerprint-len=0          |
| protocol-packet=ProtocolPacket(content=PacketContent(lie=LIEPacket(link_mtu_size=1400, name='core_1:if_1_101',                    |
| neighbor=Neighbor(originator=101, remote_id=1), link_bandwidth=100, not_a_ztp_offer=False, link_capabilities=None,                |
| flood_port=20003, label=None, instance_name=None, local_id=1, you_are_flood_repeater=False, you_are_sending_too_quickly=False,    |
| node_capabilities=NodeCapabilities(hierarchy_indications=1, flood_reduction=True, protocol_minor_version=0), holdtime=3, pod=0),  |
| tide=None, tie=None, tire=None), header=PacketHeader(level=24, sender=1, major_version=2, minor_version=0))                       |
+-----------------------------------------------------------------------------------------------------------------------------------+
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
+-----------+------------+------+--------+--------+-------+
| Direction | Originator | Type | TIE Nr | Seq Nr | Send  |
|           |            |      |        |        | Delay |
+-----------+------------+------+--------+--------+-------+

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
| Last Received LIE Nonce  | 55263          |
+--------------------------+----------------+
| Last Sent Nonce          | 57459          |
+--------------------------+----------------+
| Next Sent Nonce Increase | 48.378901 secs |
+--------------------------+----------------+

Security Statistics:
+------------------------------------------------+------------------------+--------------------------------------+-------------------+
| Description                                    | Value                  | Last Rate                            | Last Change       |
|                                                |                        | Over Last 10 Changes                 |                   |
+------------------------------------------------+------------------------+--------------------------------------+-------------------+
| Missing outer security envelope                | 0 Packets, 0 Bytes     |                                      |                   |
+------------------------------------------------+------------------------+--------------------------------------+-------------------+
| Zero outer key id not accepted                 | 0 Packets, 0 Bytes     |                                      |                   |
+------------------------------------------------+------------------------+--------------------------------------+-------------------+
| Non-zero outer key id not accepted             | 0 Packets, 0 Bytes     |                                      |                   |
+------------------------------------------------+------------------------+--------------------------------------+-------------------+
| Incorrect outer fingerprint                    | 0 Packets, 0 Bytes     |                                      |                   |
+------------------------------------------------+------------------------+--------------------------------------+-------------------+
.                                                .                        .                                      .                   .
.                                                .                        .                                      .                   .
+------------------------------------------------+------------------------+--------------------------------------+-------------------+
| Empty origin fingerprint accepted              | 3 Packets, 844 Bytes   | 11.77 Packets/Sec, 3212.29 Bytes/Sec | 0d 00h:00m:10.20s |
+------------------------------------------------+------------------------+--------------------------------------+-------------------+
</pre>
<!-- OUTPUT-END -->

### show interface <i>interface</i> sockets

The "<b>show interface</b> <i>interface</i> <b>sockets</b>" command shows the sockets that the 
current node has opened for sending and receiving packets.

Example:

<!-- OUTPUT-START: agg_101> show interface if_101_1 sockets -->
<pre>
agg_101> <b>show interface if_101_1 sockets</b>
+----------+-----------+--------+------------------------------+------------+-----------------+-------------+
| Traffic  | Direction | Family | Local Address                | Local Port | Remote Address  | Remote Port |
+----------+-----------+--------+------------------------------+------------+-----------------+-------------+
| LIEs     | Receive   | IPv4   | 224.0.0.81                   | 20001      | Any             | Any         |
+----------+-----------+--------+------------------------------+------------+-----------------+-------------+
| LIEs     | Receive   | IPv6   | ff02::a1f7%eth0              | 20001      | Any             | Any         |
+----------+-----------+--------+------------------------------+------------+-----------------+-------------+
| LIEs     | Send      | IPv4   | 172.31.22.163                | 59716      | 224.0.0.71      | 20002       |
+----------+-----------+--------+------------------------------+------------+-----------------+-------------+
| LIEs     | Send      | IPv6   | fe80::1b:a5ff:fef5:ab56%eth0 | 60659      | ff02::a1f7%eth0 | 20002       |
+----------+-----------+--------+------------------------------+------------+-----------------+-------------+
.          .           .        .                              .            .                 .             .
.          .           .        .                              .            .                 .             .
+----------+-----------+--------+------------------------------+------------+-----------------+-------------+
| Flooding | Send      | IPv4   | 172.31.22.163                | 53273      | 172.31.22.163   | 20003       |
+----------+-----------+--------+------------------------------+------------+-----------------+-------------+
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
| RX IPv4 LIE Packets       | 2 Packets, 332 Bytes  | 1.07 Packets/Sec, 177.22 Bytes/Sec  | 0d 00h:00m:00.85s |
+---------------------------+-----------------------+-------------------------------------+-------------------+
| TX IPv4 LIE Packets       | 2 Packets, 334 Bytes  | 1.03 Packets/Sec, 171.93 Bytes/Sec  | 0d 00h:00m:00.83s |
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
+------------------------------------------------+------------------------+--------------------------------------+-------------------+
| Description                                    | Value                  | Last Rate                            | Last Change       |
|                                                |                        | Over Last 10 Changes                 |                   |
+------------------------------------------------+------------------------+--------------------------------------+-------------------+
| Missing outer security envelope                | 0 Packets, 0 Bytes     |                                      |                   |
+------------------------------------------------+------------------------+--------------------------------------+-------------------+
| Zero outer key id not accepted                 | 0 Packets, 0 Bytes     |                                      |                   |
+------------------------------------------------+------------------------+--------------------------------------+-------------------+
| Non-zero outer key id not accepted             | 0 Packets, 0 Bytes     |                                      |                   |
+------------------------------------------------+------------------------+--------------------------------------+-------------------+
| Incorrect outer fingerprint                    | 0 Packets, 0 Bytes     |                                      |                   |
+------------------------------------------------+------------------------+--------------------------------------+-------------------+
.                                                .                        .                                      .                   .
.                                                .                        .                                      .                   .
+------------------------------------------------+------------------------+--------------------------------------+-------------------+
| Empty origin fingerprint accepted              | 3 Packets, 844 Bytes   | 11.77 Packets/Sec, 3212.29 Bytes/Sec | 0d 00h:00m:10.41s |
+------------------------------------------------+------------------------+--------------------------------------+-------------------+

LIE FSM:
+------------------------------------------------------------+---------------+----------------------+-------------------+
| Description                                                | Value         | Last Rate            | Last Change       |
|                                                            |               | Over Last 10 Changes |                   |
+------------------------------------------------------------+---------------+----------------------+-------------------+
| Enter ONE_WAY                                              | 0 Entries     |                      |                   |
+------------------------------------------------------------+---------------+----------------------+-------------------+
| Enter THREE_WAY                                            | 0 Entries     |                      |                   |
+------------------------------------------------------------+---------------+----------------------+-------------------+
| Enter TWO_WAY                                              | 0 Entries     |                      |                   |
+------------------------------------------------------------+---------------+----------------------+-------------------+
| Event-Transitions None -[None]-&gt; ONE_WAY                   | 0 Transitions |                      |                   |
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
| RX IPv4 LIE Packets       | 2 Packets, 332 Bytes  | 1.07 Packets/Sec, 177.22 Bytes/Sec  | 0d 00h:00m:00.96s |
+---------------------------+-----------------------+-------------------------------------+-------------------+
| TX IPv4 LIE Packets       | 2 Packets, 334 Bytes  | 1.03 Packets/Sec, 171.93 Bytes/Sec  | 0d 00h:00m:00.94s |
+---------------------------+-----------------------+-------------------------------------+-------------------+
| RX IPv4 TIDE Packets      | 1 Packet, 927 Bytes   |                                     | 0d 00h:00m:01.88s |
+---------------------------+-----------------------+-------------------------------------+-------------------+
| TX IPv4 TIDE Packets      | 1 Packet, 503 Bytes   |                                     | 0d 00h:00m:01.91s |
+---------------------------+-----------------------+-------------------------------------+-------------------+
.                           .                       .                                     .                   .
.                           .                       .                                     .                   .
+---------------------------+-----------------------+-------------------------------------+-------------------+
| Total TX Packets          | 5 Packets, 1171 Bytes | 4.12 Packets/Sec, 1033.45 Bytes/Sec | 0d 00h:00m:00.94s |
+---------------------------+-----------------------+-------------------------------------+-------------------+

Security:
+-----------------------------------+------------------------+--------------------------------------+-------------------+
| Description                       | Value                  | Last Rate                            | Last Change       |
|                                   |                        | Over Last 10 Changes                 |                   |
+-----------------------------------+------------------------+--------------------------------------+-------------------+
| Empty outer fingerprint accepted  | 36 Packets, 9572 Bytes | 2.98 Packets/Sec, 999.73 Bytes/Sec   | 0d 00h:00m:00.96s |
+-----------------------------------+------------------------+--------------------------------------+-------------------+
| Empty origin fingerprint accepted | 3 Packets, 844 Bytes   | 11.77 Packets/Sec, 3212.29 Bytes/Sec | 0d 00h:00m:10.52s |
+-----------------------------------+------------------------+--------------------------------------+-------------------+

LIE FSM:
+---------------------------------------------------------+---------------+----------------------+-------------------+
| Description                                             | Value         | Last Rate            | Last Change       |
|                                                         |               | Over Last 10 Changes |                   |
+---------------------------------------------------------+---------------+----------------------+-------------------+
| Event-Transitions THREE_WAY -[LIE_RECEIVED]-&gt; THREE_WAY | 4 Transitions | 3.28 Transitions/Sec | 0d 00h:00m:00.96s |
+---------------------------------------------------------+---------------+----------------------+-------------------+
| Event-Transitions THREE_WAY -[SEND_LIE]-&gt; THREE_WAY     | 2 Transitions | 1.03 Transitions/Sec | 0d 00h:00m:00.94s |
+---------------------------------------------------------+---------------+----------------------+-------------------+
| Event-Transitions THREE_WAY -[TIMER_TICK]-&gt; THREE_WAY   | 2 Transitions | 1.03 Transitions/Sec | 0d 00h:00m:00.95s |
+---------------------------------------------------------+---------------+----------------------+-------------------+
| Events LIE_RECEIVED                                     | 4 Events      | 3.28 Events/Sec      | 0d 00h:00m:00.96s |
+---------------------------------------------------------+---------------+----------------------+-------------------+
.                                                         .               .                      .                   .
.                                                         .               .                      .                   .
+---------------------------------------------------------+---------------+----------------------+-------------------+
| Transitions THREE_WAY -&gt; THREE_WAY                      | 8 Transitions | 7.20 Transitions/Sec | 0d 00h:00m:00.94s |
+---------------------------------------------------------+---------------+----------------------+-------------------+
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
+-------------+-----------------------+-----------+-----------+-------------------+-------+
| Interface   | Neighbor              | Neighbor  | Neighbor  | Time in           | Flaps |
| Name        | Name                  | System ID | State     | State             |       |
+-------------+-----------------------+-----------+-----------+-------------------+-------+
| if_101_1    | core_1:if_1_101       | 1         | THREE_WAY | 0d 00h:00m:11.19s | 0     |
+-------------+-----------------------+-----------+-----------+-------------------+-------+
| if_101_1001 | edge_1001:if_1001_101 | 1001      | THREE_WAY | 0d 00h:00m:11.16s | 0     |
+-------------+-----------------------+-----------+-----------+-------------------+-------+
| if_101_1002 | edge_1002:if_1002_101 | 1002      | THREE_WAY | 0d 00h:00m:11.15s | 0     |
+-------------+-----------------------+-----------+-----------+-------------------+-------+
| if_101_2    |                       |           | ONE_WAY   | 0d 00h:00m:12.20s | 0     |
+-------------+-----------------------+-----------+-----------+-------------------+-------+
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
| eth0      | 172.31.22.163           | 172.31.22.163 | 172.31.31.255 |         |
+-----------+-------------------------+---------------+---------------+---------+
|           | ::1                     |               |               |         |
+-----------+-------------------------+---------------+---------------+---------+
|           | fe80::1b:a5ff:fef5:ab56 |               |               |         |
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
| eth0      | 2         | 02:1b:a5:f5:ab:56 | ff:ff:ff:ff:ff:ff |           | 9001  | UP        |
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
+-------------+---------+-----------------------------+-------------+----------+-----------+-------------+--------+
| Table       | Address | Destination                 | Type        | Protocol | Outgoing  | Gateway     | Weight |
|             | Family  |                             |             |          | Interface |             |        |
+-------------+---------+-----------------------------+-------------+----------+-----------+-------------+--------+
| Unspecified | IPv6    | ::/0                        | Unreachable | Kernel   | lo        |             |        |
+-------------+---------+-----------------------------+-------------+----------+-----------+-------------+--------+
| Unspecified | IPv6    | ::/0                        | Unreachable | Kernel   | lo        |             |        |
+-------------+---------+-----------------------------+-------------+----------+-----------+-------------+--------+
| Main        | IPv4    | 0.0.0.0/0                   | Unicast     | Boot     | eth0      | 172.31.16.1 |        |
+-------------+---------+-----------------------------+-------------+----------+-----------+-------------+--------+
| Main        | IPv4    | 172.31.16.0/20              | Unicast     | Kernel   | eth0      |             |        |
+-------------+---------+-----------------------------+-------------+----------+-----------+-------------+--------+
.             .         .                             .             .          .           .             .        .
.             .         .                             .             .          .           .             .        .
+-------------+---------+-----------------------------+-------------+----------+-----------+-------------+--------+
| Local       | IPv6    | ff00::/8                    | Unicast     | Boot     | eth0      |             |        |
+-------------+---------+-----------------------------+-------------+----------+-----------+-------------+--------+
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
+-------+---------+----------------+---------+----------+-----------+-------------+--------+
| Table | Address | Destination    | Type    | Protocol | Outgoing  | Gateway     | Weight |
|       | Family  |                |         |          | Interface |             |        |
+-------+---------+----------------+---------+----------+-----------+-------------+--------+
| Main  | IPv4    | 0.0.0.0/0      | Unicast | Boot     | eth0      | 172.31.16.1 |        |
+-------+---------+----------------+---------+----------+-----------+-------------+--------+
| Main  | IPv4    | 172.31.16.0/20 | Unicast | Kernel   | eth0      |             |        |
+-------+---------+----------------+---------+----------+-----------+-------------+--------+
| Main  | IPv6    | fe80::/64      | Unicast | Kernel   | eth0      |             |        |
+-------+---------+----------------+---------+----------+-----------+-------------+--------+
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
| Receive LIE IPv6 Multicast Address    | FF02::A1F7       |
| Transmit LIE IPv6 Multicast Address   | FF02::A1F7       |
| Receive LIE Port                      | 20102            |
| Transmit LIE Port                     | 10000            |
| LIE Send Interval                     | 1.0 secs         |
| Receive TIE Port                      | 10001            |
| Kernel Route Table                    | 3                |
| Originating South-bound Default Route | False            |
| Flooding Reduction Enabled            | True             |
| Flooding Reduction Redundancy         | 2                |
| Flooding Reduction Similarity         | 2                |
| Flooding Reduction Node Random        | 20812            |
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
+----------+----------+----------+----------+------------+---------+--------------------+-------------------------------+----------------------+--------------------+----------+
| Sequence | Time     | Time     | Queue    | Processing | Verbose | From               | Event                         | Actions and          | To                 | Implicit |
| Nr       | Since    | Since    | Time     | Time       | Skipped | State              |                               | Pushed Events        | State              |          |
|          | First    | Prev     |          |            |         |                    |                               |                      |                    |          |
+----------+----------+----------+----------+------------+---------+--------------------+-------------------------------+----------------------+--------------------+----------+
| 1698     | 9.841496 | 0.000819 | 0.000708 | 0.000052   | 0       | COMPUTE_BEST_OFFER | COMPUTATION_DONE              | update_all_lie_fsms  | UPDATING_CLIENTS   | False    |
+----------+----------+----------+----------+------------+---------+--------------------+-------------------------------+----------------------+--------------------+----------+
| 1697     | 9.840677 | 7.887902 | 0.000366 | 0.000106   | 47      | UPDATING_CLIENTS   | CHANGE_LOCAL_CONFIGURED_LEVEL | store_level          | COMPUTE_BEST_OFFER | False    |
|          |          |          |          |            |         |                    |                               | stop_hold_down_timer |                    |          |
|          |          |          |          |            |         |                    |                               | level_compute        |                    |          |
|          |          |          |          |            |         |                    |                               | COMPUTATION_DONE     |                    |          |
+----------+----------+----------+----------+------------+---------+--------------------+-------------------------------+----------------------+--------------------+----------+
| 479      | 1.952774 | 0.000435 | 0.000334 | 0.000042   | 0       | COMPUTE_BEST_OFFER | COMPUTATION_DONE              | update_all_lie_fsms  | UPDATING_CLIENTS   | False    |
+----------+----------+----------+----------+------------+---------+--------------------+-------------------------------+----------------------+--------------------+----------+
| 478      | 1.952340 | 0.998246 | 0.000069 | 0.000087   | 12      | UPDATING_CLIENTS   | BETTER_HAT                    | stop_hold_down_timer | COMPUTE_BEST_OFFER | False    |
|          |          |          |          |            |         |                    |                               | level_compute        |                    |          |
|          |          |          |          |            |         |                    |                               | COMPUTATION_DONE     |                    |          |
+----------+----------+----------+----------+------------+---------+--------------------+-------------------------------+----------------------+--------------------+----------+
.          .          .          .          .            .         .                    .                               .                      .                    .          .
.          .          .          .          .            .         .                    .                               .                      .                    .          .
+----------+----------+----------+----------+------------+---------+--------------------+-------------------------------+----------------------+--------------------+----------+
| 11       | 0.000000 |          | 0.000000 | 0.000064   | 0       | None               | None                          | stop_hold_down_timer | COMPUTE_BEST_OFFER | False    |
|          |          |          |          |            |         |                    |                               | level_compute        |                    |          |
|          |          |          |          |            |         |                    |                               | COMPUTATION_DONE     |                    |          |
+----------+----------+----------+----------+------------+---------+--------------------+-------------------------------+----------------------+--------------------+----------+
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
+----------+-----------+----------+----------+------------+--------------------+-------------------------------+------------------------+--------------------+----------+
| Sequence | Time      | Time     | Queue    | Processing | From               | Event                         | Actions and            | To                 | Implicit |
| Nr       | Since     | Since    | Time     | Time       | State              |                               | Pushed Events          | State              |          |
|          | First     | Prev     |          |            |                    |                               |                        |                    |          |
+----------+-----------+----------+----------+------------+--------------------+-------------------------------+------------------------+--------------------+----------+
| 2188     | 13.007601 | 0.000081 | 0.001620 | 0.000013   | UPDATING_CLIENTS   | NEIGHBOR_OFFER                | update_or_remove_offer | None               | False    |
+----------+-----------+----------+----------+------------+--------------------+-------------------------------+------------------------+--------------------+----------+
| 2187     | 13.007520 | 0.890316 | 0.001672 | 0.000015   | UPDATING_CLIENTS   | NEIGHBOR_OFFER                | update_or_remove_offer | None               | False    |
+----------+-----------+----------+----------+------------+--------------------+-------------------------------+------------------------+--------------------+----------+
| 2122     | 12.117204 | 0.000090 | 0.001494 | 0.000014   | UPDATING_CLIENTS   | NEIGHBOR_OFFER                | update_or_remove_offer | None               | False    |
+----------+-----------+----------+----------+------------+--------------------+-------------------------------+------------------------+--------------------+----------+
| 2121     | 12.117114 | 0.000121 | 0.001544 | 0.000016   | UPDATING_CLIENTS   | NEIGHBOR_OFFER                | update_or_remove_offer | None               | False    |
+----------+-----------+----------+----------+------------+--------------------+-------------------------------+------------------------+--------------------+----------+
.          .           .          .          .            .                    .                               .                        .                    .          .
.          .           .          .          .            .                    .                               .                        .                    .          .
+----------+-----------+----------+----------+------------+--------------------+-------------------------------+------------------------+--------------------+----------+
| 11       | 0.000000  |          | 0.000000 | 0.000064   | None               | None                          | stop_hold_down_timer   | COMPUTE_BEST_OFFER | False    |
|          |           |          |          |            |                    |                               | level_compute          |                    |          |
|          |           |          |          |            |                    |                               | COMPUTATION_DONE       |                    |          |
+----------+-----------+----------+----------+------------+--------------------+-------------------------------+------------------------+--------------------+----------+
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
| Enter COMPUTE_BEST_OFFER                                                                 | 1 Entry        |                      | 0d 00h:00m:03.32s |
+------------------------------------------------------------------------------------------+----------------+----------------------+-------------------+
| Enter UPDATING_CLIENTS                                                                   | 1 Entry        |                      | 0d 00h:00m:03.31s |
+------------------------------------------------------------------------------------------+----------------+----------------------+-------------------+
| Event-Transitions COMPUTE_BEST_OFFER -[COMPUTATION_DONE]-&gt; UPDATING_CLIENTS              | 1 Transition   |                      | 0d 00h:00m:03.31s |
+------------------------------------------------------------------------------------------+----------------+----------------------+-------------------+
| Event-Transitions None -[None]-&gt; COMPUTE_BEST_OFFER                                      | 0 Transitions  |                      |                   |
+------------------------------------------------------------------------------------------+----------------+----------------------+-------------------+
.                                                                                          .                .                      .                   .
.                                                                                          .                .                      .                   .
+------------------------------------------------------------------------------------------+----------------+----------------------+-------------------+
| Transitions UPDATING_CLIENTS -&gt; UPDATING_CLIENTS                                         | 24 Transitions | 9.21 Transitions/Sec | 0d 00h:00m:00.06s |
+------------------------------------------------------------------------------------------+----------------+----------------------+-------------------+

Node Interfaces Traffic:
+---------------------------+------------------------+-------------------------------------+-------------------+
| Description               | Value                  | Last Rate                           | Last Change       |
|                           |                        | Over Last 10 Changes                |                   |
+---------------------------+------------------------+-------------------------------------+-------------------+
| RX IPv4 LIE Packets       | 12 Packets, 2040 Bytes | 3.01 Packets/Sec, 510.93 Bytes/Sec  | 0d 00h:00m:00.06s |
+---------------------------+------------------------+-------------------------------------+-------------------+
| TX IPv4 LIE Packets       | 16 Packets, 2608 Bytes | 4.49 Packets/Sec, 735.40 Bytes/Sec  | 0d 00h:00m:00.16s |
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
| Enter ONE_WAY                                              | 0 Entries      |                       |                   |
+------------------------------------------------------------+----------------+-----------------------+-------------------+
| Enter THREE_WAY                                            | 0 Entries      |                       |                   |
+------------------------------------------------------------+----------------+-----------------------+-------------------+
| Enter TWO_WAY                                              | 0 Entries      |                       |                   |
+------------------------------------------------------------+----------------+-----------------------+-------------------+
| Event-Transitions None -[None]-&gt; ONE_WAY                   | 0 Transitions  |                       |                   |
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
| Enter COMPUTE_BEST_OFFER                                                                 | 1 Entry        |                      | 0d 00h:00m:03.43s |
+------------------------------------------------------------------------------------------+----------------+----------------------+-------------------+
| Enter UPDATING_CLIENTS                                                                   | 1 Entry        |                      | 0d 00h:00m:03.43s |
+------------------------------------------------------------------------------------------+----------------+----------------------+-------------------+
| Event-Transitions COMPUTE_BEST_OFFER -[COMPUTATION_DONE]-&gt; UPDATING_CLIENTS              | 1 Transition   |                      | 0d 00h:00m:03.43s |
+------------------------------------------------------------------------------------------+----------------+----------------------+-------------------+
| Event-Transitions UPDATING_CLIENTS -[CHANGE_LOCAL_CONFIGURED_LEVEL]-&gt; COMPUTE_BEST_OFFER | 1 Transition   |                      | 0d 00h:00m:03.43s |
+------------------------------------------------------------------------------------------+----------------+----------------------+-------------------+
.                                                                                          .                .                      .                   .
.                                                                                          .                .                      .                   .
+------------------------------------------------------------------------------------------+----------------+----------------------+-------------------+
| Transitions UPDATING_CLIENTS -&gt; UPDATING_CLIENTS                                         | 24 Transitions | 9.21 Transitions/Sec | 0d 00h:00m:00.17s |
+------------------------------------------------------------------------------------------+----------------+----------------------+-------------------+

Node Interfaces Traffic:
+---------------------------+------------------------+-------------------------------------+-------------------+
| Description               | Value                  | Last Rate                           | Last Change       |
|                           |                        | Over Last 10 Changes                |                   |
+---------------------------+------------------------+-------------------------------------+-------------------+
| RX IPv4 LIE Packets       | 12 Packets, 2040 Bytes | 3.01 Packets/Sec, 510.93 Bytes/Sec  | 0d 00h:00m:00.18s |
+---------------------------+------------------------+-------------------------------------+-------------------+
| TX IPv4 LIE Packets       | 16 Packets, 2608 Bytes | 4.49 Packets/Sec, 735.40 Bytes/Sec  | 0d 00h:00m:00.27s |
+---------------------------+------------------------+-------------------------------------+-------------------+
| RX IPv4 TIDE Packets      | 6 Packets, 3442 Bytes  | 2.39 Packets/Sec, 1201.78 Bytes/Sec | 0d 00h:00m:01.14s |
+---------------------------+------------------------+-------------------------------------+-------------------+
| TX IPv4 TIDE Packets      | 6 Packets, 3442 Bytes  | 2.52 Packets/Sec, 1478.97 Bytes/Sec | 0d 00h:00m:01.26s |
+---------------------------+------------------------+-------------------------------------+-------------------+
.                           .                        .                                     .                   .
.                           .                        .                                     .                   .
+---------------------------+------------------------+-------------------------------------+-------------------+
| Total TX Packets          | 38 Packets, 8658 Bytes | 9.12 Packets/Sec, 1494.34 Bytes/Sec | 0d 00h:00m:00.27s |
+---------------------------+------------------------+-------------------------------------+-------------------+

Node Interfaces Security:
+----------------------------------+------------------------+-------------------------------------+-------------------+
| Description                      | Value                  | Last Rate                           | Last Change       |
|                                  |                        | Over Last 10 Changes                |                   |
+----------------------------------+------------------------+-------------------------------------+-------------------+
| Empty outer fingerprint accepted | 30 Packets, 7522 Bytes | 9.08 Packets/Sec, 2002.71 Bytes/Sec | 0d 00h:00m:00.18s |
+----------------------------------+------------------------+-------------------------------------+-------------------+

Node Interface LIE FSMs:
+---------------------------------------------------------+----------------+-----------------------+-------------------+
| Description                                             | Value          | Last Rate             | Last Change       |
|                                                         |                | Over Last 10 Changes  |                   |
+---------------------------------------------------------+----------------+-----------------------+-------------------+
| Event-Transitions ONE_WAY -[SEND_LIE]-&gt; ONE_WAY         | 4 Transitions  | 1.01 Transitions/Sec  | 0d 00h:00m:00.28s |
+---------------------------------------------------------+----------------+-----------------------+-------------------+
| Event-Transitions ONE_WAY -[TIMER_TICK]-&gt; ONE_WAY       | 4 Transitions  | 1.01 Transitions/Sec  | 0d 00h:00m:00.28s |
+---------------------------------------------------------+----------------+-----------------------+-------------------+
| Event-Transitions THREE_WAY -[LIE_RECEIVED]-&gt; THREE_WAY | 24 Transitions | 9.19 Transitions/Sec  | 0d 00h:00m:00.18s |
+---------------------------------------------------------+----------------+-----------------------+-------------------+
| Event-Transitions THREE_WAY -[SEND_LIE]-&gt; THREE_WAY     | 12 Transitions | 3.02 Transitions/Sec  | 0d 00h:00m:00.28s |
+---------------------------------------------------------+----------------+-----------------------+-------------------+
.                                                         .                .                       .                   .
.                                                         .                .                       .                   .
+---------------------------------------------------------+----------------+-----------------------+-------------------+
| Transitions THREE_WAY -&gt; THREE_WAY                      | 48 Transitions | 91.11 Transitions/Sec | 0d 00h:00m:00.18s |
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
| 0.0.0.0/0     | North SPF | if_101_1 172.31.22.163    |
+---------------+-----------+---------------------------+
| 1.1.1.0/24    | South SPF | if_101_1001 172.31.22.163 |
+---------------+-----------+---------------------------+
| 1.1.2.0/24    | South SPF | if_101_1001 172.31.22.163 |
+---------------+-----------+---------------------------+
| 1.1.3.0/24    | South SPF | if_101_1001 172.31.22.163 |
+---------------+-----------+---------------------------+
.               .           .                           .
.               .           .                           .
+---------------+-----------+---------------------------+
| 99.99.99.0/24 | South SPF | if_101_1001 172.31.22.163 |
|               |           | if_101_1002 172.31.22.163 |
+---------------+-----------+---------------------------+

IPv6 Routes:
+--------+-----------+----------------------------------+
| Prefix | Owner     | Next-hops                        |
+--------+-----------+----------------------------------+
| ::/0   | North SPF | if_101_1 fe80::1b:a5ff:fef5:ab56 |
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
| 0.0.0.0/0     | North SPF | if_101_1 172.31.22.163    |
+---------------+-----------+---------------------------+
| 1.1.1.0/24    | South SPF | if_101_1001 172.31.22.163 |
+---------------+-----------+---------------------------+
| 1.1.2.0/24    | South SPF | if_101_1001 172.31.22.163 |
+---------------+-----------+---------------------------+
| 1.1.3.0/24    | South SPF | if_101_1001 172.31.22.163 |
+---------------+-----------+---------------------------+
.               .           .                           .
.               .           .                           .
+---------------+-----------+---------------------------+
| 99.99.99.0/24 | South SPF | if_101_1001 172.31.22.163 |
|               |           | if_101_1002 172.31.22.163 |
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
| ::/0   | North SPF | if_101_1 fe80::1b:a5ff:fef5:ab56 |
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
| ::/0   | North SPF | if_101_1 fe80::1b:a5ff:fef5:ab56 |
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
| 1001 (edge_1001) | 1    | True    | 101         |      |              | if_101_1001 172.31.22.163 | if_101_1001 fe80::1b:a5ff:fef5:ab56 |
+------------------+------+---------+-------------+------+--------------+---------------------------+-------------------------------------+
| 1002 (edge_1002) | 1    | True    | 101         |      |              | if_101_1002 172.31.22.163 | if_101_1002 fe80::1b:a5ff:fef5:ab56 |
+------------------+------+---------+-------------+------+--------------+---------------------------+-------------------------------------+
| 1.1.1.0/24       | 2    | True    | 1001        |      |              | if_101_1001 172.31.22.163 | if_101_1001 fe80::1b:a5ff:fef5:ab56 |
+------------------+------+---------+-------------+------+--------------+---------------------------+-------------------------------------+
.                  .      .         .             .      .              .                           .                                     .
.                  .      .         .             .      .              .                           .                                     .
+------------------+------+---------+-------------+------+--------------+---------------------------+-------------------------------------+
| 99.99.99.0/24    | 2    | True    | 1001        | 9992 |              | if_101_1001 172.31.22.163 | if_101_1001 fe80::1b:a5ff:fef5:ab56 |
|                  |      |         | 1002        | 9991 |              | if_101_1002 172.31.22.163 | if_101_1002 fe80::1b:a5ff:fef5:ab56 |
+------------------+------+---------+-------------+------+--------------+---------------------------+-------------------------------------+

North SPF Destinations:
+---------------+------+---------+-------------+------+--------------+------------------------+----------------------------------+
| Destination   | Cost | Is Leaf | Predecessor | Tags | Disaggregate | IPv4 Next-hops         | IPv6 Next-hops                   |
|               |      |         | System IDs  |      |              |                        |                                  |
+---------------+------+---------+-------------+------+--------------+------------------------+----------------------------------+
| 1 (core_1)    | 1    | False   | 101         |      |              | if_101_1 172.31.22.163 | if_101_1 fe80::1b:a5ff:fef5:ab56 |
+---------------+------+---------+-------------+------+--------------+------------------------+----------------------------------+
| 101 (agg_101) | 0    | False   |             |      |              |                        |                                  |
+---------------+------+---------+-------------+------+--------------+------------------------+----------------------------------+
| 0.0.0.0/0     | 2    | False   | 1           |      |              | if_101_1 172.31.22.163 | if_101_1 fe80::1b:a5ff:fef5:ab56 |
+---------------+------+---------+-------------+------+--------------+------------------------+----------------------------------+
| ::/0          | 2    | False   | 1           |      |              | if_101_1 172.31.22.163 | if_101_1 fe80::1b:a5ff:fef5:ab56 |
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
| 1 (core_1)    | 1    | False   | 101         |      |              | if_101_1 172.31.22.163 | if_101_1 fe80::1b:a5ff:fef5:ab56 |
+---------------+------+---------+-------------+------+--------------+------------------------+----------------------------------+
| 101 (agg_101) | 0    | False   |             |      |              |                        |                                  |
+---------------+------+---------+-------------+------+--------------+------------------------+----------------------------------+
| 0.0.0.0/0     | 2    | False   | 1           |      |              | if_101_1 172.31.22.163 | if_101_1 fe80::1b:a5ff:fef5:ab56 |
+---------------+------+---------+-------------+------+--------------+------------------------+----------------------------------+
| ::/0          | 2    | False   | 1           |      |              | if_101_1 172.31.22.163 | if_101_1 fe80::1b:a5ff:fef5:ab56 |
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
| ::/0        | 2    | False   | 1           |      |              | if_101_1 172.31.22.163 | if_101_1 fe80::1b:a5ff:fef5:ab56 |
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
