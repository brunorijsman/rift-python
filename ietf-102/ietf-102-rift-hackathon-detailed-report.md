# IETF 102 Hackathon: Routing In Fat Trees (RIFT)

## Juniper RIFT - Python RIFT Interoperability Report

### Introduction

This reports provides a very detailed report of the interoperability testing done at the IETF 102 RIFT Hackathon in Montreal. The intent is to enable others to reproduce the test that were executed there.

We tested interoperability between two implementations of RIFT.



The interoperability test runs Juniper RIFT and Python RIFT on an t2.micro Elastic Compute Cloud (EC2) instance on Amazon Web Services (AWS).

One RIFT node runs Juniper RIFT and one RIFT node runs Python RIFT.

We demonstrate that a full adjacency (state 3-way) is established between the Juniper RIFT node and the Python RIFT node.

In this interoperability test we only verified the Link Information Element (LIE) Finite State Machine (FSM). Future interoperability tests will also verify the Zero Touch Provisioning (ZTP) FSM and the flooding FSM.

### Conventions

I use the following conventions in this document.

* **Bold** font means commands that you enter.
* _Italics_ font means a parameter value that you provide.
* Regular font means output from a command.
* [...] means that output has been truncated.
* Shell prompt "local$" means that that the command is entered on a local computer.
* Shell prompt "vm$" means that the command is entered in an SSH session to a virtual machine.
* Numbered shell prompts such as "vm1$", "vm2$", "vm3$", etc. means that there are multiple SSH sessions to the same virtual machine.

All abbreviations are expended in the appendix.

### Download the Juniper RIFT Free Trial Software

Go to the Juniper Networks RIFT Free Trial webpage at [https://www.juniper.net/us/en/dm/free-rift-trial/](https://www.juniper.net/us/en/dm/free-rift-trial/)

If you already have a Juniper customer or a Juniper partner account,   you may skip one or both of the next steps.

Create a Juniper account using the link on the RIFT Free Trial page.  You will need a company e-mail address (public e-mail services such as gmail are not accepted).

If you don't have a Juniper device serial number or a Juniper partner number, your only option is to create a guest account. By default, a guest account does not allow you to download the RIFT Free Trial software. You need to call Juniper customer support to open a customer support case (using your newly created guest account) to request access to the RIFT Free Trial. In my case, I was granted access to download the software within 30 minutes.

Once you have a sufficiently authorized Juniper account, go back to the RIFT Free Trial page and click the "Download RIFT" button, and download "Rift-public-experimental for linux".

This downloads a file "rift-public-experimental-0.6.0-926acb7-x86_64-unix-linux.tar.gz" (or similar). Just leave the image in the downloads folder for now, we will use it later.

There is also an image available for Apple macOS, but we don't provide instructions for running on macOS in this write up.

If you are a customer of Juniper, you can also ask your account representative to provide you with a "Rift-customer-experimental" image which has a few more features than the public image.

### Platform

Both Juniper RIFT and Python RIFT support Linux (various distributions such Ubuntu, Centos, Amazon Linux, etc.) as well as Apple macOS. They can both run on bare metal, in a container, in a virtual machine, locally, or in a cloud.

That said, the instructions in this write-up are specific to Ubuntu 16.04 LTS instances running on AWS. 

One thing to keep in mind is that multicast code is notoriously platform dependent. During interoperability testing we found that the code for creating multicast UDP sockets, binding to multicast sockets, setting options on multicast options, sending and receiving multicast packets, etc. behaves subtly different on different versions of the Linux kernel and on macOS.

### Launch an AWS Instance

We did our interoperability testing using a virtual machine running in the Amazon Web Services (AWS) cloud. 

The instructions in this document assume you have an AWS account. If you don't have an AWS account, you can sign up for an AWS Free Tier account at [https://aws.amazon.com/free/](https://aws.amazon.com/free/).

Go to the AWS EC2 console and create a EC2 instance:

* Choose Amazon Machine Image (AMI) "Ubuntu Server 16.04 LTS (HVM), SSD Volume Type"
* Choose instance type t2.micro
* Use the default values for all other configuration parameters
* Make sure you download the private key for the EC2 instance

Note: we are using a t2.micro instance type because it is eligible for AWS Free Tier. A t2.micro instance is powerful enough for doing interoperability testing between two RIFT speaker, but you will need a larger AWS instance type to test large topologies. We will get back to this later.

Wait for the EC2 instance to come up and then SSH into the public IP address of the EC2 instance using "ubuntu" as the username and your private key:

<pre>
$ <b>ssh ubuntu@</b><i>ipv4-address-of-vm</i><b> -i ~/.ssh/</b><i>your-private-key</i><b>.pem</b>
The authenticity of host 'xx.xx.xx.xx (xx.xx.xx.xx)' can't be established.
ECDSA key fingerprint is SHA256:xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx.
Are you sure you want to continue connecting (yes/no)? <b>yes</b>
Warning: Permanently added 'xx.xx.xx.xx' (ECDSA) to the list of known hosts.
Welcome to Ubuntu 16.04.4 LTS (GNU/Linux 4.4.0-1061-aws x86_64)
[...]
</pre>

Once logged in to your EC2 instance, run "apt-get update" to download and install the latest security patches:

<pre>
vm$ <b>sudo apt-get update -y</b>
Hit:1 http://us-west-2.ec2.archive.ubuntu.com/ubuntu xenial InRelease
Get:2 http://us-west-2.ec2.archive.ubuntu.com/ubuntu xenial-updates InRelease [109 kB]
Get:3 http://us-west-2.ec2.archive.ubuntu.com/ubuntu xenial-backports InRelease [107 kB]
Get:4 http://us-west-2.ec2.archive.ubuntu.com/ubuntu xenial/main Sources [868 kB]
[...]
</pre>

### Install Juniper RIFT on the EC2 Instance

Copy the Juniper RIFT image that we downloaded earlier from your local computer to the EC2 instance:

<pre>
local$ <b>scp -i ~/.ssh/</b><i>your-private-key.pem</i><b> ~/Downloads/rift-public-experimental-0.6.0-926acb7-x86_64-unix-linux.tar.gz ubuntu@</b><i>ipv4-address-of-vm</i><b>:/home/ubuntu</b>
rift-public-experimental-0.6.0-926acb7-x86_64-unix-linux.tar.gz                                                         100% 3965KB  79.1KB/s   00:50    
$ 
</pre>

On your EC2 instance, unpack the Juniper RIFT image:

<pre>
vm$ <b>tar xvf rift-public-experimental-0.6.0-926acb7-x86_64-unix-linux.tar.gz</b>
content-x86_64-public/
content-x86_64-public/publisher_key.pub.pkcs8
content-x86_64-public/MANIFEST.enc
content-x86_64-public/topology/
[...]
content-x86_64-public/CHANGELOG.md
content-x86_64-public/FAQ.md
</pre>

Go to the directory where the software was unpacked:

<pre>
vm$ <b>cd content-x86_64-public/</b>
</pre>

Do **not** follow the instructions in INSTALL.md about using sysctl to tune UDP and do **not** run the basicvalidation.sh script.  Running the basicvalidation.sh script verifies that a large topology runs reliably on the virtual machine. The script will fail because we are running on a t2.micro instance type which is not powerful. This is not an issue for the interoperability testing because we will only run very small 2 node topologies. In my experience, you need at least an m5.2xlarge EC2 instance to make the basicvalidation.sh script pass reliably.

Make sure that Juniper RIFT runs properly by starting it up with the "--help" command line option. You should see help text as output:

<pre>
vm$ <b>./bin/rift-environ --help</b>

====================================================
ROUTING IN FAT TREES (RIFT) Experimental Environment
Copyright (c) 2016-, Juniper Networks, Inc.
All rights reserved.
==================================================== 
version: experimental 0.6.0

[...]
</pre>

### The Concept of Topologies

Both Juniper RIFT and Python RIFT are capable of running a topology with multiple RIFT nodes on a single server. 

The Juniper RIFT implementation introduced the concept of a topology YAML file. This file specifies the configuration of each RIFT node and the way that the RIFT nodes are interconnected, i.e. the topology.

Python RIFT was implemented to support the same topology YAML files as Juniper RIFT to simplify interoperability testing.

Multi-node RIFT node topologies are implemented as follows:

* All RIFT nodes run in the same virtual machine.
* All Juniper RIFT nodes run in a single process. (Sharding across multiple processes is also supported, but we did not use this feature during the interop testing.)
* All Python RIFT nodes run in a single Python process.
* All Python packets are sent over a single interface (which may be a loopback interface).
* Multiple separate point-to-point links are simulated by using different UDP ports and different IP multicast addresses for each link.

I am planning to also run a more realistic simulation where each RIFT node runs in a separate process in a separate networking namespace, and veth interfaces (and possibly bridges) are used to interconnect the RIFT nodes. This is not yet part of this report.

### Run a Juniper RIFT Topology

We will now start a small two node topology, where both nodes run Juniper RIFT. This demonstrates that Juniper RIFT can establish a 3-way adjacency with itself. Later on, we will replace one of the Juniper RIFT nodes with a Python RIFT node for the interoperability testing.

Use the following command to start a small two node topology. 

<pre>
$ <b>./bin/rift-environ -c -C lies -vvv -R 999999 topology topology/two.yaml</b>
version: RIFT 0.6.0/926acb7
 Jul 18 12:27:11.859 INFO 
====================================================
ROUTING IN FAT TREES (RIFT) Experimental Environment
Copyright (c) 2016-, Juniper Networks, Inc.
All rights reserved.
====================================================

 Jul 18 12:27:11.859 INFO logging level=Debug features=["limited-runtime", "flood reduction", "300 seconds runtime"]
 Jul 18 12:27:11.860 INFO filtering trace: [{"lies"}]
 Jul 18 12:27:11.860 INFO topology "topology/two.yaml" starting with shard 0 ...
 Jul 18 12:27:11.861 INFO node core_1 configured & started on 1531916831.861 with thrift config/state server on ports Some(19991)/Some(19990)
[...]
</pre>

The **-c** option enables compact tracing.

The **-C** lies option enables tracing for the LIES subsystem.

The **-vvv** option sets tracing verbosity to debugs.

The **-R 999999** option sets the runtime duration to 999999 seconds instead of the default 5 seconds. Note: the pubic image limits run time to at most 300 seconds (5 minutes).

The **topology** subcommand runs a topology of RIFT nodes specified in a YAML file.

**topology/two.yaml** is the name of the YAML file that specifies the topology.

Look for the following two messages reporting that the adjacency is up i.e. has reached state 3-way. There should be two such messages, one from each RIFT node. (Note the typo in "addjacency" when you search for the message.)

<pre>
 peer: if_202_1->20021:20024:224.0.255.1/ff02::1
  nodeid: agg_202
   subsystem: lies
    Jul 18 18:05:42.727 DEBG received reflection first time, rebuild packet
    Jul 18 18:05:42.728 DEBG <b>addjacency 3-way up</b>
[...]
 peer: if_1_202->20022:20023:224.0.255.202/ff02::2
  nodeid: core_1
   subsystem: lies
    Jul 18 18:05:42.731 DEBG received reflection first time, rebuild packet
    Jul 18 18:05:42.731 DEBG <b>addjacency 3-way up</b>
</pre>


You may also see some warning messages related to creating and binding IPv6 sockets. This does not affect the interoperability testing because at this time the Python RIFT implementation only supports IPv4 and not yet IPv6. Hence the interoperability testing done at the IETF 102 hackathon only covered IPv4:

<pre>
Jul 18 18:05:42.731 WARN failed to create LIETX socket V6([ff02::2]:20021) on V6(::1) for if: 20022: Kind(NotConnected)
</pre>
<pre>
Jul 18 18:05:42.731 WARN binding peer on Some(PlatformInterfaceName("platform_if_1_202"))/Some(20022) failed: IOError(Kind(NotConnected))
</pre>

### Install Python RIFT on the EC2 Instance

#### Install Python 3

Python RIFT is written in Python 3 and tested using version 3.5.1. It will not run using Python 2, but it should run on newer (or even older) versions of Python 3.

Python3 is already installed by default on the Ubuntu 16.04 LTS AMI. Verify that it is indeed installed:

<pre>
vm$ <b>python3 --version</b>
Python 3.5.2
</pre>

However, if you need to install Python 3 yourself you can do so as follows:

<pre>
vm$ <b>sudo apt-get install -y python3</b>
</pre>

### Install virtualenv

A Python virtual environment is a mechanism to keep all project dependencies together and isolated from the dependencies of other projects you may be working on to avoid conflicts.

Install virtualenv so that you can create a virtual environment for your project later on in the installation process:

<pre>
vm$ <b>sudo apt-get install -y virtualenv</b>
</pre>

Verify that virtualenv has been properly installed by asking for the version (the exact version number may be different when you run the command, which is okay):

<pre>
vm$ <b>virtualenv --version</b>
15.0.1
</pre>

### Install git

You git to clone clone the Python RIFT repository onto the EC2 instance.

Git is already installed by default on the Ubuntu 16.04 LTS AMI. Verify that it is indeed installed:

<pre>
vm$ <b>git --version</b>
git version 2.7.4
</pre>

However, if you need to install git yourself you can do so as follows:

<pre>
vm$ <b>sudo apt-get install -y git</b>
</pre>

### Clone the Python RIFT repository

Make sure you are back in the home directory of the ubuntu user:

<pre>
vm$ <b>cd</b>
vm$ <b>pwd</b>
/home/ubuntu
</pre>

Clone the brunorijsman/rift-python repository from github:

<pre>
vm$ <b>git clone https://github.com/brunorijsman/rift-python.git</b>
Cloning into 'rift-python'...
remote: Counting objects: 351, done.
remote: Compressing objects: 100% (47/47), done.
remote: Total 351 (delta 38), reused 50 (delta 25), pack-reused 279
Receiving objects: 100% (351/351), 125.95 KiB | 0 bytes/s, done.
Resolving deltas: 100% (212/212), done.
Checking connectivity... done.
</pre>

This will create a directory rift-python with the source code:

<pre>
vm$ <b>find rift-python</b>
rift-python
rift-python/topology
rift-python/topology/one.yaml
rift-python/topology/two_by_two_by_two.yaml
rift-python/topology/two_by_two_by_two_ztp.yaml
rift-python/topology/two.yaml
rift-python/LICENSE
...
</pre>

Go to the directory where the repo was cloned:

<pre>
vm$ <b>cd rift-python</b>
</pre>

Check out the specific version of the Python RIFT code that was used during the IETF 102 RIFT hackathon:

<pre>
vm$ <b>git checkout ietf-102-rift-hackathon</b>
Note: checking out 'ietf-102-rift-hackathon'.

You are in 'detached HEAD' state. You can look around, make experimental
changes and commit them, and you can discard any commits you make in this
state without impacting any branches by performing another checkout.

If you want to create a new branch to retain commits you create, you may
do so (now or later) by using -b with the checkout command again. Example:

  git checkout -b <new-branch-name>

HEAD is now at 988fa7e... Remove print-adjacency-fsm (replaced by show command)
</pre>

IMPORTANT: If you do not check out the version tagged ietf-102-rift-hackathon as described
above, none of the examples in this document will work. The code has changed significantly 
since the IETF 102 Hackathon; both the installation and startup instructions have changed 
significantly since then. For up-to-date instructions for the current version see README.md
and doc/*.md

### Create Python virtual environment

While still in the rift-python directory, create a new virtual environment named env:

<pre>
vm$ <b>virtualenv env --python=python3</b>
Already using interpreter /usr/bin/python3
Using base prefix '/usr'
New python executable in /home/ubuntu/rift-python/env/bin/python3
Also creating executable in /home/ubuntu/rift-python/env/bin/python
Installing setuptools, pkg_resources, pip, wheel...done.
</pre>

### Activate the Python virtual environment

While still in the rift-fsm directory, activate the newly created Python environment:

<pre>
vm$ <b>source env/bin/activate</b>
</pre>

### Use pip to install dependencies

Use pip to install the external following modules. It is important that you have activated
the virtual environment as described in the previous step before you install these dependencies.

Install the trift module which is used to encode and decode Thrift messages:

<pre>
vm$ <b>pip install thrift</b>
</pre>

Install the sortedcontainers module which is used to created Python sorted containers (e.g. sorted dictionaries):

<pre>
vm$ <b>pip install sortedcontainers</b>
</pre>

Install the netifaces module which provides cross-platform portable code for retrieving information about interfaces and their addresses:

<pre>
vm$ <b>pip install netifaces</b>
</pre>

Install the pyyaml module which is used to parse YAML files:

<pre>
vm$ <b>pip install pyyaml</b>
</pre>

Install the cerberus module which is used to validate whether the data stored in a YAML file conforms to a data model (schema):

<pre>
vm$ <b>pip install cerberus</b>
</pre>

In one SSH session to the virtual machine, run the main.py script of Python RIFT with the --help command line parameter to make verify that it has been properly installed:

<pre>
vm1$ $ <b>python3 main.py --help</b>
usage: main.py [-h] [-p | -n] [configfile]

Routing In Fat Trees (RIFT) protocol engine

positional arguments:
  configfile         Configuration filename

optional arguments:
  -h, --help         show this help message and exit
  -p, --passive      Run only the nodes marked as passive
  -n, --non-passive  Run all nodes except those marked as passive
</pre>

See the [Python RIFT documentation](https://github.com/brunorijsman/rift-python/blob/master/README.md) for full documentation of the command line options.

Start the main.py script in Python RIFT without any command-line options to start it as single stand-alone mode:

<pre>
vm1$ <b>python3 main.py</b>
Command Line Interface (CLI) available on port 40441
</pre>

If all goes well, this produces a single line output as shown above. Make a note of the port number (40441 in this example).

You can press Control-C to stop the Python RIFT node. Don't stop it now, let it run.

Open a new SSH session to the virtual machine. Once logged in to the virtual machine, create a Telnet session to the port number reported above:

<pre>
vm2$ <b>telnet localhost 40441</b>
Trying 127.0.0.1...
Connected to localhost.
Escape character is '^]'.
ip-172-31-16-2551> 
</pre>

You will get a prompt equal to the name of the node, which by default is equal to the hostname of the virtual machine (ip-172-31-16-255 in this example) followed by a local node identifier (1 in this example).

Note: there is currently no "exit" command in the CLI. To exit the Telnet session use "Control-]" and then enter "exit". (Don't exit now.)

<pre>
ip-172-31-16-2551> <b>^]</b>
telnet> <b>quit</b>
Connection closed.
</pre>

Enter the "show node" command as an example of a CLI command:

<pre>
ip-172-31-16-2551> <b>show node</b>
+-------------------------------------+-------------------+
| Name                                | ip-172-31-16-2551 |
| Passive                             | False             |
| Running                             | True              |
| System ID                           | 6234ed83dc30da01  |
| Configured Level                    | 0                 |
| Multicast Loop                      | True              |
| Receive LIE IPv4 Multicast Address  | 224.0.0.120       |
| Transmit LIE IPv4 Multicast Address | 224.0.0.120       |
| Receive LIE IPv6 Multicast Address  | FF02::0078        |
| Transmit LIE IPv6 Multicast Address | FF02::0078        |
| Receive LIE Port                    | 10000             |
| Transmit LIE Port                   | 10000             |
| LIE Send Interval                   | 1.0 secs          |
| Receive TIE Port                    | 10001             |
+-------------------------------------+-------------------+
</pre>

See the [Python RIFT documentation](https://github.com/brunorijsman/rift-python/blob/master/README.md) for full documentation of the CLI commands.

Note: At this time Python RIFT does not fully support the Telnet protocol. As a result, things such as command history (Control-N or Control-P or Cursor-Up or Cursor-Down) and tab completion do not work.

Stop the RIFT node by going back to the SSH session where you started the RIFT node, and press Control-C:

<pre>
vm1$ python3 main.py
Command Line Interface (CLI) available on port 40299
<b>^C</b>
Traceback (most recent call last):
  File "main.py", line 28, in <module>
    rift_object.run()
  File "/home/ubuntu/rift-python/rift.py", line 52, in run
    scheduler.scheduler.run()
  File "/home/ubuntu/rift-python/scheduler.py", line 32, in run
    rx_ready, tx_ready, _ = select.select(self._rx_sockets, self._tx_sockets, [], timeout)
KeyboardInterrupt
</pre>

### Run a Python RIFT Topology

Python RIFT understands the same format of topology YAML files that Juniper RIFT uses.


We will now start a small two node topology, where both nodes run Python RIFT. This demonstrates that Juniper RIFT can establish a 3-way adjacency with itself. Later on, we will replace one of the Juniper RIFT nodes with a Python RIFT node for the interoperability testing.

Use the following command to start a small two node topology:

<pre>
vm1$ <b>python3 main.py two.yaml</b>
Command Line Interface (CLI) available on port 38461
</pre>

This starts a single RIFT protocol engine (i.e. a single Python process) that hosts two RIFT nodes.

In another SSH session to the same virtual machine, start a Telnet session to the CLI port (38461 in this example) of the RIFT protocol engine:

<pre>
$ <b>telnet localhost 38461</b>
Trying 127.0.0.1...
Connected to localhost.
Escape character is '^]'.
agg_202> 
</pre>

In the CLI, enter command "show nodes" to see both RIFT nodes:

<pre>
agg_202> <b>show nodes</b>
+---------+--------+---------+
| Node    | System | Running |
| Name    | ID     |         |
+---------+--------+---------+
| agg_202 | 202    | True    |
+---------+--------+---------+
| core_1  | 1      | True    |
+---------+--------+---------+
</pre>

The prompt "agg_202" indicates that node agg_202 is the currently active node.

In the CLI, enter command "show interfaces" to see all interfaces of the current node agg_202. It shows that there is a single interface in state THREE_WAY:

<pre>
agg_202> <b>show interfaces</b>
+-----------+-----------------+-----------+-----------+
| Interface | Neighbor        | Neighbor  | Neighbor  |
| Name      | Name            | System ID | State     |
+-----------+-----------------+-----------+-----------+
| if_202_1  | core_1-if_1_202 | 1         | THREE_WAY |
+-----------+-----------------+-----------+-----------+
</pre>

In the CLI, enter command "show interface if_202_1" to see the details of both the interface and the neighbor:

<pre>
agg_202> <b>show interface if_202_1</b>
Interface:
+-------------------------------------+------------------+
| Interface Name                      | if_202_1         |
| Advertised Name                     | agg_202-if_202_1 |
| Interface IPv4 Address              |                  |
| Metric                              | 1                |
| Receive LIE IPv4 Multicast Address  | 224.0.100.2      |
| Transmit LIE IPv4 Multicast Address | 224.0.100.1      |
| Receive LIE IPv6 Multicast Address  | FF02::0078       |
| Transmit LIE IPv6 Multicast Address | FF02::0078       |
| Receive LIE Port                    | 20021            |
| Transmit LIE Port                   | 20022            |
| Receive TIE Port                    | 20024            |
| System ID                           | 202              |
| Local ID                            | 1                |
| MTU                                 | 1500             |
| POD                                 | 0                |
| State                               | THREE_WAY        |
| Neighbor                            | Yes              |
+-------------------------------------+------------------+

Neighbor:
+----------------------------------+-----------------+
| Name                             | core_1-if_1_202 |
| System ID                        | 1               |
| IPv4 Address                     | 172.31.16.255   |
| LIE UDP Source Port              | 50834           |
| Link ID                          | 1               |
| Level                            | 0               |
| Flood UDP Port                   | 10001           |
| MTU                              | 1500            |
| POD                              | 0               |
| Hold Time                        | 3               |
| Not a ZTP Offer                  | False           |
| You Are Not a ZTP Flood Repeater | False           |
| Your System ID                   | 202             |
| Your Local ID                    | 1               |
+----------------------------------+-----------------+
</pre>

In the CLI, enter command "node core_1" to change the currently active node to core_1. Then, enter command "show interface if_1_202" to see the adjacency up in state THREE_WAY from the other side:

<pre>
agg_202> set node core_1

core_1> show interface if_1_202
Interface:
+-------------------------------------+-----------------+
| Interface Name                      | if_1_202        |
| Advertised Name                     | core_1-if_1_202 |
| Interface IPv4 Address              |                 |
| Metric                              | 1               |
| Receive LIE IPv4 Multicast Address  | 224.0.100.1     |
| Transmit LIE IPv4 Multicast Address | 224.0.100.2     |
| Receive LIE IPv6 Multicast Address  | FF02::0078      |
| Transmit LIE IPv6 Multicast Address | FF02::0078      |
| Receive LIE Port                    | 20022           |
| Transmit LIE Port                   | 20021           |
| Receive TIE Port                    | 20023           |
| System ID                           | 1               |
| Local ID                            | 1               |
| MTU                                 | 1500            |
| POD                                 | 0               |
| State                               | THREE_WAY       |
| Neighbor                            | Yes             |
+-------------------------------------+-----------------+

Neighbor:
+----------------------------------+------------------+
| Name                             | agg_202-if_202_1 |
| System ID                        | 202              |
| IPv4 Address                     | 172.31.16.255    |
| LIE UDP Source Port              | 51838            |
| Link ID                          | 1                |
| Level                            | 0                |
| Flood UDP Port                   | 10001            |
| MTU                              | 1500             |
| POD                              | 0                |
| Hold Time                        | 3                |
| Not a ZTP Offer                  | False            |
| You Are Not a ZTP Flood Repeater | False            |
| Your System ID                   | 1                |
| Your Local ID                    | 1                |
+----------------------------------+------------------+
</pre>

Stop the RIFT node by going back to the SSH session where you started the RIFT node, and press Control-C.

### Run a Juniper RIFT - Python RIFT Interoperability Testing Topology

We will now create a topology that contains two nodes: one Juniper RIFT node and one.

#### Create the Topology YAML file

We will use the file "two.yaml" which is stored in the Python RIFT repo as the single topology YAML file that is used by both the Juniper RIFT node and the Python RIFT node. 

In this file two.yaml, the node core_1 is not marked as passive, and the node agg_202 is marked as passive:
<pre>
shards:
  - id: 0
    nodes:
      - name: core_1
        level: 2
        systemid: 1
[...]
      - name: agg_202
        <b>passive: true</b>
        level: 1
        systemid: 202
</pre>


Note: we must have a single YAML file that is used by both the Juniper RIFT node and the Python RIFT node. It is not possible to create one YAML file for the Juniper RIFT node and a different YAML file for the Python RIFT node. I won't go into the details of why, but it is related to the way multiple links are simulated on a single host using UDP port numbers and IP multicast addresses.

#### Start Juniper RIFT node core_1

Start Juniper RIFT as follows:

<pre>
vm1$ <b>cd ${HOME}/content-x86_64-public/</b>
vm1$ <b>./bin/rift-environ -c -C lies -vvv -R 999999 topology ${HOME}/rift-python/two.yaml</b>
</pre>

Juniper RIFT notices that node agg_202 has been marked as passive, and does not start it. Hence Juniper RIFT is running only node core_1.

<pre>
Jul 18 18:56:04.477 INFO node agg_202 marked as passive, not started
</pre>

#### Start Python RIFT node agg_202

In a second SSH session to the virtual machine, start Python RIFT as follows:

<pre>
vm2$ <b>cd ${HOME}/rift-python</b>
vm2$ <b>source env/bin/activate</b>
(env) vm2$ <b>python3 main.py --passive two.yaml</b>
Command Line Interface (CLI) available on port 35403
</pre>

Make a note of the port (35403 in this case), you will need it later.

The command line option "--passive" instructs Python RIFT to only run the nodes that are marked as passive (which is exactly the opposite behavior of what Juniper RIFT is doing). As a result, Python RIFT will run node agg_202 and not node core_1)

In a third SSH session to the virtual machine, run a "tail -f" command to follow the very detailed logging that Python RIFT generates:

<pre>
vm3$ cd ${HOME}/rift-python
vm3$ tail -f rift.log 
2018-07-18 19:19:52,590:INFO:node.if.fsm:[202-if_202_1] FSM process event, state=THREE_WAY event=UPDATE_ZTP_OFFER
2018-07-18 19:19:52,590:INFO:node.if.fsm:[202-if_202_1] FSM invoke state-transition action, action=send_offer_to_ztp_fsm
2018-07-18 19:19:53,165:INFO:node.if.fsm:[202-if_202_1] FSM push event, event=TIMER_TICK
2018-07-18 19:19:53,165:INFO:node.if.fsm:[202-if_202_1] FSM process event, state=THREE_WAY event=TIMER_TICK
2018-07-18 19:19:53,165:INFO:node.if.fsm:[202-if_202_1] FSM invoke state-transition action, action=check_hold_time_expired
2018-07-18 19:19:53,165:INFO:node.if:[202-if_202_1] _time_ticks_since_lie_received = {}
2018-07-18 19:19:53,165:INFO:node.if.fsm:[202-if_202_1] FSM push event, event=SEND_LIE
2018-07-18 19:19:53,165:INFO:node.if.fsm:[202-if_202_1] FSM process event, state=THREE_WAY event=SEND_LIE
2018-07-18 19:19:53,166:INFO:node.if.fsm:[202-if_202_1] FSM invoke state-transition action, action=send_lie
2018-07-18 19:19:53,166:INFO:node.if.tx:[202-if_202_1] Send LIE ProtocolPacket(header=PacketHeader(sender=202, major_version=11, minor_version=0, level=0), content=PacketContent(lie=LIEPacket(flood_port=10001, capabilities=NodeCapabilities(leaf_indications=1, flood_reduction=True), nonce=6738351657972617102, name='agg_202-if_202_1', label=None, neighbor=Neighbor(remote_id=28672, originator=1), not_a_ztp_offer=False, link_mtu_size=1500, you_are_not_flood_repeater=False, local_id=1, holdtime=3, pod=0), tie=None, tide=None, tire=None))
[...]
</pre>

In a fourth SSH session to the same virtual machine, start a Telnet session to the CLI port of Python RIFT (which you noted above):

<pre>
vm4$ <b>telnet localhost 35403 </b>
Trying 127.0.0.1...
Connected to localhost.
Escape character is '^]'.
agg_202> 
</pre>

In the CLI session, issue the command "show nodes". Note that node agg_202 is running and node core_1 is not running.

<pre>
agg_202> <b>show nodes</b>
+---------+--------+---------+
| Node    | System | Running |
| Name    | ID     |         |
+---------+--------+---------+
| agg_202 | 202    | True    |
+---------+--------+---------+
| core_1  | 1      | False   |
+---------+--------+---------+
</pre>

On the CLI session, show the details of the currently active node, which is node agg_202:

<pre>
agg_202> <b>show node</b>
+-------------------------------------+-------------+
| Name                                | agg_202     |
| Passive                             | True        |
| Running                             | True        |
| System ID                           | 202         |
| Configured Level                    | 0           |
| Multicast Loop                      | True        |
| Receive LIE IPv4 Multicast Address  | 224.0.100.2 |
| Transmit LIE IPv4 Multicast Address | 224.0.0.120 |
| Receive LIE IPv6 Multicast Address  | ff02::2     |
| Transmit LIE IPv6 Multicast Address | FF02::0078  |
| Receive LIE Port                    | 19981       |
| Transmit LIE Port                   | 10000       |
| LIE Send Interval                   | 1.0 secs    |
| Receive TIE Port                    | 10001       |
+-------------------------------------+-------------+
</pre>

#### Check the Adjacency

We will now verify that the adjacency between the Juniper RIFT node and the Python RIFT node is fully up, i.e. has reached state THREE_WAY:

In the CLI session of the Python RIFT node, use the command "show interfaces" to report a summary of the interface:

<pre>
agg_202> <b>show interfaces</b>
+-----------+----------+-----------+-----------+
| Interface | Neighbor | Neighbor  | Neighbor  |
| Name      | Name     | System ID | State     |
+-----------+----------+-----------+-----------+
| if_202_1  | None     | 1         | <i><b>THREE_WAY</b></i> |
+-----------+----------+-----------+-----------+
</pre>

In the CLI session of the Python RIFT node, use the command "show interface if_202_1" to report much more detailed information about the interface and the neighbor:

<pre>
agg_202> <b>show interface if_202_1</b>
Interface:
+-------------------------------------+------------------+
| Interface Name                      | if_202_1         |
| Advertised Name                     | agg_202-if_202_1 |
| Interface IPv4 Address              |                  |
| Metric                              | 1                |
| Receive LIE IPv4 Multicast Address  | 224.0.100.2      |
| Transmit LIE IPv4 Multicast Address | 224.0.100.1      |
| Receive LIE IPv6 Multicast Address  | FF02::0078       |
| Transmit LIE IPv6 Multicast Address | FF02::0078       |
| Receive LIE Port                    | 20021            |
| Transmit LIE Port                   | 20022            |
| Receive TIE Port                    | 20024            |
| System ID                           | 202              |
| Local ID                            | 1                |
| MTU                                 | 1500             |
| POD                                 | 0                |
| State                               | <i><b>THREE_WAY</b></i>        |
| Neighbor                            | Yes              |
+-------------------------------------+------------------+

Neighbor:
+----------------------------------+---------------+
| Name                             | None          |
| System ID                        | 1             |
| IPv4 Address                     | 172.31.16.255 |
| LIE UDP Source Port              | 20021         |
| Link ID                          | 28672         |
| Level                            | 2             |
| Flood UDP Port                   | 20023         |
| MTU                              | 1400          |
| POD                              | 0             |
| Hold Time                        | 3             |
| Not a ZTP Offer                  | False         |
| You Are Not a ZTP Flood Repeater | False         |
| Your System ID                   | 202           |
| Your Local ID                    | 1             |
+----------------------------------+---------------+
</pre>

Note that the neighbor (i.e. the adjacency) is reported in state THREE_WAY in the above output.

In the tracing output of the Juniper RIFT node, look for the messages reporting that the neighbor (i.e. the adjacency) has reached state THREE_WAY:

<pre>
 peer: if_1_202->20022:20023:224.0.100.2/ff02::2
  nodeid: core_1
   subsystem: peering
    [...]
    Jul 18 20:01:22.946 DEBG received reflection first time, rebuild packet
    Jul 18 20:01:22.947 DEBG <b><i>addjacency 3-way up</i></b>
</pre>


### Appendix: Abbreviations

Abbreviation | Meaning |
--- | --- |
AMI | Amazon Machine Image |
AWS | Amazon Web Services |
EC2 | Elastic Compute Cloud |
FSM | Finite State Machine |
LIE | Link Information Element |
PIP | PIP Installs Python |
RIFT | Routing In Fat Trees |
SSH | Secure Shell |
UDP | User Datagram Protocol |
YAML | Yet Another Markup Language |
ZTP | Zero Touch Provisioning |

