import sortedcontainers

import packet_common
import rib_route
import table

class ForwardingTable:

    def __init__(self, address_family, kernel, log, log_id):
        self.address_family = address_family
        self.kernel = kernel
        # Sorted dict of Route objects indexed by prefix. We use the Route class for both the RIB
        # and the FIB, although not all Route attributes are relevant for the FIB.
        self.routes = sortedcontainers.SortedDict()
        self._log = log
        self._log_id = log_id

    def debug(self, msg, *args):
        if self._log:
            self._log.debug("[%s] %s" % (self._log_id, msg), *args)

    def get_route(self, prefix):
        packet_common.assert_prefix_address_family(prefix, self.address_family)
        if prefix in self.routes:
            return self.routes[prefix]
        else:
            return None

    def put_route(self, rte):
        packet_common.assert_prefix_address_family(rte.prefix, self.address_family)
        self.debug("Put %s", rte)
        self.routes[rte.prefix] = rte
        if self.kernel is not None:
            self.kernel.put_route(rte)

    def del_route(self, prefix):
        # Returns True if the route was present in the table and False if not.
        packet_common.assert_prefix_address_family(prefix, self.address_family)
        if prefix not in self.routes:
            self.debug("Attempted delete %s (not present)", prefix)
            return False
        self.debug("Delete %s", prefix)
        del self.routes[prefix]
        if self.kernel is not None:
            self.kernel.del_route(prefix)
        return True

    def all_routes(self):
        for _prefix, rte in self.routes.items():
            yield rte

    def cli_table(self):
        tab = table.Table()
        tab.add_row(rib_route.RibRoute.cli_summary_headers())
        for rte in self.all_routes():
            tab.add_row(rte.cli_summary_attributes())
        return tab

    def nr_routes(self):
        return len(self.routes)
