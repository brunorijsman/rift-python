import common.ttypes
import encoding.ttypes
import packet_common
import tie_db

# pylint: disable=line-too-long

SOUTH = common.ttypes.TieDirectionType.South
NORTH = common.ttypes.TieDirectionType.North

NODE = common.ttypes.TIETypeType.NodeTIEType
PREFIX = common.ttypes.TIETypeType.PrefixTIEType
TRANSITIVE_PREFIX = common.ttypes.TIETypeType.TransitivePrefixTIEType
PG_PREFIX = common.ttypes.TIETypeType.PGPrefixTIEType
KEY_VALUE = common.ttypes.TIETypeType.KeyValueTIEType

REQUEST_MISSING = 1  # TIE-DB is missing a TIE-ID which is reported in TIDE. Request it.
REQUEST_OLDER = 2    # TIE-DB has older version of TIE-ID than in TIDE/TIRE. Request it.
START_EXTRA = 3      # TIE-DB has extra TIE-ID which is not in TIDE. Start sending it.
START_NEWER = 4      # TIE-DB has newer version of TIE-ID than in TIDE/TIRE. Start sending it.
STOP_SAME = 5        # TIE-DB has same version of TIE-ID as in TIDE. Stop sending it.
ACK = 6              # TIE-DB has same version of TIE-ID than in TIRE. Treat it as an ACK.

def test_add_prefix_tie():
    packet_common.add_missing_methods_to_thrift()
    tdb = tie_db.TIE_DB()
    prefix_tie_1 = packet_common.make_prefix_tie(
        sender=111,
        level=2,
        direction=common.ttypes.TieDirectionType.South,
        originator=222,
        tie_nr=333,
        seq_nr=444,
        lifetime=555)
    packet_common.add_ipv4_prefix_to_prefix_tie(prefix_tie_1, "1.2.3.0/24", 2, [77, 88], 12345)
    packet_common.add_ipv6_prefix_to_prefix_tie(prefix_tie_1, "1234:abcd::/64", 3)
    tdb.store_tie(prefix_tie_1)
    prefix_tie_2 = packet_common.make_prefix_tie(
        sender=555,
        level=6,
        direction=common.ttypes.TieDirectionType.North,
        originator=777,
        tie_nr=888,
        seq_nr=999,
        lifetime=0)
    packet_common.add_ipv4_prefix_to_prefix_tie(prefix_tie_2, "0.0.0.0/0", 10)
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
            "+-----------+------------+--------+--------+--------+----------+--------------------------+\n"
            "| Direction | Originator | Type   | TIE Nr | Seq Nr | Lifetime | Contents                 |\n"
            "+-----------+------------+--------+--------+--------+----------+--------------------------+\n"
            "| South     | 222        | Prefix | 333    | 444    | 555      | Prefix: 1.2.3.0/24       |\n"
            "|           |            |        |        |        |          |   Metric: 2              |\n"
            "|           |            |        |        |        |          |   Tag: 77                |\n"
            "|           |            |        |        |        |          |   Tag: 88                |\n"
            "|           |            |        |        |        |          |   Monotonic-clock: 12345 |\n"
            "|           |            |        |        |        |          | Prefix: 1234:abcd::/64   |\n"
            "|           |            |        |        |        |          |   Metric: 3              |\n"
            "+-----------+------------+--------+--------+--------+----------+--------------------------+\n"
            "| North     | 777        | Prefix | 888    | 999    | 0        | Prefix: 0.0.0.0/0        |\n"
            "|           |            |        |        |        |          |   Metric: 10             |\n"
            "+-----------+------------+--------+--------+--------+----------+--------------------------+\n")


def tie_headers_with_disposition(tdb, disposition_list, filter_dispositions):
    tie_headers = []
    for (direction, originator, tie_nr, seq_nr, lifetime, disposition) in disposition_list:
        if disposition in filter_dispositions:
            if disposition in [START_EXTRA, START_NEWER]:
                tie_id = packet_common.make_tie_id(direction, originator, PREFIX, tie_nr)
                seq_nr = tdb.ties[tie_id].content.tie.header.seq_nr
                lifetime = tdb.ties[tie_id].content.tie.header.remaining_lifetime
            elif disposition == REQUEST_MISSING:
                seq_nr = 0
                lifetime = 0
            tie_header = packet_common.make_tie_header(direction, originator, PREFIX, tie_nr,
                                                       seq_nr, lifetime)
            tie_headers.append(tie_header)
    return tie_headers

# TODO: Add test cases for lifetime same / different (less than 2 sec) / different (more than 2 sec)

def check_process_tide_common(tdb, sender, level, start_range, end_range, disposition_list):
    # pylint:disable=too-many-locals
    # Prepare the TIDE packet
    tide = packet_common.make_tide(sender, level, start_range, end_range)
    for (direction, originator, tie_nr, seq_nr, lifetime, disposition) in disposition_list:
        # START_EXTRA refers to a TIE-ID which is only in the TIE-DB and not in the TIDE, so don't
        # add those.
        if disposition != START_EXTRA:
            tie_header = packet_common.make_tie_header(direction, originator, PREFIX, tie_nr,
                                                       seq_nr, lifetime)
            packet_common.add_tie_header_to_tide(tide, tie_header)
    # Process the TIDE packet
    result = tdb.process_received_tide_packet(tide)
    (request_tie_headers, start_sending_tie_headers, stop_sending_tie_headers) = result
    # Check results
    compare_header_lists(
        tie_headers_with_disposition(tdb, disposition_list, [REQUEST_MISSING, REQUEST_OLDER]),
        request_tie_headers)
    compare_header_lists(
        tie_headers_with_disposition(tdb, disposition_list, [START_EXTRA, START_NEWER]),
        start_sending_tie_headers)
    compare_header_lists(
        tie_headers_with_disposition(tdb, disposition_list, [STOP_SAME]),
        stop_sending_tie_headers)

def check_process_tide_1(tdb):
    start_range = packet_common.make_tie_id(SOUTH, 10, PREFIX, 1)
    end_range = packet_common.make_tie_id(NORTH, 8, PREFIX, 999)
    disposition_list = [
        # pylint:disable=bad-whitespace
        # Direction  Originator  Tie-Nr  Seq-Nr  Lifetime  Disposition
        ( SOUTH,     8,          1,      None,   100,      START_EXTRA),
        ( SOUTH,     10,         1,      None,   100,      START_EXTRA),
        ( SOUTH,     10,         2,      None,   100,      START_EXTRA),
        ( SOUTH,     10,         10,     10,     100,      STOP_SAME),
        ( SOUTH,     10,         11,     1,      100,      REQUEST_MISSING),
        ( SOUTH,     10,         12,     None,   100,      START_EXTRA),
        ( SOUTH,     10,         13,     5,      100,      REQUEST_OLDER),
        ( NORTH,     3,          15,     5,      100,      START_NEWER),
        ( NORTH,     4,          1,      None,   100,      START_EXTRA)]
    check_process_tide_common(tdb, 999, 999, start_range, end_range, disposition_list)

def check_process_tide_2(tdb):
    start_range = packet_common.make_tie_id(NORTH, 20, PREFIX, 1)
    end_range = packet_common.make_tie_id(NORTH, 100, PREFIX, 1)
    disposition_list = [
        # pylint:disable=bad-whitespace
        # Direction  Originator  Tie-Nr  Seq-Nr  Lifetime  Disposition
        ( NORTH,     10,         7,      None,   100,      START_EXTRA),
        ( NORTH,     21,         15,     5,      100,      REQUEST_OLDER)]
    check_process_tide_common(tdb, 666, 0, start_range, end_range, disposition_list)

def check_process_tide_3(tdb):
    start_range = packet_common.make_tie_id(NORTH, 200, PREFIX, 1)
    end_range = packet_common.make_tie_id(NORTH, 300, PREFIX, 1)
    disposition_list = [
        # pylint:disable=bad-whitespace
        # Direction  Originator  Tie-Nr  Seq-Nr  Lifetime  Disposition
        ( NORTH,     110,        40,     None,   100,      START_EXTRA),
        ( NORTH,     210,        6,      None,   100,      START_EXTRA)]
    check_process_tide_common(tdb, 666, 0, start_range, end_range, disposition_list)

def test_process_tide():
    # pylint:disable=too-many-locals
    # TODO: Also have other TIEs than prefix TIEs
    packet_common.add_missing_methods_to_thrift()
    tdb = tie_db.TIE_DB()
    db_tie_info_list = [
        # pylint:disable=bad-whitespace
        # Sender Level Direction Origin TieNr SeqNr Lifetime  Disposition
        ( 999,   999,  SOUTH,    8,     1,    1,    100),   # In gap before TIDE-1; start
        ( 999,   999,  SOUTH,    10,    1,    2,    100),   # Not in TIDE-1 (start gap); start
        ( 999,   999,  SOUTH,    10,    2,    5,    100),   # Not in TIDE-1 (start gap); start
        ( 777,   7,    SOUTH,    10,    10,   10,   100),   # Same version as in TIDE; stop
        ( 999,   999,  SOUTH,    10,    12,   5,    100),   # Not in TIDE-1 (middle gap); start
        ( 999,   999,  SOUTH,    10,    13,   3,    100),   # Older version than in TIDE-1; request
        ( 999,   999,  NORTH,    3,     15,   7,    100),   # Newer version than in TIDE-1; start
        ( 999,   999,  NORTH,    4,     1,    1,    100),   # Not in TIDE-1 (end gap); start
        ( 999,   999,  NORTH,    10,    7,    6,    100),   # In TIDE-1...TIDE-2 gap; start
        ( 999,   999,  NORTH,    21,    15,   3,    100),   # Older version than in TIDE-2; request
        ( 999,   999,  NORTH,    110,   40,   1,    100),   # In TIDE-2...TIDE-3 gap; start
        ( 999,   999,  NORTH,    210,   6,    6,    100)]   # Not in TIDE-3 (empty); start
    for (sender, level, direction, originator, tie_nr, seq_nr, lifetime) in db_tie_info_list:
        db_tie = packet_common.make_prefix_tie(sender, level, direction, originator, tie_nr, seq_nr,
                                               lifetime)
        tdb.store_tie(db_tie)
    check_process_tide_1(tdb)
    check_process_tide_2(tdb)
    check_process_tide_3(tdb)
    # Test wrap-around. Finished sending all TIDEs, now send first TIDE again. The key test is
    # whether the TIE in the TIE-DB in the gap before TIDE-1 is put on the send queue again.
    check_process_tide_1(tdb)

def compare_header_lists(headers1, headers2):
    # Order does not matter in comparison. This is maybe not the most efficient way of doing it,
    # but it makes it easier to debug test failures (most clear error messages)
    for header in headers1:
        assert header in headers2
    for header in headers2:
        assert header in headers1

def check_process_tire_common(tdb, sender, level, disposition_list):
    # pylint:disable=too-many-locals
    # Prepare the TIRE packet
    tire = packet_common.make_tire(sender, level)
    for (direction, originator, tie_nr, seq_nr, lifetime, _disposition) in disposition_list:
        tie_header = packet_common.make_tie_header(direction, originator, PREFIX, tie_nr,
                                                   seq_nr, lifetime)
        packet_common.add_tie_header_to_tire(tire, tie_header)
    # Process the TIRE packet
    result = tdb.process_received_tire_packet(tire)
    (request_tie_headers, start_sending_tie_headers, acked_tie_headers) = result
    # Check results
    compare_header_lists(tie_headers_with_disposition(tdb, disposition_list, [REQUEST_OLDER]),
                         request_tie_headers)
    compare_header_lists(tie_headers_with_disposition(tdb, disposition_list, [START_NEWER]),
                         start_sending_tie_headers)
    compare_header_lists(tie_headers_with_disposition(tdb, disposition_list, [ACK]),
                         acked_tie_headers)

def check_process_tire(tdb):
    disposition_list = [
        # pylint:disable=bad-whitespace
        # Direction  Originator  Tie-Nr  Seq-Nr  Lifetime  Disposition
        ( SOUTH,     10,         13,     5,      100,      REQUEST_OLDER),
        ( NORTH,     3,          15,     5,      100,      START_NEWER),
        ( NORTH,     4,          1,      8,      100,      ACK)]
    check_process_tire_common(tdb, 999, 999, disposition_list)

def test_process_tire():
    # pylint:disable=too-many-locals
    packet_common.add_missing_methods_to_thrift()
    tdb = tie_db.TIE_DB()
    db_tie_info_list = [
        # pylint:disable=bad-whitespace
        # Sender Level Direction Origin TieNr SeqNr Lifetime  Disposition
        ( 999,   999,  SOUTH,    10,    13,   3,    100),   # Older version than in TIRE; request
        ( 999,   999,  SOUTH,    10,    14,   2,    100),   # Not in TIRE; no action
        ( 777,   777,  NORTH,    3,     15,   7,    100),   # Newer version than in TIRE; start
        ( 999,   999,  NORTH,    4,     1,    8,    100)]   # Same version as in TIRE; ack
    for db_tie_info in db_tie_info_list:
        db_tie = packet_common.make_prefix_tie(*db_tie_info)
        tdb.store_tie(db_tie)
    check_process_tire(tdb)

def test_direction_str():
    assert tie_db.direction_str(common.ttypes.TieDirectionType.South) == "South"
    assert tie_db.direction_str(common.ttypes.TieDirectionType.North) == "North"
    assert tie_db.direction_str(999) == "999"

def test_tietype_str():
    assert tie_db.tietype_str(common.ttypes.TIETypeType.NodeTIEType) == "Node"
    assert tie_db.tietype_str(common.ttypes.TIETypeType.PrefixTIEType) == "Prefix"
    assert (tie_db.tietype_str(common.ttypes.TIETypeType.TransitivePrefixTIEType) ==
            "TransitivePrefix")
    assert tie_db.tietype_str(common.ttypes.TIETypeType.PGPrefixTIEType) == "PolicyGuidedPrefix"
    assert tie_db.tietype_str(common.ttypes.TIETypeType.KeyValueTIEType) == "KeyValue"
    assert tie_db.tietype_str(888) == "888"
