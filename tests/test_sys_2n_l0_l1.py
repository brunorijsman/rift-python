# System test: test_sys_2n_l0_l1
#
# Test an extremely simple topology with two nodes. One is hard-configured to level 0. The other is
# hard-configured to level 1. ZTP is not active.
#
# We test the following:
# * The adjacency reached state 3-way on both nodes
# * The right sequence of events and transitions takes place in the LIE FSM in each node

# Allow long test names
# pylint: disable=invalid-name

from rift_expect_session import RiftExpectSession
from log_expect_session import LogExpectSession

def check_rift_node1(res):
    res.check_adjacency_3way(
        node="node1",
        interface="if1",
        other_node="node2",
        other_interface="if1")
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
    res.check_level(
        node="node1",
        configured_level=1,
        level_value=1)

def check_rift_node2(res):
    res.check_adjacency_3way(
        node="node2",
        interface="if1",
        other_node="node1",
        other_interface="if1")
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
    res.check_level(
        node="node2",
        configured_level=0,
        level_value=0)

def check_log_node1(les):
    les.check_lie_fsm_3way("node1", "if1")

def test_2_nodes_level_0_and_level_1():
    res = RiftExpectSession("2n_l0_l1")
    check_rift_node1(res)
    check_rift_node2(res)
    res.stop()
    les = LogExpectSession("rift.log")
    check_log_node1(les)
