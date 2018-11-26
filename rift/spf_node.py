class SPFNode:

    # TODO: Add support for Non-Equal Cost Multi-Path (NECMP)

    def __init__(self, destination, cost):
        # System-id of the destination
        self.destination = destination
        # Cost of best-known path to this node (is always a single cost, even in the case of ECMP)
        self.cost = cost
        # System-ID of node before this node (predecessor) on best known path (*)
        # (*) here and below means: contains more than one element in the case of ECMP
        self.predecessors = []
        # (if_name, addr) of direct next-hop from source node towards this node (*)
        self.direct_nexthops = []

    def add_predecessor(self, predecessor_system_id):
        self.predecessors.append(predecessor_system_id)

    def add_direct_next_hop(self, direct_next_hop_if, direct_next_hop_addr):
        direct_next_hop = (direct_next_hop_if, direct_next_hop_addr)
        if direct_next_hop not in self.direct_nexthops:
            self.direct_nexthops.append(direct_next_hop)

    def inherit_direct_next_hops(self, other_spf_node):
        for direct_next_hop in other_spf_node.direct_nexthops:
            if direct_next_hop not in self.direct_nexthops:
                self.direct_nexthops.append(direct_next_hop)

    # TODO: get rid of this
    def __repr__(self):
        return (
            "SPFInfo(" +
            "destination={}, ".format(self.destination) +
            "cost={}, ".format(self.cost) +
            "predecessors={}, ".format(self.predecessors) +
            "direct_nexthops={})".format(self.direct_nexthops))
