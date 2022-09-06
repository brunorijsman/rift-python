FROM ubuntu:22.04
RUN apt-get update -y
RUN apt-get install -y python3
RUN apt-get install -y python3-dev
RUN apt-get install -y python3-pip
RUN apt-get install -y build-essential
RUN apt-get install -y virtualenv
RUN apt-get install -y iproute2
RUN apt-get install -y telnet
RUN apt-get install -y iputils-ping
RUN apt-get install -y traceroute
COPY requirements-3-10.txt requirements-3-10.txt
RUN pip3 install -r requirements-3-10.txt
VOLUME /host
