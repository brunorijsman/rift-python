# System test: test_sys_2n_l1_l3
#
# Topology: 2n_l1_l3
#
#  +-----------+
#  | node1     |
#  | (level 3) |
#  +-----------+
#        | if1
#        |
#        | if1
#  +-----------+
#  | node2     |
#  | (level 1) |
#  +-----------+
#
# - 2 nodes: node1 and node2
# - Both nodes have hard-configured levels:
#   - node1 is level 3 (non-leaf)
#   - node2 is level 1 (non-leaf)
# - One link:
#   - node1:if1 - node2:if1
# - The difference in hard-configured levels is more than 1
# - It is an adjacency between a non-leaf and a non-leaf
# - The adjacency should stay in 1-way and not come up to 3-way
# - But, despite the fact that the adjacency is not allowed to reach 3-way, the offer in the
#   received LIE is still accepted and considered as Valid Offered Level (VOL) ...
# - ... and used to determine the Highest Available Level (HAL)
# - But since the adjacency will not reach 3-way, it will not be considered for Highest Adjacency
#   in Three-way (HAT).
# - For details see http://bit.ly/rift-lie-rejected-but-offer-accepted-mail-thread
#
# Test scenario:
# - For both nodes, check all of the following:
# - The adjacency is in state 1-way
# - The received LIE message is rejected because of level mismatch
# - But the offer in the receive LIE message is still considered a VOL and used to compute HAL
# - The HAL and HAT are the correct values
# - The level value is the correct value
# - Check explictly for rejection of the LIE message because of level mismatch

# Allow long test names
# pylint: disable=invalid-name

from rift_expect_session import RiftExpectSession
from log_expect_session import LogExpectSession

def check_rift_node1(res):
    res.check_adjacency_1way(
        node="node1",
        interface="if1")
    res.check_lie_rejected(
        node="node1",
        interface="if1",
        reason="Level mismatch")
    res.check_rx_offer(
        node="node1",
        interface="if1",
        system_id="2",
        level=1,
        not_a_ztp_offer=False,
        state="ONE_WAY",
        best=True,
        best_3way=False,
        removed=False,
        removed_reason="")
    res.check_tx_offer(
        node="node1",
        interface="if1",
        system_id="1",
        level=3,
        not_a_ztp_offer=False,
        state="ONE_WAY")
    res.check_level(
        node="node1",
        configured_level=3,
        hal=1,
        hat="None",
        level_value=3)

def check_rift_node2(res):
    res.check_adjacency_1way(
        node="node2",
        interface="if1")
    res.check_lie_rejected(
        node="node2",
        interface="if1",
        reason="Level mismatch")
    res.check_rx_offer(
        node="node2",
        interface="if1",
        system_id="1",
        level=3,
        not_a_ztp_offer=False,
        state="ONE_WAY",
        best=True,
        best_3way=False,
        removed=False,
        removed_reason="")
    res.check_tx_offer(
        node="node2",
        interface="if1",
        system_id="2",
        level=1,
        not_a_ztp_offer=False,
        state="ONE_WAY")
    res.check_level(
        node="node2",
        configured_level=1,
        hal=3,
        hat="None",
        level_value=1)

def check_log_node1(les):
    les.check_lie_fsm_1way_bad_level("node1", "if1")

def check_log_node2(les):
    les.check_lie_fsm_1way_bad_level("node2", "if1")

def test_2n_l1_l3():
    res = RiftExpectSession("2n_l1_l3")
    les = LogExpectSession("rift.log")
    check_rift_node1(res)
    check_rift_node2(res)
    check_log_node1(les)
    check_log_node2(les)
    res.stop()
