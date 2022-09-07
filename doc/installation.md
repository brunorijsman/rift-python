# Supported platforms

As the name suggests, RIFT-Python has been implemented in Python 3. It has been tested the following
versions of CPython:

- Python 3.10

RIFT-Python cannot run on any version of Python 2.

RIFT-Python has been tested on the following operating systems:

- Ubuntu 22.04 LTS (Jammy Jellyfish)
- macOS 10.15 (Catalina)

It should be possible to run RIFT-Python on other versions of Linux or macOS or even on other platforms
(such as Windows) with little or no porting, but we have not tested that. Most code is very
portable, except for the code that deals with sending multicast and IPv6 UDP packets over sockets,
which is infuriatingly platform dependent in subtle ways.

# Installation Instructions

Installation instructions for:

- [Ubuntu Linux on AWS](#ubuntu-linux-on-aws)
- [Ubuntu Linux on local VM via Vagrant](#ubuntu-linux-on-local-vm-via-vagrant)

## Ubuntu Linux on AWS

Here we describe how to install RIFT Python on an Amazon Web Services (AWS)
Elastic Compute Cloud (EC2) instance running Ubuntu 22.04 LTS (Jammy Jellyfish).

These instructions should also work for an Ubuntu 22.04 LTS server running on bare metal or in
a locally hosted virtual machine or in a container.

### Create an EC2 instance

Using the AWS console (or CLI or API) create an EC2 instance:

- Choose Amazon Machine Image (AMI) "Ubuntu Server 22.04 LTS (HVM), SSD Volume Type, 64-bit (x86)"
- Choose instance type t2.micro (or t3.micro if t2.micro is not available in the region)
- Use the default values for all other configuration parameters
- Make sure you download the private key for the EC2 instance

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

The AWS Ubuntu 22.04 AMI comes pre-installed with Python 3.10:

<pre>
$ <b>python3 --version</b>
Python 3.10.4
</pre>

However, if you need to install Python 3 yourself you can do so as follows:

<pre>
$ <b>sudo apt-get install -y python3</b>
</pre>

### Give Python3 programs the capability to modify the route table

By default, user programs (including Python programs) are not allowed to modify the route table.
Give all Python 3.10 programs the capability to modify the route table (this is a heavy-handed
approach that is not suitable for production):

<pre>
$ <b>sudo setcap cap_net_admin+ep /usr/bin/python3.10</b>
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

The AWS Ubuntu 22.04 AMI comes pre-installed with Git version 2.34.1:

<pre>
$ <b>git --version</b>
git version 2.34.1
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
created virtual environment CPython3.10.4.final.0-64 in 402ms
  creator CPython3Posix(dest=/home/ubuntu/rift-python/env, clear=False, no_vcs_ignore=False, global=False)
  seeder FromAppData(download=False, pip=bundle, setuptools=bundle, wheel=bundle, via=copy, app_data_dir=/home/ubuntu/.local/share/virtualenv)
    added seed packages: pip==22.0.2, setuptools==59.6.0, wheel==0.37.1
  activators BashActivator,CShellActivator,FishActivator,NushellActivator,PowerShellActivator,PythonActivator
</pre>

### Activate the Python virtual environment

While still in the rift-python directory, activate the newly created Python environment:

<pre>
$ <b>source env/bin/activate</b>
(env) $ 
</pre>

### Use pip to install dependencies

Use pip to install the dependencies for Python 3.10 running on Ubuntu 22.04.
It is important that you have activated the virtual environment as described in the previous step
before you install these dependencies.

<pre>
$ <b>pip install -r requirements-3-10.txt</b> 
...
</pre>

## Ubuntu Linux on local VM via Vagrant

Using the Vagrantfile located in this repository, you can create and provision a local virtual machine to run rift-python

### Install local hypervisor that is compatible with Vagrant

For Mac users, the easiest and widely tested choice is [Virtual Box](https://www.virtualbox.org/)

Note: You can also use Vagrant to prepare VM that is not local, but that is not documented here. For more info on using
other providers such as AWS, visit [https://www.vagrantup.com/intro/getting-started/providers.html](https://www.vagrantup.com/intro/getting-started/providers.html)

### Install Vagrant

Download and follow instructions located at [https://www.vagrantup.com/downloads.html](https://www.vagrantup.com/downloads.html)

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
