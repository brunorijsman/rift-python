import ipaddress

import common.ttypes
import encoding.ttypes
import packet_common
import tie_db

SOUTH = common.ttypes.TieDirectionType.South
NORTH = common.ttypes.TieDirectionType.North

def make_tie_id(direction, originator, tie_nr):
    # TODO: Add support for TIE types other than prefix
    tie_id = encoding.ttypes.TIEID(
        direction=direction,
        originator=originator,
        tietype=common.ttypes.TIETypeType.PrefixTIEType,
        tie_nr=tie_nr)
    return tie_id

def make_tie_header(direction, originator, tie_nr, seq_nr):
    # TODO: Add support for TIE types other than prefix
    # TODO: Add support for remaining_lifetime
    # TODO: Add support for origination_time
    tie_id = make_tie_id(direction, originator, tie_nr)
    tie_header = encoding.ttypes.TIEHeader(
        tieid=tie_id,
        seq_nr=seq_nr,
        remaining_lifetime=None,
        origination_time=None)
    return tie_header

def make_prefix_tie(sender, level, direction, originator, tie_nr, seq_nr):
    tie_header = make_tie_header(direction, originator, tie_nr, seq_nr)
    prefixes = {}
    prefix_tie_element = encoding.ttypes.PrefixTIEElement(prefixes=prefixes)
    tie_element = encoding.ttypes.TIEElement(prefixes=prefix_tie_element)
    tie_packet = encoding.ttypes.TIEPacket(header=tie_header, element=tie_element)
    packet_header = encoding.ttypes.PacketHeader(sender=sender, level=level)
    packet_content = encoding.ttypes.PacketContent(tie=tie_packet)
    protocol_packet = encoding.ttypes.ProtocolPacket(header=packet_header, content=packet_content)
    return protocol_packet

def add_ipv4_prefix_to_tie(protocol_packet, ipv4_prefix_str, metric, tags=None,
                           monotonic_clock=None):
    ipv4_network = ipaddress.IPv4Network(ipv4_prefix_str)
    address = ipv4_network.network_address.packed
    prefixlen = ipv4_network.prefixlen
    ipv4_prefix = common.ttypes.IPv4PrefixType(address, prefixlen)
    prefix = common.ttypes.IPPrefixType(ipv4prefix=ipv4_prefix)
    attributes = encoding.ttypes.PrefixAttributes(metric=metric,
                                                  tags=tags,
                                                  monotonic_clock=monotonic_clock)
    protocol_packet.content.tie.element.prefixes.prefixes[prefix] = attributes

def add_ipv6_prefix_to_tie(protocol_packet, ipv6_prefix_str, metric, tags=None,
                           monotonic_clock=None):
    ipv6_network = ipaddress.IPv6Network(ipv6_prefix_str)
    address = ipv6_network.network_address.packed
    prefixlen = ipv6_network.prefixlen
    ipv6_prefix = common.ttypes.IPv6PrefixType(address, prefixlen)
    prefix = common.ttypes.IPPrefixType(ipv6prefix=ipv6_prefix)
    attributes = encoding.ttypes.PrefixAttributes(metric=metric,
                                                  tags=tags,
                                                  monotonic_clock=monotonic_clock)
    protocol_packet.content.tie.element.prefixes.prefixes[prefix] = attributes

def make_tide(sender, level, start_range, end_range):
    tide_packet = encoding.ttypes.TIDEPacket(start_range=start_range,
                                             end_range=end_range,
                                             headers=[])
    packet_header = encoding.ttypes.PacketHeader(sender=sender, level=level)
    packet_content = encoding.ttypes.PacketContent(tide=tide_packet)
    protocol_packet = encoding.ttypes.ProtocolPacket(header=packet_header, content=packet_content)
    return protocol_packet

def add_tie_header_to_tide(protocol_packet, direction, originator, tie_nr, seq_nr):
    tie_header = make_tie_header(direction, originator, tie_nr, seq_nr)
    protocol_packet.content.tide.headers.append(tie_header)

def test_add_prefix_tie():
    packet_common.add_missing_methods_to_thrift()
    tdb = tie_db.TIE_DB()
    prefix_tie_1 = make_prefix_tie(sender=111,
                                   level=2,
                                   direction=common.ttypes.TieDirectionType.South,
                                   originator=222,
                                   tie_nr=333,
                                   seq_nr=444)
    add_ipv4_prefix_to_tie(prefix_tie_1, "1.2.3.0/24", 2, [77, 88], 12345)
    add_ipv6_prefix_to_tie(prefix_tie_1, "1234:abcd::/64", 3)
    tdb.store_tie(prefix_tie_1)
    prefix_tie_2 = make_prefix_tie(sender=555,
                                   level=6,
                                   direction=common.ttypes.TieDirectionType.North,
                                   originator=777,
                                   tie_nr=888,
                                   seq_nr=999)
    add_ipv4_prefix_to_tie(prefix_tie_2, "0.0.0.0/0", 10)
    tdb.store_tie(prefix_tie_2)
    assert tdb.find_tie(prefix_tie_1.content.tie.header.tieid) == prefix_tie_1
    assert tdb.find_tie(prefix_tie_2.content.tie.header.tieid) == prefix_tie_2
    missing_tie_id = encoding.ttypes.TIEID(
        direction=common.ttypes.TieDirectionType.South,
        originator=321,
        tietype=common.ttypes.TIETypeType.PrefixTIEType,
        tie_nr=654)
    assert tdb.find_tie(missing_tie_id) is None
    tab = tdb.tie_db_table()
    tab_str = tab.to_string()
    assert (tab_str ==
            "+-----------+------------+--------+--------+--------+--------------------------+\n"
            "| Direction | Originator | Type   | TIE Nr | Seq Nr | Contents                 |\n"
            "+-----------+------------+--------+--------+--------+--------------------------+\n"
            "| South     | 222        | Prefix | 333    | 444    | Prefix: 1.2.3.0/24       |\n"
            "|           |            |        |        |        |   Metric: 2              |\n"
            "|           |            |        |        |        |   Tag: 77                |\n"
            "|           |            |        |        |        |   Tag: 88                |\n"
            "|           |            |        |        |        |   Monotonic-clock: 12345 |\n"
            "|           |            |        |        |        | Prefix: 1234:abcd::/64   |\n"
            "|           |            |        |        |        |   Metric: 3              |\n"
            "+-----------+------------+--------+--------+--------+--------------------------+\n"
            "| North     | 777        | Prefix | 888    | 999    | Prefix: 0.0.0.0/0        |\n"
            "|           |            |        |        |        |   Metric: 10             |\n"
            "+-----------+------------+--------+--------+--------+--------------------------+\n")


def check_process_tide_1(tdb):
    # pylint:disable=too-many-locals
    start_range = make_tie_id(direction=SOUTH, originator=10, tie_nr=1)
    end_range = make_tie_id(direction=NORTH, originator=8, tie_nr=999)
    tide_1 = make_tide(sender=999, level=999, start_range=start_range, end_range=end_range)
    tide_header_info_list = [
        # pylint:disable=bad-whitespace
        # Direction  Originator  Tie-Nr  Seq-Nr  Disposition
        ( SOUTH,     10,         10,     10),    # Same version as in TIE-DB; stop sending
        ( SOUTH,     10,         11,     1),     # Not in TIE-DB; request it
        ( SOUTH,     10,         13,     5),     # Newer version than in TIE-DB; request it
        ( NORTH,     3,          15,     5)]     # Older version than in TIE-DB; start sending
    for tide_header_info in tide_header_info_list:
        add_tie_header_to_tide(tide_1, *tide_header_info)
    # Process the first TIDE packet
    result = tdb.process_received_tide_packet(tide_1)
    (request_tie_ids, start_sending_tie_ids, stop_sending_tie_ids) = result
    # Check request_tie_id
    expected_request_tie_ids = []
    tie_id_info_list = [
        # pylint:disable=bad-whitespace
        # Direction  Originator  Tie-Nr
        ( SOUTH,     10,         11),
        ( SOUTH,     10,         13)]
    for tie_id_info in tie_id_info_list:
        expected_request_tie_ids.append(make_tie_id(*tie_id_info))
    assert request_tie_ids == expected_request_tie_ids
    # Check start_sending_tie_ids
    expected_start_sending_tie_ids = []
    tie_id_info_list = [
        # pylint:disable=bad-whitespace
        # Direction  Originator  Tie-Nr
        ( SOUTH,     8,          1),
        ( SOUTH,     10,         1),
        ( SOUTH,     10,         2),
        ( SOUTH,     10,         12),
        ( NORTH,     3,          15),
        ( NORTH,     4,          1)]
    for tie_id_info in tie_id_info_list:
        expected_start_sending_tie_ids.append(make_tie_id(*tie_id_info))
    assert start_sending_tie_ids == expected_start_sending_tie_ids
    # Check stop_sending_tie_ids
    expected_stop_sending_tie_ids = []
    tie_id_info_list = [
        # pylint:disable=bad-whitespace
        # Direction  Originator  Tie-Nr
        ( SOUTH,     10,         10)]
    for tie_id_info in tie_id_info_list:
        expected_stop_sending_tie_ids.append(make_tie_id(*tie_id_info))
    assert stop_sending_tie_ids == expected_stop_sending_tie_ids

def check_process_tide_2(tdb):
    # pylint:disable=too-many-locals
    # There is a gap in the end_range of TIDE-1 (North 8 Prefix 999) and the start_range of this
    # TIDE-2 (North 20 Prefix  1)
    start_range = make_tie_id(direction=NORTH, originator=20, tie_nr=1)
    end_range = make_tie_id(direction=NORTH, originator=100, tie_nr=1)
    tide_2 = make_tide(sender=666, level=0, start_range=start_range, end_range=end_range)
    tide_header_info_list = [
        # pylint:disable=bad-whitespace
        # Direction  Originator  Tie-Nr  Seq-Nr  Disposition
        ( NORTH,     21,         15,     5)]     # Newer version than in TIE-DB; request it
    for tide_header_info in tide_header_info_list:
        add_tie_header_to_tide(tide_2, *tide_header_info)
    # Process the second TIDE packet
    result = tdb.process_received_tide_packet(tide_2)
    (request_tie_ids, start_sending_tie_ids, stop_sending_tie_ids) = result
    # Check request_tie_id
    expected_request_tie_ids = []
    tie_id_info_list = [
        # pylint:disable=bad-whitespace
        # Direction  Originator  Tie-Nr
        ( NORTH,     21,         15)]
    for tie_id_info in tie_id_info_list:
        expected_request_tie_ids.append(make_tie_id(*tie_id_info))
    assert request_tie_ids == expected_request_tie_ids
    # Check start_sending_tie_ids
    expected_start_sending_tie_ids = []
    tie_id_info_list = [
        # pylint:disable=bad-whitespace
        # Direction  Originator  Tie-Nr
        ( NORTH,     10,         7)]
    for tie_id_info in tie_id_info_list:
        expected_start_sending_tie_ids.append(make_tie_id(*tie_id_info))
    assert start_sending_tie_ids == expected_start_sending_tie_ids
    # Check stop_sending_tie_ids
    expected_stop_sending_tie_ids = []
    assert stop_sending_tie_ids == expected_stop_sending_tie_ids

def check_process_tide_3(tdb):
    # pylint:disable=too-many-locals
    # There is a gap in the end_range of TIDE-2 (North 100 Prefix 1) and the start_range of this
    # TIDE-3 (North 200 Prefix  1)
    start_range = make_tie_id(direction=NORTH, originator=200, tie_nr=1)
    end_range = make_tie_id(direction=NORTH, originator=300, tie_nr=1)
    tide_2 = make_tide(sender=666, level=0, start_range=start_range, end_range=end_range)
    # Process the second TIDE packet
    result = tdb.process_received_tide_packet(tide_2)
    (request_tie_ids, start_sending_tie_ids, stop_sending_tie_ids) = result
    # Check request_tie_id
    expected_request_tie_ids = []
    assert request_tie_ids == expected_request_tie_ids
    # Check start_sending_tie_ids
    expected_start_sending_tie_ids = []
    tie_id_info_list = [
        # pylint:disable=bad-whitespace
        # Direction  Originator  Tie-Nr
        ( NORTH,     110,        40),
        ( NORTH,     210,        6)]
    for tie_id_info in tie_id_info_list:
        expected_start_sending_tie_ids.append(make_tie_id(*tie_id_info))
    assert start_sending_tie_ids == expected_start_sending_tie_ids
    # Check stop_sending_tie_ids
    expected_stop_sending_tie_ids = []
    assert stop_sending_tie_ids == expected_stop_sending_tie_ids

def test_process_tide():
    # pylint:disable=too-many-locals
    packet_common.add_missing_methods_to_thrift()
    tdb = tie_db.TIE_DB()
    db_tie_info_list = [
        # pylint:disable=bad-whitespace
        # Sender Level Direction Origin TieNr SeqNr Disposition
        ( 999,   999,  SOUTH,    8,     1,    1),   # In gap before TIDE-1; start sending
        ( 999,   999,  SOUTH,    10,    1,    2),   # Not in TIDE-1 (start gap); start sending
        ( 999,   999,  SOUTH,    10,    2,    5),   # Not in TIDE-1 (start gap); start sending
        ( 777,   7,    SOUTH,    10,    10,   10),  # Same version as in TIDE; stop sending
        ( 999,   999,  SOUTH,    10,    12,   5),   # Not in TIDE-1 (middle gap); start sending
        ( 999,   999,  SOUTH,    10,    13,   3),   # Older version than in TIDE-1; request it
        ( 999,   999,  NORTH,    3,     15,   7),   # Newer version than in TIDE-1; start sending
        ( 999,   999,  NORTH,    4,     1,    1),   # Not in TIDE-1 (end gap); start sending
        ( 999,   999,  NORTH,    10,    7,    6),   # In TIDE-1...TIDE-2 gap; start sending
        ( 999,   999,  NORTH,    21,    15,   3),   # Older version than in TIDE-2; request it
        ( 999,   999,  NORTH,    110,   40,   1),   # In TIDE-2...TIDE-3 gap; start sending
        ( 999,   999,  NORTH,    210,   6,    6)]   # Not in TIDE-3 (empty); start sending
    for db_tie_info in db_tie_info_list:
        db_tie = make_prefix_tie(*db_tie_info)
        tdb.store_tie(db_tie)
    check_process_tide_1(tdb)
    check_process_tide_2(tdb)
    check_process_tide_3(tdb)
    #
    # ISSUE: If you un-comment the next line, the test will fail. This is because the last received
    # TIDE is TIDE-3 and the newly received TIDE is TIDE-1. Because TIDE-1 < TIDE-3, the code for
    # processing the gap before TIDE-1 will *not* kick in. We could add code to detect the
    # wrap-around and fix this. However, this is also problematic. For example, if we do that and
    # RIFT receives TIDE-2 before TIDE-1 (e.g. due to a UDP drop or during startup), then this RIFT
    # will start sending all the TIEs which are reported in TIE-1.
    #
    # I suggested to Tony and alternative approach that requires that the ranges in the TIES must
    # be contiguous and collectively (union across all TIEs) must cover the entire TIE-ID space.
    # If we do that, then there would be no need to look for gaps between the TIDEs.
    #
    # An alternative approach would be to only start looking for gaps between the TIDEs when each
    # TIDE has been received at least once. However, it would be a challenge to detect that and
    # it would probably slow convergence down.
    #
    # check_process_tide_1(tdb)  # Wrap-around

def test_direction_str():
    tdb = tie_db.TIE_DB()
    assert tdb.direction_str(common.ttypes.TieDirectionType.South) == "South"
    assert tdb.direction_str(common.ttypes.TieDirectionType.North) == "North"
    assert tdb.direction_str(999) == "999"

def test_tietype_str():
    tdb = tie_db.TIE_DB()
    assert tdb.tietype_str(common.ttypes.TIETypeType.NodeTIEType) == "Node"
    assert tdb.tietype_str(common.ttypes.TIETypeType.PrefixTIEType) == "Prefix"
    assert tdb.tietype_str(common.ttypes.TIETypeType.TransitivePrefixTIEType) == "TransitivePrefix"
    assert tdb.tietype_str(common.ttypes.TIETypeType.PGPrefixTIEType) == "PolicyGuidedPrefix"
    assert tdb.tietype_str(common.ttypes.TIETypeType.KeyValueTIEType) == "KeyValue"
    assert tdb.tietype_str(888) == "888"
