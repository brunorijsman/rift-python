import logging
import re

import constants
import encoding.ttypes
import engine
import interface
import neighbor
import node
import packet_common

# pylint:disable=invalid-name
# pylint:disable=line-too-long
# pylint:disable=too-many-lines

NODE_SYSID = 1
NODE_LEVEL = 0
PARENT_LEVEL = 1
GRANDPARENT_LEVEL = 2

SOUTH = constants.DIR_SOUTH
NORTH = constants.DIR_NORTH
EW = constants.DIR_EAST_WEST

def make_test_node(parents, additional_node_config=None):
    test_engine = engine.Engine(
        passive_nodes=[],
        run_which_nodes=[],
        interactive=False,
        telnet_port_file=None,
        ipv4_multicast_loopback=False,
        ipv6_multicast_loopback=False,
        log_level=logging.CRITICAL,
        config={}
    )
    test_engine.floodred_system_random = 11111111111111111111    # Make unit test deterministic
    node_config = {
        "name": "node" + str(NODE_SYSID),
        "systemid": NODE_SYSID,
        "level": NODE_LEVEL,
        "skip-self-orginated-ties": True  # The test is in control of what TIEs are in the DB
    }
    if additional_node_config:
        node_config.update(additional_node_config)
    test_node = node.Node(node_config, test_engine)
    # Create fake interfaces for parents (in state 3-way)
    for parent_sysid in parents.keys():
        make_parent_interface(test_node, parent_sysid)
    # Fill TIE-DB for the first time
    update_test_node(test_node, parents)
    return test_node

def update_test_node(test_node, parents):
    grandparents = compute_grandparents_connectivity(parents)
    # Empty the TIE-DB (we are going to re-build it from scratch)
    test_node.tie_packet_infos.clear()
    # Add self-originated Node-TIE for node to TIE-DB
    neighbors = []
    for parent_sysid, _grandparent_sysids in parents.items():
        neighbor_info = (PARENT_LEVEL, parent_sysid)
        neighbors.append(neighbor_info)
    node_tie_packet = make_node_tie_packet(NODE_SYSID, NODE_LEVEL, neighbors)
    test_node.store_tie_packet(node_tie_packet, 100)
    # Add Node-TIEs for parents to TIE-DB
    for parent_sysid, grandparent_sysids in parents.items():
        neighbors = []
        neighbor_info = (NODE_LEVEL, NODE_SYSID)
        neighbors.append(neighbor_info)
        for grandparent_sysid in grandparent_sysids:
            neighbor_info = (GRANDPARENT_LEVEL, grandparent_sysid)
            neighbors.append(neighbor_info)
        node_tie_packet = make_node_tie_packet(parent_sysid, PARENT_LEVEL, neighbors)
        test_node.store_tie_packet(node_tie_packet, 100)
    # Add Node-TIEs for grandparents to TIE-DB
    for grandparent_sysid, parent_sysids in grandparents.items():
        neighbors = []
        for parent_sysid in parent_sysids:
            neighbor_info = (PARENT_LEVEL, parent_sysid)
            neighbors.append(neighbor_info)
        node_tie_packet = make_node_tie_packet(grandparent_sysid, GRANDPARENT_LEVEL, neighbors)
        test_node.store_tie_packet(node_tie_packet, 100)

def make_node_tie_packet(sysid, level, neighbors):
    node_tie = packet_common.make_node_tie_packet(
        name="node" + str(sysid),
        level=level,
        direction=SOUTH,
        originator=sysid,
        tie_nr=1,
        seq_nr=1)
    for neighbor_info in neighbors:
        neighbor_level, neighbor_sysid = neighbor_info
        local_link_id = neighbor_sysid
        remote_link_id = sysid
        link_id_pair = encoding.ttypes.LinkIDPair(local_link_id, remote_link_id)
        link_ids = set([link_id_pair])
        neighbor_tie_element = encoding.ttypes.NodeNeighborsTIEElement(
            level=neighbor_level,
            cost=1,
            link_ids=link_ids,
            bandwidth=100)
        node_tie.element.node.neighbors[neighbor_sysid] = neighbor_tie_element
    return node_tie

def make_parent_interface(test_node, parent_sysid):
    intf_name = "intf" + str(parent_sysid)
    intf_config = {
        "name": intf_name
    }
    intf = test_node.create_interface(intf_config)
    lie_neighbor = encoding.ttypes.Neighbor(parent_sysid, 0)
    lie_packet = encoding.ttypes.LIEPacket(
        name="intf" + str(test_node.system_id),
        local_id=0,
        flood_port=0,
        link_mtu_size=1500,
        neighbor=lie_neighbor,
        pod=0,
        # nonce=0,
        node_capabilities=None,
        holdtime=3,
        not_a_ztp_offer=False,
        you_are_flood_repeater=False,
        label=None)
    packet_content = encoding.ttypes.PacketContent(lie=lie_packet)
    packet_header = encoding.ttypes.PacketHeader(
        sender=parent_sysid,
        level=PARENT_LEVEL)
    lie_protocol_packet = encoding.ttypes.ProtocolPacket(packet_header, packet_content)
    # pylint:disable=protected-access
    intf.fsm._state = interface.Interface.State.THREE_WAY
    intf.neighbor = neighbor.Neighbor(
        lie_protocol_packet=lie_protocol_packet,
        neighbor_address="1.1.1.1",
        neighbor_port=1)

def check_flood_repeater_election(parents, expected_parents, expected_grandparents, expected_intfs,
                                  additional_node_config=None):
    test_node = make_test_node(parents, additional_node_config)
    test_node.floodred_elect_repeaters()
    if expected_parents:
        assert test_node.floodred_parents_table().to_string() == expected_parents
    if expected_grandparents:
        assert test_node.floodred_grandparents_table().to_string() == expected_grandparents
    assert test_node.floodred_interfaces_table().to_string() == expected_intfs
    return test_node

def compute_grandparents_connectivity(parents):
    grandparents = {}
    for parent_sysid, grandparent_sysids in parents.items():
        for grandparent_sysid in grandparent_sysids:
            if grandparent_sysid not in grandparents:
                grandparents[grandparent_sysid] = []
            if parent_sysid not in grandparents[grandparent_sysid]:
                grandparents[grandparent_sysid].append(parent_sysid)
    return grandparents

def test_3x3_full():
    # 3 parents (11, 12, 13)
    # 3 grandparents (21, 22, 23)
    # Full connectivity between parents and grandparents
    packet_common.add_missing_methods_to_thrift()
    parents = {
        11: [21, 22, 23],
        12: [21, 22, 23],
        13: [21, 22, 23]
    }
    expected_parents = (
        "+-----------+-----------+-----------+-------------+------------+----------+\n"
        "| Interface | Parent    | Parent    | Grandparent | Similarity | Flood    |\n"
        "| Name      | System ID | Interface | Count       | Group      | Repeater |\n"
        "|           |           | Name      |             |            |          |\n"
        "+-----------+-----------+-----------+-------------+------------+----------+\n"
        "| intf12    | 12        | intf1     | 3           | 1: 3-3     | True     |\n"
        "+-----------+-----------+-----------+-------------+------------+----------+\n"
        "| intf11    | 11        | intf1     | 3           | 1: 3-3     | True     |\n"
        "+-----------+-----------+-----------+-------------+------------+----------+\n"
        "| intf13    | 13        | intf1     | 3           | 1: 3-3     | False    |\n"
        "+-----------+-----------+-----------+-------------+------------+----------+\n")
    expected_grandparents = (
        "+-------------+--------+-------------+-------------+\n"
        "| Grandparent | Parent | Flood       | Redundantly |\n"
        "| System ID   | Count  | Repeater    | Covered     |\n"
        "|             |        | Adjacencies |             |\n"
        "+-------------+--------+-------------+-------------+\n"
        "| 21          | 3      | 2           | True        |\n"
        "+-------------+--------+-------------+-------------+\n"
        "| 22          | 3      | 2           | True        |\n"
        "+-------------+--------+-------------+-------------+\n"
        "| 23          | 3      | 2           | True        |\n"
        "+-------------+--------+-------------+-------------+\n")
    expected_intfs = (
        "+-----------+-----------+-----------+-----------+-----------+----------------+----------------+\n"
        "| Interface | Neighbor  | Neighbor  | Neighbor  | Neighbor  | Neighbor is    | This Node is   |\n"
        "| Name      | Interface | System ID | State     | Direction | Flood Repeater | Flood Repeater |\n"
        "|           | Name      |           |           |           | for This Node  | for Neighbor   |\n"
        "+-----------+-----------+-----------+-----------+-----------+----------------+----------------+\n"
        "| intf11    | intf1     | 11        | THREE_WAY | North     | True (Pending) | Not Applicable |\n"
        "+-----------+-----------+-----------+-----------+-----------+----------------+----------------+\n"
        "| intf12    | intf1     | 12        | THREE_WAY | North     | True (Pending) | Not Applicable |\n"
        "+-----------+-----------+-----------+-----------+-----------+----------------+----------------+\n"
        "| intf13    | intf1     | 13        | THREE_WAY | North     | False          | Not Applicable |\n"
        "+-----------+-----------+-----------+-----------+-----------+----------------+----------------+\n")
    check_flood_repeater_election(parents, expected_parents, expected_grandparents, expected_intfs)

def test_8x8_full():
    # 8 parents (11, ..., 18)
    # 8 grandparents (21, ..., 28)
    # Full connectivity between parents and grandparents
    packet_common.add_missing_methods_to_thrift()
    parents = {
        11: [21, 22, 23, 24, 25, 26, 27, 28],
        12: [21, 22, 23, 24, 25, 26, 27, 28],
        13: [21, 22, 23, 24, 25, 26, 27, 28],
        14: [21, 22, 23, 24, 25, 26, 27, 28],
        15: [21, 22, 23, 24, 25, 26, 27, 28],
        16: [21, 22, 23, 24, 25, 26, 27, 28],
        17: [21, 22, 23, 24, 25, 26, 27, 28],
        18: [21, 22, 23, 24, 25, 26, 27, 28]
    }
    expected_parents = (
        "+-----------+-----------+-----------+-------------+------------+----------+\n"
        "| Interface | Parent    | Parent    | Grandparent | Similarity | Flood    |\n"
        "| Name      | System ID | Interface | Count       | Group      | Repeater |\n"
        "|           |           | Name      |             |            |          |\n"
        "+-----------+-----------+-----------+-------------+------------+----------+\n"
        "| intf17    | 17        | intf1     | 8           | 1: 8-8     | True     |\n"
        "+-----------+-----------+-----------+-------------+------------+----------+\n"
        "| intf15    | 15        | intf1     | 8           | 1: 8-8     | True     |\n"
        "+-----------+-----------+-----------+-------------+------------+----------+\n"
        "| intf13    | 13        | intf1     | 8           | 1: 8-8     | False    |\n"
        "+-----------+-----------+-----------+-------------+------------+----------+\n"
        "| intf14    | 14        | intf1     | 8           | 1: 8-8     | False    |\n"
        "+-----------+-----------+-----------+-------------+------------+----------+\n"
        "| intf11    | 11        | intf1     | 8           | 1: 8-8     | False    |\n"
        "+-----------+-----------+-----------+-------------+------------+----------+\n"
        "| intf18    | 18        | intf1     | 8           | 1: 8-8     | False    |\n"
        "+-----------+-----------+-----------+-------------+------------+----------+\n"
        "| intf16    | 16        | intf1     | 8           | 1: 8-8     | False    |\n"
        "+-----------+-----------+-----------+-------------+------------+----------+\n"
        "| intf12    | 12        | intf1     | 8           | 1: 8-8     | False    |\n"
        "+-----------+-----------+-----------+-------------+------------+----------+\n")
    expected_grandparents = (
        "+-------------+--------+-------------+-------------+\n"
        "| Grandparent | Parent | Flood       | Redundantly |\n"
        "| System ID   | Count  | Repeater    | Covered     |\n"
        "|             |        | Adjacencies |             |\n"
        "+-------------+--------+-------------+-------------+\n"
        "| 21          | 8      | 2           | True        |\n"
        "+-------------+--------+-------------+-------------+\n"
        "| 22          | 8      | 2           | True        |\n"
        "+-------------+--------+-------------+-------------+\n"
        "| 23          | 8      | 2           | True        |\n"
        "+-------------+--------+-------------+-------------+\n"
        "| 24          | 8      | 2           | True        |\n"
        "+-------------+--------+-------------+-------------+\n"
        "| 25          | 8      | 2           | True        |\n"
        "+-------------+--------+-------------+-------------+\n"
        "| 26          | 8      | 2           | True        |\n"
        "+-------------+--------+-------------+-------------+\n"
        "| 27          | 8      | 2           | True        |\n"
        "+-------------+--------+-------------+-------------+\n"
        "| 28          | 8      | 2           | True        |\n"
        "+-------------+--------+-------------+-------------+\n")
    expected_intfs = (
        "+-----------+-----------+-----------+-----------+-----------+----------------+----------------+\n"
        "| Interface | Neighbor  | Neighbor  | Neighbor  | Neighbor  | Neighbor is    | This Node is   |\n"
        "| Name      | Interface | System ID | State     | Direction | Flood Repeater | Flood Repeater |\n"
        "|           | Name      |           |           |           | for This Node  | for Neighbor   |\n"
        "+-----------+-----------+-----------+-----------+-----------+----------------+----------------+\n"
        "| intf11    | intf1     | 11        | THREE_WAY | North     | False          | Not Applicable |\n"
        "+-----------+-----------+-----------+-----------+-----------+----------------+----------------+\n"
        "| intf12    | intf1     | 12        | THREE_WAY | North     | False          | Not Applicable |\n"
        "+-----------+-----------+-----------+-----------+-----------+----------------+----------------+\n"
        "| intf13    | intf1     | 13        | THREE_WAY | North     | False          | Not Applicable |\n"
        "+-----------+-----------+-----------+-----------+-----------+----------------+----------------+\n"
        "| intf14    | intf1     | 14        | THREE_WAY | North     | False          | Not Applicable |\n"
        "+-----------+-----------+-----------+-----------+-----------+----------------+----------------+\n"
        "| intf15    | intf1     | 15        | THREE_WAY | North     | True (Pending) | Not Applicable |\n"
        "+-----------+-----------+-----------+-----------+-----------+----------------+----------------+\n"
        "| intf16    | intf1     | 16        | THREE_WAY | North     | False          | Not Applicable |\n"
        "+-----------+-----------+-----------+-----------+-----------+----------------+----------------+\n"
        "| intf17    | intf1     | 17        | THREE_WAY | North     | True (Pending) | Not Applicable |\n"
        "+-----------+-----------+-----------+-----------+-----------+----------------+----------------+\n"
        "| intf18    | intf1     | 18        | THREE_WAY | North     | False          | Not Applicable |\n"
        "+-----------+-----------+-----------+-----------+-----------+----------------+----------------+\n")
    check_flood_repeater_election(parents, expected_parents, expected_grandparents, expected_intfs)

def test_1x1():
    # 1 parents (11)
    # 1 grandparents (21)
    # Full connectivity between parents and grandparents (of course)
    # In this test case, the parent only has 1 grandparent, so it is not possible to meet the
    # desired reduncancy of 2 separate paths to each grandparent
    packet_common.add_missing_methods_to_thrift()
    parents = {
        11: [21]
    }
    expected_parents = (
        "+-----------+-----------+-----------+-------------+------------+----------+\n"
        "| Interface | Parent    | Parent    | Grandparent | Similarity | Flood    |\n"
        "| Name      | System ID | Interface | Count       | Group      | Repeater |\n"
        "|           |           | Name      |             |            |          |\n"
        "+-----------+-----------+-----------+-------------+------------+----------+\n"
        "| intf11    | 11        | intf1     | 1           | 1: 1-1     | True     |\n"
        "+-----------+-----------+-----------+-------------+------------+----------+\n")
    expected_grandparents = (
        "+-------------+--------+-------------+-------------+\n"
        "| Grandparent | Parent | Flood       | Redundantly |\n"
        "| System ID   | Count  | Repeater    | Covered     |\n"
        "|             |        | Adjacencies |             |\n"
        "+-------------+--------+-------------+-------------+\n"
        "| 21          | 1      | 1           | False       |\n"
        "+-------------+--------+-------------+-------------+\n")
    expected_intfs = (
        "+-----------+-----------+-----------+-----------+-----------+----------------+----------------+\n"
        "| Interface | Neighbor  | Neighbor  | Neighbor  | Neighbor  | Neighbor is    | This Node is   |\n"
        "| Name      | Interface | System ID | State     | Direction | Flood Repeater | Flood Repeater |\n"
        "|           | Name      |           |           |           | for This Node  | for Neighbor   |\n"
        "+-----------+-----------+-----------+-----------+-----------+----------------+----------------+\n"
        "| intf11    | intf1     | 11        | THREE_WAY | North     | True (Pending) | Not Applicable |\n"
        "+-----------+-----------+-----------+-----------+-----------+----------------+----------------+\n")
    check_flood_repeater_election(parents, expected_parents, expected_grandparents, expected_intfs)

def test_8x8_partial_connectivity_fully_redundant_coverage():
    # 8 parents (11, ..., 18)
    # 8 grandparents (21, ..., 28)
    # Partial connectivity between parents and grandparents:
    # Full redundant coverage of all grandparents is possible
    # Default shuffle similarity of 2
    packet_common.add_missing_methods_to_thrift()
    parents = {
        # pylint:disable=bad-whitespace
        11: [21, 22,     24, 25, 26        ],
        12: [            24, 25, 26, 27, 28],
        13: [21, 22,     24,     26, 27, 28],
        14: [21, 22, 23, 24, 25, 26, 27, 28],
        15: [    22,     24,     26,     28],
        16: [21,                         28],
        17: [21, 22, 23,     25, 26, 27, 28],
        18: [21, 22, 23, 24, 25,     27, 28]
    }
    expected_parents = (
        "+-----------+-----------+-----------+-------------+------------+----------+\n"
        "| Interface | Parent    | Parent    | Grandparent | Similarity | Flood    |\n"
        "| Name      | System ID | Interface | Count       | Group      | Repeater |\n"
        "|           |           | Name      |             |            |          |\n"
        "+-----------+-----------+-----------+-------------+------------+----------+\n"
        "| intf18    | 18        | intf1     | 7           | 1: 8-6     | True     |\n"
        "+-----------+-----------+-----------+-------------+------------+----------+\n"
        "| intf13    | 13        | intf1     | 6           | 1: 8-6     | True     |\n"
        "+-----------+-----------+-----------+-------------+------------+----------+\n"
        "| intf14    | 14        | intf1     | 8           | 1: 8-6     | True     |\n"
        "+-----------+-----------+-----------+-------------+------------+----------+\n"
        "| intf17    | 17        | intf1     | 7           | 1: 8-6     | False    |\n"
        "+-----------+-----------+-----------+-------------+------------+----------+\n"
        "| intf11    | 11        | intf1     | 5           | 2: 5-4     | False    |\n"
        "+-----------+-----------+-----------+-------------+------------+----------+\n"
        "| intf15    | 15        | intf1     | 4           | 2: 5-4     | False    |\n"
        "+-----------+-----------+-----------+-------------+------------+----------+\n"
        "| intf12    | 12        | intf1     | 5           | 2: 5-4     | False    |\n"
        "+-----------+-----------+-----------+-------------+------------+----------+\n"
        "| intf16    | 16        | intf1     | 2           | 3: 2-2     | False    |\n"
        "+-----------+-----------+-----------+-------------+------------+----------+\n")
    expected_grandparents = (
        "+-------------+--------+-------------+-------------+\n"
        "| Grandparent | Parent | Flood       | Redundantly |\n"
        "| System ID   | Count  | Repeater    | Covered     |\n"
        "|             |        | Adjacencies |             |\n"
        "+-------------+--------+-------------+-------------+\n"
        "| 21          | 6      | 3           | True        |\n"
        "+-------------+--------+-------------+-------------+\n"
        "| 22          | 6      | 3           | True        |\n"
        "+-------------+--------+-------------+-------------+\n"
        "| 23          | 3      | 2           | True        |\n"
        "+-------------+--------+-------------+-------------+\n"
        "| 24          | 6      | 3           | True        |\n"
        "+-------------+--------+-------------+-------------+\n"
        "| 25          | 5      | 2           | True        |\n"
        "+-------------+--------+-------------+-------------+\n"
        "| 26          | 6      | 2           | True        |\n"
        "+-------------+--------+-------------+-------------+\n"
        "| 27          | 5      | 3           | True        |\n"
        "+-------------+--------+-------------+-------------+\n"
        "| 28          | 7      | 3           | True        |\n"
        "+-------------+--------+-------------+-------------+\n")
    expected_intfs = (
        "+-----------+-----------+-----------+-----------+-----------+----------------+----------------+\n"
        "| Interface | Neighbor  | Neighbor  | Neighbor  | Neighbor  | Neighbor is    | This Node is   |\n"
        "| Name      | Interface | System ID | State     | Direction | Flood Repeater | Flood Repeater |\n"
        "|           | Name      |           |           |           | for This Node  | for Neighbor   |\n"
        "+-----------+-----------+-----------+-----------+-----------+----------------+----------------+\n"
        "| intf11    | intf1     | 11        | THREE_WAY | North     | False          | Not Applicable |\n"
        "+-----------+-----------+-----------+-----------+-----------+----------------+----------------+\n"
        "| intf12    | intf1     | 12        | THREE_WAY | North     | False          | Not Applicable |\n"
        "+-----------+-----------+-----------+-----------+-----------+----------------+----------------+\n"
        "| intf13    | intf1     | 13        | THREE_WAY | North     | True (Pending) | Not Applicable |\n"
        "+-----------+-----------+-----------+-----------+-----------+----------------+----------------+\n"
        "| intf14    | intf1     | 14        | THREE_WAY | North     | True (Pending) | Not Applicable |\n"
        "+-----------+-----------+-----------+-----------+-----------+----------------+----------------+\n"
        "| intf15    | intf1     | 15        | THREE_WAY | North     | False          | Not Applicable |\n"
        "+-----------+-----------+-----------+-----------+-----------+----------------+----------------+\n"
        "| intf16    | intf1     | 16        | THREE_WAY | North     | False          | Not Applicable |\n"
        "+-----------+-----------+-----------+-----------+-----------+----------------+----------------+\n"
        "| intf17    | intf1     | 17        | THREE_WAY | North     | False          | Not Applicable |\n"
        "+-----------+-----------+-----------+-----------+-----------+----------------+----------------+\n"
        "| intf18    | intf1     | 18        | THREE_WAY | North     | True (Pending) | Not Applicable |\n"
        "+-----------+-----------+-----------+-----------+-----------+----------------+----------------+\n")
    check_flood_repeater_election(parents, expected_parents, expected_grandparents, expected_intfs)

def test_8x8_partial_connectivity_partial_redundant_coverage():
    # 8 parents (11, ..., 18)
    # 8 grandparents (21, ..., 28)
    # Partial connectivity between parents and grandparents:
    # Some grandparents are fully covered, others not
    # Default shuffle similarity of 2
    packet_common.add_missing_methods_to_thrift()
    parents = {
        # pylint:disable=bad-whitespace
        11: [21,     23,         26,     28],
        12: [    22,     24,         27    ],
        13: [21                            ],
        14: [    22,                       ],
        15: [            24,         27    ],
        16: [        23,         26, 27    ],
        17: [    22,     24,     26        ],
        18: [21,         24, 25,     27    ]
    }
    expected_parents = (
        "+-----------+-----------+-----------+-------------+------------+----------+\n"
        "| Interface | Parent    | Parent    | Grandparent | Similarity | Flood    |\n"
        "| Name      | System ID | Interface | Count       | Group      | Repeater |\n"
        "|           |           | Name      |             |            |          |\n"
        "+-----------+-----------+-----------+-------------+------------+----------+\n"
        "| intf11    | 11        | intf1     | 4           | 1: 4-2     | True     |\n"
        "+-----------+-----------+-----------+-------------+------------+----------+\n"
        "| intf16    | 16        | intf1     | 3           | 1: 4-2     | True     |\n"
        "+-----------+-----------+-----------+-------------+------------+----------+\n"
        "| intf15    | 15        | intf1     | 2           | 1: 4-2     | True     |\n"
        "+-----------+-----------+-----------+-------------+------------+----------+\n"
        "| intf12    | 12        | intf1     | 3           | 1: 4-2     | True     |\n"
        "+-----------+-----------+-----------+-------------+------------+----------+\n"
        "| intf17    | 17        | intf1     | 3           | 1: 4-2     | True     |\n"
        "+-----------+-----------+-----------+-------------+------------+----------+\n"
        "| intf18    | 18        | intf1     | 4           | 1: 4-2     | True     |\n"
        "+-----------+-----------+-----------+-------------+------------+----------+\n"
        "| intf13    | 13        | intf1     | 1           | 2: 1-1     | False    |\n"
        "+-----------+-----------+-----------+-------------+------------+----------+\n"
        "| intf14    | 14        | intf1     | 1           | 2: 1-1     | False    |\n"
        "+-----------+-----------+-----------+-------------+------------+----------+\n")
    expected_grandparents = (
        "+-------------+--------+-------------+-------------+\n"
        "| Grandparent | Parent | Flood       | Redundantly |\n"
        "| System ID   | Count  | Repeater    | Covered     |\n"
        "|             |        | Adjacencies |             |\n"
        "+-------------+--------+-------------+-------------+\n"
        "| 21          | 3      | 2           | True        |\n"
        "+-------------+--------+-------------+-------------+\n"
        "| 22          | 3      | 2           | True        |\n"
        "+-------------+--------+-------------+-------------+\n"
        "| 23          | 2      | 2           | True        |\n"
        "+-------------+--------+-------------+-------------+\n"
        "| 24          | 4      | 4           | True        |\n"
        "+-------------+--------+-------------+-------------+\n"
        "| 25          | 1      | 1           | False       |\n"
        "+-------------+--------+-------------+-------------+\n"
        "| 26          | 3      | 3           | True        |\n"
        "+-------------+--------+-------------+-------------+\n"
        "| 27          | 4      | 4           | True        |\n"
        "+-------------+--------+-------------+-------------+\n"
        "| 28          | 1      | 1           | False       |\n"
        "+-------------+--------+-------------+-------------+\n")
    expected_intfs = (
        "+-----------+-----------+-----------+-----------+-----------+----------------+----------------+\n"
        "| Interface | Neighbor  | Neighbor  | Neighbor  | Neighbor  | Neighbor is    | This Node is   |\n"
        "| Name      | Interface | System ID | State     | Direction | Flood Repeater | Flood Repeater |\n"
        "|           | Name      |           |           |           | for This Node  | for Neighbor   |\n"
        "+-----------+-----------+-----------+-----------+-----------+----------------+----------------+\n"
        "| intf11    | intf1     | 11        | THREE_WAY | North     | True (Pending) | Not Applicable |\n"
        "+-----------+-----------+-----------+-----------+-----------+----------------+----------------+\n"
        "| intf12    | intf1     | 12        | THREE_WAY | North     | True (Pending) | Not Applicable |\n"
        "+-----------+-----------+-----------+-----------+-----------+----------------+----------------+\n"
        "| intf13    | intf1     | 13        | THREE_WAY | North     | False          | Not Applicable |\n"
        "+-----------+-----------+-----------+-----------+-----------+----------------+----------------+\n"
        "| intf14    | intf1     | 14        | THREE_WAY | North     | False          | Not Applicable |\n"
        "+-----------+-----------+-----------+-----------+-----------+----------------+----------------+\n"
        "| intf15    | intf1     | 15        | THREE_WAY | North     | True (Pending) | Not Applicable |\n"
        "+-----------+-----------+-----------+-----------+-----------+----------------+----------------+\n"
        "| intf16    | intf1     | 16        | THREE_WAY | North     | True (Pending) | Not Applicable |\n"
        "+-----------+-----------+-----------+-----------+-----------+----------------+----------------+\n"
        "| intf17    | intf1     | 17        | THREE_WAY | North     | True (Pending) | Not Applicable |\n"
        "+-----------+-----------+-----------+-----------+-----------+----------------+----------------+\n"
        "| intf18    | intf1     | 18        | THREE_WAY | North     | True (Pending) | Not Applicable |\n"
        "+-----------+-----------+-----------+-----------+-----------+----------------+----------------+\n")
    check_flood_repeater_election(parents, expected_parents, expected_grandparents, expected_intfs)

def test_8x8_full_connectivity_no_redundant_coverage():
    # 8 parents (11, ..., 18)
    # 8 grandparents (21, ..., 28)
    # Partial connectivity between parents and grandparents:
    # None of the grandparents are fully covered
    # Default shuffle similarity of 2
    packet_common.add_missing_methods_to_thrift()
    parents = {
        # pylint:disable=bad-whitespace
        11: [        23                    ],
        12: [                            28],
        13: [21                            ],
        14: [    22                        ],
        15: [            24                ],
        16: [                    26        ],
        17: [                        27    ],
        18: [                25            ]
    }
    expected_parents = (
        "+-----------+-----------+-----------+-------------+------------+----------+\n"
        "| Interface | Parent    | Parent    | Grandparent | Similarity | Flood    |\n"
        "| Name      | System ID | Interface | Count       | Group      | Repeater |\n"
        "|           |           | Name      |             |            |          |\n"
        "+-----------+-----------+-----------+-------------+------------+----------+\n"
        "| intf17    | 17        | intf1     | 1           | 1: 1-1     | True     |\n"
        "+-----------+-----------+-----------+-------------+------------+----------+\n"
        "| intf15    | 15        | intf1     | 1           | 1: 1-1     | True     |\n"
        "+-----------+-----------+-----------+-------------+------------+----------+\n"
        "| intf13    | 13        | intf1     | 1           | 1: 1-1     | True     |\n"
        "+-----------+-----------+-----------+-------------+------------+----------+\n"
        "| intf14    | 14        | intf1     | 1           | 1: 1-1     | True     |\n"
        "+-----------+-----------+-----------+-------------+------------+----------+\n"
        "| intf11    | 11        | intf1     | 1           | 1: 1-1     | True     |\n"
        "+-----------+-----------+-----------+-------------+------------+----------+\n"
        "| intf18    | 18        | intf1     | 1           | 1: 1-1     | True     |\n"
        "+-----------+-----------+-----------+-------------+------------+----------+\n"
        "| intf16    | 16        | intf1     | 1           | 1: 1-1     | True     |\n"
        "+-----------+-----------+-----------+-------------+------------+----------+\n"
        "| intf12    | 12        | intf1     | 1           | 1: 1-1     | True     |\n"
        "+-----------+-----------+-----------+-------------+------------+----------+\n")
    expected_grandparents = (
        "+-------------+--------+-------------+-------------+\n"
        "| Grandparent | Parent | Flood       | Redundantly |\n"
        "| System ID   | Count  | Repeater    | Covered     |\n"
        "|             |        | Adjacencies |             |\n"
        "+-------------+--------+-------------+-------------+\n"
        "| 21          | 1      | 1           | False       |\n"
        "+-------------+--------+-------------+-------------+\n"
        "| 22          | 1      | 1           | False       |\n"
        "+-------------+--------+-------------+-------------+\n"
        "| 23          | 1      | 1           | False       |\n"
        "+-------------+--------+-------------+-------------+\n"
        "| 24          | 1      | 1           | False       |\n"
        "+-------------+--------+-------------+-------------+\n"
        "| 25          | 1      | 1           | False       |\n"
        "+-------------+--------+-------------+-------------+\n"
        "| 26          | 1      | 1           | False       |\n"
        "+-------------+--------+-------------+-------------+\n"
        "| 27          | 1      | 1           | False       |\n"
        "+-------------+--------+-------------+-------------+\n"
        "| 28          | 1      | 1           | False       |\n"
        "+-------------+--------+-------------+-------------+\n")
    expected_intfs = (
        "+-----------+-----------+-----------+-----------+-----------+----------------+----------------+\n"
        "| Interface | Neighbor  | Neighbor  | Neighbor  | Neighbor  | Neighbor is    | This Node is   |\n"
        "| Name      | Interface | System ID | State     | Direction | Flood Repeater | Flood Repeater |\n"
        "|           | Name      |           |           |           | for This Node  | for Neighbor   |\n"
        "+-----------+-----------+-----------+-----------+-----------+----------------+----------------+\n"
        "| intf11    | intf1     | 11        | THREE_WAY | North     | True (Pending) | Not Applicable |\n"
        "+-----------+-----------+-----------+-----------+-----------+----------------+----------------+\n"
        "| intf12    | intf1     | 12        | THREE_WAY | North     | True (Pending) | Not Applicable |\n"
        "+-----------+-----------+-----------+-----------+-----------+----------------+----------------+\n"
        "| intf13    | intf1     | 13        | THREE_WAY | North     | True (Pending) | Not Applicable |\n"
        "+-----------+-----------+-----------+-----------+-----------+----------------+----------------+\n"
        "| intf14    | intf1     | 14        | THREE_WAY | North     | True (Pending) | Not Applicable |\n"
        "+-----------+-----------+-----------+-----------+-----------+----------------+----------------+\n"
        "| intf15    | intf1     | 15        | THREE_WAY | North     | True (Pending) | Not Applicable |\n"
        "+-----------+-----------+-----------+-----------+-----------+----------------+----------------+\n"
        "| intf16    | intf1     | 16        | THREE_WAY | North     | True (Pending) | Not Applicable |\n"
        "+-----------+-----------+-----------+-----------+-----------+----------------+----------------+\n"
        "| intf17    | intf1     | 17        | THREE_WAY | North     | True (Pending) | Not Applicable |\n"
        "+-----------+-----------+-----------+-----------+-----------+----------------+----------------+\n"
        "| intf18    | intf1     | 18        | THREE_WAY | North     | True (Pending) | Not Applicable |\n"
        "+-----------+-----------+-----------+-----------+-----------+----------------+----------------+\n")
    check_flood_repeater_election(parents, expected_parents, expected_grandparents, expected_intfs)


def test_graceful_switchover():
    #
    # Initial topology (same as test_8x8_partial_connectivity_partial_redundant_coverage)
    #
    packet_common.add_missing_methods_to_thrift()
    parents = {
        # pylint:disable=bad-whitespace
        11: [21,     23,         26,     28],
        12: [    22,     24,         27    ],
        13: [21                            ],
        14: [    22,                       ],
        15: [            24,         27    ],
        16: [        23,         26, 27    ],
        17: [    22,     24,     26        ],
        18: [21,         24, 25,     27    ]
    }
    expected_parents = (
        "+-----------+-----------+-----------+-------------+------------+----------+\n"
        "| Interface | Parent    | Parent    | Grandparent | Similarity | Flood    |\n"
        "| Name      | System ID | Interface | Count       | Group      | Repeater |\n"
        "|           |           | Name      |             |            |          |\n"
        "+-----------+-----------+-----------+-------------+------------+----------+\n"
        "| intf11    | 11        | intf1     | 4           | 1: 4-2     | True     |\n"
        "+-----------+-----------+-----------+-------------+------------+----------+\n"
        "| intf16    | 16        | intf1     | 3           | 1: 4-2     | True     |\n"
        "+-----------+-----------+-----------+-------------+------------+----------+\n"
        "| intf15    | 15        | intf1     | 2           | 1: 4-2     | True     |\n"
        "+-----------+-----------+-----------+-------------+------------+----------+\n"
        "| intf12    | 12        | intf1     | 3           | 1: 4-2     | True     |\n"
        "+-----------+-----------+-----------+-------------+------------+----------+\n"
        "| intf17    | 17        | intf1     | 3           | 1: 4-2     | True     |\n"
        "+-----------+-----------+-----------+-------------+------------+----------+\n"
        "| intf18    | 18        | intf1     | 4           | 1: 4-2     | True     |\n"
        "+-----------+-----------+-----------+-------------+------------+----------+\n"
        "| intf13    | 13        | intf1     | 1           | 2: 1-1     | False    |\n"
        "+-----------+-----------+-----------+-------------+------------+----------+\n"
        "| intf14    | 14        | intf1     | 1           | 2: 1-1     | False    |\n"
        "+-----------+-----------+-----------+-------------+------------+----------+\n")
    expected_grandparents = (
        "+-------------+--------+-------------+-------------+\n"
        "| Grandparent | Parent | Flood       | Redundantly |\n"
        "| System ID   | Count  | Repeater    | Covered     |\n"
        "|             |        | Adjacencies |             |\n"
        "+-------------+--------+-------------+-------------+\n"
        "| 21          | 3      | 2           | True        |\n"
        "+-------------+--------+-------------+-------------+\n"
        "| 22          | 3      | 2           | True        |\n"
        "+-------------+--------+-------------+-------------+\n"
        "| 23          | 2      | 2           | True        |\n"
        "+-------------+--------+-------------+-------------+\n"
        "| 24          | 4      | 4           | True        |\n"
        "+-------------+--------+-------------+-------------+\n"
        "| 25          | 1      | 1           | False       |\n"
        "+-------------+--------+-------------+-------------+\n"
        "| 26          | 3      | 3           | True        |\n"
        "+-------------+--------+-------------+-------------+\n"
        "| 27          | 4      | 4           | True        |\n"
        "+-------------+--------+-------------+-------------+\n"
        "| 28          | 1      | 1           | False       |\n"
        "+-------------+--------+-------------+-------------+\n")
    expected_intfs = (
        "+-----------+-----------+-----------+-----------+-----------+----------------+----------------+\n"
        "| Interface | Neighbor  | Neighbor  | Neighbor  | Neighbor  | Neighbor is    | This Node is   |\n"
        "| Name      | Interface | System ID | State     | Direction | Flood Repeater | Flood Repeater |\n"
        "|           | Name      |           |           |           | for This Node  | for Neighbor   |\n"
        "+-----------+-----------+-----------+-----------+-----------+----------------+----------------+\n"
        "| intf11    | intf1     | 11        | THREE_WAY | North     | True (Pending) | Not Applicable |\n"
        "+-----------+-----------+-----------+-----------+-----------+----------------+----------------+\n"
        "| intf12    | intf1     | 12        | THREE_WAY | North     | True (Pending) | Not Applicable |\n"
        "+-----------+-----------+-----------+-----------+-----------+----------------+----------------+\n"
        "| intf13    | intf1     | 13        | THREE_WAY | North     | False          | Not Applicable |\n"
        "+-----------+-----------+-----------+-----------+-----------+----------------+----------------+\n"
        "| intf14    | intf1     | 14        | THREE_WAY | North     | False          | Not Applicable |\n"
        "+-----------+-----------+-----------+-----------+-----------+----------------+----------------+\n"
        "| intf15    | intf1     | 15        | THREE_WAY | North     | True (Pending) | Not Applicable |\n"
        "+-----------+-----------+-----------+-----------+-----------+----------------+----------------+\n"
        "| intf16    | intf1     | 16        | THREE_WAY | North     | True (Pending) | Not Applicable |\n"
        "+-----------+-----------+-----------+-----------+-----------+----------------+----------------+\n"
        "| intf17    | intf1     | 17        | THREE_WAY | North     | True (Pending) | Not Applicable |\n"
        "+-----------+-----------+-----------+-----------+-----------+----------------+----------------+\n"
        "| intf18    | intf1     | 18        | THREE_WAY | North     | True (Pending) | Not Applicable |\n"
        "+-----------+-----------+-----------+-----------+-----------+----------------+----------------+\n")
    test_node = check_flood_repeater_election(parents, expected_parents, expected_grandparents,
                                              expected_intfs)
    #
    # LIEs with you-are-flood-repeater field set to true are sent over interfaces 11 and 12. They
    # should not be pending anymore, but the others still should be.
    #
    for intf_name in ["intf11", "intf15"]:
        intf = test_node.interfaces_by_name[intf_name]
        intf.floodred_mark_sent_you_are_fr()
    expected_intfs = (
        "+-----------+-----------+-----------+-----------+-----------+----------------+----------------+\n"
        "| Interface | Neighbor  | Neighbor  | Neighbor  | Neighbor  | Neighbor is    | This Node is   |\n"
        "| Name      | Interface | System ID | State     | Direction | Flood Repeater | Flood Repeater |\n"
        "|           | Name      |           |           |           | for This Node  | for Neighbor   |\n"
        "+-----------+-----------+-----------+-----------+-----------+----------------+----------------+\n"
        "| intf11    | intf1     | 11        | THREE_WAY | North     | True           | Not Applicable |\n"
        "+-----------+-----------+-----------+-----------+-----------+----------------+----------------+\n"
        "| intf12    | intf1     | 12        | THREE_WAY | North     | True (Pending) | Not Applicable |\n"
        "+-----------+-----------+-----------+-----------+-----------+----------------+----------------+\n"
        "| intf13    | intf1     | 13        | THREE_WAY | North     | False          | Not Applicable |\n"
        "+-----------+-----------+-----------+-----------+-----------+----------------+----------------+\n"
        "| intf14    | intf1     | 14        | THREE_WAY | North     | False          | Not Applicable |\n"
        "+-----------+-----------+-----------+-----------+-----------+----------------+----------------+\n"
        "| intf15    | intf1     | 15        | THREE_WAY | North     | True           | Not Applicable |\n"
        "+-----------+-----------+-----------+-----------+-----------+----------------+----------------+\n"
        "| intf16    | intf1     | 16        | THREE_WAY | North     | True (Pending) | Not Applicable |\n"
        "+-----------+-----------+-----------+-----------+-----------+----------------+----------------+\n"
        "| intf17    | intf1     | 17        | THREE_WAY | North     | True (Pending) | Not Applicable |\n"
        "+-----------+-----------+-----------+-----------+-----------+----------------+----------------+\n"
        "| intf18    | intf1     | 18        | THREE_WAY | North     | True (Pending) | Not Applicable |\n"
        "+-----------+-----------+-----------+-----------+-----------+----------------+----------------+\n")
    assert test_node.floodred_interfaces_table().to_string() == expected_intfs
    #
    # Run the flood repeater election algorithm again. Nothing should change.
    #
    test_node.floodred_elect_repeaters()
    assert test_node.floodred_parents_table().to_string() == expected_parents
    assert test_node.floodred_grandparents_table().to_string() == expected_grandparents
    assert test_node.floodred_interfaces_table().to_string() == expected_intfs
    #
    # LIEs with you-are-flood-repeater field set to true are sent all remaining pending interfaces.
    #
    for intf_name in ["intf12", "intf16", "intf17", "intf18"]:
        intf = test_node.interfaces_by_name[intf_name]
        intf.floodred_mark_sent_you_are_fr()
    expected_intfs = (
        "+-----------+-----------+-----------+-----------+-----------+----------------+----------------+\n"
        "| Interface | Neighbor  | Neighbor  | Neighbor  | Neighbor  | Neighbor is    | This Node is   |\n"
        "| Name      | Interface | System ID | State     | Direction | Flood Repeater | Flood Repeater |\n"
        "|           | Name      |           |           |           | for This Node  | for Neighbor   |\n"
        "+-----------+-----------+-----------+-----------+-----------+----------------+----------------+\n"
        "| intf11    | intf1     | 11        | THREE_WAY | North     | True           | Not Applicable |\n"
        "+-----------+-----------+-----------+-----------+-----------+----------------+----------------+\n"
        "| intf12    | intf1     | 12        | THREE_WAY | North     | True           | Not Applicable |\n"
        "+-----------+-----------+-----------+-----------+-----------+----------------+----------------+\n"
        "| intf13    | intf1     | 13        | THREE_WAY | North     | False          | Not Applicable |\n"
        "+-----------+-----------+-----------+-----------+-----------+----------------+----------------+\n"
        "| intf14    | intf1     | 14        | THREE_WAY | North     | False          | Not Applicable |\n"
        "+-----------+-----------+-----------+-----------+-----------+----------------+----------------+\n"
        "| intf15    | intf1     | 15        | THREE_WAY | North     | True           | Not Applicable |\n"
        "+-----------+-----------+-----------+-----------+-----------+----------------+----------------+\n"
        "| intf16    | intf1     | 16        | THREE_WAY | North     | True           | Not Applicable |\n"
        "+-----------+-----------+-----------+-----------+-----------+----------------+----------------+\n"
        "| intf17    | intf1     | 17        | THREE_WAY | North     | True           | Not Applicable |\n"
        "+-----------+-----------+-----------+-----------+-----------+----------------+----------------+\n"
        "| intf18    | intf1     | 18        | THREE_WAY | North     | True           | Not Applicable |\n"
        "+-----------+-----------+-----------+-----------+-----------+----------------+----------------+\n")
    assert test_node.floodred_interfaces_table().to_string() == expected_intfs
    #
    # Run the flood repeater election algorithm again. Nothing should change.
    #
    test_node.floodred_elect_repeaters()
    assert test_node.floodred_parents_table().to_string() == expected_parents
    assert test_node.floodred_grandparents_table().to_string() == expected_grandparents
    assert test_node.floodred_interfaces_table().to_string() == expected_intfs
    #
    # Create new links between parents and grandparents, and re-run flood repeater election
    # pylint:disable=bad-whitespace
    parents[11] = [21, 22, 23, 24,     26, 27, 28]
    parents[13] = [21, 22, 23,     25, 26,     28]
    parents[14] = [21, 22,     24, 25, 26,     28]
    update_test_node(test_node, parents)
    test_node.floodred_elect_repeaters()
    expected_parents = (
        "+-----------+-----------+-----------+-------------+------------+----------+\n"
        "| Interface | Parent    | Parent    | Grandparent | Similarity | Flood    |\n"
        "| Name      | System ID | Interface | Count       | Group      | Repeater |\n"
        "|           |           | Name      |             |            |          |\n"
        "+-----------+-----------+-----------+-------------+------------+----------+\n"
        "| intf14    | 14        | intf1     | 6           | 1: 7-6     | True     |\n"
        "+-----------+-----------+-----------+-------------+------------+----------+\n"
        "| intf13    | 13        | intf1     | 6           | 1: 7-6     | True     |\n"
        "+-----------+-----------+-----------+-------------+------------+----------+\n"
        "| intf11    | 11        | intf1     | 7           | 1: 7-6     | True     |\n"
        "+-----------+-----------+-----------+-------------+------------+----------+\n"
        "| intf17    | 17        | intf1     | 3           | 2: 4-2     | False    |\n"
        "+-----------+-----------+-----------+-------------+------------+----------+\n"
        "| intf12    | 12        | intf1     | 3           | 2: 4-2     | True     |\n"
        "+-----------+-----------+-----------+-------------+------------+----------+\n"
        "| intf18    | 18        | intf1     | 4           | 2: 4-2     | False    |\n"
        "+-----------+-----------+-----------+-------------+------------+----------+\n"
        "| intf15    | 15        | intf1     | 2           | 2: 4-2     | False    |\n"
        "+-----------+-----------+-----------+-------------+------------+----------+\n"
        "| intf16    | 16        | intf1     | 3           | 2: 4-2     | False    |\n"
        "+-----------+-----------+-----------+-------------+------------+----------+\n")
    assert test_node.floodred_parents_table().to_string() == expected_parents
    expected_grandparents = (
        "+-------------+--------+-------------+-------------+\n"
        "| Grandparent | Parent | Flood       | Redundantly |\n"
        "| System ID   | Count  | Repeater    | Covered     |\n"
        "|             |        | Adjacencies |             |\n"
        "+-------------+--------+-------------+-------------+\n"
        "| 21          | 4      | 3           | True        |\n"
        "+-------------+--------+-------------+-------------+\n"
        "| 22          | 5      | 4           | True        |\n"
        "+-------------+--------+-------------+-------------+\n"
        "| 23          | 3      | 2           | True        |\n"
        "+-------------+--------+-------------+-------------+\n"
        "| 24          | 6      | 3           | True        |\n"
        "+-------------+--------+-------------+-------------+\n"
        "| 25          | 3      | 2           | True        |\n"
        "+-------------+--------+-------------+-------------+\n"
        "| 26          | 5      | 3           | True        |\n"
        "+-------------+--------+-------------+-------------+\n"
        "| 27          | 5      | 2           | True        |\n"
        "+-------------+--------+-------------+-------------+\n"
        "| 28          | 3      | 3           | True        |\n"
        "+-------------+--------+-------------+-------------+\n")
    assert test_node.floodred_grandparents_table().to_string() == expected_grandparents
    expected_intfs = (
        "+-----------+-----------+-----------+-----------+-----------+-----------------+----------------+\n"
        "| Interface | Neighbor  | Neighbor  | Neighbor  | Neighbor  | Neighbor is     | This Node is   |\n"
        "| Name      | Interface | System ID | State     | Direction | Flood Repeater  | Flood Repeater |\n"
        "|           | Name      |           |           |           | for This Node   | for Neighbor   |\n"
        "+-----------+-----------+-----------+-----------+-----------+-----------------+----------------+\n"
        "| intf11    | intf1     | 11        | THREE_WAY | North     | True            | Not Applicable |\n"
        "+-----------+-----------+-----------+-----------+-----------+-----------------+----------------+\n"
        "| intf12    | intf1     | 12        | THREE_WAY | North     | True            | Not Applicable |\n"
        "+-----------+-----------+-----------+-----------+-----------+-----------------+----------------+\n"
        "| intf13    | intf1     | 13        | THREE_WAY | North     | True (Pending)  | Not Applicable |\n"
        "+-----------+-----------+-----------+-----------+-----------+-----------------+----------------+\n"
        "| intf14    | intf1     | 14        | THREE_WAY | North     | True (Pending)  | Not Applicable |\n"
        "+-----------+-----------+-----------+-----------+-----------+-----------------+----------------+\n"
        "| intf15    | intf1     | 15        | THREE_WAY | North     | False (Pending) | Not Applicable |\n"
        "+-----------+-----------+-----------+-----------+-----------+-----------------+----------------+\n"
        "| intf16    | intf1     | 16        | THREE_WAY | North     | False (Pending) | Not Applicable |\n"
        "+-----------+-----------+-----------+-----------+-----------+-----------------+----------------+\n"
        "| intf17    | intf1     | 17        | THREE_WAY | North     | False (Pending) | Not Applicable |\n"
        "+-----------+-----------+-----------+-----------+-----------+-----------------+----------------+\n"
        "| intf18    | intf1     | 18        | THREE_WAY | North     | False (Pending) | Not Applicable |\n"
        "+-----------+-----------+-----------+-----------+-----------+-----------------+----------------+\n")
    assert test_node.floodred_interfaces_table().to_string() == expected_intfs
    #
    # Two of the parents (13 and 14) have just been elected to become new flood repeaters, but they
    # are pending because we have not yet sent a LIE to them. Four of the parents (15, 16, 17, and
    # 17) are no long flood repeaters, but they are waiting for the new flood repeaters to be
    # informed before they step down.
    #
    # Send a LIE to parent 14. The old flood repeaters will still not yet step down, since 13 still
    # needs to be informed.
    #
    intf = test_node.interfaces_by_name["intf14"]
    intf.floodred_mark_sent_you_are_fr()
    expected_intfs = (
        "+-----------+-----------+-----------+-----------+-----------+-----------------+----------------+\n"
        "| Interface | Neighbor  | Neighbor  | Neighbor  | Neighbor  | Neighbor is     | This Node is   |\n"
        "| Name      | Interface | System ID | State     | Direction | Flood Repeater  | Flood Repeater |\n"
        "|           | Name      |           |           |           | for This Node   | for Neighbor   |\n"
        "+-----------+-----------+-----------+-----------+-----------+-----------------+----------------+\n"
        "| intf11    | intf1     | 11        | THREE_WAY | North     | True            | Not Applicable |\n"
        "+-----------+-----------+-----------+-----------+-----------+-----------------+----------------+\n"
        "| intf12    | intf1     | 12        | THREE_WAY | North     | True            | Not Applicable |\n"
        "+-----------+-----------+-----------+-----------+-----------+-----------------+----------------+\n"
        "| intf13    | intf1     | 13        | THREE_WAY | North     | True (Pending)  | Not Applicable |\n"
        "+-----------+-----------+-----------+-----------+-----------+-----------------+----------------+\n"
        "| intf14    | intf1     | 14        | THREE_WAY | North     | True            | Not Applicable |\n"
        "+-----------+-----------+-----------+-----------+-----------+-----------------+----------------+\n"
        "| intf15    | intf1     | 15        | THREE_WAY | North     | False (Pending) | Not Applicable |\n"
        "+-----------+-----------+-----------+-----------+-----------+-----------------+----------------+\n"
        "| intf16    | intf1     | 16        | THREE_WAY | North     | False (Pending) | Not Applicable |\n"
        "+-----------+-----------+-----------+-----------+-----------+-----------------+----------------+\n"
        "| intf17    | intf1     | 17        | THREE_WAY | North     | False (Pending) | Not Applicable |\n"
        "+-----------+-----------+-----------+-----------+-----------+-----------------+----------------+\n"
        "| intf18    | intf1     | 18        | THREE_WAY | North     | False (Pending) | Not Applicable |\n"
        "+-----------+-----------+-----------+-----------+-----------+-----------------+----------------+\n")
    assert test_node.floodred_interfaces_table().to_string() == expected_intfs
    #
    # Send a LIE to parent 13. The old flood repeaters will finally step down since all new flood
    # repeaters have been informed.
    #
    intf = test_node.interfaces_by_name["intf13"]
    intf.floodred_mark_sent_you_are_fr()
    expected_intfs = (
        "+-----------+-----------+-----------+-----------+-----------+----------------+----------------+\n"
        "| Interface | Neighbor  | Neighbor  | Neighbor  | Neighbor  | Neighbor is    | This Node is   |\n"
        "| Name      | Interface | System ID | State     | Direction | Flood Repeater | Flood Repeater |\n"
        "|           | Name      |           |           |           | for This Node  | for Neighbor   |\n"
        "+-----------+-----------+-----------+-----------+-----------+----------------+----------------+\n"
        "| intf11    | intf1     | 11        | THREE_WAY | North     | True           | Not Applicable |\n"
        "+-----------+-----------+-----------+-----------+-----------+----------------+----------------+\n"
        "| intf12    | intf1     | 12        | THREE_WAY | North     | True           | Not Applicable |\n"
        "+-----------+-----------+-----------+-----------+-----------+----------------+----------------+\n"
        "| intf13    | intf1     | 13        | THREE_WAY | North     | True           | Not Applicable |\n"
        "+-----------+-----------+-----------+-----------+-----------+----------------+----------------+\n"
        "| intf14    | intf1     | 14        | THREE_WAY | North     | True           | Not Applicable |\n"
        "+-----------+-----------+-----------+-----------+-----------+----------------+----------------+\n"
        "| intf15    | intf1     | 15        | THREE_WAY | North     | False          | Not Applicable |\n"
        "+-----------+-----------+-----------+-----------+-----------+----------------+----------------+\n"
        "| intf16    | intf1     | 16        | THREE_WAY | North     | False          | Not Applicable |\n"
        "+-----------+-----------+-----------+-----------+-----------+----------------+----------------+\n"
        "| intf17    | intf1     | 17        | THREE_WAY | North     | False          | Not Applicable |\n"
        "+-----------+-----------+-----------+-----------+-----------+----------------+----------------+\n"
        "| intf18    | intf1     | 18        | THREE_WAY | North     | False          | Not Applicable |\n"
        "+-----------+-----------+-----------+-----------+-----------+----------------+----------------+\n")
    assert test_node.floodred_interfaces_table().to_string() == expected_intfs


def test_similarity():
    packet_common.add_missing_methods_to_thrift()
    #
    # Default similarity is 2
    #
    parents = {}
    test_node = make_test_node(parents)
    expected_node_re = r"Flooding Reduction Similarity[| ]*2 "
    assert re.search(expected_node_re, test_node.cli_details_table().to_string())
    #
    # Configure similarity 1
    #
    additional_node_config = {"flooding_reduction_similarity": 1}
    test_node = make_test_node(parents, additional_node_config)
    expected_node_re = r"Flooding Reduction Similarity[| ]*1 "
    assert re.search(expected_node_re, test_node.cli_details_table().to_string())
    #
    # Topology (same as test_8x8_partial_connectivity_fully_redundant_coverage)
    #
    parents = {
        # pylint:disable=bad-whitespace
        11: [21, 22,     24, 25, 26        ],
        12: [            24, 25, 26, 27, 28],
        13: [21, 22,     24,     26, 27, 28],
        14: [21, 22, 23, 24, 25, 26, 27, 28],
        15: [    22,     24,     26,     28],
        16: [21,                         28],
        17: [21, 22, 23,     25, 26, 27, 28],
        18: [21, 22, 23, 24, 25,     27, 28]
    }
    expected_parents = (
        "+-----------+-----------+-----------+-------------+------------+----------+\n"
        "| Interface | Parent    | Parent    | Grandparent | Similarity | Flood    |\n"
        "| Name      | System ID | Interface | Count       | Group      | Repeater |\n"
        "|           |           | Name      |             |            |          |\n"
        "+-----------+-----------+-----------+-------------+------------+----------+\n"
        "| intf18    | 18        | intf1     | 7           | 1: 8-7     | True     |\n"
        "+-----------+-----------+-----------+-------------+------------+----------+\n"
        "| intf17    | 17        | intf1     | 7           | 1: 8-7     | True     |\n"
        "+-----------+-----------+-----------+-------------+------------+----------+\n"
        "| intf14    | 14        | intf1     | 8           | 1: 8-7     | True     |\n"
        "+-----------+-----------+-----------+-------------+------------+----------+\n"
        "| intf12    | 12        | intf1     | 5           | 2: 6-5     | False    |\n"
        "+-----------+-----------+-----------+-------------+------------+----------+\n"
        "| intf11    | 11        | intf1     | 5           | 2: 6-5     | False    |\n"
        "+-----------+-----------+-----------+-------------+------------+----------+\n"
        "| intf13    | 13        | intf1     | 6           | 2: 6-5     | False    |\n"
        "+-----------+-----------+-----------+-------------+------------+----------+\n"
        "| intf15    | 15        | intf1     | 4           | 3: 4-4     | False    |\n"
        "+-----------+-----------+-----------+-------------+------------+----------+\n"
        "| intf16    | 16        | intf1     | 2           | 4: 2-2     | False    |\n"
        "+-----------+-----------+-----------+-------------+------------+----------+\n")
    expected_grandparents = (
        "+-------------+--------+-------------+-------------+\n"
        "| Grandparent | Parent | Flood       | Redundantly |\n"
        "| System ID   | Count  | Repeater    | Covered     |\n"
        "|             |        | Adjacencies |             |\n"
        "+-------------+--------+-------------+-------------+\n"
        "| 21          | 6      | 3           | True        |\n"
        "+-------------+--------+-------------+-------------+\n"
        "| 22          | 6      | 3           | True        |\n"
        "+-------------+--------+-------------+-------------+\n"
        "| 23          | 3      | 3           | True        |\n"
        "+-------------+--------+-------------+-------------+\n"
        "| 24          | 6      | 2           | True        |\n"
        "+-------------+--------+-------------+-------------+\n"
        "| 25          | 5      | 3           | True        |\n"
        "+-------------+--------+-------------+-------------+\n"
        "| 26          | 6      | 2           | True        |\n"
        "+-------------+--------+-------------+-------------+\n"
        "| 27          | 5      | 3           | True        |\n"
        "+-------------+--------+-------------+-------------+\n"
        "| 28          | 7      | 3           | True        |\n"
        "+-------------+--------+-------------+-------------+\n")
    expected_intfs = (
        "+-----------+-----------+-----------+-----------+-----------+----------------+----------------+\n"
        "| Interface | Neighbor  | Neighbor  | Neighbor  | Neighbor  | Neighbor is    | This Node is   |\n"
        "| Name      | Interface | System ID | State     | Direction | Flood Repeater | Flood Repeater |\n"
        "|           | Name      |           |           |           | for This Node  | for Neighbor   |\n"
        "+-----------+-----------+-----------+-----------+-----------+----------------+----------------+\n"
        "| intf11    | intf1     | 11        | THREE_WAY | North     | False          | Not Applicable |\n"
        "+-----------+-----------+-----------+-----------+-----------+----------------+----------------+\n"
        "| intf12    | intf1     | 12        | THREE_WAY | North     | False          | Not Applicable |\n"
        "+-----------+-----------+-----------+-----------+-----------+----------------+----------------+\n"
        "| intf13    | intf1     | 13        | THREE_WAY | North     | False          | Not Applicable |\n"
        "+-----------+-----------+-----------+-----------+-----------+----------------+----------------+\n"
        "| intf14    | intf1     | 14        | THREE_WAY | North     | True (Pending) | Not Applicable |\n"
        "+-----------+-----------+-----------+-----------+-----------+----------------+----------------+\n"
        "| intf15    | intf1     | 15        | THREE_WAY | North     | False          | Not Applicable |\n"
        "+-----------+-----------+-----------+-----------+-----------+----------------+----------------+\n"
        "| intf16    | intf1     | 16        | THREE_WAY | North     | False          | Not Applicable |\n"
        "+-----------+-----------+-----------+-----------+-----------+----------------+----------------+\n"
        "| intf17    | intf1     | 17        | THREE_WAY | North     | True (Pending) | Not Applicable |\n"
        "+-----------+-----------+-----------+-----------+-----------+----------------+----------------+\n"
        "| intf18    | intf1     | 18        | THREE_WAY | North     | True (Pending) | Not Applicable |\n"
        "+-----------+-----------+-----------+-----------+-----------+----------------+----------------+\n")
    check_flood_repeater_election(parents, expected_parents, expected_grandparents, expected_intfs,
                                  additional_node_config)

def test_redundancy():
    packet_common.add_missing_methods_to_thrift()
    #
    # Default redundancy is 2
    #
    parents = {}
    test_node = make_test_node(parents)
    expected_node_re = r"Flooding Reduction Redundancy[| ]*2 "
    assert re.search(expected_node_re, test_node.cli_details_table().to_string())
    #
    # Configure redundancy 1
    #
    additional_node_config = {"flooding_reduction_redundancy": 1}
    test_node = make_test_node(parents, additional_node_config)
    expected_node_re = r"Flooding Reduction Redundancy[| ]*1 "
    assert re.search(expected_node_re, test_node.cli_details_table().to_string())
    #
    # Topology (same as test_8x8_partial_connectivity_fully_redundant_coverage)
    #
    parents = {
        # pylint:disable=bad-whitespace
        11: [21, 22,     24, 25, 26        ],
        12: [            24, 25, 26, 27, 28],
        13: [21, 22,     24,     26, 27, 28],
        14: [21, 22, 23, 24, 25, 26, 27, 28],
        15: [    22,     24,     26,     28],
        16: [21,                         28],
        17: [21, 22, 23,     25, 26, 27, 28],
        18: [21, 22, 23, 24, 25,     27, 28]
    }
    expected_parents = (
        "+-----------+-----------+-----------+-------------+------------+----------+\n"
        "| Interface | Parent    | Parent    | Grandparent | Similarity | Flood    |\n"
        "| Name      | System ID | Interface | Count       | Group      | Repeater |\n"
        "|           |           | Name      |             |            |          |\n"
        "+-----------+-----------+-----------+-------------+------------+----------+\n"
        "| intf18    | 18        | intf1     | 7           | 1: 8-6     | True     |\n"
        "+-----------+-----------+-----------+-------------+------------+----------+\n"
        "| intf13    | 13        | intf1     | 6           | 1: 8-6     | True     |\n"
        "+-----------+-----------+-----------+-------------+------------+----------+\n"
        "| intf14    | 14        | intf1     | 8           | 1: 8-6     | False    |\n"
        "+-----------+-----------+-----------+-------------+------------+----------+\n"
        "| intf17    | 17        | intf1     | 7           | 1: 8-6     | False    |\n"
        "+-----------+-----------+-----------+-------------+------------+----------+\n"
        "| intf11    | 11        | intf1     | 5           | 2: 5-4     | False    |\n"
        "+-----------+-----------+-----------+-------------+------------+----------+\n"
        "| intf15    | 15        | intf1     | 4           | 2: 5-4     | False    |\n"
        "+-----------+-----------+-----------+-------------+------------+----------+\n"
        "| intf12    | 12        | intf1     | 5           | 2: 5-4     | False    |\n"
        "+-----------+-----------+-----------+-------------+------------+----------+\n"
        "| intf16    | 16        | intf1     | 2           | 3: 2-2     | False    |\n"
        "+-----------+-----------+-----------+-------------+------------+----------+\n")
    expected_grandparents = (
        "+-------------+--------+-------------+-------------+\n"
        "| Grandparent | Parent | Flood       | Redundantly |\n"
        "| System ID   | Count  | Repeater    | Covered     |\n"
        "|             |        | Adjacencies |             |\n"
        "+-------------+--------+-------------+-------------+\n"
        "| 21          | 6      | 2           | True        |\n"
        "+-------------+--------+-------------+-------------+\n"
        "| 22          | 6      | 2           | True        |\n"
        "+-------------+--------+-------------+-------------+\n"
        "| 23          | 3      | 1           | True        |\n"
        "+-------------+--------+-------------+-------------+\n"
        "| 24          | 6      | 2           | True        |\n"
        "+-------------+--------+-------------+-------------+\n"
        "| 25          | 5      | 1           | True        |\n"
        "+-------------+--------+-------------+-------------+\n"
        "| 26          | 6      | 1           | True        |\n"
        "+-------------+--------+-------------+-------------+\n"
        "| 27          | 5      | 2           | True        |\n"
        "+-------------+--------+-------------+-------------+\n"
        "| 28          | 7      | 2           | True        |\n"
        "+-------------+--------+-------------+-------------+\n")
    expected_intfs = (
        "+-----------+-----------+-----------+-----------+-----------+----------------+----------------+\n"
        "| Interface | Neighbor  | Neighbor  | Neighbor  | Neighbor  | Neighbor is    | This Node is   |\n"
        "| Name      | Interface | System ID | State     | Direction | Flood Repeater | Flood Repeater |\n"
        "|           | Name      |           |           |           | for This Node  | for Neighbor   |\n"
        "+-----------+-----------+-----------+-----------+-----------+----------------+----------------+\n"
        "| intf11    | intf1     | 11        | THREE_WAY | North     | False          | Not Applicable |\n"
        "+-----------+-----------+-----------+-----------+-----------+----------------+----------------+\n"
        "| intf12    | intf1     | 12        | THREE_WAY | North     | False          | Not Applicable |\n"
        "+-----------+-----------+-----------+-----------+-----------+----------------+----------------+\n"
        "| intf13    | intf1     | 13        | THREE_WAY | North     | True (Pending) | Not Applicable |\n"
        "+-----------+-----------+-----------+-----------+-----------+----------------+----------------+\n"
        "| intf14    | intf1     | 14        | THREE_WAY | North     | False          | Not Applicable |\n"
        "+-----------+-----------+-----------+-----------+-----------+----------------+----------------+\n"
        "| intf15    | intf1     | 15        | THREE_WAY | North     | False          | Not Applicable |\n"
        "+-----------+-----------+-----------+-----------+-----------+----------------+----------------+\n"
        "| intf16    | intf1     | 16        | THREE_WAY | North     | False          | Not Applicable |\n"
        "+-----------+-----------+-----------+-----------+-----------+----------------+----------------+\n"
        "| intf17    | intf1     | 17        | THREE_WAY | North     | False          | Not Applicable |\n"
        "+-----------+-----------+-----------+-----------+-----------+----------------+----------------+\n"
        "| intf18    | intf1     | 18        | THREE_WAY | North     | True (Pending) | Not Applicable |\n"
        "+-----------+-----------+-----------+-----------+-----------+----------------+----------------+\n")
    check_flood_repeater_election(parents, expected_parents, expected_grandparents, expected_intfs,
                                  additional_node_config)
    #
    # Configure redundancy 6 (not all grandparents can be covered at this redundancy)
    #
    additional_node_config = {"flooding_reduction_redundancy": 6}
    test_node = make_test_node(parents, additional_node_config)
    expected_node_re = r"Flooding Reduction Redundancy[| ]*6 "
    assert re.search(expected_node_re, test_node.cli_details_table().to_string())
    expected_parents = (
        "+-----------+-----------+-----------+-------------+------------+----------+\n"
        "| Interface | Parent    | Parent    | Grandparent | Similarity | Flood    |\n"
        "| Name      | System ID | Interface | Count       | Group      | Repeater |\n"
        "|           |           | Name      |             |            |          |\n"
        "+-----------+-----------+-----------+-------------+------------+----------+\n"
        "| intf18    | 18        | intf1     | 7           | 1: 8-6     | True     |\n"
        "+-----------+-----------+-----------+-------------+------------+----------+\n"
        "| intf13    | 13        | intf1     | 6           | 1: 8-6     | True     |\n"
        "+-----------+-----------+-----------+-------------+------------+----------+\n"
        "| intf14    | 14        | intf1     | 8           | 1: 8-6     | True     |\n"
        "+-----------+-----------+-----------+-------------+------------+----------+\n"
        "| intf17    | 17        | intf1     | 7           | 1: 8-6     | True     |\n"
        "+-----------+-----------+-----------+-------------+------------+----------+\n"
        "| intf11    | 11        | intf1     | 5           | 2: 5-4     | True     |\n"
        "+-----------+-----------+-----------+-------------+------------+----------+\n"
        "| intf15    | 15        | intf1     | 4           | 2: 5-4     | True     |\n"
        "+-----------+-----------+-----------+-------------+------------+----------+\n"
        "| intf12    | 12        | intf1     | 5           | 2: 5-4     | True     |\n"
        "+-----------+-----------+-----------+-------------+------------+----------+\n"
        "| intf16    | 16        | intf1     | 2           | 3: 2-2     | True     |\n"
        "+-----------+-----------+-----------+-------------+------------+----------+\n")
    expected_grandparents = (
        "+-------------+--------+-------------+-------------+\n"
        "| Grandparent | Parent | Flood       | Redundantly |\n"
        "| System ID   | Count  | Repeater    | Covered     |\n"
        "|             |        | Adjacencies |             |\n"
        "+-------------+--------+-------------+-------------+\n"
        "| 21          | 6      | 6           | True        |\n"
        "+-------------+--------+-------------+-------------+\n"
        "| 22          | 6      | 6           | True        |\n"
        "+-------------+--------+-------------+-------------+\n"
        "| 23          | 3      | 3           | False       |\n"
        "+-------------+--------+-------------+-------------+\n"
        "| 24          | 6      | 6           | True        |\n"
        "+-------------+--------+-------------+-------------+\n"
        "| 25          | 5      | 5           | False       |\n"
        "+-------------+--------+-------------+-------------+\n"
        "| 26          | 6      | 6           | True        |\n"
        "+-------------+--------+-------------+-------------+\n"
        "| 27          | 5      | 5           | False       |\n"
        "+-------------+--------+-------------+-------------+\n"
        "| 28          | 7      | 7           | True        |\n"
        "+-------------+--------+-------------+-------------+\n")
    expected_intfs = (
        "+-----------+-----------+-----------+-----------+-----------+----------------+----------------+\n"
        "| Interface | Neighbor  | Neighbor  | Neighbor  | Neighbor  | Neighbor is    | This Node is   |\n"
        "| Name      | Interface | System ID | State     | Direction | Flood Repeater | Flood Repeater |\n"
        "|           | Name      |           |           |           | for This Node  | for Neighbor   |\n"
        "+-----------+-----------+-----------+-----------+-----------+----------------+----------------+\n"
        "| intf11    | intf1     | 11        | THREE_WAY | North     | True (Pending) | Not Applicable |\n"
        "+-----------+-----------+-----------+-----------+-----------+----------------+----------------+\n"
        "| intf12    | intf1     | 12        | THREE_WAY | North     | True (Pending) | Not Applicable |\n"
        "+-----------+-----------+-----------+-----------+-----------+----------------+----------------+\n"
        "| intf13    | intf1     | 13        | THREE_WAY | North     | True (Pending) | Not Applicable |\n"
        "+-----------+-----------+-----------+-----------+-----------+----------------+----------------+\n"
        "| intf14    | intf1     | 14        | THREE_WAY | North     | True (Pending) | Not Applicable |\n"
        "+-----------+-----------+-----------+-----------+-----------+----------------+----------------+\n"
        "| intf15    | intf1     | 15        | THREE_WAY | North     | True (Pending) | Not Applicable |\n"
        "+-----------+-----------+-----------+-----------+-----------+----------------+----------------+\n"
        "| intf16    | intf1     | 16        | THREE_WAY | North     | True (Pending) | Not Applicable |\n"
        "+-----------+-----------+-----------+-----------+-----------+----------------+----------------+\n"
        "| intf17    | intf1     | 17        | THREE_WAY | North     | True (Pending) | Not Applicable |\n"
        "+-----------+-----------+-----------+-----------+-----------+----------------+----------------+\n"
        "| intf18    | intf1     | 18        | THREE_WAY | North     | True (Pending) | Not Applicable |\n"
        "+-----------+-----------+-----------+-----------+-----------+----------------+----------------+\n")
    check_flood_repeater_election(parents, expected_parents, expected_grandparents, expected_intfs,
                                  additional_node_config)

def test_disable():
    packet_common.add_missing_methods_to_thrift()
    #
    # Flooding reduction is enabled by default
    #
    parents = {}
    test_node = make_test_node(parents)
    expected_node_re = r"Flooding Reduction Enabled[| ]*True "
    assert re.search(expected_node_re, test_node.cli_details_table().to_string())
    #
    # Disable flooding reduction
    #
    additional_node_config = {"flooding_reduction": False}
    test_node = make_test_node(parents, additional_node_config)
    expected_node_re = r"Flooding Reduction Enabled[| ]*False "
    assert re.search(expected_node_re, test_node.cli_details_table().to_string())
    #
    # Topology (same as test_8x8_partial_connectivity_fully_redundant_coverage)
    #
    parents = {
        # pylint:disable=bad-whitespace
        11: [21, 22,     24, 25, 26        ],
        12: [            24, 25, 26, 27, 28],
        13: [21, 22,     24,     26, 27, 28],
        14: [21, 22, 23, 24, 25, 26, 27, 28],
        15: [    22,     24,     26,     28],
        16: [21,                         28],
        17: [21, 22, 23,     25, 26, 27, 28],
        18: [21, 22, 23, 24, 25,     27, 28]
    }
    expected_parents = None
    expected_grandparents = None
    expected_intfs = (
        "+-----------+-----------+-----------+-----------+-----------+----------------+----------------+\n"
        "| Interface | Neighbor  | Neighbor  | Neighbor  | Neighbor  | Neighbor is    | This Node is   |\n"
        "| Name      | Interface | System ID | State     | Direction | Flood Repeater | Flood Repeater |\n"
        "|           | Name      |           |           |           | for This Node  | for Neighbor   |\n"
        "+-----------+-----------+-----------+-----------+-----------+----------------+----------------+\n"
        "| intf11    | intf1     | 11        | THREE_WAY | North     | True           | Not Applicable |\n"
        "+-----------+-----------+-----------+-----------+-----------+----------------+----------------+\n"
        "| intf12    | intf1     | 12        | THREE_WAY | North     | True           | Not Applicable |\n"
        "+-----------+-----------+-----------+-----------+-----------+----------------+----------------+\n"
        "| intf13    | intf1     | 13        | THREE_WAY | North     | True           | Not Applicable |\n"
        "+-----------+-----------+-----------+-----------+-----------+----------------+----------------+\n"
        "| intf14    | intf1     | 14        | THREE_WAY | North     | True           | Not Applicable |\n"
        "+-----------+-----------+-----------+-----------+-----------+----------------+----------------+\n"
        "| intf15    | intf1     | 15        | THREE_WAY | North     | True           | Not Applicable |\n"
        "+-----------+-----------+-----------+-----------+-----------+----------------+----------------+\n"
        "| intf16    | intf1     | 16        | THREE_WAY | North     | True           | Not Applicable |\n"
        "+-----------+-----------+-----------+-----------+-----------+----------------+----------------+\n"
        "| intf17    | intf1     | 17        | THREE_WAY | North     | True           | Not Applicable |\n"
        "+-----------+-----------+-----------+-----------+-----------+----------------+----------------+\n"
        "| intf18    | intf1     | 18        | THREE_WAY | North     | True           | Not Applicable |\n"
        "+-----------+-----------+-----------+-----------+-----------+----------------+----------------+\n")
    check_flood_repeater_election(parents, expected_parents, expected_grandparents, expected_intfs,
                                  additional_node_config)
