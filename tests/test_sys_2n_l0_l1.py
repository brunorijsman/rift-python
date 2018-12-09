# System test: test_sys_2n_l0_l1

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
        level=0,
        not_a_ztp_offer="(False///True)", # Juniper lenient
        state="THREE_WAY",
        best=False,
        best_3way=False,
        removed=True,
        removed_reason="(Level is leaf///Not a ZTP offer flag set)")  # Juniper lenient
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
    expect_south_spf = [
        r"| 1 \(node1\) | 0 |   |  |  |",
        r"| 2 \(node2\) | 1 | 1 |  | if1",
        r"| 1.1.1.0/24  | 1 | 1 |  |  |",
        r"| 1.1.2.2.32  | 2 | 1 |  |  |",
        r"| 2.2.1.0/24  | 2 | 2 |  | if1",
        r"| 2.2.2.2/32  | 3 | 2 |  | if1",
    ]
    expect_north_spf = [
        r"| 1 \(node1\) | 0 |   |  |",
        r"| 1.1.1.0.24  | 1 | 1 |  |",
        r"| 1.1.2.2.32  | 2 | 1 |  |",
    ]
    res.check_spf("node1", expect_south_spf, expect_north_spf)
    res.check_rib_absent("node1", "0.0.0.0/0", "north-spf")
    res.check_rib_absent("node1", "::/0", "north-spf")

def check_rift_node1_intf_down(res):
    res.check_adjacency_1way(
        node="node1",
        interface="if1")
    res.check_rx_offer(
        node="node1",
        interface="if1",
        system_id="2",
        level=0,
        not_a_ztp_offer="(False///True)", # Juniper lenient
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
    expect_south_spf = [
        r"| 1 \(node1\) | 0 |   |  |  |",
        r"| 1.1.1.0/24  | 1 | 1 |  |  |",
        r"| 1.1.2.2.32  | 2 | 1 |  |  |",
    ]
    expect_north_spf = [
        r"| 1 \(node1\) | 0 |   |  |",
        r"| 1.1.1.0.24  | 1 | 1 |  |",
        r"| 1.1.2.2.32  | 2 | 1 |  |",
    ]
    res.check_spf("node1", expect_south_spf, expect_north_spf)
    res.check_spf_absent("node1", "south", "2")
    res.check_spf_absent("node1", "south", "2.2.1.0/24")
    res.check_spf_absent("node1", "south", "2.2.2.2/32")
    expect_rib = [
        r"| 1.1.1.0/24 | South SPF | |",
        r"| 1.1.1.0/24 | North SPF | |",
        r"| 1.1.2.2/32 | South SPF | |",
        r"| 1.1.2.2/32 | North SPF | |",
    ]
    res.check_rib("node1", expect_rib)
    res.check_rib_absent("node1", "0.0.0.0/0", "north-spf")
    res.check_rib_absent("node1", "2.2.1.0/24", "south-spf")
    res.check_rib_absent("node1", "2.2.2.2/32", "south-spf")
    res.check_rib_absent("node1", "::/0", "north-spf")

def check_rift_node2_intf_up(res):
    res.check_adjacency_3way(
        node="node2",
        interface="if1")
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
        not_a_ztp_offer=False,
        state="THREE_WAY")
    res.check_level(
        node="node2",
        configured_level=0,
        hal=1,
        hat=1,
        level_value=0)
    expect_south_spf = [
        r"| 2 \(node2\) | 0 |   |  |  |",
        r"| 2.2.1.0/24  | 1 | 2 |  |  |",
        r"| 2.2.2.2/32  | 2 | 2 |  |  |",
    ]
    expect_north_spf = [
        r"| 1 \(node1\) | 1 | 2 |  | if1",
        r"| 2 \(node2\) | 0 |   |  |  |",
        r"| 0.0.0.0/0   | 2 | 1 |  | if1",
        r"| 2.2.1.0/24  | 1 | 2 |  |  |",
        r"| 2.2.2.2/32  | 2 | 2 |  |  |",
        r"| ::/0        | 2 | 1 |  | if1",
    ]
    res.check_spf("node2", expect_south_spf, expect_north_spf)
    expect_rib = [
        r"| 0.0.0.0/0  | North SPF | if1",
        r"| 2.2.1.0/24 | South SPF |  |",
        r"| 2.2.1.0/24 | North SPF |  |",
        r"| 2.2.2.2/32 | South SPF |  |",
        r"| 2.2.2.2/32 | North SPF |  |",
        r"| ::/0 | North SPF | if1",
    ]
    res.check_rib("node2", expect_rib)
    res.check_rib_absent("node2", "1.1.1.0/24", "north-spf")
    res.check_rib_absent("node2", "1.1.2.2/32", "north-spf")

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
        level=0,
        not_a_ztp_offer=False,
        state="ONE_WAY")
    res.check_level(
        node="node2",
        configured_level=0,
        hal=None,
        hat=None,
        level_value=0)
    expect_south_spf = [
        r"| 2 \(node2\) | 0 |   |  |  |",
        r"| 2.2.1.0/24  | 1 | 2 |  |  |",
        r"| 2.2.2.2/32  | 2 | 2 |  |  |",
    ]
    expect_north_spf = [
        r"| 2 \(node2\) | 0 |   |  |  |",
        r"| 2.2.1.0/24  | 1 | 2 |  |  |",
        r"| 2.2.2.2/32  | 2 | 2 |  |  |",
    ]
    res.check_spf("node2", expect_south_spf, expect_north_spf)
    res.check_spf_absent("node2", "north", "1")
    res.check_spf_absent("node2", "north", "0.0.0.0/0")
    res.check_spf_absent("node2", "north", "::/0")
    expect_rib = [
        r"| 2.2.1.0/24 | South SPF |  |",
        r"| 2.2.1.0/24 | North SPF |  |",
        r"| 2.2.2.2/32 | South SPF |  |",
        r"| 2.2.2.2/32 | North SPF |  |",
    ]
    res.check_rib("node2", expect_rib)
    res.check_rib_absent("node2", "0.0.0.0/0", "north-spf")
    res.check_rib_absent("node2", "1.1.1.0/24", "north-spf")
    res.check_rib_absent("node2", "1.1.2.2/32", "north-spf")
    res.check_rib_absent("node2", "::/0", "north-spf")

def check_log_node1_intf_up(les):
    les.check_lie_fsm_3way("node1", "if1")

def check_log_node2_intf_up(les):
    les.check_lie_fsm_3way("node2", "if1")

def check_log_node1_intf_down(les):
    les.check_lie_fsm_timeout_to_1way("node1", "if1", "set interface if1 failure failed")

def check_log_node2_intf_down(les):
    les.check_lie_fsm_timeout_to_1way("node2", "if1", "set interface if1 failure failed")

def test_2n_l0_l1():
    passive_nodes = os.getenv("RIFT_PASSIVE_NODES", "").split(",")
    # Bring topology up
    les = LogExpectSession()
    res = RiftExpectSession("2n_l0_l1")
    # Check that adjacency reaches 3-way, check offers, check levels
    if "node1" not in passive_nodes:
        check_rift_node1_intf_up(res)
        check_log_node1_intf_up(les)
    if "node2" not in passive_nodes:
        check_rift_node2_intf_up(res)
        check_log_node2_intf_up(les)
    if "node1" not in passive_nodes:
        # Bring interface if1 on node1 down
        res.interface_failure("node1", "if1", "failed")
        # Check that adjacency goes back to 1-way, check offers, check levels
        check_rift_node1_intf_down(res)
        check_log_node1_intf_down(les)
        if "node2" not in passive_nodes:
            check_rift_node2_intf_down(res)
            check_log_node2_intf_down(les)
    # Done
    res.stop()
