# RIFT

This repository contains an implementation of the Routing In Fat Trees (RIFT) protocol specificied in Internet Draft (ID)
[draft-draft-rift-02](https://tools.ietf.org/html/draft-ietf-rift-rift-02)

The code is currently still a work in progress. Only the Link Information Element (LIE) Finite State Machine (FSM) is complete.

It will be used for interoperability testing in the hackathon at the Internet Engineering Task Force (IETF) meeting number 102 in Montreal (July 2018).

# Installation instructions

## Linux (Ubuntu Server 16.04 LTS)

I am using an Amazon Web Services (AWS) Elastic Compute Cloud (EC2) t2.micro instance with Amazon Machine Image (AMI) "Ubuntu Server 16.04 LTS (HVM), SSD Volume Type" (ami-ba602bc2), which is free-tier eligible.

### Login to Ubuntu

If you are using an Ubuntu instance on AWS, use user name ubuntu and your private key file to login (the following command assumes you are logging in from Linux or Mac OS X)

<pre>
$ <b>ssh ubuntu@<i>ec2-instance-ip-address</i> -i ~/.ssh/<i>your-private-key-file</i>.pem</b> 
</pre>

### Update apt-get

Install the latest security patches on your EC2 instance by doing an update:

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

Verify that virtualenv has been properly installed by asking for the version:

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

However, if you need to install Python 3 yourself you can do so as follows:

<pre>
$ <b>sudo apt-get install -y git</b>
</pre>

### Clone the repository

Clone this rift-fsm repository from github onto the EC2 instance:

<pre>
$ <b>$ git clone https://github.com/brunorijsman/rift-fsm.git</b>
Cloning into 'rift-fsm'...
remote: Counting objects: 276, done.
remote: Compressing objects: 100% (194/194), done.
remote: Total 276 (delta 172), reused 180 (delta 78), pack-reused 0
Receiving objects: 100% (276/276), 87.53 KiB | 0 bytes/s, done.
Resolving deltas: 100% (172/172), done.
Checking connectivity... done.
</pre>

This will create a directory rift-fsm with the source code:

<pre>
$ <b>find rift-fsm</b>
rift-fsm
rift-fsm/config.py
rift-fsm/encoding.thrift
rift-fsm/utils.py
rift-fsm/cli_listen_handler.py
rift-fsm/.gitignore
rift-fsm/constants.py
...
</pre>

### Create Python virtual environment

Go into the newly create rift-fsm directory and create a new virtual environment named env:

<pre>
$ <b>cd rift-fsm</b>
$ <b>virtualenv env --python=python3</b>
Already using interpreter /usr/bin/python3
Using base prefix '/usr'
New python executable in /home/ubuntu/rift-fsm/env/bin/python3
Also creating executable in /home/ubuntu/rift-fsm/env/bin/python
Installing setuptools, pkg_resources, pip, wheel...done.
</pre>

### Activate the Python virtual environment