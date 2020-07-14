from ipaddress import IPv4Address, IPv6Address

class NextHop:
    """
    A single next-hop for a route in the routing table (RIB) or forwarding table (FIB).
    """

    def __init__(self, negative, interface, address, weight):
        if negative:
            ###@@@ Remove these defensive asserts once done
            # Negative next-hops must not have a weight
            assert weight is None
        self.negative = negative
        self.interface = interface      # May be None, meaning discard route
        self.address = address          # May be None, for unnumbered interfaces
        self.weight = weight            # May be None, only used for NECMP

    def __str__(self):
        parts = []
        if self.negative:
            parts.append("Negative")
        if self.interface is not None:
            parts.append(self.interface)
        if self.address is not None:
            parts.append(str(self.address))
        if self.weight is not None:
            parts.append("({})".format(self.weight))
        return " ".join(parts)

    ###@@@ Need this?
    # def __eq__(self, other):
    #     if self.negative != other.negative:
    #         return False
    #     if self.interface != other.interface:
    #         return False
    #     if self.address != other.address:
    #         return False
    #     if self.weight != other.weight:
    #         return False
    #     return True

    def __lt__(self, other):
        # Sort by interface name (which may be None)
        if (self.interface is None) and (other.interface is not None):
            return True
        if (self.interface is not None) and (other.interface is None):
            return False
        if self.interface < other.interface:
            return True
        if self.interface > other.interface:
            return False
        # Sort by address (which may be None and keeping in mind they may be different families)
        if (self.address is None) and (other.address is not None):
            return True
        if (self.address is not None) and (other.address is None):
            return False
        if isinstance(self.address, IPv4Address) and isinstance(other.address, IPv6Address):
            return True
        if isinstance(self.address, IPv6Address) and isinstance(other.address, IPv4Address):
            return False
        if self.address < other.address:
            return True
        if self.address > other.address:
            return True
        # Sort by weight (which may be None)
        if (self.weight is None) and (other.weight is not None):
            return True
        if (self.weight is not None) and (other.weight is None):
            return False
        return self.weight < other.weight

###@@@ need this?
    # def __hash__(self):
    #     return hash((self.negative, self.interface, self.address, self.weight))
