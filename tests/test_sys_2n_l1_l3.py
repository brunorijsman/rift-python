# System test: test_sys_2n_l1_l3

# 2n_l1_l3 = 2 nodes: level 1 and level 3

# Allow long test names
# pylint: disable=invalid-name

import os
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
    expect_south_spf = [
        r"| 1 \(node1\) | 0 | False |  |  |  |  |",
    ]
    expect_north_spf = [
        r"| 1 \(node1\) | 0 | False |  |  |  |",
    ]
    res.check_spf("node1", expect_south_spf, expect_north_spf)
    res.check_spf_absent("node1", "south", "2")
    res.check_rib_absent("node1", "0.0.0.0/0", "north-spf")
    res.check_rib_absent("node1", "::/0", "north-spf")

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
    expect_south_spf = [
        r"| 2 \(node2\) | 0 | False |  |  |  |  |",
    ]
    expect_north_spf = [
        r"| 2 \(node2\) | 0 | False |  |  |  |  |",
    ]
    res.check_spf("node2", expect_south_spf, expect_north_spf)
    res.check_spf_absent("node2", "north", "1")
    res.check_spf_absent("node2", "north", "0.0.0.0/0")
    res.check_spf_absent("node2", "north", "::/0")
    res.check_rib_absent("node2", "0.0.0.0/0", "north-spf")
    res.check_rib_absent("node2", "::/0", "north-spf")

def check_log_node1(les):
    les.check_lie_fsm_1way_unacc_hdr("node1", "if1")

def check_log_node2(les):
    les.check_lie_fsm_1way_unacc_hdr("node2", "if1")

def test_2n_l1_l3():
    passive_nodes = os.getenv("RIFT_PASSIVE_NODES", "").split(",")
    les = LogExpectSession()
    res = RiftExpectSession("2n_l1_l3")
    if "node1" not in passive_nodes:
        check_rift_node1(res)
        check_log_node1(les)
    if "node2" not in passive_nodes:
        check_rift_node2(res)
        check_log_node2(les)
    res.stop()
