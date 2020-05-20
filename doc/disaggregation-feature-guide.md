# Aggregation

Aggregation is a concept that has existed in routing protocols since the dawn of time.
If you have some specific routes, say 10.1.0.0/16, 10.2.0.0/16, and 10.3.0.0/16 that all point to
the same next-hop then you can summarize those routes with a single less specific route
such as 10.0.0.0/8.
That less specific route is called an aggregate route.
The process of replacing several specific routes with single aggregate route is called aggregation.
The most extreme case of aggregation is replacing all routes in the route table with a
default route 0.0.0.0/0 (or ::0/0 in the case of IPv6).

The most common use case for aggregation is to reduce the size of the route table by removing
details where they are not needed. For example, within their own network, Internet Service
Providers (ISPs) need specific routes to each of their customers. However, ISPs typically only
advertise a single aggregate route for their entire address space to other ISPs.

Most existing routing protocols (BGP, OSPF, ISIS, ...) allow you to manually configure aggregation.

# Disaggregation

The concept of disaggregation has also been around for a long time.
Disaggregation is the opposite of aggregation: it take a single less specific route (the aggregate
route) and splits it up into several more speficic routes.

The most common use case for disaggregation is traffic engineering. For example, an enterprise
that is BGP dual-homed to two service providers, may split its address space (described by an
aggregate) into two more speficic prefixes, and advertise one to each service provider.
That way, incoming traffic is split across the two service providers, even one service provider
is always the shortest path.

Most existing routing protocols (BGP, OSPF, ISIS, ...) provide mechanisms to manually configure
disaggregation.
There exist so-called BGP optimizers that automatically configure BGP disaggregation for
traffic engineering purposes. These are separate appliances, not something that is build into
the BGP protocol itself.

# The Routing In Fat Trees (RIFT) protocol

Routing in Fat Trees (RIFT) is a new routing protocol being defined in the Internet Engineering
Task Force (IETF). It has an open source implementation and at least one commercial implementation.

RIFT is optimized for large networks that have a highly structured topology known as a fat tree
or Clos topology.
One of the main (but not the only) use cases for RIFT is to be a scalable and fast-converging
interior gateway protocol (IGP) for the underlay in large-scale data centers.

RIFT brings several innovations to the table, including:

 * RIFT is anisotropic: is a link-state protocol north-bound and a distance-vector protocol
   south-bound. This combines the advantages of link-state with the advantags of distance-vector
   / path-vector.

 * Scalability: RIFT supports large data center networks without the need for splitting the network
   into multiple areas.

 * Very fast convergence, even in very large networks.

 * Zero touch provisioning (ZTP) to virtually eliminate the need for configuration and auto-detect
   miscabling.

 * A built-in flooding reduction mechanism to eliminate flooding storms in densely connected
   topologies such as fat trees.

 * Automatic aggregation. In the absence of failures, each node only needs a single equal-cost
   multi-path (ECMP) default route pointing north. This reduces the size of the routing table
   at the edge, and hence reduces the cost of top-of-rack switches.

 * Automatic disaggregation. In the even of a failure, the north-bound default route is
   automatically disaggregated into more specific routes, but only to the extent needed to route
   around the failure.

 * Model-based (Thrift) specification of the routing protocol messages. This speeds up development,
   enhances interoperability, and mosts importantly improves security by removing most message
   parsing vulnerabilities.

 * Much more (see [this presentation](https://www.slideshare.net/apnic/routing-in-fat-trees)).

# RIFT automatic disaggregation

In this guide we focus on one particular feature of RIFT, namely automatic disaggregation.
Automatic disaggregation is one of the most novel and most interesting innovations in the RIFT
protocol.

In most existing protocols (BGP, OSPF, ISIS) disaggregation requires extensive manual configuration.
In RIFT, by contrast, disaggregation is fully automatic without the need for any configuration.

In most existing protocols, disaggregation is an optional feature that is mainly used for traffic
engineering.
RIFT, on the other hand, relies on disaggregation as an essential feature to recover from failures.
In the absence of a failure, RIFT routers only have a default route for the north-bound direction.
When a failure occurs, RIFT automatically triggers disaggregation to install more specific
north-bound routes to route traffic around the failure.
For that reason, disaggregation is always enabled in RIFT;
it is not an optional feature and it cannot be disabled.

There are actually two flavors of disaggregation in RIFT:

 * Positive disaggregation is used to deal with most types of failures. It works by the repair path
   "attracting" traffic from the broken path by advertising a more specific route.
   Positive disaggregation in RIFT works very similar to
   how disaggregation works in existing protocols, except that it is triggered automatically
   instead of configured manually.

 * Negative disaggregation is used to deal with a very particular type of failure that only occurs
   only in very large data centers, so-called multi-plane fat trees (we will explain what that is
   later). It works by the broken path "repelling" traffic towards the repair path by advertising
   a so-called negative route. Negative
   disaggregation uses completely new mechanisms that (as far as we know) do not have any equivalent
   in widely deployed existing protocols. 
 
In this guide we describe how both of these flavors of disaggregation work from a RIFT protocol
point of view (i.e. not tied to any particular implementation).
The open source implementation of RIFT offers two features guides to describe the nitty-gritty
details (including
command-line interface examples) of disaggregation:

 * The [positive disaggregation feature guide](positive-disaggregation-feature-guide.md).

 * The [negative disaggregation feature guide](negative-disaggregation-feature-guide.md).

A quick note on terminology before we proceed. In this document we use term node as a synonym for
router or layer 3 switch. And we use terms leaf, spine, and superspine for the layers
of nodes in a 3-layer fat tree topology. In a 3-layer topology, a superspine node is also known as
a top-of-fabric node, and a a spine node is also known as a a top-of-pod node (where pod stands
for point-of-deployment). Finally, we treat a fat tree topology as a synonym for a Clos topology,
and we treat a 3-layer topology as a synonym for a 5-stage topology.

# RIFT route tables in the absence of failures

As mentioned before,
one of the best known characteristics of RIFT is that it is a link-state protocol north-bound and
a distance-vector protocol south-bound. 
One consequence of that is that the RIFT route tables typically contain:

 * Specific routes for all south-bound traffic towards the servers attached to the leaf switches.
   These are typically  host /32 (for IPv4) or /128 (for IPv6) routes, but it could be something
   less specific as well.

 * Fabric default routes for all north-bound traffic. These are 
   typically 0.0.0.0/0 and ::0/0, but it could be something more specific as well.

The following figure shows typical RIFT route tables in a small 3-level fat tree topology.
The leaf nodes contain only a single north-bound default route. The superspine nodes contain
only host-specific south-bound routes. And the spine nodes contain a mixture.

![RIFT Typical Route Tables](https://brunorijsman-public.s3-us-west-2.amazonaws.com/diagram-rift-typical-route-tables.png)

If there are no failures (no broken links and no broken nodes) anywhere in the topology, then
default routes are just fine.
Each node can just "spray" all north-bound traffic accross all parent nodes using a equal cost
multi-path (ECMP) default route. The Clos topology guarantees that (in the absence of failures)
it doesn't matter which parent node is chosen. Any parent node is able to reach the final
destination at the same cost as any other parent node.

As a concrete example, have a look at the above figure and
consider the traffic from leaf-1-1 to leaf-2-2.
Leaf-1-1 can pick either spine-1-1 or spine-1-2 as the next-hop for sending traffic to leaf-2-2.
It doesn't matter which spine leaf-1-1 picks.
Both spine-1-1 and spine-1-2 have a path to leaf-2-2, and one path is not better than the other
(they are equal cost).
Everything we have said is not only true for destination leaf-2-2, but for any destination leaf.
For that reason, leaf-1-1 only needs a default route with ECMP next-hops spine-1-1 and spine-1-2.

Similarly, spine-1-1 can send traffic destined for leaf-2-2 to either super-1 or super-2.
Once again it, doesn't matter. So once again, the spines only need ECMP default routes for
north-bound traffic.

# RIFT TIE messages in the absence of failures

Consider the following leaf-spine fabric:

![RIFT Clos 3x3 No Failures](https://brunorijsman-public.s3-us-west-2.amazonaws.com/diagram-rift-clos-3-x-3-no-failure-default-only.png)

The following sequence of RIFT messages leads to the installation of a default route in the
Routing Information Base (RIB) and Forwarding Information Base (FIB) of each leaf node.
In this example, we are looking at leaf-1-1 in particular.

 1. All the RIFT nodes have exchanged Link Information Element (LIE) messages and have established
    adjacencies.

 2. Then, each spine node sends a South Prefix Toplogie Information Element (TIE) message to each
    of the leafs to advertise a default route.

 3. Thus, each leaf node receives a South-Prefix-TIE with a default route from each of its spine nodes.

 4. This results in each leaf node installing an ECMP default north-bound route that "sprays" all
    traffic over all three spine nodes. Technically, you could say that the route is a result of
    the leaf running a north-bound Shortest Path First (SPF) algorithm, but since South-TIEs are
    not propagated, it is a trivial SPF.

Make a mental note of the fact that the traffic from leaf-1 to leaf-3 is spread equally across
all three spine nodes. This will turn out to be important later on. (We are assuming here that
the traffic consists of a sufficient number of flows, allowing ECMP hashing to do its job.)

# RIFT disaggregation triggered by failures

Needing only default routes in the happy case of no failures is all good and well, but we have
to consider the unhappy scenario as well. What if one or more links or nodes
are down? In this case a simple default route for all north-bound traffic is not going to work.

Automatic disaggregation (either the positive or the negative flavor) is RIFT's mechanism for
recovering from failures by installing more specific routes to circumvent the failure.
The word disaggregation is simply a fancy word for using a more specific route instead of the default
route.

To figure out how automatic disaggregation works exactly, we must delve into the following
questions:

 * How does RIFT know a failure occured?

 * How does RIFT know which destination prefixes are broken and need to be repaired using
   disaggregation?

 * How does RIFT figure out what the alternative path is that use be used to repair the traffic?

 * How does RIFT decide whether to use positive disaggregation (i.e. point the traffic towards the
   good path) or negative disaggregation (i.e. point the traffic away from the broken path)?

 * What is the exact mechanism that positive disaggregation uses to point traffic towards the good
   path?

 * What is the exact mechanism that negative disaggregation uses to point traffic away from the
   broken path?

We shall answer these questions separately for positive and negative disaggregation.

# RIFT positive disaggregation

## Positive disaggregation on the spine nodes

We will explain how positive disaggregation works using the following example, where the link
between spine-1 and leaf-3 fails (as indicated by the red cross):

![RIFT Clos 3x3 Failures repaired by positive disaggregation](https://brunorijsman-public.s3-us-west-2.amazonaws.com/diagram-rift-clos-3-x-3-failure-pos-disagg.png)

The first thing to observe is that having only a default route on leaf-1 is not good enough anymore.
Why not? Let's see what happens if leaf-1 sends a packet to leaf-3. The default route has a 1/3rd
chance of sending the packet to spine-1, a 1/3rd chance for spine-2, and a 1/3rd chance for spine-3.
If it happens to choose spine-1, the packet will be dropped, because spine-1 cannot get to leaf-3.

Positive disaggregation detects and recovers from this failure as follows:

 1. Spine-2 knows exactly which south-bound ajacencies spine-1 has.
    That's because all leaf nodes reflect spine-1's South-Node-TIE, which contains spine-1's
    adjacencies.
 
 2. Spine-2 now looks at the next-hops for each of its own south-bound routes.
    Let's say spine-2 looks at the south-bound route for prefix P with next-hops NH1, NH2, ...,
    NHn. Spine-2 then asks itself the question: can spine-1 also reach prefix P?

 3. The answer is "_Yes, spine-1 can reach P_" if spine-1 has an adjacency to at least one of
    the next-hops NH1, NH2, ..., NHn. In this case spine-2 does nothing.

 4. The anwer is "_No, spine-1 cannot reach P_" if spine-1 does not have any adjacency to any of
    the next-hops NH1, NH2, ...., NHn. In that case, spine-2 triggers positive disaggregation:

    a. Spine-2 uses a "South Positive Disaggregation Prefix TIE" to advertise a specific route
       for prefix P south-bound to all leaves. In this example, spine-2 advertises a route
       for 2.0.0.3/32.

    b. Since this route is more specific than the default route, all leaves will start sending
       traffic for destination prefix P to spine-2 instead of following the default route.

    c. The net effect of this is that spine-2 "attracts" the traffic away from the failed link
       on spine-1.
    
 5. It's not just spine-2 that looks for broken links on spine-1 and routes around those failures
    using positive disaggregation.
    In general, every node is monitoring every other node at the same level in this manner.
    After this example has fully converged, the leaf nodes will end up with an ECMP 2.0.0.3/32 route
    for leaf-3 that ECMP's the traffic across spine-2 and spine-3 (but not spine-1).

Note that step 5 takes place independently and asynchronously on each spine node.
Thus, as the positive disaggregation process is converging, the host-specific positive disaggregate
route starts out with a single next-hop, then two ECMP next-hop, until it finally ends up with N-1
ECMP next-hops where N is the number of spine nodes.

This can be a problem. The traffic that used to be spread out over N nodes is temporarily 
concentrated on a single spine node, then two spine nodes, until it is finally spread out
again over N-1 spine nodes. This is referred to as the "transitory incast" problem. Later we will
see how negative disaggregation avoids this problem.

## Positive disaggregation on the superspine nodes



====================================================================================================



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
    reach leaf-3. If anyone wants to send traffic to any of the prefixes advertised by leaf-3 they
    can give it to spine-2 or spine-3, and they will deliver it to leaf-3."

 2. On the other hand, spine-1 also knows that it does not have any adjacency to leaf-3 itself. In
    fact it may never have had any adjacency with leaf-3. Spine-1 concludes: "I myself cannot
    reach leaf-3. If anyone wants to send traffic to any of the prefixes advertised by leaf-3
    they better not give it me because I will blackhole it."

 3. Spine-1, also being a helpful and altruistic node thinks: "I must warn all the leaf nodes!
    Evidently somewhere out there, there is this leaf-3 node, but I don't know how to get to it.
    I must warn everyone not to send any traffic destined for leaf-3 to me."

 4. How does spine-1 warn the other nodes? By advertising a special kind of 
    host-specific 2.0.0.3/32 route for
    leaf-3 to all leaf nodes.
    This route is called a negative disaggregation route.
    Such a negative route has a very special meaning: it means "Please do _not_ send traffic
    for this prefix to me. If you have another route to this same prefix that avoids me, use it,
    even if that other route is less specific, e.g. the default route."

 5. When the leaf nodes receive such a negative disaggregation route, it installs it as a
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

In step 6, there are some special rules to deal with the interaction between positive and
negative disaggregation that we skip here for the sake of simplicity.

Negative disaggregation has two advantages relative to positive disaggregation:

 1. It is simpler in the sense that it greatly reduces the amount of routes that have to be
    advertised to recover from a failure. Instead of N-1 nodes having to advertise a positive
    disaggregate route, only 1 node has to advertise a negative disaggregate route.
 
 2. For this exact same reason, negative disaggregation avoids the transitory incast problem that
    we described above.

# On the relationship between positive and negative disaggregation


@@@




By default, RIFT-Python behaves as follows:

 1. Any node can _originate_ a positive disaggregate prefix TIE. This is triggered
    the observation that the originating node has a south-bound adjacency that is missing on
    some same-level node.

 2. Each node always processes all _received_ positive disaggregate TIEs, includes them in the SPF,
    and installs them in the RIB and FIB as required.

 3. Top-of-fabric nodes that have at least one east-west inter-fabric ring interface
    can _originate_ a negative disaggregate prefix TIE. This is triggered by observing
    a falled leaf node in the special south-bound SPF that includes east-west links.

 4. Each node always processes all _received_ negative disaggregate TIEs:
 
    a. Includes them in the SPF, and installs them in the RIB and FIB as required.

    b. Propagates them if required. This is triggered
    by the fact that a negative disaggregate prefix TIE for a given prefix was received from all
    parent routers.

To summarize: by default RIFT-Python uses a combination of both positive and negative
disaggregation.
