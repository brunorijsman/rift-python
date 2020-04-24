import pytricia

import packet_common
import rib_route
import table


class RouteTable:

    def __init__(self, address_family, fib, log, log_id):
        assert fib.address_family == address_family
        self.address_family = address_family
        # Sorted dict of _Destination objects indexed by prefix
        self.destinations = pytricia.PyTricia()
        self.fib = fib
        self._log = log
        self._log_id = log_id

    def debug(self, msg, *args):
        if self._log:
            self._log.debug("[%s] %s" % (self._log_id, msg), *args)

    def get_route(self, rte_prefix, owner):
        packet_common.assert_prefix_address_family(rte_prefix, self.address_family)
        prefix = packet_common.ip_prefix_str(rte_prefix)
        if self.destinations.has_key(prefix):
            return self.destinations.get(prefix).get_route(owner)
        else:
            return None

    def put_route(self, rte):
        """
        Add a RibRoute object to the Destination object associated to the prefix.
        :param rte: (RibRoute) the object to add to the Destination associated to the prefix
        :return:
        """

        packet_common.assert_prefix_address_family(rte.prefix, self.address_family)
        rte.stale = False
        self.debug("Put %s", rte)
        # If there is no Destination object for the prefix, create a new Destination object
        # for the given prefix and insert it in the Trie
        prefix = packet_common.ip_prefix_str(rte.prefix)
        if not self.destinations.has_key(prefix):
            prefix_destination = _Destination(self, rte.prefix)
            self.destinations.insert(prefix, prefix_destination)
        else:
            prefix_destination = self.destinations.get(prefix)
        # Insert desired route in destination object
        best_changed = prefix_destination.put_route(rte)

        # Get children prefixes before performing actions on the prefix
        # (it can be deleted from the Trie)
        children_prefixes = self.destinations.children(
            packet_common.ip_prefix_str(prefix_destination.prefix))

        # If best route changed in Destination object
        if best_changed:
            # Update prefix in the fib
            self.fib.put_route(prefix_destination.best_route)
            # Try to delete superfluous children
            if not self._delete_superfluous_children(prefix_destination, children_prefixes):
                # If children have not been deleted, update them
                self._update_prefix_children(children_prefixes)

    def _update_prefix_children(self, children_prefixes):
        """
        Refresh children next hops
        :param children_prefixes: (list) all the children at each level of a given prefix
        :return:
        """
        for child_prefix in children_prefixes:
            child_prefix_dest = self.destinations.get(child_prefix)
            self.fib.put_route(child_prefix_dest.best_route)

    def _delete_superfluous_children(self, prefix_dest, children_prefixes):
        """
        Delete superfluous children of the given prefix from the RIB and the FIB when it is
        unreachable
        :param prefix_dest: (Destination) object to check for superfluous children
        :param children_prefixes: (list) children of given prefix
        :return: (boolean) if children of the given prefix have been removed or not
        """
        best_route = prefix_dest.best_route
        if (not best_route.positive_next_hops and best_route.negative_next_hops) \
                and not best_route.next_hops and prefix_dest.parent_prefix_dest:
            for child_prefix in children_prefixes:
                self.destinations.delete(child_prefix)
                self.fib.del_route(packet_common.make_ip_prefix(child_prefix))
            return True

        return False

    def del_route(self, rte_prefix, owner):
        """
        Delete given prefix and owner RibRoute object.
        If no more RibRoute objects are available, also delete Destination from trie and
        from the FIB.
        :param rte_prefix: (string) prefix to delete
        :param owner: (int) owner of the prefix
        :return: (boolean) if the route has been deleted or not
        """
        packet_common.assert_prefix_address_family(rte_prefix, self.address_family)
        destination_deleted = False
        best_changed = False
        children_prefixes = None
        prefix = packet_common.ip_prefix_str(rte_prefix)
        # Check if the prefix is stored in the trie
        if self.destinations.has_key(prefix):
            # Get children prefixes before performing actions on the prefix
            # (it can be deleted from the Trie)
            children_prefixes = self.destinations.children(prefix)
            destination = self.destinations.get(prefix)
            # Delete route from the Destination object
            deleted, best_changed = destination.del_route(owner)
            # Route was not present in Destination object, nothing to do
            if deleted:
                self.debug("Delete %s", prefix)
            else:
                self.debug("Attempted delete %s (not present)", prefix)
                return deleted
            if not destination.routes:
                # No more routes available for current prefix, delete it from trie and FIB
                self.destinations.delete(prefix)
                self.fib.del_route(rte_prefix)
                destination_deleted = True
            elif best_changed:
                # Best route changed, push it in the FIB
                self.fib.put_route(destination.best_route)
        else:
            deleted = False
        if deleted and (best_changed or destination_deleted):
            # If route has been deleted and an event occurred
            # (best changed or destination deleted), update children
            self._update_prefix_children(children_prefixes)
        return deleted

    def all_routes(self):
        for prefix in self.destinations:
            destination = self.destinations.get(prefix)
            for rte in destination.routes:
                yield rte

    def all_prefix_routes(self, rte_prefix):
        packet_common.assert_prefix_address_family(rte_prefix, self.address_family)
        prefix = packet_common.ip_prefix_str(rte_prefix)
        if self.destinations.has_key(prefix):
            destination = self.destinations[prefix]
            for rte in destination.routes:
                yield rte

    def cli_table(self):
        tab = table.Table()
        tab.add_row(rib_route.RibRoute.cli_summary_headers())
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
        for prefix in self.destinations:
            destination = self.destinations.get(prefix)
            count += len(destination.routes)
        return count


class _Destination:
    """
    Class that contains all routes for a given prefix destination
    Attributes of this class are:
        - rib: reference to the RIB
        - prefix: prefix associated to this destination
        - routes: list of RibRoute objects, in decreasing order or owner (= in decreasing order of
            preference, higher numerical value is more preferred).
            For a given owner, at most one route is allowed to be in the list
    """

    def __init__(self, rib, prefix):
        self.rib = rib
        self.prefix = prefix
        self.routes = []

    @property
    def parent_prefix_dest(self):
        """
        :return: the Destination object associated to the parent prefix of the current one
        """
        parent_prefix = self.rib.destinations.parent(packet_common.ip_prefix_str(self.prefix))
        if parent_prefix is None:
            return None

        return self.rib.destinations.get(parent_prefix)

    @property
    def best_route(self):
        """
        :return: the best RibRoute for this prefix
        """
        return self.routes[0]

    def get_route(self, owner):
        """
        Get RibRoute object for a given owner if present
        :param owner: (int) owner of the route
        :return: (RibRoute|None) desired RibRoute object if present, else None
        """
        for rte in self.routes:
            if rte.owner == owner:
                return rte
        return None

    def put_route(self, new_route):
        """
        Add a new RibRoute object in the list of routes for the current prefix. Route is added
        with proper priority.
        :param new_route: (RibRoute) route to add to the list
        :return:
        """
        assert self.prefix == new_route.prefix
        added = False
        best_changed = False
        index = 0
        for existing_route in self.routes:
            if existing_route.owner == new_route.owner:
                self.routes[index] = new_route
                added = True
                break
            elif existing_route.owner < new_route.owner:
                self.routes.insert(index, new_route)
                added = True
                break
            index += 1
        if not added:
            self.routes.append(new_route)
        if index == 0:
            best_changed = True
        # Update the Route Destination object instance with the current object
        new_route.destination = self
        return best_changed

    def del_route(self, owner):
        """
        Delete a RibRoute object for the given owner
        :param owner: (int) owner of the route
        :return: (tuple) first element is a boolean that indicates if the route has been deleted,
            second element is a boolean that indicates if the best route changed
        """
        best_changed = False
        for index, rte in enumerate(self.routes):
            if rte.owner == owner:
                del self.routes[index]
                if index == 0:
                    best_changed = True
                return True, best_changed
        return False, best_changed

    def __repr__(self):
        parent_prefix = "(Parent: " + self.parent_prefix_dest.prefix + ")" \
            if self.parent_prefix_dest else ""
        return "%s\n%s %s\nBest Computed: %s\n\n" % (self.prefix, parent_prefix, str(self.routes),
                                                     str(self.best_route.next_hops))

    @staticmethod
    def routes_significantly_different(route1, route2):
        assert route1.prefix == route2.prefix
        if route1.owner != route2.owner:
            return True
        return False
