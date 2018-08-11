# System test: test_sys_2n_l0_l2
#
# Topology: 2n_l0_l2
#
#  +-----------+
#  | node1     |
#  | (level 2) |
#  +-----------+
#        | if1
#        |
#        | if1
#  +-----------+
#  | node2     |
#  | (level 0) |
#  +-----------+
#
# - 2 nodes: node1 and node2
# - Both nodes have hard-configured levels:
#   - node1 is level 2
#   - node2 is level 0 (leaf)
# - One link:
#   - node1:if1 - node2:if1
# - The difference in hard-configured levels is more than 1
# - It is an adjacency between a leaf and a non-leaf
# - The adjacency should come up to state 3-way anyway
#
# Test scenario:
# - Bring the topology up
#   - Both nodes report adjacency to other node up as in state 3-way
#   - Check explictly for acceptance of the LIE message because of leaf-to-non-leaf link
#   - Check offers and levels on each node
# - Fail interface if1 on node1 (bi-directional failure)
#   - Both nodes report adjacency to other node as down in state 1-way
#   - Check offers and levels on each node

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
        not_a_ztp_offer=False,
        state="THREE_WAY",
        best=False,
        best_3way=False,
        removed=True,
        removed_reason="Level is leaf")
    res.check_tx_offer(
        node="node1",
        interface="if1",
        system_id="1",
        level=2,
        not_a_ztp_offer=False,
        state="THREE_WAY")
    res.check_level(
        node="node1",
        configured_level=2,
        hal=None,
        hat=None,
        level_value=2)
    res.check_lie_accepted(
        node="node1",
        interface="if1",
        reason="This node is not leaf and neighbor is leaf")

def check_rift_node1_intf_down(res):
    res.check_adjacency_1way(
        node="node1",
        interface="if1")
    # TODO: Check offers and level

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
        level=2,
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
        not_a_ztp_offer=False,
        state="THREE_WAY")
    res.check_level(
        node="node2",
        configured_level=0,
        hal=2,
        hat=2,
        level_value=0)
    res.check_lie_accepted(
        node="node2",
        interface="if1",
        reason="This node is leaf and HAT not greater than remote level")

def check_rift_node2_intf_down(res):
    res.check_adjacency_1way(
        node="node2",
        interface="if1")
    # TODO: Check offers and level

def check_log_node1_intf_up(les):
    les.check_lie_fsm_3way("node1", "if1")
    #!!!les.check_lie_fsm_3way("node2", "if1")

# TODO: Check log when interface is down

def test_2_nodes_l0_l2():
    # Bring topology up
    res = RiftExpectSession("2n_l0_l2")
    les = LogExpectSession("rift.log")
    # Check that adjacency reaches 3-way, check offers, check levels
    check_rift_node1_intf_up(res)
    check_rift_node2_intf_up(res)
    check_log_node1_intf_up(les)
    # Bring interface if1 on node1 down
    res.interface_failure("node1", "if1", "failed")
    # Check that adjacency goes back to 1-way, check offers, check levels
    check_rift_node1_intf_down(res)
    check_rift_node2_intf_down(res)
    # Done
    res.stop()
