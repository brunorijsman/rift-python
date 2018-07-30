# Installation Instructions

Installation instructions for:

* [Ubuntu Linux on AWS](#ubuntu-linux-on-aws)
* [Ubuntu Linux on local VM via Vagrant](#ubuntu-linux-on-local-vm-via-vagrant)

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
rift-python/topology
rift-python/topology/one.yaml
rift-python/topology/two_by_two_by_two.yaml
rift-python/topology/two_by_two_by_two_ztp.yaml
rift-python/topology/two.yaml
rift-python/LICENSE
rift-python/requirements.txt
rift-python/README.md
rift-python/rift-python
rift-python/rift-python/neighbor.py
rift-python/rift-python/offer.py
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

Use pip to install the dependencies. It is important that you have activated
the virtual environment as described in the previous step before you install these dependencies.

<pre>
$ <b>pip install -r requirements.txt</b> 
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

For those interested, here is the list of dependency modules:

| Module | Purpose |
| --- | --- |
| trift | Encode and decode Thrift messages |
| sortedcontainers | Python containers (e.g. dictionaries) that are sorted by key |
| netifaces | Cross-platform portable code for retrieving information about interfaces and their addresses |
| pyyaml | Parse Yet Another Markup Language (YAML) files |
| cerberus | validate whether the data stored in a YAML file conforms to a data model (schema) |

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
