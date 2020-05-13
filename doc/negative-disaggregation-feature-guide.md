
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
nor any other widely deployed protocol is able to automatically disaggregate routes to re-route
traffic around failures. 
Some support _manual_ disaggregation, but not _automatic_. For that reason, those protocol tend to
use specific
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

 4. How does spine-2 warn the other routers? By advertising a host-specific 2.0.0.3/32 route for
    leaf-3 to all leaf routers.
    This route is called a positive disaggregation route.
    It is a /32 host route, whichis more specific than the /0 default route.
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

Now that we have seen how _positive_ disaggregation recovers from a link failure, let's see
how _negative_ disaggregation could recover from the same link failure.

I carefully used the word _could_ in the previous sentence for a reason. 
According to the current version of the RIFT specification, 
RIFT currently always uses positive disaggregation to recover
from this type of failure. Negative disaggregation is perfectly capabable of recovering from this
failure as well, and that would even have advantages (which we will discuss). 
But the RIFT specification
as it is currently written, does not use negative disaggregation for this particular simple
scenario.
RIFT only uses negative disaggregation in quite complex failure scenarios
involving multi-plane fabrics with inter-plane east-west links, which we will also cover after 
covering the simpler scenario first.

So, in this section we will use the same failure scenario as before to explain how negative
disaggregation works, even though RIFT would never use negative disaggregation in this particular
scenario. We use this scenario anyway because it makes negative disaggregation much easier to
understand than the much more complex realistic scenario that we will cover later on.

![RIFT Clos 3x3 Failures repaired by negative disaggregation](https://brunorijsman-public.s3-us-west-2.amazonaws.com/diagram-rift-clos-3-x-3-failure-neg-disagg.png)

Negative disaggregation recovers from this failure as follows:

 1. Spine-1 knows that the other spine routes are connected to leaf-3. How does spine-1 know this?
    Because spine-1 can see the South-Node-TIE from the the other spines (they are reflected by the
    leaf nodes) which contain leaf-3 as an adjacency. Spine-1 conludes: "Spine-2 and spine-3 can
    reach leaf-3. If anyone wants to send traffic to leaf-3 they can give it to spine-2 or spine-3,
    and they will deliver it to leaf-3."

 2. On the other hand, spine-1 also knows that it does not have any adjacency to leaf-3 itself. In
    fact it may never have had any adjacency with leaf-3. Spine-1 concludes: "I myself cannot
    reach leaf-3. If anyone wants to send traffic to leaf-3 they better not give it me because I
    will blackhole it."

 3. Spine-1, also being a helpful and altruistic router thinks: "I must warn all the leaf routers!
    Evidently somewhere out there, there is this leaf-3 router, but I don't know how to get to it.
    I must warn everyone not to send any traffic for leaf-3 to me."

 4. How does spine-1 warn the other routers? By advertising a special kind of 
    host-specific 2.0.0.3/32 route for
    leaf-3 to all leaf routers.
    This route is called a negative disaggregation route.
    Such a negative route has a very special meaning: it means "Please do _not_ send traffic
    for this prefix to me. If you have another route to this same prefix that avoids me, even if

 5. When the leaf routers receive such a negative disaggregation route, this install it as a
    special route in the routing information base (RIB) with negative next-hops.
 
 6. This concept of a negative next-hop is a pure control-plane abstraction. In current forwarding
    plane hardware there is no such thing as a negative next-hop. So, when RIB route is installed
    in the FIB, we must translate the negative next-hop into an equivalent "complementary" set of
    positive next-hops as follows:

    a. Start with the prefix of the negative route (2.0.0.3/32 in this case).

    b. Find the most specific aggregate route that covers this prefix (0.0.0.0/0 in this case).

    c. Take the next-hops of the aggregate encompasing route (1.0.0.1, 1.0.0.2, and 1.0.0.3 in this
       case).

    d. From this set of next-hops, remove the negative next-hops of the more specific negative
       route (in this example we remove negative next-hop 1.0.0.1 which leave us with effective
       next-hops 1.0.0.2 and 1.0.0.3).

Steps 1 and 2 bring leaf-1 to the point that it realizes that there exists some destination prefix
that it should be able to reach but that it can not actually reach. We described one particular
mechanism, but later on we see a different mechanism for multi-plane topologies.

Negative disaggregation has two advantages relative to positive disaggregation:

 1. It is simpler in the sense that it greatly reduces the amount of routes that have to be
    advertised to recover from a failure. Instead of N-1 routers having to advertise a positive
    disaggregate route, only 1 router has to advertise a negative disaggregate route.
 
 2. For this exact same reason, negative disaggregation avoids the transitory incast problem that
    we described above.

# Negative disaggregation in the real world

## Multi-plane fabrics with east-west inter-plane links

We have explained how negative disaggregation works using an unrealisticly simple topology. Now
let's look at an actual realistic real-life topology, namely the following 3-level multi-plane Clos
fabric with east-west inter-plane links:

![Multi-Plane Topology Diagram](https://s3-us-west-2.amazonaws.com/brunorijsman-public/diagram_clos_3plane_3pod_3leaf_3spine_6super.png)

The description "3-level multi-plane Clos fabric with east-west inter-plane links" is quite a
mouthful. Let's take that apart to see what it really means:

 * **3-level**: There are 3 levels in the topology: leaf routers, spine routers, and superspine
   routers (also known as top-of-fabric routers).

 * **multi-plane**: The superspine routers are devided into multiple indendent "planes". This
   is typically done when the superspine routers don't have enough ports to connect to each
   spine router. The reason these are called "planes" becomes more clear when you look at the
   equivalent 3-dimensional diagram below. In this 3D diagram we have a blue, a brown, and a green
   plane.

 * **with east-west interplane links**: This means that the superspine routers in different planes
   are connected to each other using east-west links. (These links are not shown in the 3D diagram
   further below.) The east-west links between the superspine routers are only used for RIFT
   control-plane messages (LIE, TIE, TIRE, and TIDE messages) and not for data-plane traffic.
   In general these east-west inter-plane links are not mandatory, but the negative disaggregation
   feature only works if these links are present.

![3D Planes](https://brunorijsman-public.s3-us-west-2.amazonaws.com/diagram-rift-3d-planes.png)

## The failure scenario

We will study the following failure scenario: 
we will break both north-bound links from router spine-1-1.
This causes pod-1 to become completely disconnected from plane-1.

When any leaf router in pod-1 (i.e. leaf-1-1, leaf-1-2, or leaf-1-3) wants to send any traffic
to any other pod (i.e. pod-2 or pod-3) it cannot send the traffic via plane-1 and hence also not
via spine-1-1.
Instead, the traffic must go via plane-2 (and hence spine-1-2) or via plane-3 (and hence spine-1-3).

## Generating and starting the topology

Let's actually run the above topology in RIFT-Python and discover how negative disaggregation
recovers from the failure.

Although the topology is quite complex, it is almost trivial to run it in RIFT-Python.

The meta-topology file `meta_topology/clos_3plane_3pod_3leaf_3spine_6super.yaml` contains the
following extremely succint description of the topology:

<pre>
nr-pods: 3
nr-leaf-nodes-per-pod: 3
nr-spine-nodes-per-pod: 3
nr-superspine-nodes: 6
nr-planes: 3
</pre>

We use the configuration generator to convert this meta-topology into a topology file named
`generated.yaml`.

<pre>
(env) $ <b>tools/config_generator.py meta_topology/clos_3plane_3pod_3leaf_3spine_6super.yaml generated.yaml</b>
</pre>

Note: you can use the `-g` command-line option to also generate a diagram of the topology called
`diagram.html` that you can open using any web browser (this is how we produced the above diagram):

<pre>
(env) $ <b>tools/config_generator.py -g diagram.hml meta_topology/clos_3plane_3pod_3leaf_3spine_6super.yaml generated.yaml</b>
</pre>

Once the topology file is generated, you can start it in RIFT-Python as follows:

<pre>
(env) $ <b>python rift -i generated.yaml</b>
leaf-1-1>
</pre>

You can see that all the expected routers are present:

<pre>
leaf-1-1> <b>show nodes</b>
+-----------+--------+---------+
| Node      | System | Running |
| Name      | ID     |         |
+-----------+--------+---------+
| leaf-1-1  | 1001   | True    |
+-----------+--------+---------+
| leaf-1-2  | 1002   | True    |
+-----------+--------+---------+
.           .        .         .
.           .        .         .
+-----------+--------+---------+
| super-3-1 | 5      | True    |
+-----------+--------+---------+
| super-3-2 | 6      | True    |
+-----------+--------+---------+
</pre>

Note: this is a large and complex topology. My MacBook (not a Pro) laptop is too feeble to run it.
Instead, I hrun it on an m5a-large AWS instance.

## Initial convergence

Before we start breaking links and before we have a look at negative disaggregation in action,
let's just spend a few minutes looking around in the topology.

### Super-1-1

On super-1-1 all adjacencies are up:

<pre>
leaf-1-1> <b>set node super-1-1</b>
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

Note: from now on, we will omit the `set node ...` commands and expect you to navigate to the
correct router yourself.

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

### Leaf-2-1

On leaf-2-1 all adjacencies are also up:

<pre>
leaf-2-1> <b>show interfaces</b>
+-----------+-------------------+-----------+-----------+
| Interface | Neighbor          | Neighbor  | Neighbor  |
| Name      | Name              | System ID | State     |
+-----------+-------------------+-----------+-----------+
| if-1004a  | spine-2-1:if-104a | 104       | THREE_WAY |
+-----------+-------------------+-----------+-----------+
| if-1004b  | spine-2-2:if-105a | 105       | THREE_WAY |
+-----------+-------------------+-----------+-----------+
| if-1004c  | spine-2-3:if-106a | 106       | THREE_WAY |
+-----------+-------------------+-----------+-----------+
</pre>

Leaf-2-1 has a single north-bound default (actually one for IPv4 and one for IPv6) that sprays
all traffic over all three spine nodes in pod-2:

<pre>
leaf-2-1> <b>show route</b>
IPv4 Routes:
+-----------+-----------+------------------------+
| Prefix    | Owner     | Next-hops              |
+-----------+-----------+------------------------+
| 0.0.0.0/0 | North SPF | if-1004a 172.31.15.176 |
|           |           | if-1004b 172.31.15.176 |
|           |           | if-1004c 172.31.15.176 |
+-----------+-----------+------------------------+

IPv6 Routes:
+--------+-----------+----------------------------------+
| Prefix | Owner     | Next-hops                        |
+--------+-----------+----------------------------------+
| ::/0   | North SPF | if-1004a fe80::84a:2ff:fe78:2746 |
|        |           | if-1004b fe80::84a:2ff:fe78:2746 |
|        |           | if-1004c fe80::84a:2ff:fe78:2746 |
+--------+-----------+----------------------------------+
</pre>

We do not see any /32 routes on leaf-2-1 because there is no disaggregation happening.

## Breaking the first link: positive disaggreation

We will start with breaking one link from spine-1-1 to super-1-1. 
RIFT-Python offers a handy set command to
simulate link failures:

<pre>
spine-1-1> <b>set interface if-101d failure failed</b>
</pre>

We will see how this failure causes positive disaggregation to happen.

### Super-1-1

First of all, we see that the adjacency from super-1-1 to spine-1-1 goes down.
Super-1-1 still has adjacencies to spine-2-1 and spine-3-1, but not to spine-1-1 anymore.

<pre>
super-1-1> <b>show interfaces</b>
+-----------+-------------------+-----------+-----------+
| Interface | Neighbor          | Neighbor  | Neighbor  |
| Name      | Name              | System ID | State     |
+-----------+-------------------+-----------+-----------+
| if-1a     |                   |           | ONE_WAY   |
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

### Super-1-2

Router super-1-2, which is the same plane as super-1-1 (namely plane-1) still has all three
adjacencies to spine-1-1, spine-2-1, and spine-3-1:

<pre>
super-1-2> <b>show interfaces</b>
+-----------+-------------------+-----------+-----------+
| Interface | Neighbor          | Neighbor  | Neighbor  |
| Name      | Name              | System ID | State     |
+-----------+-------------------+-----------+-----------+
| if-2a     | spine-1-1:if-101e | 101       | THREE_WAY |
+-----------+-------------------+-----------+-----------+
| if-2b     | spine-2-1:if-104e | 104       | THREE_WAY |
+-----------+-------------------+-----------+-----------+
| if-2c     | spine-3-1:if-107e | 107       | THREE_WAY |
+-----------+-------------------+-----------+-----------+
| if-2d     | super-2-2:if-4d   | 4         | THREE_WAY |
+-----------+-------------------+-----------+-----------+
| if-2e     | super-3-2:if-6e   | 6         | THREE_WAY |
+-----------+-------------------+-----------+-----------+
</pre>

Super-1-2 also has the south-node-TIE from super-1-1, because it was reflected by the spine routers:

<pre>
super-1-2> <b>show tie-db direction south originator 1 tie-type node</b>
+-----------+------------+------+--------+--------+----------+-------------------------+
| Direction | Originator | Type | TIE Nr | Seq Nr | Lifetime | Contents                |
+-----------+------------+------+--------+--------+----------+-------------------------+
| South     | 1          | Node | 1      | 7      | 598859   | Name: super-1-1         |
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

Super-2-1 looks at this TIE and notices that super-1-1 reports adjacencies with spine-2-1
(system ID 104) and spine-3-1 (system ID 107) but not with spine-1-1 (system ID 101).

Super-2-1 concludes that it has an adjacency with spine-1-1 which is missing from the set
of adjacencies of super-1-1. 
A much handier command for reporting the same information is `show same-level-nodes`:

<pre>
super-1-2> <b>show same-level-nodes</b>
+-----------+-------------+-------------+-------------+
| Node      | North-bound | South-bound | Missing     |
| System ID | Adjacencies | Adjacencies | South-bound |
|           |             |             | Adjacencies |
+-----------+-------------+-------------+-------------+
| 1         |             | 104         | 101         |
|           |             | 107         |             |
+-----------+-------------+-------------+-------------+
</pre>

Here we can see that super-1-2 knows that super-1-1 (system ID 1) is another superspone router
in the same plane, that it has two south-bound adjacencies to spine-2-1 (system ID 104) and
spine-3-1 (system ID 107), but that it is missing a south-bound adjacency to spine-1-1 (system
ID 101). This is exactly the same information as what we already concluded from looking directly
at the TIE.

Yet another way of seeing the same information is as follows:

<pre>
super-1-2> <b>show interface if-2a</b>
Interface:
+--------------------------------------+----------------------------------------------------------+
| Interface Name                       | if-2a                                                    |
| Physical Interface Name              | ens5                                                     |
| Advertised Name                      | super-1-2:if-2a                                          |
.                                      .                                                          .
| <b>Neighbor is Partially Connected      | True</b>                                                     |
| <b>Nodes Causing Partial Connectivity   | 1</b>                                                        |
+--------------------------------------+----------------------------------------------------------+

Neighbor:
+------------------------+------------------------------+
|<b> Name                   | spine-1-1:if-101e</b>            |
| System ID              | 101                          |
.                        .                              .
+------------------------+------------------------------+
</pre>

Here we can see that super-1-2 has concluded that the spine-1-1 (which is on the other side of
interface if-2a) is only "partially connected" to the superspine nodes above it. In fact, it 
missing an adjacency to super-1-1 (system ID 1), which is declared "the cause of the partical
connectivity".

This missing adjacency is exactly the trigger for initiating positive disaggregation
for every prefix that super-2-1 can reach via spine-1-1.

We can look at spine-2-1's shortest path first (SPF) calculation to see which prefixes it decides
to positively disaggregate:

<pre>
super-1-2> show spf direction south
South SPF Destinations:
+-----------------+------+---------+-------------+------+--------------+---------------------+-------------------------------+
| Destination     | Cost | Is Leaf | Predecessor | Tags | Disaggregate | IPv4 Next-hops      | IPv6 Next-hops                |
|                 |      |         | System IDs  |      |              |                     |                               |
+-----------------+------+---------+-------------+------+--------------+---------------------+-------------------------------+
| 2 (super-1-2)   | 0    | False   |             |      |              |                     |                               |
+-----------------+------+---------+-------------+------+--------------+---------------------+-------------------------------+
| 101 (spine-1-1) | 1    | False   | 2           |      |              | if-2a 172.31.15.176 | if-2a fe80::84a:2ff:fe78:2746 |
+-----------------+------+---------+-------------+------+--------------+---------------------+-------------------------------+
| 104 (spine-2-1) | 1    | False   | 2           |      |              | if-2b 172.31.15.176 | if-2b fe80::84a:2ff:fe78:2746 |
+-----------------+------+---------+-------------+------+--------------+---------------------+-------------------------------+
| 107 (spine-3-1) | 1    | False   | 2           |      |              | if-2c 172.31.15.176 | if-2c fe80::84a:2ff:fe78:2746 |
+-----------------+------+---------+-------------+------+--------------+---------------------+-------------------------------+
| 1001 (leaf-1-1) | 2    | True    | 101         |      |              | if-2a 172.31.15.176 | if-2a fe80::84a:2ff:fe78:2746 |
+-----------------+------+---------+-------------+------+--------------+---------------------+-------------------------------+
| 1002 (leaf-1-2) | 2    | True    | 101         |      |              | if-2a 172.31.15.176 | if-2a fe80::84a:2ff:fe78:2746 |
+-----------------+------+---------+-------------+------+--------------+---------------------+-------------------------------+
| 1003 (leaf-1-3) | 2    | True    | 101         |      |              | if-2a 172.31.15.176 | if-2a fe80::84a:2ff:fe78:2746 |
+-----------------+------+---------+-------------+------+--------------+---------------------+-------------------------------+
| 1004 (leaf-2-1) | 2    | True    | 104         |      |              | if-2b 172.31.15.176 | if-2b fe80::84a:2ff:fe78:2746 |
+-----------------+------+---------+-------------+------+--------------+---------------------+-------------------------------+
| 1005 (leaf-2-2) | 2    | True    | 104         |      |              | if-2b 172.31.15.176 | if-2b fe80::84a:2ff:fe78:2746 |
+-----------------+------+---------+-------------+------+--------------+---------------------+-------------------------------+
| 1006 (leaf-2-3) | 2    | True    | 104         |      |              | if-2b 172.31.15.176 | if-2b fe80::84a:2ff:fe78:2746 |
+-----------------+------+---------+-------------+------+--------------+---------------------+-------------------------------+
| 1007 (leaf-3-1) | 2    | True    | 107         |      |              | if-2c 172.31.15.176 | if-2c fe80::84a:2ff:fe78:2746 |
+-----------------+------+---------+-------------+------+--------------+---------------------+-------------------------------+
| 1008 (leaf-3-2) | 2    | True    | 107         |      |              | if-2c 172.31.15.176 | if-2c fe80::84a:2ff:fe78:2746 |
+-----------------+------+---------+-------------+------+--------------+---------------------+-------------------------------+
| 1009 (leaf-3-3) | 2    | True    | 107         |      |              | if-2c 172.31.15.176 | if-2c fe80::84a:2ff:fe78:2746 |
+-----------------+------+---------+-------------+------+--------------+---------------------+-------------------------------+
| 88.0.1.1/32     | 3    | True    | 1001        |      | Positive     | if-2a 172.31.15.176 | if-2a fe80::84a:2ff:fe78:2746 |
+-----------------+------+---------+-------------+------+--------------+---------------------+-------------------------------+
| 88.0.2.1/32     | 3    | True    | 1002        |      | Positive     | if-2a 172.31.15.176 | if-2a fe80::84a:2ff:fe78:2746 |
+-----------------+------+---------+-------------+------+--------------+---------------------+-------------------------------+
| 88.0.3.1/32     | 3    | True    | 1003        |      | Positive     | if-2a 172.31.15.176 | if-2a fe80::84a:2ff:fe78:2746 |
+-----------------+------+---------+-------------+------+--------------+---------------------+-------------------------------+
| 88.0.4.1/32     | 3    | True    | 1004        |      |              | if-2b 172.31.15.176 | if-2b fe80::84a:2ff:fe78:2746 |
+-----------------+------+---------+-------------+------+--------------+---------------------+-------------------------------+
| 88.0.5.1/32     | 3    | True    | 1005        |      |              | if-2b 172.31.15.176 | if-2b fe80::84a:2ff:fe78:2746 |
+-----------------+------+---------+-------------+------+--------------+---------------------+-------------------------------+
| 88.0.6.1/32     | 3    | True    | 1006        |      |              | if-2b 172.31.15.176 | if-2b fe80::84a:2ff:fe78:2746 |
+-----------------+------+---------+-------------+------+--------------+---------------------+-------------------------------+
| 88.0.7.1/32     | 3    | True    | 1007        |      |              | if-2c 172.31.15.176 | if-2c fe80::84a:2ff:fe78:2746 |
+-----------------+------+---------+-------------+------+--------------+---------------------+-------------------------------+
| 88.0.8.1/32     | 3    | True    | 1008        |      |              | if-2c 172.31.15.176 | if-2c fe80::84a:2ff:fe78:2746 |
+-----------------+------+---------+-------------+------+--------------+---------------------+-------------------------------+
| 88.0.9.1/32     | 3    | True    | 1009        |      |              | if-2c 172.31.15.176 | if-2c fe80::84a:2ff:fe78:2746 |
+-----------------+------+---------+-------------+------+--------------+---------------------+-------------------------------+
| 88.1.1.1/32     | 2    | False   | 101         |      | Positive     | if-2a 172.31.15.176 | if-2a fe80::84a:2ff:fe78:2746 |
+-----------------+------+---------+-------------+------+--------------+---------------------+-------------------------------+
| 88.1.4.1/32     | 2    | False   | 104         |      |              | if-2b 172.31.15.176 | if-2b fe80::84a:2ff:fe78:2746 |
+-----------------+------+---------+-------------+------+--------------+---------------------+-------------------------------+
| 88.1.7.1/32     | 2    | False   | 107         |      |              | if-2c 172.31.15.176 | if-2c fe80::84a:2ff:fe78:2746 |
+-----------------+------+---------+-------------+------+--------------+---------------------+-------------------------------+
| 88.2.2.1/32     | 1    | False   | 2           |      |              |                     |                               |
+-----------------+------+---------+-------------+------+--------------+---------------------+-------------------------------+
</pre>

We can see that the prefixes that are attached to spine-1-1 (88.1.1.1/32),
leaf-1-1 (88.0.1.1/32), leaf-1-2 (88.0.2.1), and lead-1-3 (88.0.3.1/32) are being
positively disaggregated.
These are precisely the prefixes located at or behind spine-1-1.

We can see the actual positive disaggregation TIEs that spine-2-1 originates by looking at the TIE
database:

<pre>
super-1-2> <b>show tie-db direction south originator 2 tie-type pos-dis-prefix</b>
+-----------+------------+----------------+--------+--------+----------+-----------------------------+
| Direction | Originator | Type           | TIE Nr | Seq Nr | Lifetime | Contents                    |
+-----------+------------+----------------+--------+--------+----------+-----------------------------+
| South     | 2          | Pos-Dis-Prefix | 3      | 1      | 597930   | Pos-Dis-Prefix: 88.0.1.1/32 |
|           |            |                |        |        |          |   Metric: 3                 |
|           |            |                |        |        |          | Pos-Dis-Prefix: 88.0.2.1/32 |
|           |            |                |        |        |          |   Metric: 3                 |
|           |            |                |        |        |          | Pos-Dis-Prefix: 88.0.3.1/32 |
|           |            |                |        |        |          |   Metric: 3                 |
|           |            |                |        |        |          | Pos-Dis-Prefix: 88.1.1.1/32 |
|           |            |                |        |        |          |   Metric: 2                 |
+-----------+------------+----------------+--------+--------+----------+-----------------------------+
</pre>

### Spine-3-1

Now let's head over to spine-3-1 which is PoD 3's spine router in plane 1.

It has received the positive disaggregation TIE that was originated by super-1-2:

<pre>
spine-3-1> <b>show tie-db direction south originator 2 tie-type pos-dis-prefix</b>
+-----------+------------+----------------+--------+--------+----------+-----------------------------+
| Direction | Originator | Type           | TIE Nr | Seq Nr | Lifetime | Contents                    |
+-----------+------------+----------------+--------+--------+----------+-----------------------------+
| South     | 2          | Pos-Dis-Prefix | 3      | 1      | 604782   | Pos-Dis-Prefix: 88.0.1.1/32 |
|           |            |                |        |        |          |   Metric: 3                 |
|           |            |                |        |        |          | Pos-Dis-Prefix: 88.0.2.1/32 |
|           |            |                |        |        |          |   Metric: 3                 |
|           |            |                |        |        |          | Pos-Dis-Prefix: 88.0.3.1/32 |
|           |            |                |        |        |          |   Metric: 3                 |
|           |            |                |        |        |          | Pos-Dis-Prefix: 88.1.1.1/32 |
|           |            |                |        |        |          |   Metric: 2                 |
+-----------+------------+----------------+--------+--------+----------+-----------------------------+
</pre>

As far as the SPF calculation on spine-3-1 is concerned, the positive disaggregation prefixes
are treated just the same as normal prefixes:
spine-3-1 calculates the shortest path to each of those prefixes.

<pre>
spine-3-1> <b>show spf direction north</b>
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

And finally spine-3-1 installs routes to the positively disaggregated prefixes in the
routing information base (RIB):

<pre>
spine-3-1> <b>show route family ipv4</b>
IPv4 Routes:
+-------------+-----------+-----------------------+
| Prefix      | Owner     | Next-hops             |
+-------------+-----------+-----------------------+
| 0.0.0.0/0   | North SPF | if-107d 172.31.15.176 |
|             |           | if-107e 172.31.15.176 |
+-------------+-----------+-----------------------+
| 88.0.1.1/32 | North SPF | if-107e 172.31.15.176 |
+-------------+-----------+-----------------------+
| 88.0.2.1/32 | North SPF | if-107e 172.31.15.176 |
+-------------+-----------+-----------------------+
| 88.0.3.1/32 | North SPF | if-107e 172.31.15.176 |
+-------------+-----------+-----------------------+
| 88.0.7.1/32 | South SPF | if-107a 172.31.15.176 |
+-------------+-----------+-----------------------+
| 88.0.8.1/32 | South SPF | if-107b 172.31.15.176 |
+-------------+-----------+-----------------------+
| 88.0.9.1/32 | South SPF | if-107c 172.31.15.176 |
+-------------+-----------+-----------------------+
| 88.1.1.1/32 | North SPF | if-107e 172.31.15.176 |
+-------------+-----------+-----------------------+
</pre>

As well as in the forwarding information base (FIB):

<pre>
spine-3-1> <b>show forwarding family ipv4</b>
IPv4 Routes:
+-------------+-----------------------+
| Prefix      | Next-hops             |
+-------------+-----------------------+
| 0.0.0.0/0   | if-107d 172.31.15.176 |
|             | if-107e 172.31.15.176 |
+-------------+-----------------------+
| 88.0.1.1/32 | if-107e 172.31.15.176 |
+-------------+-----------------------+
| 88.0.2.1/32 | if-107e 172.31.15.176 |
+-------------+-----------------------+
| 88.0.3.1/32 | if-107e 172.31.15.176 |
+-------------+-----------------------+
| 88.0.7.1/32 | if-107a 172.31.15.176 |
+-------------+-----------------------+
| 88.0.8.1/32 | if-107b 172.31.15.176 |
+-------------+-----------------------+
| 88.0.9.1/32 | if-107c 172.31.15.176 |
+-------------+-----------------------+
| 88.1.1.1/32 | if-107e 172.31.15.176 |
+-------------+-----------------------+
</pre>

This we can see that positive disaggregation has achieved its goal and has installed exactly
the minimal set of routes to avoid the failed link, namely:

 1. Specific /32 routes for spine-1-1, leaf-1-1, leaf-1-2, and leaf-1-3 to send traffic only
    to super-1-2 and not to super-1-1.

 2. A default route for all other destinations to ECMP the traffic over both super-1-1 and
    super-1-2.

## Breaking the second link: negative disaggreation
