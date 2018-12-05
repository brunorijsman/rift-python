import sortedcontainers

import common.ttypes

ADDRESS_FAMILY_IPV4 = 1
ADDRESS_FAMILY_IPV6 = 2

# For each prefix, there can be up to one route per owner. This is also the order of preference
# for the routes from different owners to the same destination (higher numerical value is more
# preferred)
OWNER_S_SPF = 2
OWNER_N_SPF = 1

def assert_prefix_address_family(prefix, address_family):
    assert isinstance(prefix, common.ttypes.IPPrefixType)
    if address_family == ADDRESS_FAMILY_IPV4:
        assert prefix.ipv4prefix is not None
        assert prefix.ipv6prefix is None
    elif address_family == ADDRESS_FAMILY_IPV6:
        assert prefix.ipv4prefix is None
        assert prefix.ipv6prefix is not None
    else:
        assert False

class Route:

    def __init__(self, prefix, owner):
        assert isinstance(prefix, common.ttypes.IPPrefixType)
        self.prefix = prefix
        self.owner = owner

class Table:

    def __init__(self, address_family):
        self.address_family = address_family
        # Sorted dict of _Destination objects indexed by prefix
        self.destinations = sortedcontainers.SortedDict()

    def get_route(self, prefix, owner):
        assert_prefix_address_family(prefix, self.address_family)
        if prefix in self.destinations:
            return self.destinations[prefix].get_route(owner)
        else:
            return None

    def put_route(self, route):
        assert_prefix_address_family(route.prefix, self.address_family)
        prefix = route.prefix
        if route.prefix in self.destinations:
            destination = self.destinations[prefix]
        else:
            destination = _Destination(prefix)
            self.destinations[prefix] = destination
        destination.put_route(route)

    def del_route(self, prefix, owner):
        # Returns True if the route was present in the table and False if not.
        assert_prefix_address_family(prefix, self.address_family)
        if prefix in self.destinations:
            return self.destinations[prefix].del_route(owner)
        else:
            return False

class _Destination:

    def __init__(self, prefix):
        self.prefix = prefix
        # List of Route objects, in decreasing order or owner (= in decreasing order of preference)
        # For a given owner, at most one route is allowed to be in the list
        self.routes = []

    def get_route(self, owner):
        for route in self.routes:
            if route.owner == owner:
                return route
        return None

    def put_route(self, new_route):
        self.del_route(new_route.owner)
        index = 0
        for existing_route in self.routes:
            assert new_route.owner != existing_route.owner
            if existing_route.owner < new_route.owner:
                self.routes.insert(index, new_route)
                return
            index += 1
        self.routes.append(new_route)

    def del_route(self, owner):
        index = 0
        for route in self.routes:
            if route.owner == owner:
                del self.routes[index]
                return True
            index += 1
        return False
