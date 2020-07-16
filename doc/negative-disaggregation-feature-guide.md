# Negative Disaggregation Feature Guide

We assume you have already read the
[Disaggregation Feature Guide](disaggregation-feature-guide.md),
which describes what automatic disaggregation is, how automatic disaggregation works from a RIFT
protocol point of view, and what the the difference between positive disaggregation and negative
disaggregation is. This feature guide describes the nuts and bolts of using the RIFT-Python command
line interface (CLI) to see negative disagregation in action. There is a separate
[Positive Disaggregation Feature Guide](positive-disaggregation-feature-guide.md), which you should
read first.

## Example network

The examples in this guide are based on the topology shown in figure 1 below. Negative
disaggregation is applicable in multi-plane topologies with east-west inter-plane rings, which is exactly what this topology is.

![Topology Diagram](https://s3-us-west-2.amazonaws.com/brunorijsman-public/diagram-rift-neg-disagg-fg.png)

*Figure 1. Topology used in this feature guide.*

## Generating and starting the topology

The above topology is described by meta-topology `meta_topology/clos_3plane_3pod_3leaf_3spine_6super.yaml`.
Use the following commands to convert the meta-topology to topology and to start it in
single-process mode:

<pre>
(env) $ <b>tools/config_generator.py meta_topology/clos_3plane_3pod_3leaf_3spine_6super.yaml generated.yaml</b>
(env) $ <b>python rift --interactive generated.yaml</b>
</pre>

## The state of the fabric before triggering negative disaggregation

Let us first look at the fabric before we break any links and before any negative disaggregation
happens.

### Spine-1-1

On spine-1-1 all adjacencies are up:

<pre>
spine-1-1> <b>show interfaces</b>
+-----------+-------------------+-----------+-----------+-------------------+-------+
| Interface | Neighbor          | Neighbor  | Neighbor  | Time in           | Flaps |
| Name      | Name              | System ID | State     | State             |       |
+-----------+-------------------+-----------+-----------+-------------------+-------+
| if-101a   | leaf-1-1:if-1001a | 1001      | THREE_WAY | 0d 00h:00m:16.97s | 0     |
+-----------+-------------------+-----------+-----------+-------------------+-------+
| if-101b   | leaf-1-2:if-1002a | 1002      | THREE_WAY | 0d 00h:00m:16.85s | 0     |
+-----------+-------------------+-----------+-----------+-------------------+-------+
| if-101c   | leaf-1-3:if-1003a | 1003      | THREE_WAY | 0d 00h:00m:16.85s | 0     |
+-----------+-------------------+-----------+-----------+-------------------+-------+
| if-101d   | super-1-1:if-1a   | 1         | THREE_WAY | 0d 00h:00m:16.84s | 0     |
+-----------+-------------------+-----------+-----------+-------------------+-------+
| if-101e   | super-1-2:if-2a   | 2         | THREE_WAY | 0d 00h:00m:16.84s | 0     |
+-----------+-------------------+-----------+-----------+-------------------+-------+
</pre>

Note: we don't spell out the `set node `<i>`node-name`</i> commands that are needed to go to right
node that is implied by the CLI prompt in the example outputs.

### Super-1-1

On the other side, i.e. on super-1-1, the adjacency to spine-1-1 is up as well:

<pre>
super-1-1> <b>show interfaces</b>
+-----------+-------------------+-----------+-----------+-------------------+-------+
| Interface | Neighbor          | Neighbor  | Neighbor  | Time in           | Flaps |
| Name      | Name              | System ID | State     | State             |       |
+-----------+-------------------+-----------+-----------+-------------------+-------+
| if-1a     | spine-1-1:if-101d | 101       | THREE_WAY | 0d 00h:00m:39.33s | 0     |
+-----------+-------------------+-----------+-----------+-------------------+-------+
| if-1b     | spine-2-1:if-104d | 104       | THREE_WAY | 0d 00h:00m:38.78s | 0     |
+-----------+-------------------+-----------+-----------+-------------------+-------+
| if-1c     | spine-3-1:if-107d | 107       | THREE_WAY | 0d 00h:00m:38.78s | 0     |
+-----------+-------------------+-----------+-----------+-------------------+-------+
| if-1d     | super-2-1:if-3d   | 3         | THREE_WAY | 0d 00h:00m:40.03s | 0     |
+-----------+-------------------+-----------+-----------+-------------------+-------+
| if-1e     | super-3-1:if-5e   | 5         | THREE_WAY | 0d 00h:00m:40.03s | 0     |
+-----------+-------------------+-----------+-----------+-------------------+-------+
</pre>

### Super-1-2

We issue the `show disaggregation` command on anyone of the superspine nodes to get a summary of
what is happening in terms of dissaggregation in the top-of-fabric. In this example we choose node 
super-1-2 and observe that:

 1. There are no missing south-bound adjacencies. This means none of the other superspine nodes in
    plane-1 have any missing (or extra, for that matter) south-bound adjacencies as
    compared to super-1-2. Both superspines in plane-1 have the same set of south-bound adjacencies.
    Only superspines in the same plane are considered for the detection of missing south-bound
    adjacencies. If any missing south-bound adjacencies are discovered, it may trigger positive
    disaggregation. Negative disaggregation, as we will see, is triggered by something else,
    namely a difference in reachable nodes between the normal south-bound SPF and the special
    south-bound SPF.

 2. Super-1-2 does not have any partially connected south-bound interface. That means that every
    south-bound spine neighbor of super-1-2 is also fully connected to all the other superspines in
    plane-1, i.e. also connected to super-1-1.

 3. Super-1-2 is currently not originating any positive disaggregation prefixes. Evidently it had
    originated a positive disaggregation prefix in the past while the topology was converging.
    But that transitory positive disaggregation prefix has since been flushed which is evident from
    the empty TIE and sequence number 2.

 4. Super-1-2 currently does not have any positivate disaggregation prefixes from other nodes.

 5. Super-1-2 does not have any negative disaggregation prefixes (neither originated nor received)
    in its TIE database.

<pre>
super-1-2> <b>show disaggregation</b>
Same Level Nodes:
Same Level Nodes:
+---------------+-------------+-----------------+-------------+-------------+
| Same-Level    | North-bound | South-bound     | Missing     | Extra       |
| Node          | Adjacencies | Adjacencies     | South-bound | South-bound |
|               |             |                 | Adjacencies | Adjacencies |
+---------------+-------------+-----------------+-------------+-------------+
| super-1-1 (1) |             | spine-1-1 (101) |             |             |
|               |             | spine-2-1 (104) |             |             |
|               |             | spine-3-1 (107) |             |             |
+---------------+-------------+-----------------+-------------+-------------+

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

### Spine-2-1

Spine-2-1 is in plane-1. It can reach the leaves in other pods over all superspines that are in
plane-1 (note that spines and superspines are in a particular plane, but leaves are not). Thus, 
spine-2-1 has:

 1. A north-bound default ECMPs over both superspines in plane-1, namely super-1-1 and super-1-2.

 2. Normal south-bound specific routes to leaf-2-1, leaf-2-2, and leaf-2-3.

 3. No positive or negative disaggregation routes.

 4. For IPv6 there is only a default route because we did not assign any IPv6 addresses to the
    loopbacks.

<pre>
spine-2-1> <b>show routes</b>
IPv4 Routes:
+-------------+-----------+----------+-----------+--------------+----------+
| Prefix      | Owner     | Next-hop | Next-hop  | Next-hop     | Next-hop |
|             |           | Type     | Interface | Address      | Weight   |
+-------------+-----------+----------+-----------+--------------+----------+
| 0.0.0.0/0   | North SPF | Positive | if-104e   | 172.31.60.58 |          |
|             |           | Positive | if-104d   | 172.31.60.58 |          |
+-------------+-----------+----------+-----------+--------------+----------+
| 88.0.4.1/32 | South SPF | Positive | if-104a   | 172.31.60.58 |          |
+-------------+-----------+----------+-----------+--------------+----------+
| 88.0.5.1/32 | South SPF | Positive | if-104b   | 172.31.60.58 |          |
+-------------+-----------+----------+-----------+--------------+----------+
| 88.0.6.1/32 | South SPF | Positive | if-104c   | 172.31.60.58 |          |
+-------------+-----------+----------+-----------+--------------+----------+

IPv6 Routes:
+--------+-----------+----------+-----------+--------------------------+----------+
| Prefix | Owner     | Next-hop | Next-hop  | Next-hop                 | Next-hop |
|        |           | Type     | Interface | Address                  | Weight   |
+--------+-----------+----------+-----------+--------------------------+----------+
| ::/0   | North SPF | Positive | if-104e   | fe80::cfc:a3ff:fe0e:36b4 |          |
|        |           | Positive | if-104d   | fe80::cfc:a3ff:fe0e:36b4 |          |
+--------+-----------+----------+-----------+--------------------------+----------+
</pre>

### Leaf-2-2

We want to look at some arbitrary leaf in pod-2 and randomly pick leaf-2-2.
At this point leaf-2-2 only has north-bound default route that ECMPs over spine-2-1, spine-2-2,
and spine-2-3.

<pre>
leaf-2-2> <b>show routes</b>
IPv4 Routes:
+-----------+-----------+----------+-----------+--------------+----------+
| Prefix    | Owner     | Next-hop | Next-hop  | Next-hop     | Next-hop |
|           |           | Type     | Interface | Address      | Weight   |
+-----------+-----------+----------+-----------+--------------+----------+
| 0.0.0.0/0 | North SPF | Positive | if-1005a  | 172.31.60.58 |          |
|           |           | Positive | if-1005b  | 172.31.60.58 |          |
|           |           | Positive | if-1005c  | 172.31.60.58 |          |
+-----------+-----------+----------+-----------+--------------+----------+

IPv6 Routes:
+--------+-----------+----------+-----------+--------------------------+----------+
| Prefix | Owner     | Next-hop | Next-hop  | Next-hop                 | Next-hop |
|        |           | Type     | Interface | Address                  | Weight   |
+--------+-----------+----------+-----------+--------------------------+----------+
| ::/0   | North SPF | Positive | if-1005a  | fe80::cfc:a3ff:fe0e:36b4 |          |
|        |           | Positive | if-1005b  | fe80::cfc:a3ff:fe0e:36b4 |          |
|        |           | Positive | if-1005c  | fe80::cfc:a3ff:fe0e:36b4 |          |
+--------+-----------+----------+-----------+--------------------------+----------+
</pre>

We do not see any /32 routes on leaf-2-2 because there is no disaggregation happening.

Just for completness sake, we can also verify that there are no disaggregation prefix TIEs on
leaf-2-2.

<pre>
leaf-2-2> <b>show disaggregation</b>
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

## Breaking one link to trigger both positive and negative disaggregation

First we break the link between spine-1-1 and super-1-1 as shown in figure 2 below.

This causes a rather complex sequence of events:

 1. It causes super-1-1 to trigger negative disaggregation for the prefixes in pod-1 because
    super-1-1 detects that those prefixes can be reached from other planes but not from its own
    plane.

 2. It causes super-1-2 to trigger positive disaggregation for the prefixes in pod-1 because
    super-1-2 can still reach those prefixes and super-1-2 also detects that super-1-1 (which
    is a same-level-node in plane-1) can not reach those prefixes anymore.

![Topology Diagram](https://s3-us-west-2.amazonaws.com/brunorijsman-public/diagram-rift-neg-disagg-fg-orig-1-failure.png)

*Figure 2. First failure between spine-1-1 and super-1-1.*

### Spine-1-1

The following command simulates a failure of the spine-1-1 to super-1-1 link:

<pre>
spine-1-1> <b>set interface if-101d failure failed</b>
</pre>

We can see that spine-1-1's adjacency to super-1-1 goes down:

<pre>
spine-1-1> <b>show interfaces</b>
+-----------+-------------------+-----------+-----------+-------------------+-------+
| Interface | Neighbor          | Neighbor  | Neighbor  | Time in           | Flaps |
| Name      | Name              | System ID | State     | State             |       |
+-----------+-------------------+-----------+-----------+-------------------+-------+
| if-101a   | leaf-1-1:if-1001a | 1001      | THREE_WAY | 0d 00h:03m:06.49s | 0     |
+-----------+-------------------+-----------+-----------+-------------------+-------+
| if-101b   | leaf-1-2:if-1002a | 1002      | THREE_WAY | 0d 00h:03m:06.37s | 0     |
+-----------+-------------------+-----------+-----------+-------------------+-------+
| if-101c   | leaf-1-3:if-1003a | 1003      | THREE_WAY | 0d 00h:03m:06.37s | 0     |
+-----------+-------------------+-----------+-----------+-------------------+-------+
| if-101d   |                   |           | ONE_WAY   | 0d 00h:00m:04.46s | 1     |
+-----------+-------------------+-----------+-----------+-------------------+-------+
| if-101e   | super-1-2:if-2a   | 2         | THREE_WAY | 0d 00h:03m:06.36s | 0     |
+-----------+-------------------+-----------+-----------+-------------------+-------+
</pre>

### Super-1-1

Similarly, on super-1-1 we can see that the adjacency to spine-1-1 is down:

<pre>
super-1-1> <b>show interfaces</b>
+-----------+-------------------+-----------+-----------+-------------------+-------+
| Interface | Neighbor          | Neighbor  | Neighbor  | Time in           | Flaps |
| Name      | Name              | System ID | State     | State             |       |
+-----------+-------------------+-----------+-----------+-------------------+-------+
| if-1a     |                   |           | ONE_WAY   | 0d 00h:00m:27.68s | 1     |
+-----------+-------------------+-----------+-----------+-------------------+-------+
| if-1b     | spine-2-1:if-104d | 104       | THREE_WAY | 0d 00h:03m:29.14s | 0     |
+-----------+-------------------+-----------+-----------+-------------------+-------+
| if-1c     | spine-3-1:if-107d | 107       | THREE_WAY | 0d 00h:03m:29.14s | 0     |
+-----------+-------------------+-----------+-----------+-------------------+-------+
| if-1d     | super-2-1:if-3d   | 3         | THREE_WAY | 0d 00h:03m:30.39s | 0     |
+-----------+-------------------+-----------+-----------+-------------------+-------+
| if-1e     | super-3-1:if-5e   | 5         | THREE_WAY | 0d 00h:03m:30.40s | 0     |
+-----------+-------------------+-----------+-----------+-------------------+-------+
</pre>

As a result, super-1-1 does not advertise an adjacency with spine-1-1 in its
South-Node-TIE (notice that neighbor system IDs 104 and 107 are present but neighbor system 
ID 101 is missing):

<pre>
super-1-1> <b>show tie-db direction south originator 1 tie-type node</b>
+-----------+------------+------+--------+--------+----------+-------------------------+
| Direction | Originator | Type | TIE Nr | Seq Nr | Lifetime | Contents                |
+-----------+------------+------+--------+--------+----------+-------------------------+
| South     | 1          | Node | 1      | 23     | 604523   | Name: super-1-1         |
|           |            |      |        |        |          | Level: 24               |
|           |            |      |        |        |          | Capabilities:           |
|           |            |      |        |        |          |   Flood reduction: True |
|           |            |      |        |        |          | Neighbor: 3             |
|           |            |      |        |        |          |   Level: 24             |
|           |            |      |        |        |          |   Cost: 1               |
|           |            |      |        |        |          |   Bandwidth: 100 Mbps   |
|           |            |      |        |        |          |   Link: 5-4             |
|           |            |      |        |        |          | Neighbor: 5             |
|           |            |      |        |        |          |   Level: 24             |
|           |            |      |        |        |          |   Cost: 1               |
|           |            |      |        |        |          |   Bandwidth: 100 Mbps   |
|           |            |      |        |        |          |   Link: 4-5             |
|           |            |      |        |        |          | Neighbor: 104           |
|           |            |      |        |        |          |   Level: 23             |
|           |            |      |        |        |          |   Cost: 1               |
|           |            |      |        |        |          |   Bandwidth: 100 Mbps   |
|           |            |      |        |        |          |   Link: 2-4             |
|           |            |      |        |        |          | Neighbor: 107           |
|           |            |      |        |        |          |   Level: 23             |
|           |            |      |        |        |          |   Cost: 1               |
|           |            |      |        |        |          |   Bandwidth: 100 Mbps   |
|           |            |      |        |        |          |   Link: 3-4             |
+-----------+------------+------+--------+--------+----------+-------------------------+
</pre>

As mentioned before, the broken link causes both super-1-1 to trigger negative disaggregation and
super-1-2 to trigger positive disaggregation. We will look at the positive disaggregation first and
at the negative disaggregation later because it will turn out to be more complex.

### Super-1-2

Breaking that single link causes super-1-2 to intiate positive disaggregation.
In the output of `show disaggregation` on super-1-2 we observe the following:

 1. Super-1-2 has discovered that super-1-1 is missing a south-bound adjancency to spine-1-1.

 2. Interface if-2a (which is connected to spine-1-1) is "partially connected" and we see that
    super-1-1 is the cause of the partial connectivity. This means that spine-1-1 is missing a
    north-bound adjacency to super-1-1.
 
 3. Super-1-2 is originating a positive disaggregation prefix for:
 
    a. 88.1.1.1/32, which is the loopback of spine-1-1.

    b. 88.0.1.1/32, 88.0.1.2/32, and 88.0.1.3/32, which are the loopbacks of leaf-1-1, leaf-1-2,
       and leaf-1-3. These are being positively disggregated because super-1-1 cannot reach these
       prefixes anymore. Prior to the failure super-1-1, being in plane-1, could only reach these
       leaves via spine-1-1, which is the top-of-pod node in plane 1.
 
<pre>
super-1-2> <b>show disaggregation</b>
Same Level Nodes:
+---------------+-------------+-----------------+-----------------+-------------+
| Same-Level    | North-bound | South-bound     | Missing         | Extra       |
| Node          | Adjacencies | Adjacencies     | South-bound     | South-bound |
|               |             |                 | Adjacencies     | Adjacencies |
+---------------+-------------+-----------------+-----------------+-------------+
| super-1-1 (1) |             | spine-2-1 (104) | spine-1-1 (101) |             |
|               |             | spine-3-1 (107) |                 |             |
+---------------+-------------+-----------------+-----------------+-------------+

Partially Connected Interfaces:
+-------+------------------------------------+
| Name  | Nodes Causing Partial Connectivity |
+-------+------------------------------------+
| if-2a | super-1-1 (1)                      |
+-------+------------------------------------+

Positive Disaggregation TIEs:
+-----------+------------+----------------+--------+--------+------------+-----------------------------+
| Direction | Originator | Type           | TIE Nr | Seq Nr | Lifetime   | Contents                    |
+-----------+------------+----------------+--------+--------+------------+-----------------------------+
| South     | 2          | Pos-Dis-Prefix | 3      | 4      | 4294966942 | Pos-Dis-Prefix: 88.0.1.1/32 |
|           |            |                |        |        |            |   Metric: 3                 |
|           |            |                |        |        |            | Pos-Dis-Prefix: 88.0.2.1/32 |
|           |            |                |        |        |            |   Metric: 3                 |
|           |            |                |        |        |            | Pos-Dis-Prefix: 88.0.3.1/32 |
|           |            |                |        |        |            |   Metric: 3                 |
|           |            |                |        |        |            | Pos-Dis-Prefix: 88.1.1.1/32 |
|           |            |                |        |        |            |   Metric: 2                 |
+-----------+------------+----------------+--------+--------+------------+-----------------------------+

Negative Disaggregation TIEs:
+-----------+------------+------+--------+--------+----------+----------+
| Direction | Originator | Type | TIE Nr | Seq Nr | Lifetime | Contents |
+-----------+------------+------+--------+--------+----------+----------+
</pre>

### Super-1-1

Now let's turn our eye towards super-1-1 and see how it triggers negative disaggregation.
From the output of the `show disaggregation` command we can conclude that:

 1. Super-1-1 has detected that super-1-2 has an extra south-bound adjacency. That is consistent
    with the fact that super-1-2 has initiated positive disaggregation.

 2. Super-1-1 itself does not intiate positive disaggregation, because none of the same-level-nodes
    have any missing south-bound adjacencies, or saying the same thing in a different way, none of
    the interfaces are partially connected.

 3. We do see, however, that super-1-1 initiates negative disaggregation for leaf-1-1 (88.0.1.1/32),
    leaf-1-2 (88.0.2.1/32), and leaf-1-3 (88.0.3.1.32), in other words, for all the leaves in pod-1.
    We will explain why in a second.
<pre>

super-1-1> <b>show disaggregation</b>
Same Level Nodes:
+---------------+-------------+-----------------+-------------+-----------------+
| Same-Level    | North-bound | South-bound     | Missing     | Extra           |
| Node          | Adjacencies | Adjacencies     | South-bound | South-bound     |
|               |             |                 | Adjacencies | Adjacencies     |
+---------------+-------------+-----------------+-------------+-----------------+
| super-1-2 (2) |             | spine-1-1 (101) |             | spine-1-1 (101) |
|               |             | spine-2-1 (104) |             |                 |
|               |             | spine-3-1 (107) |             |                 |
+---------------+-------------+-----------------+-------------+-----------------+

Partially Connected Interfaces:
+------+------------------------------------+
| Name | Nodes Causing Partial Connectivity |
+------+------------------------------------+

Positive Disaggregation TIEs:
+-----------+------------+------+--------+--------+----------+----------+
| Direction | Originator | Type | TIE Nr | Seq Nr | Lifetime | Contents |
+-----------+------------+------+--------+--------+----------+----------+

Negative Disaggregation TIEs:
+-----------+------------+----------------+--------+--------+----------+-----------------------------+
| Direction | Originator | Type           | TIE Nr | Seq Nr | Lifetime | Contents                    |
+-----------+------------+----------------+--------+--------+----------+-----------------------------+
| South     | 1          | Neg-Dis-Prefix | 5      | 1      | 602649   | Neg-Dis-Prefix: 88.0.1.1/32 |
|           |            |                |        |        |          |   Metric: 2147483647        |
|           |            |                |        |        |          | Neg-Dis-Prefix: 88.0.2.1/32 |
|           |            |                |        |        |          |   Metric: 2147483647        |
|           |            |                |        |        |          | Neg-Dis-Prefix: 88.0.3.1/32 |
|           |            |                |        |        |          |   Metric: 2147483647        |
+-----------+------------+----------------+--------+--------+----------+-----------------------------+
</pre>

The underlying reason for super-1-1 triggering negative disaggregation for all leaf prefixes
in pod-1 can be found in the output of `show spf`. The output of `show spf` is very
long; in the following example we have removed most output except the relevant rows plus some
context.

<pre>
super-1-1> <b>show spf</b>
SPF Statistics:
+---------------+-----+
| SPF Runs      | 34  |
+---------------+-----+
| SPF Deferrals | 118 |
+---------------+-----+

South SPF Destinations:
+-----------------+------+---------+-------------+------+--------------+---------------------+-------------------------------+
| Destination     | Cost | Is Leaf | Predecessor | Tags | Disaggregate | IPv4 Next-hops      | IPv6 Next-hops                |
|                 |      |         | System IDs  |      |              |                     |                               |
+-----------------+------+---------+-------------+------+--------------+---------------------+-------------------------------+
| 1 (super-1-1)   | 0    | False   |             |      |              |                     |                               |
+-----------------+------+---------+-------------+------+--------------+---------------------+-------------------------------+
.                 .      .         .             .                     .                     .                               .
+-----------------+------+---------+-------------+------+--------------+---------------------+-------------------------------+
| 1009 (leaf-3-3) | 2    | True    | 107         |      |              | if-1c 172.31.15.176 | if-1c fe80::84a:2ff:fe78:2746 |
+-----------------+------+---------+-------------+------+--------------+---------------------+-------------------------------+
| 88.0.4.1/32     | 3    | True    | 1004        |      |              | if-1b 172.31.15.176 | if-1b fe80::84a:2ff:fe78:2746 |
+-----------------+------+---------+-------------+------+--------------+---------------------+-------------------------------+
.                 .      .         .             .                     .                     .                               .
+-----------------+------+---------+-------------+------+--------------+---------------------+-------------------------------+
| 88.0.9.1/32     | 3    | True    | 1009        |      |              | if-1c 172.31.15.176 | if-1c fe80::84a:2ff:fe78:2746 |
+-----------------+------+---------+-------------+------+--------------+---------------------+-------------------------------+
| 88.1.4.1/32     | 2    | False   | 104         |      |              | if-1b 172.31.15.176 | if-1b fe80::84a:2ff:fe78:2746 |
+-----------------+------+---------+-------------+------+--------------+---------------------+-------------------------------+
| 88.1.7.1/32     | 2    | False   | 107         |      |              | if-1c 172.31.15.176 | if-1c fe80::84a:2ff:fe78:2746 |
+-----------------+------+---------+-------------+------+--------------+---------------------+-------------------------------+
| 88.2.1.1/32     | 1    | False   | 1           |      |              |                     |                               |
+-----------------+------+---------+-------------+------+--------------+---------------------+-------------------------------+

[...]

South SPF (with East-West Links) Destinations:
+-----------------+------+---------+-------------+------+--------------+---------------------+-------------------------------+
| Destination     | Cost | Is Leaf | Predecessor | Tags | Disaggregate | IPv4 Next-hops      | IPv6 Next-hops                |
|                 |      |         | System IDs  |      |              |                     |                               |
+-----------------+------+---------+-------------+------+--------------+---------------------+-------------------------------+
| 1 (super-1-1)   | 0    | False   |             |      |              |                     |                               |
+-----------------+------+---------+-------------+------+--------------+---------------------+-------------------------------+
.                 .      .         .             .                     .                     .                               .
+-----------------+------+---------+-------------+------+--------------+---------------------+-------------------------------+
| 1009 (leaf-3-3) | 2    | True    | 107         |      |              | if-1c 172.31.15.176 | if-1c fe80::84a:2ff:fe78:2746 |
+-----------------+------+---------+-------------+------+--------------+---------------------+-------------------------------+
| 88.0.1.1/32     | 4    | True    | 1001        |      | Negative     | if-1d 172.31.15.176 | if-1d fe80::84a:2ff:fe78:2746 |
|                 |      |         |             |      |              | if-1e 172.31.15.176 | if-1e fe80::84a:2ff:fe78:2746 |
+-----------------+------+---------+-------------+------+--------------+---------------------+-------------------------------+
| 88.0.2.1/32     | 4    | True    | 1002        |      | Negative     | if-1d 172.31.15.176 | if-1d fe80::84a:2ff:fe78:2746 |
|                 |      |         |             |      |              | if-1e 172.31.15.176 | if-1e fe80::84a:2ff:fe78:2746 |
+-----------------+------+---------+-------------+------+--------------+---------------------+-------------------------------+
| 88.0.3.1/32     | 4    | True    | 1003        |      | Negative     | if-1d 172.31.15.176 | if-1d fe80::84a:2ff:fe78:2746 |
|                 |      |         |             |      |              | if-1e 172.31.15.176 | if-1e fe80::84a:2ff:fe78:2746 |
+-----------------+------+---------+-------------+------+--------------+---------------------+-------------------------------+
| 88.0.4.1/32     | 3    | True    | 1004        |      |              | if-1b 172.31.15.176 | if-1b fe80::84a:2ff:fe78:2746 |
+-----------------+------+---------+-------------+------+--------------+---------------------+-------------------------------+
.                 .      .         .             .                     .                     .                               .
+-----------------+------+---------+-------------+------+--------------+---------------------+-------------------------------+
| 88.1.9.1/32     | 3    | False   | 109         |      |              | if-1e 172.31.15.176 | if-1e fe80::84a:2ff:fe78:2746 |
+-----------------+------+---------+-------------+------+--------------+---------------------+-------------------------------+
| 88.2.1.1/32     | 1    | False   | 1           |      |              |                     |                               |
+-----------------+------+---------+-------------+------+--------------+---------------------+-------------------------------+
| 88.2.3.1/32     | 2    | False   | 3           |      |              | if-1d 172.31.15.176 | if-1d fe80::84a:2ff:fe78:2746 |
+-----------------+------+---------+-------------+------+--------------+---------------------+-------------------------------+
| 88.2.5.1/32     | 2    | False   | 5           |      |              | if-1e 172.31.15.176 | if-1e fe80::84a:2ff:fe78:2746 |
+-----------------+------+---------+-------------+------+--------------+---------------------+-------------------------------+
</pre>

As we can see, the special south SPF that does include the east-west inter-plane links finds some
extra reachable destination prefixe that were not found by the normal south SPF that does not
include the east-west inter-plane links.

Some of those extra destinations prefixes were advertised by leaf nodes. In the above output there
are three such prefixes: 88.0.1.1/32 (leaf-1-1), 88.0.2.1/32 (leaf-1-2), and 88.0.3.1/32
(leaf-1-3). These are the prefixes for which super-1-1 has discovered that they are not reachable
from plane-1 (using only north-south links) but are reachable from at least one other plane. Hence,
super-1-1 will inititiate negative disaggregation for them. This is why they are markes as
negative in the disaggregate collumn of the `show spf` output.

The rest of these extra destinations were advertised by non-leaf nodes, in this case spine or
superspine nodes. These non-leaf extra prefixes are not negatively disaggregated.

### None of the negative disaggregation prefixes is propagated

First, we use `show disaggregation` to confirm that spine-3-1 has received both the positive and
the negative disaggrevation prefix TIEs:

<pre>
spine-3-1> <b>show disaggregation</b>
Same Level Nodes:
+-----------------+-------------+-----------------+-------------+-------------+
| Same-Level      | North-bound | South-bound     | Missing     | Extra       |
| Node            | Adjacencies | Adjacencies     | South-bound | South-bound |
|                 |             |                 | Adjacencies | Adjacencies |
+-----------------+-------------+-----------------+-------------+-------------+
| spine-3-2 (108) | (3)         | leaf-3-1 (1007) |             |             |
|                 | (4)         | leaf-3-2 (1008) |             |             |
|                 |             | leaf-3-3 (1009) |             |             |
+-----------------+-------------+-----------------+-------------+-------------+
| spine-3-3 (109) | (5)         | leaf-3-1 (1007) |             |             |
|                 | (6)         | leaf-3-2 (1008) |             |             |
|                 |             | leaf-3-3 (1009) |             |             |
+-----------------+-------------+-----------------+-------------+-------------+

Partially Connected Interfaces:
+------+------------------------------------+
| Name | Nodes Causing Partial Connectivity |
+------+------------------------------------+

Positive Disaggregation TIEs:
+-----------+------------+----------------+--------+--------+----------+-----------------------------+
| Direction | Originator | Type           | TIE Nr | Seq Nr | Lifetime | Contents                    |
+-----------+------------+----------------+--------+--------+----------+-----------------------------+
| South     | 2          | Pos-Dis-Prefix | 3      | 1      | 602588   | Pos-Dis-Prefix: 88.0.1.1/32 |
|           |            |                |        |        |          |   Metric: 3                 |
|           |            |                |        |        |          | Pos-Dis-Prefix: 88.0.2.1/32 |
|           |            |                |        |        |          |   Metric: 3                 |
|           |            |                |        |        |          | Pos-Dis-Prefix: 88.0.3.1/32 |
|           |            |                |        |        |          |   Metric: 3                 |
|           |            |                |        |        |          | Pos-Dis-Prefix: 88.1.1.1/32 |
|           |            |                |        |        |          |   Metric: 2                 |
+-----------+------------+----------------+--------+--------+----------+-----------------------------+

Negative Disaggregation TIEs:
+-----------+------------+----------------+--------+--------+----------+-----------------------------+
| Direction | Originator | Type           | TIE Nr | Seq Nr | Lifetime | Contents                    |
+-----------+------------+----------------+--------+--------+----------+-----------------------------+
| South     | 1          | Neg-Dis-Prefix | 5      | 1      | 602587   | Neg-Dis-Prefix: 88.0.1.1/32 |
|           |            |                |        |        |          |   Metric: 2147483647        |
|           |            |                |        |        |          | Neg-Dis-Prefix: 88.0.2.1/32 |
|           |            |                |        |        |          |   Metric: 2147483647        |
|           |            |                |        |        |          | Neg-Dis-Prefix: 88.0.3.1/32 |
|           |            |                |        |        |          |   Metric: 2147483647        |
+-----------+------------+----------------+--------+--------+----------+-----------------------------+
</pre>

One thing to notice is that neither the positive nor the negative disaggregation prefix TIE is
propagated. Or actually, re-originated might be a better word. If the disaggregation TIE was
being re-originated, we would have seens another TIE in the output of `show disaggregation`
with originated system ID 101 (the system ID of spine-1-1).

 * The positive disaggregation prefix TIE is not propagated because positive disaggregation prefix
   TIEs are simply never propagated.

 * The negative disaggregation prefix TIE is not propagated because it is only propagated when it is
   is received from all parent nodes, which is not the case here. The negative disaggregation
   prefixes are only received from parent super-1 and not (yet) from parent super-2.

## Populating the route tables on spine-3-1

We are interested to see what routes actually get installed in the route table as a result of
the negative disaggregation prefix advertised by super-1-1 and the positive disaggregation prefix
advertised by super-1-2. Apart from spine-1-1, there are two other nodes that are attached to
both super-1-1 and super-1-2, i.e. that are in plane-1, namely spine-2-1 and spine-3-1. We could
look at either, but we choose to look at spine-3-1.

We use `show spf` to see how these positive and negative disaggregation prefixes are used
in the shortest path first (SPF) calculation. We can see the the positive disaggregation prefix
gets precedence over the negative disaggregation prefix:

<pre>
spine-3-1> show spf direction north
North SPF Destinations:
+----------------------+------+---------+-------------+------+--------------+-----------------------+---------------------------------+
| Destination          | Cost | Is Leaf | Predecessor | Tags | Disaggregate | IPv4 Next-hops        | IPv6 Next-hops                  |
|                      |      |         | System IDs  |      |              |                       |                                 |
+----------------------+------+---------+-------------+------+--------------+-----------------------+---------------------------------+
| 1 (super-1-1)        | 1    | False   | 107         |      |              | if-107d 172.31.15.176 | if-107d fe80::84a:2ff:fe78:2746 |
+----------------------+------+---------+-------------+------+--------------+-----------------------+---------------------------------+
| 2 (super-1-2)        | 1    | False   | 107         |      |              | if-107e 172.31.15.176 | if-107e fe80::84a:2ff:fe78:2746 |
+----------------------+------+---------+-------------+------+--------------+-----------------------+---------------------------------+
| 107 (spine-3-1)      | 0    | False   |             |      |              |                       |                                 |
+----------------------+------+---------+-------------+------+--------------+-----------------------+---------------------------------+
| 0.0.0.0/0            | 2    | False   | 1           |      |              | if-107d 172.31.15.176 | if-107d fe80::84a:2ff:fe78:2746 |
|                      |      |         | 2           |      |              | if-107e 172.31.15.176 | if-107e fe80::84a:2ff:fe78:2746 |
+----------------------+------+---------+-------------+------+--------------+-----------------------+---------------------------------+
| 88.1.7.1/32          | 1    | False   | 107         |      |              |                       |                                 |
+----------------------+------+---------+-------------+------+--------------+-----------------------+---------------------------------+
| ::/0                 | 2    | False   | 1           |      |              | if-107d 172.31.15.176 | if-107d fe80::84a:2ff:fe78:2746 |
|                      |      |         | 2           |      |              | if-107e 172.31.15.176 | if-107e fe80::84a:2ff:fe78:2746 |
+----------------------+------+---------+-------------+------+--------------+-----------------------+---------------------------------+
| 88.0.1.1/32 (Disagg) | 4    | False   | 2           |      | Positive     | if-107e 172.31.15.176 | if-107e fe80::84a:2ff:fe78:2746 |
+----------------------+------+---------+-------------+------+--------------+-----------------------+---------------------------------+
| 88.0.2.1/32 (Disagg) | 4    | False   | 2           |      | Positive     | if-107e 172.31.15.176 | if-107e fe80::84a:2ff:fe78:2746 |
+----------------------+------+---------+-------------+------+--------------+-----------------------+---------------------------------+
| 88.0.3.1/32 (Disagg) | 4    | False   | 2           |      | Positive     | if-107e 172.31.15.176 | if-107e fe80::84a:2ff:fe78:2746 |
+----------------------+------+---------+-------------+------+--------------+-----------------------+---------------------------------+
| 88.1.1.1/32 (Disagg) | 3    | False   | 2           |      | Positive     | if-107e 172.31.15.176 | if-107e fe80::84a:2ff:fe78:2746 |
+----------------------+------+---------+-------------+------+--------------+-----------------------+---------------------------------+
</pre>

We use the `show routes` to view the RIB. We see the normal north-bound default route that ECMPs
over super-1 and super-2. 
We see more specific north-bound routes for spine-1-1 and all three leaves in pod-1 that sends
traffic only to super-1-2 and not super-1-1.
And finally, we see specific south-bound routes for three leaves in pod-2.

<pre>
spine-3-1> <b>show routes</b>
IPv4 Routes:
+-------------+-----------+----------+-----------+--------------+----------+
| Prefix      | Owner     | Next-hop | Next-hop  | Next-hop     | Next-hop |
|             |           | Type     | Interface | Address      | Weight   |
+-------------+-----------+----------+-----------+--------------+----------+
| 0.0.0.0/0   | North SPF | Positive | if-107d   | 172.31.60.58 |          |
|             |           | Positive | if-107e   | 172.31.60.58 |          |
+-------------+-----------+----------+-----------+--------------+----------+
| 88.0.1.1/32 | North SPF | Positive | if-107e   | 172.31.60.58 |          |
+-------------+-----------+----------+-----------+--------------+----------+
| 88.0.2.1/32 | North SPF | Positive | if-107e   | 172.31.60.58 |          |
+-------------+-----------+----------+-----------+--------------+----------+
| 88.0.3.1/32 | North SPF | Positive | if-107e   | 172.31.60.58 |          |
+-------------+-----------+----------+-----------+--------------+----------+
| 88.0.7.1/32 | South SPF | Positive | if-107a   | 172.31.60.58 |          |
+-------------+-----------+----------+-----------+--------------+----------+
| 88.0.8.1/32 | South SPF | Positive | if-107b   | 172.31.60.58 |          |
+-------------+-----------+----------+-----------+--------------+----------+
| 88.0.9.1/32 | South SPF | Positive | if-107c   | 172.31.60.58 |          |
+-------------+-----------+----------+-----------+--------------+----------+
| 89.0.1.1/32 | North SPF | Positive | if-107e   | 172.31.60.58 |          |
+-------------+-----------+----------+-----------+--------------+----------+

IPv6 Routes:
+--------+-----------+----------+-----------+--------------------------+----------+
| Prefix | Owner     | Next-hop | Next-hop  | Next-hop                 | Next-hop |
|        |           | Type     | Interface | Address                  | Weight   |
+--------+-----------+----------+-----------+--------------------------+----------+
| ::/0   | North SPF | Positive | if-107d   | fe80::cfc:a3ff:fe0e:36b4 |          |
|        |           | Positive | if-107e   | fe80::cfc:a3ff:fe0e:36b4 |          |
+--------+-----------+----------+-----------+--------------------------+----------+
</pre>

And finally, we use `show forwarding` to see the exact same routes in the FIB:

<pre>
spine-3-1> <b>show forwarding</b>
IPv4 Routes:
IPv4 Routes:
+-------------+----------+-----------+--------------+----------+
| Prefix      | Next-hop | Next-hop  | Next-hop     | Next-hop |
|             | Type     | Interface | Address      | Weight   |
+-------------+----------+-----------+--------------+----------+
| 0.0.0.0/0   | Positive | if-107d   | 172.31.60.58 |          |
|             | Positive | if-107e   | 172.31.60.58 |          |
+-------------+----------+-----------+--------------+----------+
| 88.0.1.1/32 | Positive | if-107e   | 172.31.60.58 |          |
+-------------+----------+-----------+--------------+----------+
| 88.0.2.1/32 | Positive | if-107e   | 172.31.60.58 |          |
+-------------+----------+-----------+--------------+----------+
| 88.0.3.1/32 | Positive | if-107e   | 172.31.60.58 |          |
+-------------+----------+-----------+--------------+----------+
| 88.0.7.1/32 | Positive | if-107a   | 172.31.60.58 |          |
+-------------+----------+-----------+--------------+----------+
| 88.0.8.1/32 | Positive | if-107b   | 172.31.60.58 |          |
+-------------+----------+-----------+--------------+----------+
| 88.0.9.1/32 | Positive | if-107c   | 172.31.60.58 |          |
+-------------+----------+-----------+--------------+----------+
| 89.0.1.1/32 | Positive | if-107e   | 172.31.60.58 |          |
+-------------+----------+-----------+--------------+----------+

IPv6 Routes:
+--------+----------+-----------+--------------------------+----------+
| Prefix | Next-hop | Next-hop  | Next-hop                 | Next-hop |
|        | Type     | Interface | Address                  | Weight   |
+--------+----------+-----------+--------------------------+----------+
| ::/0   | Positive | if-107d   | fe80::cfc:a3ff:fe0e:36b4 |          |
|        | Positive | if-107e   | fe80::cfc:a3ff:fe0e:36b4 |          |
+--------+----------+-----------+--------------------------+----------+
</pre>

## Breaking the second link to trigger only negative disaggregation

We proceed by breaking a second link in the fabric, this time the link between spine-1-1 and
super-1-2 as shown in figure 3 below.

Once again, this causes a rather complex sequence of events:

 1. Super-1-1 continues to trigger negative disaggregation as before.

 2. Super-1-2 switches from triggering positive disaggregation to negative disaggregation.
    Previously super-1-2 was still connected to pod-1, but not it is completely disconnected
    from pod-1.
 
![Topology Diagram](https://s3-us-west-2.amazonaws.com/brunorijsman-public/diagram-rift-neg-disagg-fg-orig-2-failures.png)

*Figure 3. Second failure between spine-1-1 and super-1-2.*

### Spine-1-1

The following command simulates a failure of the spine-1-1 to super-1-2 link:

<pre>
spine-1-1> <b>set interface if-101e failure failed</b>
</pre>

This causes something quite surprising to happen: it causes all adjacencies to go down, not just
the adjacency to super-1-1 (which was already down) and the adjacency to super-1-2 (which we just
brought down), but all south-bound adjacencies as well:

<pre>
spine-1-1> <b>show interfaces</b>
+-----------+----------+-----------+----------+-------------------+-------+
| Interface | Neighbor | Neighbor  | Neighbor | Time in           | Flaps |
| Name      | Name     | System ID | State    | State             |       |
+-----------+----------+-----------+----------+-------------------+-------+
| if-101a   |          |           | ONE_WAY  | 0d 00h:00m:02.14s | 1     |
+-----------+----------+-----------+----------+-------------------+-------+
| if-101b   |          |           | ONE_WAY  | 0d 00h:00m:02.13s | 1     |
+-----------+----------+-----------+----------+-------------------+-------+
| if-101c   |          |           | ONE_WAY  | 0d 00h:00m:02.11s | 1     |
+-----------+----------+-----------+----------+-------------------+-------+
| if-101d   |          |           | ONE_WAY  | 0d 00h:02m:02.07s | 1     |
+-----------+----------+-----------+----------+-------------------+-------+
| if-101e   |          |           | ONE_WAY  | 0d 00h:00m:03.07s | 1     |
+-----------+----------+-----------+----------+-------------------+-------+
</pre>

The reason for all adjacencies going down is that node spine-1-1 does not have a valid level,
as we can see in the output of `show node` (partial output):

<pre>
spine-1-1> show node
Node:
+---------------------------------------+------------------+
| Name                                  | spine-1-1        |
| Passive                               | False            |
| Running                               | True             |
| System ID                             | 101              |
| Configured Level                      | undefined        |
.                                       .                  .
| Level Value                           | undefined        |
.                                       .                  .
+---------------------------------------+------------------+

Received Offers:
+-----------+-----------+-------+-----------------+-----------+-------+------------+---------+-------------------+
| Interface | System ID | Level | Not A ZTP Offer | State     | Best  | Best 3-Way | Removed | Removed Reason    |
+-----------+-----------+-------+-----------------+-----------+-------+------------+---------+-------------------+
| if-101a   | 1001      | 0     | False           | ONE_WAY   | False | False      | True    | Level is leaf     |
+-----------+-----------+-------+-----------------+-----------+-------+------------+---------+-------------------+
| if-101b   | 1002      | 0     | False           | ONE_WAY   | False | False      | True    | Level is leaf     |
+-----------+-----------+-------+-----------------+-----------+-------+------------+---------+-------------------+
| if-101c   | 1003      | 0     | False           | ONE_WAY   | False | False      | True    | Level is leaf     |
+-----------+-----------+-------+-----------------+-----------+-------+------------+---------+-------------------+
| if-101d   | 1         | 24    | False           | THREE_WAY | False | False      | True    | Hold-time expired |
+-----------+-----------+-------+-----------------+-----------+-------+------------+---------+-------------------+
| if-101e   | 2         | 24    | False           | THREE_WAY | False | False      | True    | Hold-time expired |
+-----------+-----------+-------+-----------------+-----------+-------+------------+---------+-------------------+

...
</pre>

We see that node spine-1-1 does not have a configured level, so it relies on zero touch provisioning
(ZTP) to dynamically choose a level based on "offers" received from neighbors.

However, in this case, spine-1-1 is not able to dynamically choose a level. There are no offers
from north-bound neighbors because we just failed the last north-bound interfaces. And the offers
from the south-bound neighbors are not accepted because the RIFT rules say offers from leaves are
unacceptable. Indeed, all rows in the "Received Offers" table have "Removed" set to true.

The fact that spine-1-1 does not have a valid level causes the adjacencies to the leaves to go down.
This is confirmed in the output of `show interface ` <i>`interface-name`</i> (parial output):

<pre>
spine-1-1> show interface if-101a
Interface:
+--------------------------------------+------------------------------+
| Interface Name                       | if-101a                      |
.                                      .                              .
| State                                | ONE_WAY                      |
| Time in State                        | 0d 00h:00m:19.80s            |
| Flaps                                | 1                            |
| Received LIE Accepted or Rejected    | Rejected                     |
| Received LIE Accept or Reject Reason | My level is undefined        |
.                                      .                              .
+--------------------------------------+------------------------------+
</pre>

### Super-1-2

On super-1-2 the adjacency to spine-1-2 is down:

<pre>
super-1-2> <b>show interfaces</b>
+-----------+-------------------+-----------+-----------+-------------------+-------+
| Interface | Neighbor          | Neighbor  | Neighbor  | Time in           | Flaps |
| Name      | Name              | System ID | State     | State             |       |
+-----------+-------------------+-----------+-----------+-------------------+-------+
| if-2a     |                   |           | ONE_WAY   | 0d 00h:00m:44.56s | 1     |
+-----------+-------------------+-----------+-----------+-------------------+-------+
| if-2b     | spine-2-1:if-104e | 104       | THREE_WAY | 0d 00h:05m:45.05s | 0     |
+-----------+-------------------+-----------+-----------+-------------------+-------+
| if-2c     | spine-3-1:if-107e | 107       | THREE_WAY | 0d 00h:05m:45.04s | 0     |
+-----------+-------------------+-----------+-----------+-------------------+-------+
| if-2d     | super-2-2:if-4d   | 4         | THREE_WAY | 0d 00h:05m:46.30s | 0     |
+-----------+-------------------+-----------+-----------+-------------------+-------+
| if-2e     | super-3-2:if-6e   | 6         | THREE_WAY | 0d 00h:05m:46.31s | 0     |
+-----------+-------------------+-----------+-----------+-------------------+-------+
</pre>

Previously, super-1-2 was positively disaggregating the prefixes in pod-1. That was because
super-1-2 itself was still connected to pod-1, but super-1-2 has detected that super-1-1 was
no longer connected to pod-1.

However, at this point super-1-2 has completely lost all north-south connectivity with pod-1 and
the special SPF shows that super-1-2 can still reach pod-1 via other planes
crossing the inter-plane east-west links. Hence, super-1-1 stops triggering positive disaggregation
and starts triggering negative disaggregation for the leaf prefixes in pod-1:

<pre>
super-1-2> <b>show disaggregation</b>
Same Level Nodes:
+---------------+-------------+-----------------+-------------+-------------+
| Same-Level    | North-bound | South-bound     | Missing     | Extra       |
| Node          | Adjacencies | Adjacencies     | South-bound | South-bound |
|               |             |                 | Adjacencies | Adjacencies |
+---------------+-------------+-----------------+-------------+-------------+
| super-1-1 (1) |             | spine-2-1 (104) |             |             |
|               |             | spine-3-1 (107) |             |             |
+---------------+-------------+-----------------+-------------+-------------+

Partially Connected Interfaces:
+------+------------------------------------+
| Name | Nodes Causing Partial Connectivity |
+------+------------------------------------+

Positive Disaggregation TIEs:
+-----------+------------+----------------+--------+--------+----------+----------+
| Direction | Originator | Type           | TIE Nr | Seq Nr | Lifetime | Contents |
+-----------+------------+----------------+--------+--------+----------+----------+
| South     | 2          | Pos-Dis-Prefix | 3      | 2      | 603937   |          |
+-----------+------------+----------------+--------+--------+----------+----------+

Negative Disaggregation TIEs:
+-----------+------------+----------------+--------+--------+----------+-----------------------------+
| Direction | Originator | Type           | TIE Nr | Seq Nr | Lifetime | Contents                    |
+-----------+------------+----------------+--------+--------+----------+-----------------------------+
| South     | 2          | Neg-Dis-Prefix | 5      | 1      | 603937   | Neg-Dis-Prefix: 88.0.1.1/32 |
|           |            |                |        |        |          |   Metric: 2147483647        |
|           |            |                |        |        |          | Neg-Dis-Prefix: 88.0.2.1/32 |
|           |            |                |        |        |          |   Metric: 2147483647        |
|           |            |                |        |        |          | Neg-Dis-Prefix: 88.0.3.1/32 |
|           |            |                |        |        |          |   Metric: 2147483647        |
+-----------+------------+----------------+--------+--------+----------+-----------------------------+
</pre>

### Super-1-1

Previously, super-1-1 was triggering negative disaggregation for the leaf prefixes in pod-1.
Nothing changes in this respect; super-1-1 continues to do so:

<pre>
super-1-1> <b>show disaggregation</b>
Same Level Nodes:
+---------------+-------------+-----------------+-------------+-------------+
| Same-Level    | North-bound | South-bound     | Missing     | Extra       |
| Node          | Adjacencies | Adjacencies     | South-bound | South-bound |
|               |             |                 | Adjacencies | Adjacencies |
+---------------+-------------+-----------------+-------------+-------------+
| super-1-2 (2) |             | spine-2-1 (104) |             |             |
|               |             | spine-3-1 (107) |             |             |
+---------------+-------------+-----------------+-------------+-------------+

Partially Connected Interfaces:
+------+------------------------------------+
| Name | Nodes Causing Partial Connectivity |
+------+------------------------------------+

Positive Disaggregation TIEs:
+-----------+------------+------+--------+--------+----------+----------+
| Direction | Originator | Type | TIE Nr | Seq Nr | Lifetime | Contents |
+-----------+------------+------+--------+--------+----------+----------+

Negative Disaggregation TIEs:
+-----------+------------+----------------+--------+--------+----------+-----------------------------+
| Direction | Originator | Type           | TIE Nr | Seq Nr | Lifetime | Contents                    |
+-----------+------------+----------------+--------+--------+----------+-----------------------------+
| South     | 1          | Neg-Dis-Prefix | 5      | 1      | 558984   | Neg-Dis-Prefix: 88.0.1.1/32 |
|           |            |                |        |        |          |   Metric: 2147483647        |
|           |            |                |        |        |          | Neg-Dis-Prefix: 88.0.2.1/32 |
|           |            |                |        |        |          |   Metric: 2147483647        |
|           |            |                |        |        |          | Neg-Dis-Prefix: 88.0.3.1/32 |
|           |            |                |        |        |          |   Metric: 2147483647        |
+-----------+------------+----------------+--------+--------+----------+-----------------------------+
</pre>

### Now the negative disaggregation prefixes are propagated

### Spine-3-1

Previously we had noted that spine-3-1 received negative disaggregation prefix TIEs but did not
propagate them. Now, the situation has changed, as shown in figure 4 below:

![Topology Diagram](https://s3-us-west-2.amazonaws.com/brunorijsman-public/diagram-rift-neg-disagg-fg-prop-2-failures.png)

*Figure 4. Propagation of negative disaggregation prefix TIEs.*

The `show disaggregation` shows that spine-3-1 has received the same negative disaggregation
prefixes from super-1 and super-2, i.e. from both of its parents nodes. This causes spine-3-1
to propagate (or rather re-originate) the negativev disaggregation prefixes in its own TIE
(the one with originator system ID 107).

<pre>
spine-3-1> <b>show disaggregation</b>
Same Level Nodes:
+-----------------+-------------+-----------------+-------------+-------------+
| Same-Level      | North-bound | South-bound     | Missing     | Extra       |
| Node            | Adjacencies | Adjacencies     | South-bound | South-bound |
|                 |             |                 | Adjacencies | Adjacencies |
+-----------------+-------------+-----------------+-------------+-------------+
| spine-3-2 (108) | (3)         | leaf-3-1 (1007) |             |             |
|                 | (4)         | leaf-3-2 (1008) |             |             |
|                 |             | leaf-3-3 (1009) |             |             |
+-----------------+-------------+-----------------+-------------+-------------+
| spine-3-3 (109) | (5)         | leaf-3-1 (1007) |             |             |
|                 | (6)         | leaf-3-2 (1008) |             |             |
|                 |             | leaf-3-3 (1009) |             |             |
+-----------------+-------------+-----------------+-------------+-------------+

Partially Connected Interfaces:
+------+------------------------------------+
| Name | Nodes Causing Partial Connectivity |
+------+------------------------------------+

Positive Disaggregation TIEs:
+-----------+------------+----------------+--------+--------+----------+----------+
| Direction | Originator | Type           | TIE Nr | Seq Nr | Lifetime | Contents |
+-----------+------------+----------------+--------+--------+----------+----------+
| South     | 2          | Pos-Dis-Prefix | 3      | 2      | 601516   |          |
+-----------+------------+----------------+--------+--------+----------+----------+

Negative Disaggregation TIEs:
+-----------+------------+----------------+--------+--------+----------+-----------------------------+
| Direction | Originator | Type           | TIE Nr | Seq Nr | Lifetime | Contents                    |
+-----------+------------+----------------+--------+--------+----------+-----------------------------+
| South     | 1          | Neg-Dis-Prefix | 5      | 1      | 557048   | Neg-Dis-Prefix: 88.0.1.1/32 |
|           |            |                |        |        |          |   Metric: 2147483647        |
|           |            |                |        |        |          | Neg-Dis-Prefix: 88.0.2.1/32 |
|           |            |                |        |        |          |   Metric: 2147483647        |
|           |            |                |        |        |          | Neg-Dis-Prefix: 88.0.3.1/32 |
|           |            |                |        |        |          |   Metric: 2147483647        |
+-----------+------------+----------------+--------+--------+----------+-----------------------------+
| South     | 2          | Neg-Dis-Prefix | 5      | 1      | 601516   | Neg-Dis-Prefix: 88.0.1.1/32 |
|           |            |                |        |        |          |   Metric: 2147483647        |
|           |            |                |        |        |          | Neg-Dis-Prefix: 88.0.2.1/32 |
|           |            |                |        |        |          |   Metric: 2147483647        |
|           |            |                |        |        |          | Neg-Dis-Prefix: 88.0.3.1/32 |
|           |            |                |        |        |          |   Metric: 2147483647        |
+-----------+------------+----------------+--------+--------+----------+-----------------------------+
| South     | 107        | Neg-Dis-Prefix | 5      | 1      | 601517   | Neg-Dis-Prefix: 88.0.1.1/32 |
|           |            |                |        |        |          |   Metric: 2147483647        |
|           |            |                |        |        |          | Neg-Dis-Prefix: 88.0.2.1/32 |
|           |            |                |        |        |          |   Metric: 2147483647        |
|           |            |                |        |        |          | Neg-Dis-Prefix: 88.0.3.1/32 |
|           |            |                |        |        |          |   Metric: 2147483647        |
+-----------+------------+----------------+--------+--------+----------+-----------------------------+
</pre>

## Populating the route tables on leaf-3-1

We skip looking at the route table of spine-3-1 for now (we will come back to it); we look at the
route table of leaf-3-1 first.

The `show routes` command shows that leaf-3-1 has:

 1. A north-bound default route that ECMPs over all three spines in pod-3.
 
 2. Three north-bound specific routes for the leaves in pod-1, each a negative next-hop for
    spine-3-1.

<pre>
leaf-3-1> show routes
IPv4 Routes:
+-------------+-----------+---------------------------------+
| Prefix      | Owner     | Next-hops                       |
+-------------+-----------+---------------------------------+
| 0.0.0.0/0   | North SPF | if-1007a 172.31.15.176          |
|             |           | if-1007b 172.31.15.176          |
|             |           | if-1007c 172.31.15.176          |
+-------------+-----------+---------------------------------+
| 88.0.1.1/32 | North SPF | Negative if-1007a 172.31.15.176 |
+-------------+-----------+---------------------------------+
| 88.0.2.1/32 | North SPF | Negative if-1007a 172.31.15.176 |
+-------------+-----------+---------------------------------+
| 88.0.3.1/32 | North SPF | Negative if-1007a 172.31.15.176 |
+-------------+-----------+---------------------------------+

IPv6 Routes:
+--------+-----------+----------------------------------+
| Prefix | Owner     | Next-hops                        |
+--------+-----------+----------------------------------+
| ::/0   | North SPF | if-1007a fe80::84a:2ff:fe78:2746 |
|        |           | if-1007b fe80::84a:2ff:fe78:2746 |
|        |           | if-1007c fe80::84a:2ff:fe78:2746 |
+--------+-----------+----------------------------------+
</pre>

The `show forwarding` command shows that the negative next-hop (spine-3-1) has been translated
into complementary positive next-hops (spine-3-2 and spine-3-3):

<pre>
leaf-3-1> <b>show forwarding</b>
IPv4 Routes:
+-------------+------------------------+
| Prefix      | Next-hops              |
+-------------+------------------------+
| 0.0.0.0/0   | if-1007a 172.31.15.176 |
|             | if-1007c 172.31.15.176 |
|             | if-1007b 172.31.15.176 |
+-------------+------------------------+
| 88.0.1.1/32 | if-1007b 172.31.15.176 |
|             | if-1007c 172.31.15.176 |
+-------------+------------------------+
| 88.0.2.1/32 | if-1007b 172.31.15.176 |
|             | if-1007c 172.31.15.176 |
+-------------+------------------------+
| 88.0.3.1/32 | if-1007b 172.31.15.176 |
|             | if-1007c 172.31.15.176 |
+-------------+------------------------+

IPv6 Routes:
+--------+----------------------------------+
| Prefix | Next-hops                        |
+--------+----------------------------------+
| ::/0   | if-1007a fe80::84a:2ff:fe78:2746 |
|        | if-1007c fe80::84a:2ff:fe78:2746 |
|        | if-1007b fe80::84a:2ff:fe78:2746 |
+--------+----------------------------------+
</pre>

## Populating the route tables on spine-3-1

We now return to spine-3-1 to look at its route tables.

The `show routes` command shows that spine-3-1 has:

 1. A north-bound default route that ECMPs over both superspines in plane-1.
 
 2. Three north-bound specific routes for the leaves in pod-1, each with to negative next-hops
    for super-1-1 and super-1-2.

 3. Three south-bound specific routes for the leaves in pod-3.

<pre>
spine-3-1> <b>show routes</b>
IPv4 Routes:
+-------------+-----------+--------------------------------+
| Prefix      | Owner     | Next-hops                      |
+-------------+-----------+--------------------------------+
| 0.0.0.0/0   | North SPF | if-107d 172.31.15.176          |
|             |           | if-107e 172.31.15.176          |
+-------------+-----------+--------------------------------+
| 88.0.1.1/32 | North SPF | Negative if-107d 172.31.15.176 |
|             |           | Negative if-107e 172.31.15.176 |
+-------------+-----------+--------------------------------+
| 88.0.2.1/32 | North SPF | Negative if-107d 172.31.15.176 |
|             |           | Negative if-107e 172.31.15.176 |
+-------------+-----------+--------------------------------+
| 88.0.3.1/32 | North SPF | Negative if-107d 172.31.15.176 |
|             |           | Negative if-107e 172.31.15.176 |
+-------------+-----------+--------------------------------+
| 88.0.7.1/32 | South SPF | if-107a 172.31.15.176          |
+-------------+-----------+--------------------------------+
| 88.0.8.1/32 | South SPF | if-107b 172.31.15.176          |
+-------------+-----------+--------------------------------+
| 88.0.9.1/32 | South SPF | if-107c 172.31.15.176          |
+-------------+-----------+--------------------------------+

IPv6 Routes:
+--------+-----------+---------------------------------+
| Prefix | Owner     | Next-hops                       |
+--------+-----------+---------------------------------+
| ::/0   | North SPF | if-107d fe80::84a:2ff:fe78:2746 |
|        |           | if-107e fe80::84a:2ff:fe78:2746 |
+--------+-----------+---------------------------------+
</pre>

When spine-3-1 translates the negative next-hops super-1-1 and super-1-2 to complementary positive
next-hops, it ends up with an empty set of next-hops. This is because the encompassing parent route
(the default route in this case) has precisely super-1-1 and super-1-2 as its ECMP next-hops.
Indeed, the `show forwarding` command shows that the routes to the leaves in pod-1 don't have
any next-hops, which means that they are essentially discard routes.

<pre>
spine-3-1> <b>show forwarding</b>
IPv4 Routes:
+-------------+-----------------------+
| Prefix      | Next-hops             |
+-------------+-----------------------+
| 0.0.0.0/0   | if-107e 172.31.15.176 |
|             | if-107d 172.31.15.176 |
+-------------+-----------------------+
| 88.0.1.1/32 |                       |
+-------------+-----------------------+
| 88.0.2.1/32 |                       |
+-------------+-----------------------+
| 88.0.3.1/32 |                       |
+-------------+-----------------------+
| 88.0.7.1/32 | if-107a 172.31.15.176 |
+-------------+-----------------------+
| 88.0.8.1/32 | if-107b 172.31.15.176 |
+-------------+-----------------------+
| 88.0.9.1/32 | if-107c 172.31.15.176 |
+-------------+-----------------------+

IPv6 Routes:
+--------+---------------------------------+
| Prefix | Next-hops                       |
+--------+---------------------------------+
| ::/0   | if-107e fe80::84a:2ff:fe78:2746 |
|        | if-107d fe80::84a:2ff:fe78:2746 |
+--------+---------------------------------+
</pre>
