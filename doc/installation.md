# Supported platforms

As the name suggests, RIFT-Python has been implemented in Python 3. It has been tested the following
versions of CPython:
 * Python 3.5
 * Python 3.6
 * Python 3.7
 * Python 3.8 
 
RIFT-Python cannot run on any version of Python 2.

RIFT-Python has been tested on the following operating systems:
 * Ubuntu 16.04 LTS (Xenial)
 * Ubuntu 18.04 LTS (Bionic)
 * Ubuntu 20.04 LTS (Focal)
 * macOS 10.14 (Mojave)
 * macOS 10.15 (Catalina)

It should be possible to run RIFT-Python on versions of Linux or macOS or even on other platforms 
(such as Windows) with little or no porting, but we have not tested that. Most code is very 
portable, except for the code that deals with sending multicast and IPv6 UDP packets over sockets,
which is infuriatingly platform dependent in subtle ways.

# Installation Instructions

Installation instructions for:

* [Ubuntu Linux on AWS](#ubuntu-linux-on-aws)
* [Ubuntu Linux on local VM via Vagrant](#ubuntu-linux-on-local-vm-via-vagrant)

## Ubuntu Linux on AWS

Here we describe how to install the Python RIFT protocol engine on an Amazon Web Services (AWS)
Elastic Compute Cloud (EC2) instance running Ubuntu 20.04 LTS (Focal).

These instructions should also work for an Ubuntu 20.04 LTS server running on bare metal or in 
a locally hosted virtual machine or in a container.

### Create an EC2 instance

Using the AWS console (or CLI or API) create an EC2 instance:

* Choose Amazon Machine Image (AMI) "Ubuntu Server 20.04 LTS (HVM), SSD Volume Type"
* Choose instance type t2.micro
* Use the default values for all other configuration parameters
* Make sure you download the private key for the EC2 instance

Note: We are using a t2.micro instance type because it is eligible for AWS Free Tier. For large
multi-node topologies you need a larger instance type with more CPU and memory.

### Login to Ubuntu

Use user name ubuntu and your private key file to login:

<pre>
$ <b>ssh ubuntu@</b><i>ec2-instance-ip-address</i><b> -i ~/.ssh/</b><i>your-private-key-file</i><b>.pem</b> 
</pre>

In the above command we assume you are logging in from a platform (such as Linux or macOS) that
supports a standard Telnet client. If you are logging in from Windows you may have to download
a Windows Telnet client such as Putty.

### Update

Once logged in to the EC2 instance, install the latest security patches on your EC2 instance 
by doing an update:

<pre>
$ <b>sudo apt-get update</b>
</pre>

### Install Python3

The AWS Ubuntu 20.04 AMI comes pre-installed with Python 3.8:

<pre>
$ <b>python3 --version</b>
Python 3.8.2
</pre>

However, if you need to install Python 3 yourself you can do so as follows:

<pre>
$ <b>sudo apt-get install -y python3</b>
</pre>

### Install build-essential

RIFT-Python itself is written entirely in Python and does not contain any C or C++ code. However,
we must install a C compiler because it is needed for the pytricia dependency, which is partly
written in C.

<pre>
$ <b>sudo apt-get install -y build-essential</b>
</pre>

### Install python3-dev

The pytricia dependency also needs the header files for the Python 3 source code:

<pre>
$ <b>sudo apt-get install -y python3-dev</b>
</pre>

### Install git

You need git to clone clone the RIFT-Python repository into the EC2 instance.

The AWS Ubuntu 20.04 AMI comes pre-installed with Git version 2.25.1:

<pre>
$ <b>git --version</b>
git version 2.25.1
</pre>

However, if you need to install git yourself you can do so as follows:

<pre>
$ <b>sudo apt-get install -y git</b>
</pre>

### Install virtualenv

A Python virtual environment is a mechanism to keep all project dependencies together and isolated
from the dependencies of other projects you may be working on to avoid conflicts.

Install virtualenv so that you can create a virtual environment for your project later on in the
installation process:

<pre>
$ <b>sudo apt-get install -y virtualenv</b>
</pre>

### Clone the repository

Clone this rift-python repository from github onto the EC2 instance:

<pre>
$ <b>git clone https://github.com/brunorijsman/rift-python.git</b>
Cloning into 'rift-python'...
remote: Counting objects: 882, done.
remote: Compressing objects: 100% (119/119), done.
remote: Total 882 (delta 121), reused 155 (delta 82), pack-reused 679
Receiving objects: 100% (882/882), 2.03 MiB | 341.00 KiB/s, done.
Resolving deltas: 100% (567/567), done.
</pre>

This will create a directory rift-python with the source code:

<pre>
$ <b>find rift-python</b> 
rift-python
rift-python/tests
rift-python/tests/test_rib_fib.py
rift-python/tests/test_visualize_log.py
rift-python/tests/test_sys_2n_un_l0.py
rift-python/tests/test_sys_2n_l0_l2.py
...
</pre>

### Create Python virtual environment

Go into the newly create rift-python directory and create a new virtual environment named env:

<pre>
$ <b>cd rift-python</b>
$ <b>virtualenv env --python=python3</b>
Already using interpreter /usr/bin/python3
Using base prefix '/usr'
New python executable in /home/ubuntu rift-python/env/bin/python3
Also creating executable in /home/ubuntu rift-python/env/bin/python
Installing setuptools, pkg_resources, pip, wheel...done.
</pre>

### Activate the Python virtual environment

While still in the rift-python directory, activate the newly created Python environment:

<pre>
$ <b>source env/bin/activate</b>
(env) $ 
</pre>

### Use pip to install dependencies

Use pip to install the dependencies. It is important that you have activated
the virtual environment as described in the previous step before you install these dependencies.

<pre>
$ <b>pip install -r requirements-3-8.txt</b> 
Collecting Cerberus==1.2 (from -r requirements.txt (line 1))
Collecting netifaces==0.10.7 (from -r requirements.txt (line 2))
Collecting PyYAML==3.13 (from -r requirements.txt (line 3))
Collecting six==1.11.0 (from -r requirements.txt (line 4))
  Using cached https://files.pythonhosted.org/packages/67/4b/141a581104b1f6397bfa78ac9d43d8ad29a7ca43ea90a2d863fe3056e86a/six-1.11.0-py2.py3-none-any.whl
Collecting sortedcontainers==2.0.4 (from -r requirements.txt (line 5))
  Using cached https://files.pythonhosted.org/packages/cb/53/fe764fc8042e13245b50c4032fb2f857bc1e502aaca83063dcdf6b94d223/sortedcontainers-2.0.4-py2.py3-none-any.whl
Collecting thrift==0.11.0 (from -r requirements.txt (line 6))
Installing collected packages: Cerberus, netifaces, PyYAML, six, sortedcontainers, thrift
Successfully installed Cerberus-1.2 PyYAML-3.13 netifaces-0.10.7 six-1.11.0 sortedcontainers-2.0.4 thrift-0.11.0
</pre>

Note: these installation instructions are for Ubuntu 20.04 which uses Python 3.8 by default. If
you are using Python 3.5, 3.6 or 3.7, use the following command to install the dependencies:

<pre>
$ <b>pip install -r requirements-3-567.txt</b> 
</pre>

## Ubuntu Linux on local VM via Vagrant

Using the Vagrantfile located in this repository, you can create and provision a local virtual machine to run rift-python

### Install local hypervisor that is compatible with Vagrant

For Mac users, the easiest and widely tested choice is [Virtual Box](https://www.virtualbox.org/)

Note: You can also use Vagrant to prepare VM that is not local, but that is not documented here. For more info on using
other providers such as AWS, visit [https://www.vagrantup.com/intro/getting-started/providers.html](https://www.vagrantup.com/intro/getting-started/providers.html)

### Install Vagrant

Download an follow instructions located at [https://www.vagrantup.com/downloads.html](https://www.vagrantup.com/downloads.html)

### Start VM via Vagrant

cd to the top level directory of this repo -- where **Vagrantfile** is located -- and type

```
vagrant up
```

Once VM is provisioned, you can access it using all the well-documented Vagrant commands,
such as

```
vagrant ssh
vagrant halt
vagrant destroy
vagrant help
```
