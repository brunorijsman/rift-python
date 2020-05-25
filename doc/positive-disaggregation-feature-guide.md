# Positive Disaggregation Feature Guide

We assume you have already read the
[Disaggregation Feature Guide](disaggregation_feature_guide.md),
which describes what automatic disaggregation is, how automatic disaggregation works from a RIFT
protocol point of view, and what the the difference between positive disaggregation and negative
disaggregation is.
This feature guide describes the nuts and bolts of using the RIFT-Python command line interface
(CLI) to see positive disagregation in action.
There is a separate
[Negative Disaggregation Feature Guide](negatite_disaggregation_feature_guide.md).

## Example network

The examples in this guide are based on the topology shown in figure 1 below.

![Topology Diagram](https://s3-us-west-2.amazonaws.com/brunorijsman-public/diagram_clos_3pod_3leaf_3spine_4super.png)

*Figure 1. Topology used in this feature guide.*

## Generating and starting the topology

The above topology is describe by meta-topology `meta_topology/clos_3plane_3pod_3leaf_3spine_6super.yaml`.
Use the following commands to convert the meta-topology to topology and to start it in
single-process mode:

<pre>
(env) $ <b>tools/config_generator.py meta_topology/clos_3pod_3leaf_3spine_4super.yaml generated.yaml</b>
(env) $ <b>python rift --interactive generated.yaml</b>
</pre>

## The state of the fabric before triggering positive disaggregation

Let us first look at the network before we break any links and before any positive disaggregation
happens.

### Leaf-1-1

On leaf-1-1 all adjacencies are up:

<pre>
leaf-1-1> <b>show interfaces</b>
+-----------+-------------------+-----------+-----------+
| Interface | Neighbor          | Neighbor  | Neighbor  |
| Name      | Name              | System ID | State     |
+-----------+-------------------+-----------+-----------+
| if-1001a  | spine-1-1:if-101a | 101       | THREE_WAY |
+-----------+-------------------+-----------+-----------+
| if-1001b  | spine-1-2:if-102a | 102       | THREE_WAY |
+-----------+-------------------+-----------+-----------+
| if-1001c  | spine-1-3:if-103a | 103       | THREE_WAY |
+-----------+-------------------+-----------+-----------+
</pre>

Note: we don't spell out the `set node `<i>`node-name`</i> commands that are needed to go to right
node that is implied by the CLI prompt in the example outputs.

### Spine-1-1

On the other side, i.e. on spine-1-1, the adjacency to leaf-1-1 is up as well:

<pre>
spine-1-1> <b>show interfaces</b>
+-----------+-------------------+-----------+-----------+
| Interface | Neighbor          | Neighbor  | Neighbor  |
| Name      | Name              | System ID | State     |
+-----------+-------------------+-----------+-----------+
| if-101a   | leaf-1-1:if-1001a | 1001      | THREE_WAY |
+-----------+-------------------+-----------+-----------+
| if-101b   | leaf-1-2:if-1002a | 1002      | THREE_WAY |
+-----------+-------------------+-----------+-----------+
| if-101c   | leaf-1-3:if-1003a | 1003      | THREE_WAY |
+-----------+-------------------+-----------+-----------+
| if-101d   | super-1:if-1a     | 1         | THREE_WAY |
+-----------+-------------------+-----------+-----------+
| if-101e   | super-2:if-2a     | 2         | THREE_WAY |
+-----------+-------------------+-----------+-----------+
| if-101f   | super-3:if-3a     | 3         | THREE_WAY |
+-----------+-------------------+-----------+-----------+
| if-101g   | super-4:if-4a     | 4         | THREE_WAY |
+-----------+-------------------+-----------+-----------+
</pre>

### Spine-1-2

We issue the `show disaggregation` command on anyone of the spine nodes in pod-1 to get a summary of
what is happening in terms of dissaggregation in pod-1. In this example we choose node super-1-2
and observe that:

 1. There are no missing south-bound adjacencies. This means none of the other spine nodes in pod-1
    have any missing (or extra, for that matter) south-bound adjacency as compared to spine-1-2.
    All the spines in pod-1 have the same set of south-bound adjacencies.

 2. Spine-1-2 does not have any partially connected south-bound interface. That means that every
    south-bound leaf neighbor of spine-1-2 is also fully connected to all the other spines in the
    pod.

 3. Spine-1-2 is currently not originating any positive disaggregation prefixes.

 4. Spine-1-2 currently does not have any positivate disaggregation prefixes from other nodes.
    Interestingly, spine-1-1 does have two empty positive disaggregation prefix TIEs from nodes
    super-3 (system ID 3) and super-4 (system ID 4). What this means is that those nodes sent
    a positive disaggregation TIE at some point in the past and then flushed it. This is consistent
    with the fact that both empty TIEs have sequence number 2. It is not unusual for transitory
    disaggregation to occur while the topology is still partially connected during initial
    convergence.

 5. Spine-1-2 does not have any negative disaggregation prefixes (neither originated nor received)
    in its TIE database. Negative disaggregation is discussed in a separate feature guide.

<pre>
spine-1-2> <b>show disaggregation</b>
Same Level Nodes:
+-----------------+-------------+-----------------+-------------+-------------+
| Same-Level      | North-bound | South-bound     | Missing     | Extra       |
| Node            | Adjacencies | Adjacencies     | South-bound | South-bound |
|                 |             |                 | Adjacencies | Adjacencies |
+-----------------+-------------+-----------------+-------------+-------------+
| spine-1-1 (101) | super-1 (1) | leaf-1-1 (1001) |             |             |
|                 | super-2 (2) | leaf-1-2 (1002) |             |             |
|                 | super-3 (3) | leaf-1-3 (1003) |             |             |
|                 | super-4 (4) |                 |             |             |
+-----------------+-------------+-----------------+-------------+-------------+
| spine-1-3 (103) | super-1 (1) | leaf-1-1 (1001) |             |             |
|                 | super-2 (2) | leaf-1-2 (1002) |             |             |
|                 | super-3 (3) | leaf-1-3 (1003) |             |             |
|                 | super-4 (4) |                 |             |             |
+-----------------+-------------+-----------------+-------------+-------------+

Partially Connected Interfaces:
+------+------------------------------------+
| Name | Nodes Causing Partial Connectivity |
+------+------------------------------------+

Positive Disaggregation TIEs:
+-----------+------------+----------------+--------+--------+----------+----------+
| Direction | Originator | Type           | TIE Nr | Seq Nr | Lifetime | Contents |
+-----------+------------+----------------+--------+--------+----------+----------+
| South     | 3          | Pos-Dis-Prefix | 3      | 2      | 604673   |          |
+-----------+------------+----------------+--------+--------+----------+----------+
| South     | 4          | Pos-Dis-Prefix | 3      | 2      | 604673   |          |
+-----------+------------+----------------+--------+--------+----------+----------+

Negative Disaggregation TIEs:
+-----------+------------+------+--------+--------+----------+----------+
| Direction | Originator | Type | TIE Nr | Seq Nr | Lifetime | Contents |
+-----------+------------+------+--------+--------+----------+----------+
</pre>

### Leaf-1-2

Since leaf-1-2 can reach leaf-1-1 over any of the three spine nodes in pod-1, leaf-1-2 only
has a north-bound default route with ECMP next-hops over spine-1-1, spine-1-2, and spine-1-3.

<pre>
leaf-1-2> <b>show routes</b>
IPv4 Routes:
+-----------+-----------+------------------------+
| Prefix    | Owner     | Next-hops              |
+-----------+-----------+------------------------+
| 0.0.0.0/0 | North SPF | if-1002a 172.31.15.176 |
|           |           | if-1002b 172.31.15.176 |
|           |           | if-1002c 172.31.15.176 |
+-----------+-----------+------------------------+

IPv6 Routes:
+--------+-----------+----------------------------------+
| Prefix | Owner     | Next-hops                        |
+--------+-----------+----------------------------------+
| ::/0   | North SPF | if-1002a fe80::84a:2ff:fe78:2746 |
|        |           | if-1002b fe80::84a:2ff:fe78:2746 |
|        |           | if-1002c fe80::84a:2ff:fe78:2746 |
+--------+-----------+----------------------------------+
</pre>

We do not see any /32 routes on leaf-1-2 because there is no disaggregation happening.

Just for completness sake, we can also verify that there are no disaggregation prefix TIEs on
leaf-1-2. Note that we do not see the empty positive disaggregation prefix TIEs from the superspine
nodes here because they are not propagated by the spine nodes.

<pre>
leaf-1-2> <b>show disaggregation</b>
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

## Breaking a link to trigger positive disaggregation within a pod

First we break the link between leaf-1-1 and spine-1-1 as shown in figure 2 below, which triggers
positive disaggregation in pod-1.

After the failure, leaf-1-2 and leaf-1-3 can no longer rely on their north-bound default route to
reach leaf-1-1 because its ECMP next-hop set includes spine-1-1 which cannot reach leaf-1-1. 
Positive disaggregation fixes the issue by causing spine-1-2 and spine-1-3 to advertise a
host-specific route for leaf-1-1.

![Topology Diagram](https://s3-us-west-2.amazonaws.com/brunorijsman-public/diagram_clos_3pod_3leaf_3spine_4super_intra_pod_1_failure.png)

*Figure 2. Failure causing intra-pod positive disaggregation in pod-1.*

### Leaf-1-1

The following command simulates a failure of the leaf-1-1 to spine-1-1 link:

<pre>
leaf-1-1> <b>set interface if-1001a failure failed</b>
</pre>

We can see that leaf-1-1's adjacency to spine-1-1 goes down:

<pre>
leaf-1-1> <b>show interfaces</b>
+-----------+-------------------+-----------+-----------+
| Interface | Neighbor          | Neighbor  | Neighbor  |
| Name      | Name              | System ID | State     |
+-----------+-------------------+-----------+-----------+
| if-1001a  |                   |           | ONE_WAY   |
+-----------+-------------------+-----------+-----------+
| if-1001b  | spine-1-2:if-102a | 102       | THREE_WAY |
+-----------+-------------------+-----------+-----------+
| if-1001c  | spine-1-3:if-103a | 103       | THREE_WAY |
+-----------+-------------------+-----------+-----------+
</pre>

### Spine-1-1

Similarly, on spine-1-1 we can see that the adjacency to leaf-1-1 is down:

<pre>
spine-1-1> <b>show interfaces</b>
+-----------------+--------------------------+-----------+-----------+
| Interface       | Neighbor                 | Neighbor  | Neighbor  |
| Name            | Name                     | System ID | State     |
+-----------------+--------------------------+-----------+-----------+
| veth-101a-1001a |                          |           | ONE_WAY   |
+-----------------+--------------------------+-----------+-----------+
| veth-101b-1002a | leaf-1-2:veth-1002a-101b | 1002      | THREE_WAY |
+-----------------+--------------------------+-----------+-----------+
| veth-101c-1003a | leaf-1-3:veth-1003a-101c | 1003      | THREE_WAY |
+-----------------+--------------------------+-----------+-----------+
| veth-101d-1a    | super-1:veth-1a-101d     | 1         | THREE_WAY |
+-----------------+--------------------------+-----------+-----------+
| veth-101e-2a    | super-2:veth-2a-101e     | 2         | THREE_WAY |
+-----------------+--------------------------+-----------+-----------+
| veth-101f-3a    | super-3:veth-3a-101f     | 3         | THREE_WAY |
+-----------------+--------------------------+-----------+-----------+
| veth-101g-4a    | super-4:veth-4a-101g     | 4         | THREE_WAY |
+-----------------+--------------------------+-----------+-----------+
</pre>
As a result, spine-1-1 does not advertise an adjacency with leaf-1-1 in its
South-Node-TIE (notice that neighbor system IDs 1002 and 1003 are present but neighbor system 
ID 1001 is missing):

<pre>
spine-1-1> <b>show tie-db direction south originator 101</b>
+-----------+------------+--------+--------+--------+----------+-------------------------+
| Direction | Originator | Type   | TIE Nr | Seq Nr | Lifetime | Contents                |
+-----------+------------+--------+--------+--------+----------+-------------------------+
| South     | 101        | Node   | 1      | 9      | 604583   | Name: spine-1-1         |
|           |            |        |        |        |          | Level: 23               |
|           |            |        |        |        |          | Capabilities:           |
|           |            |        |        |        |          |   Flood reduction: True |
|           |            |        |        |        |          | Neighbor: 1             |
|           |            |        |        |        |          |   Level: 24             |
|           |            |        |        |        |          |   Cost: 1               |
|           |            |        |        |        |          |   Bandwidth: 100 Mbps   |
|           |            |        |        |        |          |   Link: 4-1             |
|           |            |        |        |        |          | Neighbor: 2             |
|           |            |        |        |        |          |   Level: 24             |
|           |            |        |        |        |          |   Cost: 1               |
|           |            |        |        |        |          |   Bandwidth: 100 Mbps   |
|           |            |        |        |        |          |   Link: 5-1             |
|           |            |        |        |        |          | Neighbor: 3             |
|           |            |        |        |        |          |   Level: 24             |
|           |            |        |        |        |          |   Cost: 1               |
|           |            |        |        |        |          |   Bandwidth: 100 Mbps   |
|           |            |        |        |        |          |   Link: 6-1             |
|           |            |        |        |        |          | Neighbor: 4             |
|           |            |        |        |        |          |   Level: 24             |
|           |            |        |        |        |          |   Cost: 1               |
|           |            |        |        |        |          |   Bandwidth: 100 Mbps   |
|           |            |        |        |        |          |   Link: 7-1             |
|           |            |        |        |        |          | Neighbor: 1002          |
|           |            |        |        |        |          |   Level: 0              |
|           |            |        |        |        |          |   Cost: 1               |
|           |            |        |        |        |          |   Bandwidth: 100 Mbps   |
|           |            |        |        |        |          |   Link: 2-1             |
|           |            |        |        |        |          | Neighbor: 1003          |
|           |            |        |        |        |          |   Level: 0              |
|           |            |        |        |        |          |   Cost: 1               |
|           |            |        |        |        |          |   Bandwidth: 100 Mbps   |
|           |            |        |        |        |          |   Link: 3-1             |
+-----------+------------+--------+--------+--------+----------+-------------------------+
| South     | 101        | Prefix | 2      | 1      | 600946   | Prefix: 0.0.0.0/0       |
|           |            |        |        |        |          |   Metric: 1             |
|           |            |        |        |        |          | Prefix: ::/0            |
|           |            |        |        |        |          |   Metric: 1             |
+-----------+------------+--------+--------+--------+----------+-------------------------+
</pre>


### Spine-1-2

In the output of `show disaggregation` on spine-1-2 we observe the following:

 1. Spine-1-2 has discovered that spine-1-1 is missing a south-bound adjancency to leaf-1-1.

 2. Interface if-102a (which is connected to leaf-1-1) is "partially connected" and we see that
    spine-1-1 is the cause of the partial connectivity. This means that leaf-1-1 is missing a
    north-bound adjacency to spine-1-1.
 
 3. Spine-1-2 is originating a positive disaggregation prefix for 88.0.1.1/32, which is the loopback
    of leaf-1-1.
 
<pre>
spine-1-2> <b>show disaggregation</b>
Same Level Nodes:
+-----------------+-------------+-----------------+-----------------+-------------+
| Same-Level      | North-bound | South-bound     | Missing         | Extra       |
| Node            | Adjacencies | Adjacencies     | South-bound     | South-bound |
|                 |             |                 | Adjacencies     | Adjacencies |
+-----------------+-------------+-----------------+-----------------+-------------+
| spine-1-1 (101) | super-1 (1) | leaf-1-2 (1002) | leaf-1-1 (1001) |             |
|                 | super-2 (2) | leaf-1-3 (1003) |                 |             |
|                 | super-3 (3) |                 |                 |             |
|                 | super-4 (4) |                 |                 |             |
+-----------------+-------------+-----------------+-----------------+-------------+
| spine-1-3 (103) | super-1 (1) | leaf-1-1 (1001) |                 |             |
|                 | super-2 (2) | leaf-1-2 (1002) |                 |             |
|                 | super-3 (3) | leaf-1-3 (1003) |                 |             |
|                 | super-4 (4) |                 |                 |             |
+-----------------+-------------+-----------------+-----------------+-------------+

Partially Connected Interfaces:
+---------+------------------------------------+
| Name    | Nodes Causing Partial Connectivity |
+---------+------------------------------------+
| if-102a | spine-1-1 (101)                    |
+---------+------------------------------------+

Positive Disaggregation TIEs:
+-----------+------------+----------------+--------+--------+----------+-----------------------------+
| Direction | Originator | Type           | TIE Nr | Seq Nr | Lifetime | Contents                    |
+-----------+------------+----------------+--------+--------+----------+-----------------------------+
| South     | 3          | Pos-Dis-Prefix | 3      | 2      | 600827   |                             |
+-----------+------------+----------------+--------+--------+----------+-----------------------------+
| South     | 4          | Pos-Dis-Prefix | 3      | 2      | 600827   |                             |
+-----------+------------+----------------+--------+--------+----------+-----------------------------+
| South     | 102        | Pos-Dis-Prefix | 3      | 1      | 604437   | Pos-Dis-Prefix: 88.0.1.1/32 |
|           |            |                |        |        |          |   Metric: 2                 |
+-----------+------------+----------------+--------+--------+----------+-----------------------------+

Negative Disaggregation TIEs:
+-----------+------------+------+--------+--------+----------+----------+
| Direction | Originator | Type | TIE Nr | Seq Nr | Lifetime | Contents |
+-----------+------------+------+--------+--------+----------+----------+
</pre>

### Leaf-1-3

In the output of `show disaggregation` on leaf-1-3 we observe that leaf-1-3 has received positive
disaggregation prefix 88.0.1.1/32 (which is the loopback of leaf-1-1) from both spine-1-2
(system ID 102) and spine-1-3 (system ID 103).

<pre>
leaf-1-3> <b>show disaggregation</b>
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
+-----------+------------+----------------+--------+--------+----------+-----------------------------+
| Direction | Originator | Type           | TIE Nr | Seq Nr | Lifetime | Contents                    |
+-----------+------------+----------------+--------+--------+----------+-----------------------------+
| South     | 102        | Pos-Dis-Prefix | 3      | 1      | 604008   | Pos-Dis-Prefix: 88.0.1.1/32 |
|           |            |                |        |        |          |   Metric: 2                 |
+-----------+------------+----------------+--------+--------+----------+-----------------------------+
| South     | 103        | Pos-Dis-Prefix | 3      | 1      | 604008   | Pos-Dis-Prefix: 88.0.1.1/32 |
|           |            |                |        |        |          |   Metric: 2                 |
+-----------+------------+----------------+--------+--------+----------+-----------------------------+

Negative Disaggregation TIEs:
+-----------+------------+------+--------+--------+----------+----------+
| Direction | Originator | Type | TIE Nr | Seq Nr | Lifetime | Contents |
+-----------+------------+------+--------+--------+----------+----------+
</pre>

This causes leaf-1-3 to install a more specific route to leaf-1-1 (88.0.1.1/32) in its route table
with spine-1-2 and spine-1-3 (but not spine-1-1) as ECMP next-hops.
The default route 0.0.0.0/0 with all three spines as ECMP next-hops is still there for all other
traffic.

<pre>
leaf-1-3> <b>show route</b>
IPv4 Routes:
+-------------+-----------+------------------------+
| Prefix      | Owner     | Next-hops              |
+-------------+-----------+------------------------+
| 0.0.0.0/0   | North SPF | if-1003a 172.31.15.176 |
|             |           | if-1003b 172.31.15.176 |
|             |           | if-1003c 172.31.15.176 |
+-------------+-----------+------------------------+
| 88.0.1.1/32 | North SPF | if-1003b 172.31.15.176 |
|             |           | if-1003c 172.31.15.176 |
+-------------+-----------+------------------------+

IPv6 Routes:
+--------+-----------+----------------------------------+
| Prefix | Owner     | Next-hops                        |
+--------+-----------+----------------------------------+
| ::/0   | North SPF | if-1003a fe80::84a:2ff:fe78:2746 |
|        |           | if-1003b fe80::84a:2ff:fe78:2746 |
|        |           | if-1003c fe80::84a:2ff:fe78:2746 |
+--------+-----------+----------------------------------+
</pre>

## Repairing the link to end positive disaggregation within a pod

### Leaf-1-1

We now repair the link from leaf-1-1 to spine-1-1:

<pre>
leaf-1-1> <b>set interface if-1001a failure ok</b>
</pre>

The adjacency comes back up:

<pre>
leaf-1-1> <b>show interfaces</b>
+-----------+-------------------+-----------+-----------+
| Interface | Neighbor          | Neighbor  | Neighbor  |
| Name      | Name              | System ID | State     |
+-----------+-------------------+-----------+-----------+
| if-1001a  | spine-1-1:if-101a | 101       | THREE_WAY |
+-----------+-------------------+-----------+-----------+
| if-1001b  | spine-1-2:if-102a | 102       | THREE_WAY |
+-----------+-------------------+-----------+-----------+
| if-1001c  | spine-1-3:if-103a | 103       | THREE_WAY |
+-----------+-------------------+-----------+-----------+
</pre>

### Leaf-1-3

On leaf-1-3 we can see that the positive disaggregation stopped (both positive disaggregation prefix
TIEs have been flushed):

<pre>
leaf-1-3> <b>show disaggregation</b>
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
+-----------+------------+----------------+--------+--------+----------+----------+
| Direction | Originator | Type           | TIE Nr | Seq Nr | Lifetime | Contents |
+-----------+------------+----------------+--------+--------+----------+----------+
| South     | 102        | Pos-Dis-Prefix | 3      | 2      | 604699   |          |
+-----------+------------+----------------+--------+--------+----------+----------+
| South     | 103        | Pos-Dis-Prefix | 3      | 2      | 604699   |          |
+-----------+------------+----------------+--------+--------+----------+----------+

Negative Disaggregation TIEs:
+-----------+------------+------+--------+--------+----------+----------+
| Direction | Originator | Type | TIE Nr | Seq Nr | Lifetime | Contents |
+-----------+------------+------+--------+--------+----------+----------+
</pre>

And we can observe that the more specific route to leaf-1-1 has been removed, leaving only the
default route:

<pre>
leaf-1-3> <b>show routes</b>
IPv4 Routes:
+-----------+-----------+------------------------+
| Prefix    | Owner     | Next-hops              |
+-----------+-----------+------------------------+
| 0.0.0.0/0 | North SPF | if-1003a 172.31.15.176 |
|           |           | if-1003b 172.31.15.176 |
|           |           | if-1003c 172.31.15.176 |
+-----------+-----------+------------------------+

IPv6 Routes:
+--------+-----------+----------------------------------+
| Prefix | Owner     | Next-hops                        |
+--------+-----------+----------------------------------+
| ::/0   | North SPF | if-1003a fe80::84a:2ff:fe78:2746 |
|        |           | if-1003b fe80::84a:2ff:fe78:2746 |
|        |           | if-1003c fe80::84a:2ff:fe78:2746 |
+--------+-----------+----------------------------------+
</pre>

## Breaking a spine and a superspine link to cause limited positive disaggregation

Now we break the link between spine-1-1 and super-1 as shown in figure 3 below:

![Topology Diagram](https://s3-us-west-2.amazonaws.com/brunorijsman-public/diagram_clos_3pod_3leaf_3spine_4super_inter_pod_1_failure.png)

*Figure 3. Failure between a spine and superspine causing limited positive disaggregation.*

### Spine-1-1

On spine-1-1 we cause a (simulated) failure of the link to super-1:

<pre>
spine-1-1> <b>set interface if-101d failure failed</b>
</pre>

The adjacency goes down:

<pre>
spine-1-1> <b>show interfaces</b>
+-----------+-------------------+-----------+-----------+
| Interface | Neighbor          | Neighbor  | Neighbor  |
| Name      | Name              | System ID | State     |
+-----------+-------------------+-----------+-----------+
| if-101a   | leaf-1-1:if-1001a | 1001      | THREE_WAY |
+-----------+-------------------+-----------+-----------+
| if-101b   | leaf-1-2:if-1002a | 1002      | THREE_WAY |
+-----------+-------------------+-----------+-----------+
| if-101c   | leaf-1-3:if-1003a | 1003      | THREE_WAY |
+-----------+-------------------+-----------+-----------+
| if-101d   |                   |           | ONE_WAY   |
+-----------+-------------------+-----------+-----------+
| if-101e   | super-2:if-2a     | 2         | THREE_WAY |
+-----------+-------------------+-----------+-----------+
| if-101f   | super-3:if-3a     | 3         | THREE_WAY |
+-----------+-------------------+-----------+-----------+
| if-101g   | super-4:if-4a     | 4         | THREE_WAY |
+-----------+-------------------+-----------+-----------+
</pre>

### Super-2

Now, let's see whether or not super-2 initiates positive disaggregation:

<pre>
super-2> <b>show disaggregation</b>
Same Level Nodes:
+-------------+-------------+-----------------+-----------------+-------------+
| Same-Level  | North-bound | South-bound     | Missing         | Extra       |
| Node        | Adjacencies | Adjacencies     | South-bound     | South-bound |
|             |             |                 | Adjacencies     | Adjacencies |
+-------------+-------------+-----------------+-----------------+-------------+
| super-1 (1) |             | spine-1-2 (102) | spine-1-1 (101) |             |
|             |             | spine-1-3 (103) |                 |             |
|             |             | spine-2-1 (104) |                 |             |
|             |             | spine-2-2 (105) |                 |             |
|             |             | spine-2-3 (106) |                 |             |
|             |             | spine-3-1 (107) |                 |             |
|             |             | spine-3-2 (108) |                 |             |
|             |             | spine-3-3 (109) |                 |             |
+-------------+-------------+-----------------+-----------------+-------------+
| super-3 (3) |             | spine-1-1 (101) |                 |             |
|             |             | spine-1-2 (102) |                 |             |
|             |             | spine-1-3 (103) |                 |             |
|             |             | spine-2-1 (104) |                 |             |
|             |             | spine-2-2 (105) |                 |             |
|             |             | spine-2-3 (106) |                 |             |
|             |             | spine-3-1 (107) |                 |             |
|             |             | spine-3-2 (108) |                 |             |
|             |             | spine-3-3 (109) |                 |             |
+-------------+-------------+-----------------+-----------------+-------------+
| super-4 (4) |             | spine-1-1 (101) |                 |             |
|             |             | spine-1-2 (102) |                 |             |
|             |             | spine-1-3 (103) |                 |             |
|             |             | spine-2-1 (104) |                 |             |
|             |             | spine-2-2 (105) |                 |             |
|             |             | spine-2-3 (106) |                 |             |
|             |             | spine-3-1 (107) |                 |             |
|             |             | spine-3-2 (108) |                 |             |
|             |             | spine-3-3 (109) |                 |             |
+-------------+-------------+-----------------+-----------------+-------------+

Partially Connected Interfaces:
+-------+------------------------------------+
| Name  | Nodes Causing Partial Connectivity |
+-------+------------------------------------+
| if-2a | super-1 (1)                        |
+-------+------------------------------------+

Positive Disaggregation TIEs:
+-----------+------------+----------------+--------+--------+----------+-----------------------------+
| Direction | Originator | Type           | TIE Nr | Seq Nr | Lifetime | Contents                    |
+-----------+------------+----------------+--------+--------+----------+-----------------------------+
| South     | 2          | Pos-Dis-Prefix | 3      | 1      | 604758   | Pos-Dis-Prefix: 88.1.1.1/32 |
|           |            |                |        |        |          |   Metric: 2                 |
+-----------+------------+----------------+--------+--------+----------+-----------------------------+

Negative Disaggregation TIEs:
+-----------+------------+------+--------+--------+----------+----------+
| Direction | Originator | Type | TIE Nr | Seq Nr | Lifetime | Contents |
+-----------+------------+------+--------+--------+----------+----------+
</pre>

This is quite interesting (well, at least I think so)! We can see that:

 1. Super-2 has discovered that super-1 is missing a south-bound adjancency to spine-1-1.

 2. Interface if-2a (which is connected to spine-1-1) is "partially connected" and we see that
    super-1 is the cause of the partial connectivity. This means that spine-1-1 is missing a
    north-bound adjacency to super-1.
 
 3. Super-2 is originating a positive disaggregation prefix for 88.1.1.1/32, which is the loopback
    of spine-1-1.

 4. Note, however, that super-2 is **not** originating any positive disaggregation prefixes for any
    of the leaves leaf-1-1, leaf-1-2, or leaf-1-3. The reason for this is:

    a. Super-2 knows that those leaves can be reached via spine-1-1 (it knows this because
       of the next-hops of its own routes to those leaves).

    b. And yes, it is true that super-1 cannot reach those leaves via spine-1-1 anymore.

    c. But super-2 also knows that those same leaves can also be reached via spine-1-2 or spine-1-3
       (once again, by looking at its own next-hops).

    d. And, super-2 knows that super-1 can still reach spine-1-2 and spine-1-3.

    e. Super-2 concludes that spine-1 can still reach the leaves, and there is no reason to trigger
       positive disaggregation for the leaves.

### Spine-3-3

Over in pod-3, when we look at the route table on spine-3-3, we can see that:

 1. Spine-3-3 has a north-bound default route that ECMPs the traffic over all 4 superspines
    in the fabric.

 2. Spine-3-3 has a single north-bound host-specific route for spine-1-1 (88.1.1.1/32) which ECMPs
    the traffic over only 3 superspines (it avoids super-1). This is the result of positive
    disaggregation. Note that there are no positive disaggregation IPv6 prefixes because we did
    not configure any IPv6 loopbacks in this topology.

 3. Spine-3-3 has 3 south-bound host-specific routes to leaf-3-1, leaf-3-2, leaf-3-3. Even though
    these are host-specific routes, it has nothing to do with disaggreation. The south-bound routes
    are always specific routes.

<pre>
spine-3-3> <b>show routes</b>
IPv4 Routes:
+-------------+-----------+-----------------------+
| Prefix      | Owner     | Next-hops             |
+-------------+-----------+-----------------------+
| 0.0.0.0/0   | North SPF | if-109d 172.31.15.176 |
|             |           | if-109e 172.31.15.176 |
|             |           | if-109f 172.31.15.176 |
|             |           | if-109g 172.31.15.176 |
+-------------+-----------+-----------------------+
| 88.0.7.1/32 | South SPF | if-109a 172.31.15.176 |
+-------------+-----------+-----------------------+
| 88.0.8.1/32 | South SPF | if-109b 172.31.15.176 |
+-------------+-----------+-----------------------+
| 88.0.9.1/32 | South SPF | if-109c 172.31.15.176 |
+-------------+-----------+-----------------------+
| 88.1.1.1/32 | North SPF | if-109e 172.31.15.176 |
|             |           | if-109f 172.31.15.176 |
|             |           | if-109g 172.31.15.176 |
+-------------+-----------+-----------------------+

IPv6 Routes:
+--------+-----------+---------------------------------+
| Prefix | Owner     | Next-hops                       |
+--------+-----------+---------------------------------+
| ::/0   | North SPF | if-109d fe80::84a:2ff:fe78:2746 |
|        |           | if-109e fe80::84a:2ff:fe78:2746 |
|        |           | if-109f fe80::84a:2ff:fe78:2746 |
|        |           | if-109g fe80::84a:2ff:fe78:2746 |
+--------+-----------+---------------------------------+
</pre>

### Leaf-3-3

When we look at the route table on leaf-3-3, we can see that:

 1. Leaf-3-3 has a north-bound default route that ECMPs the traffic over all 3 spines in the pod.

 2. Unlike what we saw on spine-3-3, there are no north-bound positive disaggregation prefixes. This
    is because positive disaggregation TIEs are never propagated.

 3. Unlike what we saw on spine-3-3, there are no south-bound specific prefixes. This is because
    there is nothing south of the leaf nodes.

<pre>
leaf-3-3> <b>show routes</b>
IPv4 Routes:
+-----------+-----------+------------------------+
| Prefix    | Owner     | Next-hops              |
+-----------+-----------+------------------------+
| 0.0.0.0/0 | North SPF | if-1009a 172.31.15.176 |
|           |           | if-1009b 172.31.15.176 |
|           |           | if-1009c 172.31.15.176 |
+-----------+-----------+------------------------+

IPv6 Routes:
+--------+-----------+----------------------------------+
| Prefix | Owner     | Next-hops                        |
+--------+-----------+----------------------------------+
| ::/0   | North SPF | if-1009a fe80::84a:2ff:fe78:2746 |
|        |           | if-1009b fe80::84a:2ff:fe78:2746 |
|        |           | if-1009c fe80::84a:2ff:fe78:2746 |
+--------+-----------+----------------------------------+
</pre>

## Completely disconnecting a pod from one superspine to cause full positive disaggregation

Now we two more links (one on spine-1-2 and one on spine-1-3) to complete disconnect pod-1 from
super-1 as shown in figure 4 below.
But pod-1 is still connected to the other superspine nodes: super-2, super-3 and super-4.

![Topology Diagram](https://brunorijsman-public.s3-us-west-2.amazonaws.com/diagram_clos_3pod_3leaf_3spine_4super_inter_pod_3_failures.png)

*Figure 4. Completely disconnecting a pod from one superspine to cause full positive disaggregation.*

### Spine-1-2

On spine-1-2 we cause a (simulated) failure of the link to super-1:

<pre>
spine-1-2> <b>set interface if-102d failure failed</b>
</pre>

### Spine-1-3

Similarly, on spine-1-3 we cause a (simulated) failure of the link to super-1:

<pre>
spine-1-3> <b>set interface if-103d failure failed</b>
</pre>

### Super-1

On super-1, we can see that all south-bound adjacencies to pod-1 have gone down:

<pre>
super-1> <b>show interfaces</b>
+-----------+-------------------+-----------+-----------+
| Interface | Neighbor          | Neighbor  | Neighbor  |
| Name      | Name              | System ID | State     |
+-----------+-------------------+-----------+-----------+
| if-1a     |                   |           | ONE_WAY   |
+-----------+-------------------+-----------+-----------+
| if-1b     |                   |           | ONE_WAY   |
+-----------+-------------------+-----------+-----------+
| if-1c     |                   |           | ONE_WAY   |
+-----------+-------------------+-----------+-----------+
| if-1d     | spine-2-1:if-104d | 104       | THREE_WAY |
+-----------+-------------------+-----------+-----------+
| if-1e     | spine-2-2:if-105d | 105       | THREE_WAY |
+-----------+-------------------+-----------+-----------+
| if-1f     | spine-2-3:if-106d | 106       | THREE_WAY |
+-----------+-------------------+-----------+-----------+
| if-1g     | spine-3-1:if-107d | 107       | THREE_WAY |
+-----------+-------------------+-----------+-----------+
| if-1h     | spine-3-2:if-108d | 108       | THREE_WAY |
+-----------+-------------------+-----------+-----------+
| if-1i     | spine-3-3:if-109d | 109       | THREE_WAY |
+-----------+-------------------+-----------+-----------+
</pre>

### Super-2

Once again, we go back to super-2 to see what it does in terms of positive disaggregation:

<pre>
super-2> <b>show disaggregation</b>
Same Level Nodes:
+-------------+-------------+-----------------+-----------------+-------------+
| Same-Level  | North-bound | South-bound     | Missing         | Extra       |
| Node        | Adjacencies | Adjacencies     | South-bound     | South-bound |
|             |             |                 | Adjacencies     | Adjacencies |
+-------------+-------------+-----------------+-----------------+-------------+
| super-1 (1) |             | spine-2-1 (104) | spine-1-1 (101) |             |
|             |             | spine-2-2 (105) | spine-1-2 (102) |             |
|             |             | spine-2-3 (106) | spine-1-3 (103) |             |
|             |             | spine-3-1 (107) |                 |             |
|             |             | spine-3-2 (108) |                 |             |
|             |             | spine-3-3 (109) |                 |             |
+-------------+-------------+-----------------+-----------------+-------------+
| super-3 (3) |             | spine-1-1 (101) |                 |             |
|             |             | spine-1-2 (102) |                 |             |
|             |             | spine-1-3 (103) |                 |             |
|             |             | spine-2-1 (104) |                 |             |
|             |             | spine-2-2 (105) |                 |             |
|             |             | spine-2-3 (106) |                 |             |
|             |             | spine-3-1 (107) |                 |             |
|             |             | spine-3-2 (108) |                 |             |
|             |             | spine-3-3 (109) |                 |             |
+-------------+-------------+-----------------+-----------------+-------------+
| super-4 (4) |             | spine-1-1 (101) |                 |             |
|             |             | spine-1-2 (102) |                 |             |
|             |             | spine-1-3 (103) |                 |             |
|             |             | spine-2-1 (104) |                 |             |
|             |             | spine-2-2 (105) |                 |             |
|             |             | spine-2-3 (106) |                 |             |
|             |             | spine-3-1 (107) |                 |             |
|             |             | spine-3-2 (108) |                 |             |
|             |             | spine-3-3 (109) |                 |             |
+-------------+-------------+-----------------+-----------------+-------------+

Partially Connected Interfaces:
+-------+------------------------------------+
| Name  | Nodes Causing Partial Connectivity |
+-------+------------------------------------+
| if-2a | super-1 (1)                        |
+-------+------------------------------------+
| if-2b | super-1 (1)                        |
+-------+------------------------------------+
| if-2c | super-1 (1)                        |
+-------+------------------------------------+

Positive Disaggregation TIEs:
+-----------+------------+----------------+--------+--------+----------+-----------------------------+
| Direction | Originator | Type           | TIE Nr | Seq Nr | Lifetime | Contents                    |
+-----------+------------+----------------+--------+--------+----------+-----------------------------+
| South     | 2          | Pos-Dis-Prefix | 3      | 6      | 604755   | Pos-Dis-Prefix: 88.0.1.1/32 |
|           |            |                |        |        |          |   Metric: 3                 |
|           |            |                |        |        |          | Pos-Dis-Prefix: 88.0.2.1/32 |
|           |            |                |        |        |          |   Metric: 3                 |
|           |            |                |        |        |          | Pos-Dis-Prefix: 88.0.3.1/32 |
|           |            |                |        |        |          |   Metric: 3                 |
|           |            |                |        |        |          | Pos-Dis-Prefix: 88.1.1.1/32 |
|           |            |                |        |        |          |   Metric: 2                 |
|           |            |                |        |        |          | Pos-Dis-Prefix: 88.1.2.1/32 |
|           |            |                |        |        |          |   Metric: 2                 |
|           |            |                |        |        |          | Pos-Dis-Prefix: 88.1.3.1/32 |
|           |            |                |        |        |          |   Metric: 2                 |
+-----------+------------+----------------+--------+--------+----------+-----------------------------+

Negative Disaggregation TIEs:
+-----------+------------+------+--------+--------+----------+----------+
| Direction | Originator | Type | TIE Nr | Seq Nr | Lifetime | Contents |
+-----------+------------+------+--------+--------+----------+----------+
</pre>

Now there is more positive disaggregation going on. We can see that:

 1. Super-2 has discovered that super-1 is missing a south-bound adjancency to spine-1-1, spine-1-2,
    and spine-1-3.

 2. Interface if-2a (to spine-1-1), if-2b (to spine-1-2), and if-2c (to spine-1-3) are all
    "partially connected" and we see that super-1 is the cause of the partial connectivity in each
    case. This means that spine-1-1, spine-1-2, and spine-1-3 are all missing their north-bound
    adjacency to super-1.
 
 3. Super-2 is originating a positive disaggregation prefixes for all addresses in pod-1: all
    spine prefixes in pod-1 and all leaf prefixes in pod-1. This was not happening before we failed
    the additional two interfaces. It is happening now because super-1 is now completely
    disconnected from pod-1.

Note that super-3 and super-4 are both doing the exact same thing as super-2.

### Spine-3-3

Over in pod-3, when we look at the route table on spine-3-3, we can see all the north-bound positive
disaggregation prefixes from pod-1 (in addition to to normal north-bound default route and the normal
south-bound routes).

<pre>
spine-3-3> <b>show routes</b>
IPv4 Routes:
+-------------+-----------+-----------------------+
| Prefix      | Owner     | Next-hops             |
+-------------+-----------+-----------------------+
| 0.0.0.0/0   | North SPF | if-109d 172.31.15.176 |
|             |           | if-109e 172.31.15.176 |
|             |           | if-109f 172.31.15.176 |
|             |           | if-109g 172.31.15.176 |
+-------------+-----------+-----------------------+
| 88.0.1.1/32 | North SPF | if-109e 172.31.15.176 |
|             |           | if-109f 172.31.15.176 |
|             |           | if-109g 172.31.15.176 |
+-------------+-----------+-----------------------+
| 88.0.2.1/32 | North SPF | if-109e 172.31.15.176 |
|             |           | if-109f 172.31.15.176 |
|             |           | if-109g 172.31.15.176 |
+-------------+-----------+-----------------------+
| 88.0.3.1/32 | North SPF | if-109e 172.31.15.176 |
|             |           | if-109f 172.31.15.176 |
|             |           | if-109g 172.31.15.176 |
+-------------+-----------+-----------------------+
| 88.0.7.1/32 | South SPF | if-109a 172.31.15.176 |
+-------------+-----------+-----------------------+
| 88.0.8.1/32 | South SPF | if-109b 172.31.15.176 |
+-------------+-----------+-----------------------+
| 88.0.9.1/32 | South SPF | if-109c 172.31.15.176 |
+-------------+-----------+-----------------------+
| 88.1.1.1/32 | North SPF | if-109e 172.31.15.176 |
|             |           | if-109f 172.31.15.176 |
|             |           | if-109g 172.31.15.176 |
+-------------+-----------+-----------------------+
| 88.1.2.1/32 | North SPF | if-109e 172.31.15.176 |
|             |           | if-109f 172.31.15.176 |
|             |           | if-109g 172.31.15.176 |
+-------------+-----------+-----------------------+
| 88.1.3.1/32 | North SPF | if-109e 172.31.15.176 |
|             |           | if-109f 172.31.15.176 |
|             |           | if-109g 172.31.15.176 |
+-------------+-----------+-----------------------+

IPv6 Routes:
+--------+-----------+---------------------------------+
| Prefix | Owner     | Next-hops                       |
+--------+-----------+---------------------------------+
| ::/0   | North SPF | if-109d fe80::84a:2ff:fe78:2746 |
|        |           | if-109e fe80::84a:2ff:fe78:2746 |
|        |           | if-109f fe80::84a:2ff:fe78:2746 |
|        |           | if-109g fe80::84a:2ff:fe78:2746 |
+--------+-----------+---------------------------------+
</pre>

### Leaf-3-3

As before, the route table on leaf-3-3 only contains a north-bound default route (for the same
reasons as before):

<pre>
leaf-3-3> <b>show routes</b>
IPv4 Routes:
+-----------+-----------+------------------------+
| Prefix    | Owner     | Next-hops              |
+-----------+-----------+------------------------+
| 0.0.0.0/0 | North SPF | if-1009a 172.31.15.176 |
|           |           | if-1009b 172.31.15.176 |
|           |           | if-1009c 172.31.15.176 |
+-----------+-----------+------------------------+

IPv6 Routes:
+--------+-----------+----------------------------------+
| Prefix | Owner     | Next-hops                        |
+--------+-----------+----------------------------------+
| ::/0   | North SPF | if-1009a fe80::84a:2ff:fe78:2746 |
|        |           | if-1009b fe80::84a:2ff:fe78:2746 |
|        |           | if-1009c fe80::84a:2ff:fe78:2746 |
+--------+-----------+----------------------------------+
</pre>
