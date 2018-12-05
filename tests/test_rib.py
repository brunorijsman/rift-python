import pytest

import packet_common
import rib

# A bunch of helper constants and functions to make the test code more compact and easier to read

N = rib.OWNER_N_SPF
S = rib.OWNER_S_SPF

def mkp(prefix_str):
    if ":" in prefix_str:
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

def test_ipv4_table_del_route():
    packet_common.add_missing_methods_to_thrift()
    table = rib.Table(rib.ADDRESS_FAMILY_IPV4)
    # Try to delete a route that is not present in the table (empty table)
    assert not table.del_route(mkp("1.1.1.0/24"), S)
    # Try to delete a route that is not present in the table (prefix is not present)
    table.put_route(mkr("2.2.2.0/32", S))
    assert not table.del_route(mkp("3.3.3.0/24"), S)
    # Try to delete a route that is not present in the table (prefix length is wrong)
    assert not table.del_route(mkp("2.2.2.0/24"), S)
    # Try to delete a route that is not present in the table (owner is not present)
    assert not table.del_route(mkp("2.2.2.0/32"), N)
    # Delete a route that is present in the table (only route for prefix)
    assert table.get_route(mkp("2.2.2.0/32"), S) is not None
    assert table.del_route(mkp("2.2.2.0/32"), S)
    assert table.get_route(mkp("2.2.2.0/32"), S) is None
    # Put the deleted route back and add other routes to the table
    table.put_route(mkr("1.1.0.0/16", N))
    table.put_route(mkr("2.2.2.0/32", S))
    table.put_route(mkr("2.2.2.0/32", N))
    table.put_route(mkr("2.2.2.0/24", N))
    table.put_route(mkr("3.0.0.0/8", S))
    # Delete a route that is present in the table (multiple routes for prefix, get most preferred)
    assert table.get_route(mkp("2.2.2.0/32"), S) is not None
    assert table.del_route(mkp("2.2.2.0/32"), S)
    assert table.get_route(mkp("2.2.2.0/32"), S) is None
    table.put_route(mkr("2.2.2.0/32", S))
    # Delete a route that is present in the table (multiple routes for prefix, get least preferred)
    assert table.get_route(mkp("2.2.2.0/32"), N) is not None
    assert table.del_route(mkp("2.2.2.0/32"), N)
    assert table.get_route(mkp("2.2.2.0/32"), N) is None
    table.put_route(mkr("2.2.2.0/32", N))

def test_ipv6_table_put_route():
    packet_common.add_missing_methods_to_thrift()
    table = rib.Table(rib.ADDRESS_FAMILY_IPV6)
    # Add a route
    table.put_route(mkr("1111:1111:1111:1111:0000:0000:0000:0000/64", N))
    # Add two routes with same prefix but with different owners (most preferred added first)
    table.put_route(mkr("2222:2222:2222:2222:2222:2222:2222:2222/128", S))
    table.put_route(mkr("2222:2222:2222:2222:2222:2222:2222:2222/128", N))
    # Add two routes with same prefix but with different owners (most preferred added last)
    table.put_route(mkr("3333:3333:3333:3333:3333:0000:0000:0000/80", N))
    table.put_route(mkr("3333:3333:3333:3333:3333:0000:0000:0000/80", S))
    # Replace route which is already in the table (only one route to prefix)
    table.put_route(mkr("4444::/16", N))
    table.put_route(mkr("4444::/16", N))
    # Replace route which is already in the table (multiple routes to prefix)
    table.put_route(mkr("::0.0.0.0/0", S))
    table.put_route(mkr("::0.0.0.0/0", N))
    table.put_route(mkr("::0.0.0.0/0", N))

def test_ipv6_table_get_route():
    packet_common.add_missing_methods_to_thrift()
    table = rib.Table(rib.ADDRESS_FAMILY_IPV6)
    # Try to get a route that is not present in the table (empty table)
    assert table.get_route(mkp("1111:1111:1111:1111:0000:0000:0000:0000/64"), S) is None
    # Try to get a route that is not present in the table (prefix is not present)
    table.put_route(mkr("2222:2222:2222:2222:2222:2222:2222:2222/128", S))
    assert table.get_route(mkp("3333:3333:3333:3333:3333:0000:0000:0000/80"), S) is None
    # Try to get a route that is not present in the table (prefix length is wrong)
    assert table.get_route(mkp("2222:2222:2222:2222:2222:2222:2222:0000/112"), S) is None
    # Try to get a route that is not present in the table (owner is not present)
    assert table.get_route(mkp("2222:2222:2222:2222:2222:2222:2222:2222/128"), N) is None
    # Get a route that is present in the table (only route for prefix)
    route = table.get_route(mkp("2222:2222:2222:2222:2222:2222:2222:2222/128"), S)
    assert route is not None
    assert route.prefix == mkp("2222:2222:2222:2222:2222:2222:2222:2222/128")
    assert route.owner == S
    # Add other routes to the table
    table.put_route(mkr("1111:1111::/32", N))
    table.put_route(mkr("2222:2222:2222:2222:2222:2222:2222:2222/128", N))
    table.put_route(mkr("2222:2222:2222::/48", N))
    table.put_route(mkr("3333::/16", S))
    # Get a route that is present in the table (multiple routes for prefix, get most preferred)
    route = table.get_route(mkp("2222:2222:2222:2222:2222:2222:2222:2222/128"), S)
    assert route is not None
    assert route.prefix == mkp("2222:2222:2222:2222:2222:2222:2222:2222/128")
    assert route.owner == S
    # Get a route that is present in the table (multiple routes for prefix, get least preferred)
    route = table.get_route(mkp("2222:2222:2222:2222:2222:2222:2222:2222/128"), N)
    assert route is not None
    assert route.prefix == mkp("2222:2222:2222:2222:2222:2222:2222:2222/128")
    assert route.owner == N

def test_ipv6_table_del_route():
    packet_common.add_missing_methods_to_thrift()
    table = rib.Table(rib.ADDRESS_FAMILY_IPV6)
    # Try to delete a route that is not present in the table (empty table)
    assert not table.del_route(mkp("1111:1111:1111::/48"), S)
    # Try to delete a route that is not present in the table (prefix is not present)
    table.put_route(mkr("2222::/16", S))
    assert not table.del_route(mkp("3333:3333:3333:3333:3333:0000:0000:0000/80"), S)
    # Try to delete a route that is not present in the table (prefix length is wrong)
    assert not table.del_route(mkp("2222:2222::/32"), S)
    # Try to delete a route that is not present in the table (owner is not present)
    assert not table.del_route(mkp("2222::/16"), N)
    # Delete a route that is present in the table (only route for prefix)
    assert table.get_route(mkp("2222::/16"), S) is not None
    assert table.del_route(mkp("2222::/16"), S)
    assert table.get_route(mkp("2222::/16"), S) is None
    # Put the deleted route back and add other routes to the table
    table.put_route(mkr("::/0", N))
    table.put_route(mkr("2222::/16", N))
    table.put_route(mkr("2222::/16", S))
    table.put_route(mkr("2222:2222::/32", N))
    table.put_route(mkr("3333:3333:3333:3333:3333:0000:0000:0000/80", S))
    table.put_route(mkr("3333:3333:3333:3333:3333:3333:3333:3333/128", S))
    # Delete a route that is present in the table (multiple routes for prefix, get most preferred)
    assert table.get_route(mkp("2222::/16"), S) is not None
    assert table.del_route(mkp("2222::/16"), S)
    assert table.get_route(mkp("2222::/16"), S) is None
    table.put_route(mkr("2222::/16", S))
    # Delete a route that is present in the table (multiple routes for prefix, get least preferred)
    assert table.get_route(mkp("2222::/16"), N) is not None
    assert table.del_route(mkp("2222::/16"), N)
    assert table.get_route(mkp("2222::/16"), N) is None
    table.put_route(mkr("2222::/16", N))

def test_asserts():
    packet_common.add_missing_methods_to_thrift()
    table = rib.Table(rib.ADDRESS_FAMILY_IPV4)
    # Passing the wrong prefix type to assert_prefix_address_family asserts
    with pytest.raises(Exception):
        rib.assert_prefix_address_family("1.2.3.0/24", rib.ADDRESS_FAMILY_IPV4)
    with pytest.raises(Exception):
        rib.assert_prefix_address_family(mkp("1.2.3.0/24"), rib.ADDRESS_FAMILY_IPV6)
    with pytest.raises(Exception):
        rib.assert_prefix_address_family(mkp("::1.2.3.0/24"), rib.ADDRESS_FAMILY_IPV4)
    with pytest.raises(Exception):
        rib.assert_prefix_address_family(mkp("1.2.3.0/24"), 999)
    # Passing the wrong prefix type to the Route constructor asserts
    with pytest.raises(Exception):
        _route = rib.Route("1.2.3.0/24", N)
    # Passing the wrong prefix type to get_route asserts
    with pytest.raises(Exception):
        _route = table.get_route("1.2.3.0/24", N)
    # Passing the wrong prefix type to del_route asserts
    with pytest.raises(Exception):
        _route = table.del_route("1.2.3.0/24", N)
    # The address family of the route must match the address family of the table
    with pytest.raises(Exception):
        table.put_route(mkr("1111:1111:1111:1111:0000:0000:0000:0000/64", N))
