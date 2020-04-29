import common
import constants
import packet_common


class RibRoute:
    """
    An object that represents a prefix route for a Destination in the RIB.
    It keeps track of positive and negative next hops and it also computes the real next hops
    to install in the kernel.
    Attributes of this class are:
        - prefix: prefix associated to this route
        - owner: owner of this route
        - destination: Destination object which contains this route
        - stale: boolean that marks the route as stale
        - positive_next_hops: set of positive next hops for the prefix
        - negative_next_hops: set of negative next hops for the prefix
    """

    def __init__(self, prefix, owner, positive_next_hops, negative_next_hops=None):
        assert isinstance(prefix, common.ttypes.IPPrefixType)
        self.prefix = prefix
        self.owner = owner
        self.destination = None
        self.stale = False

        self.positive_next_hops = set(positive_next_hops)
        self.negative_next_hops = set(negative_next_hops) if negative_next_hops else set()

    @property
    def next_hops(self):
        """
        :return: the computed next hops for the route ready to be installed in the kernel.
        """
        return self._compute_next_hops()

    def _compute_next_hops(self):
        """
        Computes the the real next hops set for this prefix.
        Real next hops set is the set of next hops that can be used to reach this prefix. (the ones
        to be installed in the kernel)
        :return: the set of real next hops
        """
        # The route does not have any negative next hops; there is no disaggregation to be done.
        if not self.negative_next_hops:
            return self.positive_next_hops

        # Get the parent prefix destination object from the RIB
        # If there are no parents for the current prefix, then return the positive next hops set.
        # This only occurs when the prefix is the default (0.0.0.0/0)
        parent_prefix_dest = self.destination.parent_prefix_dest
        if parent_prefix_dest is None:
            return self.positive_next_hops

        # Compute the complementary next hops of the negative next hops.
        complementary_next_hops = parent_prefix_dest.best_route.next_hops - self.negative_next_hops
        return self.positive_next_hops.union(complementary_next_hops)

    def _get_nexthops_sorted(self):
        all_next_hops = []
        for positive_next_hop in self.positive_next_hops:
            all_next_hops.append((positive_next_hop, True))
        for negative_next_hop in self.negative_next_hops:
            all_next_hops.append((negative_next_hop, False))
        all_next_hops.sort()
        return all_next_hops

    def __str__(self):
        all_next_hops = self._get_nexthops_sorted()
        return "%s: %s -> %s" % (constants.owner_str(self.owner),
                                 packet_common.ip_prefix_str(self.prefix),
                                 ", ".join(
                                     map(lambda x: str(x[0]) if x[1] else "~%s" % str(x[0]),
                                         all_next_hops)))

    @staticmethod
    def cli_summary_headers():
        return [
            "Prefix",
            "Owner",
            "Next-hops"]

    def cli_summary_attributes(self):
        return [
            packet_common.ip_prefix_str(self.prefix),
            constants.owner_str(self.owner),
            list(map(lambda x: str(x[0]) if x[1] else "~%s" % str(x[0]),
                     self._get_nexthops_sorted()))
        ]
