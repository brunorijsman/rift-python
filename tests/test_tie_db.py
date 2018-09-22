import ipaddress

import common.ttypes
import encoding.ttypes
import packet_common
import tie_db

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

def test_process_tide():
    # pylint:disable=too-many-locals
    #
    # Contents of TIE database when TIDE is processed:
    #
    #   Direction  Originator  Type    TIE Nr  Seq Nr  Disposition
    #   ---------  ----------  ------  ------  ------  --------------------------------------------
    #   South      10          Prefix  10      10      Same version as in TIDE; stop sending
    #   South      10          Prefix  13      3       Older version than in TIDE; request it
    #   South      10          Prefix  15      7       Newer version than in TIDE; start sending
    #
    packet_common.add_missing_methods_to_thrift()
    tdb = tie_db.TIE_DB()
    south = common.ttypes.TieDirectionType.South
    north = common.ttypes.TieDirectionType.North
    db_tie_info_list = [
        # pylint:disable=bad-whitespace
        # Sender  Level  Direction  Originator  Tie-Nr  Seq-Nr
        ( 999,    999,   south,     10,         10,     10),
        ( 999,    999,   south,     10,         13,     3),
        ( 999,    999,   south,     10,         15,     7)]
    for db_tie_info in db_tie_info_list:
        db_tie = make_prefix_tie(*db_tie_info)
        tdb.store_tie(db_tie)
    #
    # Contents of TIDE packet:
    #
    #                 Direction  Originator  Type    TIE Nr
    #                 ---------  ----------  ------  ------
    #   Range start : South      10          Prefix  10
    #   Range end   : North      999         Prefix  999
    #
    #   Direction  Originator  Type    TIE Nr  Seq Nr  Disposition
    #   ---------  ----------  ------  ------  ------  --------------------------------------------
    #   South      10          Prefix  10      10      Same version as in TIE-DB; stop sending
    #   South      10          Prefix  11      1       Not in TIE-DB; request it
    #   South      10          Prefix  13      5       Newer version than in TIE-DB; request it
    #   South      10          Prefix  15      5       Older version than in TIE-DB; start sending
    #
    start_range = make_tie_id(direction=south, originator=10, tie_nr=10)
    end_range = make_tie_id(direction=north, originator=999, tie_nr=999)
    tide = make_tide(sender=999, level=999, start_range=start_range, end_range=end_range)
    tide_header_info_list = [
        # pylint:disable=bad-whitespace
        # Direction  Originator  Tie-Nr  Seq-Nr
        ( south,     10,         10,     10),
        ( south,     10,         11,     1),
        ( south,     10,         13,     5),
        ( south,     10,         15,     5)]
    for tide_header_info in tide_header_info_list:
        add_tie_header_to_tide(tide, *tide_header_info)
    #
    # Process the TIDE packet
    #
    result = tdb.process_received_tide_packet(tide)
    (request_tie_ids, start_sending_tie_ids, stop_sending_tie_ids) = result
    #
    # Check request_tie_id
    #
    expected_request_tie_ids = []
    tie_id_info_list = [
        # pylint:disable=bad-whitespace
        # Direction  Originator  Tie-Nr
        ( south,     10,         11),
        ( south,     10,         13)]
    for tie_id_info in tie_id_info_list:
        expected_request_tie_ids.append(make_tie_id(*tie_id_info))
    assert request_tie_ids == expected_request_tie_ids
    #
    # Check start_sending_tie_ids
    #
    expected_start_sending_tie_ids = []
    tie_id_info_list = [
        # pylint:disable=bad-whitespace
        # Direction  Originator  Tie-Nr
        ( south,     10,         15)]
    for tie_id_info in tie_id_info_list:
        expected_start_sending_tie_ids.append(make_tie_id(*tie_id_info))
    assert start_sending_tie_ids == expected_start_sending_tie_ids
    #
    # Check stop_sending_tie_ids
    #
    expected_stop_sending_tie_ids = []
    tie_id_info_list = [
        # pylint:disable=bad-whitespace
        # Direction  Originator  Tie-Nr
        ( south,     10,         10)]
    for tie_id_info in tie_id_info_list:
        expected_stop_sending_tie_ids.append(make_tie_id(*tie_id_info))
    assert stop_sending_tie_ids == expected_stop_sending_tie_ids
    #
    # TODO: Test processing 2nd TIDE packet
    # TODO: Test errors (not sorted)
