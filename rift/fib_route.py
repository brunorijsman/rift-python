from packet_common import ip_prefix_str


class FibRoute:
    """
    A route in the routing information base (RIB), also known as forwarding table.
    """

    def __init__(self, prefix, next_hops):
        self.prefix = prefix
        self.next_hops = list(next_hops)

    def __repr__(self):
        next_hops_str = ", ".join([str(next_hop) for next_hop in sorted(self.next_hops)])
        return "%s -> %s" % (ip_prefix_str(self.prefix), next_hops_str)

    @staticmethod
    def cli_summary_headers():
        return [
            "Prefix",
            ["Next-hop", "Interface"],
            ["Next-hop", "Address"],
            ["Next-hop", "Weight"]]

    def cli_summary_attributes(self):
        interfaces = [nh.interface if nh.interface is not None else "" for nh in self.next_hops]
        addresses = [nh.address if nh.address is not None else "" for nh in self.next_hops]
        weights = [nh.weight if nh.weight is not None else "" for nh in self.next_hops]
        return [ip_prefix_str(self.prefix), 
                interfaces,
                addresses,
                weights]

