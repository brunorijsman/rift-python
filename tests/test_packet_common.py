import common.ttypes
import packet_common

def test_direction_str():
    assert packet_common.direction_str(common.ttypes.TieDirectionType.South) == "South"
    assert packet_common.direction_str(common.ttypes.TieDirectionType.North) == "North"
    assert packet_common.direction_str(999) == "999"

def test_tietype_str():
    assert packet_common.tietype_str(common.ttypes.TIETypeType.NodeTIEType) == "Node"
    assert packet_common.tietype_str(common.ttypes.TIETypeType.PrefixTIEType) == "Prefix"
    assert (packet_common.tietype_str(common.ttypes.TIETypeType.PositiveDisaggregationPrefixTIEType) ==
            "PositiveDisaggregationPrefix")
    assert (packet_common.tietype_str(common.ttypes.TIETypeType.PGPrefixTIEType) ==
            "PolicyGuidedPrefix")
    assert packet_common.tietype_str(common.ttypes.TIETypeType.KeyValueTIEType) == "KeyValue"
    assert packet_common.tietype_str(888) == "888"
