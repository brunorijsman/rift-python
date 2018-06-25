import socket
import struct
import time

multicast_address = '224.0.1.200'
multicast_port = 10000

# Create the datagram socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
print('Created datagram socket...')

# Set TTL to 1
ttl = struct.pack('b', 1)
sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl)
print('Set TTL to 1...')

while True:

    # Send multicast message
    message = 'very important data'.encode()
    multicast_group = (multicast_address, multicast_port)
    bytes_sent = sock.sendto(message, multicast_group)
    print('Sent multicast message: {} ({} bytes)'.format(message, bytes_sent) )

    # Delay
    time.sleep(1)



