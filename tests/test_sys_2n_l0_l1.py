# System test: test_sys_2n_l0_l1
#
# Test an extremely simple topology with two nodes. One is hard-configured to level 0. The other is
# hard-configured to level 1. ZTP is not active. We test the following:
# * The adjacency reached state 3-way on both nodes
# * TODO: each node reports the correct level for itself and for the neighbor
# * TODO: each node reports the correct sent and received offers
# * TODO: the right sequence of events and transitions takes place in the LIE FSM in each node

# Allow long test names
# pylint: disable=invalid-name

from rift_expect_session import RiftExpectSession

def check_adjacency(res):
    res.check_adjacency_3way_both_nodes(
        node1="node1",
        interface1="if1",
        node2="node2",
        interface2="if1")

def check_offers(res):
    # Offers on node 1
    res.check_rx_offer(
        node="node1",
        interface="if1",
        system_id="2",
        level=0,
        not_a_ztp_offer=True,
        state="THREE_WAY",
        best=False,
        best_3way=False,
        removed=True,
        removed_reason="Not a ZTP offer flag set")
    res.check_tx_offer(
        node="node1",
        interface="if1",
        system_id="1",
        level=1,
        not_a_ztp_offer=False,
        state="THREE_WAY")
    # Offers on node 2
    res.check_rx_offer(
        node="node2",
        interface="if1",
        system_id="1",
        level=1,
        not_a_ztp_offer=False,
        state="THREE_WAY",
        best=True,
        best_3way=True,
        removed=False,
        removed_reason="")
    res.check_tx_offer(
        node="node2",
        interface="if1",
        system_id="2",
        level=0,
        not_a_ztp_offer=True,
        state="THREE_WAY")

def check_levels(res):
    res.check_level(node="node1", configured_level=1, level_value=1)
    res.check_level(node="node2", configured_level=0, level_value=0)

def test_2_nodes_level_0_and_level_1():
    res = RiftExpectSession("2n_l0_l1")
    check_adjacency(res)
    check_offers(res)
    check_levels(res)
    res.stop()
