# System test: test_sys_keys_match_node

import os
from rift_expect_session import RiftExpectSession

def check_rift_node1(res):
    res.check_adjacency_3way(
        node="node1",
        interface="if1")
    expect_rib = [
        r"| 2.2.2.2/32 | South SPF | if1",
        r"| 3.3.3.3/32 | South SPF | if1",
    ]
    res.check_rib("node1", expect_rib)

def check_rift_node2(res):
    res.check_adjacency_3way(
        node="node2",
        interface="if1")
    res.check_adjacency_3way(
        node="node2",
        interface="if2")
    expect_rib = [
        r"| 0.0.0.0/0  | North SPF | if1",
        r"| 3.3.3.3/32 | South SPF | if2",
    ]
    res.check_rib("node2", expect_rib)

def check_rift_node3(res):
    res.check_adjacency_3way(
        node="node3",
        interface="if1")
    expect_rib = [
        r"| 0.0.0.0/0 | North SPF | if1",
    ]
    res.check_rib("node3", expect_rib)

def test_keys_match_node():
    passive_nodes = os.getenv("RIFT_PASSIVE_NODES", "").split(",")
    res = RiftExpectSession("3n_l0_l1_l2")
    if "node1" not in passive_nodes:
        check_rift_node1(res)
    if "node2" not in passive_nodes:
        check_rift_node2(res)
    if "node3" not in passive_nodes:
        check_rift_node3(res)
    res.stop()
