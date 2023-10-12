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

from thrift.transport import TTransport


class HierarchyIndications(object):
    """
    Flags indicating node configuration in case of ZTP.
    """
    leaf_only = 0
    leaf_only_and_leaf_2_leaf_procedures = 1
    top_of_fabric = 2

    _VALUES_TO_NAMES = {
        0: "leaf_only",
        1: "leaf_only_and_leaf_2_leaf_procedures",
        2: "top_of_fabric",
    }

    _NAMES_TO_VALUES = {
        "leaf_only": 0,
        "leaf_only_and_leaf_2_leaf_procedures": 1,
        "top_of_fabric": 2,
    }


class TieDirectionType(object):
    """
    Direction of TIEs.
    """
    Illegal = 0
    South = 1
    North = 2
    DirectionMaxValue = 3

    _VALUES_TO_NAMES = {
        0: "Illegal",
        1: "South",
        2: "North",
        3: "DirectionMaxValue",
    }

    _NAMES_TO_VALUES = {
        "Illegal": 0,
        "South": 1,
        "North": 2,
        "DirectionMaxValue": 3,
    }


class AddressFamilyType(object):
    """
    Address family type.
    """
    Illegal = 0
    AddressFamilyMinValue = 1
    IPv4 = 2
    IPv6 = 3
    AddressFamilyMaxValue = 4

    _VALUES_TO_NAMES = {
        0: "Illegal",
        1: "AddressFamilyMinValue",
        2: "IPv4",
        3: "IPv6",
        4: "AddressFamilyMaxValue",
    }

    _NAMES_TO_VALUES = {
        "Illegal": 0,
        "AddressFamilyMinValue": 1,
        "IPv4": 2,
        "IPv6": 3,
        "AddressFamilyMaxValue": 4,
    }


class TIETypeType(object):
    """
    Type of TIE.
    """
    Illegal = 0
    TIETypeMinValue = 1
    NodeTIEType = 2
    PrefixTIEType = 3
    PositiveDisaggregationPrefixTIEType = 4
    NegativeDisaggregationPrefixTIEType = 5
    PGPrefixTIEType = 6
    KeyValueTIEType = 7
    ExternalPrefixTIEType = 8
    PositiveExternalDisaggregationPrefixTIEType = 9
    TIETypeMaxValue = 10

    _VALUES_TO_NAMES = {
        0: "Illegal",
        1: "TIETypeMinValue",
        2: "NodeTIEType",
        3: "PrefixTIEType",
        4: "PositiveDisaggregationPrefixTIEType",
        5: "NegativeDisaggregationPrefixTIEType",
        6: "PGPrefixTIEType",
        7: "KeyValueTIEType",
        8: "ExternalPrefixTIEType",
        9: "PositiveExternalDisaggregationPrefixTIEType",
        10: "TIETypeMaxValue",
    }

    _NAMES_TO_VALUES = {
        "Illegal": 0,
        "TIETypeMinValue": 1,
        "NodeTIEType": 2,
        "PrefixTIEType": 3,
        "PositiveDisaggregationPrefixTIEType": 4,
        "NegativeDisaggregationPrefixTIEType": 5,
        "PGPrefixTIEType": 6,
        "KeyValueTIEType": 7,
        "ExternalPrefixTIEType": 8,
        "PositiveExternalDisaggregationPrefixTIEType": 9,
        "TIETypeMaxValue": 10,
    }


class RouteType(object):
    """
    RIFT route types.
    @note: The only purpose of those values is to introduce an
           ordering whereas an implementation can choose internally
           any other values as long the ordering is preserved
    """
    Illegal = 0
    RouteTypeMinValue = 1
    Discard = 2
    LocalPrefix = 3
    SouthPGPPrefix = 4
    NorthPGPPrefix = 5
    NorthPrefix = 6
    NorthExternalPrefix = 7
    SouthPrefix = 8
    SouthExternalPrefix = 9
    NegativeSouthPrefix = 10
    RouteTypeMaxValue = 11

    _VALUES_TO_NAMES = {
        0: "Illegal",
        1: "RouteTypeMinValue",
        2: "Discard",
        3: "LocalPrefix",
        4: "SouthPGPPrefix",
        5: "NorthPGPPrefix",
        6: "NorthPrefix",
        7: "NorthExternalPrefix",
        8: "SouthPrefix",
        9: "SouthExternalPrefix",
        10: "NegativeSouthPrefix",
        11: "RouteTypeMaxValue",
    }

    _NAMES_TO_VALUES = {
        "Illegal": 0,
        "RouteTypeMinValue": 1,
        "Discard": 2,
        "LocalPrefix": 3,
        "SouthPGPPrefix": 4,
        "NorthPGPPrefix": 5,
        "NorthPrefix": 6,
        "NorthExternalPrefix": 7,
        "SouthPrefix": 8,
        "SouthExternalPrefix": 9,
        "NegativeSouthPrefix": 10,
        "RouteTypeMaxValue": 11,
    }


class KVTypes(object):
    Experimental = 1
    WellKnown = 2
    OUI = 3

    _VALUES_TO_NAMES = {
        1: "Experimental",
        2: "WellKnown",
        3: "OUI",
    }

    _NAMES_TO_VALUES = {
        "Experimental": 1,
        "WellKnown": 2,
        "OUI": 3,
    }


class AutoEVPNModel(object):
    ERB_VLAN_BUNDLE = 0

    _VALUES_TO_NAMES = {
        0: "ERB_VLAN_BUNDLE",
    }

    _NAMES_TO_VALUES = {
        "ERB_VLAN_BUNDLE": 0,
    }


class AutoFRModel(object):
    """
    <auto-flood-reflection>
    """
    NoTunnelMode = 0
    TunnelMode = 1

    _VALUES_TO_NAMES = {
        0: "NoTunnelMode",
        1: "TunnelMode",
    }

    _NAMES_TO_VALUES = {
        "NoTunnelMode": 0,
        "TunnelMode": 1,
    }


class IEEE802_1ASTimeStampType(object):
    """
    Timestamp per IEEE 802.1AS, all values MUST be interpreted in
    implementation as unsigned.

    Attributes:
     - AS_sec
     - AS_nsec
    """

    thrift_spec = (
        None,  # 0
        (1, TType.I64, 'AS_sec', None, None, ),  # 1
        (2, TType.I32, 'AS_nsec', None, None, ),  # 2
    )

    def __init__(self, AS_sec=None, AS_nsec=None,):
        self.AS_sec = AS_sec
        self.AS_nsec = AS_nsec

    def read(self, iprot):
        if iprot._fast_decode is not None and isinstance(iprot.trans, TTransport.CReadableTransport) and self.thrift_spec is not None:
            iprot._fast_decode(self, iprot, (self.__class__, self.thrift_spec))
            return
        self.AS_sec = None
        self.AS_nsec = None
        iprot.readStructBegin()
        while True:
            (fname, ftype, fid) = iprot.readFieldBegin()
            if ftype == TType.STOP:
                break
            if fid == 1:
                if ftype == TType.I64:
                    self.AS_sec = iprot.readI64()
                else:
                    iprot.skip(ftype)
            elif fid == 2:
                if ftype == TType.I32:
                    self.AS_nsec = iprot.readI32()
                else:
                    iprot.skip(ftype)
            else:
                iprot.skip(ftype)
            iprot.readFieldEnd()
        iprot.readStructEnd()

    def write(self, oprot):
        if oprot._fast_encode is not None and self.thrift_spec is not None:
            oprot.trans.write(oprot._fast_encode(self, (self.__class__, self.thrift_spec)))
            return
        oprot.writeStructBegin('IEEE802_1ASTimeStampType')
        if self.AS_sec is not None:
            oprot.writeFieldBegin('AS_sec', TType.I64, 1)
            oprot.writeI64(self.AS_sec)
            oprot.writeFieldEnd()
        if self.AS_nsec is not None:
            oprot.writeFieldBegin('AS_nsec', TType.I32, 2)
            oprot.writeI32(self.AS_nsec)
            oprot.writeFieldEnd()
        oprot.writeFieldStop()
        oprot.writeStructEnd()

    def validate(self):
        if self.AS_sec is None:
            raise TProtocolException(message='Required field AS_sec is unset!')
        return

    def __repr__(self):
        L = ['%s=%r' % (key, value)
             for key, value in self.__dict__.items()]
        return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not (self == other)


class IPv4PrefixType(object):
    """
    IPv4 prefix type.

    Attributes:
     - address
     - prefixlen
    """

    thrift_spec = (
        None,  # 0
        (1, TType.I32, 'address', None, None, ),  # 1
        (2, TType.BYTE, 'prefixlen', None, None, ),  # 2
    )

    def __init__(self, address=None, prefixlen=None,):
        super(IPv4PrefixType, self).__setattr__('address', address)
        super(IPv4PrefixType, self).__setattr__('prefixlen', prefixlen)

    def __setattr__(self, *args):
        raise TypeError("can't modify immutable instance")

    def __delattr__(self, *args):
        raise TypeError("can't modify immutable instance")

    def __hash__(self):
        return hash(self.__class__) ^ hash((self.address, self.prefixlen, ))

    @classmethod
    def read(cls, iprot):
        if iprot._fast_decode is not None and isinstance(iprot.trans, TTransport.CReadableTransport) and cls.thrift_spec is not None:
            return iprot._fast_decode(None, iprot, (cls, cls.thrift_spec))
        __var_address= None
        __var_prefixlen= None
        iprot.readStructBegin()
        while True:
            (fname, ftype, fid) = iprot.readFieldBegin()
            if ftype == TType.STOP:
                break
            if fid == 1:
                if ftype == TType.I32:
                    __var_address = iprot.readI32()
                else:
                    iprot.skip(ftype)
            elif fid == 2:
                if ftype == TType.BYTE:
                    __var_prefixlen = iprot.readByte()
                else:
                    iprot.skip(ftype)
            else:
                iprot.skip(ftype)
            iprot.readFieldEnd()
        iprot.readStructEnd()
        return cls(
            address=__var_address,
            prefixlen=__var_prefixlen,
        )

    def write(self, oprot):
        if oprot._fast_encode is not None and self.thrift_spec is not None:
            oprot.trans.write(oprot._fast_encode(self, (self.__class__, self.thrift_spec)))
            return
        oprot.writeStructBegin('IPv4PrefixType')
        if self.address is not None:
            oprot.writeFieldBegin('address', TType.I32, 1)
            oprot.writeI32(self.address)
            oprot.writeFieldEnd()
        if self.prefixlen is not None:
            oprot.writeFieldBegin('prefixlen', TType.BYTE, 2)
            oprot.writeByte(self.prefixlen)
            oprot.writeFieldEnd()
        oprot.writeFieldStop()
        oprot.writeStructEnd()

    def validate(self):
        if self.address is None:
            raise TProtocolException(message='Required field address is unset!')
        if self.prefixlen is None:
            raise TProtocolException(message='Required field prefixlen is unset!')
        return

    def __repr__(self):
        L = ['%s=%r' % (key, value)
             for key, value in self.__dict__.items()]
        return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not (self == other)


class IPv6PrefixType(object):
    """
    IPv6 prefix type.

    Attributes:
     - address
     - prefixlen
    """

    thrift_spec = (
        None,  # 0
        (1, TType.STRING, 'address', 'BINARY', None, ),  # 1
        (2, TType.BYTE, 'prefixlen', None, None, ),  # 2
    )

    def __init__(self, address=None, prefixlen=None,):
        super(IPv6PrefixType, self).__setattr__('address', address)
        super(IPv6PrefixType, self).__setattr__('prefixlen', prefixlen)

    def __setattr__(self, *args):
        raise TypeError("can't modify immutable instance")

    def __delattr__(self, *args):
        raise TypeError("can't modify immutable instance")

    def __hash__(self):
        return hash(self.__class__) ^ hash((self.address, self.prefixlen, ))

    @classmethod
    def read(cls, iprot):
        if iprot._fast_decode is not None and isinstance(iprot.trans, TTransport.CReadableTransport) and cls.thrift_spec is not None:
            return iprot._fast_decode(None, iprot, (cls, cls.thrift_spec))
        __var_address= None
        __var_prefixlen= None
        iprot.readStructBegin()
        while True:
            (fname, ftype, fid) = iprot.readFieldBegin()
            if ftype == TType.STOP:
                break
            if fid == 1:
                if ftype == TType.STRING:
                    __var_address = iprot.readBinary()
                else:
                    iprot.skip(ftype)
            elif fid == 2:
                if ftype == TType.BYTE:
                    __var_prefixlen = iprot.readByte()
                else:
                    iprot.skip(ftype)
            else:
                iprot.skip(ftype)
            iprot.readFieldEnd()
        iprot.readStructEnd()
        return cls(
            address=__var_address,
            prefixlen=__var_prefixlen,
        )

    def write(self, oprot):
        if oprot._fast_encode is not None and self.thrift_spec is not None:
            oprot.trans.write(oprot._fast_encode(self, (self.__class__, self.thrift_spec)))
            return
        oprot.writeStructBegin('IPv6PrefixType')
        if self.address is not None:
            oprot.writeFieldBegin('address', TType.STRING, 1)
            oprot.writeBinary(self.address)
            oprot.writeFieldEnd()
        if self.prefixlen is not None:
            oprot.writeFieldBegin('prefixlen', TType.BYTE, 2)
            oprot.writeByte(self.prefixlen)
            oprot.writeFieldEnd()
        oprot.writeFieldStop()
        oprot.writeStructEnd()

    def validate(self):
        if self.address is None:
            raise TProtocolException(message='Required field address is unset!')
        if self.prefixlen is None:
            raise TProtocolException(message='Required field prefixlen is unset!')
        return

    def __repr__(self):
        L = ['%s=%r' % (key, value)
             for key, value in self.__dict__.items()]
        return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not (self == other)


class IPAddressType(object):
    """
    IP address type.

    Attributes:
     - ipv4address: Content is IPv4
     - ipv6address: Content is IPv6
    """

    thrift_spec = (
        None,  # 0
        (1, TType.I32, 'ipv4address', None, None, ),  # 1
        (2, TType.STRING, 'ipv6address', 'BINARY', None, ),  # 2
    )

    def __init__(self, ipv4address=None, ipv6address=None,):
        super(IPAddressType, self).__setattr__('ipv4address', ipv4address)
        super(IPAddressType, self).__setattr__('ipv6address', ipv6address)

    def __setattr__(self, *args):
        raise TypeError("can't modify immutable instance")

    def __delattr__(self, *args):
        raise TypeError("can't modify immutable instance")

    def __hash__(self):
        return hash(self.__class__) ^ hash((self.ipv4address, self.ipv6address, ))

    @classmethod
    def read(cls, iprot):
        if iprot._fast_decode is not None and isinstance(iprot.trans, TTransport.CReadableTransport) and cls.thrift_spec is not None:
            return iprot._fast_decode(None, iprot, (cls, cls.thrift_spec))
        __var_ipv4address= None
        __var_ipv6address= None
        iprot.readStructBegin()
        while True:
            (fname, ftype, fid) = iprot.readFieldBegin()
            if ftype == TType.STOP:
                break
            if fid == 1:
                if ftype == TType.I32:
                    __var_ipv4address = iprot.readI32()
                else:
                    iprot.skip(ftype)
            elif fid == 2:
                if ftype == TType.STRING:
                    __var_ipv6address = iprot.readBinary()
                else:
                    iprot.skip(ftype)
            else:
                iprot.skip(ftype)
            iprot.readFieldEnd()
        iprot.readStructEnd()
        return cls(
            ipv4address=__var_ipv4address,
            ipv6address=__var_ipv6address,
        )

    def write(self, oprot):
        if oprot._fast_encode is not None and self.thrift_spec is not None:
            oprot.trans.write(oprot._fast_encode(self, (self.__class__, self.thrift_spec)))
            return
        oprot.writeStructBegin('IPAddressType')
        if self.ipv4address is not None:
            oprot.writeFieldBegin('ipv4address', TType.I32, 1)
            oprot.writeI32(self.ipv4address)
            oprot.writeFieldEnd()
        if self.ipv6address is not None:
            oprot.writeFieldBegin('ipv6address', TType.STRING, 2)
            oprot.writeBinary(self.ipv6address)
            oprot.writeFieldEnd()
        oprot.writeFieldStop()
        oprot.writeStructEnd()

    def validate(self):
        return

    def __repr__(self):
        L = ['%s=%r' % (key, value)
             for key, value in self.__dict__.items()]
        return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not (self == other)


class IPPrefixType(object):
    """
    Prefix advertisement.

    @note: for interface
        addresses the protocol can propagate the address part beyond
        the subnet mask and on reachability computation that has to
        be normalized. The non-significant bits can be used
        for operational purposes.

    Attributes:
     - ipv4prefix
     - ipv6prefix
    """

    thrift_spec = (
        None,  # 0
        (1, TType.STRUCT, 'ipv4prefix', (IPv4PrefixType, IPv4PrefixType.thrift_spec), None, ),  # 1
        (2, TType.STRUCT, 'ipv6prefix', (IPv6PrefixType, IPv6PrefixType.thrift_spec), None, ),  # 2
    )

    def __init__(self, ipv4prefix=None, ipv6prefix=None,):
        super(IPPrefixType, self).__setattr__('ipv4prefix', ipv4prefix)
        super(IPPrefixType, self).__setattr__('ipv6prefix', ipv6prefix)

    def __setattr__(self, *args):
        raise TypeError("can't modify immutable instance")

    def __delattr__(self, *args):
        raise TypeError("can't modify immutable instance")

    def __hash__(self):
        return hash(self.__class__) ^ hash((self.ipv4prefix, self.ipv6prefix, ))

    @classmethod
    def read(cls, iprot):
        if iprot._fast_decode is not None and isinstance(iprot.trans, TTransport.CReadableTransport) and cls.thrift_spec is not None:
            return iprot._fast_decode(None, iprot, (cls, cls.thrift_spec))
        __var_ipv4prefix= None
        __var_ipv6prefix= None
        iprot.readStructBegin()
        while True:
            (fname, ftype, fid) = iprot.readFieldBegin()
            if ftype == TType.STOP:
                break
            if fid == 1:
                if ftype == TType.STRUCT:
                    __var_ipv4prefix = IPv4PrefixType.read(iprot)
                else:
                    iprot.skip(ftype)
            elif fid == 2:
                if ftype == TType.STRUCT:
                    __var_ipv6prefix = IPv6PrefixType.read(iprot)
                else:
                    iprot.skip(ftype)
            else:
                iprot.skip(ftype)
            iprot.readFieldEnd()
        iprot.readStructEnd()
        return cls(
            ipv4prefix=__var_ipv4prefix,
            ipv6prefix=__var_ipv6prefix,
        )

    def write(self, oprot):
        if oprot._fast_encode is not None and self.thrift_spec is not None:
            oprot.trans.write(oprot._fast_encode(self, (self.__class__, self.thrift_spec)))
            return
        oprot.writeStructBegin('IPPrefixType')
        if self.ipv4prefix is not None:
            oprot.writeFieldBegin('ipv4prefix', TType.STRUCT, 1)
            self.ipv4prefix.write(oprot)
            oprot.writeFieldEnd()
        if self.ipv6prefix is not None:
            oprot.writeFieldBegin('ipv6prefix', TType.STRUCT, 2)
            self.ipv6prefix.write(oprot)
            oprot.writeFieldEnd()
        oprot.writeFieldStop()
        oprot.writeStructEnd()

    def validate(self):
        return

    def __repr__(self):
        L = ['%s=%r' % (key, value)
             for key, value in self.__dict__.items()]
        return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not (self == other)


class PrefixSequenceType(object):
    """
    Sequence of a prefix in case of move.

    Attributes:
     - timestamp
     - transactionid: Transaction ID set by client in e.g. in 6LoWPAN.
    """

    thrift_spec = (
        None,  # 0
        (1, TType.STRUCT, 'timestamp', (IEEE802_1ASTimeStampType, IEEE802_1ASTimeStampType.thrift_spec), None, ),  # 1
        (2, TType.BYTE, 'transactionid', None, None, ),  # 2
    )

    def __init__(self, timestamp=None, transactionid=None,):
        self.timestamp = timestamp
        self.transactionid = transactionid

    def read(self, iprot):
        if iprot._fast_decode is not None and isinstance(iprot.trans, TTransport.CReadableTransport) and self.thrift_spec is not None:
            iprot._fast_decode(self, iprot, (self.__class__, self.thrift_spec))
            return
        self.timestamp = None
        self.transactionid = None
        iprot.readStructBegin()
        while True:
            (fname, ftype, fid) = iprot.readFieldBegin()
            if ftype == TType.STOP:
                break
            if fid == 1:
                if ftype == TType.STRUCT:
                    self.timestamp = IEEE802_1ASTimeStampType()
                    self.timestamp.read(iprot)
                else:
                    iprot.skip(ftype)
            elif fid == 2:
                if ftype == TType.BYTE:
                    self.transactionid = iprot.readByte()
                else:
                    iprot.skip(ftype)
            else:
                iprot.skip(ftype)
            iprot.readFieldEnd()
        iprot.readStructEnd()

    def write(self, oprot):
        if oprot._fast_encode is not None and self.thrift_spec is not None:
            oprot.trans.write(oprot._fast_encode(self, (self.__class__, self.thrift_spec)))
            return
        oprot.writeStructBegin('PrefixSequenceType')
        if self.timestamp is not None:
            oprot.writeFieldBegin('timestamp', TType.STRUCT, 1)
            self.timestamp.write(oprot)
            oprot.writeFieldEnd()
        if self.transactionid is not None:
            oprot.writeFieldBegin('transactionid', TType.BYTE, 2)
            oprot.writeByte(self.transactionid)
            oprot.writeFieldEnd()
        oprot.writeFieldStop()
        oprot.writeStructEnd()

    def validate(self):
        if self.timestamp is None:
            raise TProtocolException(message='Required field timestamp is unset!')
        return

    def __repr__(self):
        L = ['%s=%r' % (key, value)
             for key, value in self.__dict__.items()]
        return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not (self == other)
