import ipaddress
import sortedcontainers

import thrift.protocol.TBinaryProtocol
import thrift.transport.TTransport

import common.ttypes
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
    common.ttypes.IPPrefixType.__lt__ = (
        lambda self, other: ip_prefix_tup(self) < ip_prefix_tup(other))
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

def encode_protocol_packet(protocol_packet):
    # This assumes we only encode a protocol_packet once (because we change it in place)
    fix_prot_packet_before_encode(protocol_packet)
    transport_out = thrift.transport.TTransport.TMemoryBuffer()
    protocol_out = thrift.protocol.TBinaryProtocol.TBinaryProtocol(transport_out)
    protocol_packet.write(protocol_out)
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

def fix_value(value, size, encode):
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

def fix_packet(packet, fixes, encode):
    for fix in fixes:
        (field_name, do_what) = fix
        if field_name in vars(packet):
            value = getattr(packet, field_name)
            if value is None:
                pass
            elif isinstance(do_what, int):
                size = do_what
                new_value = fix_value(value, size, encode)
                setattr(packet, field_name, new_value)
            else:
                nested_fixes = do_what
                fix_packet(getattr(packet, field_name), nested_fixes, encode)

def fix_packet_before_encode(packet, fixes):
    fix_packet(packet, fixes, True)

def fix_packet_after_decode(packet, fixes):
    fix_packet(packet, fixes, False)

PROTOCOL_PACKET_FIXES = [
    ('header', [
        ('sender', 64),
        ('level', 16)]),
    ('content', [
        ('lie', [
            ('flood_port', 16),
            ('link_mtu_size', 32),
            ('neighbor', [
                ('originator', 64)]),
            ('pod', 32),
            ('label', 32)]),
        ('tide', [
            ('start_range', [
                ('originator', 64),
                ('tie_nr', 32)
            ]),
            ('end_range', [
                ('originator', 64),
                ('tie_nr', 32)
            ]),
        ]),           # TODO also fields in headers list (e.g. seq_nr)
        ('tire', []),           # TODO
        ('tie', [])])]          # TODO

# TODO: Should we also fix link_id (not mentioned in the specification)?
# TODO: Should we also fix remote_id (not mentioned in the specification)?
# TODO: Should we also fix nonce (not mentioned in the specification)?
# TODO: Should we also fix holdtime (not mentioned in the specification)?

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

def make_tie_header(direction, originator, tie_type, tie_nr, seq_nr, lifetime):
    # TODO: Add support for origination_time
    tie_id = make_tie_id(direction, originator, tie_type, tie_nr)
    tie_header = encoding.ttypes.TIEHeader(
        tieid=tie_id,
        seq_nr=seq_nr,
        remaining_lifetime=lifetime,
        origination_time=None)
    return tie_header

def make_prefix_tie(sender, level, direction, originator, tie_nr, seq_nr, lifetime):
    # pylint:disable=too-many-locals
    tie_type = common.ttypes.TIETypeType.PrefixTIEType
    tie_header = make_tie_header(direction, originator, tie_type, tie_nr, seq_nr, lifetime)
    prefixes = {}
    prefix_tie_element = encoding.ttypes.PrefixTIEElement(prefixes=prefixes)
    tie_element = encoding.ttypes.TIEElement(prefixes=prefix_tie_element)
    tie_packet = encoding.ttypes.TIEPacket(header=tie_header, element=tie_element)
    packet_header = encoding.ttypes.PacketHeader(sender=sender, level=level)
    packet_content = encoding.ttypes.PacketContent(tie=tie_packet)
    protocol_packet = encoding.ttypes.ProtocolPacket(header=packet_header, content=packet_content)
    return protocol_packet

def add_ipv4_prefix_to_prefix_tie(protocol_packet, ipv4_prefix_string, metric, tags=None,
                                  monotonic_clock=None):
    ipv4_network = ipaddress.IPv4Network(ipv4_prefix_string)
    address = ipv4_network.network_address.packed
    prefixlen = ipv4_network.prefixlen
    ipv4_prefix = common.ttypes.IPv4PrefixType(address, prefixlen)
    prefix = common.ttypes.IPPrefixType(ipv4prefix=ipv4_prefix)
    attributes = encoding.ttypes.PrefixAttributes(metric=metric,
                                                  tags=tags,
                                                  monotonic_clock=monotonic_clock)
    protocol_packet.content.tie.element.prefixes.prefixes[prefix] = attributes

def add_ipv6_prefix_to_prefix_tie(protocol_packet, ipv6_prefix_string, metric, tags=None,
                                  monotonic_clock=None):
    ipv6_network = ipaddress.IPv6Network(ipv6_prefix_string)
    address = ipv6_network.network_address.packed
    prefixlen = ipv6_network.prefixlen
    ipv6_prefix = common.ttypes.IPv6PrefixType(address, prefixlen)
    prefix = common.ttypes.IPPrefixType(ipv6prefix=ipv6_prefix)
    attributes = encoding.ttypes.PrefixAttributes(metric=metric,
                                                  tags=tags,
                                                  monotonic_clock=monotonic_clock)
    protocol_packet.content.tie.element.prefixes.prefixes[prefix] = attributes

def make_node_tie(sender, name, level, direction, originator, tie_nr, seq_nr, lifetime):
    # pylint:disable=too-many-locals
    tie_type = common.ttypes.TIETypeType.NodeTIEType
    tie_header = make_tie_header(direction, originator, tie_type, tie_nr, seq_nr, lifetime)
    node_tie_element = encoding.ttypes.NodeTIEElement(
        level=level,
        neighbors={},
        capabilities=None,  ##@@ TODO: Implement this
        flags=None,         ##@@ TODO: Implement this
        name=name,
        visible_in_same_level=set(()),                 # TODO: Implement this
        same_level_unknown_north_partitions=set(()))   # TODO: Implement this
    tie_element = encoding.ttypes.TIEElement(node=node_tie_element)
    tie_packet = encoding.ttypes.TIEPacket(header=tie_header, element=tie_element)
    packet_header = encoding.ttypes.PacketHeader(sender=sender, level=level)
    packet_content = encoding.ttypes.PacketContent(tie=tie_packet)
    protocol_packet = encoding.ttypes.ProtocolPacket(header=packet_header, content=packet_content)
    return protocol_packet

def make_node_neighbor(level):
    # TODO: Add support for multiple parallel links (link_ids has more than one element)
    node_neighbor = encoding.ttypes.NodeNeighborsTIEElement(
        level=level,
        cost=1,             # TODO: Implement this. Take cost from configuration file.
        link_ids=None,      # TODO: ##@@ Implement
        bandwidth=100)      # TODO: Implement this. Use actual bandwidth of link.
    return node_neighbor

def make_tide(sender, level, start_range, end_range):
    tide_packet = encoding.ttypes.TIDEPacket(start_range=start_range,
                                             end_range=end_range,
                                             headers=[])
    packet_header = encoding.ttypes.PacketHeader(sender=sender, level=level)
    packet_content = encoding.ttypes.PacketContent(tide=tide_packet)
    protocol_packet = encoding.ttypes.ProtocolPacket(header=packet_header, content=packet_content)
    return protocol_packet

def add_tie_header_to_tide(protocol_packet, tie_header):
    protocol_packet.content.tide.headers.append(tie_header)

def make_tire(sender, level):
    tire_packet = encoding.ttypes.TIREPacket(headers=[])
    packet_header = encoding.ttypes.PacketHeader(sender=sender, level=level)
    packet_content = encoding.ttypes.PacketContent(tire=tire_packet)
    protocol_packet = encoding.ttypes.ProtocolPacket(header=packet_header, content=packet_content)
    return protocol_packet

def add_tie_header_to_tire(protocol_packet, tie_header):
    protocol_packet.content.tire.headers.append(tie_header)

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
    common.ttypes.TIETypeType.TransitivePrefixTIEType: "TransitivePrefix",
    common.ttypes.TIETypeType.PGPrefixTIEType: "PolicyGuidedPrefix",
    common.ttypes.TIETypeType.KeyValueTIEType: "KeyValue"
}

def tietype_str(tietype):
    if tietype in TIETYPE_TO_STR:
        return TIETYPE_TO_STR[tietype]
    else:
        return str(tietype)

LEAF_INDICATIONS_TO_STR = {
    common.ttypes.LeafIndications.leaf_only: "LeafOnly",
    common.ttypes.LeafIndications.leaf_only_and_leaf_2_leaf_procedures: "LeafToLeaf",
}

def leaf_indications_str(leaf_indications):
    if leaf_indications in LEAF_INDICATIONS_TO_STR:
        return LEAF_INDICATIONS_TO_STR[leaf_indications]
    else:
        return str(leaf_indications)

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
        if element.capabilities.leaf_indications is not None:
            lines.append("  Leaf indications: " +
                         leaf_indications_str(element.capabilities.leaf_indications))
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

    if element.visible_in_same_level:
        lines.append("Visible in same level:")
        sorted_system_ids = sorted(element.visible_in_same_level)
        for system_id in sorted_system_ids:
            lines.append("  System ID: " + utils.system_id_str(system_id))
    if element.same_level_unknown_north_partitions:
        lines.append("Same level unknown north partitions:")
        sorted_system_ids = sorted(element.same_level_unknown_north_partitions)
        for system_id in sorted_system_ids:
            lines.append("  System ID: " + utils.system_id_str(system_id))
    return lines

def prefix_element_str(element):
    lines = []
    sorted_prefixes = sortedcontainers.SortedDict(element.prefixes)
    for prefix, attributes in sorted_prefixes.items():
        line = "Prefix: " + ip_prefix_str(prefix)
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

def transitive_prefix_element_str(_element):
    # TODO: Implement this
    return "TODO"

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
        return prefix_element_str(element.prefixes)
    elif tietype == common.ttypes.TIETypeType.TransitivePrefixTIEType:
        return transitive_prefix_element_str(element.transitive_prefixes)
    elif tietype == common.ttypes.TIETypeType.PGPrefixTIEType:
        return pg_prefix_element_str(element)   # TODO
    elif tietype == common.ttypes.TIETypeType.KeyValueTIEType:
        return key_value_element_str(element.keyvalues)
    else:
        return unknown_element_str(element)
