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

If the configuration file contains more than a single RIFT node (i.e. when simulating a
multi-node topology), then the multiple links in the topology are simulated over a single
physical link by using different multicast addresses and port numbers
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

* Each node in the topology runs in a separate RIFT-Python instance (i.e. in a separate process) and
in a separate Linux network namespace.

* The links between nodes are simulated using virtual Ethernet (veth) interfaces, where each
endpoint of a veth pair resides in a different network namespace, corresponding to the nodes to
which it is connected.

* The `config_generator` tool produces:

    * A separate configuration file for each node.

    * A shell script which creates all the network namespaces, creates all the veth interface pairs, assigns IP addresses to the veth interfaces, and puts the veth interfaces into the right namespace.

    * Shell scripts to Telnet into each of nodes.

The "network namespace per node" mode is more realistic because it uses a separate Linux interface
for each link endpoint, and it is multi-threaded because each RIFT-Python engine runs in a separate
Python process.

## Command Line Options

### Starting the configuration generator

The `config_generator.py` script is located in the `tools` subdirectory. 

At a minimum, it takes a single command line argument which is the name of the meta-configuration file.

The `meta_topology` directory contains multiple example meta-configuration files. In the example
below we use the meta-configuration file `2c_8x8.yaml` (2-level Clos topology with 8 leafs and
8 spines).

By default, `config_generator.py` writes the generated configuration file to standard output:

<pre>
(env) $ <b>tools/config_generator.py meta_topology/2c_8x8.yaml</b>
shards:
  - id: 0
    nodes:
      - name: leaf1
        level: 0
        systemid: 1
        rx_lie_mcast_address: 224.0.1.1
        interfaces:
          - name: if1
[...]
</pre>

### Help

The `-h` or the `--help` command-line option outputs help documentation:

<pre>
(env) $ <b>tools/config_generator.py --help</b>
usage: config_generator.py [-h] [-n]
                           input-meta-config-file [output-file-or-dir]

RIFT configuration generator

positional arguments:
  input-meta-config-file
                        Input meta-configuration file name
  output-file-or-dir    Output file or directory name

optional arguments:
  -h, --help            show this help message and exit
  -n, --netns-per-node  Use network namespace per node
</pre>

### Output configuration file

`config_generator.py` takes an optional second argument which specifies where to write the generated
configuration. By default, the output is a configuration file:

<pre>
(env) $ <b>tools/config_generator.py meta_topology/2c_8x8.yaml topology/generated_2c_8x8.yaml</b>
(env) $ 
</pre>

This generated configuration file can be used as input to the RIFT-Python protocol engine:

<pre>
(env) $ <b>python rift --interactive topology/generated_2c_8x8.yaml </b>
leaf1> <b>show nodes</b>
+--------+--------+---------+
| Node   | System | Running |
| Name   | ID     |         |
+--------+--------+---------+
| leaf1  | 1      | True    |
+--------+--------+---------+
| leaf2  | 2      | True    |
+--------+--------+---------+
.        .        .         .
.        .        .         .
.        .        .         .
+--------+--------+---------+
| spine8 | 16     | True    |
+--------+--------+---------+

leaf1> <b>show interfaces</b>
+-----------+------------+-----------+-----------+
| Interface | Neighbor   | Neighbor  | Neighbor  |
| Name      | Name       | System ID | State     |
+-----------+------------+-----------+-----------+
| if1       | spine1-if1 | 9         | THREE_WAY |
+-----------+------------+-----------+-----------+
| if2       | spine2-if1 | 10        | THREE_WAY |
+-----------+------------+-----------+-----------+
| if3       | spine3-if1 | 11        | THREE_WAY |
+-----------+------------+-----------+-----------+
| if4       | spine4-if1 | 12        | THREE_WAY |
+-----------+------------+-----------+-----------+
| if5       | spine5-if1 | 13        | THREE_WAY |
+-----------+------------+-----------+-----------+
| if6       | spine6-if1 | 14        | THREE_WAY |
+-----------+------------+-----------+-----------+
| if7       | spine7-if1 | 15        | THREE_WAY |
+-----------+------------+-----------+-----------+
| if8       | spine8-if1 | 16        | THREE_WAY |
+-----------+------------+-----------+-----------+

leaf1> <b>set node spine3</b>
spine3> <b>show interfaces</b>
+-----------+-----------+-----------+-----------+
| Interface | Neighbor  | Neighbor  | Neighbor  |
| Name      | Name      | System ID | State     |
+-----------+-----------+-----------+-----------+
| if1       | leaf1-if3 | 1         | THREE_WAY |
+-----------+-----------+-----------+-----------+
| if2       | leaf2-if3 | 2         | THREE_WAY |
+-----------+-----------+-----------+-----------+
| if3       | leaf3-if3 | 3         | THREE_WAY |
+-----------+-----------+-----------+-----------+
| if4       | leaf4-if3 | 4         | THREE_WAY |
+-----------+-----------+-----------+-----------+
| if5       | leaf5-if3 | 5         | THREE_WAY |
+-----------+-----------+-----------+-----------+
| if6       | leaf6-if3 | 6         | THREE_WAY |
+-----------+-----------+-----------+-----------+
| if7       | leaf7-if3 | 7         | THREE_WAY |
+-----------+-----------+-----------+-----------+
| if8       | leaf8-if3 | 8         | THREE_WAY |
+-----------+-----------+-----------+-----------+
</pre>

Note: If you get the following error, then see the next subsection on file descriptors for a solution.

<pre>
OSError: [Errno 24] Too many open files
</pre>

### A note on file descriptors

The current implementation of RIFT-Python uses 4 file descriptors per link end-point, plus
some additional file descriptors for the CLI, log files, etc.

Note: the number of file descriptors per link end-point will be decreased to 2 or possibly even
1 in the future.

For example, in the `2c_8x8.yaml` meta-topology (2-level Clos topology with 8 leafs and 8 spines)
there are 16 nodes in total and each node has 8 link end-points, giving a grand total of 128 link
end-points. Each link end-point consumes 4 file descriptions, which means a bit more than 512 file
descriptors are needed in total.

UNIX-based operating systems (including Linux and MacOS) have limits on the number of file descriptors
than can be open at a given time. There is both a a global limit which is determined when the operating
system is compiled, and a per process limit. In practice, only the per process limit matters.

To report the maximum number of file descriptors for processes started in the current shell issue
the following command:

<pre>
(env) $ <b>ulimit -n</b>
256
</pre>

In this example, the limit of 256 is not sufficient to run the `2c_8x8.yaml` meta-topology.
To increase the limit to 1024 (in this example) use the following command:

<pre>
(env) $ <b>ulimit -n 1024</b>
</pre>

### Network namespace per node mode

The `--netns-per-node` or `-n` command-line option causes `config_generator.py` to run in
"network namespace per node" mode:

<pre>
(env) $ <b>tools/config_generator.py --netns-per-node meta_topology/2c_8x8.yaml generated_2c_8x8_dir</b>
</pre>

In this mode, the second argument (which specifies the output destination) is mandatory and specifies
the name an output directory rather than an output file.

The following files are generated in the output directory:

<pre>
(env) $ <b>ls -1 generated_2c_8x8_dir/</b>
connect-leaf1.sh
connect-leaf2.sh
connect-leaf3.sh
connect-leaf4.sh
connect-leaf5.sh
connect-leaf6.sh
connect-leaf7.sh
connect-leaf8.sh
connect-spine1.sh
connect-spine2.sh
connect-spine3.sh
connect-spine4.sh
connect-spine5.sh
connect-spine6.sh
connect-spine7.sh
connect-spine8.sh
leaf1.yaml
leaf2.yaml
leaf3.yaml
leaf4.yaml
leaf5.yaml
leaf6.yaml
leaf7.yaml
leaf8.yaml
spine1.yaml
spine2.yaml
spine3.yaml
spine4.yaml
spine5.yaml
spine6.yaml
spine7.yaml
spine8.yaml
start.sh
</pre>

The purpose of the generated files is as follows:

* `start.sh` generated script to start the entire topology (example output is give below).

* `*.yaml` generated configuration file for each individual node.

* `connect-*.sh` generated script for each node to initiate a Telnet connection to the node
(example usage is shown below).

The generated `start.sh` script creates all the names spaces, all the veth pairs, assigns all
IP addresses, and starts the RIFT-Python engine for each node. The output looks as follows (the
number at the beginning of each line is the percentage complete):

<pre>
(env) $ <b>./generated_2c_8x8_dir/start.sh </b>
[000] Create veth pair veth-1-2 - veth-2-1
[002] Create veth pair veth-3-4 - veth-4-3
[...]
[086] Create veth pair veth-125-126 - veth-126-125
[088] Create veth pair veth-127-128 - veth-128-127
[089] Create netns netns-1
[090] Create netns netns-2
[...]
[099] Create netns netns-15
[100] Create netns netns-16
</pre>

Note: the `start.sh` script can only run on Linux. If you use MacOS, you must first start a 
docker container and run both `config_generate.py` and `start.sh` in there:

<pre>
(env) $ <b>cd docker</b>
(env) $ <b>./docker-shell</b>
root@d22f9e82f9b0:/# <b>cd /host</b>
root@d22f9e82f9b0:/host# <b>./generated_2c_8x8_dir/start.sh </b>
[000] Create veth pair veth-1-2 - veth-2-1
[002] Create veth pair veth-3-4 - veth-4-3
[...]
</pre>

See the Docker](doc/docker.md) chapter for details on Docker usage in RIFT-Python.

Once you have run `start.sh` to start the topology, you can use `connect-*.sh` to start a Telnet
session to any of the running nodes. For example:

<pre>
root@d22f9e82f9b0:/host# <b>./generated_2c_8x8_dir/connect-spine3.sh </b>
Trying ::1...
Trying 127.0.0.1...
Connected to localhost.
Escape character is '^]'.
spine3> <b>show interfaces</b>
+--------------+--------------------+-----------+-----------+
| Interface    | Neighbor           | Neighbor  | Neighbor  |
| Name         | Name               | System ID | State     |
+--------------+--------------------+-----------+-----------+
| veth-102-101 | leaf7-veth-101-102 | 7         | THREE_WAY |
+--------------+--------------------+-----------+-----------+
| veth-118-117 | leaf8-veth-117-118 | 8         | THREE_WAY |
+--------------+--------------------+-----------+-----------+
| veth-22-21   | leaf2-veth-21-22   | 2         | THREE_WAY |
+--------------+--------------------+-----------+-----------+
| veth-38-37   | leaf3-veth-37-38   | 3         | THREE_WAY |
+--------------+--------------------+-----------+-----------+
| veth-54-53   | leaf4-veth-53-54   | 4         | THREE_WAY |
+--------------+--------------------+-----------+-----------+
| veth-6-5     | leaf1-veth-5-6     | 1         | THREE_WAY |
+--------------+--------------------+-----------+-----------+
| veth-70-69   | leaf5-veth-69-70   | 5         | THREE_WAY |
+--------------+--------------------+-----------+-----------+
| veth-86-85   | leaf6-veth-85-86   | 6         | THREE_WAY |
+--------------+--------------------+-----------+-----------+

spine3> 
</pre>

## Meta-Configuration File Syntax

Just like the configuration file, the meta-configuration file is a YAML file.

The syntax of the meta-configuration YAML file is as follows (! indicates an element is mandatory):

<pre>
  <b>chaos</b>: {
    <b>event-interval</b>: <i>&lt;float&gt;</i>,
    <b>max-concurrent-events</b>: <i>&lt;integer&gt;</i>,
    <b>nr-link-events</b>: <i>&lt;integer&gt;</i>,
    <b>nr-node-events</b>: <i>&lt;integer&gt;</i>
  }
  <b>leafs</b>: {
    <b>nr-ipv4-loopbacks</b>: <i>&lt;integer&gt;</i>
  } 
! <b>nr-leaf-nodes-per-pod</b>: <i>&lt;integer&gt;</i>
  <b>nr-pods</b>: <i>&lt;integer&gt;</i>
! <b>nr-spine-nodes-per-pod</b>: <i>&lt;integer&gt;</i>
  <b>nr-superspine-nodes</b>: <i>&lt;integer&gt;</i>
  <b>spines</b>: {
    <b>nr-ipv4-loopbacks</b>: <i>&lt;integer&gt;</i>
  } 
  <b>superspines</b>: {
    <b>nr-ipv4-loopbacks</b>: <i>&lt;integer&gt;</i>
  } 
</pre>

### chaos

| Element | `chaos` |
| --- | --- |
| Value | Dictionary with sub-elements: `event-interval`, `max-concurrent-events`, `nr-link-event`, `nr-node-events` |
| Level | Top-level |
| Presence | Optional |
| Meaning | Defines the parameters for chaos testing |

If the `chaos` is present, then the config_generator also outputs the `chaos.sh` script for chaos
testing.

The `chaos` element is only supported in namespace per node mode (command-line option 
`--netns-per-node`)

See the [IETF 104 Hackathon Presentation: Chaos Monkey Testing (PDF)](../ietf-104/ietf-104---rift-hackathon---chaos-monkey-testing.pdf) for more details on chaos testing.

Example:

<pre>
nr-pods: 2
nr-leaf-nodes-per-pod: 2
nr-spine-nodes-per-pod: 2
nr-superspine-nodes: 2
<b>chaos</b>: {
  event-interval: 5.0,
  max-concurrent-events: 3,
  nr-link-events: 10,
  nr-node-events: 5
}
</pre>

### event-interval

| Element | `event-interval` |
| --- | --- |
| Value | Float, minimum value 0.0 |
| Level | `chaos` |
| Presence | Optional, default value 3.0 |
| Meaning | The interval, in seconds, between events in the chaos testing script |

Example:

<pre>
nr-pods: 2
nr-leaf-nodes-per-pod: 2
nr-spine-nodes-per-pod: 2
nr-superspine-nodes: 2
chaos: {
  <b>event-interval: 5.0</b>,
  max-concurrent-events: 3,
  nr-link-events: 10,
  nr-node-events: 5
}
</pre>

### leafs

| Element | `leafs` |
| --- | --- |
| Value | Dictionary with sub-elements: `nr-ipv4-loopbacks` |
| Level | Top-level |
| Presence | Optional |
| Meaning | Defines the characteristics of each leaf node in the topology |

Example:

<pre>
nr-pods: 2
nr-leaf-nodes-per-pod: 2
<b>leafs</b>: {
  nr-ipv4-loopbacks: 2
}
nr-spine-nodes-per-pod: 2
nr-superspine-nodes: 2
</pre>

### max-concurrent-events

| Element | `max-concurrent-events` |
| --- | --- |
| Value | Integer, minimum value 1 |
| Level | `chaos` |
| Presence | Optional, default value 5 |
| Meaning | The maximum number of concurrent events in the chaos testing script |

The chaos testing script `chaos.sh` generates a sequence of random events.
Each event breaks something (e.g. a link or a node) and some time later repairs it.
Between the time that something is broken and the time that it is repaired, the failure is deemed to
be "active". The `max-concurrent-events` specifies the maximum number of concurrently active
failures.
For example, if you set `max-concurrent-events` to 1, then you are testing that the network
continues to function correctly in the face of any single failure.

Example:

<pre>
nr-pods: 2
nr-leaf-nodes-per-pod: 2
nr-spine-nodes-per-pod: 2
nr-superspine-nodes: 2
chaos: {
  event-interval: 5.0,
  <b>max-concurrent-events: 3</b>,
  nr-link-events: 10,
  nr-node-events: 5
}
</pre>

### nr-ipv4-loopbacks

| Element | `nr-ipv4-loopbacks` |
| --- | --- |
| Value | Integer, minimum value 0 |
| Level | `leafs`, `spines`, `superspines` |
| Presence | Optional, default value 1 |
| Meaning | The number of IPv4 loopback interfaces per leaf / spine / superspine node |

Example:

<pre>
nr-pods: 2
nr-leaf-nodes-per-pod: 2
nr-spine-nodes-per-pod: 2
<b>spines</b>: {
  nr-ipv4-loopbacks: 2
}
nr-superspine-nodes: 2
</pre>

### nr-leaf-nodes-per-pod

| Element | `nr-leaf-nodes-per-pod` |
| --- | --- |
| Value | Integer, minimum value 1 |
| Level | Top-level |
| Presence | Mandatory |
| Meaning | The number of leaf nodes per POD |

Example:

<pre>
<b>nr-leaf-nodes-per-pod: 8</b>
nr-spine-nodes-per-pod: 8
</pre>

### nr-link-events

| Element | `nr-link-events` |
| --- | --- |
| Value | Integer, minimum value 0 |
| Level | `chaos` |
| Presence | Optional, default value 20 |
| Meaning | The number of link events in the chaos testing script |

A link event can be one of the following (each event has a corresponding repair event):

 * A link failure (followed by a corresponding link repair)

Example:

<pre>
nr-pods: 2
nr-leaf-nodes-per-pod: 2
nr-spine-nodes-per-pod: 2
nr-superspine-nodes: 2
chaos: {
  event-interval: 5.0,
  max-concurrent-events: 3,
  <b>nr-link-events: 10</b>,
  nr-node-events: 5
}
</pre>

### nr-node-events

| Element | `nr-node-events` |
| --- | --- |
| Value | Integer, minimum value 0 |
| Level | `chaos` |
| Presence | Optional, default value 5 |
| Meaning | The number of node events in the chaos testing script |

A node event can be one of the following (each event has a corresponding repair event):

 * A node failure (followed by a corresponding node restart)

Example:

<pre>
nr-pods: 2
nr-leaf-nodes-per-pod: 2
nr-spine-nodes-per-pod: 2
nr-superspine-nodes: 2
chaos: {
  event-interval: 5.0,
  max-concurrent-events: 3,
  nr-link-events: 10,
  <b>nr-node-events: 5</b>
}
</pre>

### nr-pods

| Element | `nr-pods` |
| --- | --- |
| Value | Integer, minimum value 1 |
| Level | Top-level |
| Presence | Optional, default value 1 |
| Meaning | The number of PODs |

Example:

<pre>
<b>nr-pods: 2</b>
nr-leaf-nodes-per-pod: 8
nr-spine-nodes-per-pod: 8
</pre>

### nr-spine-nodes-per-pod

| Element | `nr-spine-nodes-per-pod` |
| --- | --- |
| Value | Integer, minimum value 1 |
| Level | Top-level |
| Presence | Mandatory |
| Meaning | The number of spine nodes per POD |

Example:

<pre>
nr-leaf-nodes-per-pod: 8
<b>nr-spine-nodes-per-pod: 8</b>
</pre>

### nr-superspine-nodes

| Element | `nr-superspine-nodes` |
| --- | --- |
| Value | Integer, minimum value 1 |
| Level | Top-level |
| Presence | If nr-pods is greater than 1, then nr-superspine-nodes is mandatory. If nr-pods equals 1, then nr-superspine-nodes must not be present. |
| Meaning | The number of superspine nodes |

Example:

<pre>
nr-leaf-nodes-per-pod: 3
nr-spine-nodes-per-pod: 3
nr-pods: 2
<b>nr-superspine-nodes: 4</b>
</pre>

### spines

| Element | `spines` |
| --- | --- |
| Value | Dictionary with sub-elements: `nr-ipv4-loopbacks` |
| Level | Top-level |
| Presence | Optional |
| Meaning | Defines the characteristics of each spine node in the topology |

Example:

<pre>
nr-pods: 2
nr-leaf-nodes-per-pod: 2
nr-spine-nodes-per-pod: 2
<b>spines</b>: {
  nr-ipv4-loopbacks: 2
}
nr-superspine-nodes: 2
</pre>

### superspines

| Element | `superspines` |
| --- | --- |
| Value | Dictionary with sub-elements: `nr-ipv4-loopbacks` |
| Level | Top-level |
| Presence | Optional |
| Meaning | Defines the characteristics of each superspine node in the topology |

Example:

<pre>
nr-pods: 2
nr-leaf-nodes-per-pod: 2
nr-spine-nodes-per-pod: 2
nr-superspine-nodes: 2
<b>superspines</b>: {
  nr-ipv4-loopbacks: 2
}
</pre>
