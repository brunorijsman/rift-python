# Configuration File Generator

## Introduction

As explained in the [Configuration File](configuration-file.md) chapter, when you start the RIFT
protocol engine, you can optionally specify a configuration file (also known as a topology file)
on the command line.

The configuration file specifies, in excruciating detail:
* which RIFT nodes are present in the topology,
* how the RIFT nodes are interconnected by links,
* which prefixes the RIFT nodes advertise,
* and some other configuration options for each node.

If the configuration file contains more than a single RIFT node (i.e. if we are simulating a
multi-node topology), then the multiple links in the topology are simulated over a single
physical link by using different multi-cast addresses and port numbers
(see the [Configuration File](configuration-file.md) chapter for details).

### Simplifying the generation of configuration files

Manually creating a configuration file for any non-trivial topology is an extremely tedious and
error-prone process.

Instead of manually creating a configuration file, you can use the `config_generator` tool to
generate one for you.

The `config_generator` takes a meta-configuration file (also known as a meta-topology file) as input
and produces a configuration file (also known as a topology file) as output.

The meta-configuration file specifies something along the lines of "I want a 5-stage Clos
topology with 8 leaf nodes, 8 spine nodes, and 4 superspine nodes" (the detailed syntax of the
meta-configuration file is specified below). The `config_generator` tool takes this 
meta-configuration file as input and produces the detailed configuration file as output with all
the configuration details for each of the 20 nodes and all the links between them.

### Using namespaces to simulate multi-node topologies

By default, the `config_generator` tool generates a single configuration file that contains all
the nodes in the topology and that is executed by a single instance of the RIFT protocol engine.
There are two issues with this approach:

* As mentioned before, in this mode multiple links are simulated over a single physical interface
using different multicast addresses and UDP port numbers. This is somewhat unrealistic since in 
real deployments each node and each link would use the same multicast addresses and the same
UDP port numbers. As a result, certain classes of bugs (related to running multicast on multiple
interfaces) are not caught by this simulation approach.

* The RIFT-Python implementation is single-threaded. When you run large topologies in a single
RIFT-Python engine (around 20+ nodes), the protocol performance and the CLI can become sluggish.

To address both of these issues, the `config_generator` tool has a `--netns-per-node` 
command-line option to operate in a different mode, called the "network namespace per node" mode.
Instead of generating a single topology file that simulates all nodes in a single RIFT-Python 
instance, the "network namespace per node" mode does the following:

* Each node in the topology runs in a separate RIFT-Python instance (i.e. in a separate process)

* Each node (i.e. each RIFT-Python) runs in a separate Linux network namespace.

* The links between nodes are simulated using virtual Ethernet (veth) interfaces, where each
endpoint of a veth pair resides in a different network namespace, corresponding to the nodes to
which it is connected.

* The `config_generator` tool produces:

    * A separate configuration file for each node.

    * A shell script which creates all the network namespaces, creates all the veth interface pairs assigns IP addresses the the veth interfaces, and puts the veth interfaces into the right namespace.

    * Shell scripts to Telnet into each of nodes.

The "network namespace per node" mode is more realistic because it uses a separate Linux interface
for each link endpoint, and it is multi-threaded because each RIFT-Python engine runs in a separate
Python process.

## Command Line Options

TODO

## Meta-Topology File Syntax

TODO
