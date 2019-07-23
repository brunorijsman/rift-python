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

Each super-spine will receive four copies of each leaf TIE.
In the diagram below you can see that super-1, for example, will receive four identical copies
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

Once again, in the above diagram, the reduction in flooding does not seem that dramatic and you
might wonder whether it is worth the trouble.
But keep in mind that is mostly because our diagrams are simple and have only a few spine nodes.
If we had many more spine nodes (as is the case in real networks) the savings would be much more apparent (but the diagrams would become unreadable).

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
some subset of its north-bound parent routers to be a flood repeater.

### How many flood repeaters?

How many flood repeaters does a given leaf choose?
Clearly, because of the redundancy and reconverge speed considerations discussed earlier, there
should be more than one flood repeater.
Well, how many then? Two? Three? Some configurable number?

There is indeed a configurable number in RIFT, called the redundancy factor R (the default value in
RIFT-Python is 2). The redundancy factor influences the number of flood repeaters in an indirect
manner.

The way that it works is that a leaf node will start with one flood repeater, and then add another
one, and maybe another one, and will keep going, until each grand-parent super-spine of the leaf
will receive no less than R copies of each TIE flooded by the leaf.

If there are no failures in the network, then the leaf will end up choosing R flood repeaters.

But as you can see in the example below, if there are some broken links, then the leaf may need to
chose more then R flood-repeater spines to "have enough coverage" for the super spines.

This is a little bit of an extreme scenario with lots of link failures, but it makes it easier to
follow the example.

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

![Flood repeater election scenario with link failures](https://brunorijsman-public.s3-us-west-2.amazonaws.com/diagram_clos_2pod_4leaf_4spine_4super-flood-repeater-election.png)

_Figure 4: Flood repeater election scenario with link failures._

In this case, the outcome is a little bit extreme, in the sense that all spines in the POD end
up being flood repeaters. In other words, it is just the same as having no flooding reductions.
But such extreme scenarios become extremely unlikely if the number of spines is greater.

### Each leaf makes its own independent decision

Each leaf makes its own local decision when choosing its flood repeaters.

There is no special leaf-to-leaf communication to coordinate the election of the flood repeaters.

In fact, there is no requirement that the leaves use the same algorithm for flood repeater election.
It is perfectly fine if each leaf node uses a completely different proprietary algorithm for flood
repeater election. The main thing is that the algorithm chooses the flood repeaters in such a manner
that each super-spine is sufficiently covered to meet the required redundancy R.

For that reason, the RIFT specification does not mandate a flood repeater election algorithm.
However, there is an example algorithm in the specification, and RIFT-Python implements exactly that
algorithm.

### Spreading the burden of being a flood repeater

If each leaf elects its flood repeaters independently, there is a risk that the all elect the same
spines as flood repeaters.

Consider, for example, figure 3 above again. 

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
     be equally desirable. We put them in an "equivalence group". After sorting spines, we randomize
     the sorted order within each equivalence group. If that sounds very abstract, the concrete
     examples and show command output below should make it a bit more concrete.

# Flooding reduction implementation

Enough theory. Let's get our hands dirty and look at what it looks like in practice. We will look
at the show commands first and then at the (optional) configuration.

@@@ CONTINUE FROM HERE @@@
