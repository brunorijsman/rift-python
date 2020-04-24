import constants
import fib
import next_hop
import packet_common
import rib
import rib_route

# pylint: disable=invalid-name,too-many-statements

# Some helper constants and functions to make the test code more compact and easier to read
N = constants.OWNER_N_SPF
S = constants.OWNER_S_SPF


def mkrt(address_family):
    forwarding_table = fib.ForwardingTable(address_family, kernel=None, log=None, log_id="")
    route_table = rib.RouteTable(address_family, forwarding_table, log=None, log_id="")
    return route_table


def mkp(prefix_str):
    return packet_common.make_ip_prefix(prefix_str)


def mkr(prefix_str, owner, next_hops=None, neg_next_hops=None):
    if neg_next_hops is None:
        neg_next_hops = []
    if next_hops is None:
        next_hops = []
    return rib_route.RibRoute(mkp(prefix_str), owner, next_hops, neg_next_hops)


def mknh(interface_str, address_str):
    if address_str is None:
        address = None
    else:
        address = packet_common.make_ip_address(address_str)
    return next_hop.NextHop(interface_str, address)


DEFAULT_PREFIX = "0.0.0.0/0"
DEFAULT_NEXT_HOPS = [mknh('if0', "10.0.0.1"), mknh("if1", "10.0.0.2"), mknh("if2", "10.0.0.3"),
                     mknh("if3", "10.0.0.4")]

FIRST_NEG_DISAGG_PREFIX = "10.0.0.0/16"
FIRST_NEG_DISAGG_NEXT_HOPS = [mknh('if0', "10.0.0.1")]

SECOND_NEG_DISAGG_PREFIX = "10.1.0.0/16"
SECOND_NEG_DISAGG_NEXT_HOPS = [mknh("if3", "10.0.0.4")]

SUBNET_NEG_DISAGG_PREFIX = "10.0.10.0/24"
SUBNET_NEG_DISAGG_NEXT_HOPS = [mknh("if1", "10.0.0.2")]

UNREACHABLE_PREFIX = "200.0.0.0/16"
UNREACHABLE_NEXT_HOPS = [mknh('if0', "10.0.0.1"), mknh("if1", "10.0.0.2"),
                         mknh("if2", "10.0.0.3"), mknh("if3", "10.0.0.4")]

LEAF_PREFIX = "20.0.0.0/16"
LEAF_PREFIX_POS_NEXT_HOPS = [mknh("eth0", "10.0.1.1")]
LEAF_PREFIX_NEG_NEXT_HOPS = [mknh("eth1", "10.0.1.2")]


# Slide 55
def test_add_default_route():
    packet_common.add_missing_methods_to_thrift()
    r_t = mkrt(constants.ADDRESS_FAMILY_IPV4)
    default_route = mkr(DEFAULT_PREFIX, S, DEFAULT_NEXT_HOPS)
    r_t.put_route(default_route)
    assert r_t.destinations.get(DEFAULT_PREFIX).best_route == default_route
    assert r_t.destinations.get(DEFAULT_PREFIX).best_route.next_hops == \
           {mknh('if0', "10.0.0.1"), mknh("if1", "10.0.0.2"), mknh("if2", "10.0.0.3"),
            mknh("if3", "10.0.0.4")}
    assert set(r_t.fib.routes[mkp(DEFAULT_PREFIX)].next_hops) == default_route.next_hops


# Test slide 56 in Pascal's "negative disaggregation" presentation:
# Add a parent aggregate with positive nexthops and one child with a negative nexthop.
def test_add_negative_disaggregation():
    packet_common.add_missing_methods_to_thrift()
    r_t = mkrt(constants.ADDRESS_FAMILY_IPV4)
    # Install two routes into the RIB: one parent aggregate with four ECMP positive nexthops, and
    # one child more specific with one negative nexthop.
    default_route = mkr(DEFAULT_PREFIX, S, DEFAULT_NEXT_HOPS)
    r_t.put_route(default_route)
    first_neg_route = mkr(FIRST_NEG_DISAGG_PREFIX, S, [], FIRST_NEG_DISAGG_NEXT_HOPS)
    r_t.put_route(first_neg_route)
    assert r_t.destinations.get(FIRST_NEG_DISAGG_PREFIX).best_route == first_neg_route
    assert r_t.destinations.get(FIRST_NEG_DISAGG_PREFIX).best_route.positive_next_hops == set()
    assert r_t.destinations.get(FIRST_NEG_DISAGG_PREFIX).best_route.negative_next_hops == \
           set(FIRST_NEG_DISAGG_NEXT_HOPS)
    assert r_t.destinations.get(FIRST_NEG_DISAGG_PREFIX).best_route.next_hops == \
           {mknh("if1", "10.0.0.2"), mknh("if2", "10.0.0.3"), mknh("if3", "10.0.0.4")}
    assert set(r_t.fib.routes[mkp(FIRST_NEG_DISAGG_PREFIX)].next_hops) == \
           first_neg_route.next_hops


# Test slide 57 in Pascal's "negative disaggregation" presentation:
# Add a parent aggregate with positive nexthops and two children with negative nexthops.
def test_add_two_negative_disaggregation():
    packet_common.add_missing_methods_to_thrift()
    r_t = mkrt(constants.ADDRESS_FAMILY_IPV4)
    default_route = mkr(DEFAULT_PREFIX, S, DEFAULT_NEXT_HOPS)
    r_t.put_route(default_route)
    first_neg_route = mkr(FIRST_NEG_DISAGG_PREFIX, S, [], FIRST_NEG_DISAGG_NEXT_HOPS)
    r_t.put_route(first_neg_route)
    second_neg_route = mkr(SECOND_NEG_DISAGG_PREFIX, S, [], SECOND_NEG_DISAGG_NEXT_HOPS)
    r_t.put_route(second_neg_route)
    assert r_t.destinations.get(SECOND_NEG_DISAGG_PREFIX).best_route == second_neg_route
    assert r_t.destinations.get(
        SECOND_NEG_DISAGG_PREFIX).best_route.positive_next_hops == set()
    assert r_t.destinations.get(SECOND_NEG_DISAGG_PREFIX).best_route.negative_next_hops == \
           {mknh("if3", "10.0.0.4")}
    assert r_t.destinations.get(SECOND_NEG_DISAGG_PREFIX).best_route.next_hops == \
           {mknh('if0', "10.0.0.1"), mknh("if1", "10.0.0.2"), mknh("if2", "10.0.0.3")}
    assert set(r_t.fib.routes[mkp(SECOND_NEG_DISAGG_PREFIX)].next_hops) == \
           second_neg_route.next_hops


# Test slide 58 in Pascal's "negative disaggregation" presentation.
# Delete a nexthop from a parent route, and check that the computed complementary nexthops in
# the child routes are properly updated.
def test_remove_default_next_hop():
    packet_common.add_missing_methods_to_thrift()
    r_t = mkrt(constants.ADDRESS_FAMILY_IPV4)
    default_route = mkr(DEFAULT_PREFIX, S, DEFAULT_NEXT_HOPS)
    r_t.put_route(default_route)
    first_neg_route = mkr(FIRST_NEG_DISAGG_PREFIX, S, [], FIRST_NEG_DISAGG_NEXT_HOPS)
    r_t.put_route(first_neg_route)
    second_neg_route = mkr(SECOND_NEG_DISAGG_PREFIX, S, [], SECOND_NEG_DISAGG_NEXT_HOPS)
    r_t.put_route(second_neg_route)
    default_route_fail = mkr(DEFAULT_PREFIX, S, [mknh('if0', "10.0.0.1"), mknh("if2", "10.0.0.3"),
                                                 mknh("if3", "10.0.0.4")])
    r_t.put_route(default_route_fail)
    # Test for default
    assert r_t.destinations.get(DEFAULT_PREFIX).best_route == default_route_fail
    assert r_t.destinations.get(DEFAULT_PREFIX).best_route.positive_next_hops == \
           {mknh('if0', "10.0.0.1"), mknh("if2", "10.0.0.3"), mknh("if3", "10.0.0.4")}
    assert r_t.destinations.get(DEFAULT_PREFIX).best_route.negative_next_hops == set()
    assert r_t.destinations.get(DEFAULT_PREFIX).best_route.next_hops == \
           {mknh('if0', "10.0.0.1"), mknh("if2", "10.0.0.3"), mknh("if3", "10.0.0.4")}
    assert set(r_t.fib.routes[mkp(DEFAULT_PREFIX)].next_hops) == default_route_fail.next_hops
    # Test for 10.0.0.0/16
    assert r_t.destinations.get(FIRST_NEG_DISAGG_PREFIX).best_route.positive_next_hops == set()
    assert r_t.destinations.get(FIRST_NEG_DISAGG_PREFIX).best_route.negative_next_hops == \
           {mknh('if0', "10.0.0.1")}
    assert r_t.destinations.get(FIRST_NEG_DISAGG_PREFIX).best_route.next_hops == \
           {mknh("if2", "10.0.0.3"), mknh("if3", "10.0.0.4")}
    assert set(r_t.fib.routes[mkp(FIRST_NEG_DISAGG_PREFIX)].next_hops) == \
           first_neg_route.next_hops
    # Test for 10.1.0.0/16
    assert r_t.destinations.get(SECOND_NEG_DISAGG_PREFIX).best_route.positive_next_hops == \
           set()
    assert r_t.destinations.get(SECOND_NEG_DISAGG_PREFIX).best_route.negative_next_hops == \
           {mknh("if3", "10.0.0.4")}
    assert r_t.destinations.get(SECOND_NEG_DISAGG_PREFIX).best_route.next_hops == \
           {mknh('if0', "10.0.0.1"), mknh("if2", "10.0.0.3")}
    assert set(r_t.fib.routes[mkp(SECOND_NEG_DISAGG_PREFIX)].next_hops) == \
           second_neg_route.next_hops


# Test slides 59 in Pascal's "negative disaggregation" presentation.
# Delete a nexthop from a parent route, and check that the computed complementary nexthops in
# the child route and the grandchild route.
def test_add_subnet_disagg_to_first_negative_disagg():
    packet_common.add_missing_methods_to_thrift()
    r_t = mkrt(constants.ADDRESS_FAMILY_IPV4)
    default_route = mkr(DEFAULT_PREFIX, S, DEFAULT_NEXT_HOPS)
    r_t.put_route(default_route)
    first_neg_route = mkr(FIRST_NEG_DISAGG_PREFIX, S, [], FIRST_NEG_DISAGG_NEXT_HOPS)
    r_t.put_route(first_neg_route)
    subnet_disagg_route = mkr(SUBNET_NEG_DISAGG_PREFIX, S, [], SUBNET_NEG_DISAGG_NEXT_HOPS)
    r_t.put_route(subnet_disagg_route)
    assert r_t.destinations.get(SUBNET_NEG_DISAGG_PREFIX).best_route.positive_next_hops == set()
    assert r_t.destinations.get(SUBNET_NEG_DISAGG_PREFIX).best_route.negative_next_hops == \
           {mknh("if1", "10.0.0.2")}
    assert r_t.destinations.get(SUBNET_NEG_DISAGG_PREFIX).best_route.next_hops == \
           {mknh("if2", "10.0.0.3"), mknh("if3", "10.0.0.4")}
    assert set(
        r_t.fib.routes[mkp(SUBNET_NEG_DISAGG_PREFIX)].next_hops) == subnet_disagg_route.next_hops


# Test slide 60 in Pascal's "negative disaggregation" presentation.
# Delete a nexthop from a parent route, and check that the computed complementary nexthops in
# the child routes are recursively updated.
def test_remove_default_next_hop_with_subnet_disagg():
    packet_common.add_missing_methods_to_thrift()
    r_t = mkrt(constants.ADDRESS_FAMILY_IPV4)
    default_route = mkr(DEFAULT_PREFIX, S, DEFAULT_NEXT_HOPS)
    r_t.put_route(default_route)
    first_neg_route = mkr(FIRST_NEG_DISAGG_PREFIX, S, [], FIRST_NEG_DISAGG_NEXT_HOPS)
    r_t.put_route(first_neg_route)
    subnet_disagg_route = mkr(SUBNET_NEG_DISAGG_PREFIX, S, [], SUBNET_NEG_DISAGG_NEXT_HOPS)
    r_t.put_route(subnet_disagg_route)
    default_route_fail = mkr(DEFAULT_PREFIX, S, [mknh('if0', "10.0.0.1"), mknh("if1", "10.0.0.2"),
                                                 mknh("if3", "10.0.0.4")])
    r_t.put_route(default_route_fail)
    # Test for default
    assert r_t.destinations.get(DEFAULT_PREFIX).best_route == default_route_fail
    assert r_t.destinations.get(DEFAULT_PREFIX).best_route.positive_next_hops == \
           {mknh('if0', "10.0.0.1"), mknh("if1", "10.0.0.2"), mknh("if3", "10.0.0.4")}
    assert r_t.destinations.get(DEFAULT_PREFIX).best_route.negative_next_hops == set()
    assert r_t.destinations.get(DEFAULT_PREFIX).best_route.next_hops == \
           {mknh('if0', "10.0.0.1"), mknh("if1", "10.0.0.2"), mknh("if3", "10.0.0.4")}
    assert set(r_t.fib.routes[mkp(DEFAULT_PREFIX)].next_hops) == default_route_fail.next_hops
    # Test for 10.0.0.0/16
    assert r_t.destinations.get(FIRST_NEG_DISAGG_PREFIX).best_route.positive_next_hops == set()
    assert r_t.destinations.get(FIRST_NEG_DISAGG_PREFIX).best_route.negative_next_hops == \
           {mknh('if0', "10.0.0.1")}
    assert r_t.destinations.get(FIRST_NEG_DISAGG_PREFIX).best_route.next_hops == \
           {mknh("if1", "10.0.0.2"), mknh("if3", "10.0.0.4")}
    assert set(r_t.fib.routes[mkp(FIRST_NEG_DISAGG_PREFIX)].next_hops) == \
           first_neg_route.next_hops
    # Test for 10.0.10.0/24
    assert r_t.destinations.get(SUBNET_NEG_DISAGG_PREFIX).best_route.positive_next_hops == set()
    assert r_t.destinations.get(SUBNET_NEG_DISAGG_PREFIX).best_route.negative_next_hops == \
           {mknh("if1", "10.0.0.2")}
    assert r_t.destinations.get(SUBNET_NEG_DISAGG_PREFIX).best_route.next_hops == \
           {mknh("if3", "10.0.0.4")}
    assert set(
        r_t.fib.routes[mkp(SUBNET_NEG_DISAGG_PREFIX)].next_hops) == subnet_disagg_route.next_hops


# Slide 60 and recover of the failed next hops
def test_recover_default_next_hop_with_subnet_disagg():
    packet_common.add_missing_methods_to_thrift()
    r_t = mkrt(constants.ADDRESS_FAMILY_IPV4)
    default_route = mkr(DEFAULT_PREFIX, S, DEFAULT_NEXT_HOPS)
    r_t.put_route(default_route)
    first_neg_route = mkr(FIRST_NEG_DISAGG_PREFIX, S, [], FIRST_NEG_DISAGG_NEXT_HOPS)
    r_t.put_route(first_neg_route)
    subnet_disagg_route = mkr(SUBNET_NEG_DISAGG_PREFIX, S, [], SUBNET_NEG_DISAGG_NEXT_HOPS)
    r_t.put_route(subnet_disagg_route)
    default_route_fail = mkr(DEFAULT_PREFIX, S, [mknh('if0', "10.0.0.1"), mknh("if1", "10.0.0.2"),
                                                 mknh("if3", "10.0.0.4")])
    r_t.put_route(default_route_fail)
    default_route_recover = mkr(DEFAULT_PREFIX, S, DEFAULT_NEXT_HOPS)
    r_t.put_route(default_route_recover)
    # Test for default
    assert r_t.destinations.get(DEFAULT_PREFIX).best_route == default_route_recover
    assert r_t.destinations.get(DEFAULT_PREFIX).best_route.positive_next_hops == \
           set(DEFAULT_NEXT_HOPS)
    assert r_t.destinations.get(DEFAULT_PREFIX).best_route.negative_next_hops == set()
    assert r_t.destinations.get(DEFAULT_PREFIX).best_route.next_hops == set(DEFAULT_NEXT_HOPS)
    assert set(r_t.fib.routes[mkp(DEFAULT_PREFIX)].next_hops) == default_route_recover.next_hops
    # Test for 10.0.0.0/16
    assert r_t.destinations.get(FIRST_NEG_DISAGG_PREFIX).best_route.positive_next_hops == set()
    assert r_t.destinations.get(FIRST_NEG_DISAGG_PREFIX).best_route.negative_next_hops == \
           {mknh('if0', "10.0.0.1")}
    assert r_t.destinations.get(FIRST_NEG_DISAGG_PREFIX).best_route.next_hops == \
           {mknh("if1", "10.0.0.2"), mknh("if2", "10.0.0.3"), mknh("if3", "10.0.0.4")}
    assert set(r_t.fib.routes[mkp(FIRST_NEG_DISAGG_PREFIX)].next_hops) == \
           first_neg_route.next_hops
    # Test for 10.0.10.0/24
    assert r_t.destinations.get(SUBNET_NEG_DISAGG_PREFIX).best_route.positive_next_hops == set()
    assert r_t.destinations.get(SUBNET_NEG_DISAGG_PREFIX).best_route.negative_next_hops == \
           {mknh("if1", "10.0.0.2")}
    assert r_t.destinations.get(SUBNET_NEG_DISAGG_PREFIX).best_route.next_hops == \
           {mknh("if2", "10.0.0.3"), mknh("if3", "10.0.0.4")}
    assert set(
        r_t.fib.routes[mkp(SUBNET_NEG_DISAGG_PREFIX)].next_hops) == subnet_disagg_route.next_hops


def test_remove_default_route():
    packet_common.add_missing_methods_to_thrift()
    r_t = mkrt(constants.ADDRESS_FAMILY_IPV4)
    default_route = mkr(DEFAULT_PREFIX, S, DEFAULT_NEXT_HOPS)
    r_t.put_route(default_route)
    first_neg_route = mkr(FIRST_NEG_DISAGG_PREFIX, S, [], FIRST_NEG_DISAGG_NEXT_HOPS)
    r_t.put_route(first_neg_route)
    subnet_disagg_route = mkr(SUBNET_NEG_DISAGG_PREFIX, S, [], SUBNET_NEG_DISAGG_NEXT_HOPS)
    r_t.put_route(subnet_disagg_route)
    r_t.del_route(mkp(DEFAULT_PREFIX), S)
    # Test for default
    assert not r_t.destinations.has_key(DEFAULT_PREFIX)
    assert DEFAULT_PREFIX not in r_t.fib.routes
    # Test for 10.0.0.0/16
    assert r_t.destinations.get(FIRST_NEG_DISAGG_PREFIX).parent_prefix_dest is None
    assert r_t.destinations.get(FIRST_NEG_DISAGG_PREFIX).best_route.positive_next_hops == set()
    assert r_t.destinations.get(FIRST_NEG_DISAGG_PREFIX).best_route.negative_next_hops == \
           {mknh('if0', "10.0.0.1")}
    assert r_t.destinations.get(FIRST_NEG_DISAGG_PREFIX).best_route.next_hops == set()
    assert set(r_t.fib.routes[mkp(FIRST_NEG_DISAGG_PREFIX)].next_hops) == set()
    # Test for 10.0.10.0/24
    assert r_t.destinations.get(SUBNET_NEG_DISAGG_PREFIX).best_route.positive_next_hops == set()
    assert r_t.destinations.get(SUBNET_NEG_DISAGG_PREFIX).best_route.negative_next_hops == \
           {mknh("if1", "10.0.0.2")}
    assert r_t.destinations.get(SUBNET_NEG_DISAGG_PREFIX).best_route.next_hops == set()
    assert set(r_t.fib.routes[mkp(SUBNET_NEG_DISAGG_PREFIX)].next_hops) == set()


# Tests if a route becomes unreachable after all next hops are negatively disaggregated
def test_neg_disagg_fib_unreachable():
    packet_common.add_missing_methods_to_thrift()
    r_t = mkrt(constants.ADDRESS_FAMILY_IPV4)
    default_route = mkr(DEFAULT_PREFIX, S, DEFAULT_NEXT_HOPS)
    r_t.put_route(default_route)
    unreachable_route = mkr(UNREACHABLE_PREFIX, S, [], UNREACHABLE_NEXT_HOPS)
    r_t.put_route(unreachable_route)
    assert r_t.destinations.get(UNREACHABLE_PREFIX).best_route.positive_next_hops == set()
    assert r_t.destinations.get(UNREACHABLE_PREFIX).best_route.negative_next_hops == \
           {mknh('if0', "10.0.0.1"), mknh("if1", "10.0.0.2"), mknh("if2", "10.0.0.3"),
            mknh("if3", "10.0.0.4")}
    assert r_t.destinations.get(UNREACHABLE_PREFIX).best_route.next_hops == set()
    assert set(r_t.fib.routes[mkp(UNREACHABLE_PREFIX)].next_hops) == unreachable_route.next_hops


# Tests if an unreachable route becomes reachable after a negative disaggregation is removed
def test_neg_disagg_fib_unreachable_recover():
    packet_common.add_missing_methods_to_thrift()
    r_t = mkrt(constants.ADDRESS_FAMILY_IPV4)
    default_route = mkr(DEFAULT_PREFIX, S, DEFAULT_NEXT_HOPS)
    r_t.put_route(default_route)
    unreachable_route = mkr(UNREACHABLE_PREFIX, S, [], UNREACHABLE_NEXT_HOPS)
    r_t.put_route(unreachable_route)
    unreachable_route_recover = mkr(UNREACHABLE_PREFIX, S, [],
                                    [mknh('if0', "10.0.0.1"), mknh("if1", "10.0.0.2"),
                                     mknh("if3", "10.0.0.4")])
    r_t.put_route(unreachable_route_recover)
    assert r_t.destinations.get(UNREACHABLE_PREFIX).best_route.positive_next_hops == set()
    assert r_t.destinations.get(UNREACHABLE_PREFIX).best_route.negative_next_hops == \
           {mknh('if0', "10.0.0.1"), mknh("if1", "10.0.0.2"), mknh("if3", "10.0.0.4")}
    assert r_t.destinations.get(UNREACHABLE_PREFIX).best_route.next_hops == \
           {mknh("if2", "10.0.0.3")}
    assert set(
        r_t.fib.routes[mkp(UNREACHABLE_PREFIX)].next_hops) == unreachable_route_recover.next_hops


# Tests if a subnet of an unreachable route (negative disaggregated) is removed from the FIB
def test_add_subnet_disagg_recursive_unreachable():
    packet_common.add_missing_methods_to_thrift()
    r_t = mkrt(constants.ADDRESS_FAMILY_IPV4)
    default_route = mkr(DEFAULT_PREFIX, S, DEFAULT_NEXT_HOPS)
    r_t.put_route(default_route)
    first_neg_route = mkr(FIRST_NEG_DISAGG_PREFIX, S, [], FIRST_NEG_DISAGG_NEXT_HOPS)
    r_t.put_route(first_neg_route)
    subnet_disagg_route = mkr(SUBNET_NEG_DISAGG_PREFIX, S, [], SUBNET_NEG_DISAGG_NEXT_HOPS)
    r_t.put_route(subnet_disagg_route)
    first_neg_unreach = mkr(FIRST_NEG_DISAGG_PREFIX, S, [], UNREACHABLE_NEXT_HOPS)
    r_t.put_route(first_neg_unreach)
    assert r_t.destinations.get(FIRST_NEG_DISAGG_PREFIX).best_route.positive_next_hops == set()
    assert r_t.destinations.get(FIRST_NEG_DISAGG_PREFIX).best_route.negative_next_hops == \
           {mknh('if0', "10.0.0.1"), mknh("if1", "10.0.0.2"), mknh("if2", "10.0.0.3"),
            mknh("if3", "10.0.0.4")}
    assert r_t.destinations.get(FIRST_NEG_DISAGG_PREFIX).best_route.next_hops == set()
    assert set(r_t.fib.routes[mkp(FIRST_NEG_DISAGG_PREFIX)].next_hops) == \
           first_neg_unreach.next_hops
    assert not r_t.destinations.has_key(SUBNET_NEG_DISAGG_PREFIX)
    assert SUBNET_NEG_DISAGG_PREFIX not in r_t.fib.routes


# Slide 61 from the perspective of L3
def test_pos_neg_disagg():
    packet_common.add_missing_methods_to_thrift()
    r_t = mkrt(constants.ADDRESS_FAMILY_IPV4)
    default_route = mkr(DEFAULT_PREFIX, S, DEFAULT_NEXT_HOPS)
    r_t.put_route(default_route)
    leaf_route = mkr(LEAF_PREFIX, S, LEAF_PREFIX_POS_NEXT_HOPS,
                     LEAF_PREFIX_NEG_NEXT_HOPS)
    r_t.put_route(leaf_route)
    assert r_t.destinations.get(LEAF_PREFIX).best_route.positive_next_hops == \
           {mknh("eth0", "10.0.1.1")}
    assert r_t.destinations.get(LEAF_PREFIX).best_route.negative_next_hops == \
           {mknh("eth1", "10.0.1.2")}
    assert r_t.destinations.get(LEAF_PREFIX).best_route.next_hops == \
           {mknh("if3", "10.0.0.4"), mknh("if2", "10.0.0.3"), mknh("eth0", "10.0.1.1"),
            mknh("if1", "10.0.0.2"), mknh("if0", "10.0.0.1")}
    assert set(r_t.fib.routes[mkp(LEAF_PREFIX)].next_hops) == leaf_route.next_hops


# Given a prefix X with N negative next hops
# Given a prefix Y, subnet of X, with M negative next hops and a positive next hop L included in N
# Results that next hops of Y include L
def test_pos_neg_disagg_recursive():
    packet_common.add_missing_methods_to_thrift()
    r_t = mkrt(constants.ADDRESS_FAMILY_IPV4)
    default_route = mkr(DEFAULT_PREFIX, S, DEFAULT_NEXT_HOPS)
    r_t.put_route(default_route)
    first_neg_route = mkr(FIRST_NEG_DISAGG_PREFIX, S, [], FIRST_NEG_DISAGG_NEXT_HOPS)
    r_t.put_route(first_neg_route)
    subnet_disagg_route = mkr(SUBNET_NEG_DISAGG_PREFIX, S, [mknh("if0", "10.0.0.1")],
                              SUBNET_NEG_DISAGG_NEXT_HOPS)
    r_t.put_route(subnet_disagg_route)
    assert r_t.destinations.get(SUBNET_NEG_DISAGG_PREFIX).best_route.positive_next_hops == \
           {mknh("if0", "10.0.0.1")}
    assert r_t.destinations.get(SUBNET_NEG_DISAGG_PREFIX).best_route.negative_next_hops == \
           {mknh("if1", "10.0.0.2")}
    assert r_t.destinations.get(SUBNET_NEG_DISAGG_PREFIX).best_route.next_hops == \
           {mknh("if0", "10.0.0.1"), mknh("if2", "10.0.0.3"), mknh("if3", "10.0.0.4")}
    assert set(
        r_t.fib.routes[mkp(SUBNET_NEG_DISAGG_PREFIX)].next_hops) == subnet_disagg_route.next_hops


# Add two destination with different owner to the same destination,
# test that the S_SPF route is preferred
def test_add_two_route_same_destination():
    packet_common.add_missing_methods_to_thrift()
    r_t = mkrt(constants.ADDRESS_FAMILY_IPV4)
    default_route = mkr(DEFAULT_PREFIX, N, DEFAULT_NEXT_HOPS)
    r_t.put_route(default_route)
    best_default_route = mkr(DEFAULT_PREFIX, S, [mknh('if0', "10.0.0.1")])
    r_t.put_route(best_default_route)
    assert r_t.destinations.get(DEFAULT_PREFIX).best_route == best_default_route
    assert r_t.destinations.get(DEFAULT_PREFIX).best_route.positive_next_hops == \
           {mknh('if0', "10.0.0.1")}
    assert r_t.destinations.get(DEFAULT_PREFIX).best_route.negative_next_hops == set()
    assert r_t.destinations.get(DEFAULT_PREFIX).best_route.next_hops == \
           {mknh('if0', "10.0.0.1")}
    assert set(r_t.fib.routes[mkp(DEFAULT_PREFIX)].next_hops) == best_default_route.next_hops


# Add two destination with different owner to the same destination,
# then remove the best route (S_SPF), test that the S_SPF is now preferred
def test_remove_best_route():
    packet_common.add_missing_methods_to_thrift()
    r_t = mkrt(constants.ADDRESS_FAMILY_IPV4)
    default_route = mkr(DEFAULT_PREFIX, N, DEFAULT_NEXT_HOPS)
    r_t.put_route(default_route)
    r_t.del_route(mkp(DEFAULT_PREFIX), S)
    assert r_t.destinations.get(DEFAULT_PREFIX).best_route == default_route
    assert r_t.destinations.get(DEFAULT_PREFIX).best_route.positive_next_hops == \
           {mknh('if0', "10.0.0.1"), mknh("if1", "10.0.0.2"), mknh("if2", "10.0.0.3"),
            mknh("if3", "10.0.0.4")}
    assert r_t.destinations.get(DEFAULT_PREFIX).best_route.negative_next_hops == set()
    assert r_t.destinations.get(DEFAULT_PREFIX).best_route.next_hops == \
           {mknh('if0', "10.0.0.1"), mknh("if1", "10.0.0.2"), mknh("if2", "10.0.0.3"),
            mknh("if3", "10.0.0.4")}
    assert set(r_t.fib.routes[mkp(DEFAULT_PREFIX)].next_hops) == default_route.next_hops


# Add two destination with different owner to the same destination, test that the S_SPF route
# is preferred. Then add subnet destination and check that they inherits the preferred one
def test_add_two_route_same_destination_with_subnet():
    packet_common.add_missing_methods_to_thrift()
    r_t = mkrt(constants.ADDRESS_FAMILY_IPV4)
    default_route = mkr(DEFAULT_PREFIX, N, DEFAULT_NEXT_HOPS)
    r_t.put_route(default_route)
    best_default_route = mkr(DEFAULT_PREFIX, S,
                             [mknh("if0", "10.0.0.1"), mknh("if1", "10.0.0.2"),
                              mknh("if2", "10.0.0.3")])
    r_t.put_route(best_default_route)
    first_neg_route = mkr(FIRST_NEG_DISAGG_PREFIX, S, [], FIRST_NEG_DISAGG_NEXT_HOPS)
    r_t.put_route(first_neg_route)
    subnet_disagg_route = mkr(SUBNET_NEG_DISAGG_PREFIX, S, [], SUBNET_NEG_DISAGG_NEXT_HOPS)
    r_t.put_route(subnet_disagg_route)
    # Test for default
    assert r_t.destinations.get(DEFAULT_PREFIX).best_route == best_default_route
    assert r_t.destinations.get(DEFAULT_PREFIX).best_route.positive_next_hops == \
           {mknh('if0', "10.0.0.1"), mknh("if1", "10.0.0.2"), mknh("if2", "10.0.0.3")}
    assert r_t.destinations.get(DEFAULT_PREFIX).best_route.negative_next_hops == set()
    assert r_t.destinations.get(DEFAULT_PREFIX).best_route.next_hops == \
           {mknh('if0', "10.0.0.1"), mknh("if1", "10.0.0.2"), mknh("if2", "10.0.0.3")}
    assert set(r_t.fib.routes[mkp(DEFAULT_PREFIX)].next_hops) == best_default_route.next_hops
    # Test for 10.0.0.0/16
    assert r_t.destinations.get(FIRST_NEG_DISAGG_PREFIX).best_route == first_neg_route
    assert r_t.destinations.get(FIRST_NEG_DISAGG_PREFIX).best_route.positive_next_hops == set()
    assert r_t.destinations.get(FIRST_NEG_DISAGG_PREFIX).best_route.negative_next_hops == \
           {mknh('if0', "10.0.0.1")}
    assert r_t.destinations.get(FIRST_NEG_DISAGG_PREFIX).best_route.next_hops == {
        mknh("if1", "10.0.0.2"), mknh("if2", "10.0.0.3")}
    assert set(r_t.fib.routes[mkp(FIRST_NEG_DISAGG_PREFIX)].next_hops) == \
           first_neg_route.next_hops
    # Test for 10.0.10.0/24
    assert r_t.destinations.get(SUBNET_NEG_DISAGG_PREFIX).best_route == subnet_disagg_route
    assert r_t.destinations.get(SUBNET_NEG_DISAGG_PREFIX).best_route.positive_next_hops == set()
    assert r_t.destinations.get(SUBNET_NEG_DISAGG_PREFIX).best_route.negative_next_hops == \
           {mknh("if1", "10.0.0.2")}
    assert r_t.destinations.get(SUBNET_NEG_DISAGG_PREFIX).best_route.next_hops == \
           {mknh("if2", "10.0.0.3")}
    assert set(
        r_t.fib.routes[mkp(SUBNET_NEG_DISAGG_PREFIX)].next_hops) == subnet_disagg_route.next_hops


# Add two destination with different owner to the default destination,
# check that the S_SPF route is preferred. Then add subnet destination and check that they
# inherits the preferred one. Delete the best route from the default and check that the
# subnets changes consequently
def test_add_two_route_same_destination_with_subnet_and_remove_one():
    packet_common.add_missing_methods_to_thrift()
    r_t = mkrt(constants.ADDRESS_FAMILY_IPV4)
    default_route = mkr(DEFAULT_PREFIX, N, DEFAULT_NEXT_HOPS)
    r_t.put_route(default_route)
    best_default_route = mkr(DEFAULT_PREFIX, S,
                             [mknh("if0", "10.0.0.1"), mknh("if1", "10.0.0.2"),
                              mknh("if2", "10.0.0.3")])
    r_t.put_route(best_default_route)
    first_neg_route = mkr(FIRST_NEG_DISAGG_PREFIX, S, [], FIRST_NEG_DISAGG_NEXT_HOPS)
    r_t.put_route(first_neg_route)
    subnet_disagg_route = mkr(SUBNET_NEG_DISAGG_PREFIX, S, [], SUBNET_NEG_DISAGG_NEXT_HOPS)
    r_t.put_route(subnet_disagg_route)
    r_t.del_route(mkp(DEFAULT_PREFIX), S)
    # Test for default
    assert r_t.destinations.get(DEFAULT_PREFIX).best_route == default_route
    assert r_t.destinations.get(DEFAULT_PREFIX).best_route.positive_next_hops == \
           {mknh('if0', "10.0.0.1"), mknh("if1", "10.0.0.2"), mknh("if2", "10.0.0.3"),
            mknh("if3", "10.0.0.4")}
    assert r_t.destinations.get(DEFAULT_PREFIX).best_route.negative_next_hops == set()
    assert r_t.destinations.get(DEFAULT_PREFIX).best_route.next_hops == \
           {mknh('if0', "10.0.0.1"), mknh("if1", "10.0.0.2"), mknh("if2", "10.0.0.3"),
            mknh("if3", "10.0.0.4")}
    assert set(r_t.fib.routes[mkp(DEFAULT_PREFIX)].next_hops) == default_route.next_hops
    # Test for 10.0.0.0/16
    assert r_t.destinations.get(FIRST_NEG_DISAGG_PREFIX).best_route == first_neg_route
    assert r_t.destinations.get(FIRST_NEG_DISAGG_PREFIX).best_route.positive_next_hops == set()
    assert r_t.destinations.get(FIRST_NEG_DISAGG_PREFIX).best_route.negative_next_hops == \
           {mknh('if0', "10.0.0.1")}
    assert r_t.destinations.get(FIRST_NEG_DISAGG_PREFIX).best_route.next_hops == \
           {mknh("if1", "10.0.0.2"), mknh("if2", "10.0.0.3"), mknh("if3", "10.0.0.4")}
    assert set(r_t.fib.routes[mkp(FIRST_NEG_DISAGG_PREFIX)].next_hops) == \
           first_neg_route.next_hops
    # Test for 10.0.10.0/24
    assert r_t.destinations.get(SUBNET_NEG_DISAGG_PREFIX).best_route == subnet_disagg_route
    assert r_t.destinations.get(SUBNET_NEG_DISAGG_PREFIX).best_route.positive_next_hops == set()
    assert r_t.destinations.get(SUBNET_NEG_DISAGG_PREFIX).best_route.negative_next_hops == \
           {mknh("if1", "10.0.0.2")}
    assert r_t.destinations.get(SUBNET_NEG_DISAGG_PREFIX).best_route.next_hops == \
           {mknh("if2", "10.0.0.3"), mknh("if3", "10.0.0.4")}
    assert set(
        r_t.fib.routes[mkp(SUBNET_NEG_DISAGG_PREFIX)].next_hops) == subnet_disagg_route.next_hops


# Test that a subnet X that becomes equal to its parent destination is removed and that its
# child subnet Y changes the parent destination to the one of X
def test_remove_superfluous_subnet_recursive():
    packet_common.add_missing_methods_to_thrift()
    r_t = mkrt(constants.ADDRESS_FAMILY_IPV4)
    default_route = mkr(DEFAULT_PREFIX, S, DEFAULT_NEXT_HOPS)
    r_t.put_route(default_route)
    first_disagg_route = mkr(FIRST_NEG_DISAGG_PREFIX, S, [], FIRST_NEG_DISAGG_NEXT_HOPS)
    r_t.put_route(first_disagg_route)
    subnet_disagg_route = mkr(SUBNET_NEG_DISAGG_PREFIX, S, [], SUBNET_NEG_DISAGG_NEXT_HOPS)
    r_t.put_route(subnet_disagg_route)
    r_t.del_route(mkp(FIRST_NEG_DISAGG_PREFIX), S)
    assert not r_t.destinations.has_key(FIRST_NEG_DISAGG_PREFIX)
    assert FIRST_NEG_DISAGG_PREFIX not in r_t.fib.routes
    assert r_t.destinations.get(SUBNET_NEG_DISAGG_PREFIX).best_route.positive_next_hops == set()
    assert r_t.destinations.get(SUBNET_NEG_DISAGG_PREFIX).best_route.negative_next_hops == \
           {mknh("if1", "10.0.0.2")}
    assert r_t.destinations.get(SUBNET_NEG_DISAGG_PREFIX).best_route.next_hops == \
           {mknh('if0', "10.0.0.1"), mknh("if2", "10.0.0.3"), mknh("if3", "10.0.0.4")}
    assert set(
        r_t.fib.routes[mkp(SUBNET_NEG_DISAGG_PREFIX)].next_hops) == subnet_disagg_route.next_hops
    assert r_t.destinations.get(SUBNET_NEG_DISAGG_PREFIX).parent_prefix_dest == \
           r_t.destinations.get(DEFAULT_PREFIX)


# Deep nesting of more specific routes: parent, child, grand child, grand-grand child, ...
def test_prop_deep_nesting():
    packet_common.add_missing_methods_to_thrift()
    r_t = mkrt(constants.ADDRESS_FAMILY_IPV4)
    # Default route
    new_default_next_hops = [mknh('if0', "10.0.0.1"), mknh("if1", "10.0.0.2"),
                             mknh("if2", "10.0.0.3"), mknh("if3", "10.0.0.4"),
                             mknh("if4", "10.0.0.5")]
    new_default_route = mkr(DEFAULT_PREFIX, S, new_default_next_hops)
    r_t.put_route(new_default_route)
    # Child route
    child_prefix = '1.0.0.0/8'
    child_route = mkr(child_prefix, S, [], [mknh('if0', "10.0.0.1")])
    r_t.put_route(child_route)
    # Grand child route
    g_child_prefix = '1.128.0.0/9'
    g_child_route = mkr(g_child_prefix, S, [], [mknh("if1", "10.0.0.2")])
    r_t.put_route(g_child_route)
    # Grand-grand child route
    gg_child_prefix = '1.192.0.0/10'
    gg_child_route = mkr(gg_child_prefix, S, [], [mknh("if2", "10.0.0.3")])
    r_t.put_route(gg_child_route)
    # Grand-grand-grand child route
    ggg_child_prefix = '1.224.0.0/11'
    ggg_child_route = mkr(ggg_child_prefix, S, [], [mknh("if3", "10.0.0.4")])
    r_t.put_route(ggg_child_route)
    # Grand-grand-grand-grand child route
    gggg_child_prefix = '1.240.0.0/12'
    gggg_child_route = mkr(gggg_child_prefix, S, [], [mknh("if4", "10.0.0.5")])
    r_t.put_route(gggg_child_route)

    # Default route asserts
    assert r_t.destinations.get(DEFAULT_PREFIX).best_route == new_default_route
    assert r_t.destinations.get(DEFAULT_PREFIX).best_route.next_hops == \
           {mknh('if0', "10.0.0.1"), mknh("if1", "10.0.0.2"), mknh("if2", "10.0.0.3"),
            mknh("if3", "10.0.0.4"), mknh("if4", "10.0.0.5")}
    assert set(r_t.fib.routes[mkp(DEFAULT_PREFIX)].next_hops) == new_default_route.next_hops
    # Child route asserts
    assert r_t.destinations.get(child_prefix).best_route == child_route
    assert r_t.destinations.get(child_prefix).best_route.next_hops == \
           {mknh("if1", "10.0.0.2"), mknh("if2", "10.0.0.3"), mknh("if3", "10.0.0.4"),
            mknh("if4", "10.0.0.5")}
    assert set(r_t.fib.routes[mkp(child_prefix)].next_hops) == child_route.next_hops
    # Grand-child route asserts
    assert r_t.destinations.get(g_child_prefix).best_route == g_child_route
    assert r_t.destinations.get(g_child_prefix).best_route.next_hops == \
           {mknh("if2", "10.0.0.3"), mknh("if3", "10.0.0.4"), mknh("if4", "10.0.0.5")}
    assert set(r_t.fib.routes[mkp(g_child_prefix)].next_hops) == g_child_route.next_hops
    # Grand-grand child route asserts
    assert r_t.destinations.get(gg_child_prefix).best_route == gg_child_route
    assert r_t.destinations.get(gg_child_prefix).best_route.next_hops == \
           {mknh("if3", "10.0.0.4"), mknh("if4", "10.0.0.5")}
    assert set(r_t.fib.routes[mkp(gg_child_prefix)].next_hops) == gg_child_route.next_hops
    # Grand-grand-grand child route asserts
    assert r_t.destinations.get(ggg_child_prefix).best_route == ggg_child_route
    assert r_t.destinations.get(ggg_child_prefix).best_route.next_hops == {mknh("if4", "10.0.0.5")}
    assert set(r_t.fib.routes[mkp(ggg_child_prefix)].next_hops) == ggg_child_route.next_hops
    # Grand-grand-grand-grand child route asserts
    assert r_t.destinations.get(gggg_child_prefix).best_route == gggg_child_route
    assert r_t.destinations.get(gggg_child_prefix).best_route.next_hops == set()
    assert set(r_t.fib.routes[mkp(gggg_child_prefix)].next_hops) == gggg_child_route.next_hops

    # Delete if2 from default route
    new_default_route = mkr(DEFAULT_PREFIX, S, [mknh('if0', "10.0.0.1"), mknh("if1", "10.0.0.2"),
                                                mknh("if3", "10.0.0.4"), mknh("if4", "10.0.0.5")])
    r_t.put_route(new_default_route)

    # Default route asserts
    assert r_t.destinations.get(DEFAULT_PREFIX).best_route == new_default_route
    assert r_t.destinations.get(DEFAULT_PREFIX).best_route.next_hops == \
           {mknh('if0', "10.0.0.1"), mknh("if1", "10.0.0.2"),
            mknh("if3", "10.0.0.4"), mknh("if4", "10.0.0.5")}
    assert set(r_t.fib.routes[mkp(DEFAULT_PREFIX)].next_hops) == new_default_route.next_hops
    # Child route asserts
    assert r_t.destinations.get(child_prefix).best_route == child_route
    assert r_t.destinations.get(child_prefix).best_route.next_hops == \
           {mknh("if1", "10.0.0.2"), mknh("if3", "10.0.0.4"), mknh("if4", "10.0.0.5")}
    assert set(r_t.fib.routes[mkp(child_prefix)].next_hops) == child_route.next_hops
    # Grand-child route asserts
    assert r_t.destinations.get(g_child_prefix).best_route == g_child_route
    assert r_t.destinations.get(g_child_prefix).best_route.next_hops == \
           {mknh("if3", "10.0.0.4"), mknh("if4", "10.0.0.5")}
    assert set(r_t.fib.routes[mkp(g_child_prefix)].next_hops) == g_child_route.next_hops
    # Grand-grand child route asserts
    assert r_t.destinations.get(gg_child_prefix).best_route == gg_child_route
    assert r_t.destinations.get(gg_child_prefix).best_route.next_hops == \
           {mknh("if3", "10.0.0.4"), mknh("if4", "10.0.0.5")}
    assert set(r_t.fib.routes[mkp(gg_child_prefix)].next_hops) == gg_child_route.next_hops
    # Grand-grand-grand child route asserts
    assert r_t.destinations.get(ggg_child_prefix).best_route == ggg_child_route
    assert r_t.destinations.get(ggg_child_prefix).best_route.next_hops == {mknh("if4", "10.0.0.5")}
    assert set(r_t.fib.routes[mkp(ggg_child_prefix)].next_hops) == ggg_child_route.next_hops
    # Grand-grand-grand-grand child route asserts
    assert r_t.destinations.get(gggg_child_prefix).best_route == gggg_child_route
    assert r_t.destinations.get(gggg_child_prefix).best_route.next_hops == set()
    assert set(r_t.fib.routes[mkp(gggg_child_prefix)].next_hops) == gggg_child_route.next_hops

    r_t.del_route(mkp(DEFAULT_PREFIX), S)
    # Default route asserts
    assert not r_t.destinations.has_key(DEFAULT_PREFIX)
    # Child route asserts
    assert r_t.destinations.get(child_prefix).best_route == child_route
    assert r_t.destinations.get(child_prefix).best_route.next_hops == set()
    assert set(r_t.fib.routes[mkp(child_prefix)].next_hops) == set()
    # Grand-child route asserts
    assert r_t.destinations.get(g_child_prefix).best_route == g_child_route
    assert r_t.destinations.get(g_child_prefix).best_route.next_hops == set()
    assert set(r_t.fib.routes[mkp(g_child_prefix)].next_hops) == set()
    # Grand-grand child route asserts
    assert r_t.destinations.get(gg_child_prefix).best_route == gg_child_route
    assert r_t.destinations.get(gg_child_prefix).best_route.next_hops == set()
    assert set(r_t.fib.routes[mkp(gg_child_prefix)].next_hops) == set()
    # Grand-grand-grand child route asserts
    assert r_t.destinations.get(ggg_child_prefix).best_route == ggg_child_route
    assert r_t.destinations.get(ggg_child_prefix).best_route.next_hops == set()
    assert set(r_t.fib.routes[mkp(ggg_child_prefix)].next_hops) == set()
    # Grand-grand-grand-grand child route asserts
    assert r_t.destinations.get(gggg_child_prefix).best_route == gggg_child_route
    assert r_t.destinations.get(gggg_child_prefix).best_route.next_hops == set()
    assert set(r_t.fib.routes[mkp(gggg_child_prefix)].next_hops) == set()

    r_t.del_route(mkp(child_prefix), S)
    # Child route asserts
    assert not r_t.destinations.has_key(child_prefix)
    # Grand-child route asserts
    assert r_t.destinations.get(g_child_prefix).best_route == g_child_route
    assert r_t.destinations.get(g_child_prefix).best_route.next_hops == set()
    assert set(r_t.fib.routes[mkp(g_child_prefix)].next_hops) == set()
    # Grand-grand child route asserts
    assert r_t.destinations.get(gg_child_prefix).best_route == gg_child_route
    assert r_t.destinations.get(gg_child_prefix).best_route.next_hops == set()
    assert set(r_t.fib.routes[mkp(gg_child_prefix)].next_hops) == set()
    # Grand-grand-grand child route asserts
    assert r_t.destinations.get(ggg_child_prefix).best_route == ggg_child_route
    assert r_t.destinations.get(ggg_child_prefix).best_route.next_hops == set()
    assert set(r_t.fib.routes[mkp(ggg_child_prefix)].next_hops) == set()
    # Grand-grand-grand-grand child route asserts
    assert r_t.destinations.get(gggg_child_prefix).best_route == gggg_child_route
    assert r_t.destinations.get(gggg_child_prefix).best_route.next_hops == set()
    assert set(r_t.fib.routes[mkp(gggg_child_prefix)].next_hops) == set()

    r_t.del_route(mkp(g_child_prefix), S)
    # Grand-child route asserts
    assert not r_t.destinations.has_key(g_child_prefix)
    # Grand-grand child route asserts
    assert r_t.destinations.get(gg_child_prefix).best_route == gg_child_route
    assert r_t.destinations.get(gg_child_prefix).best_route.next_hops == set()
    assert set(r_t.fib.routes[mkp(gg_child_prefix)].next_hops) == set()
    # Grand-grand-grand child route asserts
    assert r_t.destinations.get(ggg_child_prefix).best_route == ggg_child_route
    assert r_t.destinations.get(ggg_child_prefix).best_route.next_hops == set()
    assert set(r_t.fib.routes[mkp(ggg_child_prefix)].next_hops) == set()
    # Grand-grand-grand-grand child route asserts
    assert r_t.destinations.get(gggg_child_prefix).best_route == gggg_child_route
    assert r_t.destinations.get(gggg_child_prefix).best_route.next_hops == set()
    assert set(r_t.fib.routes[mkp(gggg_child_prefix)].next_hops) == set()

    r_t.del_route(mkp(gg_child_prefix), S)
    # Grand-child route asserts
    assert not r_t.destinations.has_key(gg_child_prefix)
    # Grand-grand-grand child route asserts
    assert r_t.destinations.get(ggg_child_prefix).best_route == ggg_child_route
    assert r_t.destinations.get(ggg_child_prefix).best_route.next_hops == set()
    assert set(r_t.fib.routes[mkp(ggg_child_prefix)].next_hops) == set()
    # Grand-grand-grand-grand child route asserts
    assert r_t.destinations.get(gggg_child_prefix).best_route == gggg_child_route
    assert r_t.destinations.get(gggg_child_prefix).best_route.next_hops == set()
    assert set(r_t.fib.routes[mkp(gggg_child_prefix)].next_hops) == set()

    r_t.del_route(mkp(ggg_child_prefix), S)
    # Grand-child route asserts
    assert not r_t.destinations.has_key(ggg_child_prefix)
    # Grand-grand-grand-grand child route asserts
    assert r_t.destinations.get(gggg_child_prefix).best_route == gggg_child_route
    assert r_t.destinations.get(gggg_child_prefix).best_route.next_hops == set()
    assert set(r_t.fib.routes[mkp(gggg_child_prefix)].next_hops) == set()

    r_t.del_route(mkp(gggg_child_prefix), S)
    # Grand-grand-grand-grand child route asserts
    assert not r_t.destinations.has_key(gggg_child_prefix)

    assert not r_t.destinations.keys()
    assert not r_t.fib.routes.keys()


def test_prop_nesting_with_siblings():
    # Deep nesting of more specific routes using the following tree:
    #
    #   1.0.0.0/8 -> S1, S2, S3, S4, S5, S6, S7
    #    |
    #    +--- 1.1.0.0/16 -> ~S1
    #    |     |
    #    |     +--- 1.1.1.0/24 -> ~S2
    #    |     |
    #    |     +--- 1.1.2.0/24 -> ~S3
    #    |
    #    +--- 1.2.0.0/16 -> ~S4
    #          |
    #          +--- 1.2.1.0/24 -> ~S5
    #          |
    #          +--- 1.2.2.0/24 -> ~S6
    #
    # Note: we add the routes in a random order
    packet_common.add_missing_methods_to_thrift()
    r_t = mkrt(constants.ADDRESS_FAMILY_IPV4)

    r_t.put_route(mkr("1.2.1.0/24", S, [], [mknh("if4", "10.0.0.5")]))
    r_t.put_route(mkr("1.1.2.0/24", S, [], [mknh("if2", "10.0.0.3")]))
    r_t.put_route(mkr("1.1.0.0/16", S, [], [mknh('if0', "10.0.0.1")]))
    r_t.put_route(mkr("1.1.1.0/24", S, [], [mknh("if1", "10.0.0.2")]))
    r_t.put_route(mkr("1.2.0.0/16", S, [], [mknh("if3", "10.0.0.4")]))
    r_t.put_route(mkr("1.0.0.0/8", S, [mknh('if0', "10.0.0.1"), mknh("if1", "10.0.0.2"),
                                       mknh("if2", "10.0.0.3"), mknh("if3", "10.0.0.4"),
                                       mknh("if4", "10.0.0.5"), mknh("if5", "10.0.0.6"),
                                       mknh("if6", "10.0.0.7")]))
    r_t.put_route(mkr("1.2.2.0/24", S, [], [mknh("if5", "10.0.0.6")]))

    # Testing only rib and fib next hops
    assert r_t.destinations.get('1.0.0.0/8').best_route.next_hops == \
           {mknh('if0', "10.0.0.1"), mknh("if1", "10.0.0.2"), mknh("if2", "10.0.0.3"),
            mknh("if3", "10.0.0.4"), mknh("if4", "10.0.0.5"), mknh("if5", "10.0.0.6"),
            mknh("if6", "10.0.0.7")}
    assert set(r_t.fib.routes[mkp('1.0.0.0/8')].next_hops) == \
           {mknh('if0', "10.0.0.1"), mknh("if1", "10.0.0.2"), mknh("if2", "10.0.0.3"),
            mknh("if3", "10.0.0.4"), mknh("if4", "10.0.0.5"), mknh("if5", "10.0.0.6"),
            mknh("if6", "10.0.0.7")}

    assert r_t.destinations.get('1.1.0.0/16').best_route.negative_next_hops == \
           {mknh('if0', "10.0.0.1")}
    assert r_t.destinations.get('1.1.0.0/16').best_route.next_hops == \
           {mknh("if1", "10.0.0.2"), mknh("if2", "10.0.0.3"), mknh("if3", "10.0.0.4"),
            mknh("if4", "10.0.0.5"), mknh("if5", "10.0.0.6"), mknh("if6", "10.0.0.7")}
    assert set(r_t.fib.routes[mkp('1.1.0.0/16')].next_hops) == \
           {mknh("if1", "10.0.0.2"), mknh("if2", "10.0.0.3"), mknh("if3", "10.0.0.4"),
            mknh("if4", "10.0.0.5"), mknh("if5", "10.0.0.6"), mknh("if6", "10.0.0.7")}

    assert r_t.destinations.get('1.1.1.0/24').best_route.negative_next_hops == \
           {mknh("if1", "10.0.0.2")}
    assert r_t.destinations.get('1.1.1.0/24').best_route.next_hops == \
           {mknh("if2", "10.0.0.3"), mknh("if3", "10.0.0.4"), mknh("if4", "10.0.0.5"),
            mknh("if5", "10.0.0.6"), mknh("if6", "10.0.0.7")}
    assert set(r_t.fib.routes[mkp('1.1.1.0/24')].next_hops) == \
           {mknh("if2", "10.0.0.3"), mknh("if3", "10.0.0.4"), mknh("if4", "10.0.0.5"),
            mknh("if5", "10.0.0.6"), mknh("if6", "10.0.0.7")}

    assert r_t.destinations.get('1.1.2.0/24').best_route.negative_next_hops == \
           {mknh("if2", "10.0.0.3")}
    assert r_t.destinations.get('1.1.2.0/24').best_route.next_hops == \
           {mknh("if1", "10.0.0.2"), mknh("if3", "10.0.0.4"), mknh("if4", "10.0.0.5"),
            mknh("if5", "10.0.0.6"), mknh("if6", "10.0.0.7")}
    assert set(r_t.fib.routes[mkp('1.1.2.0/24')].next_hops) == \
           {mknh("if1", "10.0.0.2"), mknh("if3", "10.0.0.4"), mknh("if4", "10.0.0.5"),
            mknh("if5", "10.0.0.6"), mknh("if6", "10.0.0.7")}

    assert r_t.destinations.get('1.2.0.0/16').best_route.negative_next_hops == \
           {mknh("if3", "10.0.0.4")}
    assert r_t.destinations.get('1.2.0.0/16').best_route.next_hops == \
           {mknh('if0', "10.0.0.1"), mknh("if1", "10.0.0.2"), mknh("if2", "10.0.0.3"),
            mknh("if4", "10.0.0.5"), mknh("if5", "10.0.0.6"), mknh("if6", "10.0.0.7")}
    assert set(r_t.fib.routes[mkp('1.2.0.0/16')].next_hops) == \
           {mknh('if0', "10.0.0.1"), mknh("if1", "10.0.0.2"), mknh("if2", "10.0.0.3"),
            mknh("if4", "10.0.0.5"), mknh("if5", "10.0.0.6"), mknh("if6", "10.0.0.7")}

    assert r_t.destinations.get('1.2.1.0/24').best_route.negative_next_hops == \
           {mknh("if4", "10.0.0.5")}
    assert r_t.destinations.get('1.2.1.0/24').best_route.next_hops == \
           {mknh('if0', "10.0.0.1"), mknh("if1", "10.0.0.2"), mknh("if2", "10.0.0.3"),
            mknh("if5", "10.0.0.6"), mknh("if6", "10.0.0.7")}
    assert set(r_t.fib.routes[mkp('1.2.1.0/24')].next_hops) == \
           {mknh('if0', "10.0.0.1"), mknh("if1", "10.0.0.2"), mknh("if2", "10.0.0.3"),
            mknh("if5", "10.0.0.6"), mknh("if6", "10.0.0.7")}

    assert r_t.destinations.get('1.2.2.0/24').best_route.negative_next_hops == \
           {mknh("if5", "10.0.0.6")}
    assert r_t.destinations.get('1.2.2.0/24').best_route.next_hops == \
           {mknh('if0', "10.0.0.1"), mknh("if1", "10.0.0.2"), mknh("if2", "10.0.0.3"),
            mknh("if4", "10.0.0.5"), mknh("if6", "10.0.0.7")}
    assert set(r_t.fib.routes[mkp('1.2.2.0/24')].next_hops) == \
           {mknh('if0', "10.0.0.1"), mknh("if1", "10.0.0.2"), mknh("if2", "10.0.0.3"),
            mknh("if4", "10.0.0.5"), mknh("if6", "10.0.0.7")}

    # Delete nexthop if2 from the parent route 0.0.0.0/0.
    r_t.put_route(mkr('1.0.0.0/8', S, [mknh('if0', "10.0.0.1"), mknh("if1", "10.0.0.2"),
                                       mknh("if3", "10.0.0.4"), mknh("if4", "10.0.0.5"),
                                       mknh("if5", "10.0.0.6"), mknh("if6", "10.0.0.7")]))

    # Testing only rib and fib next hops
    assert r_t.destinations.get('1.0.0.0/8').best_route.next_hops == \
           {mknh('if0', "10.0.0.1"), mknh("if1", "10.0.0.2"), mknh("if3", "10.0.0.4"),
            mknh("if4", "10.0.0.5"), mknh("if5", "10.0.0.6"), mknh("if6", "10.0.0.7")}
    assert set(r_t.fib.routes[mkp('1.0.0.0/8')].next_hops) == \
           {mknh('if0', "10.0.0.1"), mknh("if1", "10.0.0.2"), mknh("if3", "10.0.0.4"),
            mknh("if4", "10.0.0.5"), mknh("if5", "10.0.0.6"), mknh("if6", "10.0.0.7")}

    assert r_t.destinations.get('1.1.0.0/16').best_route.negative_next_hops == \
           {mknh('if0', "10.0.0.1")}
    assert r_t.destinations.get('1.1.0.0/16').best_route.next_hops == \
           {mknh("if1", "10.0.0.2"), mknh("if3", "10.0.0.4"), mknh("if4", "10.0.0.5"),
            mknh("if5", "10.0.0.6"), mknh("if6", "10.0.0.7")}
    assert set(r_t.fib.routes[mkp('1.1.0.0/16')].next_hops) == \
           {mknh("if1", "10.0.0.2"), mknh("if3", "10.0.0.4"), mknh("if4", "10.0.0.5"),
            mknh("if5", "10.0.0.6"), mknh("if6", "10.0.0.7")}

    assert r_t.destinations.get('1.1.1.0/24').best_route.negative_next_hops == \
           {mknh("if1", "10.0.0.2")}
    assert r_t.destinations.get('1.1.1.0/24').best_route.next_hops == \
           {mknh("if3", "10.0.0.4"), mknh("if4", "10.0.0.5"), mknh("if5", "10.0.0.6"),
            mknh("if6", "10.0.0.7")}
    assert set(r_t.fib.routes[mkp('1.1.1.0/24')].next_hops) == \
           {mknh("if3", "10.0.0.4"), mknh("if4", "10.0.0.5"), mknh("if5", "10.0.0.6"),
            mknh("if6", "10.0.0.7")}

    assert r_t.destinations.get('1.1.2.0/24').best_route.negative_next_hops == \
           {mknh("if2", "10.0.0.3")}
    assert r_t.destinations.get('1.1.2.0/24').best_route.next_hops == \
           {mknh("if1", "10.0.0.2"), mknh("if3", "10.0.0.4"), mknh("if4", "10.0.0.5"),
            mknh("if5", "10.0.0.6"), mknh("if6", "10.0.0.7")}
    assert set(r_t.fib.routes[mkp('1.1.2.0/24')].next_hops) == \
           {mknh("if1", "10.0.0.2"), mknh("if3", "10.0.0.4"), mknh("if4", "10.0.0.5"),
            mknh("if5", "10.0.0.6"), mknh("if6", "10.0.0.7")}

    assert r_t.destinations.get('1.2.0.0/16').best_route.negative_next_hops == \
           {mknh("if3", "10.0.0.4")}
    assert r_t.destinations.get('1.2.0.0/16').best_route.next_hops == \
           {mknh('if0', "10.0.0.1"), mknh("if1", "10.0.0.2"), mknh("if4", "10.0.0.5"),
            mknh("if5", "10.0.0.6"), mknh("if6", "10.0.0.7")}
    assert set(r_t.fib.routes[mkp('1.2.0.0/16')].next_hops) == \
           {mknh('if0', "10.0.0.1"), mknh("if1", "10.0.0.2"), mknh("if4", "10.0.0.5"),
            mknh("if5", "10.0.0.6"), mknh("if6", "10.0.0.7")}

    assert r_t.destinations.get('1.2.1.0/24').best_route.negative_next_hops == \
           {mknh("if4", "10.0.0.5")}
    assert r_t.destinations.get('1.2.1.0/24').best_route.next_hops == \
           {mknh('if0', "10.0.0.1"), mknh("if1", "10.0.0.2"), mknh("if5", "10.0.0.6"),
            mknh("if6", "10.0.0.7")}
    assert set(r_t.fib.routes[mkp('1.2.1.0/24')].next_hops) == \
           {mknh('if0', "10.0.0.1"), mknh("if1", "10.0.0.2"), mknh("if5", "10.0.0.6"),
            mknh("if6", "10.0.0.7")}

    assert r_t.destinations.get('1.2.2.0/24').best_route.negative_next_hops == \
           {mknh("if5", "10.0.0.6")}
    assert r_t.destinations.get('1.2.2.0/24').best_route.next_hops == \
           {mknh('if0', "10.0.0.1"), mknh("if1", "10.0.0.2"), mknh("if4", "10.0.0.5"),
            mknh("if6", "10.0.0.7")}
    assert set(r_t.fib.routes[mkp('1.2.2.0/24')].next_hops) == \
           {mknh('if0', "10.0.0.1"), mknh("if1", "10.0.0.2"), mknh("if4", "10.0.0.5"),
            mknh("if6", "10.0.0.7")}

    # Delete all routes from the RIB.
    r_t.del_route(mkp("1.0.0.0/8"), S)
    r_t.del_route(mkp("1.1.0.0/16"), S)
    r_t.del_route(mkp("1.1.1.0/24"), S)
    r_t.del_route(mkp("1.1.2.0/24"), S)
    r_t.del_route(mkp("1.2.0.0/16"), S)
    r_t.del_route(mkp("1.2.1.0/24"), S)
    r_t.del_route(mkp("1.2.2.0/24"), S)

    # The RIB must be empty.
    assert not r_t.destinations.keys()
    # The FIB must be empty.
    assert not r_t.fib.routes.keys()
