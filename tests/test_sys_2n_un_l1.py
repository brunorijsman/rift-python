# System test: test_sys_2n_un_l1
#
# Topology: 2n_un_l1
#
#  +-------------------+
#  | node1             |
#  | (level 1)         |
#  +-------------------+
#            | if1
#            |
#            | if1
#  +-------------------+
#  | node2             |
#  | (level undefined) |
#  +-------------------+
#
# - 2 nodes: node1 and node2
# - node1 is hard-configured as level1
# - node2 is level undefined, i.e. it uses ZTP to auto-discover its level
# - One link: node1:if1 - node2:if1
#
# Test scenario:
# - Bring the topology up
# - Both nodes report adjacency to other node up as in state 3-way
# - Node1 is hard-configured level 1
# - Node2 auto-discovers that it is level 0 (level of node1 minus one)

# Allow long test names
# pylint: disable=invalid-name

from rift_expect_session import RiftExpectSession
from log_expect_session import LogExpectSession

def check_rift_node1_intf_up(res):
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
        hal="None",
        hat="None",
        level_value=1)

def check_rift_node1_intf_down(res):
    res.check_adjacency_1way(
        node="node1",
        interface="if1")
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
        removed_reason="Hold-time expired")
    res.check_tx_offer(
        node="node1",
        interface="if1",
        system_id="1",
        level=1,
        not_a_ztp_offer=False,
        state="ONE_WAY")
    res.check_level(
        node="node1",
        configured_level=1,
        hal="None",
        hat="None",
        level_value=1)

def check_rift_node2_intf_up(res):
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
        configured_level="undefined",
        hal=1,
        hat=1,
        level_value=0)

def check_rift_node2_intf_down(res):
    res.check_adjacency_1way(
        node="node2",
        interface="if1")
    res.check_rx_offer(
        node="node2",
        interface="if1",
        system_id="1",
        level=1,
        not_a_ztp_offer=False,
        state="THREE_WAY",
        best=False,
        best_3way=False,
        removed=True,
        removed_reason="Hold-time expired")
    res.check_tx_offer(
        node="node2",
        interface="if1",
        system_id="2",
        level=None,
        not_a_ztp_offer=False,
        state="ONE_WAY")
    res.check_level(
        node="node2",
        configured_level="undefined",
        hal=None,
        hat=None,
        level_value="undefined")

def check_log_node1_intf_up(les):
    les.check_lie_fsm_3way_with_ztp("node1", "if1")

def check_log_node2_intf_up(les):
    les.check_lie_fsm_3way_with_ztp("node2", "if1")

def check_log_node1_intf_down(les):
    les.check_lie_fsm_timeout_to_1way("node1", "if1", "set interface if1 failure failed")

def check_log_node2_intf_down(les):
    les.check_lie_fsm_timeout_to_1way("node2", "if1", "set interface if1 failure failed")

def test_2n_un_l1():
    # Bring topology up
    res = RiftExpectSession("2n_un_l1")
    les = LogExpectSession("rift.log")
    # Check that adjacency reaches 3-way, check offers, check levels
    check_rift_node1_intf_up(res)
    check_rift_node2_intf_up(res)
    check_log_node1_intf_up(les)
    check_log_node2_intf_up(les)
    # Bring interface if1 on node1 down
    res.interface_failure("node1", "if1", "failed")
    # Check that adjacency goes back to 1-way, check offers, check levels
    check_rift_node1_intf_down(res)
    check_rift_node2_intf_down(res)
    check_log_node1_intf_down(les)
    check_log_node2_intf_down(les)
    # Done
    res.stop()
