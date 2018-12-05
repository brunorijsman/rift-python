import packet_common
import rib

# A bunch of helper constants and functions to make the test code more compact and easier to read

N = rib.OWNER_N_SPF
S = rib.OWNER_S_SPF

def mkp(prefix_str):
    if "::" in prefix_str:
        return packet_common.make_ipv6_prefix(prefix_str)
    else:
        return packet_common.make_ipv4_prefix(prefix_str)

def mkr(prefix_str, owner):
    return rib.Route(mkp(prefix_str), owner)

def test_ipv4_table_put_route():
    packet_common.add_missing_methods_to_thrift()
    table = rib.Table(rib.ADDRESS_FAMILY_IPV4)
    # Add a route
    table.put_route(mkr("1.1.1.0/24", N))
    # Add two routes with same prefix but with different owners (most preferred added first)
    table.put_route(mkr("2.2.2.2/32", S))
    table.put_route(mkr("2.2.2.2/32", N))
    # Add two routes with same prefix but with different owners (most preferred added last)
    table.put_route(mkr("3.3.3.0/24", N))
    table.put_route(mkr("3.3.3.0/24", S))
    # Replace route which is already in the table (only one route to prefix)
    table.put_route(mkr("4.4.4.0/30", N))
    table.put_route(mkr("4.4.4.0/30", N))
    # Replace route which is already in the table (multiple routes to prefix)
    table.put_route(mkr("0.0.0.0/0", S))
    table.put_route(mkr("0.0.0.0/0", N))
    table.put_route(mkr("0.0.0.0/0", N))

def test_ipv4_table_get_route():
    packet_common.add_missing_methods_to_thrift()
    table = rib.Table(rib.ADDRESS_FAMILY_IPV4)
    # Try to get a route that is not present in the table (empty table)
    assert table.get_route(mkp("1.1.1.0/24"), S) is None
    # Try to get a route that is not present in the table (prefix is not present)
    table.put_route(mkr("2.2.2.0/32", S))
    assert table.get_route(mkp("3.3.3.0/24"), S) is None
    # Try to get a route that is not present in the table (prefix length is wrong)
    assert table.get_route(mkp("2.2.2.0/24"), S) is None
    # Try to get a route that is not present in the table (owner is not present)
    assert table.get_route(mkp("2.2.2.0/32"), N) is None
    # Get a route that is present in the table (only route for prefix)
    route = table.get_route(mkp("2.2.2.0/32"), S)
    assert route is not None
    assert route.prefix == mkp("2.2.2.0/32")
    assert route.owner == S
    # Add other routes to the table
    table.put_route(mkr("1.1.0.0/16", N))
    table.put_route(mkr("2.2.2.0/32", N))
    table.put_route(mkr("2.2.2.0/24", N))
    table.put_route(mkr("3.0.0.0/8", S))
    # Get a route that is present in the table (multiple routes for prefix, get most preferred)
    route = table.get_route(mkp("2.2.2.0/32"), S)
    assert route is not None
    assert route.prefix == mkp("2.2.2.0/32")
    assert route.owner == S
    # Get a route that is present in the table (multiple routes for prefix, get least preferred)
    route = table.get_route(mkp("2.2.2.0/32"), N)
    assert route is not None
    assert route.prefix == mkp("2.2.2.0/32")
    assert route.owner == N
