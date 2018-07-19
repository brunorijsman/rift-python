# Installation Instructions

Installation instructions for:

* [Ubuntu Linux on AWS](ubuntu-linux-on-aws)

## Ubuntu Linux on AWS

Here we describe how to install the Pything RIFT protocol engine on an Amazon Web Services (AWS) Elastic Compute Cloud (EC2) instance running Ubuntu 16.04 LTS.

Note: these instructions should also work for an Ubuntu 16.04 LTS server running on bare metal or in 
a locally hosted virtual machine or in a container.

### Create an EC2 instance

Using the AWS console (or CLI or API) create an EC2 instance:

* Choose Amazon Machine Image (AMI) "Ubuntu Server 16.04 LTS (HVM), SSD Volume Type"
* Choose instance type t2.micro
* Use the default values for all other configuration parameters
* Make sure you download the private key for the EC2 instance

Note: We are using a t2.micro instance type because it is eligible for AWS Free Tier. For large
multi-node topologies you may need a larger instance type.

### Login to Ubuntu

Use user name ubuntu and your private key file to login:

<pre>
$ <b>ssh ubuntu@<i>ec2-instance-ip-address</i> -i ~/.ssh/<i>your-private-key-file</i>.pem</b> 
</pre>

In the above command we assume you are logging in from a platform (such as Linux or macOS) that
supports a standard Telnet client. If you are logging in from Windows you may have to download
a Windows Telnet client such as Putty.

### Update apt-get

Once logged in to the EC2 instance, install the latest security patches on your EC2 instance 
by doing an update:

<pre>
$ <b>sudo apt-get update</b>
</pre>

### Install Python3

The code is written in Python 3 and tested using version 3.5.1. It will not run using Python 2.

Python 3 comes pre-installed on the AWS Ubuntu AMI:

<pre>
$ <b>python3 --version</b>
Python 3.5.2
</pre>

However, if you need to install Python 3 yourself you can do so as follows:

<pre>
$ <b>sudo apt-get install -y python3</b>
</pre>

### Install virtualenv

A Python virtual environment is a mechanism to keep all project dependencies together and isolated from the dependencies of other projects you may be working on to avoid conflicts.

Install virtualenv so that you can create a virtual environment for your project later on in the installation process:

<pre>
$ <b>sudo apt-get install -y virtualenv</b>
</pre>

Verify that virtualenv has been properly installed by asking for the version (the exact version number may be different when you run the command, which is okay):

<pre>
$ <b>virtualenv --version</b>
15.0.1
</pre>

### Install git

You git to clone clone this repository onto the EC2 instance.

Git comes pre-installed on the AWS Ubuntu AMI:

<pre>
$ <b>git --version</b>
git version 2.7.4
</pre>

However, if you need to install git yourself you can do so as follows:

<pre>
$ <b>sudo apt-get install -y git</b>
</pre>

### Clone the repository

Clone this rift-python repository from github onto the EC2 instance:

<pre>
$ <b>$ git clone https://github.com/brunorijsman rift-python.git</b>
Cloning into rift-python'...
remote: Counting objects: 276, done.
remote: Compressing objects: 100% (194/194), done.
remote: Total 276 (delta 172), reused 180 (delta 78), pack-reused 0
Receiving objects: 100% (276/276), 87.53 KiB | 0 bytes/s, done.
Resolving deltas: 100% (172/172), done.
Checking connectivity... done.
</pre>

This will create a directory rift-python with the source code:

<pre>
$ <b>find rift-python</b> 
rift-python/config.py 
rift-python/encoding.thrift 
rift-python/utils.py 
rift-python/cli_listen_handler.py 
rift-python/.gitignore 
rift-python/constants.py
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

### Use pip to install dependecies

Use pip to install the external following modules. It is important that you have activated
the virtual environment as described in the previous step before you install these dependencies.

Install the trift module which is used to encode and decode Thrift messages:

<pre>
(env) $ <b>pip install thrift</b>
</pre>

Install the sortedcontainers module which is used to created Python containers (e.g. dictionaries) that are sorted by key value:

<pre>
(env) $ <b>pip install sortedcontainers</b>
</pre>

Install the netifaces module which provides cross-platform portable code for retrieving information about interfaces and their addresses:

<pre>
(env) $ <b>pip install netifaces</b>
</pre>

Install the pyyaml module which is used to parse YAML files:

<pre>
(env) $ <b>pip install pyyaml</b>
</pre>

Install the cerberus module which is used to validate whether the data stored in a YAML file conforms to a data model (schema):

<pre>
(env) $ <b>pip install cerberus</b>
</pre>
