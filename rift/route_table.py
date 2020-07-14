from pytricia import PyTricia

from destination import Destination
from fib_route import FibRoute
from packet_common import assert_prefix_address_family, ip_prefix_str
from rib_route import RibRoute
from table import Table


class RouteTable:
    """
    The route table, also known as routing information base (RIB).
    """

    def __init__(self, address_family, fib, log, log_id):
        assert fib.address_family == address_family
        self.address_family = address_family
        self.destinations = PyTricia()
        self.fib = fib
        self._log = log
        self._log_id = log_id

    def debug(self, msg, *args):
        if self._log:
            self._log.debug("[%s] %s" % (self._log_id, msg), *args)

    def get_route(self, prefix, owner):
        assert_prefix_address_family(prefix, self.address_family)
        prefix = ip_prefix_str(prefix)
        if self.destinations.has_key(prefix):
            return self.destinations.get(prefix).get_route(owner)
        return None

    def put_route(self, rib_route):
        assert_prefix_address_family(rib_route.prefix, self.address_family)
        rib_route.stale = False
        self.debug("Put %s", rib_route)
        prefix = rib_route.prefix
        prefix_str = ip_prefix_str(prefix)
        if not self.destinations.has_key(prefix_str):
            destination = Destination(self, prefix)
            self.destinations.insert(prefix_str, destination)
        else:
            destination = self.destinations.get(prefix_str)
        best_changed = destination.put_route(rib_route)
        if best_changed:
            child_prefix_strs = self.destinations.children(prefix_str)
            self.update_fib(prefix, child_prefix_strs)

    def del_route(self, prefix, owner):
        assert_prefix_address_family(prefix, self.address_family)
        prefix_str = ip_prefix_str(prefix)
        if self.destinations.has_key(prefix_str):
            destination = self.destinations.get(prefix_str)
            child_prefix_strs = self.destinations.children(prefix_str)
            deleted, best_changed = destination.del_route(owner)
            # If that was the last route for the destination, delete the destination itself
            if not destination.rib_routes:
                del self.destinations[prefix_str]
        else:
            deleted = False
            best_changed = False
        if deleted:
            self.debug("Delete %s", prefix)
        else:
            self.debug("Attempted delete %s (not present)", prefix)
        if best_changed:
            self.update_fib(prefix, child_prefix_strs)
        return deleted

    def update_fib(self, prefix, child_prefix_strs):
        # The child_prefix_strs have to be passed as a parameter, because they need to be collected
        # before the parent is potentially deleted by the calling function.
        # Locate the best RIB route for the prefix (None if there is no RIB route for the prefix).
        prefix_str = ip_prefix_str(prefix)
        if self.destinations.has_key(prefix_str):
            destination = self.destinations.get(prefix_str)
            rib_route = destination.best_route()
        else:
            rib_route = None
        # Determine the next-hops for the corresponding FIB route. If the next-hops is an empty
        # list [] it means it is a discard route. If the next-hops is None it means there should not
        # be a FIB route.
        if rib_route:
            fib_next_hops = rib_route.compute_fib_next_hops()
        else:
            fib_next_hops = None
        # Update the FIB route accordingly.
        if fib_next_hops is not None:
            fib_route = FibRoute(prefix, fib_next_hops)
            self.fib.put_route(fib_route)
        else:
            self.fib.del_route(prefix)
        # Recursively update the FIB for all child routes: their negative next-hops, if any, may
        # have to be recomputed if a parent route changed.
        for child_prefix_str in child_prefix_strs:
            child_destination = self.destinations[child_prefix_str]
            child_rib_route = child_destination.best_route()
            child_prefix = child_rib_route.prefix
            grand_child_prefix_strs = self.destinations.children(child_prefix_str)
            self.update_fib(child_prefix, grand_child_prefix_strs)

    def all_routes(self):
        for prefix in self.destinations:
            destination = self.destinations.get(prefix)
            for rib_route in destination.rib_routes:
                yield rib_route

    def all_prefix_routes(self, prefix):
        assert_prefix_address_family(prefix, self.address_family)
        prefix_str = ip_prefix_str(prefix)
        if self.destinations.has_key(prefix_str):
            destination = self.destinations[prefix_str]
            for rib_route in destination.routes:
                yield rib_route

    def cli_table(self):
        table = Table()
        table.add_row(RibRoute.cli_summary_headers())
        for rib_route in self.all_routes():
            table.add_row(rib_route.cli_summary_attributes())
        return table

    def mark_owner_routes_stale(self, owner):
        # Mark all routes of a given owner as stale. Returns number of routes marked.
        count = 0
        for rib_route in self.all_routes():
            if rib_route.owner == owner:
                rib_route.stale = True
                count += 1
        return count

    def del_stale_routes(self):
        # Delete all routes still marked as stale. Returns number of deleted routes.
        # Cannot delete routes while iterating over routes, so prepare a delete list
        routes_to_delete = []
        for rib_route in self.all_routes():
            if rib_route.stale:
                routes_to_delete.append((rib_route.prefix, rib_route.owner))
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
        for prefix in self.destinations:
            destination = self.destinations.get(prefix)
            count += len(destination.rib_routes)
        return count
