import ipaddress

import common.ttypes
import encoding.ttypes
import packet_common
import tie_db

def make_prefix_tie(sender, level, direction, originator, tie_nr, seq_nr):
    tie_id = encoding.ttypes.TIEID(
        direction=direction,
        originator=originator,
        tietype=common.ttypes.TIETypeType.PrefixTIEType,
        tie_nr=tie_nr)
    tie_header = encoding.ttypes.TIEHeader(
        tieid=tie_id,
        seq_nr=seq_nr,
        remaining_lifetime=None,
        origination_time=None)
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
    assert (tab_str == "+-----------+------------+--------+-----+--------------------------+\n"
                       "| Direction | Originator | Type   | Nr  | Contents                 |\n"
                       "+-----------+------------+--------+-----+--------------------------+\n"
                       "| South     | 222        | Prefix | 333 | Prefix: 1.2.3.0/24       |\n"
                       "|           |            |        |     |   Metric: 2              |\n"
                       "|           |            |        |     |   Tag: 77                |\n"
                       "|           |            |        |     |   Tag: 88                |\n"
                       "|           |            |        |     |   Monotonic-clock: 12345 |\n"
                       "|           |            |        |     | Prefix: 1234:abcd::/64   |\n"
                       "|           |            |        |     |   Metric: 3              |\n"
                       "+-----------+------------+--------+-----+--------------------------+\n"
                       "| North     | 777        | Prefix | 888 | Prefix: 0.0.0.0/0        |\n"
                       "|           |            |        |     |   Metric: 10             |\n"
                       "+-----------+------------+--------+-----+--------------------------+\n")
