import sortedcontainers

import common.ttypes
import packet_common
import table

ADDRESS_FAMILY_IPV4 = 1
ADDRESS_FAMILY_IPV6 = 2

# pylint:disable=inconsistent-return-statements
def address_family_str(address_family):
    if address_family == ADDRESS_FAMILY_IPV4:
        return "IPv4"
    elif address_family == ADDRESS_FAMILY_IPV6:
        return "IPv6"
    else:
        assert False

# For each prefix, there can be up to one route per owner. This is also the order of preference
# for the routes from different owners to the same destination (higher numerical value is more
# preferred)
OWNER_S_SPF = 2
OWNER_N_SPF = 1

def owner_str(owner):
    if owner == OWNER_S_SPF:
        return "South SPF"
    elif owner == OWNER_N_SPF:
        return "North SPF"
    else:
        assert False

def nexthop_str(nexthop):
    (nexthop_intf_name, nexthop_addr) = nexthop
    result_str = ""
    if nexthop_intf_name is not None:
        result_str += nexthop_intf_name + " "
    if nexthop_addr is not None:
        result_str += str(nexthop_addr)
    return result_str

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

    def __init__(self, prefix, owner, nexthops):
        assert isinstance(prefix, common.ttypes.IPPrefixType)
        self.prefix = prefix
        self.owner = owner
        self.nexthops = nexthops
        self.stale = False

    @staticmethod
    def cli_summary_headers():
        return [
            "Prefix",
            "Owner",
            "Nexthops"]

    def cli_summary_attributes(self):
        return [
            packet_common.ip_prefix_str(self.prefix),
            owner_str(self.owner),
            [nexthop_str(nexthop) for nexthop in sorted(self.nexthops)]]

class RouteTable:

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
        route.stale = False
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
            destination = self.destinations[prefix]
            deleted = destination.del_route(owner)
            if destination.routes == []:
                del self.destinations[prefix]
            return deleted
        else:
            return False

    def all_routes(self):
        for destination in self.destinations.values():
            for route in destination.routes:
                yield route

    def cli_table(self):
        tab = table.Table()
        tab.add_row(Route.cli_summary_headers())
        for route in self.all_routes():
            tab.add_row(route.cli_summary_attributes())
        return tab

    def mark_owner_routes_stale(self, owner):
        # Mark all routes of a given owner as stale. Returns number of routes marked.
        # A possible more efficient implementation is to have a list of routes for each owner.
        # For now, this is good enough.
        count = 0
        for route in self.all_routes():
            if route.owner == owner:
                route.stale = True
                count += 1
        return count

    def del_stale_routes(self):
        # Delete all routes still marked as stale. Returns number of deleted routes.
        # Cannot delete routes while iterating over routes, so prepare a delete list
        routes_to_delete = []
        for route in self.all_routes():
            if route.stale:
                routes_to_delete.append((route.prefix, route.owner))
        # Now delete the routes in the prepared list
        count = 0
        for (prefix, owner) in routes_to_delete:
            self.del_route(prefix, owner)
            count += 1
        return count

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
