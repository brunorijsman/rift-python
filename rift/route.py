import common
import constants
import packet_common

class Route:

    def __init__(self, prefix, owner, next_hops):
        assert isinstance(prefix, common.ttypes.IPPrefixType)
        self.prefix = prefix
        self.owner = owner
        self.next_hops = next_hops
        self.stale = False

    def __str__(self):
        return ("route to " + packet_common.ip_prefix_str(self.prefix) +
                " via " + ", ".join(str(nhop) for nhop in self.next_hops) +
                " owned by " + constants.owner_str(self.owner))

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
            [str(next_hop) for next_hop in sorted(self.next_hops)]]
