import socket
import struct
import time
import os
import select
import datetime

multicast_address = '224.0.1.200'
multicast_port = 10000

interface_address = '10.65.13.221'

send_interval_secs = 5.0

message = 'Message sent by PID ' + str(os.getpid())

def create_multicast_send_socket ():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    ttl = struct.pack('b', 1)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl)
    loop = struct.pack('b', 0)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_LOOP, loop)
    return sock

def create_multicast_receive_socket ():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((multicast_address, multicast_port))
    req = struct.pack("4sl", socket.inet_aton(multicast_address), socket.INADDR_ANY)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, req)
    return sock

def send_message (sock):
    multicast_group = (multicast_address, multicast_port)
    sock.sendto(message.encode(), multicast_group)
    print("Send {}".format(message))

def receive_message (sock):
    message = sock.recv(10240)
    print("Receive {}".format(message))

tx_sock = create_multicast_send_socket()
rx_sock = create_multicast_receive_socket()

time_until_next_send = send_interval_secs

while True:

    before_time = datetime.datetime.now()
    rx_ready, _, _ = select.select([rx_sock], [], [], time_until_next_send)
    after_time = datetime.datetime.now()
    elapsed_sec = (after_time - before_time).total_seconds()

    time_until_next_send -= elapsed_sec
    if time_until_next_send <= 0.0:
        send_message(tx_sock)
        time_until_next_send = send_interval_secs

    for s in rx_ready:
        receive_message(s)

