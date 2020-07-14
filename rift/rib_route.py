from constants import owner_str
from packet_common import ip_prefix_str


class RibRoute:
    """
    A route in the routing information base (RIB).
    """

    def __init__(self, prefix, owner, next_hops):
        self.prefix = prefix
        self.owner = owner
        self.destination = None   # The destination is set in Destination.put_route ###@@@
        self.stale = False
        self.next_hops = next_hops

    def compute_fib_next_hops(self):
        fib_next_hops = []
        for rib_next_hop in self.next_hops:
            if rib_next_hop.negative:
                # Negative RIB next-hop; compute complementary positive next-hops for FIB
                parent_destination = self.destination.parent_destination()
                if parent_destination is None:
                    continue
                parent_route = parent_destination.best_route()
                parent_fib_next_hops = parent_route.compute_fib_next_hops()
                for parent_fib_next_hop in parent_fib_next_hops:
                    if (parent_fib_next_hop.interface != rib_next_hop.interface or
                            parent_fib_next_hop.address != rib_next_hop.address):
                        fib_next_hops.append(parent_fib_next_hop)
            else:
                # Positive RIB next-hop; keep as-is in FIB
                fib_next_hops.append(rib_next_hop)
        ###@@@ TODO: This is where we should do the bandwidth adjustment for the weights
        return fib_next_hops

    def __repr__(self):
        next_hops_str = ", ".join([str(next_hop) for next_hop in sorted(self.next_hops)])
        return "%s: %s -> %s" % (owner_str(self.owner), ip_prefix_str(self.prefix), next_hops_str)

    @staticmethod
    def cli_summary_headers():
        return [
            "Prefix",
            "Owner",
            ["Next-hop", "Negative"],
            ["Next-hop", "Interface"],
            ["Next-hop", "Address"],
            ["Next-hop", "Weight"]]

    def cli_summary_attributes(self):
        negatives = ["Negative" if nh.negative else "" for nh in self.next_hops]
        interfaces = [nh.interface if nh.interface is not None else "" for nh in self.next_hops]
        addresses = [nh.address if nh.address is not None else "" for nh in self.next_hops]
        weights = [nh.weight if nh.weight is not None else "" for nh in self.next_hops]
        return [ip_prefix_str(self.prefix),
                owner_str(self.owner),
                negatives,
                interfaces,
                addresses,
                weights]
