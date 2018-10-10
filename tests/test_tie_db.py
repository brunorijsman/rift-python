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
START_NEWER = 4      # TIE-DB has newer version of TIE-ID than in TIE/TIDE/TIRE. Start sending it.
STOP_SAME = 5        # TIE-DB has same version of TIE-ID as in TIDE. Stop sending it.
ACK = 6              # TIE-DB has same version of TIE-ID than in TIRE. Treat it as an ACK. Or,
                     # TIE-DB has same version of TIE-ID in TIE. Send an ACK
STORE_AND_ACK = 7    # TIE-DB doesn't have TIE-ID in TIE. Store in DB and ACK.
RE_ORIG = 8          # TIE-DB has older self-originated version of TIE. Re-originate newer.
FLUSH = 9            # TIE appears to be self-originated but is not in DB. Flush (re-orig empty)

def test_compare_tie_header():
    # Exactly same
    header1 = packet_common.make_tie_header(
        direction=NORTH,
        originator=1,
        tie_type=PREFIX,
        tie_nr=6,
        seq_nr=7,
        lifetime=500)
    header2 = packet_common.make_tie_header(
        direction=NORTH,
        originator=1,
        tie_type=PREFIX,
        tie_nr=6,
        seq_nr=7,
        lifetime=500)
    assert tie_db.compare_tie_header_age(header1, header2) == 0
    # Almost same, lifetime is different but close enough to call it same (within 300 seconds)
    header1 = packet_common.make_tie_header(
        direction=NORTH,
        originator=1,
        tie_type=PREFIX,
        tie_nr=6,
        seq_nr=7,
        lifetime=1)
    header2 = packet_common.make_tie_header(
        direction=NORTH,
        originator=1,
        tie_type=PREFIX,
        tie_nr=6,
        seq_nr=7,
        lifetime=300)
    assert tie_db.compare_tie_header_age(header1, header2) == 0
    # Different: lifetime is the tie breaker (more than 300 seconds difference)
    header1 = packet_common.make_tie_header(
        direction=NORTH,
        originator=1,
        tie_type=PREFIX,
        tie_nr=6,
        seq_nr=7,
        lifetime=1)
    header2 = packet_common.make_tie_header(
        direction=NORTH,
        originator=1,
        tie_type=PREFIX,
        tie_nr=6,
        seq_nr=7,
        lifetime=600)
    assert tie_db.compare_tie_header_age(header1, header2) == -1
    assert tie_db.compare_tie_header_age(header2, header1) == 1
    # Different: lifetime is the tie breaker; the difference is less than 300 but one is zero and
    # the other is non-zero. The one with zero lifetime is considered older.
    header1 = packet_common.make_tie_header(
        direction=NORTH,
        originator=1,
        tie_type=PREFIX,
        tie_nr=6,
        seq_nr=7,
        lifetime=0)
    header2 = packet_common.make_tie_header(
        direction=NORTH,
        originator=1,
        tie_type=PREFIX,
        tie_nr=6,
        seq_nr=7,
        lifetime=299)
    assert tie_db.compare_tie_header_age(header1, header2) == -1
    assert tie_db.compare_tie_header_age(header2, header1) == 1
    # Different: seq_nr is the tie breaker.
    header1 = packet_common.make_tie_header(
        direction=NORTH,
        originator=1,
        tie_type=PREFIX,
        tie_nr=6,
        seq_nr=20,
        lifetime=1)
    header2 = packet_common.make_tie_header(
        direction=NORTH,
        originator=1,
        tie_type=PREFIX,
        tie_nr=6,
        seq_nr=19,
        lifetime=600)
    assert tie_db.compare_tie_header_age(header1, header2) == 1
    assert tie_db.compare_tie_header_age(header2, header1) == -1

def test_add_prefix_tie():
    packet_common.add_missing_methods_to_thrift()
    tdb = tie_db.TIE_DB()
    prefix_tie_1 = packet_common.make_prefix_tie_packet(
        direction=common.ttypes.TieDirectionType.South,
        originator=222,
        tie_nr=333,
        seq_nr=444,
        lifetime=555)
    packet_common.add_ipv4_prefix_to_prefix_tie(prefix_tie_1, "1.2.3.0/24", 2, [77, 88], 12345)
    packet_common.add_ipv6_prefix_to_prefix_tie(prefix_tie_1, "1234:abcd::/64", 3)
    tdb.store_tie(prefix_tie_1)
    prefix_tie_2 = packet_common.make_prefix_tie_packet(
        direction=common.ttypes.TieDirectionType.North,
        originator=777,
        tie_nr=888,
        seq_nr=999,
        lifetime=0)
    packet_common.add_ipv4_prefix_to_prefix_tie(prefix_tie_2, "0.0.0.0/0", 10)
    tdb.store_tie(prefix_tie_2)
    assert tdb.find_tie(prefix_tie_1.header.tieid) == prefix_tie_1
    assert tdb.find_tie(prefix_tie_2.header.tieid) == prefix_tie_2
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
                seq_nr = tdb.ties[tie_id].header.seq_nr
                lifetime = tdb.ties[tie_id].header.remaining_lifetime
            elif disposition == REQUEST_MISSING:
                seq_nr = 0
                lifetime = 0
            tie_header = packet_common.make_tie_header(direction, originator, PREFIX, tie_nr,
                                                       seq_nr, lifetime)
            tie_headers.append(tie_header)
    return tie_headers

# TODO: Add test cases for lifetime same / different (less than 2 sec) / different (more than 2 sec)

def check_process_tide_common(tdb, start_range, end_range, disposition_list):
    # pylint:disable=too-many-locals
    # Prepare the TIDE packet
    tide_packet = packet_common.make_tide_packet(start_range, end_range)
    for (direction, originator, tie_nr, seq_nr, lifetime, disposition) in disposition_list:
        # START_EXTRA refers to a TIE-ID which is only in the TIE-DB and not in the TIDE, so don't
        # add those.
        if disposition != START_EXTRA:
            tie_header = packet_common.make_tie_header(direction, originator, PREFIX, tie_nr,
                                                       seq_nr, lifetime)
            packet_common.add_tie_header_to_tide(tide_packet, tie_header)
    # Process the TIDE packet
    result = tdb.process_received_tide_packet(tide_packet)
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
    check_process_tide_common(tdb, start_range, end_range, disposition_list)

def check_process_tide_2(tdb):
    start_range = packet_common.make_tie_id(NORTH, 20, PREFIX, 1)
    end_range = packet_common.make_tie_id(NORTH, 100, PREFIX, 1)
    disposition_list = [
        # pylint:disable=bad-whitespace
        # Direction  Originator  Tie-Nr  Seq-Nr  Lifetime  Disposition
        ( NORTH,     10,         7,      None,   100,      START_EXTRA),
        ( NORTH,     21,         15,     5,      100,      REQUEST_OLDER)]
    check_process_tide_common(tdb, start_range, end_range, disposition_list)

def check_process_tide_3(tdb):
    start_range = packet_common.make_tie_id(NORTH, 200, PREFIX, 1)
    end_range = packet_common.make_tie_id(NORTH, 300, PREFIX, 1)
    disposition_list = [
        # pylint:disable=bad-whitespace
        # Direction  Originator  Tie-Nr  Seq-Nr  Lifetime  Disposition
        ( NORTH,     110,        40,     None,   100,      START_EXTRA),
        ( NORTH,     210,        6,      None,   100,      START_EXTRA)]
    check_process_tide_common(tdb, start_range, end_range, disposition_list)

def test_process_tide():
    # pylint:disable=too-many-locals
    # TODO: Also have other TIEs than prefix TIEs
    packet_common.add_missing_methods_to_thrift()
    tdb = tie_db.TIE_DB()
    db_tie_info_list = [
        # pylint:disable=bad-whitespace
        # Direction Origin TieNr SeqNr Lifetime  Disposition
        ( SOUTH,    8,     1,    1,    100),   # In gap before TIDE-1; start
        ( SOUTH,    10,    1,    2,    100),   # Not in TIDE-1 (start gap); start
        ( SOUTH,    10,    2,    5,    100),   # Not in TIDE-1 (start gap); start
        ( SOUTH,    10,    10,   10,   100),   # Same version as in TIDE; stop
        ( SOUTH,    10,    12,   5,    100),   # Not in TIDE-1 (middle gap); start
        ( SOUTH,    10,    13,   3,    100),   # Older version than in TIDE-1; request
        ( NORTH,    3,     15,   7,    100),   # Newer version than in TIDE-1; start
        ( NORTH,    4,     1,    1,    100),   # Not in TIDE-1 (end gap); start
        ( NORTH,    10,    7,    6,    100),   # In TIDE-1...TIDE-2 gap; start
        ( NORTH,    21,    15,   3,    100),   # Older version than in TIDE-2; request
        ( NORTH,    110,   40,   1,    100),   # In TIDE-2...TIDE-3 gap; start
        ( NORTH,    210,   6,    6,    100)]   # Not in TIDE-3 (empty); start
    for db_tie_info in db_tie_info_list:
        db_tie = packet_common.make_prefix_tie_packet(*db_tie_info)
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

def check_process_tire_common(tdb, disposition_list):
    # pylint:disable=too-many-locals
    # Prepare the TIRE packet
    tire = packet_common.make_tire_packet()
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
    check_process_tire_common(tdb, disposition_list)

def test_process_tire():
    packet_common.add_missing_methods_to_thrift()
    tdb = tie_db.TIE_DB()
    db_tie_info_list = [
        # pylint:disable=bad-whitespace
        # Direction Origin TieNr SeqNr Lifetime  Disposition
        ( SOUTH,    10,    13,   3,    100),   # Older version than in TIRE; request
        ( SOUTH,    10,    14,   2,    100),   # Not in TIRE; no action
        ( NORTH,    3,     15,   7,    100),   # Newer version than in TIRE; start
        ( NORTH,    4,     1,    8,    100)]   # Same version as in TIRE; ack
    for db_tie_info in db_tie_info_list:
        db_tie = packet_common.make_prefix_tie_packet(*db_tie_info)
        tdb.store_tie(db_tie)
    check_process_tire(tdb)

TIE_SAME = 1           # DB TIE is (fudgy) same version as RX TIE
TIE_NEWER = 2          # DB TIE contains newer version than RX TIE
TIE_OLDER = 3          # DB TIE contains older version than RX TIE (not self-originated)
TIE_OLDER_SELF = 4     # DB TIE contains older version than RX TIE (self-originated)
TIE_MISSING = 5        # DB TIE does not yet contain RX TIE (not self-originated)
TIE_MISSING_SELF = 6   # DB TIE does not yet contain RX TIE (not self-originated)

def check_process_tie_common(tdb, my_system_id, disposition_list):
    # pylint:disable=too-many-locals
    for (direction, originator, tie_nr, seq_nr, lifetime, disposition) in disposition_list:
        tie_id = packet_common.make_tie_id(direction, originator, PREFIX, tie_nr)
        old_db_tie = tdb.find_tie(tie_id)
        rx_tie = packet_common.make_prefix_tie_packet(direction, originator, tie_nr, seq_nr,
                                                      lifetime)
        result = tdb.process_received_tie_packet(rx_tie, my_system_id)
        (start_sending_tie_header, ack_tie_header) = result
        if disposition == TIE_SAME:
            # Acknowledge the TX TIE which is the "same" as the DB TIE
            # Note: the age in the DB TIE and the RX TIE could be slightly different; the ACK should
            # contain the DB TIE header.
            new_db_tie = tdb.find_tie(tie_id)
            assert new_db_tie is not None
            assert new_db_tie == old_db_tie
            assert ack_tie_header == new_db_tie.header
            assert start_sending_tie_header is None
        elif disposition == TIE_NEWER:
            # Start sending the DB TIE
            new_db_tie = tdb.find_tie(tie_id)
            assert new_db_tie is not None
            assert new_db_tie == old_db_tie
            assert start_sending_tie_header == new_db_tie.header
            assert ack_tie_header is None
        elif disposition == TIE_OLDER:
            # Store the RX TIE in the DB and ACK it
            new_db_tie = tdb.find_tie(tie_id)
            assert old_db_tie is not None
            assert new_db_tie is not None
            assert new_db_tie != old_db_tie
            assert new_db_tie.header == rx_tie.header
            assert ack_tie_header == new_db_tie.header
            assert start_sending_tie_header is None
        elif disposition == TIE_OLDER_SELF:
            # Re-originate the DB TIE by bumping up the version to RX TIE version plus one
            new_db_tie = tdb.find_tie(tie_id)
            assert new_db_tie is not None
            assert new_db_tie.header.seq_nr == rx_tie.header.seq_nr + 1
            assert start_sending_tie_header == new_db_tie.header
            assert ack_tie_header is None
        elif disposition == TIE_MISSING:
            # Store the RX TIE in the DB and ACK it
            new_db_tie = tdb.find_tie(tie_id)
            assert old_db_tie is None
            assert new_db_tie is not None
            assert new_db_tie.header == rx_tie.header
            assert ack_tie_header == new_db_tie.header
            assert start_sending_tie_header is None
        elif disposition == TIE_MISSING_SELF:
            # Re-originate an empty version of the RX TIE with a higher version than the RX TIE
            new_db_tie = tdb.find_tie(tie_id)
            assert old_db_tie is None
            assert new_db_tie is not None
            assert new_db_tie.header.seq_nr == rx_tie.header.seq_nr + 1
            assert start_sending_tie_header == new_db_tie.header
            assert ack_tie_header is None
        else:
            assert False

def check_process_tie(tdb, my_system_id):
    disposition_list = [
        # pylint:disable=bad-whitespace
        # Direction  Originator  Tie-Nr  Seq-Nr  Lifetime  Disposition
        ( SOUTH,     10,         13,     3,      599,      TIE_NEWER),
        ( SOUTH,     20,         4,      1,      600,      TIE_MISSING),
        ( SOUTH,     999,        1,      9,      500,      TIE_OLDER_SELF),
        ( SOUTH,     999,        4,      3,      200,      TIE_MISSING_SELF),
        ( NORTH,     5,          3,      3,      600,      TIE_OLDER),
        ( NORTH,     5,          8,      12,     100,      TIE_SAME),   # Exact same
        ( NORTH,     6,          7,      4,      550,      TIE_SAME),   # Almost same - DB is older
        ( NORTH,     6,          7,      4,      490,      TIE_SAME)]   # Almost same - DB is newer
    check_process_tie_common(tdb, my_system_id, disposition_list)

def test_process_tie():
    packet_common.add_missing_methods_to_thrift()
    tdb = tie_db.TIE_DB()
    my_id = 999
    db_tie_info_list = [
        # pylint:disable=bad-whitespace
        # Direction Origin TieNr SeqNr Lifetime  Disposition
        ( SOUTH,    10,    13,   5,    100),   # TIE_NEWER
        ( SOUTH,    999,   1,    4,    69),    # TIE_OLDER_SELF
        ( NORTH,    5,     3,    2,    200),   # TIE_OLDER
        ( NORTH,    5,     8,    12,   100),   # TIE_SAME
        ( NORTH,    6,     7,    4,    500)]   # TIE_SAME
    for db_tie_info in db_tie_info_list:
        db_tie = packet_common.make_prefix_tie_packet(*db_tie_info)
        tdb.store_tie(db_tie)
    check_process_tie(tdb, my_system_id=my_id)
