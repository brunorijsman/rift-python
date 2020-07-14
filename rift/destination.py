from packet_common import ip_prefix_str


class Destination:
    """
    The routing information base (RIB) can contain multiple routes to the same destination prefix,
    namely one per owner (south-spf, north-spf). The Destination object contains all RIB routes to
    a given destination prefix.
    """

    def __init__(self, rib, prefix):
        self.rib = rib
        self.prefix = prefix
        self.rib_routes = []

    def parent_destination(self):
        parent_prefix = self.rib.destinations.parent(ip_prefix_str(self.prefix))
        if parent_prefix is None:
            return None
        return self.rib.destinations.get(parent_prefix)

    def best_route(self):
        return self.rib_routes[0]

    def get_route(self, owner):
        for rib_route in self.rib_routes:
            if rib_route.owner == owner:
                return rib_route
        return None

    def put_route(self, new_rib_route):
        assert self.prefix == new_rib_route.prefix
        added = False
        best_changed = False
        index = 0
        for existing_rib_route in self.rib_routes:
            if existing_rib_route.owner == new_rib_route.owner:
                self.rib_routes[index] = new_rib_route
                added = True
                break
            elif existing_rib_route.owner < new_rib_route.owner:
                self.rib_routes.insert(index, new_rib_route)
                added = True
                break
            index += 1
        if not added:
            self.rib_routes.append(new_rib_route)
        if index == 0:
            best_changed = True
        new_rib_route.destination = self
        return best_changed

    def del_route(self, owner):
        # Returns (successfully_deleted, deleted_route_was_best)
        best_changed = False
        for index, rib_route in enumerate(self.rib_routes):
            if rib_route.owner == owner:
                del self.rib_routes[index]
                if index == 0:
                    best_changed = True
                return True, best_changed
        return False, best_changed

    @staticmethod
    def routes_significantly_different(rib_route1, rib_route2):
        assert rib_route1.prefix == rib_route2.prefix
        if rib_route1.owner != rib_route2.owner:
            return True
        return False
