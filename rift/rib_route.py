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
        # Gather all positive and negative next-hops
        positive_next_hops = []
        negative_next_hops = []
        for rib_next_hop in self.next_hops:
            if rib_next_hop.negative:
                negative_next_hops.append(rib_next_hop)
            else:
                positive_next_hops.append(rib_next_hop)
        # Start with the positive next-hops in the FIB
        fib_next_hops = positive_next_hops
        # We need the parent FIB next hops to (a) potentially compute the complement of the negative
        # next-hops and (b) to determine whether this route is superfluous because it has the exact
        # same FIB next-hops as its parent
        parent_destination = self.destination.parent_destination()
        if parent_destination is None:
            parent_route = None
            parent_fib_next_hops = None
        else:
            parent_route = parent_destination.best_route()
            parent_fib_next_hops = parent_route.compute_fib_next_hops()
        # If (and only if) there is at least one negative next-hop, compute the complementary
        # positive next-hops
        if negative_next_hops:
            if parent_fib_next_hops is None:
                complementary_next_hops = []
            else:
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
        if parent_fib_next_hops is not None:
            if sorted(fib_next_hops) == sorted(parent_fib_next_hops):
                fib_next_hops = None
        # Special case: discard next-hop without a parent is also superfluous
        if parent_fib_next_hops is None and fib_next_hops == []:
            fib_next_hops = None
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
