import sys
sys.path.append('rift/gen-py')

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
    