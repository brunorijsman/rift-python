import packet_common


class FibRoute:
    """
    A route in the routing information base (RIB), also known as forwarding table.
    """

    def __init__(self, prefix, next_hops):
        self.prefix = prefix
        self.next_hops = next_hops

    def __repr__(self):
        next_hops_str = ", ".join([str(next_hop) for next_hop in sorted(self.next_hops)])
        return "%s -> %s" % (packet_common.ip_prefix_str(self.prefix), next_hops_str)

    def is_discard_route(self):
        return not self.next_hops

    @staticmethod
    def cli_summary_headers():
        return [
            "Prefix",
            ["Next-hop", "Type"],
            ["Next-hop", "Interface"],
            ["Next-hop", "Address"],
            ["Next-hop", "Weight"]]

    def cli_summary_attributes(self):
        if self.is_discard_route():
            return [packet_common.ip_prefix_str(self.prefix),
                    "Discard",
                    "",
                    "",
                    ""]
        nhops = sorted(self.next_hops)
        types = ["Positive" for _ in nhops]
        interfaces = [nh.interface if nh.interface is not None else "" for nh in nhops]
        addresses = [nh.address if nh.address is not None else "" for nh in nhops]
        weights = [nh.weight if nh.weight is not None else "" for nh in nhops]
        return [packet_common.ip_prefix_str(self.prefix),
                types,
                interfaces,
                addresses,
                weights]
