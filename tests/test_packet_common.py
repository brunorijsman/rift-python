import common.ttypes
import packet_common

import encoding.ttypes

# Allow long names for test functions
# pylint: disable=invalid-name

def test_direction_str():
    assert packet_common.direction_str(common.ttypes.TieDirectionType.South) == "South"
    assert packet_common.direction_str(common.ttypes.TieDirectionType.North) == "North"
    assert packet_common.direction_str(999) == "999"

def test_tietype_str():
    assert packet_common.tietype_str(common.ttypes.TIETypeType.NodeTIEType) == "Node"
    assert packet_common.tietype_str(common.ttypes.TIETypeType.PrefixTIEType) == "Prefix"
    assert (packet_common.tietype_str(
        common.ttypes.TIETypeType.PositiveDisaggregationPrefixTIEType) == "Pos-Dis-Prefix")
    assert packet_common.tietype_str(common.ttypes.TIETypeType.PGPrefixTIEType) == "PG-Prefix"
    assert packet_common.tietype_str(common.ttypes.TIETypeType.KeyValueTIEType) == "Key-Value"
    assert packet_common.tietype_str(888) == "888"

def max_system_id(fudge=0):
    return packet_common.MAX_U64 - fudge

def max_tieid():
    return encoding.ttypes.TIEID(
        direction=common.ttypes.TieDirectionType.North,
        originator=packet_common.MAX_U64,
        tietype=common.ttypes.TIETypeType.ExternalPrefixTIEType,
        tie_nr=packet_common.MAX_U32
    )

def max_tie_header(fudge=0):
    return encoding.ttypes.TIEHeader(
        tieid=max_tieid(),
        seq_nr=packet_common.MAX_U32 - fudge,
        # remaining_lifetime=packet_common.MAX_U32 - 1,    # Actual max is not allowed
        origination_time=common.ttypes.IEEE802_1ASTimeStampType(
            AS_sec=packet_common.MAX_U64,
            AS_nsec=packet_common.MAX_U32
        ),
        origination_lifetime=packet_common.MAX_U32
    )

def max_tie_header_with_lifetime(fudge=0):
    return encoding.ttypes.TIEHeaderWithLifeTime(
        header=max_tie_header(fudge),
        remaining_lifetime=packet_common.MAX_U32 - 1,    # Actual max is not allowed
    )

def max_link_id(fudge=0):
    return packet_common.MAX_U32 - fudge

def max_link_id_pair(fudge=0):
    return encoding.ttypes.LinkIDPair(
        local_id=max_link_id(fudge),
        remote_id=max_link_id(fudge)
    )

def max_neighbor():
    return encoding.ttypes.NodeNeighborsTIEElement(
        level=packet_common.MAX_U16,
        cost=packet_common.MAX_U32,
        link_ids=set([
            max_link_id_pair(0),
            max_link_id_pair(1),
            max_link_id_pair(2),
        ]),
        bandwidth=packet_common.MAX_U32
    )

def max_ipv4_prefix(fudge=0):
    return common.ttypes.IPPrefixType(
        ipv4prefix=common.ttypes.IPv4PrefixType(
            address=packet_common.MAX_U32 - fudge,
            prefixlen=packet_common.MAX_U8
        ),
        ipv6prefix=None
    )

def max_ipv6_prefix():
    return common.ttypes.IPPrefixType(
        ipv4prefix=None,
        ipv6prefix=common.ttypes.IPv6PrefixType(
            address=b'ffffffffffffffffffffffffffffffff',
            prefixlen=packet_common.MAX_U8
        )
    )

def max_prefix_attributes():
    return encoding.ttypes.PrefixAttributes(
        metric=packet_common.MAX_U32,
        tags=set([
            packet_common.MAX_U32,
            packet_common.MAX_U32 - 1,
            packet_common.MAX_U32 - 2
        ]),
        monotonic_clock=common.ttypes.PrefixSequenceType(
            timestamp=common.ttypes.IEEE802_1ASTimeStampType(
                AS_sec=packet_common.MAX_U64,
                AS_nsec=packet_common.MAX_U32
            ),
            transactionid=packet_common.MAX_U8
        )
    )

def max_prefix_tie_element():
    return encoding.ttypes.PrefixTIEElement(
        prefixes={
            max_ipv4_prefix(0): max_prefix_attributes(),
            max_ipv4_prefix(1): max_prefix_attributes(),
            max_ipv6_prefix(): max_prefix_attributes(),
        }
    )

def test_fix_lie_packet():
    packet_common.add_missing_methods_to_thrift()
    lie_protocol_packet = encoding.ttypes.ProtocolPacket(
        header=encoding.ttypes.PacketHeader(
            major_version=packet_common.MAX_U16,
            minor_version=packet_common.MAX_U16,
            sender=packet_common.MAX_U64,
            level=packet_common.MAX_U16
        ),
        content=encoding.ttypes.PacketContent(
            lie=encoding.ttypes.LIEPacket(
                name="name",
                local_id=packet_common.MAX_U32,
                flood_port=packet_common.MAX_U16,
                link_mtu_size=packet_common.MAX_U32,
                link_bandwidth=packet_common.MAX_U32,
                neighbor=encoding.ttypes.Neighbor(
                    originator=packet_common.MAX_U64,
                    remote_id=packet_common.MAX_U32
                ),
                pod=packet_common.MAX_U32,
                # nonce=packet_common.MAX_U16,
                # last_neighbor_nonce=packet_common.MAX_U16,
                node_capabilities=encoding.ttypes.NodeCapabilities(
                    flood_reduction=True,
                    hierarchy_indications=common.ttypes.HierarchyIndications.leaf_only
                ),
                link_capabilities=encoding.ttypes.LinkCapabilities(
                    bfd=False,
                ),
                holdtime=packet_common.MAX_U16,
                not_a_ztp_offer=True,
                you_are_flood_repeater=True,
                label=packet_common.MAX_U32
            ),
            tide=None,
            tire=None,
            tie=None
        )
    )
    packet_info = packet_common.encode_protocol_packet(lie_protocol_packet, None)
    packet_info.update_env_header(0)
    packet_info.update_outer_sec_env_header(None, 111, 222)
    message = b''.join(packet_info.message_parts())
    decoded_packet_info = packet_common.decode_message(None, None, message, None, None)
    assert not decoded_packet_info.error
    assert packet_info.protocol_packet == decoded_packet_info.protocol_packet

def test_fix_tide_packet():
    packet_common.add_missing_methods_to_thrift()
    tide_protocol_packet = encoding.ttypes.ProtocolPacket(
        header=encoding.ttypes.PacketHeader(
            major_version=packet_common.MAX_U16,
            minor_version=packet_common.MAX_U16,
            sender=packet_common.MAX_U64,
            level=packet_common.MAX_U16
        ),
        content=encoding.ttypes.PacketContent(
            lie=None,
            tide=encoding.ttypes.TIDEPacket(
                start_range=max_tieid(),
                end_range=max_tieid(),
                headers=[
                    max_tie_header_with_lifetime(),
                    max_tie_header_with_lifetime(),
                    max_tie_header_with_lifetime()
                ]
            ),
            tire=None,
            tie=None
        )
    )
    packet_info = packet_common.encode_protocol_packet(tide_protocol_packet, None)
    packet_info.update_env_header(0)
    packet_info.update_outer_sec_env_header(None, 111, 222)
    message = b''.join(packet_info.message_parts())
    decoded_packet_info = packet_common.decode_message(None, None, message, None, None)
    assert not decoded_packet_info.error
    assert packet_info.protocol_packet == decoded_packet_info.protocol_packet

def test_fix_tire_packet():
    packet_common.add_missing_methods_to_thrift()
    tire_protocol_packet = encoding.ttypes.ProtocolPacket(
        header=encoding.ttypes.PacketHeader(
            major_version=packet_common.MAX_U16,
            minor_version=packet_common.MAX_U16,
            sender=packet_common.MAX_U64,
            level=packet_common.MAX_U16
        ),
        content=encoding.ttypes.PacketContent(
            lie=None,
            tide=None,
            tire=encoding.ttypes.TIREPacket(
                headers=set([
                    max_tie_header(0),
                    max_tie_header(1),
                    max_tie_header(2)
                ])
            ),
            tie=None
        )
    )
    packet_info = packet_common.encode_protocol_packet(tire_protocol_packet, None)
    packet_info.update_env_header(0)
    packet_info.update_outer_sec_env_header(None, 111, 222)
    message = b''.join(packet_info.message_parts())
    decoded_packet_info = packet_common.decode_message(None, None, message, None, None)
    assert not decoded_packet_info.error
    assert packet_info.protocol_packet == decoded_packet_info.protocol_packet

def test_fix_node_tie_packet():
    packet_common.add_missing_methods_to_thrift()
    tie_protocol_packet = encoding.ttypes.ProtocolPacket(
        header=encoding.ttypes.PacketHeader(
            major_version=packet_common.MAX_U16,
            minor_version=packet_common.MAX_U16,
            sender=packet_common.MAX_U64,
            level=packet_common.MAX_U16
        ),
        content=encoding.ttypes.PacketContent(
            lie=None,
            tide=None,
            tire=None,
            tie=encoding.ttypes.TIEPacket(
                header=max_tie_header(),
                element=encoding.ttypes.TIEElement(
                    node=encoding.ttypes.NodeTIEElement(
                        level=packet_common.MAX_U16,
                        neighbors={
                            max_system_id(0): max_neighbor(),
                            max_system_id(1): max_neighbor(),
                            max_system_id(2): max_neighbor()
                        },
                        capabilities=encoding.ttypes.NodeCapabilities(
                            flood_reduction=True,
                            hierarchy_indications=common.ttypes.HierarchyIndications.leaf_only
                        ),
                        flags=encoding.ttypes.NodeFlags(
                            overload=True
                        ),
                        name="name"
                    ),
                    prefixes=None,
                    positive_disaggregation_prefixes=None,
                    negative_disaggregation_prefixes=None,
                    external_prefixes=None,
                    keyvalues=None
                )
            )
        )
    )
    packet_info = packet_common.encode_protocol_packet(tie_protocol_packet, None)
    packet_info.update_env_header(0)
    packet_info.update_outer_sec_env_header(None, 111, 222)
    message = b''.join(packet_info.message_parts())
    decoded_packet_info = packet_common.decode_message(None, None, message, None, None)
    assert not decoded_packet_info.error
    assert packet_info.protocol_packet == decoded_packet_info.protocol_packet

def test_fix_prefixes_tie_packet():
    packet_common.add_missing_methods_to_thrift()
    tie_protocol_packet = encoding.ttypes.ProtocolPacket(
        header=encoding.ttypes.PacketHeader(
            major_version=packet_common.MAX_U16,
            minor_version=packet_common.MAX_U16,
            sender=packet_common.MAX_U64,
            level=packet_common.MAX_U16
        ),
        content=encoding.ttypes.PacketContent(
            lie=None,
            tide=None,
            tire=None,
            tie=encoding.ttypes.TIEPacket(
                header=max_tie_header(),
                element=encoding.ttypes.TIEElement(
                    node=None,
                    prefixes=max_prefix_tie_element(),
                    positive_disaggregation_prefixes=None,
                    negative_disaggregation_prefixes=None,
                    external_prefixes=None,
                    keyvalues=None
                )
            )
        )
    )
    packet_info = packet_common.encode_protocol_packet(tie_protocol_packet, None)
    packet_info.update_env_header(0)
    packet_info.update_outer_sec_env_header(None, 111, 222)
    message = b''.join(packet_info.message_parts())
    decoded_packet_info = packet_common.decode_message(None, None, message, None, None)
    assert not decoded_packet_info.error
    assert packet_info.protocol_packet == decoded_packet_info.protocol_packet

def test_fix_positive_disaggregation_prefixes_tie_packet():
    packet_common.add_missing_methods_to_thrift()
    tie_protocol_packet = encoding.ttypes.ProtocolPacket(
        header=encoding.ttypes.PacketHeader(
            major_version=packet_common.MAX_U16,
            minor_version=packet_common.MAX_U16,
            sender=packet_common.MAX_U64,
            level=packet_common.MAX_U16
        ),
        content=encoding.ttypes.PacketContent(
            lie=None,
            tide=None,
            tire=None,
            tie=encoding.ttypes.TIEPacket(
                header=max_tie_header(),
                element=encoding.ttypes.TIEElement(
                    node=None,
                    prefixes=None,
                    positive_disaggregation_prefixes=max_prefix_tie_element(),
                    negative_disaggregation_prefixes=None,
                    external_prefixes=None,
                    keyvalues=None
                )
            )
        )
    )
    packet_info = packet_common.encode_protocol_packet(tie_protocol_packet, None)
    packet_info.update_env_header(0)
    packet_info.update_outer_sec_env_header(None, 111, 222)
    message = b''.join(packet_info.message_parts())
    decoded_packet_info = packet_common.decode_message(None, None, message, None, None)
    assert not decoded_packet_info.error
    assert packet_info.protocol_packet == decoded_packet_info.protocol_packet

def test_fix_negative_disaggregation_prefixes_tie_packet():
    packet_common.add_missing_methods_to_thrift()
    tie_protocol_packet = encoding.ttypes.ProtocolPacket(
        header=encoding.ttypes.PacketHeader(
            major_version=packet_common.MAX_U16,
            minor_version=packet_common.MAX_U16,
            sender=packet_common.MAX_U64,
            level=packet_common.MAX_U16
        ),
        content=encoding.ttypes.PacketContent(
            lie=None,
            tide=None,
            tire=None,
            tie=encoding.ttypes.TIEPacket(
                header=max_tie_header(),
                element=encoding.ttypes.TIEElement(
                    node=None,
                    prefixes=None,
                    positive_disaggregation_prefixes=None,
                    negative_disaggregation_prefixes=max_prefix_tie_element(),
                    external_prefixes=None,
                    keyvalues=None
                )
            )
        )
    )
    packet_info = packet_common.encode_protocol_packet(tie_protocol_packet, None)
    packet_info.update_env_header(0)
    packet_info.update_outer_sec_env_header(None, 111, 222)
    message = b''.join(packet_info.message_parts())
    decoded_packet_info = packet_common.decode_message(None, None, message, None, None)
    assert not decoded_packet_info.error
    assert packet_info.protocol_packet == decoded_packet_info.protocol_packet

def test_fix_external_prefixes_tie_packet():
    packet_common.add_missing_methods_to_thrift()
    tie_protocol_packet = encoding.ttypes.ProtocolPacket(
        header=encoding.ttypes.PacketHeader(
            major_version=packet_common.MAX_U16,
            minor_version=packet_common.MAX_U16,
            sender=packet_common.MAX_U64,
            level=packet_common.MAX_U16
        ),
        content=encoding.ttypes.PacketContent(
            lie=None,
            tide=None,
            tire=None,
            tie=encoding.ttypes.TIEPacket(
                header=max_tie_header(),
                element=encoding.ttypes.TIEElement(
                    node=None,
                    prefixes=None,
                    positive_disaggregation_prefixes=None,
                    negative_disaggregation_prefixes=None,
                    external_prefixes=max_prefix_tie_element(),
                    keyvalues=None
                )
            )
        )
    )
    packet_info = packet_common.encode_protocol_packet(tie_protocol_packet, None)
    packet_info.update_env_header(0)
    packet_info.update_outer_sec_env_header(None, 111, 222)
    message = b''.join(packet_info.message_parts())
    decoded_packet_info = packet_common.decode_message(None, None, message, None, None)
    assert not decoded_packet_info.error
    assert packet_info.protocol_packet == decoded_packet_info.protocol_packet

def test_fix_key_value_tie_packet():
    packet_common.add_missing_methods_to_thrift()
    tie_protocol_packet = encoding.ttypes.ProtocolPacket(
        header=encoding.ttypes.PacketHeader(
            major_version=packet_common.MAX_U16,
            minor_version=packet_common.MAX_U16,
            sender=packet_common.MAX_U64,
            level=packet_common.MAX_U16
        ),
        content=encoding.ttypes.PacketContent(
            lie=None,
            tide=None,
            tire=None,
            tie=encoding.ttypes.TIEPacket(
                header=max_tie_header(),
                element=encoding.ttypes.TIEElement(
                    node=None,
                    prefixes=None,
                    positive_disaggregation_prefixes=None,
                    negative_disaggregation_prefixes=None,
                    external_prefixes=None,
                    keyvalues=encoding.ttypes.KeyValueTIEElement(
                        keyvalues={
                            "one": "een",
                            "two": "twee"
                        }
                    )
                )
            )
        )
    )
    packet_info = packet_common.encode_protocol_packet(tie_protocol_packet, None)
    packet_info.update_env_header(0)
    packet_info.update_outer_sec_env_header(None, 111, 222)
    message = b''.join(packet_info.message_parts())
    decoded_packet_info = packet_common.decode_message(None, None, message, None, None)
    assert not decoded_packet_info.error
    assert packet_info.protocol_packet == decoded_packet_info.protocol_packet
