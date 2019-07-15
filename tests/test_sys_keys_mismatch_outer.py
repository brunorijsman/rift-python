# System test: test_sys_keys_mismatch_outer

import os
from rift_expect_session import RiftExpectSession

def check_rift_node1(res):
    res.check_adjacency_3way(
        node="node1",
        interface="if1")
    expect_rib = [
        r"| 2.2.2.2/32 | South SPF | if1",
    ]
    res.check_rib("node1", expect_rib)
    res.check_rib_absent("node1", "3.3.3.3/32", "south-spf")
    expect_node_security = [
        r"Origin Keys:",
        r"| Active Origin Key  | 3  | Node Active Origin Key |",
        r"| Accept Origin Keys |    | Node Accept Keys       |",
    ]
    res.check_node_security("node1", expect_node_security)
    expect_intf_security = [
        r"Outer Keys:",
        r"| Key | Key ID\(s\) | Configuration Source |",
        r"| Active Outer Key  | 1 | Node Active Key  |",
        r"| Accept Outer Keys |   | Node Accept Keys |",
        r"Nonces:",
        r"| Last Received LIE Nonce  | [0-9]*[1-9][0-9]* |",   # non-zero value
        r"| Last Sent Nonce          | [0-9]*[1-9][0-9]* |",   # non-zero value
        r"| Next Sent Nonce Increase | .* |",
    ]
    res.check_intf_security("node1", "if1", expect_intf_security)

def check_rift_node2(res):
    res.check_adjacency_3way(
        node="node2",
        interface="if1")
    res.check_adjacency_1way(
        node="node2",
        interface="if2")
    expect_rib = [
        r"| 0.0.0.0/0 | North SPF | if1",
    ]
    res.check_rib("node2", expect_rib)
    res.check_rib_absent("node2", "3.3.3.3/32", "south-spf")
    expect_node_security = [
        r"Origin Keys:",
        r"| Active Origin Key  | 3  | Node Active Origin Key |",
        r"| Accept Origin Keys |    | Node Accept Keys       |",
    ]
    res.check_node_security("node2", expect_node_security)
    expect_intf_security = [
        r"Outer Keys:",
        r"| Key | Key ID\(s\) | Configuration Source |",
        r"| Active Outer Key  | 1 | Node Active Key  |",
        r"| Accept Outer Keys |   | Node Accept Keys |",
        r"Nonces:",
        r"| Last Received LIE Nonce  | [0-9]*[1-9][0-9]* |",   # non-zero value
        r"| Last Sent Nonce          | [0-9]*[1-9][0-9]* |",   # non-zero value
        r"| Next Sent Nonce Increase | .* |",
    ]
    res.check_intf_security("node2", "if1", expect_intf_security)
    expect_intf_security = [
        r"Outer Keys:",
        r"| Key | Key ID\(s\) | Configuration Source |",
        r"| Active Outer Key  | 1 | Node Active Key  |",
        r"| Accept Outer Keys |   | Node Accept Keys |",
        r"Nonces:",
        r"| Last Received LIE Nonce  | 0 |",
        r"| Last Sent Nonce          | [0-9]*[1-9][0-9]* |",   # non-zero value
        r"| Next Sent Nonce Increase | .* |",
        r"Security Statistics:",
        r"| Non-zero outer key id not accepted | [0-9]*[1-9][0-9]* Packets",   # non-zero value
    ]
    res.check_intf_security("node2", "if2", expect_intf_security)

def check_rift_node3(res):
    res.check_adjacency_1way(
        node="node3",
        interface="if1")
    res.check_rib_absent("node3", "0.0.0.0/0", "north-spf")
    expect_node_security = [
        r"Origin Keys:",
        r"| Active Origin Key  | 3  | Node Active Origin Key |",
        r"| Accept Origin Keys |    | Node Accept Keys       |",
    ]
    res.check_node_security("node3", expect_node_security)
    expect_intf_security = [
        r"Outer Keys:",
        r"| Key | Key ID\(s\) | Configuration Source |",
        r"| Active Outer Key  | 2 | Node Active Key  |",
        r"| Accept Outer Keys |   | Node Accept Keys |",
        r"Nonces:",
        r"| Last Received LIE Nonce  | 0 |",
        r"| Last Sent Nonce          | [0-9]*[1-9][0-9]* |",   # non-zero value
        r"| Next Sent Nonce Increase | .* |",
        r"Security Statistics:",
        r"| Non-zero outer key id not accepted | [0-9]*[1-9][0-9]* Packets",   # non-zero value
    ]
    res.check_intf_security("node3", "if1", expect_intf_security)

def test_keys_mismatch_outer():
    passive_nodes = os.getenv("RIFT_PASSIVE_NODES", "").split(",")
    res = RiftExpectSession("keys_mismatch_outer")
    if "node1" not in passive_nodes:
        check_rift_node1(res)
    if "node2" not in passive_nodes:
        check_rift_node2(res)
    if "node3" not in passive_nodes:
        check_rift_node3(res)
    res.stop()
