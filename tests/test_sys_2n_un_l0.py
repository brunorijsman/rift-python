# System test: test_sys_2n_un_l0
#
# Topology: 2n_un_l0
#
#  +-------------------+
#  | node1             |
#  | (level 0)         |
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
# - node1 is hard-configured as level 0
# - node2 is level undefined, i.e. it uses ZTP to auto-discover its level
# - One link: node1:if1 - node2:if1
#
# Test scenario:
# - Bring the topology up
# - Both nodes report adjacency to other node up as in state 3-way
# - Node1 is hard-configured level 0
# - The adjacency stays in ONE_WAY

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
