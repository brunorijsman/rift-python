from pytest import fixture

from constants import ADDRESS_FAMILY_IPV4, OWNER_N_SPF, OWNER_S_SPF
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

def mkr(prefix_str, next_hops, owner=OWNER_S_SPF):
    # Make a RIB route
    if next_hops is None:
        next_hops = []
    return RibRoute(mkp(prefix_str), owner, next_hops)

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

def check_rib_route(rt, prefix_str, exp_next_hops, exp_owner=OWNER_S_SPF):
    assert prefix_str in rt.destinations
    best_rib_route = rt.destinations[prefix_str].best_route()
    assert best_rib_route is not None
    assert str(best_rib_route.prefix) == prefix_str
    assert best_rib_route.owner == exp_owner
    assert sorted(best_rib_route.next_hops) == sorted(exp_next_hops)

def check_rib_route_absent(rt, prefix_str):
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
    assert prefix not in fib.fib_routes

@fixture(autouse=True)
def run_before_every_test_case():
    add_missing_methods_to_thrift()

def test_default_route_only():
    # Test slide 55 in Pascal's "negative disaggregation" presentation:
    # Just a default route with positive next-hops; there are no more specific routes
    rt = mkrt()
    default_prefix = "0.0.0.0/0"
    default_next_hops = [mknh_pos("if0", "10.0.0.1"),
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
    default_next_hops = [mknh_pos("if0", "10.0.0.1"),
                         mknh_pos("if1", "10.0.0.2"),
                         mknh_pos("if2", "10.0.0.3"),
                         mknh_pos("if3", "10.0.0.4")]
    default_route = mkr(default_prefix, default_next_hops)
    rt.put_route(default_route)
    check_rib_route(rt, default_prefix, default_next_hops)
    check_fib_route(rt, default_prefix, default_next_hops)
    # Add a more specific child route with a negative next-hop
    child_prefix = "10.0.0.0/16"
    child_rib_next_hops = [mknh_neg("if0", "10.0.0.1")]
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
    default_next_hops = [mknh_pos("if0", "10.0.0.1"),
                         mknh_pos("if1", "10.0.0.2"),
                         mknh_pos("if2", "10.0.0.3"),
                         mknh_pos("if3", "10.0.0.4")]
    default_route = mkr(default_prefix, default_next_hops)
    rt.put_route(default_route)
    check_rib_route(rt, default_prefix, default_next_hops)
    check_fib_route(rt, default_prefix, default_next_hops)
    # Add first more specific child route with a negative next-hop
    first_child_prefix = "10.0.0.0/16"
    first_child_rib_next_hops = [mknh_neg("if0", "10.0.0.1")]
    first_child_route = mkr(first_child_prefix, first_child_rib_next_hops)
    rt.put_route(first_child_route)
    check_rib_route(rt, first_child_prefix, first_child_rib_next_hops)
    # Add second more specific child route with a negative next-hop
    second_child_prefix = "10.1.0.0/16"
    second_child_rib_next_hops = [mknh_neg("if3", "10.0.0.4")]
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
    default_next_hops = [mknh_pos("if0", "10.0.0.1"),
                         mknh_pos("if1", "10.0.0.2"),
                         mknh_pos("if2", "10.0.0.3"),
                         mknh_pos("if3", "10.0.0.4")]
    default_route = mkr(default_prefix, default_next_hops)
    rt.put_route(default_route)
    check_rib_route(rt, default_prefix, default_next_hops)
    check_fib_route(rt, default_prefix, default_next_hops)
    # Add first more specific child route with a negative next-hop
    first_child_prefix = "10.0.0.0/16"
    first_child_rib_next_hops = [mknh_neg("if0", "10.0.0.1")]
    first_child_route = mkr(first_child_prefix, first_child_rib_next_hops)
    rt.put_route(first_child_route)
    check_rib_route(rt, first_child_prefix, first_child_rib_next_hops)
    # Add second more specific child route with a negative next-hop
    second_child_prefix = "10.1.0.0/16"
    second_child_rib_next_hops = [mknh_neg("if3", "10.0.0.4")]
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
    new1_default_next_hops = [mknh_pos("if0", "10.0.0.1"),
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
    new2_default_next_hops = [mknh_pos("if0", "10.0.0.1"),
                              mknh_pos("if1", "10.0.0.2")]
    new2_default_route = mkr(default_prefix, new2_default_next_hops)
    rt.put_route(new2_default_route)
    check_rib_route(rt, default_prefix, new2_default_next_hops)
    check_fib_route(rt, default_prefix, new2_default_next_hops)
    # Check updated negative to positive next-hop conversion in FIB for the first child
    first_child_new2_fib_next_hops = [mknh_pos("if1", "10.0.0.2")]
    check_fib_route(rt, first_child_prefix, first_child_new2_fib_next_hops)
    # Check updated negative to positive next-hop conversion in FIB for the second child; the
    # second child ends up with the exact same set of next-hops as the parent route, so it is
    # superfluous.
    check_fib_route_absent(rt, second_child_prefix)

def test_parent_with_negative_child_and_negative_grandchild():
    # Test slides 59 in Pascal's "negative disaggregation" presentation.
    # Start with a parent default route with some positive next-hops
    rt = mkrt()
    default_prefix = "0.0.0.0/0"
    default_next_hops = [mknh_pos("if0", "10.0.0.1"),
                         mknh_pos("if1", "10.0.0.2"),
                         mknh_pos("if2", "10.0.0.3"),
                         mknh_pos("if3", "10.0.0.4")]
    default_route = mkr(default_prefix, default_next_hops)
    rt.put_route(default_route)
    check_rib_route(rt, default_prefix, default_next_hops)
    check_fib_route(rt, default_prefix, default_next_hops)
    # Add a more specific child route with a negative next-hop
    child_prefix = "10.0.0.0/16"
    child_rib_next_hops = [mknh_neg("if0", "10.0.0.1")]
    child_route = mkr(child_prefix, child_rib_next_hops)
    rt.put_route(child_route)
    check_rib_route(rt, child_prefix, child_rib_next_hops)
    # Add an even more specific grand-child route with a negative next-hop
    grand_child_prefix = "10.0.10.0/24"
    grand_child_rib_next_hops = [mknh_neg("if1", "10.0.0.2")]
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
    default_next_hops = [mknh_pos("if0", "10.0.0.1"),
                         mknh_pos("if1", "10.0.0.2"),
                         mknh_pos("if2", "10.0.0.3"),
                         mknh_pos("if3", "10.0.0.4")]
    default_route = mkr(default_prefix, default_next_hops)
    rt.put_route(default_route)
    check_rib_route(rt, default_prefix, default_next_hops)
    check_fib_route(rt, default_prefix, default_next_hops)
    # Add a more specific child route with a negative next-hop
    child_prefix = "10.0.0.0/16"
    child_rib_next_hops = [mknh_neg("if0", "10.0.0.1")]
    child_route = mkr(child_prefix, child_rib_next_hops)
    rt.put_route(child_route)
    check_rib_route(rt, child_prefix, child_rib_next_hops)
    # Add an even more specific grand-child route with a negative next-hop
    grand_child_prefix = "10.0.10.0/24"
    grand_child_rib_next_hops = [mknh_neg("if1", "10.0.0.2")]
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
    new1_default_next_hops = [mknh_pos("if0", "10.0.0.1"),
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
    default_next_hops = [mknh_pos("if0", "10.0.0.1"),
                         mknh_pos("if1", "10.0.0.2"),
                         mknh_pos("if2", "10.0.0.3"),
                         mknh_pos("if3", "10.0.0.4")]
    default_route = mkr(default_prefix, default_next_hops)
    rt.put_route(default_route)
    check_rib_route(rt, default_prefix, default_next_hops)
    check_fib_route(rt, default_prefix, default_next_hops)
    # Add a more specific child route with a negative next-hop
    child_prefix = "10.0.0.0/16"
    child_rib_next_hops = [mknh_neg("if0", "10.0.0.1")]
    child_route = mkr(child_prefix, child_rib_next_hops)
    rt.put_route(child_route)
    check_rib_route(rt, child_prefix, child_rib_next_hops)
    # Add an even more specific grand-child route with a negative next-hop
    grand_child_prefix = "10.0.10.0/24"
    grand_child_rib_next_hops = [mknh_neg("if1", "10.0.0.2")]
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
    new1_default_next_hops = [mknh_pos("if0", "10.0.0.1"),
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
    default_next_hops = [mknh_pos("if0", "10.0.0.1"),
                         mknh_pos("if1", "10.0.0.2"),
                         mknh_pos("if2", "10.0.0.3"),
                         mknh_pos("if3", "10.0.0.4")]
    default_route = mkr(default_prefix, default_next_hops)
    rt.put_route(default_route)
    check_rib_route(rt, default_prefix, default_next_hops)
    check_fib_route(rt, default_prefix, default_next_hops)
    # Add a more specific child route with a negative next-hop
    child_prefix = "10.0.0.0/16"
    child_rib_next_hops = [mknh_neg("if0", "10.0.0.1")]
    child_route = mkr(child_prefix, child_rib_next_hops)
    rt.put_route(child_route)
    check_rib_route(rt, child_prefix, child_rib_next_hops)
    # Add an even more specific grand-child route with a negative next-hop
    grand_child_prefix = "10.0.10.0/24"
    grand_child_rib_next_hops = [mknh_neg("if1", "10.0.0.2")]
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
    # Check that the parent route is absent from the RIB and FIB
    check_rib_route_absent(rt, default_prefix)
    check_fib_route_absent(rt, default_prefix)
    # Check that the child route is present in the RIB and a discard route in the FIB
    check_rib_route(rt, child_prefix, child_rib_next_hops)
    no_next_hops = []
    check_fib_route(rt, child_prefix, no_next_hops)
    # Check that the grand-child route is present in the RIB and absent from the FIB because it
    # is a superfluous route (grand-child is discard, but it parent -the child- is also discard)
    check_rib_route(rt, grand_child_prefix, grand_child_rib_next_hops)
    check_fib_route_absent(rt, grand_child_prefix)

def test_discard_child_from_fib_when_no_next_hops_left():
    # Tests if a route becomes unreachable (i.e. becomes a discard route) after all next hops are
    # negatively disaggregated
    # Start with a parent default route with some positive next-hops
    rt = mkrt()
    default_prefix = "0.0.0.0/0"
    default_next_hops = [mknh_pos("if0", "10.0.0.1"),
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
    child_rib_next_hops = [mknh_neg("if0", "10.0.0.1"),
                           mknh_neg("if1", "10.0.0.2"),
                           mknh_neg("if2", "10.0.0.3"),
                           mknh_neg("if3", "10.0.0.4")]
    child_route = mkr(child_prefix, child_rib_next_hops)
    rt.put_route(child_route)
    check_rib_route(rt, child_prefix, child_rib_next_hops)
    # Check that the child route in the FIB is now a discard route
    no_next_hops = []
    check_fib_route(rt, child_prefix, no_next_hops)
    # Go back to the parent, and check it's next-hops haven't changed
    check_fib_route(rt, default_prefix, default_next_hops)

def test_restore_child_from_to_when_neg_next_hop_removed():
    # Tests if an unreachable route becomes reachable after a negative disaggregation is removed
    # Start with a parent default route with some positive next-hops
    rt = mkrt()
    default_prefix = "0.0.0.0/0"
    default_next_hops = [mknh_pos("if0", "10.0.0.1"),
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
    child_rib_next_hops = [mknh_neg("if0", "10.0.0.1"),
                           mknh_neg("if1", "10.0.0.2"),
                           mknh_neg("if2", "10.0.0.3"),
                           mknh_neg("if3", "10.0.0.4")]
    child_route = mkr(child_prefix, child_rib_next_hops)
    rt.put_route(child_route)
    check_rib_route(rt, child_prefix, child_rib_next_hops)
    # Check that the child route in the FIB is now a discard route
    no_next_hops = []
    check_fib_route(rt, child_prefix, no_next_hops)
    # Go back to the parent, and check it's next-hops haven't changed
    check_fib_route(rt, default_prefix, default_next_hops)
    # Remove one of the negative next-hops of the child route (namely if2 10.0.0.3)
    new_child_rib_next_hops = [mknh_neg("if0", "10.0.0.1"),
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
    default_next_hops = [mknh_pos("if0", "10.0.0.1"),
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
    child_rib_next_hops = [mknh_neg("if0", "10.0.0.1"),
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
    grand_child_rib_next_hops = [mknh_neg("if1", "10.0.0.2")]
    grand_child_route = mkr(grand_child_prefix, grand_child_rib_next_hops)
    rt.put_route(grand_child_route)
    check_rib_route(rt, grand_child_prefix, grand_child_rib_next_hops)
    # Check that the child route in the FIB is now a discard route
    no_next_hops = []
    check_fib_route(rt, child_prefix, no_next_hops)
    # Check that the grand-child route in the FIB is now absent because it is superfluous (it
    # would have been a discard route, but it's parent -the child route- is also a discard route)
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
    default_next_hops = [mknh_pos("if0", "10.0.0.1"),
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
    child_rib_next_hops = [mknh_neg("if0", "10.0.0.1"),
                           mknh_neg("if1", "10.0.0.2"),
                           mknh_neg("if2", "10.0.0.3"),
                           mknh_neg("if3", "10.0.0.4")]
    child_route = mkr(child_prefix, child_rib_next_hops)
    rt.put_route(child_route)
    check_rib_route(rt, child_prefix, child_rib_next_hops)
    # Add an even more specific grand-child route with a positive next-hops that puts one of the
    # next-hops that was removed by its parent (i.e. by the child-route) explicitly back.
    grand_child_prefix = "10.0.10.0/24"
    grand_child_next_hops = [mknh_pos("if4", "10.0.0.5")]
    grand_child_route = mkr(grand_child_prefix, grand_child_next_hops)
    rt.put_route(grand_child_route)
    check_rib_route(rt, grand_child_prefix, grand_child_next_hops)
    # Check that the child route in the FIB is now a discard route
    no_next_hops = []
    check_fib_route(rt, child_prefix, no_next_hops)
    # Check that the grand-child route is present in the FIB
    check_fib_route(rt, grand_child_prefix, grand_child_next_hops)
    # Go back to the parent, and check it's next-hops haven't changed
    check_fib_route(rt, default_prefix, default_next_hops)

def test_keep_grand_child_in_fib_replace_positive_next_hop():
    # Test that a grand-child route is present in the FIB in the following scenario:
    # - A parent route has some positive next-hops
    # - A child route removes all of the next-hops with negative next-hops
    # - The grand-child route puts one of the removed next-hops explicitly back with a positive
    #   next-hop.
    # Start with a parent default route with some positive next-hops
    rt = mkrt()
    default_prefix = "0.0.0.0/0"
    default_next_hops = [mknh_pos("if0", "10.0.0.1"),
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
    child_rib_next_hops = [mknh_neg("if0", "10.0.0.1"),
                           mknh_neg("if1", "10.0.0.2"),
                           mknh_neg("if2", "10.0.0.3"),
                           mknh_neg("if3", "10.0.0.4")]
    child_route = mkr(child_prefix, child_rib_next_hops)
    rt.put_route(child_route)
    check_rib_route(rt, child_prefix, child_rib_next_hops)
    # Add an even more specific grand-child route with a positive next-hops that puts one of the
    # next-hops that was removed by its parent (i.e. by the child-route) explicitly back.
    grand_child_prefix = "10.0.10.0/24"
    grand_child_next_hops = [mknh_pos("if1", "10.0.0.2")]
    grand_child_route = mkr(grand_child_prefix, grand_child_next_hops)
    rt.put_route(grand_child_route)
    check_rib_route(rt, grand_child_prefix, grand_child_next_hops)
    # Check that the child route in the FIB is now a discard route
    no_next_hops = []
    check_fib_route(rt, child_prefix, no_next_hops)
    # Check that the grand-child route is present from the FIB
    check_fib_route(rt, grand_child_prefix, grand_child_next_hops)
    # Go back to the parent, and check it's next-hops haven't changed
    check_fib_route(rt, default_prefix, default_next_hops)

def test_add_two_parent_routes_same_destination_different_owners():
    # Add two parent routes with different owners to the same destination; test that the
    # south-SPF parent route is preferred and used by children for negative to positive next-hop
    # conversion.
    # Add a north-SPF parent default route with some positive next-hops
    rt = mkrt()
    default_prefix = "0.0.0.0/0"
    north_spf_default_next_hops = [mknh_pos("if0", "10.0.0.1"),
                                   mknh_pos("if1", "10.0.0.2"),
                                   mknh_pos("if2", "10.0.0.3")]
    north_spf_default_route = mkr(default_prefix, north_spf_default_next_hops, OWNER_N_SPF)
    rt.put_route(north_spf_default_route)
    check_rib_route(rt, default_prefix, north_spf_default_next_hops, OWNER_N_SPF)
    # The default route in the FIB contains the next-hops of the north-SPF default route
    check_fib_route(rt, default_prefix, north_spf_default_next_hops)
    # Add a more specific child route with a negative next-hop
    child_prefix = "10.0.0.0/16"
    child_rib_next_hops = [mknh_neg("if2", "10.0.0.3")]
    child_route = mkr(child_prefix, child_rib_next_hops)
    rt.put_route(child_route)
    check_rib_route(rt, child_prefix, child_rib_next_hops)
    # Check that the child route used the north-SPF default route to convert negative next-hops
    # to positive next-hops.
    child_fib_next_hops = [mknh_pos("if0", "10.0.0.1"),
                           mknh_pos("if1", "10.0.0.2")]
    check_fib_route(rt, child_prefix, child_fib_next_hops)
    # Add a south-SPF parent default route with some different (overlapping) positive next-hops
    south_spf_default_next_hops = [mknh_pos("if1", "10.0.0.2"),
                                   mknh_pos("if2", "10.0.0.3"),
                                   mknh_pos("if3", "10.0.0.4")]
    south_spf_default_route = mkr(default_prefix, south_spf_default_next_hops, OWNER_S_SPF)
    rt.put_route(south_spf_default_route)
    check_rib_route(rt, default_prefix, south_spf_default_next_hops, OWNER_S_SPF)
    # The default route FIB next-hops have been replaced by the the next-hops of the north-SPF
    # default route
    check_fib_route(rt, default_prefix, south_spf_default_next_hops)
    # Check that the child route now uses the south-SPF default route to convert negative next-hops
    # to positive next-hops.
    new_child_fib_next_hops = [mknh_pos("if1", "10.0.0.2"),
                               mknh_pos("if3", "10.0.0.4")]
    check_fib_route(rt, child_prefix, new_child_fib_next_hops)
    # Remove the south-SPF parent default route again
    rt.del_route(mkp(default_prefix), OWNER_S_SPF)
    # The north-SPF RIB route became the best route again
    check_rib_route(rt, default_prefix, north_spf_default_next_hops, OWNER_N_SPF)
    # Check that the child route now uses the noth-SPF default route again to convert negative
    # next-hops to positive next-hops.
    check_fib_route(rt, child_prefix, child_fib_next_hops)

def test_add_two_child_routes_same_destination_different_owners():
    # Add two child routes with different owners to the same destination. Test that the
    # south-SPF child route is preferred. Test that the parent FIB route is used, even if the parent
    # FIB route came from a north-SPF RIB route.
    # Add a north-SPF parent default route with some positive next-hops
    rt = mkrt()
    default_prefix = "0.0.0.0/0"
    north_spf_default_next_hops = [mknh_pos("if0", "10.0.0.1"),
                                   mknh_pos("if1", "10.0.0.2"),
                                   mknh_pos("if2", "10.0.0.3"),
                                   mknh_pos("if3", "10.0.0.4")]
    north_spf_default_route = mkr(default_prefix, north_spf_default_next_hops, OWNER_N_SPF)
    rt.put_route(north_spf_default_route)
    check_rib_route(rt, default_prefix, north_spf_default_next_hops, OWNER_N_SPF)
    # Add a north-SPF child route with a negative next-hop
    child_prefix = "10.0.0.0/16"
    north_spf_child_rib_next_hops = [mknh_neg("if2", "10.0.0.3")]
    child_route = mkr(child_prefix, north_spf_child_rib_next_hops, OWNER_N_SPF)
    rt.put_route(child_route)
    check_rib_route(rt, child_prefix, north_spf_child_rib_next_hops, OWNER_N_SPF)
    # Check that RIB to FIB next-hop conversion uses the north-SPF parent and the north-SPF child
    north_spf_child_fib_next_hops = [mknh_pos("if0", "10.0.0.1"),
                                     mknh_pos("if1", "10.0.0.2"),
                                     mknh_pos("if3", "10.0.0.4")]
    check_fib_route(rt, child_prefix, north_spf_child_fib_next_hops)
    # Add a south-SPF child route with a different negative next-hop
    south_spf_child_rib_next_hops = [mknh_neg("if1", "10.0.0.2")]
    child_route = mkr(child_prefix, south_spf_child_rib_next_hops, OWNER_S_SPF)
    rt.put_route(child_route)
    check_rib_route(rt, child_prefix, south_spf_child_rib_next_hops, OWNER_S_SPF)
    # Check that RIB to FIB next-hop conversion uses the north-SPF parent and the north-SPF child
    south_spf_child_fib_next_hops = [mknh_pos("if0", "10.0.0.1"),
                                     mknh_pos("if2", "10.0.0.3"),
                                     mknh_pos("if3", "10.0.0.4")]
    check_fib_route(rt, child_prefix, south_spf_child_fib_next_hops)

def test_superfluous_positive_next_hop():
    # Test that installation of a superfluous route in the FIB is prevented when the child's FIB
    # next-hops are the same as the parent's next-hops because.
    # Specific scenario: the child has the exact same positive next-hops as the parent.
    # Start with a parent default route with some positive next-hops
    rt = mkrt()
    default_prefix = "0.0.0.0/0"
    default_next_hops = [mknh_pos("if0", "10.0.0.1"),
                         mknh_pos("if1", "10.0.0.2"),
                         mknh_pos("if2", "10.0.0.3"),
                         mknh_pos("if3", "10.0.0.4")]
    default_route = mkr(default_prefix, default_next_hops)
    rt.put_route(default_route)
    check_rib_route(rt, default_prefix, default_next_hops)
    check_fib_route(rt, default_prefix, default_next_hops)
    # Add a more specific child route with the exact same set of positive next-hops as the parent
    child_prefix = "10.0.0.0/16"
    child_rib_next_hops = default_next_hops
    child_route = mkr(child_prefix, child_rib_next_hops)
    rt.put_route(child_route)
    check_rib_route(rt, child_prefix, child_rib_next_hops)
    # Check that the negative route is not installed in the FIB because it is superfluous
    check_fib_route_absent(rt, child_prefix)
    ###@@@ no longer superfluous

def test_superfluous_negative_next_hop():
    # Test that installation of a superfluous route in the FIB is prevented when the child's FIB
    # next-hops are the same as the parent's next-hops because.
    # Specific scenario: the child has negative next-hops that don't actually remove any next-hops
    # from the set of positive next-hops of the parent.
    # Start with a parent default route with some positive next-hops
    rt = mkrt()
    default_prefix = "0.0.0.0/0"
    default_next_hops = [mknh_pos("if0", "10.0.0.1"),
                         mknh_pos("if1", "10.0.0.2"),
                         mknh_pos("if2", "10.0.0.3"),
                         mknh_pos("if3", "10.0.0.4")]
    default_route = mkr(default_prefix, default_next_hops)
    rt.put_route(default_route)
    check_rib_route(rt, default_prefix, default_next_hops)
    check_fib_route(rt, default_prefix, default_next_hops)
    # Add a more specific child route with negative next-hops that are not equal to any of the
    # positive next-hops in the parent route.
    child_prefix = "10.0.0.0/16"
    child_rib_next_hops = [mknh_neg("if4", "10.0.0.5"),
                           mknh_neg("if5", "10.0.0.6")]
    child_route = mkr(child_prefix, child_rib_next_hops)
    rt.put_route(child_route)
    check_rib_route(rt, child_prefix, child_rib_next_hops)
    # Check that the negative child route is not installed in the FIB because it is superfluous
    check_fib_route_absent(rt, child_prefix)
    ###@@@ no longer superfluous

def test_superfluous_discard_parent_also_discard():
    # Test that installation of a superfluous route in the FIB is prevented when the child's FIB
    # next-hops are the same as the parent's next-hops because.
    # Specific scenario: a child ends up with a discard route, but its parent also is a discard
    # route
    # Start with a parent default route with some positive next-hops
    rt = mkrt()
    default_prefix = "0.0.0.0/0"
    default_next_hops = [mknh_pos("if0", "10.0.0.1"),
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
    child_rib_next_hops = [mknh_neg("if0", "10.0.0.1"),
                           mknh_neg("if1", "10.0.0.2"),
                           mknh_neg("if2", "10.0.0.3"),
                           mknh_neg("if3", "10.0.0.4")]
    child_route = mkr(child_prefix, child_rib_next_hops)
    rt.put_route(child_route)
    check_rib_route(rt, child_prefix, child_rib_next_hops)
    # Check that the child route in the FIB is now a discard route
    no_next_hops = []
    check_fib_route(rt, child_prefix, no_next_hops)
    # Create a discard grand-child route (empty list of next-hops means discard)
    grand_child_prefix = "10.0.1.0/24"
    grand_child_rib_next_hops = []
    grand_child_route = mkr(grand_child_prefix, grand_child_rib_next_hops)
    rt.put_route(grand_child_route)
    check_rib_route(rt, grand_child_prefix, grand_child_rib_next_hops)
    # Check that the grand-child route is not installed in the FIB because it is superfluous
    check_fib_route_absent(rt, grand_child_prefix)
    # Remove the child route
    rt.del_route(mkp(child_prefix), OWNER_S_SPF)
    # Check that the child route is now absent from the FIB
    check_fib_route_absent(rt, child_prefix)
    # The grand-child route is now not superfluous anymore and should be installed as a discard
    # route
    ###@@@ FAILS
    check_fib_route(rt, grand_child_prefix, no_next_hops)

def test_superfluous_discard_no_parent():
    # Test that installation of a superfluous route in the FIB is prevented when the child's FIB
    # next-hops are the same as the parent's next-hops because.
    # Specific scenario: the child ends up with a discard route, but there is no parent
    ###@@@
    pass

# # Deep nesting of more specific routes: parent, child, grand child, grand-grand child, ...
# def test_prop_deep_nesting():
#     add_missing_methods_to_thrift()
#     rt = mkrt()
#     # Default route
#     new_default_next_hops = [mknh("if0", "10.0.0.1"), mknh("if1", "10.0.0.2"),
#                              mknh("if2", "10.0.0.3"), mknh("if3", "10.0.0.4"),
#                              mknh("if4", "10.0.0.5")]
#     new_default_route = mkr(DEFAULT_PREFIX, new_default_next_hops)
#     rt.put_route(new_default_route)
#     # Child route
#     child_prefix = '1.0.0.0/8'
#     child_route = mkr(child_prefix, [], [mknh("if0", "10.0.0.1")])
#     rt.put_route(child_route)
#     # Grand child route
#     g_child_prefix = '1.128.0.0/9'
#     g_child_route = mkr(g_child_prefix, [], [mknh("if1", "10.0.0.2")])
#     rt.put_route(g_child_route)
#     # Grand-grand child route
#     gg_child_prefix = '1.192.0.0/10'
#     gg_child_route = mkr(gg_child_prefix, [], [mknh("if2", "10.0.0.3")])
#     rt.put_route(gg_child_route)
#     # Grand-grand-grand child route
#     ggg_child_prefix = '1.224.0.0/11'
#     ggg_child_route = mkr(ggg_child_prefix, [], [mknh("if3", "10.0.0.4")])
#     rt.put_route(ggg_child_route)
#     # Grand-grand-grand-grand child route
#     gggg_child_prefix = '1.240.0.0/12'
#     gggg_child_route = mkr(gggg_child_prefix, [], [mknh("if4", "10.0.0.5")])
#     rt.put_route(gggg_child_route)

#     # Default route asserts
#     assert rt.destinations.get(DEFAULT_PREFIX).best_route == new_default_route
#     assert rt.destinations.get(DEFAULT_PREFIX).best_route.next_hops == \
#            {mknh("if0", "10.0.0.1"), mknh("if1", "10.0.0.2"), mknh("if2", "10.0.0.3"),
#             mknh("if3", "10.0.0.4"), mknh("if4", "10.0.0.5")}
#     assert set(rt.fib.routes[mkp(DEFAULT_PREFIX)].next_hops) == new_default_route.next_hops
#     # Child route asserts
#     assert rt.destinations.get(child_prefix).best_route == child_route
#     assert rt.destinations.get(child_prefix).best_route.next_hops == \
#            {mknh("if1", "10.0.0.2"), mknh("if2", "10.0.0.3"), mknh("if3", "10.0.0.4"),
#             mknh("if4", "10.0.0.5")}
#     assert set(rt.fib.routes[mkp(child_prefix)].next_hops) == child_route.next_hops
#     # Grand-child route asserts
#     assert rt.destinations.get(g_child_prefix).best_route == g_child_route
#     assert rt.destinations.get(g_child_prefix).best_route.next_hops == \
#            {mknh("if2", "10.0.0.3"), mknh("if3", "10.0.0.4"), mknh("if4", "10.0.0.5")}
#     assert set(rt.fib.routes[mkp(g_child_prefix)].next_hops) == g_child_route.next_hops
#     # Grand-grand child route asserts
#     assert rt.destinations.get(gg_child_prefix).best_route == gg_child_route
#     assert rt.destinations.get(gg_child_prefix).best_route.next_hops == \
#            {mknh("if3", "10.0.0.4"), mknh("if4", "10.0.0.5")}
#     assert set(rt.fib.routes[mkp(gg_child_prefix)].next_hops) == gg_child_route.next_hops
#     # Grand-grand-grand child route asserts
#     assert rt.destinations.get(ggg_child_prefix).best_route == ggg_child_route
#     assert rt.destinations.get(ggg_child_prefix).best_route.next_hops == {mknh("if4", "10.0.0.5")}
#     assert set(rt.fib.routes[mkp(ggg_child_prefix)].next_hops) == ggg_child_route.next_hops
#     # Grand-grand-grand-grand child route asserts
#     assert rt.destinations.get(gggg_child_prefix).best_route == gggg_child_route
#     assert rt.destinations.get(gggg_child_prefix).best_route.next_hops == set()
#     assert set(rt.fib.routes[mkp(gggg_child_prefix)].next_hops) == gggg_child_route.next_hops

#     # Delete if2 from default route
#     new_default_route = mkr(DEFAULT_PREFIX, [mknh("if0", "10.0.0.1"), mknh("if1", "10.0.0.2"),
#                                                 mknh("if3", "10.0.0.4"), mknh("if4", "10.0.0.5")])
#     rt.put_route(new_default_route)

#     # Default route asserts
#     assert rt.destinations.get(DEFAULT_PREFIX).best_route == new_default_route
#     assert rt.destinations.get(DEFAULT_PREFIX).best_route.next_hops == \
#            {mknh("if0", "10.0.0.1"), mknh("if1", "10.0.0.2"),
#             mknh("if3", "10.0.0.4"), mknh("if4", "10.0.0.5")}
#     assert set(rt.fib.routes[mkp(DEFAULT_PREFIX)].next_hops) == new_default_route.next_hops
#     # Child route asserts
#     assert rt.destinations.get(child_prefix).best_route == child_route
#     assert rt.destinations.get(child_prefix).best_route.next_hops == \
#            {mknh("if1", "10.0.0.2"), mknh("if3", "10.0.0.4"), mknh("if4", "10.0.0.5")}
#     assert set(rt.fib.routes[mkp(child_prefix)].next_hops) == child_route.next_hops
#     # Grand-child route asserts
#     assert rt.destinations.get(g_child_prefix).best_route == g_child_route
#     assert rt.destinations.get(g_child_prefix).best_route.next_hops == \
#            {mknh("if3", "10.0.0.4"), mknh("if4", "10.0.0.5")}
#     assert set(rt.fib.routes[mkp(g_child_prefix)].next_hops) == g_child_route.next_hops
#     # Grand-grand child route asserts
#     assert rt.destinations.get(gg_child_prefix).best_route == gg_child_route
#     assert rt.destinations.get(gg_child_prefix).best_route.next_hops == \
#            {mknh("if3", "10.0.0.4"), mknh("if4", "10.0.0.5")}
#     assert set(rt.fib.routes[mkp(gg_child_prefix)].next_hops) == gg_child_route.next_hops
#     # Grand-grand-grand child route asserts
#     assert rt.destinations.get(ggg_child_prefix).best_route == ggg_child_route
#     assert rt.destinations.get(ggg_child_prefix).best_route.next_hops == {mknh("if4", "10.0.0.5")}
#     assert set(rt.fib.routes[mkp(ggg_child_prefix)].next_hops) == ggg_child_route.next_hops
#     # Grand-grand-grand-grand child route asserts
#     assert rt.destinations.get(gggg_child_prefix).best_route == gggg_child_route
#     assert rt.destinations.get(gggg_child_prefix).best_route.next_hops == set()
#     assert set(rt.fib.routes[mkp(gggg_child_prefix)].next_hops) == gggg_child_route.next_hops

#     rt.del_route(mkp(DEFAULT_PREFIX), S)
#     # Default route asserts
#     assert not rt.destinations.has_key(DEFAULT_PREFIX)
#     # Child route asserts
#     assert rt.destinations.get(child_prefix).best_route == child_route
#     assert rt.destinations.get(child_prefix).best_route.next_hops == set()
#     assert set(rt.fib.routes[mkp(child_prefix)].next_hops) == set()
#     # Grand-child route asserts
#     assert rt.destinations.get(g_child_prefix).best_route == g_child_route
#     assert rt.destinations.get(g_child_prefix).best_route.next_hops == set()
#     assert set(rt.fib.routes[mkp(g_child_prefix)].next_hops) == set()
#     # Grand-grand child route asserts
#     assert rt.destinations.get(gg_child_prefix).best_route == gg_child_route
#     assert rt.destinations.get(gg_child_prefix).best_route.next_hops == set()
#     assert set(rt.fib.routes[mkp(gg_child_prefix)].next_hops) == set()
#     # Grand-grand-grand child route asserts
#     assert rt.destinations.get(ggg_child_prefix).best_route == ggg_child_route
#     assert rt.destinations.get(ggg_child_prefix).best_route.next_hops == set()
#     assert set(rt.fib.routes[mkp(ggg_child_prefix)].next_hops) == set()
#     # Grand-grand-grand-grand child route asserts
#     assert rt.destinations.get(gggg_child_prefix).best_route == gggg_child_route
#     assert rt.destinations.get(gggg_child_prefix).best_route.next_hops == set()
#     assert set(rt.fib.routes[mkp(gggg_child_prefix)].next_hops) == set()

#     rt.del_route(mkp(child_prefix), S)
#     # Child route asserts
#     assert not rt.destinations.has_key(child_prefix)
#     # Grand-child route asserts
#     assert rt.destinations.get(g_child_prefix).best_route == g_child_route
#     assert rt.destinations.get(g_child_prefix).best_route.next_hops == set()
#     assert set(rt.fib.routes[mkp(g_child_prefix)].next_hops) == set()
#     # Grand-grand child route asserts
#     assert rt.destinations.get(gg_child_prefix).best_route == gg_child_route
#     assert rt.destinations.get(gg_child_prefix).best_route.next_hops == set()
#     assert set(rt.fib.routes[mkp(gg_child_prefix)].next_hops) == set()
#     # Grand-grand-grand child route asserts
#     assert rt.destinations.get(ggg_child_prefix).best_route == ggg_child_route
#     assert rt.destinations.get(ggg_child_prefix).best_route.next_hops == set()
#     assert set(rt.fib.routes[mkp(ggg_child_prefix)].next_hops) == set()
#     # Grand-grand-grand-grand child route asserts
#     assert rt.destinations.get(gggg_child_prefix).best_route == gggg_child_route
#     assert rt.destinations.get(gggg_child_prefix).best_route.next_hops == set()
#     assert set(rt.fib.routes[mkp(gggg_child_prefix)].next_hops) == set()

#     rt.del_route(mkp(g_child_prefix), S)
#     # Grand-child route asserts
#     assert not rt.destinations.has_key(g_child_prefix)
#     # Grand-grand child route asserts
#     assert rt.destinations.get(gg_child_prefix).best_route == gg_child_route
#     assert rt.destinations.get(gg_child_prefix).best_route.next_hops == set()
#     assert set(rt.fib.routes[mkp(gg_child_prefix)].next_hops) == set()
#     # Grand-grand-grand child route asserts
#     assert rt.destinations.get(ggg_child_prefix).best_route == ggg_child_route
#     assert rt.destinations.get(ggg_child_prefix).best_route.next_hops == set()
#     assert set(rt.fib.routes[mkp(ggg_child_prefix)].next_hops) == set()
#     # Grand-grand-grand-grand child route asserts
#     assert rt.destinations.get(gggg_child_prefix).best_route == gggg_child_route
#     assert rt.destinations.get(gggg_child_prefix).best_route.next_hops == set()
#     assert set(rt.fib.routes[mkp(gggg_child_prefix)].next_hops) == set()

#     rt.del_route(mkp(gg_child_prefix), S)
#     # Grand-child route asserts
#     assert not rt.destinations.has_key(gg_child_prefix)
#     # Grand-grand-grand child route asserts
#     assert rt.destinations.get(ggg_child_prefix).best_route == ggg_child_route
#     assert rt.destinations.get(ggg_child_prefix).best_route.next_hops == set()
#     assert set(rt.fib.routes[mkp(ggg_child_prefix)].next_hops) == set()
#     # Grand-grand-grand-grand child route asserts
#     assert rt.destinations.get(gggg_child_prefix).best_route == gggg_child_route
#     assert rt.destinations.get(gggg_child_prefix).best_route.next_hops == set()
#     assert set(rt.fib.routes[mkp(gggg_child_prefix)].next_hops) == set()

#     rt.del_route(mkp(ggg_child_prefix), S)
#     # Grand-child route asserts
#     assert not rt.destinations.has_key(ggg_child_prefix)
#     # Grand-grand-grand-grand child route asserts
#     assert rt.destinations.get(gggg_child_prefix).best_route == gggg_child_route
#     assert rt.destinations.get(gggg_child_prefix).best_route.next_hops == set()
#     assert set(rt.fib.routes[mkp(gggg_child_prefix)].next_hops) == set()

#     rt.del_route(mkp(gggg_child_prefix), S)
#     # Grand-grand-grand-grand child route asserts
#     assert not rt.destinations.has_key(gggg_child_prefix)

#     assert not rt.destinations.keys()
#     assert not rt.fib.routes.keys()


# def test_prop_nesting_with_siblings():
#     # Deep nesting of more specific routes using the following tree:
#     #
#     #   1.0.0.0/8 -> S1, S2, S3, S4, S5, S6, S7
#     #    |
#     #    +--- 1.1.0.0/16 -> S1
#     #    |     |
#     #    |     +--- 1.1.1.0/24 -> ~S2
#     #    |     |
#     #    |     +--- 1.1.2.0/24 -> ~S3
#     #    |
#     #    +--- 1.2.0.0/16 -> ~S4
#     #          |
#     #          +--- 1.2.1.0/24 -> ~S5
#     #          |
#     #          +--- 1.2.2.0/24 -> ~S6
#     #
#     # Note: we add the routes in a random order
#     add_missing_methods_to_thrift()
#     rt = mkrt()

#     rt.put_route(mkr("1.2.1.0/24", [], [mknh("if4", "10.0.0.5")]))
#     rt.put_route(mkr("1.1.2.0/24", [], [mknh("if2", "10.0.0.3")]))
#     rt.put_route(mkr("1.1.0.0/16", [], [mknh("if0", "10.0.0.1")]))
#     rt.put_route(mkr("1.1.1.0/24", [], [mknh("if1", "10.0.0.2")]))
#     rt.put_route(mkr("1.2.0.0/16", [], [mknh("if3", "10.0.0.4")]))
#     rt.put_route(mkr("1.0.0.0/8", [mknh("if0", "10.0.0.1"), mknh("if1", "10.0.0.2"),
#                                        mknh("if2", "10.0.0.3"), mknh("if3", "10.0.0.4"),
#                                        mknh("if4", "10.0.0.5"), mknh("if5", "10.0.0.6"),
#                                        mknh("if6", "10.0.0.7")]))
#     rt.put_route(mkr("1.2.2.0/24", [], [mknh("if5", "10.0.0.6")]))

#     # Testing only rib and fib next hops
#     assert rt.destinations.get('1.0.0.0/8').best_route.next_hops == \
#            {mknh("if0", "10.0.0.1"), mknh("if1", "10.0.0.2"), mknh("if2", "10.0.0.3"),
#             mknh("if3", "10.0.0.4"), mknh("if4", "10.0.0.5"), mknh("if5", "10.0.0.6"),
#             mknh("if6", "10.0.0.7")}
#     assert set(rt.fib.routes[mkp('1.0.0.0/8')].next_hops) == \
#            {mknh("if0", "10.0.0.1"), mknh("if1", "10.0.0.2"), mknh("if2", "10.0.0.3"),
#             mknh("if3", "10.0.0.4"), mknh("if4", "10.0.0.5"), mknh("if5", "10.0.0.6"),
#             mknh("if6", "10.0.0.7")}

#     assert rt.destinations.get('1.1.0.0/16').best_route.negative_next_hops == \
#            {mknh("if0", "10.0.0.1")}
#     assert rt.destinations.get('1.1.0.0/16').best_route.next_hops == \
#            {mknh("if1", "10.0.0.2"), mknh("if2", "10.0.0.3"), mknh("if3", "10.0.0.4"),
#             mknh("if4", "10.0.0.5"), mknh("if5", "10.0.0.6"), mknh("if6", "10.0.0.7")}
#     assert set(rt.fib.routes[mkp('1.1.0.0/16')].next_hops) == \
#            {mknh("if1", "10.0.0.2"), mknh("if2", "10.0.0.3"), mknh("if3", "10.0.0.4"),
#             mknh("if4", "10.0.0.5"), mknh("if5", "10.0.0.6"), mknh("if6", "10.0.0.7")}

#     assert rt.destinations.get('1.1.1.0/24').best_route.negative_next_hops == \
#            {mknh("if1", "10.0.0.2")}
#     assert rt.destinations.get('1.1.1.0/24').best_route.next_hops == \
#            {mknh("if2", "10.0.0.3"), mknh("if3", "10.0.0.4"), mknh("if4", "10.0.0.5"),
#             mknh("if5", "10.0.0.6"), mknh("if6", "10.0.0.7")}
#     assert set(rt.fib.routes[mkp('1.1.1.0/24')].next_hops) == \
#            {mknh("if2", "10.0.0.3"), mknh("if3", "10.0.0.4"), mknh("if4", "10.0.0.5"),
#             mknh("if5", "10.0.0.6"), mknh("if6", "10.0.0.7")}

#     assert rt.destinations.get('1.1.2.0/24').best_route.negative_next_hops == \
#            {mknh("if2", "10.0.0.3")}
#     assert rt.destinations.get('1.1.2.0/24').best_route.next_hops == \
#            {mknh("if1", "10.0.0.2"), mknh("if3", "10.0.0.4"), mknh("if4", "10.0.0.5"),
#             mknh("if5", "10.0.0.6"), mknh("if6", "10.0.0.7")}
#     assert set(rt.fib.routes[mkp('1.1.2.0/24')].next_hops) == \
#            {mknh("if1", "10.0.0.2"), mknh("if3", "10.0.0.4"), mknh("if4", "10.0.0.5"),
#             mknh("if5", "10.0.0.6"), mknh("if6", "10.0.0.7")}

#     assert rt.destinations.get('1.2.0.0/16').best_route.negative_next_hops == \
#            {mknh("if3", "10.0.0.4")}
#     assert rt.destinations.get('1.2.0.0/16').best_route.next_hops == \
#            {mknh("if0", "10.0.0.1"), mknh("if1", "10.0.0.2"), mknh("if2", "10.0.0.3"),
#             mknh("if4", "10.0.0.5"), mknh("if5", "10.0.0.6"), mknh("if6", "10.0.0.7")}
#     assert set(rt.fib.routes[mkp('1.2.0.0/16')].next_hops) == \
#            {mknh("if0", "10.0.0.1"), mknh("if1", "10.0.0.2"), mknh("if2", "10.0.0.3"),
#             mknh("if4", "10.0.0.5"), mknh("if5", "10.0.0.6"), mknh("if6", "10.0.0.7")}

#     assert rt.destinations.get('1.2.1.0/24').best_route.negative_next_hops == \
#            {mknh("if4", "10.0.0.5")}
#     assert rt.destinations.get('1.2.1.0/24').best_route.next_hops == \
#            {mknh("if0", "10.0.0.1"), mknh("if1", "10.0.0.2"), mknh("if2", "10.0.0.3"),
#             mknh("if5", "10.0.0.6"), mknh("if6", "10.0.0.7")}
#     assert set(rt.fib.routes[mkp('1.2.1.0/24')].next_hops) == \
#            {mknh("if0", "10.0.0.1"), mknh("if1", "10.0.0.2"), mknh("if2", "10.0.0.3"),
#             mknh("if5", "10.0.0.6"), mknh("if6", "10.0.0.7")}

#     assert rt.destinations.get('1.2.2.0/24').best_route.negative_next_hops == \
#            {mknh("if5", "10.0.0.6")}
#     assert rt.destinations.get('1.2.2.0/24').best_route.next_hops == \
#            {mknh("if0", "10.0.0.1"), mknh("if1", "10.0.0.2"), mknh("if2", "10.0.0.3"),
#             mknh("if4", "10.0.0.5"), mknh("if6", "10.0.0.7")}
#     assert set(rt.fib.routes[mkp('1.2.2.0/24')].next_hops) == \
#            {mknh("if0", "10.0.0.1"), mknh("if1", "10.0.0.2"), mknh("if2", "10.0.0.3"),
#             mknh("if4", "10.0.0.5"), mknh("if6", "10.0.0.7")}

#     # Delete nexthop if2 from the parent route 0.0.0.0/0.
#     rt.put_route(mkr('1.0.0.0/8', [mknh("if0", "10.0.0.1"), mknh("if1", "10.0.0.2"),
#                                        mknh("if3", "10.0.0.4"), mknh("if4", "10.0.0.5"),
#                                        mknh("if5", "10.0.0.6"), mknh("if6", "10.0.0.7")]))

#     # Testing only rib and fib next hops
#     assert rt.destinations.get('1.0.0.0/8').best_route.next_hops == \
#            {mknh("if0", "10.0.0.1"), mknh("if1", "10.0.0.2"), mknh("if3", "10.0.0.4"),
#             mknh("if4", "10.0.0.5"), mknh("if5", "10.0.0.6"), mknh("if6", "10.0.0.7")}
#     assert set(rt.fib.routes[mkp('1.0.0.0/8')].next_hops) == \
#            {mknh("if0", "10.0.0.1"), mknh("if1", "10.0.0.2"), mknh("if3", "10.0.0.4"),
#             mknh("if4", "10.0.0.5"), mknh("if5", "10.0.0.6"), mknh("if6", "10.0.0.7")}

#     assert rt.destinations.get('1.1.0.0/16').best_route.negative_next_hops == \
#            {mknh("if0", "10.0.0.1")}
#     assert rt.destinations.get('1.1.0.0/16').best_route.next_hops == \
#            {mknh("if1", "10.0.0.2"), mknh("if3", "10.0.0.4"), mknh("if4", "10.0.0.5"),
#             mknh("if5", "10.0.0.6"), mknh("if6", "10.0.0.7")}
#     assert set(rt.fib.routes[mkp('1.1.0.0/16')].next_hops) == \
#            {mknh("if1", "10.0.0.2"), mknh("if3", "10.0.0.4"), mknh("if4", "10.0.0.5"),
#             mknh("if5", "10.0.0.6"), mknh("if6", "10.0.0.7")}

#     assert rt.destinations.get('1.1.1.0/24').best_route.negative_next_hops == \
#            {mknh("if1", "10.0.0.2")}
#     assert rt.destinations.get('1.1.1.0/24').best_route.next_hops == \
#            {mknh("if3", "10.0.0.4"), mknh("if4", "10.0.0.5"), mknh("if5", "10.0.0.6"),
#             mknh("if6", "10.0.0.7")}
#     assert set(rt.fib.routes[mkp('1.1.1.0/24')].next_hops) == \
#            {mknh("if3", "10.0.0.4"), mknh("if4", "10.0.0.5"), mknh("if5", "10.0.0.6"),
#             mknh("if6", "10.0.0.7")}

#     assert rt.destinations.get('1.1.2.0/24').best_route.negative_next_hops == \
#            {mknh("if2", "10.0.0.3")}
#     assert rt.destinations.get('1.1.2.0/24').best_route.next_hops == \
#            {mknh("if1", "10.0.0.2"), mknh("if3", "10.0.0.4"), mknh("if4", "10.0.0.5"),
#             mknh("if5", "10.0.0.6"), mknh("if6", "10.0.0.7")}
#     assert set(rt.fib.routes[mkp('1.1.2.0/24')].next_hops) == \
#            {mknh("if1", "10.0.0.2"), mknh("if3", "10.0.0.4"), mknh("if4", "10.0.0.5"),
#             mknh("if5", "10.0.0.6"), mknh("if6", "10.0.0.7")}

#     assert rt.destinations.get('1.2.0.0/16').best_route.negative_next_hops == \
#            {mknh("if3", "10.0.0.4")}
#     assert rt.destinations.get('1.2.0.0/16').best_route.next_hops == \
#            {mknh("if0", "10.0.0.1"), mknh("if1", "10.0.0.2"), mknh("if4", "10.0.0.5"),
#             mknh("if5", "10.0.0.6"), mknh("if6", "10.0.0.7")}
#     assert set(rt.fib.routes[mkp('1.2.0.0/16')].next_hops) == \
#            {mknh("if0", "10.0.0.1"), mknh("if1", "10.0.0.2"), mknh("if4", "10.0.0.5"),
#             mknh("if5", "10.0.0.6"), mknh("if6", "10.0.0.7")}

#     assert rt.destinations.get('1.2.1.0/24').best_route.negative_next_hops == \
#            {mknh("if4", "10.0.0.5")}
#     assert rt.destinations.get('1.2.1.0/24').best_route.next_hops == \
#            {mknh("if0", "10.0.0.1"), mknh("if1", "10.0.0.2"), mknh("if5", "10.0.0.6"),
#             mknh("if6", "10.0.0.7")}
#     assert set(rt.fib.routes[mkp('1.2.1.0/24')].next_hops) == \
#            {mknh("if0", "10.0.0.1"), mknh("if1", "10.0.0.2"), mknh("if5", "10.0.0.6"),
#             mknh("if6", "10.0.0.7")}

#     assert rt.destinations.get('1.2.2.0/24').best_route.negative_next_hops == \
#            {mknh("if5", "10.0.0.6")}
#     assert rt.destinations.get('1.2.2.0/24').best_route.next_hops == \
#            {mknh("if0", "10.0.0.1"), mknh("if1", "10.0.0.2"), mknh("if4", "10.0.0.5"),
#             mknh("if6", "10.0.0.7")}
#     assert set(rt.fib.routes[mkp('1.2.2.0/24')].next_hops) == \
#            {mknh("if0", "10.0.0.1"), mknh("if1", "10.0.0.2"), mknh("if4", "10.0.0.5"),
#             mknh("if6", "10.0.0.7")}

#     # Delete all routes from the RIB.
#     rt.del_route(mkp("1.0.0.0/8"), S)
#     rt.del_route(mkp("1.1.0.0/16"), S)
#     rt.del_route(mkp("1.1.1.0/24"), S)
#     rt.del_route(mkp("1.1.2.0/24"), S)
#     rt.del_route(mkp("1.2.0.0/16"), S)
#     rt.del_route(mkp("1.2.1.0/24"), S)
#     rt.del_route(mkp("1.2.2.0/24"), S)

#     # The RIB must be empty.
#     assert not rt.destinations.keys()
#     # The FIB must be empty.
#     assert not rt.fib.routes.keys()


# def test_cli_table():
#     add_missing_methods_to_thrift()
#     route_table = mkrt()
#     nh1 = mknh("if1", "1.1.1.1")
#     nh2 = mknh("if2", "2.2.2.2")
#     nh3 = mknh("if3", None)
#     nh4 = mknh("if4", "4.4.4.4")
#     route_table.put_route(mkr("2.2.2.0/24", N))
#     route_table.put_route(mkr("1.1.1.0/24", [nh1]))
#     route_table.put_route(mkr("0.0.0.0/0", [nh1, nh2]))
#     route_table.put_route(mkr("2.2.0.0/16", [nh3], [nh4]))
#     route_table.put_route(mkr("1.1.1.0/24", N))
#     route_table.put_route(mkr("4.4.4.0/24", [], [nh2, nh3]))
#     tab_str = route_table.cli_table().to_string()
#     assert (tab_str == "+------------+-----------+----------------------+\n"
#                        "| Prefix     | Owner     | Next-hops            |\n"
#                        "+------------+-----------+----------------------+\n"
#                        "| 0.0.0.0/0  | South SPF | if1 1.1.1.1          |\n"
#                        "|            |           | if2 2.2.2.2          |\n"
#                        "+------------+-----------+----------------------+\n"
#                        "| 1.1.1.0/24 | South SPF | if1 1.1.1.1          |\n"
#                        "+------------+-----------+----------------------+\n"
#                        "| 1.1.1.0/24 | North SPF |                      |\n"
#                        "+------------+-----------+----------------------+\n"
#                        "| 2.2.0.0/16 | South SPF | if3                  |\n"
#                        "|            |           | Negative if4 4.4.4.4 |\n"
#                        "+------------+-----------+----------------------+\n"
#                        "| 2.2.2.0/24 | North SPF |                      |\n"
#                        "+------------+-----------+----------------------+\n"
#                        "| 4.4.4.0/24 | South SPF | Negative if2 2.2.2.2 |\n"
#                        "|            |           | Negative if3         |\n"
#                        "+------------+-----------+----------------------+\n")