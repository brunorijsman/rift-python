import sortedcontainers

import packet_common
import route
import table

class RouteTable:

    def __init__(self, address_family, fib, log, log_id):
        assert fib.address_family == address_family
        self.address_family = address_family
        # Sorted dict of _Destination objects indexed by prefix
        self.destinations = sortedcontainers.SortedDict()
        self.fib = fib
        self._log = log
        self._log_id = log_id

    def debug(self, msg, *args):
        if self._log:
            self._log.debug("[%s] %s" % (self._log_id, msg), *args)

    def get_route(self, prefix, owner):
        packet_common.assert_prefix_address_family(prefix, self.address_family)
        if prefix in self.destinations:
            return self.destinations[prefix].get_route(owner)
        else:
            return None

    def put_route(self, rte):
        packet_common.assert_prefix_address_family(rte.prefix, self.address_family)
        rte.stale = False
        prefix = rte.prefix
        self.debug("Put %s", rte)
        if rte.prefix in self.destinations:
            destination = self.destinations[prefix]
        else:
            destination = _Destination(prefix)
            self.destinations[prefix] = destination
        destination.put_route(rte, self.fib)

    def del_route(self, prefix, owner):
        # Returns True if the route was present in the table and False if not.
        packet_common.assert_prefix_address_family(prefix, self.address_family)
        if prefix in self.destinations:
            destination = self.destinations[prefix]
            deleted = destination.del_route(owner, self.fib)
            if destination.routes == []:
                del self.destinations[prefix]
        else:
            deleted = False
        if deleted:
            self.debug("Delete %s", prefix)
        else:
            self.debug("Attempted delete %s (not present)", prefix)
        return deleted

    def all_routes(self):
        for destination in self.destinations.values():
            for rte in destination.routes:
                yield rte

    def all_prefix_routes(self, prefix):
        packet_common.assert_prefix_address_family(prefix, self.address_family)
        if prefix in self.destinations:
            destination = self.destinations[prefix]
            for rte in destination.routes:
                yield rte

    def cli_table(self):
        tab = table.Table()
        tab.add_row(route.Route.cli_summary_headers())
        for rte in self.all_routes():
            tab.add_row(rte.cli_summary_attributes())
        return tab

    def mark_owner_routes_stale(self, owner):
        # Mark all routes of a given owner as stale. Returns number of routes marked.
        # A possible more efficient implementation is to have a list of routes for each owner.
        # For now, this is good enough.
        count = 0
        for rte in self.all_routes():
            if rte.owner == owner:
                rte.stale = True
                count += 1
        return count

    def del_stale_routes(self):
        # Delete all routes still marked as stale. Returns number of deleted routes.
        # Cannot delete routes while iterating over routes, so prepare a delete list
        routes_to_delete = []
        for rte in self.all_routes():
            if rte.stale:
                routes_to_delete.append((rte.prefix, rte.owner))
        # Now delete the routes in the prepared list
        count = len(routes_to_delete)
        if count > 0:
            self.debug("Delete %d remaining stale routes", count)
        for (prefix, owner) in routes_to_delete:
            self.del_route(prefix, owner)
        return count

    def nr_destinations(self):
        return len(self.destinations)

    def nr_routes(self):
        count = 0
        for destination in self.destinations.values():
            count += len(destination.routes)
        return count

class _Destination:

    # For each prefix, there can be up to one route per owner. This is also the order of preference
    # for the routes from different owners to the same destination (higher numerical value is more
    # preferred)

    def __init__(self, prefix):
        self.prefix = prefix
        # List of Route objects, in decreasing order or owner (= in decreasing order of preference)
        # For a given owner, at most one route is allowed to be in the list
        self.routes = []

    def get_route(self, owner):
        for rte in self.routes:
            if rte.owner == owner:
                return rte
        return None

    def update_fib(self, fib):
        if self.routes == []:
            fib.del_route(self.prefix)
        else:
            best_route = self.routes[0]
            fib.put_route(best_route)

    def put_route(self, new_route, fib):
        index = 0
        inserted = False
        for existing_route in self.routes:
            if existing_route.owner == new_route.owner:
                self.routes[index] = new_route
                inserted = True
                different = self.routes_significantly_different(existing_route, new_route)
                break
            elif existing_route.owner < new_route.owner:
                self.routes.insert(index, new_route)
                inserted = True
                different = True
                break
            index += 1
        if not inserted:
            self.routes.append(new_route)
            different = True
        if different:
            self.update_fib(fib)

    def del_route(self, owner, fib):
        index = 0
        for rte in self.routes:
            if rte.owner == owner:
                del self.routes[index]
                self.update_fib(fib)
                return True
            index += 1
        return False

    @staticmethod
    def routes_significantly_different(route1, route2):
        assert route1.prefix == route2.prefix
        if route1.owner != route2.owner:
            return True
        if route1.next_hops != route2.next_hops:
            return True
        return False
