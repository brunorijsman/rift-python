# TODO: Add hierarchical configuration with inheritance

class Config:

    DEFAULT_LIE_IPV4_MULTICAST_ADDRESS = '224.0.0.120'
    DEFAULT_LIE_IPV6_MULTICAST_ADDRESS = 'FF02::0078'     # TODO: Add IPv6 support
    DEFAULT_LIE_DESTINATION_PORT = 10000    # TODO: Change to 911 (needs root privs)
    DEFAULT_LIE_SEND_INTERVAL_SECS = 1.0    # TODO: What does the draft say?

    def __init__(self):
        self._lie_ipv4_multicast_address = self.DEFAULT_LIE_IPV4_MULTICAST_ADDRESS
        self._lie_ipv6_multicast_address = self.DEFAULT_LIE_IPV6_MULTICAST_ADDRESS
        self._lie_destination_port = self.DEFAULT_LIE_DESTINATION_PORT
        self._lie_send_interval_secs = self.DEFAULT_LIE_SEND_INTERVAL_SECS

    @property
    def lie_ipv4_multicast_address(self):
        return self._lie_ipv4_multicast_address

    @property
    def lie_ipv6_multicast_address(self):
        return self._lie_ipv6_multicast_address

    @property
    def lie_destination_port(self):
        return self._lie_destination_port

    @property
    def lie_send_interval_secs(self):
        return self._lie_send_interval_secs
