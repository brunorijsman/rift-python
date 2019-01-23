import ipaddress
import socket
import struct
import scheduler

class UdpRxHandler:

    MAXIMUM_MESSAGE_SIZE = 65535

    # TODO: Reorder parameters
    def __init__(self, remote_address, port, receive_function, local_address):
        self._local_address = local_address
        self._remote_address = remote_address
        self._port = port
        self._receive_function = receive_function
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # TODO: SO_REUSEPORT is not portable
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        self.sock.bind((remote_address, port))
        # If remote address is multicast, join the group
        if ipaddress.IPv4Address(remote_address).is_multicast:
            if self._local_address:
                req = struct.pack("=4s4s", socket.inet_aton(remote_address),
                                  socket.inet_aton(self._local_address))
            else:
                req = struct.pack("=4sl", socket.inet_aton(remote_address), socket.INADDR_ANY)
            self.sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, req)
        scheduler.SCHEDULER.register_handler(self, True, False)

    def close(self):
        scheduler.SCHEDULER.unregister_handler(self)
        self.sock.close()

    def rx_fd(self):
        return self.sock.fileno()

    def ready_to_read(self):
        message, from_address_and_port = self.sock.recvfrom(self.MAXIMUM_MESSAGE_SIZE)
        self._receive_function(message, from_address_and_port)

    # TODO: Finish this
    #
    # def create_ipv4_mcast_rx_socket(self, interface_name):
    #     # pylint:disable=no-member
    #     local_address = self.interface_ipv4_address(interface_name)
    #     if local_address is None:
    #         return None
    #     sock = socket.socket(netifaces.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    #     self.enable_addr_and_port_reuse(sock)
    #     sock.setsockopt(socket.IPPROTO_IP, socket.IP_PKTINFO, 1)
    #     sock.bind((IPV4_MULTICAST_ADDR, MULTICAST_PORT))
    #     req = struct.pack("=4s4s", socket.inet_aton(IPV4_MULTICAST_ADDR),
    #                     socket.inet_aton(local_address))
    #     sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, req)
    #     return sock

    # TODO: Finish this
    #
    # def create_ipv6_mcast_rx_socket(self, interface_name):
    #     # pylint:disable=no-member
    #     sock = socket.socket(netifaces.AF_INET6, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    #     self.enable_addr_and_port_reuse(sock)
    #     sock.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_RECVPKTINFO, 1)
    #     sock.bind(("::", MULTICAST_PORT))
    #     index = self.interface_index(interface_name)
    #     req = struct.pack("=16si", socket.inet_pton(netifaces.AF_INET6, IPV6_MULTICAST_ADDR),
    #                       index)
    #     sock.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_ADD_MEMBERSHIP, req)
    #     return sock

    # def receive(sock_info):
    #     # pylint:disable=too-many-locals
    #     (sock, interface_name, interface_index) = sock_info
    #     ancillary_size = socket.CMSG_LEN(MAX_SIZE)
    #     try:
    #         message, ancillary_messages, _msg_flags, source = sock.recvmsg(MAX_SIZE,
    #                         ancillary_size)
    #         message_str = message.decode()
    #     except Exception as exception:
    #         report("exception {} while receiving on {}".format(exception, interface_name))
    #     else:
    #         rx_interface_index = None
    #         for anc in ancillary_messages:
    #             # pylint:disable=no-member
    #             if anc[0] == socket.SOL_IP and anc[1] == socket.IP_PKTINFO:
    #                 packet_info = in_pktinfo.from_buffer_copy(anc[2])
    #                 rx_interface_index = packet_info.ipi_ifindex
    #             elif anc[0] == socket.SOL_IPV6 and anc[1] == socket.IPV6_PKTINFO:
    #                 packet_info = in6_pktinfo.from_buffer_copy(anc[2])
    #                 rx_interface_index = packet_info.ipi6_ifindex
    #         if rx_interface_index and (rx_interface_index != interface_index):
    #             return
    #         report("received {} on {} from {}".format(message_str, interface_name, source))
