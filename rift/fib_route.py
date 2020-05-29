import packet_common


class FibRoute:
    def __init__(self, prefix, next_hops):
        self.prefix = prefix
        self.next_hops = list(next_hops)

    def __str__(self):
        sorted_next_hops = sorted([str(next_hop) for next_hop in self.next_hops])
        return "%s -> %s" % (packet_common.ip_prefix_str(self.prefix), ", ".join(sorted_next_hops))

    def __repr__(self):
        return str(self)

    @staticmethod
    def cli_summary_headers():
        return [
            "Prefix",
            "Next-hops"]

    def cli_summary_attributes(self):
        all_next_hops = self.next_hops.sorted()
        return [
            packet_common.ip_prefix_str(self.prefix),
            [str(next_hop) for next_hop in all_next_hops]
        ]
