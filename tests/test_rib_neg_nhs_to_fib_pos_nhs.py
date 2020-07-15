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
    rt = mkrt()
    # Just a default route with positive next-hops; there are no more specific routes
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
    rt = mkrt()
    # Start with a parent default route with some positive next-hops
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
    rt = mkrt()
    # Start a parent default route with some positive next-hops
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
    # Delete a next-hop from a parent route, and check that the computed complementary next-hops in
    # the child routes are properly updated.
    rt = mkrt()
    # Create a parent default route with positive next-hops
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
    rt = mkrt()
    # Start with a parent default route with some positive next-hops
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
    rt = mkrt()
    # Start with a parent default route with some positive next-hops
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
    rt = mkrt()
    # Start with a parent default route with some positive next-hops
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
    rt = mkrt()
    # Start with a parent default route with some positive next-hops
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
    # Check that the child route is present in the RIB and also absent from the FIB (it is
    # superfluous because it is a discard route without a parent route)
    check_rib_route(rt, child_prefix, child_rib_next_hops)
    check_fib_route_absent(rt, child_prefix)
    # Check that the grand-child route is present in the RIB and absent from the FIB because it
    # is a superfluous route (grand-child is discard, but it parent -the child- is also discard)
    check_rib_route(rt, grand_child_prefix, grand_child_rib_next_hops)
    check_fib_route_absent(rt, grand_child_prefix)

def test_discard_child_from_fib_when_no_next_hops_left():
    # Tests if a route becomes unreachable (i.e. becomes a discard route) after all next hops are
    # negatively disaggregated
    rt = mkrt()
    # Start with a parent default route with some positive next-hops
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
    rt = mkrt()
    # Start with a parent default route with some positive next-hops
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
    rt = mkrt()
    # Start with a parent default route with some positive next-hops
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
    rt = mkrt()
    # Start with a parent default route with some positive next-hops
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
    rt = mkrt()
    # Start with a parent default route with some positive next-hops
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
    rt = mkrt()
    # Add a north-SPF parent default route with some positive next-hops
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
    rt = mkrt()
    # Add a north-SPF parent default route with some positive next-hops
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
    rt = mkrt()
    # Start with a parent default route with some positive next-hops
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
    # Remove the default route
    rt.del_route(mkp(default_prefix), OWNER_S_SPF)
    check_rib_route_absent(rt, default_prefix)
    check_fib_route_absent(rt, default_prefix)
    # Now the child route is no longer superfluous
    check_rib_route(rt, child_prefix, child_rib_next_hops)
    child_fib_next_hops = child_rib_next_hops
    check_fib_route(rt, child_prefix, child_fib_next_hops)

def test_superfluous_negative_next_hop():
    # Test that installation of a superfluous route in the FIB is prevented when the child's FIB
    # next-hops are the same as the parent's next-hops because.
    # Specific scenario: the child has negative next-hops that don't actually remove any next-hops
    # from the set of positive next-hops of the parent.
    rt = mkrt()
    # Start with a parent default route with some positive next-hops
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
    # Check that the negative child route is not installed in the FIB because it is superfluous:
    # it has the exact same FIB next-hops as its parent, the default route
    check_fib_route_absent(rt, child_prefix)
    # Add a new next-hop to the default route that does match one of the negative next-hops of the
    # child route
    new_default_next_hops = [mknh_pos("if0", "10.0.0.1"),
                             mknh_pos("if1", "10.0.0.2"),
                             mknh_pos("if2", "10.0.0.3"),
                             mknh_pos("if3", "10.0.0.4"),
                             mknh_pos("if4", "10.0.0.5")]
    new_default_route = mkr(default_prefix, new_default_next_hops)
    rt.put_route(new_default_route)
    check_rib_route(rt, default_prefix, new_default_next_hops)
    check_fib_route(rt, default_prefix, new_default_next_hops)
    # The child route is not superfluous anymore, since it's FIB next-hops are now different from
    # the FIB next-hops of its parent
    child_fib_next_hops = [mknh_pos("if0", "10.0.0.1"),
                           mknh_pos("if1", "10.0.0.2"),
                           mknh_pos("if2", "10.0.0.3"),
                           mknh_pos("if3", "10.0.0.4")]
    check_fib_route(rt, child_prefix, child_fib_next_hops)

def test_superfluous_discard_parent_also_discard():
    # Test that installation of a superfluous route in the FIB is prevented when the child's FIB
    # next-hops are the same as the parent's next-hops because.
    # Specific scenario: a child ends up with a discard route, but its parent also is a discard
    # route
    rt = mkrt()
    # Start with a parent default route with some positive next-hops
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
    check_fib_route(rt, grand_child_prefix, no_next_hops)

def test_superfluous_discard_no_parent():
    # Test that installation of a superfluous route in the FIB is prevented when the child's FIB
    # next-hops are the same as the parent's next-hops because.
    # Specific scenario: the child ends up with a discard route, but there is no parent
    rt = mkrt()
    # Create a so-called child route that only has some negative next-hops, but not parent route
    child_prefix = "10.0.0.0/16"
    child_rib_next_hops = [mknh_neg("if0", "10.0.0.1"),
                           mknh_neg("if1", "10.0.0.2")]
    child_route = mkr(child_prefix, child_rib_next_hops)
    rt.put_route(child_route)
    check_rib_route(rt, child_prefix, child_rib_next_hops)
    # Check that the child child route is absent from the FIB because it is superfluous (it is a
    # discard route without a parent route)
    check_fib_route_absent(rt, child_prefix)
    # Add a default route with some positive next-hops
    default_prefix = "0.0.0.0/0"
    default_next_hops = [mknh_pos("if0", "10.0.0.1"),
                         mknh_pos("if1", "10.0.0.2"),
                         mknh_pos("if2", "10.0.0.3"),
                         mknh_pos("if3", "10.0.0.4")]
    default_route = mkr(default_prefix, default_next_hops)
    rt.put_route(default_route)
    check_rib_route(rt, default_prefix, default_next_hops)
    check_fib_route(rt, default_prefix, default_next_hops)
    # The child route (which is now really a child route) is no longer superfluous
    child_fib_next_hops = [mknh_pos("if2", "10.0.0.3"),
                           mknh_pos("if3", "10.0.0.4")]
    check_fib_route(rt, child_prefix, child_fib_next_hops)

def test_prop_deep_nesting():
    # Deep nesting of more specific routes: parent, child, grand child, grand-grand child, ...
    #
    #   default         0.0.0.0/0 -> if0, if1, if2, if3, if4   [if0, if1, if2, if3, if4]
    #                    |
    #   child            +--- 1.0.0.0/8 -> ~if1   [if0, if2, if3, if4]
    #                          |
    #   g_child                +--- 1.128.0.0/9 -> ~if0, if5   [if2, if3, if4, if5]
    #                                |
    #   gg_child                     +--- 1.192.0.0/10 -> if1, ~if3   [if1, if2, if4, if5]
    #                                      |
    #   ggg_child                          +--- 1.224.0.0/11 -> ~if1, ~if5   [if2, if4]
    #                                            |
    #   gggg_child                               +--- 1.240.0.0/12 -> if2, if4   [superfluous]
    #
    rt = mkrt()
    # Add default
    default_prefix = "0.0.0.0/0"
    default_rib_next_hops = [mknh_pos("if0", "10.0.0.1"),
                             mknh_pos("if1", "10.0.0.2"),
                             mknh_pos("if2", "10.0.0.3"),
                             mknh_pos("if3", "10.0.0.4"),
                             mknh_pos("if4", "10.0.0.5")]
    default_route = mkr(default_prefix, default_rib_next_hops)
    rt.put_route(default_route)
    check_rib_route(rt, default_prefix, default_rib_next_hops)
    default_fib_next_hops = default_rib_next_hops
    check_fib_route(rt, default_prefix, default_fib_next_hops)
    # Add child
    child_prefix = "1.0.0.0/8"
    child_rib_next_hops = [mknh_neg("if1", "10.0.0.2")]
    child_route = mkr(child_prefix, child_rib_next_hops)
    rt.put_route(child_route)
    check_rib_route(rt, child_prefix, child_rib_next_hops)
    child_fib_next_hops = [mknh_pos("if0", "10.0.0.1"),
                           mknh_pos("if2", "10.0.0.3"),
                           mknh_pos("if3", "10.0.0.4"),
                           mknh_pos("if4", "10.0.0.5")]
    check_fib_route(rt, child_prefix, child_fib_next_hops)
    # Add grand child
    g_child_prefix = "1.128.0.0/9"
    g_child_rib_next_hops = [mknh_neg("if0", "10.0.0.1"),
                             mknh_pos("if5", "10.0.0.6")]
    g_child_route = mkr(g_child_prefix, g_child_rib_next_hops)
    rt.put_route(g_child_route)
    check_rib_route(rt, g_child_prefix, g_child_rib_next_hops)
    g_child_fib_next_hops = [mknh_pos("if2", "10.0.0.3"),
                             mknh_pos("if3", "10.0.0.4"),
                             mknh_pos("if4", "10.0.0.5"),
                             mknh_pos("if5", "10.0.0.6")]
    check_fib_route(rt, g_child_prefix, g_child_fib_next_hops)
    # Add grand-grand child
    gg_child_prefix = "1.192.0.0/10"
    gg_child_rib_next_hops = [mknh_pos("if1", "10.0.0.2"),
                              mknh_neg("if3", "10.0.0.4")]
    gg_child_route = mkr(gg_child_prefix, gg_child_rib_next_hops)
    rt.put_route(gg_child_route)
    check_rib_route(rt, gg_child_prefix, gg_child_rib_next_hops)
    gg_child_fib_next_hops = [mknh_pos("if1", "10.0.0.2"),
                              mknh_pos("if2", "10.0.0.3"),
                              mknh_pos("if4", "10.0.0.5"),
                              mknh_pos("if5", "10.0.0.6")]
    check_fib_route(rt, gg_child_prefix, gg_child_fib_next_hops)
    # Add grand-grand-grand child
    ggg_child_prefix = "1.224.0.0/11"
    ggg_child_rib_next_hops = [mknh_neg("if1", "10.0.0.2"),
                               mknh_neg("if5", "10.0.0.6")]
    ggg_child_route = mkr(ggg_child_prefix, ggg_child_rib_next_hops)
    rt.put_route(ggg_child_route)
    check_rib_route(rt, ggg_child_prefix, ggg_child_rib_next_hops)
    ggg_child_fib_next_hops = [mknh_pos("if2", "10.0.0.3"),
                               mknh_pos("if4", "10.0.0.5")]
    check_fib_route(rt, ggg_child_prefix, ggg_child_fib_next_hops)
    # Add grand-grand-grand-grand child
    gggg_child_prefix = "1.240.0.0/12"
    gggg_child_rib_next_hops = [mknh_pos("if2", "10.0.0.3"),
                                mknh_pos("if4", "10.0.0.5")]
    gggg_child_route = mkr(gggg_child_prefix, gggg_child_rib_next_hops)
    rt.put_route(gggg_child_route)
    check_rib_route(rt, gggg_child_prefix, gggg_child_rib_next_hops)
    check_fib_route_absent(rt, gggg_child_prefix)  # Superfluous
    #
    # Delete the top default route, which results in the following updated tree:
    #
    #   child            +--- 1.0.0.0/8 -> ~if1   [superfluous]
    #                          |
    #   g_child                +--- 1.128.0.0/9 -> ~if0, if5   [if5]
    #                                |
    #   gg_child                     +--- 1.192.0.0/10 -> if1, ~if3   [if1, if5]
    #                                      |
    #   ggg_child                          +--- 1.224.0.0/11 -> ~if1, ~if5   [discard]
    #                                            |
    #   gggg_child                               +--- 1.240.0.0/12 -> if2, if4   [if2, if4]
    #
    rt.del_route(mkp(default_prefix), OWNER_S_SPF)
    # Child (superfluous)
    check_fib_route_absent(rt, child_prefix)
    # Grand child
    g_child_fib_next_hops = [mknh_pos("if5", "10.0.0.6")]
    check_fib_route(rt, g_child_prefix, g_child_fib_next_hops)
    # Grand-grand child
    gg_child_fib_next_hops = [mknh_pos("if1", "10.0.0.2"),
                              mknh_pos("if5", "10.0.0.6")]
    check_fib_route(rt, gg_child_prefix, gg_child_fib_next_hops)
    # Grand-grand-grand child
    ggg_child_fib_next_hops = []  # Discard
    check_fib_route(rt, ggg_child_prefix, ggg_child_fib_next_hops)
    # Grand-grand-grand-grand child
    gggg_child_fib_next_hops = [mknh_pos("if2", "10.0.0.3"),
                                mknh_pos("if4", "10.0.0.5")]
    check_fib_route(rt, gggg_child_prefix, gggg_child_fib_next_hops)

def test_prop_nesting_with_siblings():
    # Deep nesting of more specific routes using the following tree:
    #
    #   top         1.0.0.0/8 -> if0, if1, if2, if3, if4, if5   [if0, if1, if2, if3, if4, if5]
    #                |
    #   left         +--- 1.1.0.0/16 -> ~if0   [if1, if2, if3, if4, if5]
    #                |     |
    #   left-left    |     +--- 1.1.1.0/24 -> ~if1    [if2, if3, if4, if5]
    #                |     |
    #   left-right   |     +--- 1.1.2.0/24 -> ~if2    [if1, if3, if4, if5]
    #                |
    #   right        +--- 1.2.0.0/16 -> ~if3   [if0, if1, if2, if4, if5]
    #                      |
    #   right-left         +--- 1.2.1.0/24 -> ~if4   [if0, if1, if2, if5]
    #                      |
    #   right-right        +--- 1.2.2.0/24 -> ~if5   [if0, if1, if2, if4]
    #
    # The routes are created in a random order:
    #  1. left-left
    #  2. right
    #  3. top
    #  4. right-right
    #  5. left-right
    #  6. left
    #  7. right-left
    rt = mkrt()
    # 1. Add left-left
    left_left_prefix = "1.1.1.0/24"
    left_left_rib_next_hops = [mknh_neg("if1", "10.0.0.2")]
    left_left_route = mkr(left_left_prefix, left_left_rib_next_hops)
    rt.put_route(left_left_route)
    check_rib_route(rt, left_left_prefix, left_left_rib_next_hops)
    # 2. Add right
    right_prefix = "1.2.0.0/16"
    right_rib_next_hops = [mknh_neg("if3", "10.0.0.4")]
    right_route = mkr(right_prefix, right_rib_next_hops)
    rt.put_route(right_route)
    check_rib_route(rt, right_prefix, right_rib_next_hops)
    # 3. Add top
    top_prefix = "1.0.0.0/8"
    top_rib_next_hops = [mknh_pos("if0", "10.0.0.1"),
                         mknh_pos("if1", "10.0.0.2"),
                         mknh_pos("if2", "10.0.0.3"),
                         mknh_pos("if3", "10.0.0.4"),
                         mknh_pos("if4", "10.0.0.5"),
                         mknh_pos("if5", "10.0.0.6")]
    top_route = mkr(top_prefix, top_rib_next_hops)
    rt.put_route(top_route)
    check_rib_route(rt, top_prefix, top_rib_next_hops)
    # 4. Add right-right
    right_right_prefix = "1.2.2.0/24"
    right_right_rib_next_hops = [mknh_neg("if5", "10.0.0.6")]
    right_right_route = mkr(right_right_prefix, right_right_rib_next_hops)
    rt.put_route(right_right_route)
    check_rib_route(rt, right_right_prefix, right_right_rib_next_hops)
    # 5. Add left-right
    left_right_prefix = "1.1.2.0/24"
    left_right_rib_next_hops = [mknh_neg("if2", "10.0.0.3")]
    left_right_route = mkr(left_right_prefix, left_right_rib_next_hops)
    rt.put_route(left_right_route)
    check_rib_route(rt, left_right_prefix, left_right_rib_next_hops)
    # 6. Add left
    left_prefix = "1.1.0.0/16"
    left_rib_next_hops = [mknh_neg("if0", "10.0.0.1")]
    left_route = mkr(left_prefix, left_rib_next_hops)
    rt.put_route(left_route)
    check_rib_route(rt, left_prefix, left_rib_next_hops)
    # 6. Add right-left
    right_left_prefix = "1.2.1.0/24"
    right_left_rib_next_hops = [mknh_neg("if4", "10.0.0.5")]
    right_left_route = mkr(right_left_prefix, right_left_rib_next_hops)
    rt.put_route(right_left_route)
    check_rib_route(rt, right_left_prefix, right_left_rib_next_hops)
    # Check
    if0 = mknh_pos("if0", "10.0.0.1")
    if1 = mknh_pos("if1", "10.0.0.2")
    if2 = mknh_pos("if2", "10.0.0.3")
    if3 = mknh_pos("if3", "10.0.0.4")
    if4 = mknh_pos("if4", "10.0.0.5")
    if5 = mknh_pos("if5", "10.0.0.6")
    check_fib_route(rt, top_prefix, [if0, if1, if2, if3, if4, if5])
    check_fib_route(rt, left_prefix, [if1, if2, if3, if4, if5])
    check_fib_route(rt, left_left_prefix, [if2, if3, if4, if5])
    check_fib_route(rt, left_right_prefix, [if1, if3, if4, if5])
    check_fib_route(rt, right_prefix, [if0, if1, if2, if4, if5])
    check_fib_route(rt, right_left_prefix, [if0, if1, if2, if5])
    check_fib_route(rt, right_right_prefix, [if0, if1, if2, if4])

def test_cli_table():
    # pylint: disable=bad-continuation
    rt = mkrt()
    if0 = mknh_pos("if0", "10.0.0.1")
    if1 = mknh_pos("if1", "10.0.0.2")
    if2 = mknh_pos("if2", "10.0.0.3")
    if3 = mknh_pos("if3", "10.0.0.4")
    neg_if2 = mknh_neg("if2", "10.0.0.3")
    neg_if3 = mknh_neg("if3", "10.0.0.4")
    rt.put_route(mkr("0.0.0.0/0", [if0, if1]))
    rt.put_route(mkr("1.0.0.0/8", [if2, if3]))
    rt.put_route(mkr("1.1.0.0/16", [neg_if2]))
    rt.put_route(mkr("1.2.0.0/16", [neg_if2, neg_if3]))
    rt.put_route(mkr("1.1.1.0/24", [neg_if2]))
    tab_str = rt.cli_table().to_string()
    assert (tab_str ==
        "+------------+-----------+----------+-----------+----------+----------+\n"
        "| Prefix     | Owner     | Next-hop | Next-hop  | Next-hop | Next-hop |\n"
        "|            |           | Type     | Interface | Address  | Weight   |\n"
        "+------------+-----------+----------+-----------+----------+----------+\n"
        "| 0.0.0.0/0  | South SPF | Positive | if0       | 10.0.0.1 |          |\n"
        "|            |           | Positive | if1       | 10.0.0.2 |          |\n"
        "+------------+-----------+----------+-----------+----------+----------+\n"
        "| 1.0.0.0/8  | South SPF | Positive | if2       | 10.0.0.3 |          |\n"
        "|            |           | Positive | if3       | 10.0.0.4 |          |\n"
        "+------------+-----------+----------+-----------+----------+----------+\n"
        "| 1.1.0.0/16 | South SPF | Negative | if2       | 10.0.0.3 |          |\n"
        "+------------+-----------+----------+-----------+----------+----------+\n"
        "| 1.1.1.0/24 | South SPF | Negative | if2       | 10.0.0.3 |          |\n"
        "+------------+-----------+----------+-----------+----------+----------+\n"
        "| 1.2.0.0/16 | South SPF | Negative | if2       | 10.0.0.3 |          |\n"
        "|            |           | Negative | if3       | 10.0.0.4 |          |\n"
        "+------------+-----------+----------+-----------+----------+----------+\n")
    tab_str = rt.fib.cli_table().to_string()
    assert (tab_str ==
        "+------------+----------+-----------+----------+----------+\n"
        "| Prefix     | Next-hop | Next-hop  | Next-hop | Next-hop |\n"
        "|            | Type     | Interface | Address  | Weight   |\n"
        "+------------+----------+-----------+----------+----------+\n"
        "| 0.0.0.0/0  | Positive | if0       | 10.0.0.1 |          |\n"
        "|            | Positive | if1       | 10.0.0.2 |          |\n"
        "+------------+----------+-----------+----------+----------+\n"
        "| 1.0.0.0/8  | Positive | if2       | 10.0.0.3 |          |\n"
        "|            | Positive | if3       | 10.0.0.4 |          |\n"
        "+------------+----------+-----------+----------+----------+\n"
        "| 1.1.0.0/16 | Positive | if3       | 10.0.0.4 |          |\n"
        "+------------+----------+-----------+----------+----------+\n"
        "| 1.2.0.0/16 | Discard  |           |          |          |\n"
        "+------------+----------+-----------+----------+----------+\n")
