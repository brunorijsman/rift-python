# System test: test_sys_3n_l0_l1_l2s
#
# See topology 3n_l0_l1_l2.yaml
#
# TODO: Add description

# Allow long test names
# pylint: disable=invalid-name

import os
from rift_expect_session import RiftExpectSession
from log_expect_session import LogExpectSession

def check_rift_node1_intf_up(res):
    res.check_adjacency_3way(
        node="node1",
        interface="if1")
    res.check_rx_offer(
        node="node1",
        interface="if1",
        system_id="2",
        level=1,
        not_a_ztp_offer="(False/True)", # TODO: Juniper lenient
        state="THREE_WAY",
        best="(True/False)", # TODO: Juniper lenient
        best_3way="(True/False)", # TODO: Juniper lenient
        removed="(False/True)", # TODO: Juniper lenient
        removed_reason="(Level is leaf/Not a ZTP offer flag set/)")  # TODO: Juniper lenient
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
        hal="(1/None)", # TODO: Juniper lenient
        hat="(1/None)", # TODO: Juniper lenient
        level_value=2)

def check_rift_node1_intf_down(res):
    res.check_adjacency_1way(
        node="node1",
        interface="if1")
    # TODO: Check offers and level

def check_rift_node2_intf_up(res):
    res.check_adjacency_3way(
        node="node2",
        interface="if1")
    # TODO: Check adjacency with node3
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
    # TODO: Check RX offer from node3
    res.check_tx_offer(
        node="node2",
        interface="if1",
        system_id="2",
        level=1,
        not_a_ztp_offer=False,
        state="THREE_WAY")
    # TODO: Check TX offer to node3
    res.check_level(
        node="node2",
        configured_level=1,
        hal=2,
        hat=2,
        level_value=1)

def check_rift_node2_intf_down(res):
    res.check_adjacency_1way(
        node="node2",
        interface="if1")
    # TODO: Check offers and level

def check_rift_node3_intf_up(_res):
    # TODO: implement this
    pass

def check_rift_node3_intf_down(_res):
    # TODO: implement this
    pass

def check_log_node1_intf_up(les):
    les.check_lie_fsm_3way("node1", "if1")

def check_log_node1_intf_down(_les):
    # TODO: implement this
    pass

def check_log_node2_intf_up(les):
    les.check_lie_fsm_3way("node2", "if1")
    les.check_lie_fsm_3way("node2", "if2")

def check_log_node2_intf_down(_les):
    # TODO: implement this
    pass

def check_log_node3_intf_up(les):
    les.check_lie_fsm_3way("node3", "if1")

def check_log_node3_intf_down(_les):
    # TODO: implement this
    pass

def test_3n_l0_l1_l2():
    passive_nodes = os.getenv("RIFT_PASSIVE_NODES", "").split(",")
    # Bring topology up
    les = LogExpectSession()
    res = RiftExpectSession("3n_l0_l1_l2")
    # Check that node1-node2 and node2-node3 adjacencies reaches 3-way
    if "node1" not in passive_nodes:
        check_rift_node1_intf_up(res)
        check_log_node1_intf_up(les)
    if "node2" not in passive_nodes:
        check_rift_node2_intf_up(res)
        check_log_node2_intf_up(les)
    if "node3" not in passive_nodes:
        check_rift_node3_intf_up(res)
        check_log_node3_intf_up(les)
    if "node1" not in passive_nodes:
        # Bring interface if1 on node1 down
        res.interface_failure("node1", "if1", "failed")
        check_rift_node1_intf_down(res)
        check_log_node1_intf_down(res)
        if "node2" not in passive_nodes:
            check_rift_node2_intf_down(res)
            check_log_node2_intf_down(res)
        if "node3" not in passive_nodes:
            check_rift_node3_intf_down(res)
            check_log_node3_intf_down(res)
    # TODO: add test cases for bringing interface node2-node3 down
    # Done
    res.stop()
