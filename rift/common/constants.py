#
#
# $Id
#
# Copyright (c) 2021, Juniper Networks, Inc.
# All rights reserved.
#
#
#
# Autogenerated by Thrift Compiler (1.0.0-dev)
#
# DO NOT EDIT UNLESS YOU ARE SURE THAT YOU KNOW WHAT YOU ARE DOING
#
#  options string: py
#

from thrift.Thrift import TType, TMessageType, TFrozenDict, TException, TApplicationException
from thrift.protocol.TProtocol import TProtocolException
import sys
from .ttypes import *
undefined_packet_number = 0
top_of_fabric_level = 24
default_bandwidth = 100
leaf_level = 0
default_level = 0
default_pod = 0
undefined_linkid = 0
invalid_key_value_key = 0
default_distance = 1
infinite_distance = 2147483647
invalid_distance = 0
overload_default = False
flood_reduction_default = True
default_lie_tx_interval = 1
default_lie_holdtime = 3
multiple_neighbors_lie_holdtime_multipler = 4
default_ztp_holdtime = 1
default_not_a_ztp_offer = False
default_you_are_flood_repeater = True
IllegalSystemID = 0
empty_set_of_nodeids = set((
))
default_lifetime = 604800
purge_lifetime = 300
rounddown_lifetime_interval = 60
lifetime_diff2ignore = 400
default_lie_udp_port = 914
default_tie_udp_flood_port = 915
default_mtu_size = 1400
bfd_default = True
keyvaluetarget_default = 0
keyvaluetarget_all_south_leaves = -1
undefined_nonce = 0
undefined_securitykey_id = 0
maximum_valid_nonce_delta = 5
nonce_regeneration_interval = 300
undefined_fabric_id = 0
default_fabric_id = 1
default_acting_auto_evpn_dci_when_tof = False
default_autoevpn_model = 0
AUTO_EVPN_SUPPORT_DEFAULT = False
default_autofr_model = 0
IllegalClusterID = 0
DefaultClusterID = 1
MinFloodReflectionPreference = 0
AUTO_FLOOD_REFLECTION_SUPPORT = False
