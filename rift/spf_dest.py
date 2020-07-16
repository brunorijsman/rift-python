from next_hop import NextHop
from packet_common import ip_prefix_str
from utils import system_id_str

DEST_TYPE_NODE = 1
DEST_TYPE_PREFIX = 2
DEST_TYPE_POS_DISAGG_PREFIX = 3
DEST_TYPE_NEG_DISAGG_PREFIX = 4

def make_node_dest(system_id, name, cost, is_leaf):
    return SPFDest(DEST_TYPE_NODE, system_id, name, None, set(), cost, is_leaf)

def make_prefix_dest(prefix, tags, cost, is_leaf, is_pos_disagg, is_neg_disagg):
    if is_pos_disagg:
        return SPFDest(DEST_TYPE_POS_DISAGG_PREFIX, None, None, prefix, tags, cost, is_leaf)
    elif is_neg_disagg:
        return SPFDest(DEST_TYPE_NEG_DISAGG_PREFIX, None, None, prefix, tags, cost, is_leaf)
    else:
        return SPFDest(DEST_TYPE_PREFIX, None, None, prefix, tags, cost, is_leaf)

class SPFDest:

    # Each possible destination in SPF calculation is represented by an SPFDest object. There are
    # two types of destinations: node destinations and prefix destinations.

    def __init__(self, dest_type, system_id, name, prefix, tags, cost, is_leaf):
        # Type of the SPFDest: DEST_TYPE_xxx
        self.dest_type = dest_type
        # System-id of the node for TYPE_NODE, None for TYPE_PREFIX/DEST_TYPE_POS_DISAGG_PREFIX/
        # DEST_TYPE_NEG_DISAGG_PREFIX
        self.system_id = system_id
        # Name of the node for TYPE_NODE, None for TYPE_PREFIX/DEST_TYPE_POS_DISAGG_PREFIX/
        # DEST_TYPE_NEG_DISAGG_PREFIX
        self.name = name
        # Destination prefix for TYPE_PREFIX/DEST_TYPE_POS_DISAGG_PREFIX/DEST_TYPE_NEG_DISAGG_PREFIX
        # None for TYPE_NODE
        self.prefix = prefix
        # Prefix  tags for TYPE_PREFIX/DEST_TYPE_POS_DISAGG_PREFIX/DEST_TYPE_NEG_DISAGG_PREFIX
        # None for TYPE_NODE
        self.tags = tags
        # Cost of best-known path to this destination (is always a single cost, even in the case of
        # ECMP)
        self.cost = cost
        # Is the advertising node a leaf node?
        self.is_leaf = is_leaf
        # Has the best path to the destination been determined?
        self.best = False
        # System-ID of node before this destination (predecessor) on best known path (*)
        # (*) here and below means: contains more than one element in the case of ECMP
        self.predecessors = []
        # (if_name, addr) of direct next-hop from source node towards this destination (*)
        self.ipv4_next_hops = []
        self.ipv6_next_hops = []
        # This is a prefix that needs to be positively disaggregated
        self.positively_disaggregate = (dest_type == DEST_TYPE_POS_DISAGG_PREFIX)
        # This is a prefix that needs to be negatively disaggregated
        self.negatively_disaggregate = (dest_type == DEST_TYPE_NEG_DISAGG_PREFIX)

    def key(self):
        if self.dest_type == DEST_TYPE_NODE:
            return self.system_id
        else:
            assert self.dest_type in [DEST_TYPE_PREFIX, DEST_TYPE_POS_DISAGG_PREFIX,
                                      DEST_TYPE_NEG_DISAGG_PREFIX]
            return self.prefix

    def __eq__(self, other):
        return (self.dest_type, self.key()) == (other.dest_type, other.key())

    def __lt__(self, other):
        return (self.dest_type, self.key()) < (other.dest_type, other.key())

    def is_node(self):
        return self.dest_type == DEST_TYPE_NODE

    def add_predecessor(self, predecessor_system_id):
        self.predecessors.append(predecessor_system_id)

    def add_ipv4_next_hop(self, next_hop):
        if (next_hop is not None) and (next_hop not in self.ipv4_next_hops):
            self.ipv4_next_hops.append(next_hop)

    def add_ipv6_next_hop(self, next_hop):
        if (next_hop is not None) and (next_hop not in self.ipv6_next_hops):
            self.ipv6_next_hops.append(next_hop)

    def inherit_next_hops(self, other_spf_destination, negative):
        for next_hop in other_spf_destination.ipv4_next_hops:
            if negative != next_hop.negative:
                next_hop = NextHop(negative, next_hop.interface, next_hop.address, next_hop.weight)
            if next_hop not in self.ipv4_next_hops:
                self.ipv4_next_hops.append(next_hop)
        for next_hop in other_spf_destination.ipv6_next_hops:
            if negative != next_hop.negative:
                next_hop = NextHop(negative, next_hop.interface, next_hop.address, next_hop.weight)
            if next_hop not in self.ipv6_next_hops:
                self.ipv6_next_hops.append(next_hop)

    def inherit_tags(self, other_spf_destination):
        if (self.tags is None) and (other_spf_destination.tags is None):
            return
        if self.tags is None:
            self.tags = set()
        self.tags = self.tags.union(other_spf_destination.tags)

    @staticmethod
    def cli_summary_headers():
        return [
            "Destination",
            "Cost",
            "Is Leaf",
            ["Predecessor", "System IDs"],
            ["Tags"],
            "Disaggregate",
            "IPv4 Next-hops",
            "IPv6 Next-hops"
        ]

    def cli_summary_attributes(self):
        if self.dest_type == DEST_TYPE_NODE:
            destination_str = system_id_str(self.system_id)
            if self.name:
                destination_str += " (" + self.name + ")"
        elif self.dest_type == DEST_TYPE_PREFIX:
            destination_str = ip_prefix_str(self.prefix)
        elif self.dest_type == DEST_TYPE_POS_DISAGG_PREFIX:
            destination_str = ip_prefix_str(self.prefix) + " (Pos-Disagg)"
        elif self.dest_type == DEST_TYPE_NEG_DISAGG_PREFIX:
            destination_str = ip_prefix_str(self.prefix) + " (Neg-Disagg)"
        else:
            assert False
        if self.tags:
            tags_str = list(self.tags)
        else:
            tags_str = ""
        if self.positively_disaggregate:
            disaggregate_str = 'Positive'
        elif self.negatively_disaggregate:
            disaggregate_str = 'Negative'
        else:
            disaggregate_str = ''
        return [
            destination_str,
            self.cost,
            self.is_leaf,
            sorted(self.predecessors),
            tags_str,
            disaggregate_str,
            [str(next_hop) for next_hop in sorted(self.ipv4_next_hops)],
            [str(next_hop) for next_hop in sorted(self.ipv6_next_hops)]
        ]
