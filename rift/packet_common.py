# TODO: Handle receiving malformed packets (i.e. decoding errors)

import thrift.protocol.TBinaryProtocol
import thrift.transport.TTransport
import encoding.ttypes
import encoding.constants

# TODO: This is defined in two separate places
RIFT_MAJOR_VERSION = encoding.constants.protocol_major_version
RIFT_MINOR_VERSION = encoding.constants.protocol_minor_version

def create_packet_header(node):
    packet_header = encoding.ttypes.PacketHeader(
        major_version=RIFT_MAJOR_VERSION,
        minor_version=RIFT_MINOR_VERSION,
        sender=node.system_id,
        level=node.level_value()
    )
    return packet_header

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

_MAX_U64 = 0xffffffffffffffff
_MAX_S64 = 0x7fffffffffffffff

_MAX_U32 = 0xffffffff
_MAX_S32 = 0x7fffffff

_MAX_U16 = 0xffff
_MAX_S16 = 0x7fff

_MAX_U16 = 0xffff
_MAX_S16 = 0x7fff

_MAX_U8 = 0xff
_MAX_S8 = 0x7f

def u64_to_s64(u64):
    return u64 if u64 <= _MAX_S64 else u64 - _MAX_U64 - 1

def u32_to_s32(u32):
    return u32 if u32 <= _MAX_S32 else u32 - _MAX_U32 - 1

def u16_to_s16(u16):
    return u16 if u16 <= _MAX_S16 else u16 - _MAX_U16 - 1

def u8_to_s8(u08):
    return u08 if u08 <= _MAX_S8 else u08 - _MAX_U8 - 1

def s64_to_u64(s64):
    return s64 if s64 >= 0 else s64 + _MAX_U64 + 1

def s32_to_u32(s32):
    return s32 if s32 >= 0 else s32 + _MAX_U32 + 1

def s16_to_u16(s16):
    return s16 if s16 >= 0 else s16 + _MAX_U16 + 1

def s8_to_u8(s08):
    return s08 if s08 >= 0 else s08 + _MAX_U8 + 1

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
        ('tide', []),           # TODO
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
