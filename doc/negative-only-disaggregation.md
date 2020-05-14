# Negative-Only Disaggregation Feature Guide

This is a variation of the
[negative disaggregation feature guide](negative-disaggregation-feature-guide.md)
that demonstrates `negative-only` disaggregation instead of the default
`positive-and-negative` disaggregation.

## Generating and starting the topology

To enable negative-only disaggration we use the meta-topology file 
`meta_topology/clos_3plane_3pod_3leaf_3spine_6super_negdisagg.yaml`
which contains one extra line:

<pre>
nr-pods: 3
nr-leaf-nodes-per-pod: 3
nr-spine-nodes-per-pod: 3
nr-superspine-nodes: 6
nr-planes: 3
<b>disaggregation: negative-only</b>
</pre>

As before, we use the configuration generator to convert this meta-topology into a topology file 
named `generated.yaml`.

<pre>
(env) $ <b>tools/config_generator.py meta_topology/clos_3plane_3pod_3leaf_3spine_6super_negdisagg.yaml generated.yaml</b>
</pre>

Once the topology file is generated, you can start it in RIFT-Python as follows:

<pre>
(env) $ <b>python rift -i generated.yaml</b>
leaf-1-1>
</pre>

The `show engine` command confirms that we have enabled negative-only disaggregation:

<pre>
leaf-1-1> <b>show engine</b>
+----------------------------------+---------------------+
| Stand-alone                      | False               |
| Interactive                      | True                |
| Simulated Interfaces             | True                |
| Physical Interface               | ens5                |
| Telnet Port File                 | None                |
| IPv4 Multicast Loopback          | True                |
| IPv6 Multicast Loopback          | True                |
| Number of Nodes                  | 24                  |
| Transmit Source Address          |                     |
| Flooding Reduction Enabled       | True                |
| Flooding Reduction Redundancy    | 2                   |
| Flooding Reduction Similarity    | 2                   |
| Flooding Reduction System Random | 4296011516847335669 |
<b>| Disaggregation                   | negative-only       |</b>
+----------------------------------+---------------------+
</pre>

## Breaking the first link: negative disaggreation

We will start with breaking one link from spine-1-1 to super-1-1. 
RIFT-Python offers a handy set command to
simulate link failures:

<pre>
spine-1-1> <b>set interface if-101d failure failed</b>
</pre>

In the original [negative disaggregation feature guide](negative-disaggregation-feature-guide.md)
we saw that this would cause positive disaggregation to happen.
But now we have configured RIFT-Python to use only negative disaggregation, so let's see how
negative disaggregation can replace positive disaggregation to recover from this failure.




@@@@ 

### Super-1-1

As before, we see that the adjacency from super-1-1 to spine-1-1 goes down.
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

Node super-1-2, which is the same plane as super-1-1 (namely plane-1) still has all three
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

### Super-1-1

Back on super-1-1, we see that super-1-1  has the south-node-TIE from super-1-2,
because it was reflected by the spine nodes:

<pre>
super-1-1> <b>show tie-db direction south originator 2 tie-type node</b>
+-----------+------------+------+--------+--------+----------+-------------------------+
| Direction | Originator | Type | TIE Nr | Seq Nr | Lifetime | Contents                |
+-----------+------------+------+--------+--------+----------+-------------------------+
| South     | 2          | Node | 1      | 6      | 604311   | Name: super-1-2         |
|           |            |      |        |        |          | Level: 24               |
|           |            |      |        |        |          | Capabilities:           |
|           |            |      |        |        |          |   Flood reduction: True |
|           |            |      |        |        |          | Neighbor: 4             |
|           |            |      |        |        |          |   Level: 24             |
|           |            |      |        |        |          |   Cost: 1               |
|           |            |      |        |        |          |   Bandwidth: 100 Mbps   |
|           |            |      |        |        |          |   Link: 5-4             |
|           |            |      |        |        |          | Neighbor: 6             |
|           |            |      |        |        |          |   Level: 24             |
|           |            |      |        |        |          |   Cost: 1               |
|           |            |      |        |        |          |   Bandwidth: 100 Mbps   |
|           |            |      |        |        |          |   Link: 4-5             |
|           |            |      |        |        |          | Neighbor: 101           |
|           |            |      |        |        |          |   Level: 23             |
|           |            |      |        |        |          |   Cost: 1               |
|           |            |      |        |        |          |   Bandwidth: 100 Mbps   |
|           |            |      |        |        |          |   Link: 1-5             |
|           |            |      |        |        |          | Neighbor: 104           |
|           |            |      |        |        |          |   Level: 23             |
|           |            |      |        |        |          |   Cost: 1               |
|           |            |      |        |        |          |   Bandwidth: 100 Mbps   |
|           |            |      |        |        |          |   Link: 2-5             |
|           |            |      |        |        |          | Neighbor: 107           |
|           |            |      |        |        |          |   Level: 23             |
|           |            |      |        |        |          |   Cost: 1               |
|           |            |      |        |        |          |   Bandwidth: 100 Mbps   |
|           |            |      |        |        |          |   Link: 3-5             |
+-----------+------------+------+--------+--------+----------+-------------------------+
</pre>

We also see that the south-node-TIE from super-1-1 itself has one less south-bound adjacency,
it is missing the adjacency to spine-1-1 (system ID 101):

<pre>
super-1-1> <b>show tie-db direction south originator 1 tie-type node</b>
+-----------+------------+------+--------+--------+----------+-------------------------+
| Direction | Originator | Type | TIE Nr | Seq Nr | Lifetime | Contents                |
+-----------+------------+------+--------+--------+----------+-------------------------+
| South     | 1          | Node | 1      | 7      | 604594   | Name: super-1-1         |
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
We will see how this failure causes positive disaggregation to happen.

Note: in this feature guide, we describe how RIFT-Python behaves by default, i.e.
with using the default value `positive-and-negative` for the `

` configuration
parameter.

<pre>
spine-1-1> <b>show engine</b>
+----------------------------------+-----------------------+
.                                  .                       .
| Disaggregation                   | positive-and-negative |
+----------------------------------+-----------------------+
</pre>

It is actually quite interesting to see how RIFT-Python behaves in the `negative-only` 
aggregation mode. In particular, it gives a better insight into the propagation rules for
negative disaggregation.
We describe this in [a separate guide](negative-only-disaggregation.md).

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

Node super-1-2, which is the same plane as super-1-1 (namely plane-1) still has all three
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

Super-1-2 also has the south-node-TIE from super-1-1, because it was reflected by the spine nodes:

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

Here we can see that super-1-2 knows that super-1-1 (system ID 1) is another superspone node
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

Now let's head over to spine-3-1 which is PoD 3's spine node in plane 1.

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

And finally spine-3-1 installs routes to the positive disaggregate prefixes in the
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

Now, we break the second link from spine-1-1 to super-1-2:

<pre>
spine-1-1> <b>set interface if-101e failure failed</b>
</pre>

At this point pod-1 is completely isolated from plane-1 in the superspine.
Thus, we expect to see negative disaggregation to occur at this point.

### Super-1-2

We start by having a look at super-1-2 and confirming that it indeed has lost its adjacency
with spine-1-1:

<pre>
super-1-2> <b>show interfaces</b>
+-----------+-------------------+-----------+-----------+
| Interface | Neighbor          | Neighbor  | Neighbor  |
| Name      | Name              | System ID | State     |
+-----------+-------------------+-----------+-----------+
| if-2a     |                   |           | ONE_WAY   |
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

At this point, plane-1 in the superspine is completely disconnected from pod-1.
For exampe, if we look at the route table of spine-1-2, we see that it is missing routes
to leaf-1-1 (88.0.1.1), leaf-1-2 (88.0.2.1), leaf-1-3 (88.0.3.1), and spine-1-1 (88.1.1.1):

<pre>
super-1-2> <b>show route family ipv4</b>
IPv4 Routes:
+-------------+-----------+---------------------+
| Prefix      | Owner     | Next-hops           |
+-------------+-----------+---------------------+
| 88.0.4.1/32 | South SPF | if-2b 172.31.15.176 |
+-------------+-----------+---------------------+
| 88.0.5.1/32 | South SPF | if-2b 172.31.15.176 |
+-------------+-----------+---------------------+
| 88.0.6.1/32 | South SPF | if-2b 172.31.15.176 |
+-------------+-----------+---------------------+
| 88.0.7.1/32 | South SPF | if-2c 172.31.15.176 |
+-------------+-----------+---------------------+
| 88.0.8.1/32 | South SPF | if-2c 172.31.15.176 |
+-------------+-----------+---------------------+
| 88.0.9.1/32 | South SPF | if-2c 172.31.15.176 |
+-------------+-----------+---------------------+
| 88.1.4.1/32 | South SPF | if-2b 172.31.15.176 |
+-------------+-----------+---------------------+
| 88.1.7.1/32 | South SPF | if-2c 172.31.15.176 |
+-------------+-----------+---------------------+
</pre>

If we look at super-2-1, we do see routes to leaf-1-1 (88.0.1.1), leaf-1-2 (88.0.2.1), 
and leaf-1-3 (88.0.3.1). 
We don't see a route to spine-1-1 (88.1.1.1) but that is expected because super-2-1 is in
plane-2, so we do see a route to spine-1-2 (88.1.2.1) instead.

<pre>
super-2-1> <b>show routes family ipv4</b>
IPv4 Routes:
+-------------+-----------+---------------------+
| Prefix      | Owner     | Next-hops           |
+-------------+-----------+---------------------+
| 88.0.1.1/32 | South SPF | if-3a 172.31.15.176 |
+-------------+-----------+---------------------+
| 88.0.2.1/32 | South SPF | if-3a 172.31.15.176 |
+-------------+-----------+---------------------+
| 88.0.3.1/32 | South SPF | if-3a 172.31.15.176 |
+-------------+-----------+---------------------+
| 88.0.4.1/32 | South SPF | if-3b 172.31.15.176 |
+-------------+-----------+---------------------+
| 88.0.5.1/32 | South SPF | if-3b 172.31.15.176 |
+-------------+-----------+---------------------+
| 88.0.6.1/32 | South SPF | if-3b 172.31.15.176 |
+-------------+-----------+---------------------+
| 88.0.7.1/32 | South SPF | if-3c 172.31.15.176 |
+-------------+-----------+---------------------+
| 88.0.8.1/32 | South SPF | if-3c 172.31.15.176 |
+-------------+-----------+---------------------+
| 88.0.9.1/32 | South SPF | if-3c 172.31.15.176 |
+-------------+-----------+---------------------+
| 88.1.2.1/32 | South SPF | if-3a 172.31.15.176 |
+-------------+-----------+---------------------+
| 88.1.5.1/32 | South SPF | if-3b 172.31.15.176 |
+-------------+-----------+---------------------+
| 88.1.8.1/32 | South SPF | if-3c 172.31.15.176 |
+-------------+-----------+---------------------+