# Positive Disaggregation Feature Guide

## Example network

The examples in this chapter are based on the following topology. We will cause routes to be 
positively disaggregated in pod-1 by breaking the red link.

![Topology Diagram](https://s3-us-west-2.amazonaws.com/brunorijsman-public/diagram_clos_3pod_3leaf_3spine_4super.png)

## Before breaking the link: no positive disaggregation occurs

Let us first look at the network before we break the red link and before any positive disaggregation
happens.


On leaf-1-1 all adjacencies are up:

<pre>
leaf-1-1> <b>show interfaces</b>
+-----------------+---------------------------+-----------+-----------+
| Interface       | Neighbor                  | Neighbor  | Neighbor  |
| Name            | Name                      | System ID | State     |
+-----------------+---------------------------+-----------+-----------+
| veth-1001a-101a | spine-1-1:veth-101a-1001a | 101       | THREE_WAY |
+-----------------+---------------------------+-----------+-----------+
| veth-1001b-102a | spine-1-2:veth-102a-1001b | 102       | THREE_WAY |
+-----------------+---------------------------+-----------+-----------+
| veth-1001c-103a | spine-1-3:veth-103a-1001c | 103       | THREE_WAY |
+-----------------+---------------------------+-----------+-----------+
</pre>

Since leaf-1-2 can reach leaf-1-1 over any of the three spine nodes in pod-1, leaf-1-2 only
has a north-bound default route with an ECMP next-hop over spine-1-1, spine-1-2, and spine-1-3.

<pre>
leaf-1-2> <b>show route</b>
IPv4 Routes:
+-----------+-----------+-----------------------------+
| Prefix    | Owner     | Next-hops                   |
+-----------+-----------+-----------------------------+
| 0.0.0.0/0 | North SPF | veth-1002a-101b 99.7.8.8    |
|           |           | veth-1002b-102b 99.9.10.10  |
|           |           | veth-1002c-103b 99.11.12.12 |
+-----------+-----------+-----------------------------+

IPv6 Routes:
+--------+-----------+-------------------------------------------+
| Prefix | Owner     | Next-hops                                 |
+--------+-----------+-------------------------------------------+
| ::/0   | North SPF | veth-1002a-101b fe80::f0d0:f7ff:fe9a:3c1c |
|        |           | veth-1002b-102b fe80::c038:98ff:fe9b:1499 |
|        |           | veth-1002c-103b fe80::38ac:10ff:fe48:310f |
+--------+-----------+-------------------------------------------+
</pre>

We do not see any /32 routes on leaf-1-2 because there is no disaggregation happening.

## After breaking the link: positive disaggregation occurs

We break the link marked in red in the above diagram.

As a result, leaf-1-1 is partially connected: it has an adjacencies with spine-1-2 and spine-1-3
but it is missing an adjacency with spine-1-1:

<pre>
leaf-1-1> <b>show interfaces</b>
+-----------------+---------------------------+-----------+-----------+
| Interface       | Neighbor                  | Neighbor  | Neighbor  |
| Name            | Name                      | System ID | State     |
+-----------------+---------------------------+-----------+-----------+
| veth-1001a-101a |                           |           | ONE_WAY   |
+-----------------+---------------------------+-----------+-----------+
| veth-1001b-102a | spine-1-2:veth-102a-1001b | 102       | THREE_WAY |
+-----------------+---------------------------+-----------+-----------+
| veth-1001c-103a | spine-1-3:veth-103a-1001c | 103       | THREE_WAY |
+-----------------+---------------------------+-----------+-----------+
</pre>

On spine-1-1 we can see that the adjacency to leaf-1-1 is down:

<pre>
spine-1-1> <b>show interfaces</b>
+-----------------+--------------------------+-----------+-----------+
| Interface       | Neighbor                 | Neighbor  | Neighbor  |
| Name            | Name                     | System ID | State     |
+-----------------+--------------------------+-----------+-----------+
| veth-101a-1001a |                          |           | <b>ONE_WAY</b>   |
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

As a result, spine-1-1 does not advertise an adjacency with leaf-1-1 in its South-Node-TIE
(notice that neighbor 1001 is missing):

<pre>
spine-1-1> <b>show tie-db</b>
+-----------+------------+--------+--------+--------+----------+-----------------------+
| Direction | Originator | Type   | TIE Nr | Seq Nr | Lifetime | Contents              |
+-----------+------------+--------+--------+--------+----------+-----------------------+
.           .            .        .        .        .          .                       .
.           .            .        .        .        .          .                       .
.           .            .        .        .        .          .                       .
+-----------+------------+--------+--------+--------+----------+-----------------------+
| South     | 101        | Node   | 1      | 11     | 603815   | Name: spine-1-1       |
|           |            |        |        |        |          | Level: 1              |
|           |            |        |        |        |          | Neighbor: 1           |
|           |            |        |        |        |          |   Level: 2            |
|           |            |        |        |        |          |   Cost: 1             |
|           |            |        |        |        |          |   Bandwidth: 100 Mbps |
|           |            |        |        |        |          |   Link: 4-1           |
|           |            |        |        |        |          | Neighbor: 2           |
|           |            |        |        |        |          |   Level: 2            |
|           |            |        |        |        |          |   Cost: 1             |
|           |            |        |        |        |          |   Bandwidth: 100 Mbps |
|           |            |        |        |        |          |   Link: 5-1           |
|           |            |        |        |        |          | Neighbor: 3           |
|           |            |        |        |        |          |   Level: 2            |
|           |            |        |        |        |          |   Cost: 1             |
|           |            |        |        |        |          |   Bandwidth: 100 Mbps |
|           |            |        |        |        |          |   Link: 6-1           |
|           |            |        |        |        |          | Neighbor: 4           |
|           |            |        |        |        |          |   Level: 2            |
|           |            |        |        |        |          |   Cost: 1             |
|           |            |        |        |        |          |   Bandwidth: 100 Mbps |
|           |            |        |        |        |          |   Link: 7-1           |
|           |            |        |        |        |          | Neighbor: 1002        |
|           |            |        |        |        |          |   Level: 0            |
|           |            |        |        |        |          |   Cost: 1             |
|           |            |        |        |        |          |   Bandwidth: 100 Mbps |
|           |            |        |        |        |          |   Link: 2-1           |
|           |            |        |        |        |          | Neighbor: 1003        |
|           |            |        |        |        |          |   Level: 0            |
|           |            |        |        |        |          |   Cost: 1             |
|           |            |        |        |        |          |   Bandwidth: 100 Mbps |
|           |            |        |        |        |          |   Link: 3-1           |
+-----------+------------+--------+--------+--------+----------+-----------------------+
.           .            .        .        .        .          .                       .
.           .            .        .        .        .          .                       .
.           .            .        .        .        .          .                       .
</pre>

Spine-1-2 notices that spine-1-1 is not reporting leaf-1-1 as a neighbor.
On spine-1-2 we can look at the other nodes that are on the same level as spine-1-2 (we call these
same-level-nodes):

<pre>
spine-1-2> <b>show same-level-nodes</b>
+-----------+-------------+-------------+-------------+
| Node      | North-bound | South-bound | Missing     |
| System ID | Adjacencies | Adjacencies | South-bound |
|           |             |             | Adjacencies |
+-----------+-------------+-------------+-------------+
| 101       | 1           | 1002        | <b>1001</b>        |
|           | 2           | 1003        |             |
|           | 3           |             |             |
|           | 4           |             |             |
+-----------+-------------+-------------+-------------+
| 103       | 1           | 1001        |             |
|           | 2           | 1002        |             |
|           | 3           | 1003        |             |
|           | 4           |             |             |
+-----------+-------------+-------------+-------------+
</pre>

We can see that:

 * Spine-1-2 knows about two other nodes at the same level as itself: one with
system ID 101 and one with system ID 103.

 * Same-level-node 103 (which is spine-1-3) has a full set of south-bound
 adjacencies with all of the leaf nodes in pod-1, which have system IDs 1001, 1002, and 1003.

 * However, same-level-node 101 (which is spine-1-1) is missing one south-bound adjacency,
 namely the adjacency with system ID 1001 (which is leaf-1-1). This reflects the fact that
 the link between spine-1-1 and leaf-1-1 is broken.

Based on this information, spine-1-2 knows that leaf-1-1 (which has system ID 1001) is what we call
"partially connected". Partially connected means that leaf-1-1 is connected to spine-1-2 itself,
but not to at least one other node at the same level (spine-1-1, which has system ID 101,
in this case).

<pre>
spine-1-2> show interface veth-102a-1001b
Interface:
+--------------------------------------+--------------------------------------------+
| Interface Name                       | veth-102a-1001b                            |
.                                      .                                            .
.                                      .                                            .
.                                      .                                            .
| <b>Neighbor is Partially Connected</b>      | <b>True</b>                                       |
| <b>Nodes Causing Partial Connectivity</b>   | <b>101</b>                                        |
+--------------------------------------+--------------------------------------------+
...
</pre>

At this point spine-1-2 knows that leaf-1-1 is partially connected. What is the implication of this
partial connectivity?

Well, let's see.

Up until now, all spine nodes in pod-1 were only advertising default routes to the leaf nodes
in pod-1.

Let's consider the scenario that leaf-1-3 wants to send a packet to leaf-1-1.

If we only have default routes, leaf-1-3 with only have a default route with ECMP next-hops over
all three spines: spine-1-1, spine-1-2, and spine-1-3.

There is a 1 in 3 probability that leaf-1-3 choses spine-1-1 to send a packet to leaf-1-1.
This will not work: spine-1-1 is not able forward the packet to leaf-1-1 because of the broken link.

Now, positive disaggregation comes to the rescue.

When spine-1-2 runs it south-bound SPF, it calculates a specific (i.e. /32 in the case of IPv4) to
each of the leaf nodes below it, including leaf-1-1.

There is a show command to see the result of this SPF calculation:

<pre>
spine-1-2> <b>show spf</b>
SPF Statistics:
+---------------+----+
| SPF Runs      | 8  |
+---------------+----+
| SPF Deferrals | 53 |
+---------------+----+

South SPF Destinations:
+-----------------+------+-------------+------+--------------+-----------------------------+-------------------------------------------+
| Destination     | Cost | Predecessor | Tags | Disaggregate | IPv4 Next-hops              | IPv6 Next-hops                            |
|                 |      | System IDs  |      |              |                             |                                           |
+-----------------+------+-------------+------+--------------+-----------------------------+-------------------------------------------+
| 102 (spine-1-2) | 0    |             |      |              |                             |                                           |
+-----------------+------+-------------+------+--------------+-----------------------------+-------------------------------------------+
| 1001 (leaf-1-1) | 1    | 102         |      |              | veth-102a-1001b 99.3.4.3    | veth-102a-1001b fe80::c845:8eff:fe61:dca3 |
+-----------------+------+-------------+------+--------------+-----------------------------+-------------------------------------------+
| 1002 (leaf-1-2) | 1    | 102         |      |              | veth-102b-1002b 99.9.10.9   | veth-102b-1002b fe80::ec2d:d9ff:fe10:301f |
+-----------------+------+-------------+------+--------------+-----------------------------+-------------------------------------------+
| 1003 (leaf-1-3) | 1    | 102         |      |              | veth-102c-1003b 99.15.16.15 | veth-102c-1003b fe80::c024:8bff:feb5:e930 |
+-----------------+------+-------------+------+--------------+-----------------------------+-------------------------------------------+
| 88.0.1.1/32     | 2    | 1001        |      | <b>Positive</b>     | veth-102a-1001b 99.3.4.3    | veth-102a-1001b fe80::c845:8eff:fe61:dca3 |
+-----------------+------+-------------+------+--------------+-----------------------------+-------------------------------------------+
| 88.0.2.1/32     | 2    | 1002        |      |              | veth-102b-1002b 99.9.10.9   | veth-102b-1002b fe80::ec2d:d9ff:fe10:301f |
+-----------------+------+-------------+------+--------------+-----------------------------+-------------------------------------------+
| 88.0.3.1/32     | 2    | 1003        |      |              | veth-102c-1003b 99.15.16.15 | veth-102c-1003b fe80::c024:8bff:feb5:e930 |
+-----------------+------+-------------+------+--------------+-----------------------------+-------------------------------------------+
| 88.1.2.1/32     | 1    | 102         |      |              |                             |                                           |
+-----------------+------+-------------+------+--------------+-----------------------------+-------------------------------------------+

...
</pre>

There is something interesting in this output: the SPF entry for destination 88.0.1.1/32 (which
is the loopback of leaf_1_1) is marked for "Positive" disaggregation.

What happened here?

Well, when spine-1-2 calculated the route to 88.0.1.1/32, it determine that interface
veth-102a-1001b and next-hop 99.3.4.3 are the direct next-hop for the route.

Interface veth-102a-1001b is the iterface to leaf-1-1, which as we observed before was marked as
"partially connected".

The fact that a south-bound route has a direct next-hop which is marked as partially connected
is what triggers the positive disaggregation, and is what causes spine-1-2 to advertise the more
specific route (88.0.1.1/32 in this case) as a positively disaggregated prefix to the southern
neighbors (the leaves in this case).

Now, let's jump over to leaf-1-3 (which we mentioned previously in the example of why a default
route alone is not goog enough enymore).

Leaf-1-3 did indeed receive a new TIE from spine-1-2 (and also from spine-1-3 for that matter)
with positively disaggregated prefixes:

<pre>
leaf-1-3> show tie-db
+-----------+------------+----------------+--------+--------+----------+-----------------------------+
| Direction | Originator | Type           | TIE Nr | Seq Nr | Lifetime | Contents                    |
+-----------+------------+----------------+--------+--------+----------+-----------------------------+
.           .            .                .        .        .          .                             .
.           .            .                .        .        .          .                             .
.           .            .                .        .        .          .                             .
+-----------+------------+----------------+--------+--------+----------+-----------------------------+
| South     | 102        | Pos-Dis-Prefix | 3      | 1      | 602156   | Pos-Dis-Prefix: 88.0.1.1/32 |
|           |            |                |        |        |          |   Metric: 2                 |
+-----------+------------+----------------+--------+--------+----------+-----------------------------+
.           .            .                .        .        .          .                             .
.           .            .                .        .        .          .                             .
.           .            .                .        .        .          .                             .
+-----------+------------+----------------+--------+--------+----------+-----------------------------+
| South     | 103        | Pos-Dis-Prefix | 3      | 1      | 602156   | Pos-Dis-Prefix: 88.0.1.1/32 |
|           |            |                |        |        |          |   Metric: 2                 |
+-----------+------------+----------------+--------+--------+----------+-----------------------------+
.           .            .                .        .        .          .                             .
.           .            .                .        .        .          .                             .
.           .            .                .        .        .          .                             .
</pre>

These positively disaggregated prefixes participate normally in the SPF calculation:

<pre>
leaf-1-3> <b>show spf</b>
SPF Statistics:
+---------------+----+
| SPF Runs      | 6  |
+---------------+----+
| SPF Deferrals | 19 |
+---------------+----+

South SPF Destinations:
+-----------------+------+-------------+------+--------------+----------------+----------------+
| Destination     | Cost | Predecessor | Tags | Disaggregate | IPv4 Next-hops | IPv6 Next-hops |
|                 |      | System IDs  |      |              |                |                |
+-----------------+------+-------------+------+--------------+----------------+----------------+
| 1003 (leaf-1-3) | 0    |             |      |              |                |                |
+-----------------+------+-------------+------+--------------+----------------+----------------+
| 88.0.3.1/32     | 1    | 1003        |      |              |                |                |
+-----------------+------+-------------+------+--------------+----------------+----------------+

North SPF Destinations:
+----------------------+------+-------------+------+--------------+-----------------------------+-------------------------------------------+
| Destination          | Cost | Predecessor | Tags | Disaggregate | IPv4 Next-hops              | IPv6 Next-hops                            |
|                      |      | System IDs  |      |              |                             |                                           |
+----------------------+------+-------------+------+--------------+-----------------------------+-------------------------------------------+
| 101 (spine-1-1)      | 1    | 1003        |      |              | veth-1003a-101c 99.13.14.14 | veth-1003a-101c fe80::f04d:cbff:fe55:e159 |
+----------------------+------+-------------+------+--------------+-----------------------------+-------------------------------------------+
| 102 (spine-1-2)      | 1    | 1003        |      |              | veth-1003b-102c 99.15.16.16 | veth-1003b-102c fe80::8050:b6ff:fe11:fc10 |
+----------------------+------+-------------+------+--------------+-----------------------------+-------------------------------------------+
| 103 (spine-1-3)      | 1    | 1003        |      |              | veth-1003c-103c 99.17.18.18 | veth-1003c-103c fe80::d48f:43ff:fe0a:edf6 |
+----------------------+------+-------------+------+--------------+-----------------------------+-------------------------------------------+
| 1003 (leaf-1-3)      | 0    |             |      |              |                             |                                           |
+----------------------+------+-------------+------+--------------+-----------------------------+-------------------------------------------+
| 0.0.0.0/0            | 2    | 101         |      |              | veth-1003a-101c 99.13.14.14 | veth-1003a-101c fe80::f04d:cbff:fe55:e159 |
|                      |      | 102         |      |              | veth-1003b-102c 99.15.16.16 | veth-1003b-102c fe80::8050:b6ff:fe11:fc10 |
|                      |      | 103         |      |              | veth-1003c-103c 99.17.18.18 | veth-1003c-103c fe80::d48f:43ff:fe0a:edf6 |
+----------------------+------+-------------+------+--------------+-----------------------------+-------------------------------------------+
| 88.0.3.1/32          | 1    | 1003        |      |              |                             |                                           |
+----------------------+------+-------------+------+--------------+-----------------------------+-------------------------------------------+
| ::/0                 | 2    | 101         |      |              | veth-1003a-101c 99.13.14.14 | veth-1003a-101c fe80::f04d:cbff:fe55:e159 |
|                      |      | 102         |      |              | veth-1003b-102c 99.15.16.16 | veth-1003b-102c fe80::8050:b6ff:fe11:fc10 |
|                      |      | 103         |      |              | veth-1003c-103c 99.17.18.18 | veth-1003c-103c fe80::d48f:43ff:fe0a:edf6 |
+----------------------+------+-------------+------+--------------+-----------------------------+-------------------------------------------+
| 88.0.1.1/32 <b>(Disagg)</b> | 3    | 102         |      |              | veth-1003b-102c 99.15.16.16 | veth-1003b-102c fe80::8050:b6ff:fe11:fc10 |
|                      |      | 103         |      |              | veth-1003c-103c 99.17.18.18 | veth-1003c-103c fe80::d48f:43ff:fe0a:edf6 |
+----------------------+------+-------------+------+--------------+-----------------------------+-------------------------------------------+
</pre>

Note that prefix 88.0.1.1/32 is marked with "(Disagg)". This means it is a prefix that was
received in the Positive-Disaggregation-Prefix-TIE (as opposed to a normal Prefix-TIE). This is
only mentioned for debugging; it does not influence the SPF calculation.

I have to point out something to avoid confusion:

 * If the prefix in the destination column is marked with "(Disagg)", it means that the prefix was
   disaggregated with a node north of this node.

 * If the column "Disaggregate" has the work "Positive" in it, it means that this node will
   disaggregate the prefix.

Finally, if we look at the route table of leaf-1-3, we see the more specific disaggregated prefix
(in addition to the default route which is still there):

<pre>
leaf-1-3> <b>show route</b>
IPv4 Routes:
+-------------+-----------+-----------------------------+
| Prefix      | Owner     | Next-hops                   |
+-------------+-----------+-----------------------------+
| 0.0.0.0/0   | North SPF | veth-1003a-101c 99.13.14.14 |
|             |           | veth-1003b-102c 99.15.16.16 |
|             |           | veth-1003c-103c 99.17.18.18 |
+-------------+-----------+-----------------------------+
| <b>88.0.1.1/32</b> | <b>North SPF</b> | <b>veth-1003b-102c 99.15.16.16</b> |
|             |           | <b>veth-1003c-103c 99.17.18.18</b> |
+-------------+-----------+-----------------------------+

IPv6 Routes:
+--------+-----------+-------------------------------------------+
| Prefix | Owner     | Next-hops                                 |
+--------+-----------+-------------------------------------------+
| ::/0   | North SPF | veth-1003a-101c fe80::f04d:cbff:fe55:e159 |
|        |           | veth-1003b-102c fe80::8050:b6ff:fe11:fc10 |
|        |           | veth-1003c-103c fe80::d48f:43ff:fe0a:edf6 |
+--------+-----------+-------------------------------------------+
</pre>

These more specific /32 routes fix the blackholing of the traffic to leaf-1-1:

 * When leaf-1-3 sends a packet to leaf-1-1 (destination address 80.0.1.1), it uses the more
   specific route 80.0.1.1/32. That route has ECMP next-hops spine-1-2 and spine-1-3. However,
   spine-1-1 is not a next-hop, so we avoid the spine that would blackhole the traffic.

 * When leaf-1-3 sends packets to any other destination, it uses the default route which still
   ECMPs the traffic over all three spines.

And there you have it, I present you: positive disaggregation! 

As an execercise for the reader: repair the red link and verify that the positive disaggreggation
goes away.