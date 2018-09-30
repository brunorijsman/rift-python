import enum

import common.constants
import encoding.constants

RUN_AS_ROOT = False

END_LN = "\n" #Character mode Telnet
HISTORY = 40 # Recall Commands
BS = 8 # ASCII Backspace
ESC = 27 # ASCII ESC
ESC_UP = 65 # ASCII A  UP Arrow
ESC_DN = 66 # ASCII B  Down Arrow
ESC_RT = 67 # ASCII C  Right Arrow
ESC_LT = 68 # ASCII D  Left Arrow
CAP_O = 79 # ASCII O
CAP_P = 80 # ASCII O
DEL_SEQ_3 = 51 # ASCII 3
LEFT_SQB = 91 # ASCII [
DEL_SEQ_TILDE = 126 # ASCII Tilde
DEL = 127 # ASCII DEL
COMMAND = 255 # Command Delimiter
LEFT_ARROW = '1B5B44'
RIGHT_ARROW = '1B5B43'
BKSP_OVERWRITE = '082008'

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

class FloodingScope(enum.Enum):
    NORTH = 1
    SOUTH = 2
    EAST_WEST = 3
