FROM ubuntu:latest
RUN apt-get update
RUN apt-get install -y python3
RUN apt-get install -y python3-pip
RUN apt-get install -y iproute2
RUN apt-get install -y telnet
COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt
VOLUME /host
