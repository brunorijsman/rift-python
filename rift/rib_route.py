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
        # First take all the positive next-hops of this route
        for rib_next_hop in self.next_hops:
            if not rib_next_hop.negative:
                if rib_next_hop not in fib_next_hops:
                    fib_next_hops.append(rib_next_hop)
        # Then add the complement of all negative next-hops of this route = parent FIB route
        # next-hops minus this RIB route negative next-hops.
        parent_destination = self.destination.parent_destination()
        if parent_destination is not None:
            parent_route = parent_destination.best_route()
            complementary_next_hops = parent_route.compute_fib_next_hops()
            for rib_next_hop in self.next_hops:
                if rib_next_hop.negative:
                    for index, complementary_next_hop in enumerate(complementary_next_hops):
                        if (complementary_next_hop.interface == rib_next_hop.interface and
                                complementary_next_hop.address == rib_next_hop.address):
                            del complementary_next_hops[index]
                            break
            fib_next_hops.extend(complementary_next_hops)
        ###@@@ TODO: This is where we should do the bandwidth adjustment for the weights
        return fib_next_hops

    def __repr__(self):
        next_hops_str = ", ".join([str(next_hop) for next_hop in sorted(self.next_hops)])
        return "%s: %s -> %s" % (owner_str(self.owner), ip_prefix_str(self.prefix), next_hops_str)

    def is_discard_route(self):
        return not self.next_hops

    @staticmethod
    def cli_summary_headers():
        return [
            "Prefix",
            "Owner",
            ["Next-hop", "Type"],
            ["Next-hop", "Interface"],
            ["Next-hop", "Address"],
            ["Next-hop", "Weight"]]

    def cli_summary_attributes(self):
        if self.is_discard_route():
            return [ip_prefix_str(self.prefix),
                    owner_str(self.owner),
                    "Discard",
                    "",
                    "",
                    ""]
        types = ["Negative" if nh.negative else "Positive" for nh in self.next_hops]
        interfaces = [nh.interface if nh.interface is not None else "" for nh in self.next_hops]
        addresses = [nh.address if nh.address is not None else "" for nh in self.next_hops]
        weights = [nh.weight if nh.weight is not None else "" for nh in self.next_hops]
        return [ip_prefix_str(self.prefix),
                owner_str(self.owner),
                types,
                interfaces,
                addresses,
                weights]
