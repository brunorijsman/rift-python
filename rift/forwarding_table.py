import sortedcontainers

import packet_common
import fib_route
import table

class ForwardingTable:
    """
    The forwarding table, also known as forwarding information base (FIB).
    """

    def __init__(self, address_family, kernel, log, log_id):
        self.address_family = address_family
        self.kernel = kernel
        self.fib_routes = sortedcontainers.SortedDict()
        self._log = log
        self._log_id = log_id

    def debug(self, msg, *args):
        if self._log:
            self._log.debug("[%s] %s" % (self._log_id, msg), *args)

    def get_route(self, prefix):
        packet_common.assert_prefix_address_family(prefix, self.address_family)
        if prefix in self.fib_routes:
            return self.fib_routes[prefix]
        else:
            return None

    def put_route(self, fib_rte):
        packet_common.assert_prefix_address_family(fib_rte.prefix, self.address_family)
        self.debug("Put %s", fib_rte)
        self.fib_routes[fib_rte.prefix] = fib_rte
        if self.kernel is not None:
            self.kernel.put_route(fib_rte)

    def del_route(self, prefix):
        # Returns True if the route was present in the table and False if not.
        packet_common.assert_prefix_address_family(prefix, self.address_family)
        if prefix not in self.fib_routes:
            self.debug("Attempted delete %s (not present)", prefix)
            return False
        self.debug("Delete %s", prefix)
        del self.fib_routes[prefix]
        if self.kernel is not None:
            self.kernel.del_route(prefix)
        return True

    def all_routes(self):
        for _prefix, fib_rte in self.fib_routes.items():
            yield fib_rte

    def cli_table(self):
        tab = table.Table()
        tab.add_row(fib_route.FibRoute.cli_summary_headers())
        for fib_rte in self.all_routes():
            tab.add_row(fib_rte.cli_summary_attributes())
        return tab

    def nr_routes(self):
        return len(self.fib_routes)
