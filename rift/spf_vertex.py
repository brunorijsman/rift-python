TYPE_NODE = 1
TYPE_PREFIX = 2

def make_node_vertex(system_id, cost):
    return SPFVertex(TYPE_NODE, system_id, None, cost)

def make_prefix_vertex(prefix, cost):
    return SPFVertex(TYPE_PREFIX, None, prefix, cost)

class SPFVertex:

    # TODO: Add support for Non-Equal Cost Multi-Path (NECMP)

    def __init__(self, vertex_type, system_id, prefix, cost):
        # Type of the SPFVertex: TYPE_NODE or TYPE_PREFIX
        self.type = vertex_type
        # System-id of the node for TYPE_NODE, None for TYPE_PREFIX
        self.system_id = system_id
        # Destination prefix for TYPE_PREFIX, None for TYPE_NODE
        self.prefix = prefix
        # Cost of best-known path to this vertex (is always a single cost, even in the case of ECMP)
        self.cost = cost
        # System-ID of node before this vertex (predecessor) on best known path (*)
        # (*) here and below means: contains more than one element in the case of ECMP
        self.predecessors = []
        # (if_name, addr) of direct next-hop from source node towards this vertex (*)
        self.direct_nexthops = []

    def add_predecessor(self, predecessor_system_id):
        self.predecessors.append(predecessor_system_id)

    def add_direct_nexthop(self, direct_nexthop_if_name, direct_nexthop_addr):
        direct_nexthop = (direct_nexthop_if_name, direct_nexthop_addr)
        if direct_nexthop not in self.direct_nexthops:
            self.direct_nexthops.append(direct_nexthop)

    def inherit_direct_nexthops(self, other_spf_vertex):
        for direct_nexthop in other_spf_vertex.direct_nexthops:
            if direct_nexthop not in self.direct_nexthops:
                self.direct_nexthops.append(direct_nexthop)
