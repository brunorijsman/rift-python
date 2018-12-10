import pytest

import constants
import fib
import next_hop
import packet_common
import rib
import route

# Some helper constants and functions to make the test code more compact and easier to read
N = constants.OWNER_N_SPF
S = constants.OWNER_S_SPF

def mkrt(address_family):
    forwarding_table = fib.ForwardingTable(address_family)
    route_table = rib.RouteTable(address_family, forwarding_table)
    return route_table

def mkp(prefix_str):
    return packet_common.make_ip_prefix(prefix_str)

def mkr(prefix_str, owner, next_hops=None):
    if next_hops is None:
        next_hops = []
    return route.Route(mkp(prefix_str), owner, next_hops)

def mknh(interface_str, address_str):
    if address_str is None:
        address = None
    else:
        address = packet_common.make_ip_address(address_str)
    return next_hop.NextHop(interface_str, address)

def test_ipv4_table_put_route():
    packet_common.add_missing_methods_to_thrift()
    route_table = mkrt(constants.ADDRESS_FAMILY_IPV4)
    nh1 = mknh("if1", "1.1.1.1")
    nh2 = mknh("if2", "2.2.2.2")
    assert route_table.nr_destinations() == 0
    assert route_table.nr_routes() == 0
    # Add a route
    # No next_hop
    route_table.put_route(mkr("1.1.1.0/24", N))
    assert route_table.nr_destinations() == 1
    assert route_table.nr_routes() == 1
    # Add two routes with same prefix but with different owners (most preferred added first)
    # One next_hops each
    route_table.put_route(mkr("2.2.2.2/32", S, [nh1]))
    route_table.put_route(mkr("2.2.2.2/32", N, [nh2]))
    assert route_table.nr_destinations() == 2
    assert route_table.nr_routes() == 3
    # Add two routes with same prefix but with different owners (most preferred added last)
    # Two next_hops each
    route_table.put_route(mkr("3.3.3.0/24", N, [nh1, nh2]))
    route_table.put_route(mkr("3.3.3.0/24", S, [nh1, nh2]))
    assert route_table.nr_destinations() == 3
    assert route_table.nr_routes() == 5
    # Replace route which is already in the table (only one route to prefix)
    route_table.put_route(mkr("4.4.4.0/30", N))
    route_table.put_route(mkr("4.4.4.0/30", N))
    assert route_table.nr_destinations() == 4
    assert route_table.nr_routes() == 6
    # Replace route which is already in the table (multiple routes to prefix)
    route_table.put_route(mkr("0.0.0.0/0", S))
    route_table.put_route(mkr("0.0.0.0/0", N))
    route_table.put_route(mkr("0.0.0.0/0", N))
    assert route_table.nr_destinations() == 5
    assert route_table.nr_routes() == 8

def test_ipv4_table_get_route():
    packet_common.add_missing_methods_to_thrift()
    route_table = mkrt(constants.ADDRESS_FAMILY_IPV4)
    # Try to get a route that is not present in the table (empty table)
    assert route_table.get_route(mkp("1.1.1.0/24"), S) is None
    # Try to get a route that is not present in the table (prefix is not present)
    route_table.put_route(mkr("2.2.2.0/32", S))
    assert route_table.get_route(mkp("3.3.3.0/24"), S) is None
    # Try to get a route that is not present in the table (prefix length is wrong)
    assert route_table.get_route(mkp("2.2.2.0/24"), S) is None
    # Try to get a route that is not present in the table (owner is not present)
    assert route_table.get_route(mkp("2.2.2.0/32"), N) is None
    # Get a route that is present in the table (only route for prefix)
    rte = route_table.get_route(mkp("2.2.2.0/32"), S)
    assert rte is not None
    assert rte.prefix == mkp("2.2.2.0/32")
    assert rte.owner == S
    # Add other routes to the table
    route_table.put_route(mkr("1.1.0.0/16", N))
    route_table.put_route(mkr("2.2.2.0/32", N))
    route_table.put_route(mkr("2.2.2.0/24", N))
    route_table.put_route(mkr("3.0.0.0/8", S))
    # Get a route that is present in the table (multiple routes for prefix, get most preferred)
    rte = route_table.get_route(mkp("2.2.2.0/32"), S)
    assert rte is not None
    assert rte.prefix == mkp("2.2.2.0/32")
    assert rte.owner == S
    # Get a route that is present in the table (multiple routes for prefix, get least preferred)
    rte = route_table.get_route(mkp("2.2.2.0/32"), N)
    assert rte is not None
    assert rte.prefix == mkp("2.2.2.0/32")
    assert rte.owner == N

def test_ipv4_table_del_route():
    packet_common.add_missing_methods_to_thrift()
    route_table = mkrt(constants.ADDRESS_FAMILY_IPV4)
    assert route_table.nr_destinations() == 0
    assert route_table.nr_routes() == 0
    # Try to delete a route that is not present in the table (empty table)
    assert not route_table.del_route(mkp("1.1.1.0/24"), S)
    assert route_table.nr_destinations() == 0
    assert route_table.nr_routes() == 0
    # Try to delete a route that is not present in the table (prefix is not present)
    route_table.put_route(mkr("2.2.2.0/32", S))
    assert not route_table.del_route(mkp("3.3.3.0/24"), S)
    assert route_table.nr_destinations() == 1
    assert route_table.nr_routes() == 1
    # Try to delete a route that is not present in the table (prefix length is wrong)
    assert not route_table.del_route(mkp("2.2.2.0/24"), S)
    assert route_table.nr_destinations() == 1
    assert route_table.nr_routes() == 1
    # Try to delete a route that is not present in the table (owner is not present)
    assert not route_table.del_route(mkp("2.2.2.0/32"), N)
    assert route_table.nr_destinations() == 1
    assert route_table.nr_routes() == 1
    # Delete a route that is present in the table (only route for prefix)
    assert route_table.get_route(mkp("2.2.2.0/32"), S) is not None
    assert route_table.del_route(mkp("2.2.2.0/32"), S)
    assert route_table.get_route(mkp("2.2.2.0/32"), S) is None
    assert route_table.nr_destinations() == 0
    assert route_table.nr_routes() == 0
    # Put the deleted route back and add other routes to the table
    route_table.put_route(mkr("1.1.0.0/16", N))
    route_table.put_route(mkr("2.2.2.0/32", S))
    route_table.put_route(mkr("2.2.2.0/32", N))
    route_table.put_route(mkr("2.2.2.0/24", N))
    route_table.put_route(mkr("3.0.0.0/8", S))
    assert route_table.nr_destinations() == 4
    assert route_table.nr_routes() == 5
    # Delete a route that is present in the table (multiple routes for prefix, get most preferred)
    assert route_table.get_route(mkp("2.2.2.0/32"), S) is not None
    assert route_table.del_route(mkp("2.2.2.0/32"), S)
    assert route_table.get_route(mkp("2.2.2.0/32"), S) is None
    assert route_table.nr_destinations() == 4
    assert route_table.nr_routes() == 4
    route_table.put_route(mkr("2.2.2.0/32", S))
    # Delete a route that is present in the table (multiple routes for prefix, get least preferred)
    assert route_table.get_route(mkp("2.2.2.0/32"), N) is not None
    assert route_table.del_route(mkp("2.2.2.0/32"), N)
    assert route_table.get_route(mkp("2.2.2.0/32"), N) is None
    assert route_table.nr_destinations() == 4
    assert route_table.nr_routes() == 4
    route_table.put_route(mkr("2.2.2.0/32", N))

def test_ipv6_table_put_route():
    packet_common.add_missing_methods_to_thrift()
    route_table = mkrt(constants.ADDRESS_FAMILY_IPV6)
    nh1 = mknh("if1", "::1.1.1.1")
    nh2 = mknh("if2", "::2.2.2.2")
    assert route_table.nr_destinations() == 0
    assert route_table.nr_routes() == 0
    # Add a route
    # No next_hop
    route_table.put_route(mkr("1111:1111:1111:1111:0000:0000:0000:0000/64", N))
    assert route_table.nr_destinations() == 1
    assert route_table.nr_routes() == 1
    # Add two routes with same prefix but with different owners (most preferred added first)
    # One next_hop each
    route_table.put_route(mkr("2222:2222:2222:2222:2222:2222:2222:2222/128", S, [nh1]))
    route_table.put_route(mkr("2222:2222:2222:2222:2222:2222:2222:2222/128", N, [nh2]))
    assert route_table.nr_destinations() == 2
    assert route_table.nr_routes() == 3
    # Add two routes with same prefix but with different owners (most preferred added last)
    # Two next_hops each
    route_table.put_route(mkr("3333:3333:3333:3333:3333:0000:0000:0000/80", N, [nh1, nh2]))
    route_table.put_route(mkr("3333:3333:3333:3333:3333:0000:0000:0000/80", S, [nh1, nh2]))
    assert route_table.nr_destinations() == 3
    assert route_table.nr_routes() == 5
    # Replace route which is already in the table (only one route to prefix)
    route_table.put_route(mkr("4444::/16", N))
    route_table.put_route(mkr("4444::/16", N))
    assert route_table.nr_destinations() == 4
    assert route_table.nr_routes() == 6
    # Replace route which is already in the table (multiple routes to prefix)
    route_table.put_route(mkr("::0.0.0.0/0", S))
    route_table.put_route(mkr("::0.0.0.0/0", N))
    route_table.put_route(mkr("::0.0.0.0/0", N))
    assert route_table.nr_destinations() == 5
    assert route_table.nr_routes() == 8

def test_ipv6_table_get_route():
    packet_common.add_missing_methods_to_thrift()
    route_table = mkrt(constants.ADDRESS_FAMILY_IPV6)
    # Try to get a route that is not present in the table (empty table)
    assert route_table.get_route(mkp("1111:1111:1111:1111:0000:0000:0000:0000/64"), S) is None
    # Try to get a route that is not present in the table (prefix is not present)
    route_table.put_route(mkr("2222:2222:2222:2222:2222:2222:2222:2222/128", S))
    assert route_table.get_route(mkp("3333:3333:3333:3333:3333:0000:0000:0000/80"), S) is None
    # Try to get a route that is not present in the table (prefix length is wrong)
    assert route_table.get_route(mkp("2222:2222:2222:2222:2222:2222:2222:0000/112"), S) is None
    # Try to get a route that is not present in the table (owner is not present)
    assert route_table.get_route(mkp("2222:2222:2222:2222:2222:2222:2222:2222/128"), N) is None
    # Get a route that is present in the table (only route for prefix)
    rte = route_table.get_route(mkp("2222:2222:2222:2222:2222:2222:2222:2222/128"), S)
    assert rte is not None
    assert rte.prefix == mkp("2222:2222:2222:2222:2222:2222:2222:2222/128")
    assert rte.owner == S
    # Add other routes to the table
    route_table.put_route(mkr("1111:1111::/32", N))
    route_table.put_route(mkr("2222:2222:2222:2222:2222:2222:2222:2222/128", N))
    route_table.put_route(mkr("2222:2222:2222::/48", N))
    route_table.put_route(mkr("3333::/16", S))
    # Get a route that is present in the table (multiple routes for prefix, get most preferred)
    rte = route_table.get_route(mkp("2222:2222:2222:2222:2222:2222:2222:2222/128"), S)
    assert rte is not None
    assert rte.prefix == mkp("2222:2222:2222:2222:2222:2222:2222:2222/128")
    assert rte.owner == S
    # Get a route that is present in the table (multiple routes for prefix, get least preferred)
    rte = route_table.get_route(mkp("2222:2222:2222:2222:2222:2222:2222:2222/128"), N)
    assert rte is not None
    assert rte.prefix == mkp("2222:2222:2222:2222:2222:2222:2222:2222/128")
    assert rte.owner == N

def test_ipv6_table_del_route():
    packet_common.add_missing_methods_to_thrift()
    route_table = mkrt(constants.ADDRESS_FAMILY_IPV6)
    assert route_table.nr_destinations() == 0
    assert route_table.nr_routes() == 0
    # Try to delete a route that is not present in the table (empty table)
    assert not route_table.del_route(mkp("1111:1111:1111::/48"), S)
    assert route_table.nr_destinations() == 0
    assert route_table.nr_routes() == 0
    # Try to delete a route that is not present in the table (prefix is not present)
    route_table.put_route(mkr("2222::/16", S))
    assert not route_table.del_route(mkp("3333:3333:3333:3333:3333:0000:0000:0000/80"), S)
    assert route_table.nr_destinations() == 1
    assert route_table.nr_routes() == 1
    # Try to delete a route that is not present in the table (prefix length is wrong)
    assert not route_table.del_route(mkp("2222:2222::/32"), S)
    assert route_table.nr_destinations() == 1
    assert route_table.nr_routes() == 1
    # Try to delete a route that is not present in the table (owner is not present)
    assert not route_table.del_route(mkp("2222::/16"), N)
    assert route_table.nr_destinations() == 1
    assert route_table.nr_routes() == 1
    # Delete a route that is present in the table (only route for prefix)
    assert route_table.get_route(mkp("2222::/16"), S) is not None
    assert route_table.del_route(mkp("2222::/16"), S)
    assert route_table.get_route(mkp("2222::/16"), S) is None
    assert route_table.nr_destinations() == 0
    assert route_table.nr_routes() == 0
    # Put the deleted route back and add other routes to the table
    route_table.put_route(mkr("::/0", N))
    route_table.put_route(mkr("2222::/16", N))
    route_table.put_route(mkr("2222::/16", S))
    route_table.put_route(mkr("2222:2222::/32", N))
    route_table.put_route(mkr("3333:3333:3333:3333:3333:0000:0000:0000/80", S))
    route_table.put_route(mkr("3333:3333:3333:3333:3333:3333:3333:3333/128", S))
    assert route_table.nr_destinations() == 5
    assert route_table.nr_routes() == 6
    # Delete a route that is present in the table (multiple routes for prefix, get most preferred)
    assert route_table.get_route(mkp("2222::/16"), S) is not None
    assert route_table.del_route(mkp("2222::/16"), S)
    assert route_table.get_route(mkp("2222::/16"), S) is None
    assert route_table.nr_destinations() == 5
    assert route_table.nr_routes() == 5
    route_table.put_route(mkr("2222::/16", S))
    # Delete a route that is present in the table (multiple routes for prefix, get least preferred)
    assert route_table.get_route(mkp("2222::/16"), N) is not None
    assert route_table.del_route(mkp("2222::/16"), N)
    assert route_table.get_route(mkp("2222::/16"), N) is None
    assert route_table.nr_destinations() == 5
    assert route_table.nr_routes() == 5
    route_table.put_route(mkr("2222::/16", N))

def test_asserts():
    packet_common.add_missing_methods_to_thrift()
    route_table = mkrt(constants.ADDRESS_FAMILY_IPV4)
    # Passing the wrong prefix type to assert_prefix_address_family asserts
    with pytest.raises(Exception):
        packet_common.assert_prefix_address_family("1.2.3.0/24", constants.ADDRESS_FAMILY_IPV4)
    with pytest.raises(Exception):
        packet_common.assert_prefix_address_family(mkp("1.2.3.0/24"), constants.ADDRESS_FAMILY_IPV6)
    with pytest.raises(Exception):
        packet_common.assert_prefix_address_family(mkp("::1.2.3.0/24"),
                                                   constants.ADDRESS_FAMILY_IPV4)
    with pytest.raises(Exception):
        packet_common.assert_prefix_address_family(mkp("1.2.3.0/24"), 999)
    # Passing the wrong prefix type to the Route constructor asserts
    with pytest.raises(Exception):
        _rte = route.Route("1.2.3.0/24", N, [])
    # Passing the wrong prefix type to get_route asserts
    with pytest.raises(Exception):
        _rte = route_table.get_route("1.2.3.0/24", N)
    # Passing the wrong prefix type to del_route asserts
    with pytest.raises(Exception):
        _rte = route_table.del_route("1.2.3.0/24", N)
    # The address family of the route must match the address family of the table
    with pytest.raises(Exception):
        route_table.put_route(mkr("1111:1111:1111:1111:0000:0000:0000:0000/64", N))

def test_all_routes():
    packet_common.add_missing_methods_to_thrift()
    route_table = mkrt(constants.ADDRESS_FAMILY_IPV4)
    # Use all_routes generator to walk empty table
    generator = route_table.all_routes()
    with pytest.raises(Exception):
        next(generator)
    # Add some routes to the table (purposely in the wrong order)
    route_table.put_route(mkr("2.2.2.0/24", N))
    route_table.put_route(mkr("1.1.1.0/24", N))
    route_table.put_route(mkr("0.0.0.0/0", S))
    route_table.put_route(mkr("1.1.1.0/24", S))
    route_table.put_route(mkr("2.2.0.0/16", S))
    # Use the generator to visit all routes
    generator = route_table.all_routes()
    rte = next(generator)
    assert rte.prefix == mkp("0.0.0.0/0")
    assert rte.owner == S
    rte = next(generator)
    assert rte.prefix == mkp("1.1.1.0/24")
    assert rte.owner == S
    rte = next(generator)
    assert rte.prefix == mkp("1.1.1.0/24")
    assert rte.owner == N
    rte = next(generator)
    assert rte.prefix == mkp("2.2.0.0/16")
    assert rte.owner == S
    rte = next(generator)
    assert rte.prefix == mkp("2.2.2.0/24")
    assert rte.owner == N
    with pytest.raises(Exception):
        next(generator)

def test_all_prefix_routes():
    packet_common.add_missing_methods_to_thrift()
    route_table = mkrt(constants.ADDRESS_FAMILY_IPV4)
    # Use all_routes generator to walk empty table
    generator = route_table.all_prefix_routes(mkp("1.2.3.4/32"))
    with pytest.raises(Exception):
        next(generator)
    # Add some routes to the table (purposely in the wrong order)
    route_table.put_route(mkr("2.2.2.0/24", N))
    route_table.put_route(mkr("1.1.1.0/24", N))
    route_table.put_route(mkr("0.0.0.0/0", S))
    route_table.put_route(mkr("1.1.1.0/24", S))
    route_table.put_route(mkr("2.2.0.0/16", S))
    # Use the generator to visit all routes for prefix 3.3.0.0/16 (there are none)
    generator = route_table.all_prefix_routes(mkp("3.3.0.0/16"))
    with pytest.raises(Exception):
        next(generator)
    # Use the generator to visit all routes for prefix 2.2.0.0/16 (there is one)
    generator = route_table.all_prefix_routes(mkp("2.2.0.0/16"))
    rte = next(generator)
    assert rte.prefix == mkp("2.2.0.0/16")
    assert rte.owner == S
    with pytest.raises(Exception):
        next(generator)
    # Use the generator to visit all routes for prefix 1.1.1.0/24 (there are two)
    generator = route_table.all_prefix_routes(mkp("1.1.1.0/24"))
    rte = next(generator)
    assert rte.prefix == mkp("1.1.1.0/24")
    assert rte.owner == S
    rte = next(generator)
    assert rte.prefix == mkp("1.1.1.0/24")
    assert rte.owner == N
    with pytest.raises(Exception):
        next(generator)

def test_cli_table():
    packet_common.add_missing_methods_to_thrift()
    route_table = mkrt(constants.ADDRESS_FAMILY_IPV4)
    nh1 = mknh("if1", "1.1.1.1")
    nh2 = mknh("if2", "2.2.2.2")
    nh3 = mknh("if3", None)
    route_table.put_route(mkr("2.2.2.0/24", N))
    route_table.put_route(mkr("1.1.1.0/24", S, [nh1]))
    route_table.put_route(mkr("0.0.0.0/0", S, [nh1, nh2]))
    route_table.put_route(mkr("2.2.0.0/16", S, [nh3]))
    route_table.put_route(mkr("1.1.1.0/24", N))
    tab_str = route_table.cli_table().to_string()
    assert (tab_str == "+------------+-----------+-------------+\n"
                       "| Prefix     | Owner     | Next-hops   |\n"
                       "+------------+-----------+-------------+\n"
                       "| 0.0.0.0/0  | South SPF | if1 1.1.1.1 |\n"
                       "|            |           | if2 2.2.2.2 |\n"
                       "+------------+-----------+-------------+\n"
                       "| 1.1.1.0/24 | South SPF | if1 1.1.1.1 |\n"
                       "+------------+-----------+-------------+\n"
                       "| 1.1.1.0/24 | North SPF |             |\n"
                       "+------------+-----------+-------------+\n"
                       "| 2.2.0.0/16 | South SPF | if3         |\n"
                       "+------------+-----------+-------------+\n"
                       "| 2.2.2.0/24 | North SPF |             |\n"
                       "+------------+-----------+-------------+\n")

def test_mark_and_del_stale():
    packet_common.add_missing_methods_to_thrift()
    route_table = mkrt(constants.ADDRESS_FAMILY_IPV4)
    # Mark all S routes stale on an empty table
    assert route_table.mark_owner_routes_stale(S) == 0
    # Delete all remaining stale routes (which there are none)
    assert route_table.del_stale_routes() == 0
    # Prepare a route table with a mixture of N and S routes
    route_table.put_route(mkr("0.0.0.0/0", S))
    route_table.put_route(mkr("1.1.1.0/24", S))
    route_table.put_route(mkr("1.1.1.0/24", N))
    route_table.put_route(mkr("2.2.0.0/16", S))
    route_table.put_route(mkr("2.2.2.0/24", N))
    # Mark all N routes stale
    assert route_table.mark_owner_routes_stale(N) == 2
    # Overwrite an existing routes that was marked stale
    route_table.put_route(mkr("1.1.1.0/24", N))
    # Overwrite an existing routes that was not marked stale
    route_table.put_route(mkr("2.2.0.0/16", S))
    # Add a new route
    route_table.put_route(mkr("3.3.0.0/16", N))
    # Delete the one remaining stale route
    assert route_table.del_stale_routes() == 1
