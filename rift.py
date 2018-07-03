import os
from multicast_send_handler import MulticastSendHandler
from multicast_receive_handler import MulticastReceiveHandler
from timer import Timer
from socket_scheduler import socket_scheduler

multicast_address = '224.0.1.200'
port = 10000

send_interval_secs = 5.0

message = 'Message sent by PID ' + str(os.getpid())

def receive_message(message):
    print("Receive {}".format(message))

def send_message():
    multicast_send_handler.send_message(message)
    print("Sent {}".format(message))

multicast_send_handler = MulticastSendHandler(multicast_address, port)

multicast_receive_handler = MulticastReceiveHandler(multicast_address, port, receive_message)

send_timer = Timer(send_interval_secs, send_message)

socket_scheduler.run()