from pytest import fixture

from constants import ADDRESS_FAMILY_IPV4, ADDRESS_FAMILY_IPV6, OWNER_N_SPF, OWNER_S_SPF
from forwarding_table import ForwardingTable
from next_hop import NextHop
from packet_common import add_missing_methods_to_thrift, make_ip_address, make_ip_prefix
from rib_route import RibRoute
from route_table import RouteTable

# pylint: disable=invalid-name,too-many-statements,too-many-lines

def mkrt():
    # Make a route table
    address_family = ADDRESS_FAMILY_IPV4
    forwarding_table = ForwardingTable(address_family, kernel=None, log=None, log_id="")
    route_table = RouteTable(address_family, forwarding_table, log=None, log_id="")
    return route_table

def mkp(prefix_str):
    # Make an IP prefix
    return make_ip_prefix(prefix_str)

def mkr(prefix_str, next_hops):
    # Make a RIB route
    if next_hops is None:
        next_hops = []
    return RibRoute(mkp(prefix_str), OWNER_S_SPF, next_hops)

def mknh_pos(interface_str, address_str):
    # Make positive next-hop
    if address_str is None:
        address = None
    else:
        address = make_ip_address(address_str)
    return NextHop(False, interface_str, address, None)

def mknh_neg(interface_str, address_str):
    # Make negative next-hop
    if address_str is None:
        address = None
    else:
        address = make_ip_address(address_str)
    return NextHop(True, interface_str, address, None)

def check_rib_route(rt, prefix_str, exp_next_hops):
    assert prefix_str in rt.destinations
    best_rib_route = rt.destinations[prefix_str].best_route()
    assert best_rib_route is not None
    assert str(best_rib_route.prefix) == prefix_str
    assert best_rib_route.owner == OWNER_S_SPF
    assert sorted(best_rib_route.next_hops) == sorted(exp_next_hops)

def check_rib_route_absent(rt, prefix_str):
    ###@@@
    if prefix_str in rt.destinations:
        print("****RIB***", rt.destinations[prefix_str])
    ###@@@
    assert prefix_str not in rt.destinations

def check_fib_route(rt, prefix_str, exp_next_hops):
    prefix = make_ip_prefix(prefix_str)
    fib = rt.fib
    assert prefix in fib.fib_routes
    fib_route = fib.fib_routes[prefix]
    assert fib_route is not None
    assert str(fib_route.prefix) == prefix_str
    assert sorted(fib_route.next_hops) == sorted(exp_next_hops)

def check_fib_route_absent(rt, prefix_str):
    prefix = make_ip_prefix(prefix_str)
    fib = rt.fib
    ###@@@
    if prefix in fib.fib_routes:
        print("****FIB***", fib.fib_routes[prefix])
    ###@@@
    assert prefix not in fib.fib_routes

@fixture(autouse=True)
def run_before_every_test_case():
    add_missing_methods_to_thrift()

def test_default_route_only():
    # Test slide 55 in Pascal's "negative disaggregation" presentation:
    # Just a default route with positive next-hops; there are no more specific routes
    rt = mkrt()
    default_prefix = "0.0.0.0/0"
    default_next_hops = [mknh_pos('if0', "10.0.0.1"),
                         mknh_pos("if1", "10.0.0.2"),
                         mknh_pos("if2", "10.0.0.3"),
                         mknh_pos("if3", "10.0.0.4")]
    default_route = mkr(default_prefix, default_next_hops)
    rt.put_route(default_route)
    check_rib_route(rt, default_prefix, default_next_hops)
    check_fib_route(rt, default_prefix, default_next_hops)

def test_parent_with_negative_child():
    # Test slide 56 in Pascal's "negative disaggregation" presentation:
    # Start with a parent default route with some positive next-hops
    rt = mkrt()
    default_prefix = "0.0.0.0/0"
    default_next_hops = [mknh_pos('if0', "10.0.0.1"),
                         mknh_pos("if1", "10.0.0.2"),
                         mknh_pos("if2", "10.0.0.3"),
                         mknh_pos("if3", "10.0.0.4")]
    default_route = mkr(default_prefix, default_next_hops)
    rt.put_route(default_route)
    check_rib_route(rt, default_prefix, default_next_hops)
    check_fib_route(rt, default_prefix, default_next_hops)
    # Add a more specific child route with a negative next-hop
    child_prefix = "10.0.0.0/16"
    child_rib_next_hops = [mknh_neg('if0', "10.0.0.1")]
    child_route = mkr(child_prefix, child_rib_next_hops)
    rt.put_route(child_route)
    check_rib_route(rt, child_prefix, child_rib_next_hops)
    # Check negative to positive next-hop conversion in FIB
    child_fib_next_hops = [mknh_pos("if1", "10.0.0.2"),
                           mknh_pos("if2", "10.0.0.3"),
                           mknh_pos("if3", "10.0.0.4")]
    check_fib_route(rt, child_prefix, child_fib_next_hops)
    # Go back to the parent, and check it's next-hops haven't changed
    check_fib_route(rt, default_prefix, default_next_hops)

def test_parent_with_two_negative_children():
    # Test slide 57 in Pascal's "negative disaggregation" presentation:
    # Start a parent default route with some positive nexthops
    rt = mkrt()
    default_prefix = "0.0.0.0/0"
    default_next_hops = [mknh_pos('if0', "10.0.0.1"),
                         mknh_pos("if1", "10.0.0.2"),
                         mknh_pos("if2", "10.0.0.3"),
                         mknh_pos("if3", "10.0.0.4")]
    default_route = mkr(default_prefix, default_next_hops)
    rt.put_route(default_route)
    check_rib_route(rt, default_prefix, default_next_hops)
    check_fib_route(rt, default_prefix, default_next_hops)
    # Add first more specific child route with a negative next-hop
    first_child_prefix = "10.0.0.0/16"
    first_child_rib_next_hops = [mknh_neg('if0', "10.0.0.1")]
    first_child_route = mkr(first_child_prefix, first_child_rib_next_hops)
    rt.put_route(first_child_route)
    check_rib_route(rt, first_child_prefix, first_child_rib_next_hops)
    # Add second more specific child route with a negative next-hop
    second_child_prefix = "10.1.0.0/16"
    second_child_rib_next_hops = [mknh_neg('if3', "10.0.0.4")]
    second_child_route = mkr(second_child_prefix, second_child_rib_next_hops)
    rt.put_route(second_child_route)
    check_rib_route(rt, second_child_prefix, second_child_rib_next_hops)
    # Check negative to positive next-hop conversion in FIB
    first_child_fib_next_hops = [mknh_pos("if1", "10.0.0.2"),
                                 mknh_pos("if2", "10.0.0.3"),
                                 mknh_pos("if3", "10.0.0.4")]
    check_fib_route(rt, first_child_prefix, first_child_fib_next_hops)
    second_child_fib_next_hops = [mknh_pos("if0", "10.0.0.1"),
                                  mknh_pos("if1", "10.0.0.2"),
                                  mknh_pos("if2", "10.0.0.3")]
    check_fib_route(rt, second_child_prefix, second_child_fib_next_hops)
    # Go back to the parent, and check it's next-hops haven't changed
    check_fib_route(rt, default_prefix, default_next_hops)

def test_remove_pos_next_hop_from_parent_update_child():
    # Test slide 58 in Pascal's "negative disaggregation" presentation.
    # Delete a nexthop from a parent route, and check that the computed complementary nexthops in
    # the child routes are properly updated.
    # Create a parent default route with positive nexthops
    rt = mkrt()
    default_prefix = "0.0.0.0/0"
    default_next_hops = [mknh_pos('if0', "10.0.0.1"),
                         mknh_pos("if1", "10.0.0.2"),
                         mknh_pos("if2", "10.0.0.3"),
                         mknh_pos("if3", "10.0.0.4")]
    default_route = mkr(default_prefix, default_next_hops)
    rt.put_route(default_route)
    check_rib_route(rt, default_prefix, default_next_hops)
    check_fib_route(rt, default_prefix, default_next_hops)
    # Add first more specific child route with a negative next-hop
    first_child_prefix = "10.0.0.0/16"
    first_child_rib_next_hops = [mknh_neg('if0', "10.0.0.1")]
    first_child_route = mkr(first_child_prefix, first_child_rib_next_hops)
    rt.put_route(first_child_route)
    check_rib_route(rt, first_child_prefix, first_child_rib_next_hops)
    # Add second more specific child route with a negative next-hop
    second_child_prefix = "10.1.0.0/16"
    second_child_rib_next_hops = [mknh_neg('if3', "10.0.0.4")]
    second_child_route = mkr(second_child_prefix, second_child_rib_next_hops)
    rt.put_route(second_child_route)
    check_rib_route(rt, second_child_prefix, second_child_rib_next_hops)
    # Check negative to positive next-hop conversion in FIB for both child routes
    first_child_fib_next_hops = [mknh_pos("if1", "10.0.0.2"),
                                 mknh_pos("if2", "10.0.0.3"),
                                 mknh_pos("if3", "10.0.0.4")]
    check_fib_route(rt, first_child_prefix, first_child_fib_next_hops)
    second_child_fib_next_hops = [mknh_pos("if0", "10.0.0.1"),
                                  mknh_pos("if1", "10.0.0.2"),
                                  mknh_pos("if2", "10.0.0.3")]
    check_fib_route(rt, second_child_prefix, second_child_fib_next_hops)
    # Remove one positive next-hop (if2 10.0.0.3) from the default route
    new1_default_next_hops = [mknh_pos('if0', "10.0.0.1"),
                              mknh_pos("if1", "10.0.0.2"),
                              mknh_pos("if3", "10.0.0.4")]
    new1_default_route = mkr(default_prefix, new1_default_next_hops)
    rt.put_route(new1_default_route)
    check_rib_route(rt, default_prefix, new1_default_next_hops)
    check_fib_route(rt, default_prefix, new1_default_next_hops)
    # Check updated negative to positive next-hop conversion in FIB for both child routes
    first_child_new1_fib_next_hops = [mknh_pos("if1", "10.0.0.2"),
                                      mknh_pos("if3", "10.0.0.4")]
    check_fib_route(rt, first_child_prefix, first_child_new1_fib_next_hops)
    second_child_new1_fib_next_hops = [mknh_pos("if0", "10.0.0.1"),
                                       mknh_pos("if1", "10.0.0.2")]
    check_fib_route(rt, second_child_prefix, second_child_new1_fib_next_hops)
    # Remove another positive next-hop (if3 10.0.0.4) from the default route
    new2_default_next_hops = [mknh_pos('if0', "10.0.0.1"),
                              mknh_pos("if1", "10.0.0.2")]
    new2_default_route = mkr(default_prefix, new2_default_next_hops)
    rt.put_route(new2_default_route)
    check_rib_route(rt, default_prefix, new2_default_next_hops)
    check_fib_route(rt, default_prefix, new2_default_next_hops)
    # Check updated negative to positive next-hop conversion in FIB for both child routes
    first_child_new2_fib_next_hops = [mknh_pos("if1", "10.0.0.2")]
    check_fib_route(rt, first_child_prefix, first_child_new2_fib_next_hops)
    second_child_new2_fib_next_hops = [mknh_pos("if0", "10.0.0.1"),
                                       mknh_pos("if1", "10.0.0.2")]
    check_fib_route(rt, second_child_prefix, second_child_new2_fib_next_hops)

def test_parent_with_negative_child_and_negative_grandchild():
    # Test slides 59 in Pascal's "negative disaggregation" presentation.
    # Start with a parent default route with some positive next-hops
    rt = mkrt()
    default_prefix = "0.0.0.0/0"
    default_next_hops = [mknh_pos('if0', "10.0.0.1"),
                         mknh_pos("if1", "10.0.0.2"),
                         mknh_pos("if2", "10.0.0.3"),
                         mknh_pos("if3", "10.0.0.4")]
    default_route = mkr(default_prefix, default_next_hops)
    rt.put_route(default_route)
    check_rib_route(rt, default_prefix, default_next_hops)
    check_fib_route(rt, default_prefix, default_next_hops)
    # Add a more specific child route with a negative next-hop
    child_prefix = "10.0.0.0/16"
    child_rib_next_hops = [mknh_neg('if0', "10.0.0.1")]
    child_route = mkr(child_prefix, child_rib_next_hops)
    rt.put_route(child_route)
    check_rib_route(rt, child_prefix, child_rib_next_hops)
    # Add an even more specific grand-child route with a negative next-hop
    grand_child_prefix = "10.0.10.0/24"
    grand_child_rib_next_hops = [mknh_neg('if1', "10.0.0.2")]
    grand_child_route = mkr(grand_child_prefix, grand_child_rib_next_hops)
    rt.put_route(grand_child_route)
    check_rib_route(rt, grand_child_prefix, grand_child_rib_next_hops)
    # Check child's negative to positive next-hop conversion in FIB
    child_fib_next_hops = [mknh_pos("if1", "10.0.0.2"),
                           mknh_pos("if2", "10.0.0.3"),
                           mknh_pos("if3", "10.0.0.4")]
    check_fib_route(rt, child_prefix, child_fib_next_hops)
    # Check grand-child's negative to positive next-hop conversion in FIB
    grand_child_fib_next_hops = [mknh_pos("if2", "10.0.0.3"),
                                 mknh_pos("if3", "10.0.0.4")]
    check_fib_route(rt, grand_child_prefix, grand_child_fib_next_hops)
    # Go back to the parent, and check it's next-hops haven't changed
    check_fib_route(rt, default_prefix, default_next_hops)

def test_remove_pos_next_hop_from_parent_update_grand_child():
    # Test slide 60 in Pascal's "negative disaggregation" presentation.
    # Start with a parent default route with some positive next-hops
    rt = mkrt()
    default_prefix = "0.0.0.0/0"
    default_next_hops = [mknh_pos('if0', "10.0.0.1"),
                         mknh_pos("if1", "10.0.0.2"),
                         mknh_pos("if2", "10.0.0.3"),
                         mknh_pos("if3", "10.0.0.4")]
    default_route = mkr(default_prefix, default_next_hops)
    rt.put_route(default_route)
    check_rib_route(rt, default_prefix, default_next_hops)
    check_fib_route(rt, default_prefix, default_next_hops)
    # Add a more specific child route with a negative next-hop
    child_prefix = "10.0.0.0/16"
    child_rib_next_hops = [mknh_neg('if0', "10.0.0.1")]
    child_route = mkr(child_prefix, child_rib_next_hops)
    rt.put_route(child_route)
    check_rib_route(rt, child_prefix, child_rib_next_hops)
    # Add an even more specific grand-child route with a negative next-hop
    grand_child_prefix = "10.0.10.0/24"
    grand_child_rib_next_hops = [mknh_neg('if1', "10.0.0.2")]
    grand_child_route = mkr(grand_child_prefix, grand_child_rib_next_hops)
    rt.put_route(grand_child_route)
    check_rib_route(rt, grand_child_prefix, grand_child_rib_next_hops)
    # Check child's negative to positive next-hop conversion in FIB
    child_fib_next_hops = [mknh_pos("if1", "10.0.0.2"),
                           mknh_pos("if2", "10.0.0.3"),
                           mknh_pos("if3", "10.0.0.4")]
    check_fib_route(rt, child_prefix, child_fib_next_hops)
    # Check grand-child's negative to positive next-hop conversion in FIB
    grand_child_fib_next_hops = [mknh_pos("if2", "10.0.0.3"),
                                 mknh_pos("if3", "10.0.0.4")]
    check_fib_route(rt, grand_child_prefix, grand_child_fib_next_hops)
    # Go back to the parent, and check it's next-hops haven't changed
    check_fib_route(rt, default_prefix, default_next_hops)
    # Remove one positive next-hop (if2 10.0.0.3) from the default route
    new1_default_next_hops = [mknh_pos('if0', "10.0.0.1"),
                              mknh_pos("if1", "10.0.0.2"),
                              mknh_pos("if3", "10.0.0.4")]
    new1_default_route = mkr(default_prefix, new1_default_next_hops)
    rt.put_route(new1_default_route)
    check_rib_route(rt, default_prefix, new1_default_next_hops)
    check_fib_route(rt, default_prefix, new1_default_next_hops)
    # Check updated negative to positive next-hop conversion in FIB for child and grand-child routes
    child_new1_fib_next_hops = [mknh_pos("if1", "10.0.0.2"),
                                mknh_pos("if3", "10.0.0.4")]
    check_fib_route(rt, child_prefix, child_new1_fib_next_hops)
    grand_child_new1_fib_next_hops = [mknh_pos("if3", "10.0.0.4")]
    check_fib_route(rt, grand_child_prefix, grand_child_new1_fib_next_hops)
    # Go back to the parent, and check it's next-hops haven't changed
    check_fib_route(rt, default_prefix, new1_default_next_hops)

def test_recover_default_next_hop_with_subnet_disagg():
    # Slide 60 and recover of the failed next hops
    # Start with a parent default route with some positive next-hops
    rt = mkrt()
    default_prefix = "0.0.0.0/0"
    default_next_hops = [mknh_pos('if0', "10.0.0.1"),
                         mknh_pos("if1", "10.0.0.2"),
                         mknh_pos("if2", "10.0.0.3"),
                         mknh_pos("if3", "10.0.0.4")]
    default_route = mkr(default_prefix, default_next_hops)
    rt.put_route(default_route)
    check_rib_route(rt, default_prefix, default_next_hops)
    check_fib_route(rt, default_prefix, default_next_hops)
    # Add a more specific child route with a negative next-hop
    child_prefix = "10.0.0.0/16"
    child_rib_next_hops = [mknh_neg('if0', "10.0.0.1")]
    child_route = mkr(child_prefix, child_rib_next_hops)
    rt.put_route(child_route)
    check_rib_route(rt, child_prefix, child_rib_next_hops)
    # Add an even more specific grand-child route with a negative next-hop
    grand_child_prefix = "10.0.10.0/24"
    grand_child_rib_next_hops = [mknh_neg('if1', "10.0.0.2")]
    grand_child_route = mkr(grand_child_prefix, grand_child_rib_next_hops)
    rt.put_route(grand_child_route)
    check_rib_route(rt, grand_child_prefix, grand_child_rib_next_hops)
    # Check child's negative to positive next-hop conversion in FIB
    child_fib_next_hops = [mknh_pos("if1", "10.0.0.2"),
                           mknh_pos("if2", "10.0.0.3"),
                           mknh_pos("if3", "10.0.0.4")]
    check_fib_route(rt, child_prefix, child_fib_next_hops)
    # Check grand-child's negative to positive next-hop conversion in FIB
    grand_child_fib_next_hops = [mknh_pos("if2", "10.0.0.3"),
                                 mknh_pos("if3", "10.0.0.4")]
    check_fib_route(rt, grand_child_prefix, grand_child_fib_next_hops)
    # Go back to the parent, and check it's next-hops haven't changed
    check_fib_route(rt, default_prefix, default_next_hops)
    # Remove one positive next-hop (if2 10.0.0.3) from the default route
    new1_default_next_hops = [mknh_pos('if0', "10.0.0.1"),
                              mknh_pos("if1", "10.0.0.2"),
                              mknh_pos("if3", "10.0.0.4")]
    new1_default_route = mkr(default_prefix, new1_default_next_hops)
    rt.put_route(new1_default_route)
    check_rib_route(rt, default_prefix, new1_default_next_hops)
    check_fib_route(rt, default_prefix, new1_default_next_hops)
    # Check updated negative to positive next-hop conversion in FIB for child and grand-child routes
    child_new1_fib_next_hops = [mknh_pos("if1", "10.0.0.2"),
                                mknh_pos("if3", "10.0.0.4")]
    check_fib_route(rt, child_prefix, child_new1_fib_next_hops)
    grand_child_new1_fib_next_hops = [mknh_pos("if3", "10.0.0.4")]
    check_fib_route(rt, grand_child_prefix, grand_child_new1_fib_next_hops)
    # Go back to the parent, and check it's next-hops haven't changed
    check_fib_route(rt, default_prefix, new1_default_next_hops)
    # Put back the next-hop in the default route that was previously taken away
    rt.put_route(default_route)
    # Check child's negative to positive next-hop conversion in FIB
    check_fib_route(rt, child_prefix, child_fib_next_hops)
    # Check grand-child's negative to positive next-hop conversion in FIB
    check_fib_route(rt, grand_child_prefix, grand_child_fib_next_hops)
    # Go back to the parent, and check it's next-hops haven't changed
    check_fib_route(rt, default_prefix, default_next_hops)

def test_remove_default_route():
    # Test that the child routes are removed from the FIB when the parent route is removed
    # Start with a parent default route with some positive next-hops
    rt = mkrt()
    default_prefix = "0.0.0.0/0"
    default_next_hops = [mknh_pos('if0', "10.0.0.1"),
                         mknh_pos("if1", "10.0.0.2"),
                         mknh_pos("if2", "10.0.0.3"),
                         mknh_pos("if3", "10.0.0.4")]
    default_route = mkr(default_prefix, default_next_hops)
    rt.put_route(default_route)
    check_rib_route(rt, default_prefix, default_next_hops)
    check_fib_route(rt, default_prefix, default_next_hops)
    # Add a more specific child route with a negative next-hop
    child_prefix = "10.0.0.0/16"
    child_rib_next_hops = [mknh_neg('if0', "10.0.0.1")]
    child_route = mkr(child_prefix, child_rib_next_hops)
    rt.put_route(child_route)
    check_rib_route(rt, child_prefix, child_rib_next_hops)
    # Add an even more specific grand-child route with a negative next-hop
    grand_child_prefix = "10.0.10.0/24"
    grand_child_rib_next_hops = [mknh_neg('if1', "10.0.0.2")]
    grand_child_route = mkr(grand_child_prefix, grand_child_rib_next_hops)
    rt.put_route(grand_child_route)
    check_rib_route(rt, grand_child_prefix, grand_child_rib_next_hops)
    # Check child's negative to positive next-hop conversion in FIB
    child_fib_next_hops = [mknh_pos("if1", "10.0.0.2"),
                           mknh_pos("if2", "10.0.0.3"),
                           mknh_pos("if3", "10.0.0.4")]
    check_fib_route(rt, child_prefix, child_fib_next_hops)
    # Check grand-child's negative to positive next-hop conversion in FIB
    grand_child_fib_next_hops = [mknh_pos("if2", "10.0.0.3"),
                                 mknh_pos("if3", "10.0.0.4")]
    check_fib_route(rt, grand_child_prefix, grand_child_fib_next_hops)
    # Go back to the parent, and check it's next-hops haven't changed
    check_fib_route(rt, default_prefix, default_next_hops)
    # Delete the default route
    rt.del_route(mkp(default_prefix), OWNER_S_SPF)
    # Check all routes (parent, child, grand-child) are gone
    check_rib_route_absent(rt, default_prefix)
    check_fib_route_absent(rt, default_prefix)
    check_rib_route(rt, child_prefix, child_rib_next_hops)
    check_fib_route_absent(rt, child_prefix)
    check_rib_route(rt, grand_child_prefix, grand_child_rib_next_hops)
    check_fib_route_absent(rt, grand_child_prefix)

def test_remove_child_from_fib_when_no_next_hops_left():
    # Tests if a route becomes unreachable after all next hops are negatively disaggregated
    # Start with a parent default route with some positive next-hops
    rt = mkrt()
    default_prefix = "0.0.0.0/0"
    default_next_hops = [mknh_pos('if0', "10.0.0.1"),
                         mknh_pos("if1", "10.0.0.2"),
                         mknh_pos("if2", "10.0.0.3"),
                         mknh_pos("if3", "10.0.0.4")]
    default_route = mkr(default_prefix, default_next_hops)
    rt.put_route(default_route)
    check_rib_route(rt, default_prefix, default_next_hops)
    check_fib_route(rt, default_prefix, default_next_hops)
    # Add a more specific child route with negative next-hops for all of the parent's positive
    # next-hops.
    child_prefix = "10.0.0.0/16"
    child_rib_next_hops = [mknh_neg('if0', "10.0.0.1"),
                           mknh_neg("if1", "10.0.0.2"),
                           mknh_neg("if2", "10.0.0.3"),
                           mknh_neg("if3", "10.0.0.4")]
    child_route = mkr(child_prefix, child_rib_next_hops)
    rt.put_route(child_route)
    check_rib_route(rt, child_prefix, child_rib_next_hops)
    # Check that the child route is absent from the FIB (even though it is present in the RIB)
    check_fib_route_absent(rt, child_prefix)
    # Go back to the parent, and check it's next-hops haven't changed
    check_fib_route(rt, default_prefix, default_next_hops)

def test_restore_child_from_to_when_neg_next_hop_removed():
    # Tests if an unreachable route becomes reachable after a negative disaggregation is removed
    # Start with a parent default route with some positive next-hops
    rt = mkrt()
    default_prefix = "0.0.0.0/0"
    default_next_hops = [mknh_pos('if0', "10.0.0.1"),
                         mknh_pos("if1", "10.0.0.2"),
                         mknh_pos("if2", "10.0.0.3"),
                         mknh_pos("if3", "10.0.0.4")]
    default_route = mkr(default_prefix, default_next_hops)
    rt.put_route(default_route)
    check_rib_route(rt, default_prefix, default_next_hops)
    check_fib_route(rt, default_prefix, default_next_hops)
    # Add a more specific child route with negative next-hops for all of the parent's positive
    # next-hops.
    child_prefix = "10.0.0.0/16"
    child_rib_next_hops = [mknh_neg('if0', "10.0.0.1"),
                           mknh_neg("if1", "10.0.0.2"),
                           mknh_neg("if2", "10.0.0.3"),
                           mknh_neg("if3", "10.0.0.4")]
    child_route = mkr(child_prefix, child_rib_next_hops)
    rt.put_route(child_route)
    check_rib_route(rt, child_prefix, child_rib_next_hops)
    # Check that the child route is absent from the FIB (even though it is present in the RIB)
    check_fib_route_absent(rt, child_prefix)
    # Go back to the parent, and check it's next-hops haven't changed
    check_fib_route(rt, default_prefix, default_next_hops)
    # Remove one of the negative next-hops of the child route (namely if2 10.0.0.3)
    new_child_rib_next_hops = [mknh_neg('if0', "10.0.0.1"),
                               mknh_neg("if1", "10.0.0.2"),
                               mknh_neg("if3", "10.0.0.4")]
    child_route = mkr(child_prefix, new_child_rib_next_hops)
    rt.put_route(child_route)
    check_rib_route(rt, child_prefix, new_child_rib_next_hops)
    # Check that the child route has appeared in the FIB
    new_child_fib_next_hops = [mknh_pos("if2", "10.0.0.3")]
    check_fib_route(rt, child_prefix, new_child_fib_next_hops)

def test_remove_grand_child_from_fib_when_no_next_hops_left_due_to_inheritance():
    # Test that a grand-child route is removed from the FIB when it has no next-hops left because
    # the child route (i.e. the parent of the grand-child route) removed all next-hops.
    # Start with a parent default route with some positive next-hops
    rt = mkrt()
    default_prefix = "0.0.0.0/0"
    default_next_hops = [mknh_pos('if0', "10.0.0.1"),
                         mknh_pos("if1", "10.0.0.2"),
                         mknh_pos("if2", "10.0.0.3"),
                         mknh_pos("if3", "10.0.0.4")]
    default_route = mkr(default_prefix, default_next_hops)
    rt.put_route(default_route)
    check_rib_route(rt, default_prefix, default_next_hops)
    check_fib_route(rt, default_prefix, default_next_hops)
    # Add a more specific child route with negative next-hops for all of the parent's positive
    # next-hops.
    child_prefix = "10.0.0.0/16"
    child_rib_next_hops = [mknh_neg('if0', "10.0.0.1"),
                           mknh_neg("if1", "10.0.0.2"),
                           mknh_neg("if2", "10.0.0.3"),
                           mknh_neg("if3", "10.0.0.4")]
    child_route = mkr(child_prefix, child_rib_next_hops)
    rt.put_route(child_route)
    check_rib_route(rt, child_prefix, child_rib_next_hops)
    # Add an even more specific grand-child route with only one negative next-hop of its own, but
    # the other next-hops that could potentially be inherited from the default were already removed
    # by the child route.
    grand_child_prefix = "10.0.10.0/24"
    grand_child_rib_next_hops = [mknh_neg('if1', "10.0.0.2")]
    grand_child_route = mkr(grand_child_prefix, grand_child_rib_next_hops)
    rt.put_route(grand_child_route)
    check_rib_route(rt, grand_child_prefix, grand_child_rib_next_hops)
    # Check that the child route is absent from the FIB
    check_fib_route_absent(rt, child_prefix)
    # Check that the grand-child route is also absent from the FIB
    check_fib_route_absent(rt, grand_child_prefix)
    # Go back to the parent, and check it's next-hops haven't changed
    check_fib_route(rt, default_prefix, default_next_hops)

def test_keep_grand_child_in_fib_extra_positive_next_hop():
    # Test that a grand-child route is present in the FIB in the following scenario:
    # - A parent route has some positive next-hops
    # - A child route removes all of the next-hops with negative next-hops
    # - The grand-child route adds a new positive next-hops, completely separate from the ones
    #   that the child and parent used.
    # Start with a parent default route with some positive next-hops
    rt = mkrt()
    default_prefix = "0.0.0.0/0"
    default_next_hops = [mknh_pos('if0', "10.0.0.1"),
                         mknh_pos("if1", "10.0.0.2"),
                         mknh_pos("if2", "10.0.0.3"),
                         mknh_pos("if3", "10.0.0.4")]
    default_route = mkr(default_prefix, default_next_hops)
    rt.put_route(default_route)
    check_rib_route(rt, default_prefix, default_next_hops)
    check_fib_route(rt, default_prefix, default_next_hops)
    # Add a more specific child route with negative next-hops for all of the parent's positive
    # next-hops.
    child_prefix = "10.0.0.0/16"
    child_rib_next_hops = [mknh_neg('if0', "10.0.0.1"),
                           mknh_neg("if1", "10.0.0.2"),
                           mknh_neg("if2", "10.0.0.3"),
                           mknh_neg("if3", "10.0.0.4")]
    child_route = mkr(child_prefix, child_rib_next_hops)
    rt.put_route(child_route)
    check_rib_route(rt, child_prefix, child_rib_next_hops)
    # Add an even more specific grand-child route with a positive next-hops that puts one of the
    # next-hops that was removed by its parent (i.e. by the child-route) explicitly back.
    grand_child_prefix = "10.0.10.0/24"
    grand_child_next_hops = [mknh_pos('if4', "10.0.0.5")]
    grand_child_route = mkr(grand_child_prefix, grand_child_next_hops)
    rt.put_route(grand_child_route)
    check_rib_route(rt, grand_child_prefix, grand_child_next_hops)
    # Check that the child route is absent from the FIB
    check_fib_route_absent(rt, child_prefix)
    # Check that the grand-child route is present from the FIB
    check_fib_route(rt, grand_child_prefix, grand_child_next_hops)
    # Go back to the parent, and check it's next-hops haven't changed
    check_fib_route(rt, default_prefix, default_next_hops)

def test_keep_grand_child_in_fib_readd_positive_next_hop():
    # Test that a grand-child route is present in the FIB in the following scenario:
    # - A parent route has some positive next-hops
    # - A child route removes all of the next-hops with negative next-hops
    # - The grand-child route puts one of the removed next-hops explicitly back with a positive
    #   next-hop.
    # Start with a parent default route with some positive next-hops
    rt = mkrt()
    default_prefix = "0.0.0.0/0"
    default_next_hops = [mknh_pos('if0', "10.0.0.1"),
                         mknh_pos("if1", "10.0.0.2"),
                         mknh_pos("if2", "10.0.0.3"),
                         mknh_pos("if3", "10.0.0.4")]
    default_route = mkr(default_prefix, default_next_hops)
    rt.put_route(default_route)
    check_rib_route(rt, default_prefix, default_next_hops)
    check_fib_route(rt, default_prefix, default_next_hops)
    # Add a more specific child route with negative next-hops for all of the parent's positive
    # next-hops.
    child_prefix = "10.0.0.0/16"
    child_rib_next_hops = [mknh_neg('if0', "10.0.0.1"),
                           mknh_neg("if1", "10.0.0.2"),
                           mknh_neg("if2", "10.0.0.3"),
                           mknh_neg("if3", "10.0.0.4")]
    child_route = mkr(child_prefix, child_rib_next_hops)
    rt.put_route(child_route)
    check_rib_route(rt, child_prefix, child_rib_next_hops)
    # Add an even more specific grand-child route with a positive next-hops that puts one of the
    # next-hops that was removed by its parent (i.e. by the child-route) explicitly back.
    grand_child_prefix = "10.0.10.0/24"
    grand_child_next_hops = [mknh_pos('if1', "10.0.0.2")]
    grand_child_route = mkr(grand_child_prefix, grand_child_next_hops)
    rt.put_route(grand_child_route)
    check_rib_route(rt, grand_child_prefix, grand_child_next_hops)
    # Check that the child route is absent from the FIB
    check_fib_route_absent(rt, child_prefix)
    # Check that the grand-child route is present from the FIB
    check_fib_route(rt, grand_child_prefix, grand_child_next_hops)
    # Go back to the parent, and check it's next-hops haven't changed
    check_fib_route(rt, default_prefix, default_next_hops)

# Slide 61 from the perspective of L3
def test_pos_neg_disagg():
    add_missing_methods_to_thrift()
    rt = mkrt()
    default_route = mkr(DEFAULT_PREFIX, DEFAULT_NEXT_HOPS)
    rt.put_route(default_route)
    leaf_route = mkr(LEAF_PREFIX, LEAF_PREFIX_POS_NEXT_HOPS,
                     LEAF_PREFIX_NEG_NEXT_HOPS)
    rt.put_route(leaf_route)
    assert rt.destinations.get(LEAF_PREFIX).best_route.positive_next_hops == \
           {mknh("eth0", "10.0.1.1")}
    assert rt.destinations.get(LEAF_PREFIX).best_route.negative_next_hops == \
           {mknh("eth1", "10.0.1.2")}
    assert rt.destinations.get(LEAF_PREFIX).best_route.next_hops == \
           {mknh("if3", "10.0.0.4"), mknh("if2", "10.0.0.3"), mknh("eth0", "10.0.1.1"),
            mknh("if1", "10.0.0.2"), mknh("if0", "10.0.0.1")}
    assert set(rt.fib.routes[mkp(LEAF_PREFIX)].next_hops) == leaf_route.next_hops


# Given a prefix X with N negative next hops
# Given a prefix Y, subnet of X, with M negative next hops and a positive next hop L included in N
# Results that next hops of Y include L
def test_pos_neg_disagg_recursive():
    add_missing_methods_to_thrift()
    rt = mkrt()
    default_route = mkr(DEFAULT_PREFIX, DEFAULT_NEXT_HOPS)
    rt.put_route(default_route)
    first_neg_route = mkr(FIRST_NEG_DISAGG_PREFIX, [], FIRST_NEG_DISAGG_NEXT_HOPS)
    rt.put_route(first_neg_route)
    subnet_disagg_route = mkr(SUBNET_NEG_DISAGG_PREFIX, [mknh("if0", "10.0.0.1")],
                              SUBNET_NEG_DISAGG_NEXT_HOPS)
    rt.put_route(subnet_disagg_route)
    assert rt.destinations.get(SUBNET_NEG_DISAGG_PREFIX).best_route.positive_next_hops == \
           {mknh("if0", "10.0.0.1")}
    assert rt.destinations.get(SUBNET_NEG_DISAGG_PREFIX).best_route.negative_next_hops == \
           {mknh("if1", "10.0.0.2")}
    assert rt.destinations.get(SUBNET_NEG_DISAGG_PREFIX).best_route.next_hops == \
           {mknh("if0", "10.0.0.1"), mknh("if2", "10.0.0.3"), mknh("if3", "10.0.0.4")}
    assert set(
        rt.fib.routes[mkp(SUBNET_NEG_DISAGG_PREFIX)].next_hops) == subnet_disagg_route.next_hops


# Add two destination with different owner to the same destination,
# test that the S_SPF route is preferred
def test_add_two_route_same_destination():
    add_missing_methods_to_thrift()
    rt = mkrt()
    default_route = mkr(DEFAULT_PREFIX, N, DEFAULT_NEXT_HOPS)
    rt.put_route(default_route)
    best_default_route = mkr(DEFAULT_PREFIX, [mknh('if0', "10.0.0.1")])
    rt.put_route(best_default_route)
    assert rt.destinations.get(DEFAULT_PREFIX).best_route == best_default_route
    assert rt.destinations.get(DEFAULT_PREFIX).best_route.positive_next_hops == \
           {mknh('if0', "10.0.0.1")}
    assert rt.destinations.get(DEFAULT_PREFIX).best_route.negative_next_hops == set()
    assert rt.destinations.get(DEFAULT_PREFIX).best_route.next_hops == \
           {mknh('if0', "10.0.0.1")}
    assert set(rt.fib.routes[mkp(DEFAULT_PREFIX)].next_hops) == best_default_route.next_hops


# Add two destination with different owner to the same destination,
# then remove the best route (S_SPF), test that the S_SPF is now preferred
def test_remove_best_route():
    add_missing_methods_to_thrift()
    rt = mkrt()
    default_route = mkr(DEFAULT_PREFIX, N, DEFAULT_NEXT_HOPS)
    rt.put_route(default_route)
    rt.del_route(mkp(DEFAULT_PREFIX), S)
    assert rt.destinations.get(DEFAULT_PREFIX).best_route == default_route
    assert rt.destinations.get(DEFAULT_PREFIX).best_route.positive_next_hops == \
           {mknh('if0', "10.0.0.1"), mknh("if1", "10.0.0.2"), mknh("if2", "10.0.0.3"),
            mknh("if3", "10.0.0.4")}
    assert rt.destinations.get(DEFAULT_PREFIX).best_route.negative_next_hops == set()
    assert rt.destinations.get(DEFAULT_PREFIX).best_route.next_hops == \
           {mknh('if0', "10.0.0.1"), mknh("if1", "10.0.0.2"), mknh("if2", "10.0.0.3"),
            mknh("if3", "10.0.0.4")}
    assert set(rt.fib.routes[mkp(DEFAULT_PREFIX)].next_hops) == default_route.next_hops


# Add two destination with different owner to the same destination, test that the S_SPF route
# is preferred. Then add subnet destination and check that they inherits the preferred one
def test_add_two_route_same_destination_with_subnet():
    add_missing_methods_to_thrift()
    rt = mkrt()
    default_route = mkr(DEFAULT_PREFIX, N, DEFAULT_NEXT_HOPS)
    rt.put_route(default_route)
    best_default_route = mkr(DEFAULT_PREFIX,
                             [mknh("if0", "10.0.0.1"), mknh("if1", "10.0.0.2"),
                              mknh("if2", "10.0.0.3")])
    rt.put_route(best_default_route)
    first_neg_route = mkr(FIRST_NEG_DISAGG_PREFIX, [], FIRST_NEG_DISAGG_NEXT_HOPS)
    rt.put_route(first_neg_route)
    subnet_disagg_route = mkr(SUBNET_NEG_DISAGG_PREFIX, [], SUBNET_NEG_DISAGG_NEXT_HOPS)
    rt.put_route(subnet_disagg_route)
    # Test for default
    assert rt.destinations.get(DEFAULT_PREFIX).best_route == best_default_route
    assert rt.destinations.get(DEFAULT_PREFIX).best_route.positive_next_hops == \
           {mknh('if0', "10.0.0.1"), mknh("if1", "10.0.0.2"), mknh("if2", "10.0.0.3")}
    assert rt.destinations.get(DEFAULT_PREFIX).best_route.negative_next_hops == set()
    assert rt.destinations.get(DEFAULT_PREFIX).best_route.next_hops == \
           {mknh('if0', "10.0.0.1"), mknh("if1", "10.0.0.2"), mknh("if2", "10.0.0.3")}
    assert set(rt.fib.routes[mkp(DEFAULT_PREFIX)].next_hops) == best_default_route.next_hops
    # Test for 10.0.0.0/16
    assert rt.destinations.get(FIRST_NEG_DISAGG_PREFIX).best_route == first_neg_route
    assert rt.destinations.get(FIRST_NEG_DISAGG_PREFIX).best_route.positive_next_hops == set()
    assert rt.destinations.get(FIRST_NEG_DISAGG_PREFIX).best_route.negative_next_hops == \
           {mknh('if0', "10.0.0.1")}
    assert rt.destinations.get(FIRST_NEG_DISAGG_PREFIX).best_route.next_hops == {
        mknh("if1", "10.0.0.2"), mknh("if2", "10.0.0.3")}
    assert set(rt.fib.routes[mkp(FIRST_NEG_DISAGG_PREFIX)].next_hops) == \
           first_neg_route.next_hops
    # Test for 10.0.10.0/24
    assert rt.destinations.get(SUBNET_NEG_DISAGG_PREFIX).best_route == subnet_disagg_route
    assert rt.destinations.get(SUBNET_NEG_DISAGG_PREFIX).best_route.positive_next_hops == set()
    assert rt.destinations.get(SUBNET_NEG_DISAGG_PREFIX).best_route.negative_next_hops == \
           {mknh("if1", "10.0.0.2")}
    assert rt.destinations.get(SUBNET_NEG_DISAGG_PREFIX).best_route.next_hops == \
           {mknh("if2", "10.0.0.3")}
    assert set(
        rt.fib.routes[mkp(SUBNET_NEG_DISAGG_PREFIX)].next_hops) == subnet_disagg_route.next_hops


# Add two destination with different owner to the default destination,
# check that the S_SPF route is preferred. Then add subnet destination and check that they
# inherits the preferred one. Delete the best route from the default and check that the
# subnets changes consequently
def test_add_two_route_same_destination_with_subnet_and_remove_one():
    add_missing_methods_to_thrift()
    rt = mkrt()
    default_route = mkr(DEFAULT_PREFIX, N, DEFAULT_NEXT_HOPS)
    rt.put_route(default_route)
    best_default_route = mkr(DEFAULT_PREFIX,
                             [mknh("if0", "10.0.0.1"), mknh("if1", "10.0.0.2"),
                              mknh("if2", "10.0.0.3")])
    rt.put_route(best_default_route)
    first_neg_route = mkr(FIRST_NEG_DISAGG_PREFIX, [], FIRST_NEG_DISAGG_NEXT_HOPS)
    rt.put_route(first_neg_route)
    subnet_disagg_route = mkr(SUBNET_NEG_DISAGG_PREFIX, [], SUBNET_NEG_DISAGG_NEXT_HOPS)
    rt.put_route(subnet_disagg_route)
    rt.del_route(mkp(DEFAULT_PREFIX), S)
    # Test for default
    assert rt.destinations.get(DEFAULT_PREFIX).best_route == default_route
    assert rt.destinations.get(DEFAULT_PREFIX).best_route.positive_next_hops == \
           {mknh('if0', "10.0.0.1"), mknh("if1", "10.0.0.2"), mknh("if2", "10.0.0.3"),
            mknh("if3", "10.0.0.4")}
    assert rt.destinations.get(DEFAULT_PREFIX).best_route.negative_next_hops == set()
    assert rt.destinations.get(DEFAULT_PREFIX).best_route.next_hops == \
           {mknh('if0', "10.0.0.1"), mknh("if1", "10.0.0.2"), mknh("if2", "10.0.0.3"),
            mknh("if3", "10.0.0.4")}
    assert set(rt.fib.routes[mkp(DEFAULT_PREFIX)].next_hops) == default_route.next_hops
    # Test for 10.0.0.0/16
    assert rt.destinations.get(FIRST_NEG_DISAGG_PREFIX).best_route == first_neg_route
    assert rt.destinations.get(FIRST_NEG_DISAGG_PREFIX).best_route.positive_next_hops == set()
    assert rt.destinations.get(FIRST_NEG_DISAGG_PREFIX).best_route.negative_next_hops == \
           {mknh('if0', "10.0.0.1")}
    assert rt.destinations.get(FIRST_NEG_DISAGG_PREFIX).best_route.next_hops == \
           {mknh("if1", "10.0.0.2"), mknh("if2", "10.0.0.3"), mknh("if3", "10.0.0.4")}
    assert set(rt.fib.routes[mkp(FIRST_NEG_DISAGG_PREFIX)].next_hops) == \
           first_neg_route.next_hops
    # Test for 10.0.10.0/24
    assert rt.destinations.get(SUBNET_NEG_DISAGG_PREFIX).best_route == subnet_disagg_route
    assert rt.destinations.get(SUBNET_NEG_DISAGG_PREFIX).best_route.positive_next_hops == set()
    assert rt.destinations.get(SUBNET_NEG_DISAGG_PREFIX).best_route.negative_next_hops == \
           {mknh("if1", "10.0.0.2")}
    assert rt.destinations.get(SUBNET_NEG_DISAGG_PREFIX).best_route.next_hops == \
           {mknh("if2", "10.0.0.3"), mknh("if3", "10.0.0.4")}
    assert set(
        rt.fib.routes[mkp(SUBNET_NEG_DISAGG_PREFIX)].next_hops) == subnet_disagg_route.next_hops


# Test that a subnet X that becomes equal to its parent destination is removed and that its
# child subnet Y changes the parent destination to the one of X
def test_remove_superfluous_subnet_recursive():
    add_missing_methods_to_thrift()
    rt = mkrt()
    default_route = mkr(DEFAULT_PREFIX, DEFAULT_NEXT_HOPS)
    rt.put_route(default_route)
    first_disagg_route = mkr(FIRST_NEG_DISAGG_PREFIX, [], FIRST_NEG_DISAGG_NEXT_HOPS)
    rt.put_route(first_disagg_route)
    subnet_disagg_route = mkr(SUBNET_NEG_DISAGG_PREFIX, [], SUBNET_NEG_DISAGG_NEXT_HOPS)
    rt.put_route(subnet_disagg_route)
    rt.del_route(mkp(FIRST_NEG_DISAGG_PREFIX), S)
    assert not rt.destinations.has_key(FIRST_NEG_DISAGG_PREFIX)
    assert FIRST_NEG_DISAGG_PREFIX not in rt.fib.routes
    assert rt.destinations.get(SUBNET_NEG_DISAGG_PREFIX).best_route.positive_next_hops == set()
    assert rt.destinations.get(SUBNET_NEG_DISAGG_PREFIX).best_route.negative_next_hops == \
           {mknh("if1", "10.0.0.2")}
    assert rt.destinations.get(SUBNET_NEG_DISAGG_PREFIX).best_route.next_hops == \
           {mknh('if0', "10.0.0.1"), mknh("if2", "10.0.0.3"), mknh("if3", "10.0.0.4")}
    assert set(
        rt.fib.routes[mkp(SUBNET_NEG_DISAGG_PREFIX)].next_hops) == subnet_disagg_route.next_hops
    assert rt.destinations.get(SUBNET_NEG_DISAGG_PREFIX).parent_prefix_dest == \
           rt.destinations.get(DEFAULT_PREFIX)


# Deep nesting of more specific routes: parent, child, grand child, grand-grand child, ...
def test_prop_deep_nesting():
    add_missing_methods_to_thrift()
    rt = mkrt()
    # Default route
    new_default_next_hops = [mknh('if0', "10.0.0.1"), mknh("if1", "10.0.0.2"),
                             mknh("if2", "10.0.0.3"), mknh("if3", "10.0.0.4"),
                             mknh("if4", "10.0.0.5")]
    new_default_route = mkr(DEFAULT_PREFIX, new_default_next_hops)
    rt.put_route(new_default_route)
    # Child route
    child_prefix = '1.0.0.0/8'
    child_route = mkr(child_prefix, [], [mknh('if0', "10.0.0.1")])
    rt.put_route(child_route)
    # Grand child route
    g_child_prefix = '1.128.0.0/9'
    g_child_route = mkr(g_child_prefix, [], [mknh("if1", "10.0.0.2")])
    rt.put_route(g_child_route)
    # Grand-grand child route
    gg_child_prefix = '1.192.0.0/10'
    gg_child_route = mkr(gg_child_prefix, [], [mknh("if2", "10.0.0.3")])
    rt.put_route(gg_child_route)
    # Grand-grand-grand child route
    ggg_child_prefix = '1.224.0.0/11'
    ggg_child_route = mkr(ggg_child_prefix, [], [mknh("if3", "10.0.0.4")])
    rt.put_route(ggg_child_route)
    # Grand-grand-grand-grand child route
    gggg_child_prefix = '1.240.0.0/12'
    gggg_child_route = mkr(gggg_child_prefix, [], [mknh("if4", "10.0.0.5")])
    rt.put_route(gggg_child_route)

    # Default route asserts
    assert rt.destinations.get(DEFAULT_PREFIX).best_route == new_default_route
    assert rt.destinations.get(DEFAULT_PREFIX).best_route.next_hops == \
           {mknh('if0', "10.0.0.1"), mknh("if1", "10.0.0.2"), mknh("if2", "10.0.0.3"),
            mknh("if3", "10.0.0.4"), mknh("if4", "10.0.0.5")}
    assert set(rt.fib.routes[mkp(DEFAULT_PREFIX)].next_hops) == new_default_route.next_hops
    # Child route asserts
    assert rt.destinations.get(child_prefix).best_route == child_route
    assert rt.destinations.get(child_prefix).best_route.next_hops == \
           {mknh("if1", "10.0.0.2"), mknh("if2", "10.0.0.3"), mknh("if3", "10.0.0.4"),
            mknh("if4", "10.0.0.5")}
    assert set(rt.fib.routes[mkp(child_prefix)].next_hops) == child_route.next_hops
    # Grand-child route asserts
    assert rt.destinations.get(g_child_prefix).best_route == g_child_route
    assert rt.destinations.get(g_child_prefix).best_route.next_hops == \
           {mknh("if2", "10.0.0.3"), mknh("if3", "10.0.0.4"), mknh("if4", "10.0.0.5")}
    assert set(rt.fib.routes[mkp(g_child_prefix)].next_hops) == g_child_route.next_hops
    # Grand-grand child route asserts
    assert rt.destinations.get(gg_child_prefix).best_route == gg_child_route
    assert rt.destinations.get(gg_child_prefix).best_route.next_hops == \
           {mknh("if3", "10.0.0.4"), mknh("if4", "10.0.0.5")}
    assert set(rt.fib.routes[mkp(gg_child_prefix)].next_hops) == gg_child_route.next_hops
    # Grand-grand-grand child route asserts
    assert rt.destinations.get(ggg_child_prefix).best_route == ggg_child_route
    assert rt.destinations.get(ggg_child_prefix).best_route.next_hops == {mknh("if4", "10.0.0.5")}
    assert set(rt.fib.routes[mkp(ggg_child_prefix)].next_hops) == ggg_child_route.next_hops
    # Grand-grand-grand-grand child route asserts
    assert rt.destinations.get(gggg_child_prefix).best_route == gggg_child_route
    assert rt.destinations.get(gggg_child_prefix).best_route.next_hops == set()
    assert set(rt.fib.routes[mkp(gggg_child_prefix)].next_hops) == gggg_child_route.next_hops

    # Delete if2 from default route
    new_default_route = mkr(DEFAULT_PREFIX, [mknh('if0', "10.0.0.1"), mknh("if1", "10.0.0.2"),
                                                mknh("if3", "10.0.0.4"), mknh("if4", "10.0.0.5")])
    rt.put_route(new_default_route)

    # Default route asserts
    assert rt.destinations.get(DEFAULT_PREFIX).best_route == new_default_route
    assert rt.destinations.get(DEFAULT_PREFIX).best_route.next_hops == \
           {mknh('if0', "10.0.0.1"), mknh("if1", "10.0.0.2"),
            mknh("if3", "10.0.0.4"), mknh("if4", "10.0.0.5")}
    assert set(rt.fib.routes[mkp(DEFAULT_PREFIX)].next_hops) == new_default_route.next_hops
    # Child route asserts
    assert rt.destinations.get(child_prefix).best_route == child_route
    assert rt.destinations.get(child_prefix).best_route.next_hops == \
           {mknh("if1", "10.0.0.2"), mknh("if3", "10.0.0.4"), mknh("if4", "10.0.0.5")}
    assert set(rt.fib.routes[mkp(child_prefix)].next_hops) == child_route.next_hops
    # Grand-child route asserts
    assert rt.destinations.get(g_child_prefix).best_route == g_child_route
    assert rt.destinations.get(g_child_prefix).best_route.next_hops == \
           {mknh("if3", "10.0.0.4"), mknh("if4", "10.0.0.5")}
    assert set(rt.fib.routes[mkp(g_child_prefix)].next_hops) == g_child_route.next_hops
    # Grand-grand child route asserts
    assert rt.destinations.get(gg_child_prefix).best_route == gg_child_route
    assert rt.destinations.get(gg_child_prefix).best_route.next_hops == \
           {mknh("if3", "10.0.0.4"), mknh("if4", "10.0.0.5")}
    assert set(rt.fib.routes[mkp(gg_child_prefix)].next_hops) == gg_child_route.next_hops
    # Grand-grand-grand child route asserts
    assert rt.destinations.get(ggg_child_prefix).best_route == ggg_child_route
    assert rt.destinations.get(ggg_child_prefix).best_route.next_hops == {mknh("if4", "10.0.0.5")}
    assert set(rt.fib.routes[mkp(ggg_child_prefix)].next_hops) == ggg_child_route.next_hops
    # Grand-grand-grand-grand child route asserts
    assert rt.destinations.get(gggg_child_prefix).best_route == gggg_child_route
    assert rt.destinations.get(gggg_child_prefix).best_route.next_hops == set()
    assert set(rt.fib.routes[mkp(gggg_child_prefix)].next_hops) == gggg_child_route.next_hops

    rt.del_route(mkp(DEFAULT_PREFIX), S)
    # Default route asserts
    assert not rt.destinations.has_key(DEFAULT_PREFIX)
    # Child route asserts
    assert rt.destinations.get(child_prefix).best_route == child_route
    assert rt.destinations.get(child_prefix).best_route.next_hops == set()
    assert set(rt.fib.routes[mkp(child_prefix)].next_hops) == set()
    # Grand-child route asserts
    assert rt.destinations.get(g_child_prefix).best_route == g_child_route
    assert rt.destinations.get(g_child_prefix).best_route.next_hops == set()
    assert set(rt.fib.routes[mkp(g_child_prefix)].next_hops) == set()
    # Grand-grand child route asserts
    assert rt.destinations.get(gg_child_prefix).best_route == gg_child_route
    assert rt.destinations.get(gg_child_prefix).best_route.next_hops == set()
    assert set(rt.fib.routes[mkp(gg_child_prefix)].next_hops) == set()
    # Grand-grand-grand child route asserts
    assert rt.destinations.get(ggg_child_prefix).best_route == ggg_child_route
    assert rt.destinations.get(ggg_child_prefix).best_route.next_hops == set()
    assert set(rt.fib.routes[mkp(ggg_child_prefix)].next_hops) == set()
    # Grand-grand-grand-grand child route asserts
    assert rt.destinations.get(gggg_child_prefix).best_route == gggg_child_route
    assert rt.destinations.get(gggg_child_prefix).best_route.next_hops == set()
    assert set(rt.fib.routes[mkp(gggg_child_prefix)].next_hops) == set()

    rt.del_route(mkp(child_prefix), S)
    # Child route asserts
    assert not rt.destinations.has_key(child_prefix)
    # Grand-child route asserts
    assert rt.destinations.get(g_child_prefix).best_route == g_child_route
    assert rt.destinations.get(g_child_prefix).best_route.next_hops == set()
    assert set(rt.fib.routes[mkp(g_child_prefix)].next_hops) == set()
    # Grand-grand child route asserts
    assert rt.destinations.get(gg_child_prefix).best_route == gg_child_route
    assert rt.destinations.get(gg_child_prefix).best_route.next_hops == set()
    assert set(rt.fib.routes[mkp(gg_child_prefix)].next_hops) == set()
    # Grand-grand-grand child route asserts
    assert rt.destinations.get(ggg_child_prefix).best_route == ggg_child_route
    assert rt.destinations.get(ggg_child_prefix).best_route.next_hops == set()
    assert set(rt.fib.routes[mkp(ggg_child_prefix)].next_hops) == set()
    # Grand-grand-grand-grand child route asserts
    assert rt.destinations.get(gggg_child_prefix).best_route == gggg_child_route
    assert rt.destinations.get(gggg_child_prefix).best_route.next_hops == set()
    assert set(rt.fib.routes[mkp(gggg_child_prefix)].next_hops) == set()

    rt.del_route(mkp(g_child_prefix), S)
    # Grand-child route asserts
    assert not rt.destinations.has_key(g_child_prefix)
    # Grand-grand child route asserts
    assert rt.destinations.get(gg_child_prefix).best_route == gg_child_route
    assert rt.destinations.get(gg_child_prefix).best_route.next_hops == set()
    assert set(rt.fib.routes[mkp(gg_child_prefix)].next_hops) == set()
    # Grand-grand-grand child route asserts
    assert rt.destinations.get(ggg_child_prefix).best_route == ggg_child_route
    assert rt.destinations.get(ggg_child_prefix).best_route.next_hops == set()
    assert set(rt.fib.routes[mkp(ggg_child_prefix)].next_hops) == set()
    # Grand-grand-grand-grand child route asserts
    assert rt.destinations.get(gggg_child_prefix).best_route == gggg_child_route
    assert rt.destinations.get(gggg_child_prefix).best_route.next_hops == set()
    assert set(rt.fib.routes[mkp(gggg_child_prefix)].next_hops) == set()

    rt.del_route(mkp(gg_child_prefix), S)
    # Grand-child route asserts
    assert not rt.destinations.has_key(gg_child_prefix)
    # Grand-grand-grand child route asserts
    assert rt.destinations.get(ggg_child_prefix).best_route == ggg_child_route
    assert rt.destinations.get(ggg_child_prefix).best_route.next_hops == set()
    assert set(rt.fib.routes[mkp(ggg_child_prefix)].next_hops) == set()
    # Grand-grand-grand-grand child route asserts
    assert rt.destinations.get(gggg_child_prefix).best_route == gggg_child_route
    assert rt.destinations.get(gggg_child_prefix).best_route.next_hops == set()
    assert set(rt.fib.routes[mkp(gggg_child_prefix)].next_hops) == set()

    rt.del_route(mkp(ggg_child_prefix), S)
    # Grand-child route asserts
    assert not rt.destinations.has_key(ggg_child_prefix)
    # Grand-grand-grand-grand child route asserts
    assert rt.destinations.get(gggg_child_prefix).best_route == gggg_child_route
    assert rt.destinations.get(gggg_child_prefix).best_route.next_hops == set()
    assert set(rt.fib.routes[mkp(gggg_child_prefix)].next_hops) == set()

    rt.del_route(mkp(gggg_child_prefix), S)
    # Grand-grand-grand-grand child route asserts
    assert not rt.destinations.has_key(gggg_child_prefix)

    assert not rt.destinations.keys()
    assert not rt.fib.routes.keys()


def test_prop_nesting_with_siblings():
    # Deep nesting of more specific routes using the following tree:
    #
    #   1.0.0.0/8 -> S1, S2, S3, S4, S5, S6, S7
    #    |
    #    +--- 1.1.0.0/16 -> S1
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
    add_missing_methods_to_thrift()
    rt = mkrt()

    rt.put_route(mkr("1.2.1.0/24", [], [mknh("if4", "10.0.0.5")]))
    rt.put_route(mkr("1.1.2.0/24", [], [mknh("if2", "10.0.0.3")]))
    rt.put_route(mkr("1.1.0.0/16", [], [mknh('if0', "10.0.0.1")]))
    rt.put_route(mkr("1.1.1.0/24", [], [mknh("if1", "10.0.0.2")]))
    rt.put_route(mkr("1.2.0.0/16", [], [mknh("if3", "10.0.0.4")]))
    rt.put_route(mkr("1.0.0.0/8", [mknh('if0', "10.0.0.1"), mknh("if1", "10.0.0.2"),
                                       mknh("if2", "10.0.0.3"), mknh("if3", "10.0.0.4"),
                                       mknh("if4", "10.0.0.5"), mknh("if5", "10.0.0.6"),
                                       mknh("if6", "10.0.0.7")]))
    rt.put_route(mkr("1.2.2.0/24", [], [mknh("if5", "10.0.0.6")]))

    # Testing only rib and fib next hops
    assert rt.destinations.get('1.0.0.0/8').best_route.next_hops == \
           {mknh('if0', "10.0.0.1"), mknh("if1", "10.0.0.2"), mknh("if2", "10.0.0.3"),
            mknh("if3", "10.0.0.4"), mknh("if4", "10.0.0.5"), mknh("if5", "10.0.0.6"),
            mknh("if6", "10.0.0.7")}
    assert set(rt.fib.routes[mkp('1.0.0.0/8')].next_hops) == \
           {mknh('if0', "10.0.0.1"), mknh("if1", "10.0.0.2"), mknh("if2", "10.0.0.3"),
            mknh("if3", "10.0.0.4"), mknh("if4", "10.0.0.5"), mknh("if5", "10.0.0.6"),
            mknh("if6", "10.0.0.7")}

    assert rt.destinations.get('1.1.0.0/16').best_route.negative_next_hops == \
           {mknh('if0', "10.0.0.1")}
    assert rt.destinations.get('1.1.0.0/16').best_route.next_hops == \
           {mknh("if1", "10.0.0.2"), mknh("if2", "10.0.0.3"), mknh("if3", "10.0.0.4"),
            mknh("if4", "10.0.0.5"), mknh("if5", "10.0.0.6"), mknh("if6", "10.0.0.7")}
    assert set(rt.fib.routes[mkp('1.1.0.0/16')].next_hops) == \
           {mknh("if1", "10.0.0.2"), mknh("if2", "10.0.0.3"), mknh("if3", "10.0.0.4"),
            mknh("if4", "10.0.0.5"), mknh("if5", "10.0.0.6"), mknh("if6", "10.0.0.7")}

    assert rt.destinations.get('1.1.1.0/24').best_route.negative_next_hops == \
           {mknh("if1", "10.0.0.2")}
    assert rt.destinations.get('1.1.1.0/24').best_route.next_hops == \
           {mknh("if2", "10.0.0.3"), mknh("if3", "10.0.0.4"), mknh("if4", "10.0.0.5"),
            mknh("if5", "10.0.0.6"), mknh("if6", "10.0.0.7")}
    assert set(rt.fib.routes[mkp('1.1.1.0/24')].next_hops) == \
           {mknh("if2", "10.0.0.3"), mknh("if3", "10.0.0.4"), mknh("if4", "10.0.0.5"),
            mknh("if5", "10.0.0.6"), mknh("if6", "10.0.0.7")}

    assert rt.destinations.get('1.1.2.0/24').best_route.negative_next_hops == \
           {mknh("if2", "10.0.0.3")}
    assert rt.destinations.get('1.1.2.0/24').best_route.next_hops == \
           {mknh("if1", "10.0.0.2"), mknh("if3", "10.0.0.4"), mknh("if4", "10.0.0.5"),
            mknh("if5", "10.0.0.6"), mknh("if6", "10.0.0.7")}
    assert set(rt.fib.routes[mkp('1.1.2.0/24')].next_hops) == \
           {mknh("if1", "10.0.0.2"), mknh("if3", "10.0.0.4"), mknh("if4", "10.0.0.5"),
            mknh("if5", "10.0.0.6"), mknh("if6", "10.0.0.7")}

    assert rt.destinations.get('1.2.0.0/16').best_route.negative_next_hops == \
           {mknh("if3", "10.0.0.4")}
    assert rt.destinations.get('1.2.0.0/16').best_route.next_hops == \
           {mknh('if0', "10.0.0.1"), mknh("if1", "10.0.0.2"), mknh("if2", "10.0.0.3"),
            mknh("if4", "10.0.0.5"), mknh("if5", "10.0.0.6"), mknh("if6", "10.0.0.7")}
    assert set(rt.fib.routes[mkp('1.2.0.0/16')].next_hops) == \
           {mknh('if0', "10.0.0.1"), mknh("if1", "10.0.0.2"), mknh("if2", "10.0.0.3"),
            mknh("if4", "10.0.0.5"), mknh("if5", "10.0.0.6"), mknh("if6", "10.0.0.7")}

    assert rt.destinations.get('1.2.1.0/24').best_route.negative_next_hops == \
           {mknh("if4", "10.0.0.5")}
    assert rt.destinations.get('1.2.1.0/24').best_route.next_hops == \
           {mknh('if0', "10.0.0.1"), mknh("if1", "10.0.0.2"), mknh("if2", "10.0.0.3"),
            mknh("if5", "10.0.0.6"), mknh("if6", "10.0.0.7")}
    assert set(rt.fib.routes[mkp('1.2.1.0/24')].next_hops) == \
           {mknh('if0', "10.0.0.1"), mknh("if1", "10.0.0.2"), mknh("if2", "10.0.0.3"),
            mknh("if5", "10.0.0.6"), mknh("if6", "10.0.0.7")}

    assert rt.destinations.get('1.2.2.0/24').best_route.negative_next_hops == \
           {mknh("if5", "10.0.0.6")}
    assert rt.destinations.get('1.2.2.0/24').best_route.next_hops == \
           {mknh('if0', "10.0.0.1"), mknh("if1", "10.0.0.2"), mknh("if2", "10.0.0.3"),
            mknh("if4", "10.0.0.5"), mknh("if6", "10.0.0.7")}
    assert set(rt.fib.routes[mkp('1.2.2.0/24')].next_hops) == \
           {mknh('if0', "10.0.0.1"), mknh("if1", "10.0.0.2"), mknh("if2", "10.0.0.3"),
            mknh("if4", "10.0.0.5"), mknh("if6", "10.0.0.7")}

    # Delete nexthop if2 from the parent route 0.0.0.0/0.
    rt.put_route(mkr('1.0.0.0/8', [mknh('if0', "10.0.0.1"), mknh("if1", "10.0.0.2"),
                                       mknh("if3", "10.0.0.4"), mknh("if4", "10.0.0.5"),
                                       mknh("if5", "10.0.0.6"), mknh("if6", "10.0.0.7")]))

    # Testing only rib and fib next hops
    assert rt.destinations.get('1.0.0.0/8').best_route.next_hops == \
           {mknh('if0', "10.0.0.1"), mknh("if1", "10.0.0.2"), mknh("if3", "10.0.0.4"),
            mknh("if4", "10.0.0.5"), mknh("if5", "10.0.0.6"), mknh("if6", "10.0.0.7")}
    assert set(rt.fib.routes[mkp('1.0.0.0/8')].next_hops) == \
           {mknh('if0', "10.0.0.1"), mknh("if1", "10.0.0.2"), mknh("if3", "10.0.0.4"),
            mknh("if4", "10.0.0.5"), mknh("if5", "10.0.0.6"), mknh("if6", "10.0.0.7")}

    assert rt.destinations.get('1.1.0.0/16').best_route.negative_next_hops == \
           {mknh('if0', "10.0.0.1")}
    assert rt.destinations.get('1.1.0.0/16').best_route.next_hops == \
           {mknh("if1", "10.0.0.2"), mknh("if3", "10.0.0.4"), mknh("if4", "10.0.0.5"),
            mknh("if5", "10.0.0.6"), mknh("if6", "10.0.0.7")}
    assert set(rt.fib.routes[mkp('1.1.0.0/16')].next_hops) == \
           {mknh("if1", "10.0.0.2"), mknh("if3", "10.0.0.4"), mknh("if4", "10.0.0.5"),
            mknh("if5", "10.0.0.6"), mknh("if6", "10.0.0.7")}

    assert rt.destinations.get('1.1.1.0/24').best_route.negative_next_hops == \
           {mknh("if1", "10.0.0.2")}
    assert rt.destinations.get('1.1.1.0/24').best_route.next_hops == \
           {mknh("if3", "10.0.0.4"), mknh("if4", "10.0.0.5"), mknh("if5", "10.0.0.6"),
            mknh("if6", "10.0.0.7")}
    assert set(rt.fib.routes[mkp('1.1.1.0/24')].next_hops) == \
           {mknh("if3", "10.0.0.4"), mknh("if4", "10.0.0.5"), mknh("if5", "10.0.0.6"),
            mknh("if6", "10.0.0.7")}

    assert rt.destinations.get('1.1.2.0/24').best_route.negative_next_hops == \
           {mknh("if2", "10.0.0.3")}
    assert rt.destinations.get('1.1.2.0/24').best_route.next_hops == \
           {mknh("if1", "10.0.0.2"), mknh("if3", "10.0.0.4"), mknh("if4", "10.0.0.5"),
            mknh("if5", "10.0.0.6"), mknh("if6", "10.0.0.7")}
    assert set(rt.fib.routes[mkp('1.1.2.0/24')].next_hops) == \
           {mknh("if1", "10.0.0.2"), mknh("if3", "10.0.0.4"), mknh("if4", "10.0.0.5"),
            mknh("if5", "10.0.0.6"), mknh("if6", "10.0.0.7")}

    assert rt.destinations.get('1.2.0.0/16').best_route.negative_next_hops == \
           {mknh("if3", "10.0.0.4")}
    assert rt.destinations.get('1.2.0.0/16').best_route.next_hops == \
           {mknh('if0', "10.0.0.1"), mknh("if1", "10.0.0.2"), mknh("if4", "10.0.0.5"),
            mknh("if5", "10.0.0.6"), mknh("if6", "10.0.0.7")}
    assert set(rt.fib.routes[mkp('1.2.0.0/16')].next_hops) == \
           {mknh('if0', "10.0.0.1"), mknh("if1", "10.0.0.2"), mknh("if4", "10.0.0.5"),
            mknh("if5", "10.0.0.6"), mknh("if6", "10.0.0.7")}

    assert rt.destinations.get('1.2.1.0/24').best_route.negative_next_hops == \
           {mknh("if4", "10.0.0.5")}
    assert rt.destinations.get('1.2.1.0/24').best_route.next_hops == \
           {mknh('if0', "10.0.0.1"), mknh("if1", "10.0.0.2"), mknh("if5", "10.0.0.6"),
            mknh("if6", "10.0.0.7")}
    assert set(rt.fib.routes[mkp('1.2.1.0/24')].next_hops) == \
           {mknh('if0', "10.0.0.1"), mknh("if1", "10.0.0.2"), mknh("if5", "10.0.0.6"),
            mknh("if6", "10.0.0.7")}

    assert rt.destinations.get('1.2.2.0/24').best_route.negative_next_hops == \
           {mknh("if5", "10.0.0.6")}
    assert rt.destinations.get('1.2.2.0/24').best_route.next_hops == \
           {mknh('if0', "10.0.0.1"), mknh("if1", "10.0.0.2"), mknh("if4", "10.0.0.5"),
            mknh("if6", "10.0.0.7")}
    assert set(rt.fib.routes[mkp('1.2.2.0/24')].next_hops) == \
           {mknh('if0', "10.0.0.1"), mknh("if1", "10.0.0.2"), mknh("if4", "10.0.0.5"),
            mknh("if6", "10.0.0.7")}

    # Delete all routes from the RIB.
    rt.del_route(mkp("1.0.0.0/8"), S)
    rt.del_route(mkp("1.1.0.0/16"), S)
    rt.del_route(mkp("1.1.1.0/24"), S)
    rt.del_route(mkp("1.1.2.0/24"), S)
    rt.del_route(mkp("1.2.0.0/16"), S)
    rt.del_route(mkp("1.2.1.0/24"), S)
    rt.del_route(mkp("1.2.2.0/24"), S)

    # The RIB must be empty.
    assert not rt.destinations.keys()
    # The FIB must be empty.
    assert not rt.fib.routes.keys()


def test_cli_table():
    add_missing_methods_to_thrift()
    route_table = mkrt()
    nh1 = mknh("if1", "1.1.1.1")
    nh2 = mknh("if2", "2.2.2.2")
    nh3 = mknh("if3", None)
    nh4 = mknh("if4", "4.4.4.4")
    route_table.put_route(mkr("2.2.2.0/24", N))
    route_table.put_route(mkr("1.1.1.0/24", [nh1]))
    route_table.put_route(mkr("0.0.0.0/0", [nh1, nh2]))
    route_table.put_route(mkr("2.2.0.0/16", [nh3], [nh4]))
    route_table.put_route(mkr("1.1.1.0/24", N))
    route_table.put_route(mkr("4.4.4.0/24", [], [nh2, nh3]))
    tab_str = route_table.cli_table().to_string()
    assert (tab_str == "+------------+-----------+----------------------+\n"
                       "| Prefix     | Owner     | Next-hops            |\n"
                       "+------------+-----------+----------------------+\n"
                       "| 0.0.0.0/0  | South SPF | if1 1.1.1.1          |\n"
                       "|            |           | if2 2.2.2.2          |\n"
                       "+------------+-----------+----------------------+\n"
                       "| 1.1.1.0/24 | South SPF | if1 1.1.1.1          |\n"
                       "+------------+-----------+----------------------+\n"
                       "| 1.1.1.0/24 | North SPF |                      |\n"
                       "+------------+-----------+----------------------+\n"
                       "| 2.2.0.0/16 | South SPF | if3                  |\n"
                       "|            |           | Negative if4 4.4.4.4 |\n"
                       "+------------+-----------+----------------------+\n"
                       "| 2.2.2.0/24 | North SPF |                      |\n"
                       "+------------+-----------+----------------------+\n"
                       "| 4.4.4.0/24 | South SPF | Negative if2 2.2.2.2 |\n"
                       "|            |           | Negative if3         |\n"
                       "+------------+-----------+----------------------+\n")
