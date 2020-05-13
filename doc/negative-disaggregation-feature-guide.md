
*** WORK IN PROGRESS ***

# Negative Disaggregation Feature Guide

## Innovations in disaggregation

Automatic disaggregation and negative disaggregation are two of the most novel and most interesting
innovations in the Routing In Fat Trees (RIFT) protocol.

Negative disaggregation is very closely related to positive disaggregation which is briefly
mentioned in this feature guide and which is described in far greater detail in its own feature
guide @@@.

One of the best known characteristics of RIFT is that it is a link-state protocol north-bound and
a distance-vector protocol south-bound. 
One consequence of that is that the RIFT routing tables typically contain host /32 (for IPv4) or
/128 (for IPv6) routes for all south-bound traffic,
and only default 0.0.0.0/0 and ::0/0 routes for all north-bound traffic.

The following figure shows typical RIFT route tables in a small 3-level fat tree topology.
The leaf nodes contain only a single north-bound default route. The superspine nodes contain
only host-specific south-bound routes. And the spine nodes contain a mixture.

![RIFT Typical Route Tables](https://brunorijsman-public.s3-us-west-2.amazonaws.com/diagram-rift-typical-route-tables.png)

Automatic disaggregation (either the positive or the negative flavor) is what allows RIFT to get
away with only using default routes for north-bound traffic.

If there are no failures (no broken links and no broken routers) anywhere in the topology, then
default routes are just fine.
Each router can just "spray" all north-bound traffic accross all parent routers using a equal cost
multi-path (ECMP) default route. The Clos topology guarantees that (in the absence of failures)
it doesn't matter which parent router is chosen. Any parent router is able to reach the final
destination at the same cost as any other parent router. Have a look at the topology below and
spend a few minutes to convince yourself that this is indeed a true statement.

However, we have to consider the unhappy scenario as well. What if one or more links or routers
are down? In this case a simple default route for all north-bound traffic is not going to work.
The traffic for certain destinations must avoid certain parents, and use certain alternative
parents instead. I intentionally wrote that previous sentence to sound very vague:

 * Which destination prefixes exactly must follow a special path and cannot follow the default
   route? In other words, which destination prefixes must be disaggregated? The word disaggregate
   is simply a fancy word for using a more specific route instead of the default route.

 * For those disaggregated routes, which subset of parent next-hops should these disaggregated
   routes avoid? This is the question that negative disaggregation answers.

 * Or equivalently, you might ask: which subset of alternative parent next-hops should these
   disaggregated routes use instead? This is the question that positive disaggregation answers.

It is complex to answer these questions. The answer depends on the topology of the network, where
the prefixes are located in the network, and which links and routers have failed at any particular
moment in time.

This is exactly the magical leap that RIFT took. It answers this question in a completely automated
manner without the need for any manual a-priori configuration or any manual intervention when a
failure occurs. In the absence of a failure, RIFT only installs ECMP default routes for all
north-bound traffic. RIFT automatically detects link and router failures. When one or more failures
occur, RIFT automatically decides which prefixes need to be disaggregated, whether positive or
negative disaggregation should be used, automatically floods the disaggregated routes to those
parts of the network where they are needed, and automatically installs the disaggregated routes
into the routing tables of the routers where they are needed.

As far as I know, no other widely used protocol has taken this leap. Neither OSPF nor ISIS nor BGP
nor any other widely deployed protocol is able to automatically disaggregate routes. Some support
_manual_ disaggregation, but not _automatic_. For that reason, those protocol tend to use specific
/32 and /128 routes for both south-bound and north-bound traffic in Clos topologies.

On top of that, as far as I know, prior to RIFT no protocol supported the concept of _negative_
disaggregation. In protocols prior to RIFT all disaggregation was _positive_. If traffic to a
specific destination prefix needed to follow a non-default path, then the protocol would advertise
specific routes pointing to all remaining feasible equal-cost paths. In contrast, RIFT supports the
concept of _negative_ disaggregation: instead of advertising positive more specific routes poiting
to the more preferred path, it can advertise negative more specific routes advertising which paths
should be avoided. This is particularly useful in topologies that have massive ECMP, such as
Clos topologies. Consider a route that has 64-way ECMP, which not uncommon in large datacenter
topologies. Now consider that one of the 64 paths fails. With positive disaggregation, we would
advertise 63 more specific routes to the remaining feasily paths. With negative disaggregation,
we would only advertise one single more specific (negative) route to the single path to be
avoided.

To summarize: disaggregation per-se is not novel in RIFT; disaggregation already existed in
other protocols prior to RIFT. The main two innovations in RIFT are
(a) the fact that disaggregation is _automatic_ and (b) the concept of _negative_ disaggregation.

## Positive disaggregation versus negative disaggregation

Consider the following toy example topology.

![RIFT Clos 3x3 No Failures](https://brunorijsman-public.s3-us-west-2.amazonaws.com/diagram-rift-clos-3-x-3-no-failure-default-only.png)

We are interested in how traffic gets from leaf-1 to leaf-3.

In the absence of failures, each spine router advertises a default route to each leaf router.
Each leaf router, including leaf-1, ends up with a single ECMP default route that sprays
all traffic over all three spines.

Make a mental note of the fact that the traffic from leaf-1 to leaf-3 is spread equally across
all three spine nodes. This will turn out to be important later on. (We are assuming here that
the traffic consists of a sufficient number of flows, allowing ECMP hashing to do its job.)

### Positive disaggregation

Now let us consider how positive disaggregation can recover from a link failure between spine-1
and leaf-3 (indicated by the red cross).

![RIFT Clos 3x3 Failures repaired by positive disaggregation](https://brunorijsman-public.s3-us-west-2.amazonaws.com/diagram-rift-clos-3-x-3-failure-pos-disagg.png)

The first thing to observe is that having only a default route on leaf-1 is not good enough anymore.
Why not? Let's see what happens if leaf-1 sends a packet to leaf-3. The default route has a 1/3rd
chance of sending the packet to spine-1, a 1/3rd chance for spine-2, and a 1/3rd chance for spine-3.
If it happens to choose spine-1, the packet will be dropped, because spine-1 cannot get to leaf-3.

Positive disaggregation deals with this situation as follows:

 1. Spine-2 knows that its link to leaf-3 is still up. Spine-2 concludes: "I can still reach
    leaf-3. If anyone wants to send traffic to leaf-3, they can safely give it to me, and I will
    deliver it to leaf-3."
 
 2. Spine-2 also knows that the link from spine-1 to leaf-3 is down. How does spine-2 know this? 
    Because spine-2 can see the South-Node-TIE from spine-1 (it is reflected by the leaf nodes)
    which contains spine-1's adjacencies. Spine-2 conludes: "Spine-1 cannot reach leaf-3. If anyone
    wants to send traffic to leaf-3, they better not give it to leaf-1 because leaf-1 will blackhole
    that traffic."
 
 3. Spine-2, being a helpful and altruistic router thinks: "I must warn all the leaf routers! I
    must tell them that if they have any traffic to send to leaf-3, they better not give it to
    spine-1, but it is okay to give it to me!"

 4. How does spine-2 warn the leaf routers? By advertising a host-specific 2.0.0.3/32 route for
    leaf-1 to all leaf routers. This /32 host route more specific than the /0 default route.
    Hence, all leaf routes will send traffic to leaf-3 via spine-2. Traffic for leaf-1 and leaf-2
    still follows the default route and is ECMP'ed across all three spine routers.
 
 5. Router spine-3 independently goes through the exact sequence of steps as spine-2: it also
    advertises a host-specific route 2.0.0.3/32 for leaf-3.

 6. After everything has converged, the leaf routers will end up with an ECMP 2.0.0.3/32 route
    for leaf-3 that ECMP's the traffic across spine-2 and spine-3 (but not spine-1).

Note that step 5 takes place independently and asynchronously on each spine routers.
Thus, as the positive disaggregation process is converging, the host-specific positive disaggregate
route starts out with a single next-hop, then two ECMP next-hop, until it finally ends up with N-1
ECMP next-hops where N is the number of spine routers.

This can be a problem. The traffic that used to be spread out over N routers is temporarily 
concentrated on a single spine router, then two spine routers, until it is finally spread out
again over N-1 spine routers. This is referred to as the "transitory incast" problem. Later we will
see how negative disaggregation avoids this problem.

### Negative disaggregation



## Example network

This feature guide for negative disaggregation is based on the following topology:

![Topology Diagram](https://s3-us-west-2.amazonaws.com/brunorijsman-public/diagram_clos_3plane_3pod_3leaf_3spine_6super.png)

We will complete disconnect plane-1 from pod-1 by breaking both links marked with red crosses.
This will cause plane-1 to send negative disaggregation routes for pod-1 to the other pods pod-2
and pod-3.

## Before breaking the link: no positive disaggregation occurs

Let us first look at the network before we break the red links and before any negative
disaggregation happens.

### Super-1-1

On super-1-1 all adjacencies are up:

<pre>
super-1-1> <b>show interfaces</b>
+-----------+-------------------+-----------+-----------+
| Interface | Neighbor          | Neighbor  | Neighbor  |
| Name      | Name              | System ID | State     |
+-----------+-------------------+-----------+-----------+
| if-1a     | spine-1-1:if-101d | 101       | THREE_WAY |
+-----------+-------------------+-----------+-----------+
| if-1b     | spine-2-1:if-104d | 104       | THREE_WAY |
+-----------+-------------------+-----------+-----------+
| if-1c     | spine-3-1:if-107d | 107       | THREE_WAY |
+-----------+-------------------+-----------+-----------+
| if-1d     | super-2-1:if-3d   | 3         | THREE_WAY |
+-----------+-------------------+-----------+-----------+
| if-1e     | super-3-1:if-5e   | 5         | THREE_WAY |
+-----------+-------------------+-----------+-----------+
</pre>

Super-1-1 has three south-bound adjacencies to spine-1-1, spine-2-1, and spine-3-1, which are the
first spines in pod-1, pod-2, and pod-3 respectively.

Additionally, super-1-1 has two east-west adjacencies to super-2-1 and super-3-1, which are the 
first superspines in plane-2 and plane-3 respectively. This forms one of the two interplane
east-west loops.

### Spine-2-1

On spine-2-1 all adjacencies are also up:

<pre>
spine-2-1> <b<>how interfaces</b>
+-----------+-------------------+-----------+-----------+
| Interface | Neighbor          | Neighbor  | Neighbor  |
| Name      | Name              | System ID | State     |
+-----------+-------------------+-----------+-----------+
| if-104a   | leaf-2-1:if-1004a | 1004      | THREE_WAY |
+-----------+-------------------+-----------+-----------+
| if-104b   | leaf-2-2:if-1005a | 1005      | THREE_WAY |
+-----------+-------------------+-----------+-----------+
| if-104c   | leaf-2-3:if-1006a | 1006      | THREE_WAY |
+-----------+-------------------+-----------+-----------+
| if-104d   | super-1-1:if-1b   | 1         | THREE_WAY |
+-----------+-------------------+-----------+-----------+
| if-104e   | super-1-2:if-2b   | 2         | THREE_WAY |
+-----------+-------------------+-----------+-----------+
</pre>

Spine-2-1 has two north-bound adjacencies to super-1-1 and super-2-1, which are the two superspine
nodes in plane-1.

Additionally, spine-2-1 has three south-bound adjacencies to leaf-2-1, leaf-2-2, and leaf-2-3, 
which are the three leaf nodes in pod-2.





@@@ CONTINUE FROM HERE @@@

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