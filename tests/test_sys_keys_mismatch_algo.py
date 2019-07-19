# System test: test_sys_keys_mismatch_algo

import os
from rift_expect_session import RiftExpectSession

def check_rift_node1(res):
    res.check_adjacency_3way(
        node="node1",
        interface="if1")
    res.check_rib_absent("node1", "2.2.2.2/32", "south-spf")
    res.check_rib_absent("node1", "3.3.3.3/32", "south-spf")
    expect_node_security = [
        r"Security Keys:",
        r"| Key ID | Algorithm    | Secret                                            |",
        r"| 0      | null         |                                                   |",
        r"| 1      | sha-256      | all-keys-have-different-algos-but-the-same-secret |",
        r"| 2      | sha-512      | all-keys-have-different-algos-but-the-same-secret |",
        r"| 3      | hmac-sha-256 | all-keys-have-different-algos-but-the-same-secret |",
        r"| 4      | hmac-sha-512 | all-keys-have-different-algos-but-the-same-secret |",
        r"Origin Keys:",
        r"| Active Origin Key  | 3 |",
        r"| Accept Origin Keys |   |",
    ]
    res.check_node_security("node1", expect_node_security)
    expect_intf_security = [
        r"Outer Keys:",
        r"| Key | Key ID\(s\) | Configuration Source |",
        r"| Active Outer Key  | 1 | Interface Active Key |",
        r"| Accept Outer Keys |   | Node Accept Keys     |",
        r"Security Statistics:",
        r"| Missing outer security envelope | 0 Packets",
        r"| Zero outer key id not accepted | 0 Packets",
        r"| Non-zero outer key id not accepted | 0 Packets",
        r"| Incorrect outer fingerprint | 0 Packets",
        r"| Missing TIE origin security envelope | 0 Packets",
        r"| Zero TIE origin key id not accepted | 0 Packets",
        r"| Non-zero TIE origin key id not accepted | [0-9]*[1-9][0-9]* Packets",
        r"| Unexpected TIE origin security envelope | 0 Packets",
        r"| Inconsistent TIE origin key id and fingerprint | 0 Packets",
        r"| Incorrect TIE origin fingerprint | 0 Packets",
        r"| Reflected nonce out of sync | 0 Packets",
        r"| Total Authentication Errors | [0-9]*[1-9][0-9]* Packets",
        r"| Non-empty outer fingerprint accepted | [0-9]*[1-9][0-9]* Packets",
        r"| Non-empty origin fingerprint accepted | 0 Packets",
        r"| Empty outer fingerprint accepted | 0 Packets",
        r"| Empty origin fingerprint accepted | 0 Packets",
    ]
    res.check_intf_security("node1", "if1", expect_intf_security)

def check_rift_node2(res):
    res.check_adjacency_3way(
        node="node2",
        interface="if1")
    res.check_adjacency_1way(
        node="node2",
        interface="if2")
    res.check_rib_absent("node1", "0.0.0.0/0", "north-spf")
    res.check_rib_absent("node1", "3.3.3.3/32", "south-spf")
    expect_node_security = [
        r"Origin Keys:",
        r"| Active Origin Key  | 4 |",
        r"| Accept Origin Keys |   |",
    ]
    res.check_node_security("node2", expect_node_security)
    expect_intf_security = [
        r"Outer Keys:",
        r"| Key | Key ID\(s\) | Configuration Source |",
        r"| Active Outer Key  | 1 | Interface Active Key |",
        r"| Accept Outer Keys |   | Node Accept Keys     |",
        r"Security Statistics:",
        r"| Missing outer security envelope | 0 Packets",
        r"| Zero outer key id not accepted | 0 Packets",
        r"| Non-zero outer key id not accepted | 0 Packets",
        r"| Incorrect outer fingerprint | 0 Packets",
        r"| Missing TIE origin security envelope | 0 Packets",
        r"| Zero TIE origin key id not accepted | 0 Packets",
        r"| Non-zero TIE origin key id not accepted | [0-9]*[1-9][0-9]* Packets",
        r"| Unexpected TIE origin security envelope | 0 Packets",
        r"| Inconsistent TIE origin key id and fingerprint | 0 Packets",
        r"| Incorrect TIE origin fingerprint | 0 Packets",
        r"| Reflected nonce out of sync | 0 Packets",
        r"| Total Authentication Errors | [0-9]*[1-9][0-9]* Packets",
        r"| Non-empty outer fingerprint accepted | [0-9]*[1-9][0-9]* Packets",
        r"| Non-empty origin fingerprint accepted | 0 Packets",
        r"| Empty outer fingerprint accepted | 0 Packets",
        r"| Empty origin fingerprint accepted | 0 Packets",
    ]
    res.check_intf_security("node2", "if1", expect_intf_security)
    expect_intf_security = [
        r"Outer Keys:",
        r"| Key | Key ID\(s\) | Configuration Source |",
        r"| Active Outer Key  | 1 | Interface Active Key |",
        r"| Accept Outer Keys |   | Node Accept Keys     |",
        r"Security Statistics:",
        r"| Missing outer security envelope | 0 Packets",
        r"| Zero outer key id not accepted | 0 Packets",
        r"| Non-zero outer key id not accepted | [0-9]*[1-9][0-9]* Packets",
        r"| Incorrect outer fingerprint | 0 Packets",
        r"| Missing TIE origin security envelope | 0 Packets",
        r"| Zero TIE origin key id not accepted | 0 Packets",
        r"| Non-zero TIE origin key id not accepted | 0 Packets",
        r"| Unexpected TIE origin security envelope | 0 Packets",
        r"| Inconsistent TIE origin key id and fingerprint | 0 Packets",
        r"| Incorrect TIE origin fingerprint | 0 Packets",
        r"| Reflected nonce out of sync | 0 Packets",
        r"| Total Authentication Errors | [0-9]*[1-9][0-9]* Packets",
        r"| Non-empty outer fingerprint accepted | 0 Packets",
        r"| Non-empty origin fingerprint accepted | 0 Packets",
        r"| Empty outer fingerprint accepted | 0 Packets",
        r"| Empty origin fingerprint accepted | 0 Packets",
    ]
    res.check_intf_security("node2", "if2", expect_intf_security)

def check_rift_node3(res):
    res.check_adjacency_1way(
        node="node3",
        interface="if1")
    res.check_rib_absent("node3", "0.0.0.0/0", "north-spf")
    expect_node_security = [
        r"Origin Keys:",
        r"| Active Origin Key  | 4 |",
        r"| Accept Origin Keys |   |",
    ]
    res.check_node_security("node3", expect_node_security)
    expect_intf_security = [
        r"Outer Keys:",
        r"| Key | Key ID\(s\) | Configuration Source |",
        r"| Active Outer Key  | 2 | Interface Active Key |",
        r"| Accept Outer Keys |   | Node Accept Keys     |",
        r"Security Statistics:",
        r"| Missing outer security envelope | 0 Packets",
        r"| Zero outer key id not accepted | 0 Packets",
        r"| Non-zero outer key id not accepted | [0-9]*[1-9][0-9]* Packets",
        r"| Incorrect outer fingerprint | 0 Packets",
        r"| Missing TIE origin security envelope | 0 Packets",
        r"| Zero TIE origin key id not accepted | 0 Packets",
        r"| Non-zero TIE origin key id not accepted | 0 Packets",
        r"| Unexpected TIE origin security envelope | 0 Packets",
        r"| Inconsistent TIE origin key id and fingerprint | 0 Packets",
        r"| Incorrect TIE origin fingerprint | 0 Packets",
        r"| Reflected nonce out of sync | 0 Packets",
        r"| Total Authentication Errors | [0-9]*[1-9][0-9]* Packets",
        r"| Non-empty outer fingerprint accepted | 0 Packets",
        r"| Non-empty origin fingerprint accepted | 0 Packets",
        r"| Empty outer fingerprint accepted | 0 Packets",
        r"| Empty origin fingerprint accepted | 0 Packets",
    ]
    res.check_intf_security("node3", "if1", expect_intf_security)

def test_keys_mismatch_origin():
    passive_nodes = os.getenv("RIFT_PASSIVE_NODES", "").split(",")
    res = RiftExpectSession("keys_mismatch_algo")
    if "node1" not in passive_nodes:
        check_rift_node1(res)
    if "node2" not in passive_nodes:
        check_rift_node2(res)
    if "node3" not in passive_nodes:
        check_rift_node3(res)
    res.stop()
