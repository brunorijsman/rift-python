# Flooding Reduction Feature Guide

## Example network

The examples in this chapter are based on the following topology.

![Topology Diagram](https://brunorijsman-public.s3-us-west-2.amazonaws.com/diagram_clos_2pod_4leaf_4spine_4super.png)

_Figure 1: Topology diagram._


## North-bound without flooding reduction

Consider the TIEs that are flooded north-bound by some leaf node, let's pick leaf-1-1 for the sake
of discussion (shaded red in the diagram below). Leaf-1-1 will flood its TIEs to each of its four
north-bound parent spines, which are spine-1-1, spine-1-2, spine-1-3, and spine-1-4. Each of those
four spines, in turn, will propagate the TIEs further north-bound to each of their four north-bound
parent super-spines, which are super-1, super-2, super-3, and super-4. This flooding of TIEs is
shown by the red arrows below.

Each super-spine receives four copies of each leaf TIE.
In the diagram below you can see that super-1, for example, receives four identical copies
of the TIEs from leaf-1-1 (red arrows) and also four identical copies of the TIEs from leaf-1-2
(green arrows).

![Before flooding reduction](https://brunorijsman-public.s3-us-west-2.amazonaws.com/diagram_clos_2pod_4leaf_4spine_4super-before-floodred.png)

_Figure 2: Before flooding reduction._

In real life things are actually *much* worse than what is apparent from the discussion above.
In the above example, we only had four spine nodes in each POD just to keep the diagram simple.
In real life, there would be many more spine nodes per POD. 
16 or 32 spines are common, and in extreme cases a POD can contain 64, 128, or even 256 spines.
In such more realistic topologies each super-spine would receive correspondingly many more copies
of each TIE (16, 32, 64, 128, 256 etc.)

On a more positive note, even without flooding reduction, in RIFT the situation is not as bad as it
would have been in a general purpose link-state protocol that is not optimized for fat-tree
topologies.
This is because RIFT is "link-state towards to spines and distance-vector towards the leafs." 
In RIFT, a super-spine will not propagate a TIE received from one spine to the other
spines.
In the above diagram, for example, when super-1 receives a north-bound TIE from spine-1-1,
it will *not* turn it around and propagate it south-bound to each of the of the seven other spines
in both PODs.
It RIFT *would* have done that (as a general purpose link state protocol would have done), the
problem would take on disastrous proportions: each spine would receive 4 * 4 = 16 copies of each TIE
in this example. 
(Or in general N * M copies, where N is the number of spines per POD and M is the number of super-spines.)

## North-bound with flooding reduction

### Removing redundant flooding

If you look at the above diagram, it is immediately clear that a lot of the TIE flooding is
redundant.
There is absolutely no need for each super-spine to receive so many copies of the same leaf TIE.

The goal of the "flooding reduction" feature is to automatically remove most of the unnecessary
flooding, as shown in the diagram below.

Note that flooding in the south-bound direction is not a problem, because in the south-bound
direction, TIEs are (normally) not propagated. Thus, flooding reduction is only useful for
north-bound flooding.

![After flooding reduction](https://brunorijsman-public.s3-us-west-2.amazonaws.com/diagram_clos_2pod_4leaf_4spine_4super-after-floodred.png)

_Figure 3: After flooding reduction._

In the above diagram, the reduction in flooding does not seem that dramatic and you
might wonder whether it is worth the trouble.
But keep in mind that is mostly because our diagrams are simple and have only a few spine nodes.
If we had many more spine nodes (as is the case in real networks) the savings would be much more apparent (but the diagrams would become unreadable).

### Redundancy

You will notice that in the above diagram, each super-spine still receives two copies of each TIE.
Why did we do that? Wouldn't it be enough if each super-spine received only a single copy?
Well, yes, technically a single copy would be enough. 
But that would mean that we would flood only along a single flooding path. 
If any link failed on that flooding path, the super-spine would be cut off and stop receiving TIEs,
at least until the flooding reduction mechanism could reconverge and pick a different flooding path.

For better redundancy and faster reconvergence after a failure, we want there to be some number
(at least 2) of redundant flooding paths to each super-spine. This redundancy factor is called R
in the RIFT specification. 

### The concept of a flood repeater

To understand how flooding reduction works in RIFT, you first need to understand the concept of a
flood repeater (also known as a flooding repeater, flood leader, or flooding leader).

The basic idea is that each leaf node chooses some small subset of its parent spine nodes to be
responsible for propagating the north-bound leaf TIE further north towards the spine nodes.

Those chosen spines are the flood repeaters. The leaf still floods all of its TIEs to all of the
spines, but only the flood repeater spines propagate the leaf TIEs further north.

More generally, if there are more than 3 levels in the fat tree topology, each router elects
some subset of its north-bound parent routers to be a flood repeater, as long as those parents
are not the top-of-fabric.

To keep this tutorial simple, all of our examples assume that the spines are the flood repeaters and that the super-spines are the top-of-fabric.
But everything we say is easily generalized to more than 3 levels, and the RIFT-Python
implementation supports more than 3 levels.

### How many flood repeaters?

How many flood repeaters does a given leaf choose?
Clearly, because of the redundancy and reconverge speed considerations discussed earlier, there
should be more than one flood repeater.
Well, how many then? Two? Three? Some configurable number?

There is indeed a configurable number in RIFT, called the redundancy factor R (the default value in
RIFT-Python is 2). The redundancy factor influences the number of flood repeaters but in an indirect
manner.

The way that it works is that a leaf node will start with one flood repeater, and then add another
one, and maybe another one, and will keep going, until each grand-parent super-spine of the leaf
will receive no less than R copies of each TIE flooded by the leaf.

If there are no failures in the network, then the leaf will end up choosing R flood repeaters.

But as you can see in the example below, if there are some broken links, then the leaf may need to
chose more then R flood-repeater spines to "have enough coverage" for the super spines.


![Flood repeater election scenario with link failures](https://brunorijsman-public.s3-us-west-2.amazonaws.com/diagram_clos_2pod_4leaf_4spine_4super-flood-repeater-election.png)

_Figure 4: Flood repeater election scenario with link failures._

This example is a little bit of an extreme scenario with lots of link failures, but it makes it
easier to follow the example.

The question we are asking is: which spine nodes should leaf-1-1 pick as flood repeaters to make
sure that each super-spine gets at least two copies of the TIEs flooded by leaf-1-1.

Well, let's see. 

Neither spine-1-1 nor spine-1-2 has any link to super-3. Thus, spine-1-3 and spine-1-4 are the only
two spine nodes connected to super-3. Clearly, if super-3 needs to get two copies of each TIE, then
spine-1-3 and spine-1-4 must both be in the set of flood repeaters.

Similarly, neither spine-1-3 nor spine-1-4 has any link to super-1. Thus, spine-1-1 and spine-1-2
are the only two spines connected to super-1. Clearly, if super-1 needs to get two copies of each
TIE, then spine-1-1 and spine-1-2 must both be in the set of flood repeaters.

The conclusion is that in this scenario, leaf-1-1 will choose all four spines to be flood repeaters.
This is needed to make sure that each super-spine gets at least two copies of each TIE. In other
words, this is needed to achieve the desired super-spine coverage of redundancy factor R=2.

In this case, the outcome is a little bit extreme, in the sense that all spines in the POD end
up being flood repeaters. In other words, it is just the same as having no flooding reductions.
But such extreme scenarios become extremely unlikely if the number of spines is greater.

### Each leaf makes its own independent decision

Each leaf makes its own local decision when choosing its flood repeaters.

There is no special leaf-to-leaf communication to coordinate the election of the flood repeaters.

In fact, there is no requirement that the leaves use the same algorithm for flood repeater election.
It is perfectly fine if each leaf node uses a completely different proprietary algorithm for flood
repeater election. This is okay as long as each algorithm chooses the flood repeaters in such a
manner that each super-spine is sufficiently covered to meet the required redundancy R.

For that reason, the RIFT specification does not mandate a flood repeater election algorithm.
However, there is an example algorithm in the specification, and RIFT-Python implements exactly that
algorithm.

### Spreading the burden of being a flood repeater

If each leaf elects its flood repeaters independently, there is a risk that the all elect the same
spines as flood repeaters.

To understand that danger, let's revisit figure 3 above again. 

Imagine, for a second, that all four leaves leaf-1-1, leaf-1-2, leaf-1-3, and leaf-1-4 elected the
same spines (say spine-1-1 and spine-1-2) as the flood repeaters.
That would be unfair and lead to non-optimal flooding performance because all of the burden for
doing the flooding would land on the shoulders of spine-1-1 and spine-1-2. The other spines,
spine-1-3 and spine-1-4, but get away scot-free without having to do any flooding.

Thankfully, that did not happen in figure 3. We can see that leaf-1-1 picked spine-1-1 and spine-1-3
as the flood repeaters, and that leaf-1-2 picked spine-1-1 and spine-1-4 as the flood repeaters.
The figure does not show which flood repeaters leaf-1-3 and leaf-1-4 elected, but it is already
clear that the burden of flooding is spread more evenly over all the spines.

The example algorithm in the specification achieves this "fair spreading of the flooding burden"
as follows.

 1. As mentioned before, the flood repeater election process chooses one spine as a flood repeater,
    and then another, and then possibly another, until the required redundancy coverage R is
    achieved.

 2. The minimize the number of spines in the flood repeater set, the spines are considered in a
    specific order: the spines with the most adjacencies to super-spine nodes are considered first.

 3. If that was all that there was to the algorithm, each leaf would end up electing the same
    set of spines as flood repeaters. This is precisely what we want to avoid: we want to spread
    the burden of flooding across different spines.

  4. To achieve that, we make the sorting of the spines by number of super-spine adjacencies
     a little but "fuzzy" on purpose. We do that as follows.

  5. If two spine nodes have a similar number of super-spine adjacencies, they are considered to
     be equally desirable.
     We put them in an "equivalence group". After sorting spines, we randomize the sorted order
     within each equivalence group. 
     In real life, there will be few equivalence groups with large numbers of member spines.
     In that case, the election of flood repeater will be quite random.

The net result of this algorithm is that each leaf node tries to pick different flood repeaters,
while still avoiding very non-optimal flood repeaters (i.e. avoiding spines that have bad
connectivity to the super spines).

If all of this sounds very abstract, the concrete examples and show command output below should make 
it a bit more concrete.

And if all of this sounds very fuzzy and imprecise, let me remind you of what I said earlier:
there is no requirement to standardize the algorithm and there is no requirement that all leaves
run the same algorithm.

There is another subtle point to point out. In other link state routing protocols there are also
ongoing efforts to implement flooding reduction. Many of those efforts involve "pruning the flooding
topology", i.e. to pick a subset of the links to do the flooding over. That mental model of a pruned
flooding topology does not really work for the RIFT approach, because each leaf can pick a different
set of flood repeaters, and hence a different subset of the spine to super-spine links.

# Flooding reduction implementation

##  Perspective of leaf in the absence of link failures

Enough theory. Let's get our hands dirty and look at what it looks like in practice. We will look
at the show commands first and then at the (optional) configuration.

Let's assume we are using the topology shown in figure 1 and we are logged into router leaf-1-1.

Our configuration does not contain anything related to flooding reduction, but flooding reduction
is enabled by default.

A good place to start is to issue the `show flooding-reduction` command:

<pre>
leaf-1-1> <b>show flood</b>
Parents:
+-----------------+-----------+---------------------------+-------------+------------+----------+
| Interface       | Parent    | Parent                    | Grandparent | Similarity | Flood    |
| Name            | System ID | Interface                 | Count       | Group      | Repeater |
|                 |           | Name                      |             |            |          |
+-----------------+-----------+---------------------------+-------------+------------+----------+
| veth-1001c-103a | 103       | spine-1-3:veth-103a-1001c | 4           | 1: 4-4     | True     |
+-----------------+-----------+---------------------------+-------------+------------+----------+
| veth-1001b-102a | 102       | spine-1-2:veth-102a-1001b | 4           | 1: 4-4     | True     |
+-----------------+-----------+---------------------------+-------------+------------+----------+
| veth-1001a-101a | 101       | spine-1-1:veth-101a-1001a | 4           | 1: 4-4     | False    |
+-----------------+-----------+---------------------------+-------------+------------+----------+
| veth-1001d-104a | 104       | spine-1-4:veth-104a-1001d | 4           | 1: 4-4     | False    |
+-----------------+-----------+---------------------------+-------------+------------+----------+

Grandparents:
+-------------+--------+-------------+-------------+
| Grandparent | Parent | Flood       | Redundantly |
| System ID   | Count  | Repeater    | Covered     |
|             |        | Adjacencies |             |
+-------------+--------+-------------+-------------+
| 1           | 4      | 2           | True        |
+-------------+--------+-------------+-------------+
| 2           | 4      | 2           | True        |
+-------------+--------+-------------+-------------+
| 3           | 4      | 2           | True        |
+-------------+--------+-------------+-------------+
| 4           | 4      | 2           | True        |
+-------------+--------+-------------+-------------+

Interfaces:
+-----------------+---------------------------+-----------+-----------+-----------+----------------+----------------+
| Interface       | Neighbor                  | Neighbor  | Neighbor  | Neighbor  | Neighbor is    | This Node is   |
| Name            | Interface                 | System ID | State     | Direction | Flood Repeater | Flood Repeater |
|                 | Name                      |           |           |           | for This Node  | for Neighbor   |
+-----------------+---------------------------+-----------+-----------+-----------+----------------+----------------+
| veth-1001a-101a | spine-1-1:veth-101a-1001a | 101       | THREE_WAY | North     | False          | Not Applicable |
+-----------------+---------------------------+-----------+-----------+-----------+----------------+----------------+
| veth-1001b-102a | spine-1-2:veth-102a-1001b | 102       | THREE_WAY | North     | True           | Not Applicable |
+-----------------+---------------------------+-----------+-----------+-----------+----------------+----------------+
| veth-1001c-103a | spine-1-3:veth-103a-1001c | 103       | THREE_WAY | North     | True           | Not Applicable |
+-----------------+---------------------------+-----------+-----------+-----------+----------------+----------------+
| veth-1001d-104a | spine-1-4:veth-104a-1001d | 104       | THREE_WAY | North     | False          | Not Applicable |
+-----------------+---------------------------+-----------+-----------+-----------+----------------+----------------+
</pre>

There is a lot of information here, so lets go over it section by section.

Before we dive in, let me remind you that we are looking at a 3-level (= 5-stage) Clos topology,
and we are logged in to a leaf node. So, when the output says "parent" it means "spine", and when
the output says "grand-parent" it means "super-spine".

### Parents

The first section lists all the parents of the node:

<pre>
Parents:
+-----------------+-----------+---------------------------+-------------+------------+----------+
| Interface       | Parent    | Parent                    | Grandparent | Similarity | Flood    |
| Name            | System ID | Interface                 | Count       | Group      | Repeater |
|                 |           | Name                      |             |            |          |
+-----------------+-----------+---------------------------+-------------+------------+----------+
| veth-1001c-103a | 103       | spine-1-3:veth-103a-1001c | 4           | 1: 4-4     | True     |
+-----------------+-----------+---------------------------+-------------+------------+----------+
| veth-1001b-102a | 102       | spine-1-2:veth-102a-1001b | 4           | 1: 4-4     | True     |
+-----------------+-----------+---------------------------+-------------+------------+----------+
| veth-1001a-101a | 101       | spine-1-1:veth-101a-1001a | 4           | 1: 4-4     | False    |
+-----------------+-----------+---------------------------+-------------+------------+----------+
| veth-1001d-104a | 104       | spine-1-4:veth-104a-1001d | 4           | 1: 4-4     | False    |
+-----------------+-----------+---------------------------+-------------+------------+----------+
</pre>

The leaf knows who its parent spines are based on the South-Node-TIEs received from those parent
spines.

The table contains the following fields:

 * *Interface Name*: The name of the local interface on the leaf to which the parent spine is 
   connected.

 * *Parent System ID*: The system ID of the parent spine node.

 * *Parent Interface Name*: The name of the remote interface on the parent spine that connects
   back to this leaf.

 * *Grandparent Count*: The number of north-bound adjacencies that the parent spine has its
   grand-parent super-spines. You might wonder how the leaf knows this, and the answer is that
   the South-Node-TIEs originated by the spine includes the north-bound adjacencies, although those
   are not used by North-bound SPF.

 * *Similarity Group*: The similarity group that the spine has been assigned to. The format is
   "G: A-B" where G is the index of the similarity group, A-B is the range of grandparent count
   for the group. In this example all spines are in the same similarity group, namely group 1
   which contains all spines with between 4 and 4 (so, exactly 4) super-spine adjacencies.

 * *Flood Repeater*: Whether or not the node has elected that particular spine as a flood repeater.
   In this example spine-1-2 and spine-1-3 have been elected as flood repeaters.

### Grandparents

Now lets look at the grandparents table.

<pre>
Grandparents:
+-------------+--------+-------------+-------------+
| Grandparent | Parent | Flood       | Redundantly |
| System ID   | Count  | Repeater    | Covered     |
|             |        | Adjacencies |             |
+-------------+--------+-------------+-------------+
| 1           | 4      | 2           | True        |
+-------------+--------+-------------+-------------+
| 2           | 4      | 2           | True        |
+-------------+--------+-------------+-------------+
| 3           | 4      | 2           | True        |
+-------------+--------+-------------+-------------+
| 4           | 4      | 2           | True        |
+-------------+--------+-------------+-------------+
</pre>

The leaf knows who its grandparent super-spines are based on the north-bound adjacencies
reported in the South-Node-TIEs received from the parent spines.

The table contains the following fields:

 * *Grandparent System ID*: The system ID of the grandparent super-spine.

 * *Parent Count*: The total number of parent spines that have a north-bound adjacency with that
   particular grandparent super-spine. In other words, how many south-bound adjacencies does the
   grandparent have to spines?

 * *Flood Repeater Adjacencies*: Out of those grandparent-to-spine adjacencies that were reported
   in the previous field, in how many cases is the spine a flood repeater?

 * *Redundantly Covered*: Now that we know by how many flood repeaters the grandparent super-spine
   is served, is that number enough? In other words, does that number meet the minimum redundancy
   requirement?

### Interfaces

Finally, let's look at the interfaces table:

<pre>
Interfaces:
+-----------------+---------------------------+-----------+-----------+-----------+----------------+----------------+
| Interface       | Neighbor                  | Neighbor  | Neighbor  | Neighbor  | Neighbor is    | This Node is   |
| Name            | Interface                 | System ID | State     | Direction | Flood Repeater | Flood Repeater |
|                 | Name                      |           |           |           | for This Node  | for Neighbor   |
+-----------------+---------------------------+-----------+-----------+-----------+----------------+----------------+
| veth-1001a-101a | spine-1-1:veth-101a-1001a | 101       | THREE_WAY | North     | False          | Not Applicable |
+-----------------+---------------------------+-----------+-----------+-----------+----------------+----------------+
| veth-1001b-102a | spine-1-2:veth-102a-1001b | 102       | THREE_WAY | North     | True           | Not Applicable |
+-----------------+---------------------------+-----------+-----------+-----------+----------------+----------------+
| veth-1001c-103a | spine-1-3:veth-103a-1001c | 103       | THREE_WAY | North     | True           | Not Applicable |
+-----------------+---------------------------+-----------+-----------+-----------+----------------+----------------+
| veth-1001d-104a | spine-1-4:veth-104a-1001d | 104       | THREE_WAY | North     | False          | Not Applicable |
+-----------------+---------------------------+-----------+-----------+-----------+----------------+----------------+
</pre>

All the output up until now was really just background information to understand what is going on.
This interfaces table reports the final result.

The most relevant fields in this table are:

 * *Interface Name*: The name of the local interface on the leaf node.

 * *Neighbor is Flood Repeater for This Node*: Has the neighbor (the spine in this case) been
   elected as a Flood Repeater? This is only relevant if the neighbor is a parent and not a
   top-of-fabric.

 * *This Node is Flood Repeater for Neighbor*: Has the neighbor elected this node as its flood
   repeater? This is only relevant if the neighbor is a child (which it is not in this case) and
   we are not top-of-fabric.

##  Perspective of spine in the absence of link failures

Now, let's keep the same topology and log in to a spine node (spine-1-1 in this case) and let's
look at its perspective on the flooding reduction situation:

<pre>
spine-1-1> <b>show flooding-reduction</b>
Parents:
+--------------+-----------+----------------------+-------------+------------+----------+
| Interface    | Parent    | Parent               | Grandparent | Similarity | Flood    |
| Name         | System ID | Interface            | Count       | Group      | Repeater |
|              |           | Name                 |             |            |          |
+--------------+-----------+----------------------+-------------+------------+----------+
| veth-101f-2a | 2         | super-2:veth-2a-101f | 0           | 1: 0-0     | False    |
+--------------+-----------+----------------------+-------------+------------+----------+
| veth-101e-1a | 1         | super-1:veth-1a-101e | 0           | 1: 0-0     | False    |
+--------------+-----------+----------------------+-------------+------------+----------+
| veth-101g-3a | 3         | super-3:veth-3a-101g | 0           | 1: 0-0     | False    |
+--------------+-----------+----------------------+-------------+------------+----------+
| veth-101h-4a | 4         | super-4:veth-4a-101h | 0           | 1: 0-0     | False    |
+--------------+-----------+----------------------+-------------+------------+----------+

Grandparents:
+-------------+--------+-------------+-------------+
| Grandparent | Parent | Flood       | Redundantly |
| System ID   | Count  | Repeater    | Covered     |
|             |        | Adjacencies |             |
+-------------+--------+-------------+-------------+

Interfaces:
+-----------------+--------------------------+-----------+-----------+-----------+----------------+----------------+
| Interface       | Neighbor                 | Neighbor  | Neighbor  | Neighbor  | Neighbor is    | This Node is   |
| Name            | Interface                | System ID | State     | Direction | Flood Repeater | Flood Repeater |
|                 | Name                     |           |           |           | for This Node  | for Neighbor   |
+-----------------+--------------------------+-----------+-----------+-----------+----------------+----------------+
| veth-101a-1001a | leaf-1-1:veth-1001a-101a | 1001      | THREE_WAY | South     | Not Applicable | False          |
+-----------------+--------------------------+-----------+-----------+-----------+----------------+----------------+
| veth-101b-1002a | leaf-1-2:veth-1002a-101b | 1002      | THREE_WAY | South     | Not Applicable | True           |
+-----------------+--------------------------+-----------+-----------+-----------+----------------+----------------+
| veth-101c-1003a | leaf-1-3:veth-1003a-101c | 1003      | THREE_WAY | South     | Not Applicable | False          |
+-----------------+--------------------------+-----------+-----------+-----------+----------------+----------------+
| veth-101d-1004a | leaf-1-4:veth-1004a-101d | 1004      | THREE_WAY | South     | Not Applicable | False          |
+-----------------+--------------------------+-----------+-----------+-----------+----------------+----------------+
| veth-101e-1a    | super-1:veth-1a-101e     | 1         | THREE_WAY | North     | False          | Not Applicable |
+-----------------+--------------------------+-----------+-----------+-----------+----------------+----------------+
| veth-101f-2a    | super-2:veth-2a-101f     | 2         | THREE_WAY | North     | False          | Not Applicable |
+-----------------+--------------------------+-----------+-----------+-----------+----------------+----------------+
| veth-101g-3a    | super-3:veth-3a-101g     | 3         | THREE_WAY | North     | False          | Not Applicable |
+-----------------+--------------------------+-----------+-----------+-----------+----------------+----------------+
| veth-101h-4a    | super-4:veth-4a-101h     | 4         | THREE_WAY | North     | False          | Not Applicable |
+-----------------+--------------------------+-----------+-----------+-----------+----------------+----------------+
</pre>

We can make the following observations:

 * Spine-1-1 has four parents (the super-spines)

 * Spine-1-1 has no grandparents

 * Spine-1-1 has not elected any of its parents to be flood repeaters, because they are all
   top-of-fabric

 * Spine-1-1 has been elected as flood repeater by one leaf, namely leaf-1-2.

 ##  Breaking some links

 Now, let's spice things up and break some links.

 While we are still logged in to spine-1-1, we use the following special command to simulate some
 link failures (namely link spine-1-1:super-1, spine-1-1:super-2, and spine-1-1:super-3)

 <pre>
spine-1-1> <b>set interface veth-101e-1a failure failed</b>
spine-1-1> <b>set interface veth-101f-2a failure failed</b>
spine-1-1> <b>set interface veth-101g-3a failure failed</b>
 </pre>
 
 We can see that the adjacencies have indeed gone down:

<pre>
spine-1-1> show interfaces
+-----------------+--------------------------+-----------+-----------+
| Interface       | Neighbor                 | Neighbor  | Neighbor  |
| Name            | Name                     | System ID | State     |
+-----------------+--------------------------+-----------+-----------+
| veth-101a-1001a | leaf-1-1:veth-1001a-101a | 1001      | THREE_WAY |
+-----------------+--------------------------+-----------+-----------+
| veth-101b-1002a | leaf-1-2:veth-1002a-101b | 1002      | THREE_WAY |
+-----------------+--------------------------+-----------+-----------+
| veth-101c-1003a | leaf-1-3:veth-1003a-101c | 1003      | THREE_WAY |
+-----------------+--------------------------+-----------+-----------+
| veth-101d-1004a | leaf-1-4:veth-1004a-101d | 1004      | THREE_WAY |
+-----------------+--------------------------+-----------+-----------+
| veth-101e-1a    |                          |           | ONE_WAY   |
+-----------------+--------------------------+-----------+-----------+
| veth-101f-2a    |                          |           | ONE_WAY   |
+-----------------+--------------------------+-----------+-----------+
| veth-101g-3a    |                          |           | ONE_WAY   |
+-----------------+--------------------------+-----------+-----------+
| veth-101h-4a    | super-4:veth-4a-101h     | 4         | THREE_WAY |
+-----------------+--------------------------+-----------+-----------+
</pre>

##  Perspective of lead in the presence of link failures

Going back to leaf-1-1, let's see what changed in the flooding reduction:

<pre>
leaf-1-1> <b>show flooding-reduction</b>
Parents:
+-----------------+-----------+---------------------------+-------------+------------+----------+
| Interface       | Parent    | Parent                    | Grandparent | Similarity | Flood    |
| Name            | System ID | Interface                 | Count       | Group      | Repeater |
|                 |           | Name                      |             |            |          |
+-----------------+-----------+---------------------------+-------------+------------+----------+
| veth-1001c-103a | 103       | spine-1-3:veth-103a-1001c | 4           | 1: 4-4     | True     |
+-----------------+-----------+---------------------------+-------------+------------+----------+
| veth-1001b-102a | 102       | spine-1-2:veth-102a-1001b | 4           | 1: 4-4     | True     |
+-----------------+-----------+---------------------------+-------------+------------+----------+
| veth-1001d-104a | 104       | spine-1-4:veth-104a-1001d | 4           | 1: 4-4     | False    |
+-----------------+-----------+---------------------------+-------------+------------+----------+
| veth-1001a-101a | 101       | spine-1-1:veth-101a-1001a | 1           | 2: 1-1     | False    |
+-----------------+-----------+---------------------------+-------------+------------+----------+

Grandparents:
+-------------+--------+-------------+-------------+
| Grandparent | Parent | Flood       | Redundantly |
| System ID   | Count  | Repeater    | Covered     |
|             |        | Adjacencies |             |
+-------------+--------+-------------+-------------+
| 1           | 3      | 2           | True        |
+-------------+--------+-------------+-------------+
| 2           | 3      | 2           | True        |
+-------------+--------+-------------+-------------+
| 3           | 3      | 2           | True        |
+-------------+--------+-------------+-------------+
| 4           | 4      | 2           | True        |
+-------------+--------+-------------+-------------+

Interfaces:
+-----------------+---------------------------+-----------+-----------+-----------+----------------+----------------+
| Interface       | Neighbor                  | Neighbor  | Neighbor  | Neighbor  | Neighbor is    | This Node is   |
| Name            | Interface                 | System ID | State     | Direction | Flood Repeater | Flood Repeater |
|                 | Name                      |           |           |           | for This Node  | for Neighbor   |
+-----------------+---------------------------+-----------+-----------+-----------+----------------+----------------+
| veth-1001a-101a | spine-1-1:veth-101a-1001a | 101       | THREE_WAY | North     | False          | Not Applicable |
+-----------------+---------------------------+-----------+-----------+-----------+----------------+----------------+
| veth-1001b-102a | spine-1-2:veth-102a-1001b | 102       | THREE_WAY | North     | True           | Not Applicable |
+-----------------+---------------------------+-----------+-----------+-----------+----------------+----------------+
| veth-1001c-103a | spine-1-3:veth-103a-1001c | 103       | THREE_WAY | North     | True           | Not Applicable |
+-----------------+---------------------------+-----------+-----------+-----------+----------------+----------------+
| veth-1001d-104a | spine-1-4:veth-104a-1001d | 104       | THREE_WAY | North     | False          | Not Applicable |
+-----------------+---------------------------+-----------+-----------+-----------+----------------+----------------+
</pre>

We can observe the following:

 * Leaf-1-1 still has all spines as parents. However, spine-1-1 only has one grandparent left.

 * Spine-1-1 has been put in its own similarity group, namely group "2: 1-1", which is group number
   2 which contains all parents with 1 grandparent. RIFT has a parameter similarity factor (whose
   default value is 2 in RIFT-Python). If the grandparent count differs by more than this number,
   the spine gets put in its own similarity group. Grandparent count 4 and grandparent count 1
   differ by more than 2, and that why spine-1-1 it in its own similarity group.

 * The spines in the parent table are sorted by desirability, and we can notice that spine-1-1
   moved to the bottom because it has so few grandparents. The sorting is based on the similarity
   group number, and not the absolute grandparent count. This allows the spines which are flood
   repeater candidates to be randomly shuffled for better spreading of the flooding burden over
   spines, as discussed earlier.

 * The flood repeaters have not changed in this example. It is still spine-1-2 and spine-1-3 who
   are the flood repeaters for leaf-1-1. But if spine-1-1 had been a flood repeater, it would have
   lost its flood repeatership and some other spine would have been elected instead.