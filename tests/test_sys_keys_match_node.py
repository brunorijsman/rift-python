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
    expect_node_security = [
        r"Security Keys:",
        r"| Key ID | Algorithm    | Secret                       | Active | Accept |",
        r"| 1      | hmac-sha-256 | this-is-the-secret-for-key-1 | Active |        |",
        r"| 2      | hmac-sha-256 | this-is-the-secret-for-key-2 |        | Accept |",
        r"| 3      | hmac-sha-256 | this-is-the-secret-for-key-3 |        |        |",
    ]
    res.check_node_security("node1", expect_node_security)
    expect_intf_security = [
        r"| Outer Key Source             | Node |",
        r"| Active Outer Key             | 1    |",
        r"| Additional Accept Outer Keys | 2    |",
    ]
    res.check_intf_security("node1", "if1", expect_intf_security)

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
    expect_node_security = [
        r"Security Keys:",
        r"| Key ID | Algorithm    | Secret                       | Active | Accept |",
        r"| 1      | hmac-sha-256 | this-is-the-secret-for-key-1 | Active |        |",
        r"| 2      | hmac-sha-256 | this-is-the-secret-for-key-2 |        | Accept |",
        r"| 3      | hmac-sha-256 | this-is-the-secret-for-key-3 |        |        |",
    ]
    res.check_node_security("node2", expect_node_security)
    expect_intf_security = [
        r"| Outer Key Source             | Node |",
        r"| Active Outer Key             | 1    |",
        r"| Additional Accept Outer Keys | 2    |",
    ]
    res.check_intf_security("node2", "if1", expect_intf_security)
    res.check_intf_security("node2", "if2", expect_intf_security)

def check_rift_node3(res):
    res.check_adjacency_3way(
        node="node3",
        interface="if1")
    expect_rib = [
        r"| 0.0.0.0/0 | North SPF | if1",
    ]
    res.check_rib("node3", expect_rib)
    expect_node_security = [
        r"Security Keys:",
        r"| Key ID | Algorithm    | Secret                       | Active | Accept |",
        r"| 1      | hmac-sha-256 | this-is-the-secret-for-key-1 |        | Accept |",
        r"| 2      | hmac-sha-256 | this-is-the-secret-for-key-2 | Active |        |",
        r"| 3      | hmac-sha-256 | this-is-the-secret-for-key-3 |        | Accept |",
    ]
    res.check_node_security("node3", expect_node_security)
    expect_intf_security = [
        r"| Outer Key Source             | Node |",
        r"| Active Outer Key             | 2    |",
        r"| Additional Accept Outer Keys | 3, 1 |",
    ]
    res.check_intf_security("node3", "if1", expect_intf_security)

def test_keys_match_node():
    passive_nodes = os.getenv("RIFT_PASSIVE_NODES", "").split(",")
    res = RiftExpectSession("keys_match_node")
    if "node1" not in passive_nodes:
        check_rift_node1(res)
    if "node2" not in passive_nodes:
        check_rift_node2(res)
    if "node3" not in passive_nodes:
        check_rift_node3(res)
    res.stop()
