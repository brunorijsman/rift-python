from copy import copy

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

    @staticmethod
    def index_of_nh_with_intf_and_addr(next_hops, interface, address):
        for index, next_hop in enumerate(next_hops):
            if next_hop.interface == interface and next_hop.address == address:
                return index
        return None

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
        if parent_destination is None:
            parent_fib_next_hops = []
        else:
            # Compute the set of positive next-hops that are the complement of the routes set of
            # negative next-hops.
            parent_route = parent_destination.best_route()
            parent_fib_next_hops = parent_route.compute_fib_next_hops()
            complementary_next_hops = copy(parent_fib_next_hops)
            for rib_next_hop in self.next_hops:
                if rib_next_hop.negative:
                    index = self.index_of_nh_with_intf_and_addr(complementary_next_hops,
                                                                rib_next_hop.interface,
                                                                rib_next_hop.address)
                    if index is not None:
                        del complementary_next_hops[index]
            # Add the complementary positive next-hops to the FIB next-hops (avoiding duplicates)
            for complementary_next_hop in complementary_next_hops:
                index = self.index_of_nh_with_intf_and_addr(fib_next_hops,
                                                            complementary_next_hop.interface,
                                                            complementary_next_hop.address)
                if index is None:
                    fib_next_hops.append(complementary_next_hop)
        # If this route ends up with the exact same set of FIB next-hops as its parent route,
        # then we declare this route to be "superfluous" and we don't install it in the FIB.
        # Note: next_hops = [] means this route is a discard route, next_hops = None means this
        # route is a superfluous route.
        if sorted(fib_next_hops) == sorted(parent_fib_next_hops):
            fib_next_hops = None
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
