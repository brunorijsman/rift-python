# System test: test_sys_2n_un_l0

# Allow long test names
# pylint: disable=invalid-name

import os
from rift_expect_session import RiftExpectSession
from log_expect_session import LogExpectSession

def check_rift_node1_intf_up(res):
    res.check_adjacency_1way(
        node="node1",
        interface="if1")
    res.check_rx_offer(
        node="node1",
        interface="if1",
        system_id="2",
        level=None,
        not_a_ztp_offer="(False///True)", # Juniper lenient
        state="ONE_WAY",
        best=False,
        best_3way=False,
        removed=True,
        removed_reason="(Level is undefined///Not a ZTP offer flag set)")  # Juniper lenient
    res.check_tx_offer(
        node="node1",
        interface="if1",
        system_id="1",
        level=0,
        not_a_ztp_offer=False,
        state="ONE_WAY")
    res.check_level(
        node="node1",
        configured_level=0,
        hal="None",
        hat="None",
        level_value=0)
    expect_south_spf = [
        r"| 1 \(node1\) | 0 |   |  |  |",
    ]
    expect_north_spf = [
        r"| 1 \(node1\) | 0 |   |  |",
    ]
    res.check_spf("node1", expect_south_spf, expect_north_spf)
    res.check_spf_absent("node1", "south", "2")
    res.check_rib_absent("node1", "0.0.0.0/0", "north-spf")
    res.check_rib_absent("node1", "::/0", "north-spf")

def check_rift_node2_intf_up(res):
    res.check_adjacency_1way(
        node="node2",
        interface="if1")
    res.check_rx_offer(
        node="node2",
        interface="if1",
        system_id="1",
        level=0,
        not_a_ztp_offer="(False///True)", # Juniper lenient
        state="ONE_WAY",
        best=False,
        best_3way=False,
        removed=True,
        removed_reason="(Level is leaf///Not a ZTP offer flag set)")  # Juniper lenient
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
    expect_south_spf = [
        r"| 2 \(node2\) | 0 |   |  |  |",
    ]
    expect_north_spf = [
        r"| 2 \(node2\) | 0 |   |  |  |",
    ]
    res.check_spf("node2", expect_south_spf, expect_north_spf)
    res.check_spf_absent("node2", "north", "1")
    res.check_spf_absent("node2", "north", "0.0.0.0/0")
    res.check_spf_absent("node2", "north", "::/0")
    res.check_rib_absent("node2", "0.0.0.0/0", "north-spf")
    res.check_rib_absent("node2", "::/0", "north-spf")

def check_log_node1_intf_up(les):
    les.check_lie_fsm_1way_unacc_hdr("node1", "if1")

def check_log_node2_intf_up(les):
    les.check_lie_fsm_1way_unacc_hdr("node2", "if1")

def test_2n_un_l0():
    passive_nodes = os.getenv("RIFT_PASSIVE_NODES", "").split(",")
    # Bring topology up
    les = LogExpectSession()
    res = RiftExpectSession("2n_un_l0")
    # Check that adjacency stays in 1-way, check offers, check levels
    if "node1" not in passive_nodes:
        check_rift_node1_intf_up(res)
        check_log_node1_intf_up(les)
    if "node2" not in passive_nodes:
        check_rift_node2_intf_up(res)
        check_log_node2_intf_up(les)
    # Done
    res.stop()
