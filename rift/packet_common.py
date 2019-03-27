import copy
import ipaddress
import sortedcontainers

import thrift.protocol.TBinaryProtocol
import thrift.transport.TTransport

import common.ttypes
import constants
import encoding.ttypes
import encoding.constants
import utils

def ipv4_prefix_tup(ipv4_prefix):
    return (ipv4_prefix.address, ipv4_prefix.prefixlen)

def ipv6_prefix_tup(ipv6_prefix):
    return (ipv6_prefix.address, ipv6_prefix.prefixlen)

def ip_prefix_tup(ip_prefix):
    assert (ip_prefix.ipv4prefix is None) or (ip_prefix.ipv6prefix is None)
    assert (ip_prefix.ipv4prefix is not None) or (ip_prefix.ipv6prefix is not None)
    if ip_prefix.ipv4prefix:
        return (4, ipv4_prefix_tup(ip_prefix.ipv4prefix))
    return (6, ipv6_prefix_tup(ip_prefix.ipv6prefix))

def tie_id_tup(tie_id):
    return (tie_id.direction, tie_id.originator, tie_id.tietype, tie_id.tie_nr)

def tie_header_tup(tie_header):
    return (tie_header.tieid, tie_header.seq_nr, tie_header.remaining_lifetime,
            tie_header.origination_time)

def link_id_pair_tup(link_id_pair):
    return (link_id_pair.local_id, link_id_pair.remote_id)

def timestamp_tup(timestamp):
    return (timestamp.AS_sec, timestamp.AS_nsec)

def add_missing_methods_to_thrift():
    # See http://bit.ly/thrift-missing-hash for details about why this is needed
    common.ttypes.IPv4PrefixType.__hash__ = (
        lambda self: hash(ipv4_prefix_tup(self)))
    common.ttypes.IPv4PrefixType.__eq__ = (
        lambda self, other: ipv4_prefix_tup(self) == ipv4_prefix_tup(other))
    common.ttypes.IPv6PrefixType.__hash__ = (
        lambda self: hash(ipv6_prefix_tup(self)))
    common.ttypes.IPv6PrefixType.__eq__ = (
        lambda self, other: ipv6_prefix_tup(self) == ipv6_prefix_tup(other))
    common.ttypes.IPPrefixType.__hash__ = (
        lambda self: hash(ip_prefix_tup(self)))
    common.ttypes.IPPrefixType.__eq__ = (
        lambda self, other: ip_prefix_tup(self) == ip_prefix_tup(other))
    common.ttypes.IPPrefixType.__str__ = ip_prefix_str
    common.ttypes.IPPrefixType.__lt__ = (
        lambda self, other: ip_prefix_tup(self) < ip_prefix_tup(other))
    common.ttypes.IEEE802_1ASTimeStampType.__hash__ = (
        lambda self: hash(timestamp_tup(self)))
    common.ttypes.IEEE802_1ASTimeStampType.__eq__ = (
        lambda self, other: timestamp_tup(self) == timestamp_tup(other))
    encoding.ttypes.TIEID.__hash__ = (
        lambda self: hash(tie_id_tup(self)))
    encoding.ttypes.TIEID.__eq__ = (
        lambda self, other: tie_id_tup(self) == tie_id_tup(other))
    encoding.ttypes.TIEID.__lt__ = (
        lambda self, other: tie_id_tup(self) < tie_id_tup(other))
    encoding.ttypes.TIEHeader.__hash__ = (
        lambda self: hash(tie_header_tup(self)))
    encoding.ttypes.TIEHeader.__eq__ = (
        lambda self, other: tie_header_tup(self) == tie_header_tup(other))
    encoding.ttypes.LinkIDPair.__hash__ = (
        lambda self: hash(link_id_pair_tup(self)))
    encoding.ttypes.LinkIDPair.__eq__ = (
        lambda self, other: link_id_pair_tup(self) == link_id_pair_tup(other))
    encoding.ttypes.LinkIDPair.__hash__ = (
        lambda self: hash(link_id_pair_tup(self)))
    encoding.ttypes.LinkIDPair.__lt__ = (
        lambda self, other: link_id_pair_tup(self) < link_id_pair_tup(other))

def encode_protocol_packet(protocol_packet):
    # Since Thrift does not support unsigned integer, we need to "fix" unsigned integers to be
    # encoded as signed integers.
    # We have to make a deep copy of the non-encoded packet, but this "fixing" involves changing
    # various fields in the non-encoded packet from the range (0...MAX_UNSIGNED_INT) to
    # (MIN_SIGNED_INT...MAX_SIGNED_INT) for various sizes of integers.
    # For the longest time, I tried to avoid making a deep copy of the non-encoded packets, at least
    # for some of the packets. For transient messages (e.g. LIEs) that is easier than for persistent
    # messages (e.g. TIE which are stored in the database, or TIDEs which are encoded once and sent
    # multiple times). However, in the end this turned out to be impossible or at least a
    # bountiful source of bugs, because transient messages contain direct or indirect references
    # to persistent objects.
    # So, I gave up, and now always do a deep copy of the message to be encoded.
    fixed_protocol_packet = copy.deepcopy(protocol_packet)
    fix_prot_packet_before_encode(fixed_protocol_packet)
    transport_out = thrift.transport.TTransport.TMemoryBuffer()
    protocol_out = thrift.protocol.TBinaryProtocol.TBinaryProtocol(transport_out)
    fixed_protocol_packet.write(protocol_out)
    encoded_protocol_packet = transport_out.getvalue()
    return encoded_protocol_packet

def decode_protocol_packet(encoded_protocol_packet):
    transport_in = thrift.transport.TTransport.TMemoryBuffer(encoded_protocol_packet)
    protocol_in = thrift.protocol.TBinaryProtocol.TBinaryProtocol(transport_in)
    protocol_packet = encoding.ttypes.ProtocolPacket()
    # Thrift is prone to throw any unpredictable exception if the decode fails,
    # so disable pylint warning "No exception type(s) specified"
    # pylint: disable=W0702
    try:
        protocol_packet.read(protocol_in)
    except:
        # Decoding error
        return None
    fix_prot_packet_after_decode(protocol_packet)
    return protocol_packet

# What follows are some horrible hacks to deal with the fact that Thrift only support signed 8, 16,
# 32, and 64 bit numbers and not unsigned 8, 16, 32, and 64 bit numbers. The RIFT specification has
# several fields are intended to contain an unsigned numbers, but that are actually specified in the
# .thrift files as a signed numbers. Just look for the following text in the specification: "MUST be
# interpreted in implementation as unsigned ..." where ... can be 8 bits, or 16 bits, or 32 bits, or
# 64 bits. Keep in mind Python does not have sized integers: values of type int are unbounded (i.e.
# they have no limit on the size and no minimum or maximum value).

MAX_U64 = 0xffffffffffffffff
MAX_S64 = 0x7fffffffffffffff

MAX_U32 = 0xffffffff
MAX_S32 = 0x7fffffff

MAX_U16 = 0xffff
MAX_S16 = 0x7fff

MAX_U8 = 0xff
MAX_S8 = 0x7f

def u64_to_s64(u64):
    return u64 if u64 <= MAX_S64 else u64 - MAX_U64 - 1

def u32_to_s32(u32):
    return u32 if u32 <= MAX_S32 else u32 - MAX_U32 - 1

def u16_to_s16(u16):
    return u16 if u16 <= MAX_S16 else u16 - MAX_U16 - 1

def u8_to_s8(u08):
    return u08 if u08 <= MAX_S8 else u08 - MAX_U8 - 1

def s64_to_u64(s64):
    return s64 if s64 >= 0 else s64 + MAX_U64 + 1

def s32_to_u32(s32):
    return s32 if s32 >= 0 else s32 + MAX_U32 + 1

def s16_to_u16(s16):
    return s16 if s16 >= 0 else s16 + MAX_U16 + 1

def s8_to_u8(s08):
    return s08 if s08 >= 0 else s08 + MAX_U8 + 1

def fix_int(value, size, encode):
    if encode:
        # Fix before encode
        if size == 8:
            return u8_to_s8(value)
        if size == 16:
            return u16_to_s16(value)
        if size == 32:
            return u32_to_s32(value)
        if size == 64:
            return u64_to_s64(value)
        assert False
    else:
        # Fix after decode
        if size == 8:
            return s8_to_u8(value)
        if size == 16:
            return s16_to_u16(value)
        if size == 32:
            return s32_to_u32(value)
        if size == 64:
            return s64_to_u64(value)
        assert False
    return value  # Unreachable, stop pylint from complaining about inconsistent-return-statements

def fix_dict(old_dict, dict_fixes, encode):
    (key_fixes, value_fixes) = dict_fixes
    new_dict = {}
    for key, value in old_dict.items():
        new_key = fix_value(key, key_fixes, encode)
        new_value = fix_value(value, value_fixes, encode)
        new_dict[new_key] = new_value
    return new_dict

def fix_struct(struct, fixes, encode):
    for fix in fixes:
        (field_name, field_fix) = fix
        if field_name in vars(struct):
            field_value = getattr(struct, field_name)
            if field_value is not None:
                new_value = fix_value(field_value, field_fix, encode)
                setattr(struct, field_name, new_value)
    return struct

def fix_set(old_set, fix, encode):
    new_set = set()
    for old_value in old_set:
        new_value = fix_value(old_value, fix, encode)
        new_set.add(new_value)
    return new_set

def fix_list(old_list, fix, encode):
    new_list = []
    for old_value in old_list:
        new_value = fix_value(old_value, fix, encode)
        new_list.append(new_value)
    return new_list

def fix_value(value, fix, encode):
    if isinstance(value, set):
        new_value = fix_set(value, fix, encode)
    elif isinstance(value, list):
        new_value = fix_list(value, fix, encode)
    elif isinstance(fix, int):
        new_value = fix_int(value, fix, encode)
    elif isinstance(fix, tuple):
        new_value = fix_dict(value, fix, encode)
    elif isinstance(fix, list):
        new_value = fix_struct(value, fix, encode)
    else:
        assert False
    return new_value

def fix_packet_before_encode(packet, fixes):
    fix_struct(packet, fixes, True)

def fix_packet_after_decode(packet, fixes):
    fix_struct(packet, fixes, False)

TIEID_FIXES = [
    ('originator', 64),
    ('tie_nr', 32)
]

TIMESTAMP_FIXES = [
    ('AS_sec', 64),
    ('AS_nsec', 32)
]

TIE_HEADER_FIXES = [
    ('tieid', TIEID_FIXES),
    ('seq_nr', 32),
    ('remaining_lifetime', 32),
    ('origination_time', TIMESTAMP_FIXES),
    ('origination_lifetime', 32)
]

LINK_ID_PAIR_FIXES = [
    ('local_id', 32),                      # Draft doesn't mention this needs to treated as unsigned
    ('remote_id', 32)                      # Draft doesn't mention this needs to treated as unsigned
]

NODE_NEIGHBORS_TIE_ELEMENT_FIXES = [
    ('level', 16),
    ('cost', 32),
    ('link_ids', LINK_ID_PAIR_FIXES),
    ('bandwidth', 32)
]

IP_PREFIX_FIXES = [
    ('ipv4prefix', [
        ('address', 32),
        ('prefixlen', 8)                   # Draft doesn't mention this needs to treated as unsigned
    ]),
    ('ipv6prefix', [
        ('prefixlen', 8)                   # Draft doesn't mention this needs to treated as unsigned
    ])
]

PREFIX_ATTRIBUTES_FIXES = [
    ('metric', 32),
    ('tags', 64),
    ('monotonic_clock', [
        ('timestamp', TIMESTAMP_FIXES),
        ('transactionid', 8)
    ])
]

PREFIX_TIE_ELEMENT_FIXES = [
    ('prefixes', (IP_PREFIX_FIXES, PREFIX_ATTRIBUTES_FIXES))
]

PROTOCOL_PACKET_FIXES = [
    ('header', [
        ('major_version', 16),
        ('minor_version', 16),
        ('sender', 64),
        ('level', 16)]),
    ('content', [
        ('lie', [
            ('local_id', 32),              # Draft doesn't mention this needs to treated as unsigned
            ('flood_port', 16),
            ('link_mtu_size', 32),
            ('link_bandwidth', 32),
            ('neighbor', [
                ('originator', 64),
                ('remote_id', 32)          # Draft doesn't mention this needs to treated as unsigned
            ]),
            ('pod', 32),
            ('nonce', 16),                 # Draft doesn't mention this needs to treated as unsigned
            ('last_neighbor_nonce', 16),   # Draft doesn't mention this needs to treated as unsigned
            ('holdtime', 16),              # Draft doesn't mention this needs to treated as unsigned
            ('label', 32)]),
        ('tide', [
            ('start_range', TIEID_FIXES),
            ('end_range', TIEID_FIXES),
            ('headers', TIE_HEADER_FIXES)
        ]),
        ('tire', [
            ('headers', TIE_HEADER_FIXES)
        ]),
        ('tie', [
            ('header', TIE_HEADER_FIXES),
            ('element', [
                ('node', [
                    ('level', 16),
                    ('neighbors', (64, NODE_NEIGHBORS_TIE_ELEMENT_FIXES))
                ]),
                ('prefixes', PREFIX_TIE_ELEMENT_FIXES),
                ('positive_disaggregation_prefixes', PREFIX_TIE_ELEMENT_FIXES),
                ('negative_disaggregation_prefixes', PREFIX_TIE_ELEMENT_FIXES),
                ('external_prefixes', PREFIX_TIE_ELEMENT_FIXES),
            ])
        ])
    ])
]

def fix_prot_packet_before_encode(protocol_packet):
    fix_packet_before_encode(protocol_packet, PROTOCOL_PACKET_FIXES)

def fix_prot_packet_after_decode(protocol_packet):
    fix_packet_after_decode(protocol_packet, PROTOCOL_PACKET_FIXES)

def make_tie_id(direction, originator, tie_type, tie_nr):
    tie_id = encoding.ttypes.TIEID(
        direction=direction,
        originator=originator,
        tietype=tie_type,
        tie_nr=tie_nr)
    return tie_id

def make_tie_header(direction, originator, tie_type, tie_nr, seq_nr, lifetime,
                    origination_time=None):
    tie_id = make_tie_id(direction, originator, tie_type, tie_nr)
    tie_header = encoding.ttypes.TIEHeader(
        tieid=tie_id,
        seq_nr=seq_nr,
        remaining_lifetime=lifetime,
        origination_time=origination_time)
    return tie_header

def make_prefix_tie_packet(direction, originator, tie_nr, seq_nr, lifetime):
    # pylint:disable=too-many-locals
    tie_type = common.ttypes.TIETypeType.PrefixTIEType
    tie_header = make_tie_header(direction, originator, tie_type, tie_nr, seq_nr, lifetime)
    prefixes = {}
    prefix_tie_element = encoding.ttypes.PrefixTIEElement(prefixes=prefixes)
    tie_element = encoding.ttypes.TIEElement(prefixes=prefix_tie_element)
    tie_packet = encoding.ttypes.TIEPacket(header=tie_header, element=tie_element)
    return tie_packet

def make_ip_address(address_str):
    if ":" in address_str:
        return make_ipv6_address(address_str)
    else:
        return make_ipv4_address(address_str)

def make_ipv4_address(address_str):
    return ipaddress.IPv4Address(address_str)

def make_ipv6_address(address_str):
    return ipaddress.IPv6Address(address_str)

def make_ip_prefix(prefix_str):
    if ":" in prefix_str:
        return make_ipv6_prefix(prefix_str)
    else:
        return make_ipv4_prefix(prefix_str)

def make_ipv4_prefix(prefix_str):
    ipv4_network = ipaddress.IPv4Network(prefix_str)
    address = int(ipv4_network.network_address)
    prefixlen = ipv4_network.prefixlen
    ipv4_prefix = common.ttypes.IPv4PrefixType(address, prefixlen)
    prefix = common.ttypes.IPPrefixType(ipv4prefix=ipv4_prefix)
    return prefix

def make_ipv6_prefix(prefix_str):
    ipv6_network = ipaddress.IPv6Network(prefix_str)
    address = ipv6_network.network_address.packed
    prefixlen = ipv6_network.prefixlen
    ipv6_prefix = common.ttypes.IPv6PrefixType(address, prefixlen)
    prefix = common.ttypes.IPPrefixType(ipv6prefix=ipv6_prefix)
    return prefix

def add_ipv4_prefix_to_prefix_tie(prefix_tie_packet, prefix, metric, tags=None,
                                  monotonic_clock=None):
    attributes = encoding.ttypes.PrefixAttributes(metric, tags, monotonic_clock)
    prefix_tie_packet.element.prefixes.prefixes[prefix] = attributes

def add_ipv6_prefix_to_prefix_tie(prefix_tie_packet, ipv6_prefix_string, metric, tags=None,
                                  monotonic_clock=None):
    prefix = make_ipv6_prefix(ipv6_prefix_string)
    attributes = encoding.ttypes.PrefixAttributes(metric=metric,
                                                  tags=tags,
                                                  monotonic_clock=monotonic_clock)
    prefix_tie_packet.element.prefixes.prefixes[prefix] = attributes

def make_node_tie_packet(name, level, direction, originator, tie_nr, seq_nr, lifetime):
    # pylint:disable=too-many-locals
    tie_type = common.ttypes.TIETypeType.NodeTIEType
    tie_header = make_tie_header(direction, originator, tie_type, tie_nr, seq_nr, lifetime)
    node_tie_element = encoding.ttypes.NodeTIEElement(
        level=level,
        neighbors={},
        capabilities=None,  # TODO: Implement this
        flags=None,         # TODO: Implement this
        name=name)
    tie_element = encoding.ttypes.TIEElement(node=node_tie_element)
    tie_packet = encoding.ttypes.TIEPacket(header=tie_header, element=tie_element)
    return tie_packet

def make_tide_packet(start_range, end_range):
    tide_packet = encoding.ttypes.TIDEPacket(start_range=start_range,
                                             end_range=end_range,
                                             headers=[])
    return tide_packet

def add_tie_header_to_tide(tide_packet, tie_header):
    tide_packet.headers.append(tie_header)

def make_tire_packet():
    tire_packet = encoding.ttypes.TIREPacket(headers=set())
    return tire_packet

def add_tie_header_to_tire(tire_packet, tie_header):
    tire_packet.headers.add(tie_header)

DIRECTION_TO_STR = {
    common.ttypes.TieDirectionType.South: "South",
    common.ttypes.TieDirectionType.North: "North"
}

def direction_str(direction):
    if direction in DIRECTION_TO_STR:
        return DIRECTION_TO_STR[direction]
    else:
        return str(direction)

def ipv4_prefix_str(ipv4_prefix):
    address = ipv4_prefix.address
    length = ipv4_prefix.prefixlen
    return str(ipaddress.IPv4Network((address, length)))

def ipv6_prefix_str(ipv6_prefix):
    address = ipv6_prefix.address.rjust(16, b"\x00")
    length = ipv6_prefix.prefixlen
    return str(ipaddress.IPv6Network((address, length)))

def ip_prefix_str(ip_prefix):
    assert (ip_prefix.ipv4prefix is None) or (ip_prefix.ipv6prefix is None)
    assert (ip_prefix.ipv4prefix is not None) or (ip_prefix.ipv6prefix is not None)
    result = ""
    if ip_prefix.ipv4prefix:
        result += ipv4_prefix_str(ip_prefix.ipv4prefix)
    if ip_prefix.ipv6prefix:
        result += ipv6_prefix_str(ip_prefix.ipv6prefix)
    return result

TIETYPE_TO_STR = {
    common.ttypes.TIETypeType.NodeTIEType: "Node",
    common.ttypes.TIETypeType.PrefixTIEType: "Prefix",
    common.ttypes.TIETypeType.PositiveDisaggregationPrefixTIEType: "Pos-Dis-Prefix",
    common.ttypes.TIETypeType.NegativeDisaggregationPrefixTIEType: "Neg-Dis-Prefix",
    common.ttypes.TIETypeType.ExternalPrefixTIEType: "Ext-Prefix",
    common.ttypes.TIETypeType.PGPrefixTIEType: "PG-Prefix",
    common.ttypes.TIETypeType.KeyValueTIEType: "Key-Value"
}

def tietype_str(tietype):
    if tietype in TIETYPE_TO_STR:
        return TIETYPE_TO_STR[tietype]
    else:
        return str(tietype)

def tie_id_str(tie_id):
    return (direction_str(tie_id.direction) + ":" +
            str(tie_id.originator) + ":" +
            tietype_str(tie_id.tietype) + ":" +
            str(tie_id.tie_nr))

HIERARCHY_INDICATIONS_TO_STR = {
    common.ttypes.HierarchyIndications.leaf_only: "LeafOnly",
    common.ttypes.HierarchyIndications.leaf_only_and_leaf_2_leaf_procedures: "LeafToLeaf",
    common.ttypes.HierarchyIndications.top_of_fabric: "TopOfFabric",
}

def hierarchy_indications_str(hierarchy_indications):
    if hierarchy_indications in HIERARCHY_INDICATIONS_TO_STR:
        return HIERARCHY_INDICATIONS_TO_STR[hierarchy_indications]
    else:
        return str(hierarchy_indications)

def bandwidth_str(bandwidth):
    return str(bandwidth) + " Mbps"

def link_id_pair_str(link_id_pair):
    return str(link_id_pair.local_id) + "-" + str(link_id_pair.remote_id)

def node_element_str(element):
    lines = []
    if element.name is not None:
        lines.append("Name: " + str(element.name))
    lines.append("Level: " + str(element.level))
    if element.flags is not None:
        lines.append("Flags:")
        if element.flags.overload is not None:
            lines.append("  Overload: " + str(element.flags.overload))
    if element.capabilities is not None:
        lines.append("Capabilities:")
        if element.capabilities.flood_reduction is not None:
            lines.append("  Flood reduction: " + str(element.capabilities.flood_reduction))
        if element.capabilities.hierarchy_indications is not None:
            lines.append("  Leaf indications: " +
                         hierarchy_indications_str(element.capabilities.hierarchy_indications))
    sorted_neighbors = sortedcontainers.SortedDict(element.neighbors)
    for system_id, neighbor in sorted_neighbors.items():
        lines.append("Neighbor: " + utils.system_id_str(system_id))
        lines.append("  Level: " + str(neighbor.level))
        if neighbor.cost is not None:
            lines.append("  Cost: " + str(neighbor.cost))
        if neighbor.bandwidth is not None:
            lines.append("  Bandwidth: " + bandwidth_str(neighbor.bandwidth))
        if neighbor.link_ids is not None:
            sorted_link_ids = sorted(neighbor.link_ids)
            for link_id_pair in sorted_link_ids:
                lines.append("  Link: " + link_id_pair_str(link_id_pair))
    return lines

def prefixes_str(label_str, prefixes):
    lines = []
    sorted_prefixes = sortedcontainers.SortedDict(prefixes.prefixes)
    for prefix, attributes in sorted_prefixes.items():
        line = label_str + ' ' + ip_prefix_str(prefix)
        lines.append(line)
        if attributes:
            if attributes.metric:
                line = "  Metric: " + str(attributes.metric)
                lines.append(line)
            if attributes.tags:
                for tag in attributes.tags:
                    line = "  Tag: " + str(tag)
                    lines.append(line)
            if attributes.monotonic_clock:
                line = "  Monotonic-clock: " + str(attributes.monotonic_clock)
                lines.append(line)
    return lines

def pg_prefix_element_str(_element):
    # TODO: Implement this
    return "TODO"

def key_value_element_str(_element):
    # TODO: Implement this
    return "TODO"

def unknown_element_str(_element):
    # TODO: Implement this
    return "TODO"

def element_str(tietype, element):
    if tietype == common.ttypes.TIETypeType.NodeTIEType:
        return node_element_str(element.node)
    elif tietype == common.ttypes.TIETypeType.PrefixTIEType:
        return prefixes_str("Prefix:", element.prefixes)
    elif tietype == common.ttypes.TIETypeType.PositiveDisaggregationPrefixTIEType:
        return prefixes_str("Pos-Dis-Prefix:", element.positive_disaggregation_prefixes)
    elif tietype == common.ttypes.TIETypeType.NegativeDisaggregationPrefixTIEType:
        return prefixes_str("Neg-Dis-Prefix:", element.negative_disaggregation_prefixes)
    elif tietype == common.ttypes.TIETypeType.PGPrefixTIEType:
        # TODO: PG Prefixes not yet in model
        return unknown_element_str(element)
    elif tietype == common.ttypes.TIETypeType.KeyValueTIEType:
        return key_value_element_str(element.keyvalues)
    elif tietype == common.ttypes.TIETypeType.ExternalPrefixTIEType:
        return prefixes_str("Ext-Prefix:", element.external_prefixes)
    else:
        return unknown_element_str(element)

def assert_prefix_address_family(prefix, address_family):
    assert isinstance(prefix, common.ttypes.IPPrefixType)
    if address_family == constants.ADDRESS_FAMILY_IPV4:
        assert prefix.ipv4prefix is not None
        assert prefix.ipv6prefix is None
    elif address_family == constants.ADDRESS_FAMILY_IPV6:
        assert prefix.ipv4prefix is None
        assert prefix.ipv6prefix is not None
    else:
        assert False
