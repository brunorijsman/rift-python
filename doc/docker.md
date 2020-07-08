# Docker

## Why Docker?

RIFT-Python can be developed, tested, and used on macOS Mojave (10.14), macOS Catalina (10.15), and
Ubuntu Xenial (16.04) Linux. Since it is written in Python, it _should_ also work on other platforms
including Windows and other Linux distributions, but we have not tested that.

However, the current implementation of RIFT-Python only supports installing routes in the kernel
route table on Linux. RIFT-Python will still run on other platforms, but it won't install routes
into the kernel and all `show kernel ...` CLI commands will return an error message.

To allow developers who use macOS as their development platform to test RIFT-Python interaction
with the Linux kernel, we have added some convenience scripts to run RIFT-Python in a Linux
container using Docker.

## Installing Docker

Follow the instructions on the [Docker Website](https://www.docker.com/get-started) to download
and install Docker in your development environment.

## Building the RIFT-Python Docker Container Image

The RIFT-Python repository contains a subdirectory `docker` which contains scripts for creating
and starting a docker container image.

If you have not already done so, go to the root directory of the rift-python repository and
activate the Python virtual environment:

<pre>
$ <b>cd ~/rift-python</b>
$ <b>source env/bin/activate</b>
(env) $
</pre>

To create the RIFT-Python docker image use the `docker-build` shell script:

<pre>
(env) $ <b>docker/docker-build</b>
(env) $ docker/docker-build 
Sending build context to Docker daemon  9.216kB
Step 1/14 : FROM ubuntu:16.04
16.04: Pulling from library/ubuntu
6aa38bd67045: Pull complete 
...
Removing intermediate container b6aaef1614ed
 ---> 5f31dd71fd5f
Successfully built 5f31dd71fd5f
Successfully tagged rift-python:latest
</pre>

When you run the `docker-build` script for the first time, it takes almost 4 minutes to complete
(depending on your Internet connection speed - it downloads large images).

You can verify that the docker image was created using the `docker images` command:

<pre>
(env) $ <b>docker images</b>
REPOSITORY          TAG                 IMAGE ID            CREATED             SIZE
rift-python         latest              f8be1435a49d        5 minutes ago       554MB
ubuntu              16.04               c522ac0d6194        33 hours ago        126MB
</pre>

## The /host Directory in the RIFT-Python Docker Container

The Docker container image that is created by the `docker-build` script includes all dependencies
needed to run RIFT-Python (e.g. Python3, all dependency modules, etc.) but it does _not_ include the
RIFT-Python source code itself.

This was a conscious choice. If we included the RIFT-Python source code in the container image,
we would have to re-build the container image every single time we changed RIFT-Python source code.
This would significantly slow down the development cycle.

Instead, the `Dockerfile` which is used by the `docker-build` script includes a `VOLUME /host`
statement. The scripts which start the docker container (which are explained below) mount the
`/host` volume in the container to the `rift-python` directory that represents the Git
repository on the development host.

The net result of this, is that the directory `/host` inside the running container contains the
entire live development environment on the host. If you make a change in the source code on the
host, the change will immediately be visible inside the container without any need for re-building
the container.

## Starting the RIFT-Python Docker Container Image

There are two scripts for starting a RIFT-Python Docker container:

### Starting a Container Running the Shell

The `docker-shell` script starts a container running the bash shell:

<pre>
(env) $ docker/docker-shell 
root@ee292d55bf57:/# 
</pre>

At this point you are in an Ubuntu Linux environment and you can execute any Linux command:

<pre>
root@ee292d55bf57:/# <b>uname</b>
Linux
</pre>

You can change directory to the `/host` directory and start RIFT-Python as you would normally:

<pre>
root@ee292d55bf57:/# <b>cd /host</b>
root@ee292d55bf57:/host# <b>python3 rift -i topology/3n_l0_l1_l2.yaml</b>
node1> 
</pre>

Note: if you don't activate the virtual environment, make sure to run `python3` instead of just
`python`.

Observe that while running in Docker, RIFT-Python does support the `show kernel ...` CLI commands:

<pre>
node1> <b>show kernel routes table main</b>
Kernel Routes:
+-------+---------+-----------------+---------+----------+-----------+---------------+--------+
| Table | Address | Destination     | Type    | Protocol | Outgoing  | Gateway       | Weight |
|       | Family  |                 |         |          | Interface |               |        |
+-------+---------+-----------------+---------+----------+-----------+---------------+--------+
| Main  | IPv4    | 0.0.0.0/0       | Unicast | Boot     | eth0      | 172.17.0.1    |        |
+-------+---------+-----------------+---------+----------+-----------+---------------+--------+
| Main  | IPv4    | 172.17.0.0/16   | Unicast | Kernel   | eth0      |               |        |
+-------+---------+-----------------+---------+----------+-----------+---------------+--------+
| Main  | IPv6    | ::/0            | Unicast | Boot     | eth0      | 2001:db8:1::1 |        |
+-------+---------+-----------------+---------+----------+-----------+---------------+--------+
| Main  | IPv6    | 2001:db8:1::/64 | Unicast | Kernel   | eth0      |               |        |
+-------+---------+-----------------+---------+----------+-----------+---------------+--------+
| Main  | IPv6    | fe80::/64       | Unicast | Kernel   | eth0      |               |        |
+-------+---------+-----------------+---------+----------+-----------+---------------+--------+
</pre>

Still, when you run a multi-node topology in a Docker container, you might be surprised that
RIFT-Python typically does *not* properly install routes into the Kernel route tables:

<pre>
node1> <b>show route prefix 2.2.2.2/32</b>
+------------+-----------+----------------+
| Prefix     | Owner     | Next-hops      |
+------------+-----------+----------------+
| 2.2.2.2/32 | South SPF | if1 172.17.0.2 |
+------------+-----------+----------------+

node1> <b>show forwarding prefix 2.2.2.2/32</b>
+------------+----------------+
| Prefix     | Next-hops      |
+------------+----------------+
| 2.2.2.2/32 | if1 172.17.0.2 |
+------------+----------------+

node1> <b>show kernel route table main prefix 2.2.2.2/32</b>
Prefix "2.2.2.2/32" in table "Main" not present in kernel route table
</pre>

There are two reasons for this behavior:

 * While there are multiple nodes in a multi-node topology, there is only a single kernel to
   install routes into.

 * The interface names that are used in multi-node topologies are fictitious (e.g. "if1") and
   do not correspond to real interfaces that are known by the kernel.

Ways to get around both issues are discussed 
[below](#multi-process-testing-of-multi-node-topologies-in-docker)

### Starting a Container Running RIFT

The `docker-rift` script starts a container running a single stand-alone instance of RIFT-Python
and immediately places you in the CLI:

<pre>
(env) $ <b>docker/docker-rift</b>
2ca54a23b8ab1> <b>show interfaces</b>
+-----------+----------+-----------+----------+-------------------+-------+
| Interface | Neighbor | Neighbor  | Neighbor | Time in           | Flaps |
| Name      | Name     | System ID | State    | State             |       |
+-----------+----------+-----------+----------+-------------------+-------+
| en0       |          |           | ONE_WAY  | 0d 00h:00m:07.85s | 0     |
+-----------+----------+-----------+----------+-------------------+-------+
</pre>

Use the `stop` CLI command to exit the container.

## Running Tests in Docker

Above, we described how to start RIFT-Python "as usual" from inside the Docker container.
You can also run unit tests and system tests "as usual" from inside the container.

First remove all cached .pyc files, otherwhise running the test from inside the container will
report an error because the filenames of the Python files are different in the container because
of the directory mapping:

<pre>
(env) $ <b>rm -rf rift/__pycache__</b>
(env) $ <b>rm -rf tests/__pycache__</b>
</pre>

Then, start a single unit test "as usual" from inside the Docker container, using the following
steps:

<pre>
(env) $ <b>docker/docker-shell</b>
root@faf75d4aa679:/# <b>cd /host</b>
root@faf75d4aa679:/host# <b>pytest tests/test_table.py</b>
======================================================= test session starts ========================================================
platform linux -- Python 3.6.7, pytest-3.6.4, py-1.5.4, pluggy-0.7.1
rootdir: /host, inifile:
plugins: cov-2.5.1
collected 4 items                                                                                                                  

tests/test_table.py ....                                                                                                     [100%]

===================================================== 4 passed in 0.13 seconds =====================================================
root@faf75d4aa679:/host# 
</pre>

One particularly interesting unit test to run from inside the Docker container is the
`test_kernel.py` unit test. If you run this unit test from macOS or Windows, all tests will pass
without doing any real testing; but if you run it on Linux in the Docker container, it will actually
test the interaction with the Kernel using Netlink.

You can observe this for yourself by running the test with code coverage measurement enabled:

<pre>
root@faf75d4aa679:/host# <b>source env/bin/activate</b>
(env) root@faf75d4aa679:/host# <b>tools/cleanup && pytest -vvv -s tests/test_kernel.py --cov --cov-report=html</b>
tools/cleanup: line 10: cd: /Users/brunorijsman/rift-python/env/..: No such file or directory
======================================================= test session starts ========================================================
platform linux -- Python 3.6.7, pytest-3.6.4, py-1.5.4, pluggy-0.7.1 -- /usr/bin/python3
cachedir: .pytest_cache
rootdir: /host, inifile:
plugins: cov-2.5.1
collected 9 items                                                                                                                  

tests/test_kernel.py::test_create_kernel PASSED
tests/test_kernel.py::test_cli_addresses_table PASSED
tests/test_kernel.py::test_cli_links_table PASSED
tests/test_kernel.py::test_cli_routes_table PASSED
tests/test_kernel.py::test_cli_route_prefix_table PASSED
tests/test_kernel.py::test_put_del_route PASSED
tests/test_kernel.py::test_put_del_route_errors PASSED
tests/test_kernel.py::test_table_nr_to_name PASSED
tests/test_kernel.py::test_table_name_to_nr PASSED

----------- coverage: platform linux, python 3.6.7-final-0 -----------
Coverage HTML written to dir htmlcov


===================================================== 9 passed in 7.15 seconds =====================================================
(env) root@faf75d4aa679:/host# 
</pre>

Open a web browser and click on `rift/kernel.py` to see that a large portion of the kernel module has
in fact been covered by the unit test. The following command must be executed from the host
operating system (not the Docker container) and in this example we assume your are running macOS:

<pre>
(env) $ open htmlcov/index.html
</pre>

To start a single system test "as usual" from inside the Docker container, use the following steps:

<pre>
(env) root@faf75d4aa679:/host# <b>pytest tests/test_sys_2n_l0_l1.py</b>
======================================================= test session starts ========================================================
platform linux -- Python 3.6.7, pytest-3.6.4, py-1.5.4, pluggy-0.7.1
rootdir: /host, inifile:
plugins: cov-2.5.1
collected 1 item                                                                                                                   

tests/test_sys_2n_l0_l1.py .                                                                                                 [100%]

==================================================== 1 passed in 23.48 seconds =====================================================
(env) root@faf75d4aa679:/host# 
</pre>

To run the entire suite of unit tests and system tests, and also lint the code, use the
`pre-commit-checks` script:

<pre>
(env) root@faf75d4aa679:/host# tools/pre-commit-checks 
tools/pre-commit-checks: line 10: cd: /Users/brunorijsman/rift-python/env/..: No such file or directory

------------------------------------
Your code has been rated at 10.00/10


------------------------------------
Your code has been rated at 10.00/10

======================================================= test session starts ========================================================
platform linux -- Python 3.6.7, pytest-3.6.4, py-1.5.4, pluggy-0.7.1
rootdir: /host, inifile:
plugins: cov-2.5.1
collected 78 items                                                                                                                 

tests/test_constants.py ....                                                                                                 [  5%]
tests/test_fsm.py ......                                                                                                     [ 12%]
tests/test_kernel.py .........                                                                                               [ 24%]
[...]
tests/test_telnet.py ......                                                                                                  [ 92%]
tests/test_timer.py .....                                                                                                    [ 98%]
tests/test_visualize_log.py .                                                                                                [100%]

----------- coverage: platform linux, python 3.6.7-final-0 -----------
Name                                                                                        Stmts   Miss  Cover
---------------------------------------------------------------------------------------------------------------
rift/__main__.py                                                                               58      9    84%
rift/cli_listen_handler.py                                                                     28      3    89%
[...]
/usr/local/lib/python3.6/dist-packages/yaml/serializer.py                                      85     70    18%
/usr/local/lib/python3.6/dist-packages/yaml/tokens.py                                          76     17    78%
---------------------------------------------------------------------------------------------------------------
TOTAL                                                                                       26000  12460    52%


=================================================== 78 passed in 272.11 seconds ====================================================
All good; you can commit.
(env) root@faf75d4aa679:/host# 
</pre>

## A Note on Travis Continuous Integration

As mentioned before, the Docker container is useful for testing the interaction with the kernel
route table. 

When you commit and push new code to the RIFT-Python repository, an Continuous
Integration (CI) cycle automatically kicks off and runs the entire test suite in
[Travis](https://travis-ci.org/). Note that Travis runs its tests in Linux virtual machines, which
means that the kernel integration will be tested there are well. 

If you only run `pre-commit-checks`
in your macOS or Windows host environment (and not in the Docker container), you cannot be sure 
that the kernel tests will pass in Travis as well.

## Multi-Process Testing of Multi-Node Topologies in Docker

The following example demonstrates how to run a multi-process topology in Docker.

Start a docker shell:

<pre>
(env) $ <b>docker/docker-shell</b>
root@6bc97a203594:/# 
</pre>

Generate shell scripts and configuration files from the meta-topology file:

<pre>
root@6bc97a203594:/# <b>cd /host</b>
root@6bc97a203594:/host# <b>tools/config_generator.py -n meta_topology/2c_3x2.yaml generated</b>
</pre>

Depending on your laptop, you will typically only be able to run fairly small topologies. If you
need to run large topologies, use a suitably powerful AWS instance.

Start the topology:

<pre>
root@76acd2ce9f8c:/host# <b>generated/start.sh</b>
Create veth pair veth-1001a-101a and veth-101a-1001a for link from leaf-1:if-1001a to spine-1:if-101a
Create veth pair veth-1001b-102a and veth-102a-1001b for link from leaf-1:if-1001b to spine-2:if-102a
Create veth pair veth-1002a-101b and veth-101b-1002a for link from leaf-2:if-1002a to spine-1:if-101b
Create veth pair veth-1002b-102b and veth-102b-1002b for link from leaf-2:if-1002b to spine-2:if-102b
Create veth pair veth-1003a-101c and veth-101c-1003a for link from leaf-3:if-1003a to spine-1:if-101c
Create veth pair veth-1003b-102c and veth-102c-1003b for link from leaf-3:if-1003b to spine-2:if-102c
Create network namespace netns-1001 for node leaf-1
Create network namespace netns-1002 for node leaf-2
Create network namespace netns-1003 for node leaf-3
Create network namespace netns-101 for node spine-1
Create network namespace netns-102 for node spine-2
Start RIFT-Python engine for node leaf-1
Start RIFT-Python engine for node leaf-2
Start RIFT-Python engine for node leaf-3
Start RIFT-Python engine for node spine-1
Start RIFT-Python engine for node spine-2
</pre>

Connect to one of the nodes, in this example node spine-2:

<pre>
root@76acd2ce9f8c:/host# <b>generated/connect-spine-2.sh</b>
Trying ::1...
Trying 127.0.0.1...
Connected to localhost.
Escape character is '^]'.
spine-2> 
</pre>

You can see that in this multi-process topology, routes are actually installed in the kernel:

<pre>
spine-2> <b>show route prefix 88.0.1.1/32</b>
+-------------+-----------+--------------------------+
| Prefix      | Owner     | Next-hops                |
+-------------+-----------+--------------------------+
| 88.0.1.1/32 | South SPF | veth-102a-1001b 99.0.4.1 |
+-------------+-----------+--------------------------+

spine-2> <b>show forwarding prefix 88.0.1.1/32</b>
+-------------+--------------------------+
| Prefix      | Next-hops                |
+-------------+--------------------------+
| 88.0.1.1/32 | veth-102a-1001b 99.0.4.1 |
+-------------+--------------------------+

spine-2> <b>show kernel routes table main prefix 88.0.1.1/32</b>
+--------------------------+---------------------------+
| Table                    | Main                      |
| Address Family           | IPv4                      |
| Destination              | 88.0.1.1/32               |
| Type                     | Unicast                   |
| Protocol                 | RIFT                      |
| Scope                    | Universe                  |
| Next-hops                | veth-102a-1001b 99.0.4.1  |
| Priority                 | 199                       |
| Preference               |                           |
| Preferred Source Address |                           |
| Source                   |                           |
| Flow                     |                           |
| Encapsulation Type       |                           |
| Encapsulation            |                           |
| Metrics                  |                           |
| Type of Service          | 0                         |
| Flags                    | 0                         |
+--------------------------+---------------------------+
</pre>

Exit out of the CLI:

<pre>
spine-2> <b>exit</b>
Connection closed by foreign host.
root@76acd2ce9f8c:/host# 
</pre>

Stop the topology:

<pre>
root@76acd2ce9f8c:/host# <b>generated/stop.sh </b>
Stop RIFT-Python engine for node leaf-1
Delete interface veth-1001a-101a for node leaf-1
Delete interface veth-1001b-102a for node leaf-1
Stop RIFT-Python engine for node leaf-2
Delete interface veth-1002a-101b for node leaf-2
Delete interface veth-1002b-102b for node leaf-2
Stop RIFT-Python engine for node leaf-3
Delete interface veth-1003a-101c for node leaf-3
Delete interface veth-1003b-102c for node leaf-3
Stop RIFT-Python engine for node spine-1
Delete interface veth-101a-1001a for node spine-1
Delete interface veth-101b-1002a for node spine-1
Delete interface veth-101c-1003a for node spine-1
Stop RIFT-Python engine for node spine-2
Delete interface veth-102a-1001b for node spine-2
Delete interface veth-102b-1002b for node spine-2
Delete interface veth-102c-1003b for node spine-2
Delete network namespace netns-1001 for node leaf-1
Delete network namespace netns-1002 for node leaf-2
Delete network namespace netns-1003 for node leaf-3
Delete network namespace netns-101 for node spine-1
Delete network namespace netns-102 for node spine-2
</pre>

Exit out of the container (which also stops the container):

<pre>
root@76acd2ce9f8c:/host# <b>exit</b>
exit
(env) $ 
</pre>