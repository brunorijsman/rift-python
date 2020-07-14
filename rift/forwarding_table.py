from sortedcontainers import SortedDict

from packet_common import assert_prefix_address_family
from fib_route import FibRoute
from table import Table


class ForwardingTable:
    """
    The forwarding table, also known as forwarding information base (FIB).
    """

    def __init__(self, address_family, kernel, log, log_id):
        self.address_family = address_family
        self.kernel = kernel
        self.fib_routes = SortedDict()
        self._log = log
        self._log_id = log_id

    def debug(self, msg, *args):
        if self._log:
            self._log.debug("[%s] %s" % (self._log_id, msg), *args)

    def get_route(self, prefix):
        assert_prefix_address_family(prefix, self.address_family)
        if prefix in self.fib_routes:
            return self.rib_routes[prefix]
        else:
            return None

    def put_route(self, fib_route):
        assert_prefix_address_family(fib_route.prefix, self.address_family)
        self.debug("Put %s", fib_route)
        self.fib_routes[fib_route.prefix] = fib_route
        if self.kernel is not None:
            self.kernel.put_route(fib_route)

    def del_route(self, prefix):
        # Returns True if the route was present in the table and False if not.
        assert_prefix_address_family(prefix, self.address_family)
        if prefix not in self.fib_routes:
            self.debug("Attempted delete %s (not present)", prefix)
            return False
        self.debug("Delete %s", prefix)
        del self.fib_routes[prefix]
        if self.kernel is not None:
            self.kernel.del_route(prefix)
        return True

    def all_routes(self):
        for _prefix, fib_route in self.fib_routes.items():
            yield fib_route

    def cli_table(self):
        table = Table()
        table.add_row(FibRoute.cli_summary_headers())
        for fib_route in self.all_routes():
            table.add_row(fib_route.cli_summary_attributes())
        return table

    def nr_routes(self):
        return len(self.fib_routes)
