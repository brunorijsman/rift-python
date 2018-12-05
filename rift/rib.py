import sortedcontainers

import common.ttypes

ADDRESS_FAMILY_IPV4 = 1
ADDRESS_FAMILY_IPV6 = 2

# For each prefix, there can be up to one route per owner. This is also the order of preference
# for the routes from different owners to the same destination (higher numerical value is more
# preferred)
OWNER_S_SPF = 2
OWNER_N_SPF = 1

class Route:

    def __init__(self, prefix, owner):
        # Avoid common mistake of passing prefix string instead of prefix object
        assert isinstance(prefix, common.ttypes.IPPrefixType)
        self.prefix = prefix
        self.owner = owner

class Table:

    def __init__(self, address_family):
        self.address_family = address_family
        # Sorted dict of _Destination objects indexed by prefix
        self.destinations = sortedcontainers.SortedDict()

    def get_route(self, prefix, owner):
        assert isinstance(prefix, common.ttypes.IPPrefixType)
        if prefix in self.destinations:
            return self.destinations[prefix].get_route(owner)
        else:
            return None

    def put_route(self, route):
        prefix = route.prefix
        if route.prefix in self.destinations:
            destination = self.destinations[prefix]
        else:
            destination = _Destination(prefix)
            self.destinations[prefix] = destination
        destination.put_route(route)

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
                return
            index += 1
