import re

from kernel import Kernel
from fib_route import FibRoute
from next_hop import NextHop
from packet_common import add_missing_methods_to_thrift, make_ip_address, make_ip_prefix

# pylint: disable=line-too-long
# pylint: disable=bad-continuation

def test_create_kernel():
    _kernel_1 = Kernel(simulated_interfaces=False, log=None, log_id="", table_name="main")
    _kernel_2 = Kernel(simulated_interfaces=False, log=None, log_id="", table_name=3)

def test_cli_addresses_table():
    kern = Kernel(simulated_interfaces=False, log=None, log_id="", table_name="main")
    if not kern.platform_supported:
        return
    # We assume the loopback interface (lo) is always there, and we look for something like this:
    # +-----------+------------+------------+----------------+---------+
    # | Interface | Address    | Local      | Broadcast      | Anycast |
    # | Name      |            |            |                |         |
    # +-----------+------------+------------+----------------+---------+
    # | lo        | 127.0.0.1  | 127.0.0.1  |                |         |
    tab_str = kern.cli_addresses_table().to_string()
    pattern = (r"[|] Interface +[|] +Address +[|] +Local +[|] +Broadcast +[|] +Anycast +[|]\n"
               r"[|] Name +[|] +[|] +[|] +[|] +[|]\n"
               r"(.|[\n])*"
               r"[|] lo +[|] 127\.0\.0\.1 +[|] 127\.0\.0\.1 +[|] +[|] +[|]\n")
    assert re.search(pattern, tab_str) is not None

def test_cli_links_table():
    kern = Kernel(simulated_interfaces=False, log=None, log_id="", table_name="main")
    if not kern.platform_supported:
        return
    # We assume the loopback interface (lo) is always there, and we look for something like this:
    # +-----------+-----------+-------------------+-------------------+-----------+-------+-----------+
    # | Interface | Interface | Hardware          | Hardware          | Link Type | MTU   | Flags     |
    # | Name      | Index     | Address           | Broadcast         |           |       |           |
    # |           |           |                   | Address           |           |       |           |
    # +-----------+-----------+-------------------+-------------------+-----------+-------+-----------+
    # | lo        | 1         | 00:00:00:00:00:00 | 00:00:00:00:00:00 |           | 65536 | UP        |
    # ...
    tab_str = kern.cli_links_table().to_string()
    pattern = (r"[|] Interface +[|] +Interface +[|] +Hardware +[|] +Hardware  +[|] +Link Type +[|] +MTU   +[|] +Flags +[|]\n"
               r"[|] Name      +[|] +Index     +[|] +Address  +[|] +Broadcast +[|] +          +[|] +      +[|] +      +[|]\n"
               r"[|]           +[|] +          +[|] +         +[|] +Address   +[|] +          +[|] +      +[|] +      +[|]\n"
               r"(.|[\n])*"
               r"[|] lo +[|] +[0-9]+ +[|] +[0-9:]+ +[|] +[0-9:]+ +[|] + +[|] +[0-9 ]+[|] +UP +[|]\n")
    assert re.search(pattern, tab_str) is not None

def test_cli_routes_table():
    add_missing_methods_to_thrift()
    kern = Kernel(simulated_interfaces=False, log=None, log_id="", table_name="main")
    if not kern.platform_supported:
        return
    # We assume that the main route table always has a default route, and we look for this:
    # +-------------+---------+--------------------+-------------+-----------+-----------+------------+--------+
    # | Table       | Address | Destination        | Type        | Protocol  | Outgoing  | Gateway    | Weight |
    # |             | Family  |                    |             |           | Interface |            |        |
    # +-------------+---------+--------------------+-------------+-----------+-----------+------------+--------+
    # ...
    # | Main        | IPv4    | 0.0.0.0/0          | Unicast     | Boot/Dhcp | eth0      | 172.17.0.1 |        |
    # ...
    tab_str = kern.cli_routes_table(254).to_string()
    pattern = (r"[|] Table +[|] Address +[|] Destination +[|] Type +[|] Protocol +[|] Outgoing +[|] Gateway +[|] Weight +[|]\n"
               r"[|] +[|] Family +[|] +[|] +[|] +[|] Interface +[|] +[|] +[|]\n"
               r"(.|[\n])*"
               r"[|] Main +[|] IPv4 +[|] 0\.0\.0\.0/0 +[|] Unicast +[|]")
    assert re.search(pattern, tab_str) is not None

def test_cli_route_prefix_table():
    kern = Kernel(simulated_interfaces=False, log=None, log_id="", table_name="main")
    if not kern.platform_supported:
        return
    # We assume that the main route table always has a default route, and we look for this:
    # +--------------------------+------------------+
    # | Table                    | Main             |
    # | Address Family           | IPv4             |
    # | Destination              | 0.0.0.0/0        |
    # | Type                     | Unicast          |
    # | Protocol                 | Boot             | << or Dhcp in some deployments
    # | Scope                    | Universe         |
    # | Next-hops                | eth0 172.17.0.1  |
    # | Priority                 |                  |
    # | Preference               |                  |
    # | Preferred Source Address |                  |
    # | Source                   |                  |
    # | Flow                     |                  |
    # | Encapsulation Type       |                  |
    # | Encapsulation            |                  |
    # | Metrics                  |                  |
    # | Type of Service          | 0                |
    # | Flags                    | 0                |
    # +--------------------------+------------------+
    default_prefix = make_ip_prefix("0.0.0.0/0")
    tab_str = kern.cli_route_prefix_table(254, default_prefix).to_string()
    pattern = (r"[|] Table +[|] Main +[|]\n"
               r"[|] Address Family +[|] IPv4 +[|]\n"
               r"[|] Destination +[|] 0\.0\.0\.0/0 +[|]\n"
               r"[|] Type +[|] Unicast +[|]\n"
               r"[|] Protocol +[|] (Boot|Dhcp) +[|]\n"
               r"[|] Scope +[|] Universe +[|]\n")
    assert re.search(pattern, tab_str) is not None

def test_put_del_route():
    kern = Kernel(simulated_interfaces=False, log=None, log_id="", table_name="5")
    if not kern.platform_supported:
        return
    # Put route with one next-hop (with interface but no address)
    prefix = make_ip_prefix("99.99.99.99/32")
    nhops = [NextHop(False, "lo", None, None)]
    rte = FibRoute(prefix, nhops)
    assert kern.put_route(rte)
    # Delete route just added
    assert kern.del_route(prefix)
    # Put route with one next-hop (with interface and address)
    prefix = make_ip_prefix("99.99.99.99/32")
    address = make_ip_address("127.0.0.1")
    nhops = [NextHop(False, "lo", address, None)]
    rte = FibRoute(prefix, nhops)
    assert kern.put_route(rte)
    # Delete route just added
    assert kern.del_route(prefix)
    # Put ECMP route with multiple next-hop (with interface and address)
    prefix = make_ip_prefix("99.99.99.99/32")
    address1 = make_ip_address("127.0.0.1")
    address2 = make_ip_address("127.0.0.2")
    nhops = [NextHop(False, "lo", address1, None), NextHop(False, "lo", address2, None)]
    rte = FibRoute(prefix, nhops)
    assert kern.put_route(rte)
    # Do we display the ECMP route properly?
    tab_str = kern.cli_route_prefix_table(5, prefix).to_string()
    pattern = (r"[|] Table +[|] 5 +[|]\n"
               r"[|] Address Family +[|] IPv4 +[|]\n"
               r"[|] Destination +[|] 99\.99\.99\.99/32 +[|]\n"
               r"[|] Type +[|] Unicast +[|]\n"
               r"[|] Protocol +[|] RIFT +[|]\n"
               r"[|] Scope +[|] Universe +[|]\n"
               r"[|] Next-hops +[|] lo 127\.0\.0\.1 1 +[|]\n"
               r"[|] +[|] lo 127\.0\.0\.2 1 +[|]\n")
    assert re.search(pattern, tab_str) is not None
    # Delete route just added
    assert kern.del_route(prefix)

def test_put_del_route_errors():
    kern = Kernel(simulated_interfaces=False, log=None, log_id="", table_name="main")
    if not kern.platform_supported:
        return
    # Attempt to add route with nonsense next-hop interface
    prefix = make_ip_prefix("99.99.99.99/32")
    nhops = [NextHop(False, "nonsense", None, None)]
    rte = FibRoute(prefix, nhops)
    assert not kern.put_route(rte)


def test_put_del_route_unreachable():
    kern = Kernel(simulated_interfaces=False, log=None, log_id="", table_name="main")
    if not kern.platform_supported:
        return
    # Add unreachable prefix in the kernel routing table (no next hops)
    prefix = make_ip_prefix("99.99.99.99/32")
    nhops = []
    rte = FibRoute(prefix, nhops)
    assert kern.put_route(rte)
    tab_str = kern.cli_route_prefix_table(254, prefix).to_string()
    pattern = (r"[|] Table +[|] Main +[|]\n"
               r"[|] Address Family +[|] IPv4 +[|]\n"
               r"[|] Destination +[|] 99\.99\.99\.99/32 +[|]\n"
               r"[|] Type +[|] Unreachable +[|]\n"
               r"[|] Protocol +[|] RIFT +[|]\n"
               r"[|] Scope +[|] Universe +[|]\n"
               r"[|] Next-hops +[|]  +[|]\n"
               r"[|] Priority +[|] 199 +[|]\n")
    assert re.search(pattern, tab_str) is not None
    # Replace unreachable route with a route containing one next hop
    new_nhops = [NextHop(False, "lo", make_ip_address("127.0.0.1"), None)]
    rte = FibRoute(prefix, new_nhops)
    assert kern.put_route(rte)
    tab_str = kern.cli_route_prefix_table(254, prefix).to_string()
    pattern = (r"[|] Table +[|] Main +[|]\n"
               r"[|] Address Family +[|] IPv4 +[|]\n"
               r"[|] Destination +[|] 99\.99\.99\.99/32 +[|]\n"
               r"[|] Type +[|] Unicast +[|]\n"
               r"[|] Protocol +[|] RIFT +[|]\n"
               r"[|] Scope +[|] Universe +[|]\n"
               r"[|] Next-hops +[|] lo 127.0.0.1 +[|]\n"
               r"[|] Priority +[|] 199 +[|]\n")
    assert re.search(pattern, tab_str) is not None
    # Delete next hops
    assert kern.del_route(prefix)


def test_table_nr_to_name():
    assert Kernel.table_nr_to_name(255) == "Local"
    assert Kernel.table_nr_to_name(254) == "Main"
    assert Kernel.table_nr_to_name(253) == "Default"
    assert Kernel.table_nr_to_name(5) == "5"
    assert Kernel.table_nr_to_name(0) == "Unspecified"
    assert Kernel.table_nr_to_name(-1) == "None"

def test_table_name_to_nr():
    assert Kernel.table_name_to_nr("LoCaL") == 255
    assert Kernel.table_name_to_nr("local") == 255
    assert Kernel.table_name_to_nr("main") == 254
    assert Kernel.table_name_to_nr("default") == 253
    assert Kernel.table_name_to_nr("5") == 5
    assert Kernel.table_name_to_nr("unspecified") == 0
    assert Kernel.table_name_to_nr("none") == -1
