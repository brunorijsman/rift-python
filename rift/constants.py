import enum

import common.constants
import encoding.constants

RUN_AS_ROOT = False

RIFT_MAJOR_VERSION = encoding.constants.protocol_major_version
RIFT_MINOR_VERSION = encoding.constants.protocol_minor_version
DEFAULT_LIE_IPV4_MCAST_ADDRESS = '224.0.0.120'
DEFAULT_LIE_IPV6_MCAST_ADDRESS = 'FF02::0078'
DEFAULT_LIE_SEND_INTERVAL_SECS = 1.0
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

def address_family_str(address_family):
    if address_family == ADDRESS_FAMILY_IPV4:
        return "IPv4"
    else:
        assert address_family == ADDRESS_FAMILY_IPV6
        return "IPv6"
