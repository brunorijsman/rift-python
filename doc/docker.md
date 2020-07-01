# Docker

## Why Docker?

For the most part, RIFT-Python can be developed, tested, and used on any platform that supports
Python: not just Linux, but also macOS, Windows, and BSD.

However, the current implementation of RIFT-Python only supports installing routes in the kernel
route table on Linux. RIFT-Python will still run on other platforms, but it won't install routes
into the kernel and all `show kernel ...` CLI commands will return an error message.

To allow developers who use macOS or Windows as their development platform to test RIFT-Python
interaction with the Linux kernel, we have added some convenience scripts to run RIFT-Python
in a Linux container using Docker.

## Installing Docker

Follow the instructions on the [Docker Website](https://www.docker.com/get-started) to download
and install Docker in your development environment.

## Building the RIFT-Python Docker Container Image

The RIFT-Python repository contains a subdirectory `docker` which contains scripts for creating
and starting a docker container image.

To create the RIFT-Python docker image use the `docker-build` shell script:

<pre>
(env) $ <b>./docker-build</b>
Sending build context to Docker daemon  6.656kB
Step 1/8 : FROM ubuntu:latest
latest: Pulling from library/ubuntu
32802c0cfa4d: Pull complete 
da1315cffa03: Pull complete 
fa83472a3562: Pull complete 
f85999a86bef: Pull complete 
Digest: sha256:6d0e0c26489e33f5a6f0020edface2727db9489744ecc9b4f50c7fa671f23c49
Status: Downloaded newer image for ubuntu:latest
 ---> 93fd78260bd1
Step 2/8 : RUN apt-get update
 ---> Running in 79d24e89579c
Get:1 http://archive.ubuntu.com/ubuntu bionic InRelease [242 kB]
Get:2 http://security.ubuntu.com/ubuntu bionic-security InRelease [83.2 kB]
[...]
 ---> 612d5fabc8dd
Step 8/8 : VOLUME /host
 ---> Running in 8bbf68097bf2
Removing intermediate container 8bbf68097bf2
 ---> 0e70ec6cfcb8
Successfully built 0e70ec6cfcb8
Successfully tagged rift-python:latest
</pre>

You must activate the virtual environment before running the `docker-build` shell script:

<pre>
$ <b>cd ${HOME}/rift-python</b>
$ <b>source env/bin/activate</b>
(env) $ 
</pre>

When you run the `docker-build` script for the first time, it takes almost 4 minutes to complete
(depending on your Internet connection speed - it downloads large images).

You can verify that the docker image was created using the `docker images` command:

<pre>
(env) $ <b>docker images</b>
REPOSITORY          TAG                 IMAGE ID            CREATED             SIZE
rift-python         latest              0e70ec6cfcb8        3 minutes ago       522MB
ubuntu              latest              93fd78260bd1        4 weeks ago         86.2MB
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
(env) $ ./docker-shell 
root@ee292d55bf57:/# 
</pre>

At this point you are in an Ubuntu Linux environment and you can execute any ol' Linux command:

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
+-------+---------+---------------+---------+----------+-----------+------------+--------+
| Table | Address | Destination   | Type    | Protocol | Outgoing  | Gateway    | Weight |
|       | Family  |               |         |          | Interface |            |        |
+-------+---------+---------------+---------+----------+-----------+------------+--------+
| Main  | IPv4    | 0.0.0.0/0     | Unicast | Boot     | eth0      | 172.17.0.1 |        |
+-------+---------+---------------+---------+----------+-----------+------------+--------+
| Main  | IPv4    | 172.17.0.0/16 | Unicast | Kernel   | eth0      |            |        |
+-------+---------+---------------+---------+----------+-----------+------------+--------+
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
+------------+-----------+----------------+
| Prefix     | Owner     | Next-hops      |
+------------+-----------+----------------+
| 2.2.2.2/32 | South SPF | if1 172.17.0.2 |
+------------+-----------+----------------+

node1> <b>show kernel route table main prefix 2.2.2.2/32</b>
Prefix "2.2.2.2/32" in table "Main" not present in kernel route table
</pre>



There are two reasons for this behavior:

 * While there are multiple nodes in a multi-node topology, there is only a single kernel to
   install routes into.
 * The interface names that are used in multi-node topologies are fictitious (e.g. "if1") and
   do not correspond to real interfaces that are known by the kernel.

Ways to get around both issues are discussed 
[below](#realistic-testing-of-multi-node-topologies-in-docker)

### Starting a Container Running RIFT

The `docker-rift` script starts a container running a single stand-alone instance of RIFT-Python
and immediately places you in the CLI:

<pre>
(env) $ <b>./docker-rift</b>
2ca54a23b8ab1> <b>show interfaces</b>
+-----------+----------+-----------+----------+
| Interface | Neighbor | Neighbor  | Neighbor |
| Name      | Name     | System ID | State    |
+-----------+----------+-----------+----------+
| en0       |          |           | ONE_WAY  |
+-----------+----------+-----------+----------+
</pre>

Use the `stop` CLI command to exit the container.

## Running Tests in Docker

Above, we described how to start RIFT-Python "as usual" from inside the Docker container.
You can also run unit tests and system tests "as usual" from inside the container.

To start a single unit test "as usual" from inside the Docker container, use the following steps:

<pre>
(env) $ <b>./docker-shell</b>
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
that the kernel tests will pass inTravis as well.

## Realistic Testing of Multi-Node Topologies in Docker

Note: This is an area still under development. In the future additional and tools and scripts will
be added to make this easier.

As mentioned [before](#running-tests-in-docker), when you run a multi-node topology system test
in a Docker container, RIFT-Python typically still does not properly install routes in the kernel
route table because there is only one kernel and because the interface names are not real.

One way to work around these issues is to:

 * Use multiple network name spaces in the Docker container.
 * Interconnect the network name spaces using virtual Ethernet interfaces (veth pairs)
 * Run a separate RIFT-Python process in each name space.

Here is an example sequence of shell command to achieve this (once again, we will provide tools
and scripts to make this easier in the future):

<pre>
ip link add dev veth-a1 type veth peer name veth-a2
ip link add dev veth-b1 type veth peer name veth-b2
ip netns add netns-1
ip link set veth-a1 netns netns-1
ip netns exec netns-1 ip link set dev veth-a1 up
ip netns exec netns-1 ip addr add 99.99.1.1/24 dev veth-a1
ip link set veth-b1 netns netns-1
ip netns exec netns-1 ip link set dev veth-b1 up
ip netns exec netns-1 ip addr add 99.99.2.1/24 dev veth-b1
ip netns exec netns-1 ip link set dev lo up
ip netns exec netns-1 ip addr add 88.88.1.1/32 dev lo
ip netns add netns-2
ip link set veth-a2 netns netns-2
ip netns exec netns-2 ip link set dev veth-a2 up
ip netns exec netns-2 ip addr add 99.99.1.2/24 dev veth-a2
ip link set veth-b2 netns netns-2
ip netns exec netns-2 ip link set dev veth-b2 up
ip netns exec netns-2 ip addr add 99.99.2.2/24 dev veth-b2
ip netns exec netns-2 ip link set dev lo up
ip netns exec netns-2 ip addr add 88.88.2.1/32 dev lo
cd /host
ip netns exec netns-1 python3 rift --multicast-loopback-disable topology/real_1.yaml &
ip netns exec netns-2 python3 rift -i --multicast-loopback-disable -l debug topology/real_2.yaml
</pre>



