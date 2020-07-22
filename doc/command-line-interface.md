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
  * [show bandwidth-balancing](#show-bandwidth-balancing)
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
  * [show neighbors](#show-neighbors)
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

### show bandwidth-balancing

The "<b>show bandwidth-balancing</b> reports details about how the bandwidth is distributed across
neighbors and interfaces, for north-bound traffic following the default route.

<!-- OUTPUT-START: agg_101> show bandwidth-balancing -->
<pre>
agg_101> <b>show bandwidth-balancing</b>
North-Bound Neighbors:
+-----------+-----------+-----------+------------+-----------+-----------+------------+
| System ID | Neighbor  | Neighbor  | Neighbor   | Interface | Interface | Interface  |
|           | Ingress   | Egress    | Traffic    | Name      | Bandwidth | Traffic    |
|           | Bandwidth | Bandwidth | Percentage |           |           | Percentage |
+-----------+-----------+-----------+------------+-----------+-----------+------------+
| 1         | 100 Mbps  | 300 Mbps  | 50.0 %     | if_101_1  | 100 Mbps  | 50.0 %     |
+-----------+-----------+-----------+------------+-----------+-----------+------------+
| 2         | 100 Mbps  | 300 Mbps  | 50.0 %     | if_101_2  | 100 Mbps  | 50.0 %     |
+-----------+-----------+-----------+------------+-----------+-----------+------------+
</pre>
<!-- OUTPUT-END -->

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
+------------+-------------+-------------+-------------+-------------+
| Same-Level | North-bound | South-bound | Missing     | Extra       |
| Node       | Adjacencies | Adjacencies | South-bound | South-bound |
|            |             |             | Adjacencies | Adjacencies |
+------------+-------------+-------------+-------------+-------------+

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
+------------------------------------+---------------------+
| Stand-alone                        | False               |
| Interactive                        | True                |
| Simulated Interfaces               | True                |
| Physical Interface                 | eth0                |
| Telnet Port File                   | None                |
| IPv4 Multicast Loopback            | True                |
| IPv6 Multicast Loopback            | True                |
| Number of Nodes                    | 10                  |
| Transmit Source Address            | 127.0.0.1           |
| Flooding Reduction Enabled         | True                |
| Flooding Reduction Redundancy      | 2                   |
| Flooding Reduction Similarity      | 2                   |
| Flooding Reduction System Random   | 7891748190123070091 |
| Timer slips &gt; 10ms                 | 0                   |
| Timer slips &gt; 100ms                | 0                   |
| Timer slips &gt; 1000ms               | 0                   |
| Max pending events processing time | 0.003419            |
| Max expired timers processing time | 0.008722            |
| Max select processing time         | 0.056549            |
| Max ready-to-read processing time  | 0.009731            |
+------------------------------------+---------------------+
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
+------------------------------------------------------------------------------------------+----------------+----------------------+-------------------+
| Description                                                                              | Value          | Rate Over            | Last Change       |
|                                                                                          |                | Last 10 Seconds      |                   |
+------------------------------------------------------------------------------------------+----------------+----------------------+-------------------+
| Events CHANGE_LOCAL_CONFIGURED_LEVEL                                                     | 1 Event        | 0.00 Events/Sec      | 0d 00h:00m:00.38s |
+------------------------------------------------------------------------------------------+----------------+----------------------+-------------------+
| Events NEIGHBOR_OFFER                                                                    | 22 Events      | 0.00 Events/Sec      | 0d 00h:00m:00.74s |
+------------------------------------------------------------------------------------------+----------------+----------------------+-------------------+
| Events BETTER_HAL                                                                        | 0 Events       | 0.00 Events/Sec      |                   |
+------------------------------------------------------------------------------------------+----------------+----------------------+-------------------+
| Events BETTER_HAT                                                                        | 0 Events       | 0.00 Events/Sec      |                   |
+------------------------------------------------------------------------------------------+----------------+----------------------+-------------------+
.                                                                                          .                .                      .                   .
.                                                                                          .                .                      .                   .
+------------------------------------------------------------------------------------------+----------------+----------------------+-------------------+
| Event-Transitions UPDATING_CLIENTS -[CHANGE_LOCAL_CONFIGURED_LEVEL]-&gt; COMPUTE_BEST_OFFER | 1 Transition   | 0.00 Transitions/Sec | 0d 00h:00m:00.37s |
+------------------------------------------------------------------------------------------+----------------+----------------------+-------------------+

All Interfaces Traffic:
+---------------------------+------------------------+----------------------------------+-------------------+
| Description               | Value                  | Rate Over                        | Last Change       |
|                           |                        | Last 10 Seconds                  |                   |
+---------------------------+------------------------+----------------------------------+-------------------+
| RX IPv4 LIE Packets       | 11 Packets, 1894 Bytes | 0.00 Packets/Sec, 0.00 Bytes/Sec | 0d 00h:00m:00.75s |
+---------------------------+------------------------+----------------------------------+-------------------+
| TX IPv4 LIE Packets       | 12 Packets, 2040 Bytes | 0.00 Packets/Sec, 0.00 Bytes/Sec | 0d 00h:00m:00.75s |
+---------------------------+------------------------+----------------------------------+-------------------+
| RX IPv4 TIE Packets       | 0 Packets, 0 Bytes     | 0.00 Packets/Sec, 0.00 Bytes/Sec |                   |
+---------------------------+------------------------+----------------------------------+-------------------+
| TX IPv4 TIE Packets       | 0 Packets, 0 Bytes     | 0.00 Packets/Sec, 0.00 Bytes/Sec |                   |
+---------------------------+------------------------+----------------------------------+-------------------+
.                           .                        .                                  .                   .
.                           .                        .                                  .                   .
+---------------------------+------------------------+----------------------------------+-------------------+
| Total RX Misorders        | 0 Packets              | 0.00 Packets/Sec                 |                   |
+---------------------------+------------------------+----------------------------------+-------------------+

All Interfaces Security:
+------------------------------------------------+------------------------+----------------------------------+-------------------+
| Description                                    | Value                  | Rate Over                        | Last Change       |
|                                                |                        | Last 10 Seconds                  |                   |
+------------------------------------------------+------------------------+----------------------------------+-------------------+
| Missing outer security envelope                | 0 Packets, 0 Bytes     | 0.00 Packets/Sec, 0.00 Bytes/Sec |                   |
+------------------------------------------------+------------------------+----------------------------------+-------------------+
| Zero outer key id not accepted                 | 0 Packets, 0 Bytes     | 0.00 Packets/Sec, 0.00 Bytes/Sec |                   |
+------------------------------------------------+------------------------+----------------------------------+-------------------+
| Non-zero outer key id not accepted             | 0 Packets, 0 Bytes     | 0.00 Packets/Sec, 0.00 Bytes/Sec |                   |
+------------------------------------------------+------------------------+----------------------------------+-------------------+
| Incorrect outer fingerprint                    | 0 Packets, 0 Bytes     | 0.00 Packets/Sec, 0.00 Bytes/Sec |                   |
+------------------------------------------------+------------------------+----------------------------------+-------------------+
.                                                .                        .                                  .                   .
.                                                .                        .                                  .                   .
+------------------------------------------------+------------------------+----------------------------------+-------------------+
| Empty origin fingerprint accepted              | 0 Packets, 0 Bytes     | 0.00 Packets/Sec, 0.00 Bytes/Sec |                   |
+------------------------------------------------+------------------------+----------------------------------+-------------------+

All Interface LIE FSMs:
+------------------------------------------------------------+----------------+----------------------+-------------------+
| Description                                                | Value          | Rate Over            | Last Change       |
|                                                            |                | Last 10 Seconds      |                   |
+------------------------------------------------------------+----------------+----------------------+-------------------+
| Events TIMER_TICK                                          | 12 Events      | 0.00 Events/Sec      | 0d 00h:00m:00.76s |
+------------------------------------------------------------+----------------+----------------------+-------------------+
| Events LEVEL_CHANGED                                       | 0 Events       | 0.00 Events/Sec      |                   |
+------------------------------------------------------------+----------------+----------------------+-------------------+
| Events HAL_CHANGED                                         | 0 Events       | 0.00 Events/Sec      |                   |
+------------------------------------------------------------+----------------+----------------------+-------------------+
| Events HAT_CHANGED                                         | 0 Events       | 0.00 Events/Sec      |                   |
+------------------------------------------------------------+----------------+----------------------+-------------------+
.                                                            .                .                      .                   .
.                                                            .                .                      .                   .
+------------------------------------------------------------+----------------+----------------------+-------------------+
| Event-Transitions TWO_WAY -[TIMER_TICK]-&gt; TWO_WAY          | 0 Transitions  | 0.00 Transitions/Sec |                   |
+------------------------------------------------------------+----------------+----------------------+-------------------+
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
+------------------------------------------------------------------------------------------+----------------+----------------------+-------------------+
| Description                                                                              | Value          | Rate Over            | Last Change       |
|                                                                                          |                | Last 10 Seconds      |                   |
+------------------------------------------------------------------------------------------+----------------+----------------------+-------------------+
| Events CHANGE_LOCAL_CONFIGURED_LEVEL                                                     | 1 Event        | 0.10 Events/Sec      | 0d 00h:00m:00.53s |
+------------------------------------------------------------------------------------------+----------------+----------------------+-------------------+
| Events NEIGHBOR_OFFER                                                                    | 48 Events      | 4.40 Events/Sec      | 0d 00h:00m:00.02s |
+------------------------------------------------------------------------------------------+----------------+----------------------+-------------------+
| Events COMPUTATION_DONE                                                                  | 1 Event        | 0.10 Events/Sec      | 0d 00h:00m:00.53s |
+------------------------------------------------------------------------------------------+----------------+----------------------+-------------------+
| Enter COMPUTE_BEST_OFFER                                                                 | 1 Entry        | 0.10 Entries/Sec     | 0d 00h:00m:00.53s |
+------------------------------------------------------------------------------------------+----------------+----------------------+-------------------+
.                                                                                          .                .                      .                   .
.                                                                                          .                .                      .                   .
+------------------------------------------------------------------------------------------+----------------+----------------------+-------------------+
| Event-Transitions UPDATING_CLIENTS -[CHANGE_LOCAL_CONFIGURED_LEVEL]-&gt; COMPUTE_BEST_OFFER | 1 Transition   | 0.00 Transitions/Sec | 0d 00h:00m:00.53s |
+------------------------------------------------------------------------------------------+----------------+----------------------+-------------------+

All Interfaces Traffic:
+---------------------------+-------------------------+-------------------------------------+-------------------+
| Description               | Value                   | Rate Over                           | Last Change       |
|                           |                         | Last 10 Seconds                     |                   |
+---------------------------+-------------------------+-------------------------------------+-------------------+
| RX IPv4 LIE Packets       | 25 Packets, 4260 Bytes  | 2.40 Packets/Sec, 409.20 Bytes/Sec  | 0d 00h:00m:00.00s |
+---------------------------+-------------------------+-------------------------------------+-------------------+
| TX IPv4 LIE Packets       | 30 Packets, 4990 Bytes  | 2.80 Packets/Sec, 467.60 Bytes/Sec  | 0d 00h:00m:00.00s |
+---------------------------+-------------------------+-------------------------------------+-------------------+
| RX IPv4 TIE Packets       | 2 Packets, 612 Bytes    | 0.10 Packets/Sec, 30.60 Bytes/Sec   | 0d 00h:00m:00.01s |
+---------------------------+-------------------------+-------------------------------------+-------------------+
| TX IPv4 TIE Packets       | 2 Packets, 612 Bytes    | 0.10 Packets/Sec, 30.60 Bytes/Sec   | 0d 00h:00m:00.02s |
+---------------------------+-------------------------+-------------------------------------+-------------------+
.                           .                         .                                     .                   .
.                           .                         .                                     .                   .
+---------------------------+-------------------------+-------------------------------------+-------------------+
| Total TX Packets          | 91 Packets, 22560 Bytes | 8.30 Packets/Sec, 1987.00 Bytes/Sec | 0d 00h:00m:00.01s |
+---------------------------+-------------------------+-------------------------------------+-------------------+

All Interfaces Security:
+-----------------------------------+-------------------------+-------------------------------------+-------------------+
| Description                       | Value                   | Rate Over                           | Last Change       |
|                                   |                         | Last 10 Seconds                     |                   |
+-----------------------------------+-------------------------+-------------------------------------+-------------------+
| Empty outer fingerprint accepted  | 81 Packets, 21100 Bytes | 7.50 Packets/Sec, 1870.20 Bytes/Sec | 0d 00h:00m:00.01s |
+-----------------------------------+-------------------------+-------------------------------------+-------------------+
| Empty origin fingerprint accepted | 2 Packets, 612 Bytes    | 0.10 Packets/Sec, 30.60 Bytes/Sec   | 0d 00h:00m:00.01s |
+-----------------------------------+-------------------------+-------------------------------------+-------------------+

All Interface LIE FSMs:
+---------------------------------------------------------+----------------+----------------------+-------------------+
| Description                                             | Value          | Rate Over            | Last Change       |
|                                                         |                | Last 10 Seconds      |                   |
+---------------------------------------------------------+----------------+----------------------+-------------------+
| Events TIMER_TICK                                       | 30 Events      | 2.80 Events/Sec      | 0d 00h:00m:00.01s |
+---------------------------------------------------------+----------------+----------------------+-------------------+
| Events LIE_RECEIVED                                     | 48 Events      | 4.50 Events/Sec      | 0d 00h:00m:00.02s |
+---------------------------------------------------------+----------------+----------------------+-------------------+
| Events SEND_LIE                                         | 30 Events      | 2.80 Events/Sec      | 0d 00h:00m:00.01s |
+---------------------------------------------------------+----------------+----------------------+-------------------+
| Transitions ONE_WAY -&gt; ONE_WAY                          | 10 Transitions | 0.80 Transitions/Sec | 0d 00h:00m:00.01s |
+---------------------------------------------------------+----------------+----------------------+-------------------+
.                                                         .                .                      .                   .
.                                                         .                .                      .                   .
+---------------------------------------------------------+----------------+----------------------+-------------------+
| Event-Transitions THREE_WAY -[SEND_LIE]-&gt; THREE_WAY     | 25 Transitions | 2.40 Transitions/Sec | 0d 00h:00m:00.01s |
+---------------------------------------------------------+----------------+----------------------+-------------------+
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
+---------------+----------+-------------+------------+----------+
| Prefix        | Next-hop | Next-hop    | Next-hop   | Next-hop |
|               | Type     | Interface   | Address    | Weight   |
+---------------+----------+-------------+------------+----------+
| 0.0.0.0/0     | Positive | if_101_1    | 172.17.0.2 |          |
+---------------+----------+-------------+------------+----------+
| 1.1.1.0/24    | Positive | if_101_1001 | 172.17.0.2 |          |
+---------------+----------+-------------+------------+----------+
| 1.1.2.0/24    | Positive | if_101_1001 | 172.17.0.2 |          |
+---------------+----------+-------------+------------+----------+
| 1.1.3.0/24    | Positive | if_101_1001 | 172.17.0.2 |          |
+---------------+----------+-------------+------------+----------+
.               .          .             .            .          .
.               .          .             .            .          .
+---------------+----------+-------------+------------+----------+
| 99.99.99.0/24 | Positive | if_101_1001 | 172.17.0.2 |          |
|               | Positive | if_101_1002 | 172.17.0.2 |          |
+---------------+----------+-------------+------------+----------+

IPv6 Routes:
+--------+----------+-----------+----------------------+----------+
| Prefix | Next-hop | Next-hop  | Next-hop             | Next-hop |
|        | Type     | Interface | Address              | Weight   |
+--------+----------+-----------+----------------------+----------+
| ::/0   | Positive | if_101_1  | fe80::42:acff:fe11:2 |          |
+--------+----------+-----------+----------------------+----------+
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
+---------------+----------+-------------+------------+----------+
| Prefix        | Next-hop | Next-hop    | Next-hop   | Next-hop |
|               | Type     | Interface   | Address    | Weight   |
+---------------+----------+-------------+------------+----------+
| 0.0.0.0/0     | Positive | if_101_1    | 172.17.0.2 |          |
+---------------+----------+-------------+------------+----------+
| 1.1.1.0/24    | Positive | if_101_1001 | 172.17.0.2 |          |
+---------------+----------+-------------+------------+----------+
| 1.1.2.0/24    | Positive | if_101_1001 | 172.17.0.2 |          |
+---------------+----------+-------------+------------+----------+
| 1.1.3.0/24    | Positive | if_101_1001 | 172.17.0.2 |          |
+---------------+----------+-------------+------------+----------+
.               .          .             .            .          .
.               .          .             .            .          .
+---------------+----------+-------------+------------+----------+
| 99.99.99.0/24 | Positive | if_101_1001 | 172.17.0.2 |          |
|               | Positive | if_101_1002 | 172.17.0.2 |          |
+---------------+----------+-------------+------------+----------+
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
+--------+----------+-----------+----------------------+----------+
| Prefix | Next-hop | Next-hop  | Next-hop             | Next-hop |
|        | Type     | Interface | Address              | Weight   |
+--------+----------+-----------+----------------------+----------+
| ::/0   | Positive | if_101_1  | fe80::42:acff:fe11:2 |          |
+--------+----------+-----------+----------------------+----------+
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
| Interface IPv4 Address               | 172.17.0.2                                               |
| Interface IPv6 Address               | 2001:db8:1::242:ac11:2                                   |
| Interface Index                      | 8                                                        |
| Metric                               | 1                                                        |
| Bandwidth                            | 100 Mbpps                                                |
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
| Time in State                        | 0d 00h:00m:03.93s                                        |
| Flaps                                | 0                                                        |
| Received LIE Accepted or Rejected    | Accepted                                                 |
| Received LIE Accept or Reject Reason | Neither node is leaf and level difference is at most one |
| Neighbor is Flood Repeater           | False                                                    |
| Neighbor is Partially Connected      | N/A                                                      |
| Nodes Causing Partial Connectivity   |                                                          |
+--------------------------------------+----------------------------------------------------------+

Neighbor:
+------------------------+---------------------------+
| Name                   | core_1:if_1_101           |
| System ID              | 1                         |
| IPv4 Address           | 172.17.0.2                |
| IPv6 Address           | fe80::42:acff:fe11:2%eth0 |
| LIE UDP Source Port    | 58114                     |
| Link ID                | 1                         |
| Level                  | 24                        |
| Flood UDP Port         | 20003                     |
| MTU                    | 1400                      |
| POD                    | 0                         |
| Hold Time              | 3                         |
| Not a ZTP Offer        | False                     |
| You are Flood Repeater | False                     |
| Your System ID         | 101                       |
| Your Local ID          | 1                         |
+------------------------+---------------------------+
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
| 212      | 1.064085 | 0.001621 | 0.000075 | 0.008868   | 2       | TWO_WAY | VALID_REFLECTION    | increase_tx_nonce_local | THREE_WAY | False    |
|          |          |          |          |            |         |         |                     | start_flooding          |           |          |
|          |          |          |          |            |         |         |                     | init_partially_conn     |           |          |
+----------+----------+----------+----------+------------+---------+---------+---------------------+-------------------------+-----------+----------+
| 209      | 1.062464 | 0.837820 | 0.000135 | 0.000083   | 3       | ONE_WAY | NEW_NEIGHBOR        | SEND_LIE                | TWO_WAY   | False    |
|          |          |          |          |            |         |         |                     | increase_tx_nonce_local |           |          |
+----------+----------+----------+----------+------------+---------+---------+---------------------+-------------------------+-----------+----------+
| 68       | 0.224644 | 0.001721 | 0.000083 | 0.000006   | 1       | ONE_WAY | UNACCEPTABLE_HEADER |                         | ONE_WAY   | False    |
+----------+----------+----------+----------+------------+---------+---------+---------------------+-------------------------+-----------+----------+
| 66       | 0.222923 | 0.222923 | 0.000160 | 0.000006   | 1       | ONE_WAY | UNACCEPTABLE_HEADER |                         | ONE_WAY   | False    |
+----------+----------+----------+----------+------------+---------+---------+---------------------+-------------------------+-----------+----------+
| 9        | 0.000000 |          | 0.000000 | 0.000977   | 0       | None    | None                | cleanup                 | ONE_WAY   | False    |
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
+----------+----------+----------+----------+------------+-----------+---------------------+-------------------------+-----------+----------+
| Sequence | Time     | Time     | Queue    | Processing | From      | Event               | Actions and             | To        | Implicit |
| Nr       | Since    | Since    | Time     | Time       | State     |                     | Pushed Events           | State     |          |
|          | First    | Prev     |          |            |           |                     |                         |           |          |
+----------+----------+----------+----------+------------+-----------+---------------------+-------------------------+-----------+----------+
| 1046     | 5.129199 | 0.000266 | 0.000501 | 0.000092   | THREE_WAY | LIE_RECEIVED        | process_lie             | None      | False    |
+----------+----------+----------+----------+------------+-----------+---------------------+-------------------------+-----------+----------+
| 1045     | 5.128934 | 0.128804 | 0.001155 | 0.000122   | THREE_WAY | LIE_RECEIVED        | process_lie             | None      | False    |
+----------+----------+----------+----------+------------+-----------+---------------------+-------------------------+-----------+----------+
| 972      | 5.000130 | 0.000182 | 0.000147 | 0.001473   | THREE_WAY | SEND_LIE            | send_lie                | None      | False    |
+----------+----------+----------+----------+------------+-----------+---------------------+-------------------------+-----------+----------+
| 971      | 4.999947 | 0.872083 | 0.000131 | 0.000032   | THREE_WAY | TIMER_TICK          | check_hold_time_expired | None      | False    |
|          |          |          |          |            |           |                     | SEND_LIE                |           |          |
+----------+----------+----------+----------+------------+-----------+---------------------+-------------------------+-----------+----------+
.          .          .          .          .            .           .                     .                         .           .          .
.          .          .          .          .            .           .                     .                         .           .          .
+----------+----------+----------+----------+------------+-----------+---------------------+-------------------------+-----------+----------+
| 9        | 0.000000 |          | 0.000000 | 0.000977   | None      | None                | cleanup                 | ONE_WAY   | False    |
|          |          |          |          |            |           |                     | send_lie                |           |          |
+----------+----------+----------+----------+------------+-----------+---------------------+-------------------------+-----------+----------+
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
| direction=TX  timestamp=2020-07-16-12:08:41.272240                                                                                |
| local-address=fe80::42:acff:fe11:2%eth0:38951  remote_address=ff02::a1f7%eth0:20002                                               |
|                                                                                                                                   |
| packet-nr=7 outer-key-id=0 nonce-local=13630 nonce-remote=15365 remaining-lie-lifetime=all-ones outer-fingerprint-len=0           |
| protocol-packet=ProtocolPacket(content=PacketContent(tie=None, lie=LIEPacket(you_are_flood_repeater=False, flood_port=20004,      |
| link_capabilities=None, label=None, link_mtu_size=1400, local_id=1, name='agg_101:if_101_1', you_are_sending_too_quickly=False,   |
| pod=0, not_a_ztp_offer=True, holdtime=3, node_capabilities=NodeCapabilities(hierarchy_indications=1, flood_reduction=True,        |
| protocol_minor_version=1), instance_name=None, link_bandwidth=100, neighbor=Neighbor(originator=1, remote_id=1)), tide=None,      |
| tire=None), header=PacketHeader(major_version=4, sender=101, minor_version=1, level=23))                                          |
+-----------------------------------------------------------------------------------------------------------------------------------+
| direction=TX  timestamp=2020-07-16-12:08:41.271970  seconds-since-prev=0.0003                                                     |
| local-address=172.17.0.2:60055  remote_address=224.0.0.71:20002                                                                   |
|                                                                                                                                   |
| packet-nr=7 outer-key-id=0 nonce-local=13630 nonce-remote=15365 remaining-lie-lifetime=all-ones outer-fingerprint-len=0           |
| protocol-packet=ProtocolPacket(content=PacketContent(tie=None, lie=LIEPacket(you_are_flood_repeater=False, flood_port=20004,      |
| link_capabilities=None, label=None, link_mtu_size=1400, local_id=1, name='agg_101:if_101_1', you_are_sending_too_quickly=False,   |
| pod=0, not_a_ztp_offer=True, holdtime=3, node_capabilities=NodeCapabilities(hierarchy_indications=1, flood_reduction=True,        |
| protocol_minor_version=1), instance_name=None, link_bandwidth=100, neighbor=Neighbor(originator=1, remote_id=1)), tide=None,      |
| tire=None), header=PacketHeader(major_version=4, sender=101, minor_version=1, level=23))                                          |
+-----------------------------------------------------------------------------------------------------------------------------------+
| direction=RX  timestamp=2020-07-16-12:08:41.234127  seconds-since-prev=0.0378                                                     |
| local-address=ff02::a1f7%eth0:20001  remote_address=fe80::42:acff:fe11:2%eth0:58114                                               |
|                                                                                                                                   |
| packet-nr=7 outer-key-id=0 nonce-local=15365 nonce-remote=13630 remaining-lie-lifetime=all-ones outer-fingerprint-len=0           |
| protocol-packet=ProtocolPacket(content=PacketContent(tie=None, lie=LIEPacket(you_are_flood_repeater=False, flood_port=20003,      |
| link_capabilities=None, label=None, link_mtu_size=1400, local_id=1, name='core_1:if_1_101', you_are_sending_too_quickly=False,    |
| pod=0, not_a_ztp_offer=False, holdtime=3, node_capabilities=NodeCapabilities(hierarchy_indications=1, flood_reduction=True,       |
| protocol_minor_version=1), instance_name=None, link_bandwidth=100, neighbor=Neighbor(originator=101, remote_id=1)), tide=None,    |
| tire=None), header=PacketHeader(major_version=4, sender=1, minor_version=1, level=24))                                            |
+-----------------------------------------------------------------------------------------------------------------------------------+
| direction=RX  timestamp=2020-07-16-12:08:41.232770  seconds-since-prev=0.0014                                                     |
| local-address=224.0.0.81:20001  remote_address=172.17.0.2:33911                                                                   |
|                                                                                                                                   |
| packet-nr=7 outer-key-id=0 nonce-local=15365 nonce-remote=13630 remaining-lie-lifetime=all-ones outer-fingerprint-len=0           |
| protocol-packet=ProtocolPacket(content=PacketContent(tie=None, lie=LIEPacket(you_are_flood_repeater=False, flood_port=20003,      |
| link_capabilities=None, label=None, link_mtu_size=1400, local_id=1, name='core_1:if_1_101', you_are_sending_too_quickly=False,    |
| pod=0, not_a_ztp_offer=False, holdtime=3, node_capabilities=NodeCapabilities(hierarchy_indications=1, flood_reduction=True,       |
| protocol_minor_version=1), instance_name=None, link_bandwidth=100, neighbor=Neighbor(originator=101, remote_id=1)), tide=None,    |
| tire=None), header=PacketHeader(major_version=4, sender=1, minor_version=1, level=24))                                            |
+-----------------------------------------------------------------------------------------------------------------------------------+
| direction=TX  timestamp=2020-07-16-12:08:40.310888  seconds-since-prev=0.9219                                                     |
| local-address=172.17.0.2:59948  remote_address=172.17.0.2:20003                                                                   |
|                                                                                                                                   |
| packet-nr=3 outer-key-id=0 nonce-local=13630 nonce-remote=15365 remaining-lie-lifetime=all-ones outer-fingerprint-len=0           |
| protocol-packet=ProtocolPacket(content=PacketContent(tie=None, lie=None, tide=TIDEPacket(start_range=TIEID(originator=0,          |
| direction=1, tie_nr=0, tietype=2), headers=[TIEHeaderWithLifeTime(remaining_lifetime=604797,                                      |
| header=TIEHeader(origination_lifetime=None, origination_time=None, seq_nr=5, tieid=TIEID(originator=1, direction=1, tie_nr=1,     |
| tietype=2))), TIEHeaderWithLifeTime(remaining_lifetime=604797, header=TIEHeader(origination_lifetime=None, origination_time=None, |
| seq_nr=1, tieid=TIEID(originator=1, direction=1, tie_nr=2, tietype=3))), TIEHeaderWithLifeTime(remaining_lifetime=604797,         |
| header=TIEHeader(origination_lifetime=None, origination_time=None, seq_nr=4, tieid=TIEID(originator=101, direction=2, tie_nr=1,   |
| tietype=2))), TIEHeaderWithLifeTime(remaining_lifetime=604797, header=TIEHeader(origination_lifetime=None, origination_time=None, |
| seq_nr=3, tieid=TIEID(originator=1001, direction=2, tie_nr=1, tietype=2))), TIEHeaderWithLifeTime(remaining_lifetime=604796,      |
| header=TIEHeader(origination_lifetime=None, origination_time=None, seq_nr=1, tieid=TIEID(originator=1001, direction=2, tie_nr=2,  |
| tietype=3))), TIEHeaderWithLifeTime(remaining_lifetime=604797, header=TIEHeader(origination_lifetime=None, origination_time=None, |
| seq_nr=3, tieid=TIEID(originator=1002, direction=2, tie_nr=1, tietype=2))), TIEHeaderWithLifeTime(remaining_lifetime=604796,      |
| header=TIEHeader(origination_lifetime=None, origination_time=None, seq_nr=1, tieid=TIEID(originator=1002, direction=2, tie_nr=2,  |
| tietype=3)))], end_range=TIEID(originator=18446744073709551615, direction=2, tie_nr=4294967295, tietype=7)), tire=None),          |
| header=PacketHeader(major_version=4, sender=101, minor_version=1, level=23))                                                      |
+-----------------------------------------------------------------------------------------------------------------------------------+
.                                                                                                                                   .
.                                                                                                                                   .
+-----------------------------------------------------------------------------------------------------------------------------------+
| direction=RX  timestamp=2020-07-16-12:08:38.518123  seconds-since-prev=0.0018                                                     |
| local-address=172.17.0.2:20004  remote_address=172.17.0.2:37348                                                                   |
|                                                                                                                                   |
| packet-nr=1 outer-key-id=0 nonce-local=15365 nonce-remote=13630 remaining-lie-lifetime=all-ones outer-fingerprint-len=0           |
| protocol-packet=ProtocolPacket(content=PacketContent(tie=None, lie=None, tide=None,                                               |
| tire=TIREPacket(headers={TIEHeaderWithLifeTime(remaining_lifetime=0, header=TIEHeader(origination_lifetime=None,                  |
| origination_time=None, seq_nr=0, tieid=TIEID(originator=101, direction=2, tie_nr=1, tietype=2)))})),                              |
| header=PacketHeader(major_version=4, sender=1, minor_version=1, level=24))                                                        |
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
| Last Received LIE Nonce  | 15365          |
+--------------------------+----------------+
| Last Sent Nonce          | 13630          |
+--------------------------+----------------+
| Next Sent Nonce Increase | 54.359729 secs |
+--------------------------+----------------+

Security Statistics:
+------------------------------------------------+------------------------+------------------------------------+-------------------+
| Description                                    | Value                  | Rate Over                          | Last Change       |
|                                                |                        | Last 10 Seconds                    |                   |
+------------------------------------------------+------------------------+------------------------------------+-------------------+
| Missing outer security envelope                | 0 Packets, 0 Bytes     | 0.00 Packets/Sec, 0.00 Bytes/Sec   |                   |
+------------------------------------------------+------------------------+------------------------------------+-------------------+
| Zero outer key id not accepted                 | 0 Packets, 0 Bytes     | 0.00 Packets/Sec, 0.00 Bytes/Sec   |                   |
+------------------------------------------------+------------------------+------------------------------------+-------------------+
| Non-zero outer key id not accepted             | 0 Packets, 0 Bytes     | 0.00 Packets/Sec, 0.00 Bytes/Sec   |                   |
+------------------------------------------------+------------------------+------------------------------------+-------------------+
| Incorrect outer fingerprint                    | 0 Packets, 0 Bytes     | 0.00 Packets/Sec, 0.00 Bytes/Sec   |                   |
+------------------------------------------------+------------------------+------------------------------------+-------------------+
.                                                .                        .                                    .                   .
.                                                .                        .                                    .                   .
+------------------------------------------------+------------------------+------------------------------------+-------------------+
| Empty origin fingerprint accepted              | 2 Packets, 560 Bytes   | 0.20 Packets/Sec, 56.00 Bytes/Sec  | 0d 00h:00m:04.25s |
+------------------------------------------------+------------------------+------------------------------------+-------------------+
</pre>
<!-- OUTPUT-END -->

### show interface <i>interface</i> sockets

The "<b>show interface</b> <i>interface</i> <b>sockets</b>" command shows the sockets that the 
current node has opened for sending and receiving packets.

Example:

<!-- OUTPUT-START: agg_101> show interface if_101_1 sockets -->
<pre>
agg_101> <b>show interface if_101_1 sockets</b>
+----------+-----------+--------+---------------------------+------------+-----------------+-------------+
| Traffic  | Direction | Family | Local Address             | Local Port | Remote Address  | Remote Port |
+----------+-----------+--------+---------------------------+------------+-----------------+-------------+
| LIEs     | Receive   | IPv4   | 224.0.0.81                | 20001      | Any             | Any         |
+----------+-----------+--------+---------------------------+------------+-----------------+-------------+
| LIEs     | Receive   | IPv6   | ff02::a1f7%eth0           | 20001      | Any             | Any         |
+----------+-----------+--------+---------------------------+------------+-----------------+-------------+
| LIEs     | Send      | IPv4   | 172.17.0.2                | 60055      | 224.0.0.71      | 20002       |
+----------+-----------+--------+---------------------------+------------+-----------------+-------------+
| LIEs     | Send      | IPv6   | fe80::42:acff:fe11:2%eth0 | 38951      | ff02::a1f7%eth0 | 20002       |
+----------+-----------+--------+---------------------------+------------+-----------------+-------------+
.          .           .        .                           .            .                 .             .
.          .           .        .                           .            .                 .             .
+----------+-----------+--------+---------------------------+------------+-----------------+-------------+
| Flooding | Send      | IPv4   | 172.17.0.2                | 59948      | 172.17.0.2      | 20003       |
+----------+-----------+--------+---------------------------+------------+-----------------+-------------+
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
+---------------------------+-----------------------+------------------------------------+-------------------+
| Description               | Value                 | Rate Over                          | Last Change       |
|                           |                       | Last 10 Seconds                    |                   |
+---------------------------+-----------------------+------------------------------------+-------------------+
| RX IPv4 LIE Packets       | 2 Packets, 334 Bytes  | 0.20 Packets/Sec, 33.40 Bytes/Sec  | 0d 00h:00m:00.93s |
+---------------------------+-----------------------+------------------------------------+-------------------+
| TX IPv4 LIE Packets       | 2 Packets, 336 Bytes  | 0.20 Packets/Sec, 33.60 Bytes/Sec  | 0d 00h:00m:00.89s |
+---------------------------+-----------------------+------------------------------------+-------------------+
| RX IPv4 TIE Packets       | 0 Packets, 0 Bytes    | 0.00 Packets/Sec, 0.00 Bytes/Sec   |                   |
+---------------------------+-----------------------+------------------------------------+-------------------+
| TX IPv4 TIE Packets       | 0 Packets, 0 Bytes    | 0.00 Packets/Sec, 0.00 Bytes/Sec   |                   |
+---------------------------+-----------------------+------------------------------------+-------------------+
.                           .                       .                                    .                   .
.                           .                       .                                    .                   .
+---------------------------+-----------------------+------------------------------------+-------------------+
| Total RX Misorders        | 0 Packets             | 0.00 Packets/Sec                   |                   |
+---------------------------+-----------------------+------------------------------------+-------------------+

Security:
+------------------------------------------------+------------------------+------------------------------------+-------------------+
| Description                                    | Value                  | Rate Over                          | Last Change       |
|                                                |                        | Last 10 Seconds                    |                   |
+------------------------------------------------+------------------------+------------------------------------+-------------------+
| Missing outer security envelope                | 0 Packets, 0 Bytes     | 0.00 Packets/Sec, 0.00 Bytes/Sec   |                   |
+------------------------------------------------+------------------------+------------------------------------+-------------------+
| Zero outer key id not accepted                 | 0 Packets, 0 Bytes     | 0.00 Packets/Sec, 0.00 Bytes/Sec   |                   |
+------------------------------------------------+------------------------+------------------------------------+-------------------+
| Non-zero outer key id not accepted             | 0 Packets, 0 Bytes     | 0.00 Packets/Sec, 0.00 Bytes/Sec   |                   |
+------------------------------------------------+------------------------+------------------------------------+-------------------+
| Incorrect outer fingerprint                    | 0 Packets, 0 Bytes     | 0.00 Packets/Sec, 0.00 Bytes/Sec   |                   |
+------------------------------------------------+------------------------+------------------------------------+-------------------+
.                                                .                        .                                    .                   .
.                                                .                        .                                    .                   .
+------------------------------------------------+------------------------+------------------------------------+-------------------+
| Empty origin fingerprint accepted              | 2 Packets, 560 Bytes   | 0.20 Packets/Sec, 56.00 Bytes/Sec  | 0d 00h:00m:04.50s |
+------------------------------------------------+------------------------+------------------------------------+-------------------+

LIE FSM:
+------------------------------------------------------------+---------------+----------------------+-------------------+
| Description                                                | Value         | Rate Over            | Last Change       |
|                                                            |               | Last 10 Seconds      |                   |
+------------------------------------------------------------+---------------+----------------------+-------------------+
| Enter ONE_WAY                                              | 0 Entries     | 0.00 Entries/Sec     |                   |
+------------------------------------------------------------+---------------+----------------------+-------------------+
| Enter THREE_WAY                                            | 0 Entries     | 0.00 Entries/Sec     |                   |
+------------------------------------------------------------+---------------+----------------------+-------------------+
| Enter TWO_WAY                                              | 0 Entries     | 0.00 Entries/Sec     |                   |
+------------------------------------------------------------+---------------+----------------------+-------------------+
| Event-Transitions None -[None]-&gt; ONE_WAY                   | 0 Transitions | 0.00 Transitions/Sec |                   |
+------------------------------------------------------------+---------------+----------------------+-------------------+
.                                                            .               .                      .                   .
.                                                            .               .                      .                   .
+------------------------------------------------------------+---------------+----------------------+-------------------+
| Transitions TWO_WAY -&gt; TWO_WAY                             | 0 Transitions | 0.00 Transitions/Sec |                   |
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
+---------------------------+------------------------+------------------------------------+-------------------+
| Description               | Value                  | Rate Over                          | Last Change       |
|                           |                        | Last 10 Seconds                    |                   |
+---------------------------+------------------------+------------------------------------+-------------------+
| RX IPv4 LIE Packets       | 3 Packets, 501 Bytes   | 0.20 Packets/Sec, 33.40 Bytes/Sec  | 0d 00h:00m:00.08s |
+---------------------------+------------------------+------------------------------------+-------------------+
| TX IPv4 LIE Packets       | 3 Packets, 504 Bytes   | 0.20 Packets/Sec, 33.60 Bytes/Sec  | 0d 00h:00m:00.02s |
+---------------------------+------------------------+------------------------------------+-------------------+
| RX IPv4 TIDE Packets      | 2 Packets, 2036 Bytes  | 0.10 Packets/Sec, 101.80 Bytes/Sec | 0d 00h:00m:00.04s |
+---------------------------+------------------------+------------------------------------+-------------------+
| TX IPv4 TIDE Packets      | 2 Packets, 1092 Bytes  | 0.10 Packets/Sec, 54.60 Bytes/Sec  | 0d 00h:00m:00.01s |
+---------------------------+------------------------+------------------------------------+-------------------+
.                           .                        .                                    .                   .
.                           .                        .                                    .                   .
+---------------------------+------------------------+------------------------------------+-------------------+
| Total TX Packets          | 8 Packets, 2100 Bytes  | 0.50 Packets/Sec, 121.80 Bytes/Sec | 0d 00h:00m:00.01s |
+---------------------------+------------------------+------------------------------------+-------------------+

Security:
+-----------------------------------+------------------------+------------------------------------+-------------------+
| Description                       | Value                  | Rate Over                          | Last Change       |
|                                   |                        | Last 10 Seconds                    |                   |
+-----------------------------------+------------------------+------------------------------------+-------------------+
| Empty outer fingerprint accepted  | 25 Packets, 6464 Bytes | 2.40 Packets/Sec, 544.60 Bytes/Sec | 0d 00h:00m:00.04s |
+-----------------------------------+------------------------+------------------------------------+-------------------+
| Empty origin fingerprint accepted | 2 Packets, 560 Bytes   | 0.20 Packets/Sec, 56.00 Bytes/Sec  | 0d 00h:00m:04.65s |
+-----------------------------------+------------------------+------------------------------------+-------------------+

LIE FSM:
+---------------------------------------------------------+----------------+----------------------+-------------------+
| Description                                             | Value          | Rate Over            | Last Change       |
|                                                         |                | Last 10 Seconds      |                   |
+---------------------------------------------------------+----------------+----------------------+-------------------+
| Event-Transitions THREE_WAY -[LIE_RECEIVED]-&gt; THREE_WAY | 6 Transitions  | 0.40 Transitions/Sec | 0d 00h:00m:00.08s |
+---------------------------------------------------------+----------------+----------------------+-------------------+
| Event-Transitions THREE_WAY -[SEND_LIE]-&gt; THREE_WAY     | 3 Transitions  | 0.20 Transitions/Sec | 0d 00h:00m:00.03s |
+---------------------------------------------------------+----------------+----------------------+-------------------+
| Event-Transitions THREE_WAY -[TIMER_TICK]-&gt; THREE_WAY   | 3 Transitions  | 0.20 Transitions/Sec | 0d 00h:00m:00.03s |
+---------------------------------------------------------+----------------+----------------------+-------------------+
| Events LIE_RECEIVED                                     | 6 Events       | 0.40 Events/Sec      | 0d 00h:00m:00.08s |
+---------------------------------------------------------+----------------+----------------------+-------------------+
.                                                         .                .                      .                   .
.                                                         .                .                      .                   .
+---------------------------------------------------------+----------------+----------------------+-------------------+
| Transitions THREE_WAY -&gt; THREE_WAY                      | 12 Transitions | 0.80 Transitions/Sec | 0d 00h:00m:00.03s |
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
| South:0:Node:0 | North:18446744073709551615:Key-Value:4294967295 | South     | 1          | Node   | 1      | 5      | 604795    | -           |
|                |                                                 | South     | 1          | Prefix | 2      | 1      | 604795    | -           |
|                |                                                 | North     | 101        | Node   | 1      | 4      | 604795    | -           |
|                |                                                 | North     | 1001       | Node   | 1      | 3      | 604795    | -           |
|                |                                                 | North     | 1001       | Prefix | 2      | 1      | 604794    | -           |
|                |                                                 | North     | 1002       | Node   | 1      | 3      | 604795    | -           |
|                |                                                 | North     | 1002       | Prefix | 2      | 1      | 604794    | -           |
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
| if_101_1    | core_1:if_1_101       | 1         | THREE_WAY | 0d 00h:00m:05.24s | 0     |
+-------------+-----------------------+-----------+-----------+-------------------+-------+
| if_101_1001 | edge_1001:if_1001_101 | 1001      | THREE_WAY | 0d 00h:00m:05.23s | 0     |
+-------------+-----------------------+-----------+-----------+-------------------+-------+
| if_101_1002 | edge_1002:if_1002_101 | 1002      | THREE_WAY | 0d 00h:00m:05.21s | 0     |
+-------------+-----------------------+-----------+-----------+-------------------+-------+
| if_101_2    |                       |           | ONE_WAY   | 0d 00h:00m:06.30s | 0     |
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
+-----------+------------------------+------------+----------------+---------+
| Interface | Address                | Local      | Broadcast      | Anycast |
| Name      |                        |            |                |         |
+-----------+------------------------+------------+----------------+---------+
| lo        | 127.0.0.1              | 127.0.0.1  |                |         |
+-----------+------------------------+------------+----------------+---------+
| eth0      | 172.17.0.2             | 172.17.0.2 | 172.17.255.255 |         |
+-----------+------------------------+------------+----------------+---------+
|           | ::1                    |            |                |         |
+-----------+------------------------+------------+----------------+---------+
|           | 2001:db8:1::242:ac11:2 |            |                |         |
+-----------+------------------------+------------+----------------+---------+
|           | fe80::42:acff:fe11:2   |            |                |         |
+-----------+------------------------+------------+----------------+---------+
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
| tunl0     | 2         | 00:00:00:00:08:00 | 00:00:00:00:c4:00 | 0         | 1480  | NOARP     |
+-----------+-----------+-------------------+-------------------+-----------+-------+-----------+
| ip6tnl0   | 3         | 00:00:00:00:00:00 | 00:00:00:00:00:00 | 0         | 1452  | NOARP     |
+-----------+-----------+-------------------+-------------------+-----------+-------+-----------+
| eth0      | 8         | 02:42:ac:11:00:02 | ff:ff:ff:ff:ff:ff | 9         | 1500  | UP        |
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
+-------+---------+----------------------------+-----------+----------+-----------+---------------+--------+
| Table | Address | Destination                | Type      | Protocol | Outgoing  | Gateway       | Weight |
|       | Family  |                            |           |          | Interface |               |        |
+-------+---------+----------------------------+-----------+----------+-----------+---------------+--------+
| Main  | IPv4    | 0.0.0.0/0                  | Unicast   | Boot     | eth0      | 172.17.0.1    |        |
+-------+---------+----------------------------+-----------+----------+-----------+---------------+--------+
| Main  | IPv4    | 172.17.0.0/16              | Unicast   | Kernel   | eth0      |               |        |
+-------+---------+----------------------------+-----------+----------+-----------+---------------+--------+
| Main  | IPv6    | ::/0                       | Unicast   | Boot     | eth0      | 2001:db8:1::1 |        |
+-------+---------+----------------------------+-----------+----------+-----------+---------------+--------+
| Main  | IPv6    | 2001:db8:1::/64            | Unicast   | Kernel   | eth0      |               |        |
+-------+---------+----------------------------+-----------+----------+-----------+---------------+--------+
.       .         .                            .           .          .           .               .        .
.       .         .                            .           .          .           .               .        .
+-------+---------+----------------------------+-----------+----------+-----------+---------------+--------+
| Local | IPv6    | ff00::/8                   | Unicast   | Boot     | eth0      |               |        |
+-------+---------+----------------------------+-----------+----------+-----------+---------------+--------+
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
+-------+---------+-----------------+---------+----------+-----------+---------------+--------+
| Table | Address | Destination     | Type    | Protocol | Outgoing  | Gateway       | Weight |
|       | Family  |                 |         |          | Interface |               |        |
+-------+---------+-----------------+---------+----------+-----------+---------------+--------+
| Main  | IPv4    | 0.0.0.0/0       | Unicast | Boot     | eth0      | 172.17.0.1    |        |
+-------+---------+-----------------+---------+----------+-----------+---------------+--------+
| Main  | IPv4    | 172.17.0.0/16   | Unicast | Kernel   | eth0      |               |        |
+-------+---------+-----------------+---------+----------+-----------+---------------+--------+
| Main  | IPv6    | ::/0            | Unicast | Boot     | eth0      | 2001:db8:1::1 |        |
+-------+---------+-----------------+---------+----------+-----------+---------------+--------+
| Main  | IPv6    | 2001:db8:1::/64 | Unicast | Kernel   | eth0      |               |        |
+-------+---------+-----------------+---------+----------+-----------+---------------+--------+
| Main  | IPv6    | fe80::/64       | Unicast | Kernel   | eth0      |               |        |
+-------+---------+-----------------+---------+----------+-----------+---------------+--------+
</pre>
<!-- OUTPUT-END -->

If this command is executed on a platform that does not support the Netlink interface to the
kernel routing table (i.e. any non-Linux platform including BSD and macOS) the following error
message is reported:

<pre>
agg_101> <b>show kernel routes table main</b>
Kernel networking not supported on this platform
</pre>

### show neighbors

The "<b>show neighbor</b>" command reports a summary of all RIFT neighbors of the current node.
If there are multiple parallel links to the same neighbor, there may be fewer neighbors than
interfaces.

Use the "<b>show bandwidth-balancing</b> command to see details about how the bandwidth is
distributed across neighbors and interfaces.

<!-- OUTPUT-START: agg_101> show neighbors -->
<pre>
agg_101> <b>show neighbors</b>
+-----------+-----------+-------------+-----------------------+
| System ID | Direction | Interface   | Adjacency             |
|           |           | Name        | Name                  |
+-----------+-----------+-------------+-----------------------+
| 1         | North     | if_101_1    | core_1:if_1_101       |
+-----------+-----------+-------------+-----------------------+
| 2         | North     | if_101_2    | core_2:if_2_101       |
+-----------+-----------+-------------+-----------------------+
| 1001      | South     | if_101_1001 | edge_1001:if_1001_101 |
+-----------+-----------+-------------+-----------------------+
| 1002      | South     | if_101_1002 | edge_1002:if_1002_101 |
+-----------+-----------+-------------+-----------------------+
</pre>
<!-- OUTPUT-END -->

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
| Flooding Reduction Node Random        | 49551            |
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
| 786      | 3.560886 | 0.002231 | 0.002082 | 0.000091   | 0       | COMPUTE_BEST_OFFER | COMPUTATION_DONE              | update_all_lie_fsms  | UPDATING_CLIENTS   | False    |
+----------+----------+----------+----------+------------+---------+--------------------+-------------------------------+----------------------+--------------------+----------+
| 785      | 3.558656 | 1.609555 | 0.006622 | 0.000144   | 11      | UPDATING_CLIENTS   | CHANGE_LOCAL_CONFIGURED_LEVEL | store_level          | COMPUTE_BEST_OFFER | False    |
|          |          |          |          |            |         |                    |                               | stop_hold_down_timer |                    |          |
|          |          |          |          |            |         |                    |                               | level_compute        |                    |          |
|          |          |          |          |            |         |                    |                               | COMPUTATION_DONE     |                    |          |
+----------+----------+----------+----------+------------+---------+--------------------+-------------------------------+----------------------+--------------------+----------+
| 483      | 1.949101 | 0.001643 | 0.001408 | 0.000094   | 0       | COMPUTE_BEST_OFFER | COMPUTATION_DONE              | update_all_lie_fsms  | UPDATING_CLIENTS   | False    |
+----------+----------+----------+----------+------------+---------+--------------------+-------------------------------+----------------------+--------------------+----------+
| 482      | 1.947458 | 0.987272 | 0.000165 | 0.000231   | 12      | UPDATING_CLIENTS   | BETTER_HAT                    | stop_hold_down_timer | COMPUTE_BEST_OFFER | False    |
|          |          |          |          |            |         |                    |                               | level_compute        |                    |          |
|          |          |          |          |            |         |                    |                               | COMPUTATION_DONE     |                    |          |
+----------+----------+----------+----------+------------+---------+--------------------+-------------------------------+----------------------+--------------------+----------+
.          .          .          .          .            .         .                    .                               .                      .                    .          .
.          .          .          .          .            .         .                    .                               .                      .                    .          .
+----------+----------+----------+----------+------------+---------+--------------------+-------------------------------+----------------------+--------------------+----------+
| 11       | 0.000000 |          | 0.000000 | 0.000086   | 0       | None               | None                          | stop_hold_down_timer | COMPUTE_BEST_OFFER | False    |
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
+----------+----------+----------+----------+------------+--------------------+-------------------------------+------------------------+--------------------+----------+
| Sequence | Time     | Time     | Queue    | Processing | From               | Event                         | Actions and            | To                 | Implicit |
| Nr       | Since    | Since    | Time     | Time       | State              |                               | Pushed Events          | State              |          |
|          | First    | Prev     |          |            |                    |                               |                        |                    |          |
+----------+----------+----------+----------+------------+--------------------+-------------------------------+------------------------+--------------------+----------+
| 1364     | 7.138171 | 0.000130 | 0.000488 | 0.000015   | UPDATING_CLIENTS   | NEIGHBOR_OFFER                | update_or_remove_offer | None               | False    |
+----------+----------+----------+----------+------------+--------------------+-------------------------------+------------------------+--------------------+----------+
| 1363     | 7.138041 | 0.019121 | 0.000707 | 0.000026   | UPDATING_CLIENTS   | NEIGHBOR_OFFER                | update_or_remove_offer | None               | False    |
+----------+----------+----------+----------+------------+--------------------+-------------------------------+------------------------+--------------------+----------+
| 1352     | 7.118920 | 0.000119 | 0.000250 | 0.000014   | UPDATING_CLIENTS   | NEIGHBOR_OFFER                | update_or_remove_offer | None               | False    |
+----------+----------+----------+----------+------------+--------------------+-------------------------------+------------------------+--------------------+----------+
| 1351     | 7.118801 | 0.154187 | 0.000421 | 0.000022   | UPDATING_CLIENTS   | NEIGHBOR_OFFER                | update_or_remove_offer | None               | False    |
+----------+----------+----------+----------+------------+--------------------+-------------------------------+------------------------+--------------------+----------+
.          .          .          .          .            .                    .                               .                        .                    .          .
.          .          .          .          .            .                    .                               .                        .                    .          .
+----------+----------+----------+----------+------------+--------------------+-------------------------------+------------------------+--------------------+----------+
| 11       | 0.000000 |          | 0.000000 | 0.000086   | None               | None                          | stop_hold_down_timer   | COMPUTE_BEST_OFFER | False    |
|          |          |          |          |            |                    |                               | level_compute          |                    |          |
|          |          |          |          |            |                    |                               | COMPUTATION_DONE       |                    |          |
+----------+----------+----------+----------+------------+--------------------+-------------------------------+------------------------+--------------------+----------+
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
| Description                                                                              | Value          | Rate Over            | Last Change       |
|                                                                                          |                | Last 10 Seconds      |                   |
+------------------------------------------------------------------------------------------+----------------+----------------------+-------------------+
| Enter COMPUTE_BEST_OFFER                                                                 | 1 Entry        | 0.10 Entries/Sec     | 0d 00h:00m:03.89s |
+------------------------------------------------------------------------------------------+----------------+----------------------+-------------------+
| Enter UPDATING_CLIENTS                                                                   | 1 Entry        | 0.10 Entries/Sec     | 0d 00h:00m:03.89s |
+------------------------------------------------------------------------------------------+----------------+----------------------+-------------------+
| Event-Transitions COMPUTE_BEST_OFFER -[COMPUTATION_DONE]-&gt; UPDATING_CLIENTS              | 1 Transition   | 0.10 Transitions/Sec | 0d 00h:00m:03.89s |
+------------------------------------------------------------------------------------------+----------------+----------------------+-------------------+
| Event-Transitions None -[None]-&gt; COMPUTE_BEST_OFFER                                      | 0 Transitions  | 0.00 Transitions/Sec |                   |
+------------------------------------------------------------------------------------------+----------------+----------------------+-------------------+
.                                                                                          .                .                      .                   .
.                                                                                          .                .                      .                   .
+------------------------------------------------------------------------------------------+----------------+----------------------+-------------------+
| Transitions UPDATING_CLIENTS -&gt; UPDATING_CLIENTS                                         | 24 Transitions | 2.40 Transitions/Sec | 0d 00h:00m:00.31s |
+------------------------------------------------------------------------------------------+----------------+----------------------+-------------------+

Node Interfaces Traffic:
+---------------------------+------------------------+------------------------------------+-------------------+
| Description               | Value                  | Rate Over                          | Last Change       |
|                           |                        | Last 10 Seconds                    |                   |
+---------------------------+------------------------+------------------------------------+-------------------+
| RX IPv4 LIE Packets       | 12 Packets, 2052 Bytes | 1.20 Packets/Sec, 205.20 Bytes/Sec | 0d 00h:00m:00.32s |
+---------------------------+------------------------+------------------------------------+-------------------+
| TX IPv4 LIE Packets       | 16 Packets, 2624 Bytes | 1.60 Packets/Sec, 262.40 Bytes/Sec | 0d 00h:00m:00.46s |
+---------------------------+------------------------+------------------------------------+-------------------+
| RX IPv4 TIE Packets       | 4 Packets, 1224 Bytes  | 0.40 Packets/Sec, 122.40 Bytes/Sec | 0d 00h:00m:02.37s |
+---------------------------+------------------------+------------------------------------+-------------------+
| TX IPv4 TIE Packets       | 0 Packets, 0 Bytes     | 0.00 Packets/Sec, 0.00 Bytes/Sec   |                   |
+---------------------------+------------------------+------------------------------------+-------------------+
.                           .                        .                                    .                   .
.                           .                        .                                    .                   .
+---------------------------+------------------------+------------------------------------+-------------------+
| Total RX Misorders        | 0 Packets              | 0.00 Packets/Sec                   |                   |
+---------------------------+------------------------+------------------------------------+-------------------+

Node Interfaces Security:
+------------------------------------------------+------------------------+------------------------------------+-------------------+
| Description                                    | Value                  | Rate Over                          | Last Change       |
|                                                |                        | Last 10 Seconds                    |                   |
+------------------------------------------------+------------------------+------------------------------------+-------------------+
| Missing outer security envelope                | 0 Packets, 0 Bytes     | 0.00 Packets/Sec, 0.00 Bytes/Sec   |                   |
+------------------------------------------------+------------------------+------------------------------------+-------------------+
| Zero outer key id not accepted                 | 0 Packets, 0 Bytes     | 0.00 Packets/Sec, 0.00 Bytes/Sec   |                   |
+------------------------------------------------+------------------------+------------------------------------+-------------------+
| Non-zero outer key id not accepted             | 0 Packets, 0 Bytes     | 0.00 Packets/Sec, 0.00 Bytes/Sec   |                   |
+------------------------------------------------+------------------------+------------------------------------+-------------------+
| Incorrect outer fingerprint                    | 0 Packets, 0 Bytes     | 0.00 Packets/Sec, 0.00 Bytes/Sec   |                   |
+------------------------------------------------+------------------------+------------------------------------+-------------------+
.                                                .                        .                                    .                   .
.                                                .                        .                                    .                   .
+------------------------------------------------+------------------------+------------------------------------+-------------------+
| Empty origin fingerprint accepted              | 4 Packets, 1224 Bytes  | 0.40 Packets/Sec, 122.40 Bytes/Sec | 0d 00h:00m:02.38s |
+------------------------------------------------+------------------------+------------------------------------+-------------------+

Node Interface LIE FSMs:
+------------------------------------------------------------+----------------+----------------------+-------------------+
| Description                                                | Value          | Rate Over            | Last Change       |
|                                                            |                | Last 10 Seconds      |                   |
+------------------------------------------------------------+----------------+----------------------+-------------------+
| Enter ONE_WAY                                              | 0 Entries      | 0.00 Entries/Sec     |                   |
+------------------------------------------------------------+----------------+----------------------+-------------------+
| Enter THREE_WAY                                            | 0 Entries      | 0.00 Entries/Sec     |                   |
+------------------------------------------------------------+----------------+----------------------+-------------------+
| Enter TWO_WAY                                              | 0 Entries      | 0.00 Entries/Sec     |                   |
+------------------------------------------------------------+----------------+----------------------+-------------------+
| Event-Transitions None -[None]-&gt; ONE_WAY                   | 0 Transitions  | 0.00 Transitions/Sec |                   |
+------------------------------------------------------------+----------------+----------------------+-------------------+
.                                                            .                .                      .                   .
.                                                            .                .                      .                   .
+------------------------------------------------------------+----------------+----------------------+-------------------+
| Transitions TWO_WAY -&gt; TWO_WAY                             | 0 Transitions  | 0.00 Transitions/Sec |                   |
+------------------------------------------------------------+----------------+----------------------+-------------------+
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
| Description                                                                              | Value          | Rate Over            | Last Change       |
|                                                                                          |                | Last 10 Seconds      |                   |
+------------------------------------------------------------------------------------------+----------------+----------------------+-------------------+
| Enter COMPUTE_BEST_OFFER                                                                 | 1 Entry        | 0.10 Entries/Sec     | 0d 00h:00m:04.03s |
+------------------------------------------------------------------------------------------+----------------+----------------------+-------------------+
| Enter UPDATING_CLIENTS                                                                   | 1 Entry        | 0.10 Entries/Sec     | 0d 00h:00m:04.03s |
+------------------------------------------------------------------------------------------+----------------+----------------------+-------------------+
| Event-Transitions COMPUTE_BEST_OFFER -[COMPUTATION_DONE]-&gt; UPDATING_CLIENTS              | 1 Transition   | 0.10 Transitions/Sec | 0d 00h:00m:04.03s |
+------------------------------------------------------------------------------------------+----------------+----------------------+-------------------+
| Event-Transitions UPDATING_CLIENTS -[CHANGE_LOCAL_CONFIGURED_LEVEL]-&gt; COMPUTE_BEST_OFFER | 1 Transition   | 0.10 Transitions/Sec | 0d 00h:00m:04.03s |
+------------------------------------------------------------------------------------------+----------------+----------------------+-------------------+
.                                                                                          .                .                      .                   .
.                                                                                          .                .                      .                   .
+------------------------------------------------------------------------------------------+----------------+----------------------+-------------------+
| Transitions UPDATING_CLIENTS -&gt; UPDATING_CLIENTS                                         | 24 Transitions | 2.40 Transitions/Sec | 0d 00h:00m:00.45s |
+------------------------------------------------------------------------------------------+----------------+----------------------+-------------------+

Node Interfaces Traffic:
+---------------------------+------------------------+------------------------------------+-------------------+
| Description               | Value                  | Rate Over                          | Last Change       |
|                           |                        | Last 10 Seconds                    |                   |
+---------------------------+------------------------+------------------------------------+-------------------+
| RX IPv4 LIE Packets       | 12 Packets, 2052 Bytes | 1.20 Packets/Sec, 205.20 Bytes/Sec | 0d 00h:00m:00.46s |
+---------------------------+------------------------+------------------------------------+-------------------+
| TX IPv4 LIE Packets       | 16 Packets, 2624 Bytes | 1.60 Packets/Sec, 262.40 Bytes/Sec | 0d 00h:00m:00.60s |
+---------------------------+------------------------+------------------------------------+-------------------+
| RX IPv4 TIE Packets       | 4 Packets, 1224 Bytes  | 0.40 Packets/Sec, 122.40 Bytes/Sec | 0d 00h:00m:02.51s |
+---------------------------+------------------------+------------------------------------+-------------------+
| RX IPv4 TIDE Packets      | 6 Packets, 3748 Bytes  | 0.60 Packets/Sec, 374.80 Bytes/Sec | 0d 00h:00m:01.45s |
+---------------------------+------------------------+------------------------------------+-------------------+
.                           .                        .                                    .                   .
.                           .                        .                                    .                   .
+---------------------------+------------------------+------------------------------------+-------------------+
| Total TX Packets          | 40 Packets, 9118 Bytes | 4.00 Packets/Sec, 911.80 Bytes/Sec | 0d 00h:00m:00.60s |
+---------------------------+------------------------+------------------------------------+-------------------+

Node Interfaces Security:
+-----------------------------------+------------------------+------------------------------------+-------------------+
| Description                       | Value                  | Rate Over                          | Last Change       |
|                                   |                        | Last 10 Seconds                    |                   |
+-----------------------------------+------------------------+------------------------------------+-------------------+
| Empty outer fingerprint accepted  | 37 Packets, 9436 Bytes | 3.70 Packets/Sec, 943.60 Bytes/Sec | 0d 00h:00m:00.46s |
+-----------------------------------+------------------------+------------------------------------+-------------------+
| Empty origin fingerprint accepted | 4 Packets, 1224 Bytes  | 0.40 Packets/Sec, 122.40 Bytes/Sec | 0d 00h:00m:02.52s |
+-----------------------------------+------------------------+------------------------------------+-------------------+

Node Interface LIE FSMs:
+---------------------------------------------------------+----------------+----------------------+-------------------+
| Description                                             | Value          | Rate Over            | Last Change       |
|                                                         |                | Last 10 Seconds      |                   |
+---------------------------------------------------------+----------------+----------------------+-------------------+
| Event-Transitions ONE_WAY -[SEND_LIE]-&gt; ONE_WAY         | 4 Transitions  | 0.40 Transitions/Sec | 0d 00h:00m:00.61s |
+---------------------------------------------------------+----------------+----------------------+-------------------+
| Event-Transitions ONE_WAY -[TIMER_TICK]-&gt; ONE_WAY       | 4 Transitions  | 0.40 Transitions/Sec | 0d 00h:00m:00.62s |
+---------------------------------------------------------+----------------+----------------------+-------------------+
| Event-Transitions THREE_WAY -[LIE_RECEIVED]-&gt; THREE_WAY | 24 Transitions | 2.40 Transitions/Sec | 0d 00h:00m:00.46s |
+---------------------------------------------------------+----------------+----------------------+-------------------+
| Event-Transitions THREE_WAY -[SEND_LIE]-&gt; THREE_WAY     | 12 Transitions | 1.20 Transitions/Sec | 0d 00h:00m:00.61s |
+---------------------------------------------------------+----------------+----------------------+-------------------+
.                                                         .                .                      .                   .
.                                                         .                .                      .                   .
+---------------------------------------------------------+----------------+----------------------+-------------------+
| Transitions THREE_WAY -&gt; THREE_WAY                      | 48 Transitions | 4.80 Transitions/Sec | 0d 00h:00m:00.46s |
+---------------------------------------------------------+----------------+----------------------+-------------------+
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
+---------------+-----------+----------+-------------+------------+----------+
| Prefix        | Owner     | Next-hop | Next-hop    | Next-hop   | Next-hop |
|               |           | Type     | Interface   | Address    | Weight   |
+---------------+-----------+----------+-------------+------------+----------+
| 0.0.0.0/0     | North SPF | Positive | if_101_1    | 172.17.0.2 |          |
+---------------+-----------+----------+-------------+------------+----------+
| 1.1.1.0/24    | South SPF | Positive | if_101_1001 | 172.17.0.2 |          |
+---------------+-----------+----------+-------------+------------+----------+
| 1.1.2.0/24    | South SPF | Positive | if_101_1001 | 172.17.0.2 |          |
+---------------+-----------+----------+-------------+------------+----------+
| 1.1.3.0/24    | South SPF | Positive | if_101_1001 | 172.17.0.2 |          |
+---------------+-----------+----------+-------------+------------+----------+
.               .           .          .             .            .          .
.               .           .          .             .            .          .
+---------------+-----------+----------+-------------+------------+----------+
| 99.99.99.0/24 | South SPF | Positive | if_101_1001 | 172.17.0.2 |          |
|               |           | Positive | if_101_1002 | 172.17.0.2 |          |
+---------------+-----------+----------+-------------+------------+----------+

IPv6 Routes:
+--------+-----------+----------+-----------+----------------------+----------+
| Prefix | Owner     | Next-hop | Next-hop  | Next-hop             | Next-hop |
|        |           | Type     | Interface | Address              | Weight   |
+--------+-----------+----------+-----------+----------------------+----------+
| ::/0   | North SPF | Positive | if_101_1  | fe80::42:acff:fe11:2 |          |
+--------+-----------+----------+-----------+----------------------+----------+
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
+---------------+-----------+----------+-------------+------------+----------+
| Prefix        | Owner     | Next-hop | Next-hop    | Next-hop   | Next-hop |
|               |           | Type     | Interface   | Address    | Weight   |
+---------------+-----------+----------+-------------+------------+----------+
| 0.0.0.0/0     | North SPF | Positive | if_101_1    | 172.17.0.2 |          |
+---------------+-----------+----------+-------------+------------+----------+
| 1.1.1.0/24    | South SPF | Positive | if_101_1001 | 172.17.0.2 |          |
+---------------+-----------+----------+-------------+------------+----------+
| 1.1.2.0/24    | South SPF | Positive | if_101_1001 | 172.17.0.2 |          |
+---------------+-----------+----------+-------------+------------+----------+
| 1.1.3.0/24    | South SPF | Positive | if_101_1001 | 172.17.0.2 |          |
+---------------+-----------+----------+-------------+------------+----------+
.               .           .          .             .            .          .
.               .           .          .             .            .          .
+---------------+-----------+----------+-------------+------------+----------+
| 99.99.99.0/24 | South SPF | Positive | if_101_1001 | 172.17.0.2 |          |
|               |           | Positive | if_101_1002 | 172.17.0.2 |          |
+---------------+-----------+----------+-------------+------------+----------+
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
+--------+-----------+----------+-----------+----------------------+----------+
| Prefix | Owner     | Next-hop | Next-hop  | Next-hop             | Next-hop |
|        |           | Type     | Interface | Address              | Weight   |
+--------+-----------+----------+-----------+----------------------+----------+
| ::/0   | North SPF | Positive | if_101_1  | fe80::42:acff:fe11:2 |          |
+--------+-----------+----------+-----------+----------------------+----------+
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
+--------+-----------+----------+-----------+----------------------+----------+
| Prefix | Owner     | Next-hop | Next-hop  | Next-hop             | Next-hop |
|        |           | Type     | Interface | Address              | Weight   |
+--------+-----------+----------+-----------+----------------------+----------+
| ::/0   | North SPF | Positive | if_101_1  | fe80::42:acff:fe11:2 |          |
+--------+-----------+----------+-----------+----------------------+----------+
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
+------------------------------------------------+-------------------------+-------------------------------------+-------------------+
| Description                                    | Value                   | Rate Over                           | Last Change       |
|                                                |                         | Last 10 Seconds                     |                   |
+------------------------------------------------+-------------------------+-------------------------------------+-------------------+
| Missing outer security envelope                | 0 Packets, 0 Bytes      | 0.00 Packets/Sec, 0.00 Bytes/Sec    |                   |
+------------------------------------------------+-------------------------+-------------------------------------+-------------------+
| Zero outer key id not accepted                 | 0 Packets, 0 Bytes      | 0.00 Packets/Sec, 0.00 Bytes/Sec    |                   |
+------------------------------------------------+-------------------------+-------------------------------------+-------------------+
| Non-zero outer key id not accepted             | 0 Packets, 0 Bytes      | 0.00 Packets/Sec, 0.00 Bytes/Sec    |                   |
+------------------------------------------------+-------------------------+-------------------------------------+-------------------+
| Incorrect outer fingerprint                    | 0 Packets, 0 Bytes      | 0.00 Packets/Sec, 0.00 Bytes/Sec    |                   |
+------------------------------------------------+-------------------------+-------------------------------------+-------------------+
.                                                .                         .                                     .                   .
.                                                .                         .                                     .                   .
+------------------------------------------------+-------------------------+-------------------------------------+-------------------+
| Empty origin fingerprint accepted              | 4 Packets, 1224 Bytes   | 0.40 Packets/Sec, 122.40 Bytes/Sec  | 0d 00h:00m:03.39s |
+------------------------------------------------+-------------------------+-------------------------------------+-------------------+
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
| SPF Deferrals | 17 |
+---------------+----+

South SPF Destinations:
+------------------+------+---------+-------------+------+--------------+------------------------+----------------------------------+
| Destination      | Cost | Is Leaf | Predecessor | Tags | Disaggregate | IPv4 Next-hops         | IPv6 Next-hops                   |
|                  |      |         | System IDs  |      |              |                        |                                  |
+------------------+------+---------+-------------+------+--------------+------------------------+----------------------------------+
| 101 (agg_101)    | 0    | False   |             |      |              |                        |                                  |
+------------------+------+---------+-------------+------+--------------+------------------------+----------------------------------+
| 1001 (edge_1001) | 1    | True    | 101         |      |              | if_101_1001 172.17.0.2 | if_101_1001 fe80::42:acff:fe11:2 |
+------------------+------+---------+-------------+------+--------------+------------------------+----------------------------------+
| 1002 (edge_1002) | 1    | True    | 101         |      |              | if_101_1002 172.17.0.2 | if_101_1002 fe80::42:acff:fe11:2 |
+------------------+------+---------+-------------+------+--------------+------------------------+----------------------------------+
| 1.1.1.0/24       | 2    | True    | 1001        |      |              | if_101_1001 172.17.0.2 | if_101_1001 fe80::42:acff:fe11:2 |
+------------------+------+---------+-------------+------+--------------+------------------------+----------------------------------+
.                  .      .         .             .      .              .                        .                                  .
.                  .      .         .             .      .              .                        .                                  .
+------------------+------+---------+-------------+------+--------------+------------------------+----------------------------------+
| 99.99.99.0/24    | 2    | True    | 1001        | 9992 |              | if_101_1001 172.17.0.2 | if_101_1001 fe80::42:acff:fe11:2 |
|                  |      |         | 1002        | 9991 |              | if_101_1002 172.17.0.2 | if_101_1002 fe80::42:acff:fe11:2 |
+------------------+------+---------+-------------+------+--------------+------------------------+----------------------------------+

North SPF Destinations:
+---------------+------+---------+-------------+------+--------------+---------------------+-------------------------------+
| Destination   | Cost | Is Leaf | Predecessor | Tags | Disaggregate | IPv4 Next-hops      | IPv6 Next-hops                |
|               |      |         | System IDs  |      |              |                     |                               |
+---------------+------+---------+-------------+------+--------------+---------------------+-------------------------------+
| 1 (core_1)    | 1    | False   | 101         |      |              | if_101_1 172.17.0.2 | if_101_1 fe80::42:acff:fe11:2 |
+---------------+------+---------+-------------+------+--------------+---------------------+-------------------------------+
| 101 (agg_101) | 0    | False   |             |      |              |                     |                               |
+---------------+------+---------+-------------+------+--------------+---------------------+-------------------------------+
| 0.0.0.0/0     | 2    | False   | 1           |      |              | if_101_1 172.17.0.2 | if_101_1 fe80::42:acff:fe11:2 |
+---------------+------+---------+-------------+------+--------------+---------------------+-------------------------------+
| ::/0          | 2    | False   | 1           |      |              | if_101_1 172.17.0.2 | if_101_1 fe80::42:acff:fe11:2 |
+---------------+------+---------+-------------+------+--------------+---------------------+-------------------------------+

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
+---------------+------+---------+-------------+------+--------------+---------------------+-------------------------------+
| Destination   | Cost | Is Leaf | Predecessor | Tags | Disaggregate | IPv4 Next-hops      | IPv6 Next-hops                |
|               |      |         | System IDs  |      |              |                     |                               |
+---------------+------+---------+-------------+------+--------------+---------------------+-------------------------------+
| 1 (core_1)    | 1    | False   | 101         |      |              | if_101_1 172.17.0.2 | if_101_1 fe80::42:acff:fe11:2 |
+---------------+------+---------+-------------+------+--------------+---------------------+-------------------------------+
| 101 (agg_101) | 0    | False   |             |      |              |                     |                               |
+---------------+------+---------+-------------+------+--------------+---------------------+-------------------------------+
| 0.0.0.0/0     | 2    | False   | 1           |      |              | if_101_1 172.17.0.2 | if_101_1 fe80::42:acff:fe11:2 |
+---------------+------+---------+-------------+------+--------------+---------------------+-------------------------------+
| ::/0          | 2    | False   | 1           |      |              | if_101_1 172.17.0.2 | if_101_1 fe80::42:acff:fe11:2 |
+---------------+------+---------+-------------+------+--------------+---------------------+-------------------------------+
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
+-------------+------+---------+-------------+------+--------------+---------------------+-------------------------------+
| Destination | Cost | Is Leaf | Predecessor | Tags | Disaggregate | IPv4 Next-hops      | IPv6 Next-hops                |
|             |      |         | System IDs  |      |              |                     |                               |
+-------------+------+---------+-------------+------+--------------+---------------------+-------------------------------+
| ::/0        | 2    | False   | 1           |      |              | if_101_1 172.17.0.2 | if_101_1 fe80::42:acff:fe11:2 |
+-------------+------+---------+-------------+------+--------------+---------------------+-------------------------------+
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
| South     | 1          | Node   | 1      | 5      | 604792   | Name: core_1            |
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
| South     | 1          | Prefix | 2      | 1      | 604792   | Prefix: 0.0.0.0/0       |
|           |            |        |        |        |          |   Metric: 1             |
|           |            |        |        |        |          | Prefix: ::/0            |
|           |            |        |        |        |          |   Metric: 1             |
+-----------+------------+--------+--------+--------+----------+-------------------------+
| South     | 101        | Node   | 1      | 4      | 604792   | Name: agg_101           |
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
| South     | 101        | Prefix | 2      | 1      | 604792   | Prefix: 0.0.0.0/0       |
|           |            |        |        |        |          |   Metric: 1             |
|           |            |        |        |        |          | Prefix: ::/0            |
|           |            |        |        |        |          |   Metric: 1             |
+-----------+------------+--------+--------+--------+----------+-------------------------+
.           .            .        .        .        .          .                         .
.           .            .        .        .        .          .                         .
+-----------+------------+--------+--------+--------+----------+-------------------------+
| North     | 1002       | Prefix | 2      | 1      | 604791   | Prefix: 1.2.1.0/24      |
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
| South     | 1          | Node   | 1      | 5      | 604792   | Name: core_1            |
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
| South     | 1          | Prefix | 2      | 1      | 604792   | Prefix: 0.0.0.0/0       |
|           |            |        |        |        |          |   Metric: 1             |
|           |            |        |        |        |          | Prefix: ::/0            |
|           |            |        |        |        |          |   Metric: 1             |
+-----------+------------+--------+--------+--------+----------+-------------------------+
| South     | 101        | Node   | 1      | 4      | 604792   | Name: agg_101           |
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
| South     | 101        | Prefix | 2      | 1      | 604792   | Prefix: 0.0.0.0/0       |
|           |            |        |        |        |          |   Metric: 1             |
|           |            |        |        |        |          | Prefix: ::/0            |
|           |            |        |        |        |          |   Metric: 1             |
+-----------+------------+--------+--------+--------+----------+-------------------------+
| South     | 102        | Node   | 1      | 4      | 604793   | Name: agg_102           |
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
| South     | 1          | Node   | 1      | 5      | 604792   | Name: core_1            |
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
| South     | 1          | Prefix | 2      | 1      | 604792   | Prefix: 0.0.0.0/0       |
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
| South     | 1          | Node | 1      | 5      | 604792   | Name: core_1            |
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
