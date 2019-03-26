# System test: test_sys_3n_l0_l1_l2

# 3n_l0_l1_l2 = 3 nodes: level 0, level 1, and level 2

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
        not_a_ztp_offer="(False///True)", # Juniper lenient
        state="THREE_WAY",
        best="(True///False)", # Juniper lenient
        best_3way="(True///False)", # Juniper lenient
        removed="(False///True)", # Juniper lenient
        removed_reason="(Level is leaf///Not a ZTP offer flag set///)")  # Juniper lenient
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
        hal="(1///None)", # Juniper lenient
        hat="(1///None)", # Juniper lenient
        level_value=2)
    expect_south_spf = [
        r"| 1 \(node1\)     | 0 |   |  |  |  |",
        r"| 2 \(node2\)     | 1 | 1 |  |  | if1",
        r"| 3 \(node3\)     | 2 | 2 |  |  | if1",
        r"| 1.1.1.1/32      | 1 | 1 |  |  |  |",
        r"| 2.2.2.2/32      | 2 | 2 |  |  | if1",
        r"| 3.3.3.3/32      | 3 | 3 |  |  | if1",
        r"| 1111:1111::/128 | 1 | 1 |  |  |  |",
        r"| 2222:2222::/128 | 2 | 2 |  |  | if1",
        r"| 3333:3333::/128 | 3 | 3 |  |  | if1",
    ]
    expect_north_spf = [
        r"| 1 \(node1\)     | 0 |   |  |  |",
        r"| 1.1.1.1/32      | 1 | 1 |  |  |",
        r"| 1111:1111::/128 | 1 | 1 |  |  |",
    ]
    res.check_spf("node1", expect_south_spf, expect_north_spf)
    res.check_spf_absent("node1", "south", "0.0.0.0/0")
    res.check_spf_absent("node1", "south", "::/0")
    res.check_spf_absent("node1", "north", "2")
    res.check_spf_absent("node1", "north", "3")
    res.check_spf_absent("node1", "north", "0.0.0.0/0")
    res.check_spf_absent("node1", "north", "2.2.2.2/32")
    res.check_spf_absent("node1", "north", "3.3.3.3/32")
    res.check_spf_absent("node1", "north", "::/0")
    res.check_spf_absent("node1", "north", "2222:2222::/128")
    res.check_spf_absent("node1", "north", "3333:3333::/128")
    expect_rib = [
        r"| 2.2.2.2/32 | South SPF | if1",
        r"| 3.3.3.3/32 | South SPF | if1",
        r"| 2222:2222::/128 | South SPF | if1",
        r"| 3333:3333::/128 | South SPF | if1",
    ]
    res.check_rib("node1", expect_rib)
    res.check_rib_absent("node1", "0.0.0.0/0", "south-spf")
    res.check_rib_absent("node1", "0.0.0.0/0", "north-spf")
    res.check_rib_absent("node1", "1.1.1.1/32", "south-spf")
    res.check_rib_absent("node1", "1.1.1.1/32", "north-spf")
    res.check_rib_absent("node1", "2.2.2.2/32", "north-spf")
    res.check_rib_absent("node1", "3.3.3.3/32", "north-spf")
    res.check_rib_absent("node1", "::/0", "south-spf")
    res.check_rib_absent("node1", "::/0", "north-spf")
    res.check_rib_absent("node1", "1111:1111::/128", "south-spf")
    res.check_rib_absent("node1", "1111:1111::/128", "north-spf")
    res.check_rib_absent("node1", "2222:2222::/128", "north-spf")
    res.check_rib_absent("node1", "3333:3333::/128", "north-spf")

def check_rift_node1_intf_down(res):
    res.check_adjacency_1way(
        node="node1",
        interface="if1")
    res.check_rx_offer(
        node="node1",
        interface="if1",
        system_id="2",
        level=1,
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
        level=2,
        not_a_ztp_offer=False,
        state="ONE_WAY")
    res.check_level(
        node="node1",
        configured_level=2,
        hal="None",
        hat="None",
        level_value=2)
    expect_south_spf = [
        r"| 1 \(node1\)     | 0 |   |  |  |  |",
        r"| 1.1.1.1/32      | 1 | 1 |  |  |  |",
        r"| 1111:1111::/128 | 1 | 1 |  |  |  |",
    ]
    expect_north_spf = [
        r"| 1 \(node1\)     | 0 |   |  |  |",
        r"| 1.1.1.1/32      | 1 | 1 |  |  |",
        r"| 1111:1111::/128 | 1 | 1 |  |  |",
    ]
    res.check_spf("node1", expect_south_spf, expect_north_spf)
    res.check_spf_absent("node1", "south", "2")
    res.check_spf_absent("node1", "south", "3")
    res.check_spf_absent("node1", "south", "0.0.0.0/0")
    res.check_spf_absent("node1", "south", "2.2.2.2/32")
    res.check_spf_absent("node1", "south", "3.3.3.3/32")
    res.check_spf_absent("node1", "south", "::/0")
    res.check_spf_absent("node1", "south", "2222:2222::/128")
    res.check_spf_absent("node1", "south", "3333:3333::/128")
    res.check_spf_absent("node1", "north", "2")
    res.check_spf_absent("node1", "north", "3")
    res.check_spf_absent("node1", "north", "0.0.0.0/0")
    res.check_spf_absent("node1", "north", "2.2.2.2/32")
    res.check_spf_absent("node1", "north", "3.3.3.3/32")
    res.check_spf_absent("node1", "north", "::/0")
    res.check_spf_absent("node1", "north", "2222:2222::/128")
    res.check_spf_absent("node1", "north", "3333:3333::/128")

def check_rift_node2_intf_up(res):
    res.check_adjacency_3way(
        node="node2",
        interface="if1")
    res.check_adjacency_3way(
        node="node2",
        interface="if2")
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
    res.check_rx_offer(
        node="node2",
        interface="if2",
        system_id="3",
        level=0,
        not_a_ztp_offer="(False///True)", # Juniper lenient
        state="THREE_WAY",
        best=False,
        best_3way=False,
        removed=True,
        removed_reason="(Level is leaf///Not a ZTP offer flag set)")  # Juniper lenient
    res.check_tx_offer(
        node="node2",
        interface="if1",
        system_id="2",
        level=1,
        not_a_ztp_offer=False,
        state="THREE_WAY")
    res.check_tx_offer(
        node="node2",
        interface="if2",
        system_id="2",
        level=1,
        not_a_ztp_offer=False,
        state="THREE_WAY")
    res.check_level(
        node="node2",
        configured_level=1,
        hal=2,
        hat=2,
        level_value=1)
    expect_south_spf = [
        r"| 2 \(node2\)     | 0 |   |  |  |  |",
        r"| 3 \(node3\)     | 1 | 2 |  |  | if2",
        r"| 2.2.2.2/32      | 1 | 2 |  |  |  |",
        r"| 3.3.3.3/32      | 2 | 3 |  |  | if2",
        r"| 2222:2222::/128 | 1 | 2 |  |  |  |",
        r"| 3333:3333::/128 | 2 | 3 |  |  | if2",
    ]
    expect_north_spf = [
        r"| 1 \(node1\)     | 1 | 2 |  |  | if1",
        r"| 2 \(node2\)     | 0 |   |  |  |  |",
        r"| 0.0.0.0/0       | 2 | 1 |  |  | if1",
        r"| 2.2.2.2/32      | 1 | 2 |  |  |  |",
        r"| ::/0            | 2 | 1 |  |  | if1",
        r"| 2222:2222::/128 | 1 | 2 |  |  |  |",
    ]
    res.check_spf("node2", expect_south_spf, expect_north_spf)
    res.check_spf_absent("node2", "south", "1")
    res.check_spf_absent("node2", "south", "0.0.0.0/0")
    res.check_spf_absent("node2", "south", "1.1.1.1/32")
    res.check_spf_absent("node2", "south", "::/0")
    res.check_spf_absent("node2", "south", "1111:1111::/128")
    res.check_spf_absent("node2", "north", "3")
    res.check_spf_absent("node2", "north", "3.3.3.3/32")
    res.check_spf_absent("node2", "north", "3333:3333::/128")
    expect_rib = [
        r"| 0.0.0.0/0  | North SPF | if1",
        r"| 3.3.3.3/32 | South SPF | if2",
        r"| ::/0            | North SPF | if1",
        r"| 3333:3333::/128 | South SPF | if2",
    ]
    res.check_rib("node2", expect_rib)
    res.check_rib_absent("node2", "0.0.0.0/0", "south-spf")
    res.check_rib_absent("node2", "2.2.2.2/32", "south-spf")
    res.check_rib_absent("node2", "2.2.2.2/32", "north-spf")
    res.check_rib_absent("node2", "3.3.3.3/32", "north-spf")
    res.check_rib_absent("node2", "::/0", "south-spf")
    res.check_rib_absent("node2", "2222:2222::/128", "south-spf")
    res.check_rib_absent("node2", "2222:2222::/128", "north-spf")
    res.check_rib_absent("node2", "3333:3333::/128", "north-spf")

def check_rift_node2_intf_down(res):
    res.check_adjacency_1way(
        node="node2",
        interface="if1")
    res.check_rx_offer(
        node="node2",
        interface="if1",
        system_id="1",
        level=2,
        not_a_ztp_offer="(False///True)", # Juniper lenient
        state="THREE_WAY",
        best=False,
        best_3way=False,
        removed=True,
        removed_reason="Hold-time expired")
    res.check_rx_offer(
        node="node2",
        interface="if2",
        system_id="3",
        level=0,
        not_a_ztp_offer="(False///True)", # Juniper lenient
        state="THREE_WAY",
        best=False,
        best_3way=False,
        removed=True,
        removed_reason="(Level is leaf///Not a ZTP offer flag set)")  # Juniper lenient
    res.check_tx_offer(
        node="node2",
        interface="if1",
        system_id="2",
        level=1,
        not_a_ztp_offer=False,
        state="ONE_WAY")
    res.check_tx_offer(
        node="node2",
        interface="if2",
        system_id="2",
        level=1,
        not_a_ztp_offer=False,
        state="THREE_WAY")
    res.check_level(
        node="node2",
        configured_level=1,
        hal=None,
        hat=None,
        level_value=1)
    expect_south_spf = [
        r"| 2 \(node2\)     | 0 |   |  |  |  |",
        r"| 3 \(node3\)     | 1 | 2 |  |  | if2",
        r"| 2.2.2.2/32      | 1 | 2 |  |  |  |",
        r"| 3.3.3.3/32      | 2 | 3 |  |  | if2",
        r"| 2222:2222::/128 | 1 | 2 |  |  |  |",
        r"| 3333:3333::/128 | 2 | 3 |  |  | if2",
    ]
    expect_north_spf = [
        r"| 2 \(node2\)     | 0 |   |  |  |  |",
        r"| 2.2.2.2/32      | 1 | 2 |  |  |  |",
        r"| 2222:2222::/128 | 1 | 2 |  |  |  |",
    ]
    res.check_spf("node2", expect_south_spf, expect_north_spf)
    res.check_spf_absent("node2", "south", "1")
    res.check_spf_absent("node2", "south", "0.0.0.0/0")
    res.check_spf_absent("node2", "south", "1.1.1.1/32")
    res.check_spf_absent("node2", "south", "::/0")
    res.check_spf_absent("node2", "south", "1111:1111::/128")
    res.check_spf_absent("node2", "north", "1")
    res.check_spf_absent("node2", "north", "3")
    res.check_spf_absent("node2", "north", "0.0.0.0/0")
    res.check_spf_absent("node2", "north", "3.3.3.3/32")
    res.check_spf_absent("node2", "north", "::/0")
    res.check_spf_absent("node2", "north", "3333:3333::/128")
    expect_rib = [
        r"| 3.3.3.3/32 | South SPF | if2",
        r"| 3333:3333::/128 | South SPF | if2",
    ]
    res.check_rib("node2", expect_rib)
    res.check_rib_absent("node2", "0.0.0.0/0", "south-spf")
    res.check_rib_absent("node2", "0.0.0.0/0", "north-spf")
    res.check_rib_absent("node2", "2.2.2.2/32", "south-spf")
    res.check_rib_absent("node2", "2.2.2.2/32", "north-spf")
    res.check_rib_absent("node2", "3.3.3.3/32", "north-spf")
    res.check_rib_absent("node2", "::/0", "south-spf")
    res.check_rib_absent("node2", "::/0", "north-spf")
    res.check_rib_absent("node2", "2222:2222::/128", "south-spf")
    res.check_rib_absent("node2", "2222:2222::/128", "north-spf")
    res.check_rib_absent("node2", "3333:3333::/128", "north-spf")

def check_rift_node3_intf_up(res):
    res.check_adjacency_3way(
        node="node3",
        interface="if1")
    res.check_rx_offer(
        node="node3",
        interface="if1",
        system_id="2",
        level=1,
        not_a_ztp_offer=False,
        state="THREE_WAY",
        best=True,
        best_3way=True,
        removed=False,
        removed_reason="")
    res.check_tx_offer(
        node="node3",
        interface="if1",
        system_id="3",
        level=0,
        not_a_ztp_offer=False,
        state="THREE_WAY")
    res.check_level(
        node="node3",
        configured_level=0,
        hal=1,
        hat=1,
        level_value=0)
    expect_south_spf = [
        r"| 3 \(node3\)     | 0 |   |  |  |  |",
        r"| 3.3.3.3/32      | 1 | 3 |  |  |  |",
        r"| 3333:3333::/128 | 1 | 3 |  |  |  |",
    ]
    expect_north_spf = [
        r"| 2 \(node2\)     | 1 | 3 |  |  | if1",
        r"| 3 \(node3\)     | 0 |   |  |  |  |",
        r"| 0.0.0.0/0       | 2 | 2 |  |  | if1",
        r"| 3.3.3.3/32      | 1 | 3 |  |  |  |",
        r"| ::/0            | 2 | 2 |  |  | if1",
        r"| 3333:3333::/128 | 1 | 3 |  |  |  |",
    ]
    res.check_spf("node3", expect_south_spf, expect_north_spf)
    res.check_spf_absent("node3", "south", "1")
    res.check_spf_absent("node3", "south", "2")
    res.check_spf_absent("node3", "south", "0.0.0.0/0")
    res.check_spf_absent("node3", "south", "1.1.1.1/32")
    res.check_spf_absent("node3", "south", "2.2.2.2/32")
    res.check_spf_absent("node3", "south", "::/0")
    res.check_spf_absent("node3", "south", "1111:1111::/128")
    res.check_spf_absent("node3", "south", "2222:2222::/128")
    res.check_spf_absent("node3", "north", "1")
    res.check_spf_absent("node3", "north", "1.1.1.1/32")
    res.check_spf_absent("node3", "north", "2.2.2.2/32")
    res.check_spf_absent("node3", "north", "1111:1111::/128")
    res.check_spf_absent("node3", "north", "2222:2222::/128")
    expect_rib = [
        r"| 0.0.0.0/0 | North SPF | if1",
        r"| ::/0 | North SPF | if1",
    ]
    res.check_rib("node3", expect_rib)
    res.check_rib_absent("node3", "0.0.0.0/0", "south-spf")
    res.check_rib_absent("node3", "1.1.1.1/32", "south-spf")
    res.check_rib_absent("node3", "1.1.1.1/32", "north-spf")
    res.check_rib_absent("node3", "2.2.2.2/32", "south-spf")
    res.check_rib_absent("node3", "2.2.2.2/32", "north-spf")
    res.check_rib_absent("node3", "3.3.3.3/32", "south-spf")
    res.check_rib_absent("node3", "3.3.3.3/32", "north-spf")
    res.check_rib_absent("node3", "::/0", "south-spf")
    res.check_rib_absent("node3", "1111:1111::/128", "south-spf")
    res.check_rib_absent("node3", "1111:1111::/128", "north-spf")
    res.check_rib_absent("node3", "2222:2222::/128", "south-spf")
    res.check_rib_absent("node3", "2222:2222::/128", "north-spf")
    res.check_rib_absent("node3", "3333:3333::/128", "north-spf")
    res.check_rib_absent("node3", "3333:3333::/128", "south-spf")

def check_rift_node3_intf_down(res):
    res.check_adjacency_3way(
        node="node3",
        interface="if1")
    res.check_rx_offer(
        node="node3",
        interface="if1",
        system_id="2",
        level=1,
        not_a_ztp_offer=False,
        state="THREE_WAY",
        best=True,
        best_3way=True,
        removed=False,
        removed_reason="")
    res.check_tx_offer(
        node="node3",
        interface="if1",
        system_id="3",
        level=0,
        not_a_ztp_offer=False,
        state="THREE_WAY")
    res.check_level(
        node="node3",
        configured_level=0,
        hal=1,
        hat=1,
        level_value=0)
    expect_south_spf = [
        r"| 3 \(node3\)     | 0 |   |  |  |  |",
        r"| 3.3.3.3/32      | 1 | 3 |  |  |  |",
        r"| 3333:3333::/128 | 1 | 3 |  |  |  |",
    ]
    expect_north_spf = [
        r"| 2 \(node2\)     | 1 | 3 |  |  | if1",
        r"| 3 \(node3\)     | 0 |   |  |  |  |",
        r"| 0.0.0.0/0       | 2 | 2 |  |  | if1",
        r"| 3.3.3.3/32      | 1 | 3 |  |  |  |",
        r"| ::/0            | 2 | 2 |  |  | if1",
        r"| 3333:3333::/128 | 1 | 3 |  |  |  |",
    ]
    res.check_spf("node3", expect_south_spf, expect_north_spf)
    res.check_spf_absent("node3", "south", "1")
    res.check_spf_absent("node3", "south", "2")
    res.check_spf_absent("node3", "south", "0.0.0.0/0")
    res.check_spf_absent("node3", "south", "1.1.1.1/32")
    res.check_spf_absent("node3", "south", "2.2.2.2/32")
    res.check_spf_absent("node3", "south", "::/0")
    res.check_spf_absent("node3", "south", "1111:1111::/128")
    res.check_spf_absent("node3", "south", "2222:2222::/128")
    res.check_spf_absent("node3", "north", "1")
    res.check_spf_absent("node3", "north", "1.1.1.1/32")
    res.check_spf_absent("node3", "north", "2.2.2.2/32")
    res.check_spf_absent("node3", "north", "1111:1111::/128")
    res.check_spf_absent("node3", "north", "2222:2222::/128")
    expect_rib = [
        r"| 0.0.0.0/0 | North SPF | if1",
        r"| ::/0 | North SPF | if1",
    ]
    res.check_rib("node3", expect_rib)
    res.check_rib_absent("node3", "0.0.0.0/0", "south-spf")
    res.check_rib_absent("node3", "1.1.1.1/32", "south-spf")
    res.check_rib_absent("node3", "1.1.1.1/32", "north-spf")
    res.check_rib_absent("node3", "2.2.2.2/32", "south-spf")
    res.check_rib_absent("node3", "2.2.2.2/32", "north-spf")
    res.check_rib_absent("node3", "3.3.3.3/32", "north-spf")
    res.check_rib_absent("node3", "3.3.3.3/32", "south-spf")
    res.check_rib_absent("node3", "::/0", "south-spf")
    res.check_rib_absent("node3", "1111:1111::/128", "south-spf")
    res.check_rib_absent("node3", "1111:1111::/128", "north-spf")
    res.check_rib_absent("node3", "2222:2222::/128", "south-spf")
    res.check_rib_absent("node3", "2222:2222::/128", "north-spf")
    res.check_rib_absent("node3", "3333:3333::/128", "south-spf")
    res.check_rib_absent("node3", "3333:3333::/128", "north-spf")

def check_log_node1_intf_up(les):
    les.check_lie_fsm_3way("node1", "if1")

def check_log_node1_intf_down(les):
    les.check_lie_fsm_timeout_to_1way("node1", "if1", "set interface if1 failure failed")

def check_log_node2_intf_up(les):
    les.check_lie_fsm_3way("node2", "if1")
    les.check_lie_fsm_3way("node2", "if2")

def check_log_node2_intf_down(les):
    les.check_lie_fsm_timeout_to_1way("node2", "if1", "set interface if1 failure failed")

def check_log_node3_intf_up(les):
    les.check_lie_fsm_3way("node3", "if1")

def check_log_node3_intf_down(les):
    les.check_lie_fsm_3way("node3", "if1")

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
        check_log_node1_intf_down(les)
        if "node2" not in passive_nodes:
            check_rift_node2_intf_down(res)
            check_log_node2_intf_down(les)
        if "node3" not in passive_nodes:
            check_rift_node3_intf_down(res)
            check_log_node3_intf_down(les)
        # Bring interface if1 on node1 up again
        res.interface_failure("node1", "if1", "ok")
        check_rift_node1_intf_up(res)
        check_log_node1_intf_up(les)
        if "node2" not in passive_nodes:
            check_rift_node2_intf_up(res)
            check_log_node2_intf_up(les)
        if "node3" not in passive_nodes:
            check_rift_node3_intf_up(res)
            check_log_node3_intf_up(les)
    # TODO: add test cases for bringing interface node2-node3 down
    # Done
    res.stop()
