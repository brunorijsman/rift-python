import re

import constants
import kernel
import next_hop
import packet_common
import route

# pylint: disable=line-too-long
# pylint: disable=bad-continuation

def test_create_kernel():
    _kernel_1 = kernel.Kernel(log=None, log_id="", table_name="main")
    _kernel_2 = kernel.Kernel(log=None, log_id="", table_name=3)

def test_cli_addresses_table():
    kern = kernel.Kernel(log=None, log_id="", table_name="main")
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
    kern = kernel.Kernel(log=None, log_id="", table_name="main")
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
    packet_common.add_missing_methods_to_thrift()
    kern = kernel.Kernel(log=None, log_id="", table_name="main")
    if not kern.platform_supported:
        return
    # We assume that the main route table always has a default route, and we look for this:
    # +-------------+---------+--------------------+-------------+----------+-----------+------------+--------+
    # | Table       | Address | Destination        | Type        | Protocol | Outgoing  | Gateway    | Weight |
    # |             | Family  |                    |             |          | Interface |            |        |
    # +-------------+---------+--------------------+-------------+----------+-----------+------------+--------+
    # ...
    # | Main        | IPv4    | 0.0.0.0/0          | Unicast     | Boot     | eth0      | 172.17.0.1 |        |
    # ...
    tab_str = kern.cli_routes_table(254).to_string()
    pattern = (r"[|] Table +[|] Address +[|] Destination +[|] Type +[|] Protocol +[|] Outgoing +[|] Gateway +[|] Weight +[|]\n"
               r"[|] +[|] Family +[|] +[|] +[|] +[|] Interface +[|] +[|] +[|]\n"
               r"(.|[\n])*"
               r"[|] Main +[|] IPv4 +[|] 0\.0\.0\.0/0 +[|] Unicast +[|] Boot +[|]")
    assert re.search(pattern, tab_str) is not None

def test_cli_route_prefix_table():
    kern = kernel.Kernel(log=None, log_id="", table_name="main")
    if not kern.platform_supported:
        return
    # We assume that the main route table always has a default route, and we look for this:
    # +--------------------------+------------------+
    # | Table                    | Main             |
    # | Address Family           | IPv4             |
    # | Destination              | 0.0.0.0/0        |
    # | Type                     | Unicast          |
    # | Protocol                 | Boot             |
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
    default_prefix = packet_common.make_ip_prefix("0.0.0.0/0")
    tab_str = kern.cli_route_prefix_table(254, default_prefix).to_string()
    pattern = (r"[|] Table +[|] Main +[|]\n"
               r"[|] Address Family +[|] IPv4 +[|]\n"
               r"[|] Destination +[|] 0\.0\.0\.0/0 +[|]\n"
               r"[|] Type +[|] Unicast +[|]\n"
               r"[|] Protocol +[|] Boot +[|]\n"
               r"[|] Scope +[|] Universe +[|]\n")
    assert re.search(pattern, tab_str) is not None

def test_put_del_route():
    kern = kernel.Kernel(log=None, log_id="", table_name="5")
    if not kern.platform_supported:
        return
    # Put route with one next-hop (with interface but no address)
    prefix = packet_common.make_ip_prefix("99.99.99.99/32")
    nhops = [next_hop.NextHop("lo", None)]
    rte = route.Route(prefix, constants.OWNER_S_SPF, nhops)
    assert kern.put_route(rte)
    # Delete route just added
    assert kern.del_route(prefix)
    # Put route with one next-hop (with interface and address)
    prefix = packet_common.make_ip_prefix("99.99.99.99/32")
    address = packet_common.make_ip_address("127.0.0.1")
    nhops = [next_hop.NextHop("lo", address)]
    rte = route.Route(prefix, constants.OWNER_S_SPF, nhops)
    assert kern.put_route(rte)
    # Delete route just added
    assert kern.del_route(prefix)
    # Put ECMP route with multiple next-hop (with interface and address)
    prefix = packet_common.make_ip_prefix("99.99.99.99/32")
    address1 = packet_common.make_ip_address("127.0.0.1")
    address2 = packet_common.make_ip_address("127.0.0.2")
    nhops = [next_hop.NextHop("lo", address1), next_hop.NextHop("lo", address2)]
    rte = route.Route(prefix, constants.OWNER_S_SPF, nhops)
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
    kern = kernel.Kernel(log=None, log_id="", table_name="main")
    if not kern.platform_supported:
        return
    # Attempt to add route with nonsense next-hop interface
    prefix = packet_common.make_ip_prefix("99.99.99.99/32")
    nhops = [next_hop.NextHop("nonsense", None)]
    rte = route.Route(prefix, constants.OWNER_S_SPF, nhops)
    assert not kern.put_route(rte)

def test_table_nr_to_name():
    assert kernel.Kernel.table_nr_to_name(255) == "Local"
    assert kernel.Kernel.table_nr_to_name(254) == "Main"
    assert kernel.Kernel.table_nr_to_name(253) == "Default"
    assert kernel.Kernel.table_nr_to_name(5) == "5"
    assert kernel.Kernel.table_nr_to_name(0) == "Unspecified"
    assert kernel.Kernel.table_nr_to_name(-1) == "None"

def test_table_name_to_nr():
    assert kernel.Kernel.table_name_to_nr("LoCaL") == 255
    assert kernel.Kernel.table_name_to_nr("local") == 255
    assert kernel.Kernel.table_name_to_nr("main") == 254
    assert kernel.Kernel.table_name_to_nr("default") == 253
    assert kernel.Kernel.table_name_to_nr("5") == 5
    assert kernel.Kernel.table_name_to_nr("unspecified") == 0
    assert kernel.Kernel.table_name_to_nr("none") == -1
