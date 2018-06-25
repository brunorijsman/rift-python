import socket
import struct
import time

multicast_address = '224.0.1.200'
multicast_port = 10000

# Create the datagram socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
print('Created datagram socket...')

sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

sock.bind((multicast_address, multicast_port))

req = struct.pack("4sl", socket.inet_aton(multicast_address), socket.INADDR_ANY)
sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, req)

while True:
  print(sock.recv(10240))
