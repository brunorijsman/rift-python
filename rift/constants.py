import enum

import common.constants
import encoding.constants

RUN_AS_ROOT = False

RIFT_MAJOR_VERSION = encoding.constants.protocol_major_version
RIFT_MINOR_VERSION = encoding.constants.protocol_minor_version
DEFAULT_LIE_IPV4_MCAST_ADDRESS = '224.0.0.120'
DEFAULT_LIE_IPV6_MCAST_ADDRESS = 'FF02::0078'
DEFAULT_LIE_SEND_INTERVAL_SECS = 1.0
DEFAULT_FLOODING_REDUCTION_REDUNDANCY = 2
DEFAULT_FLOODING_REDUCTION_SIMILARITY = 2
if RUN_AS_ROOT:
    DEFAULT_LIE_PORT = common.constants.default_lie_udp_port
    DEFAULT_TIE_PORT = common.constants.default_tie_udp_flood_port
else:
    DEFAULT_LIE_PORT = 10000
    DEFAULT_TIE_PORT = 10001

class ActiveNodes(enum.Enum):
    ALL_NODES = 1
    ONLY_PASSIVE_NODES = 2
    ALL_NODES_EXCEPT_PASSIVE_NODES = 3

DIR_SOUTH = common.ttypes.TieDirectionType.South
DIR_NORTH = common.ttypes.TieDirectionType.North
DIR_EAST_WEST = common.ttypes.TieDirectionType.DirectionMaxValue   # Only used internally

def reverse_dir(direction):
    if direction == DIR_SOUTH:
        return DIR_NORTH
    elif direction == DIR_NORTH:
        return DIR_SOUTH
    else:
        assert direction == DIR_EAST_WEST
        return DIR_EAST_WEST

def direction_str(direction):
    if direction == DIR_SOUTH:
        return "South"
    elif direction == DIR_NORTH:
        return "North"
    else:
        assert direction == DIR_EAST_WEST
        return "East-West"

ADDRESS_FAMILY_IPV4 = 1
ADDRESS_FAMILY_IPV6 = 2
ADDRESS_FAMILIES = [ADDRESS_FAMILY_IPV4, ADDRESS_FAMILY_IPV6]

def address_family_str(address_family):
    if address_family == ADDRESS_FAMILY_IPV4:
        return "IPv4"
    else:
        assert address_family == ADDRESS_FAMILY_IPV6
        return "IPv6"

PACKET_TYPE_LIE = 1
PACKET_TYPE_TIE = 2
PACKET_TYPE_TIDE = 3
PACKET_TYPE_TIRE = 4
PACKET_TYPES = [PACKET_TYPE_LIE, PACKET_TYPE_TIE, PACKET_TYPE_TIDE, PACKET_TYPE_TIRE]

def packet_type_str(packet_type):
    if packet_type == PACKET_TYPE_LIE:
        return "LIE"
    elif packet_type == PACKET_TYPE_TIE:
        return "TIE"
    elif packet_type == PACKET_TYPE_TIDE:
        return "TIDE"
    else:
        assert packet_type == PACKET_TYPE_TIRE
        return "TIRE"

OWNER_S_SPF = 2
OWNER_N_SPF = 1

def owner_str(owner):
    if owner == OWNER_S_SPF:
        return "South SPF"
    else:
        assert owner == OWNER_N_SPF
        return "North SPF"

DISAGG_POS_AND_NEG = 1
DISAGG_POS_ONLY = 2
DISAGG_NEG_ONLY = 3

def disagg_str(disagg):
    if disagg == DISAGG_POS_AND_NEG:
        return "positive-and-negative"
    elif disagg == DISAGG_POS_ONLY:
        return "positive-only"
    else:
        assert disagg == DISAGG_NEG_ONLY
        return "negative-only"

def disagg_from_str(str_value):
    lower_str = str_value.lower()
    if lower_str == "positive-and-negative":
        return DISAGG_POS_AND_NEG
    elif lower_str == "positive-only":
        return DISAGG_POS_ONLY
    else:
        assert lower_str == "negative-only"
        return DISAGG_NEG_ONLY
