import packet_common
import utils

DEST_TYPE_NODE = 1
DEST_TYPE_PREFIX = 2

def make_node_destination(system_id, name, cost):
    return SPFDest(DEST_TYPE_NODE, system_id, name, None, cost)

def make_prefix_destintation(prefix, cost):
    return SPFDest(DEST_TYPE_PREFIX, None, None, prefix, cost)

class SPFDest:

    # Each possible destination in SPF calculation is represented by an SPFDest object. There are
    # two types of destinations: node destinations and prefix destinations.

    # TODO: Add support for Non-Equal Cost Multi-Path (NECMP)

    def __init__(self, dest_type, system_id, name, prefix, cost):
        # Type of the SPFDest: DEST_TYPE_NODE or DEST_TYPE_PREFIX
        self.dest_type = dest_type
        # System-id of the node for TYPE_NODE, None for TYPE_PREFIX
        self.system_id = system_id
        # Name of the node for TYPE_NODE, None for TYPE_PREFIX
        self.name = name
        # Destination prefix for TYPE_PREFIX, None for TYPE_NODE
        self.prefix = prefix
        # Cost of best-known path to this destination (is always a single cost, even in the case of
        # ECMP)
        self.cost = cost
        # Has the best path to the destination been determined?
        self.best = False
        # System-ID of node before this destination (predecessor) on best known path (*)
        # (*) here and below means: contains more than one element in the case of ECMP
        self.predecessors = []
        # (if_name, addr) of direct next-hop from source node towards this destination (*)
        self.direct_nexthops = []

    def key(self):
        if self.dest_type == DEST_TYPE_NODE:
            return self.system_id
        else:
            assert self.dest_type == DEST_TYPE_PREFIX
            return self.prefix

    def __eq__(self, other):
        return (self.dest_type, self.key()) == (other.dest_type, other.key())

    def __lt__(self, other):
        return (self.dest_type, self.key()) < (other.dest_type, other.key())

    def is_node(self):
        return self.dest_type == DEST_TYPE_NODE

    def add_predecessor(self, predecessor_system_id):
        self.predecessors.append(predecessor_system_id)

    def add_direct_nexthop(self, direct_nexthop_if_name, direct_nexthop_addr):
        direct_nexthop = (direct_nexthop_if_name, direct_nexthop_addr)
        if direct_nexthop not in self.direct_nexthops:
            self.direct_nexthops.append(direct_nexthop)

    def inherit_direct_nexthops(self, other_spf_destination):
        for direct_nexthop in other_spf_destination.direct_nexthops:
            if direct_nexthop not in self.direct_nexthops:
                self.direct_nexthops.append(direct_nexthop)

    @staticmethod
    def cli_summary_headers():
        return [
            ["Destination"],
            "Cost",
            ["Predecessor", "System IDs"],
            ["Direct", "Nexthops"]]

    def cli_summary_attributes(self, destination):
        if self.dest_type == DEST_TYPE_NODE:
            destination_str = utils.system_id_str(destination.system_id)
            if self.name:
                destination_str += " (" + self.name + ")"
        else:
            destination_str = packet_common.ip_prefix_str(self.prefix)
        return [
            destination_str,
            destination.cost,
            sorted(destination.predecessors),
            [self.nexthop_str(nexthop) for nexthop in sorted(destination.direct_nexthops)]
        ]

    @staticmethod
    def nexthop_str(nexthop):
        (nexthop_intf_name, nexthop_addr) = nexthop
        result_str = ""
        if nexthop_intf_name is not None:
            result_str += nexthop_intf_name + " "
        if nexthop_addr is not None:
            result_str += str(nexthop_addr)
        return result_str
