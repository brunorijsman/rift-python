# Topology Information Element DataBase (TIE_DB)

import ipaddress
import sortedcontainers

import common.ttypes
import encoding.ttypes
import table

# TODO: We currently only store the decoded TIE messages.
# Also store the encoded TIE messages for the following reasons:
# - Encode only once, instead of each time the message is sent
# - Ability to flood the message immediately before it is decoded

DIRECTION_TO_STR = {
    common.ttypes.TieDirectionType.South: "South",
    common.ttypes.TieDirectionType.North: "North"
}

def direction_str(direction):
    if direction in DIRECTION_TO_STR:
        return DIRECTION_TO_STR[direction]
    else:
        return str(direction)

TIETYPE_TO_STR = {
    common.ttypes.TIETypeType.NodeTIEType: "Node",
    common.ttypes.TIETypeType.PrefixTIEType: "Prefix",
    common.ttypes.TIETypeType.TransitivePrefixTIEType: "TransitivePrefix",
    common.ttypes.TIETypeType.PGPrefixTIEType: "PolicyGuidedPrefix",
    common.ttypes.TIETypeType.KeyValueTIEType: "KeyValue"
}

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

def tietype_str(tietype):
    if tietype in TIETYPE_TO_STR:
        return TIETYPE_TO_STR[tietype]
    else:
        return str(tietype)

def node_element_str(_element):
    # TODO: Implement this
    return "TODO"

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

# The TieKey class is when we need a key (e.g. as an index to a map) to uniquely identify one
# particular version of a TIE.
class TIEKey:

    def __init__(self, tie_id, seq_nr):
        self.tie_id = tie_id
        self.seq_nr = seq_nr

    def tup(self):
        return (self.tie_id, self.seq_nr)

    def __hash__(self):
        return hash(self.tup())

    def __eq__(self, other):
        return self.tup() == other.tup()

    def __lt__(self, other):
        return self.tup() < other.tup()

    def __repr__(self):
        return ("TIEKey(tie_id=TIEID(direction={}, originator={}, tietype={}, tie_nr={}),"
                " seq_nr={})".format(self.tie_id.direction, self.tie_id.originator,
                                     self.tie_id.tietype, self.tie_id.tie_nr, self.seq_nr))

    @staticmethod
    def cli_summary_headers():
        return [
            "Direction",
            "Originator",
            "Type",
            "TIE-Nr",
            "Seq-Nr"]

    def cli_summary_attributes(self):
        return [
            direction_str(self.tie_id.direction),
            self.tie_id.originator,
            tietype_str(self.tie_id.tietype),
            self.tie_id.tie_nr,
            self.seq_nr]

# Extend the generated class TIEHeader with a method to extract the key as defined above
encoding.ttypes.TIEHeader.to_key = (lambda self: TIEKey(self.tieid, self.seq_nr))

# pylint: disable=invalid-name
class TIE_DB:

    MIN_TIE_ID = encoding.ttypes.TIEID(direction=common.ttypes.TieDirectionType.Illegal,
                                       originator=0,
                                       tietype=common.ttypes.TIETypeType.Illegal,
                                       tie_nr=0)

    def __init__(self):
        self.ties = sortedcontainers.SortedDict()
        # Statefull record of the end of the range of the most recently received TIDE. This is used
        # to detect gaps between the range end of one received TIDE and the range beginning of the
        # next received TIDE, and start sending any TIEs in our TIE DB that fall in that gap.
        # When we have not yet received any TIDE yet, this is initialized to the lowest possible
        # TIEID value.
        self._last_received_tide_end = self.MIN_TIE_ID

    def store_tie(self, tie):
        tie_id = tie.content.tie.header.tieid
        self.ties[tie_id] = tie

    def find_tie(self, tie_id):
        return self.ties.get(tie_id)

    def start_sending_db_ties_in_range(self, start_sending_tie_keys, start_id, start_incl,
                                       end_id, end_incl):
        db_ties = self.ties.irange(start_id, end_id, (start_incl, end_incl))
        for db_tie_id in db_ties:
            db_tie = self.ties[db_tie_id]
            start_sending_tie_keys.append(db_tie.content.tie.header.to_key())

    def process_received_tide_packet(self, protocol_packet):
        tide_packet = protocol_packet.content.tide
        assert tide_packet is not None
        request_tie_keys = []
        start_sending_tie_keys = []
        stop_sending_tie_keys = []
        # It is assumed TIDEs are sent and received in increasing order or range. If we observe
        # a gap between the end of the range of the last TIDE (if any) and the start of the range
        # of this TIDE, then we must start sending all TIEs in our database that fall in that gap.
        if tide_packet.start_range < self._last_received_tide_end:
            # The neighbor has wrapped around: it has sent its last TIDE and is not sending the
            # first TIDE again (look for comment "wrap-around" in test_tie_db.py for an example)
            # Note - I am not completely happy with this rule since it may lead to unnecessarily
            # putting TIEs on the send queue if TIDEs are received out of order.
            self._last_received_tide_end = self.MIN_TIE_ID
        if tide_packet.start_range > self._last_received_tide_end:
            # There is a gap between the end of the previous TIDE and the start of this TIDE
            self.start_sending_db_ties_in_range(start_sending_tie_keys,
                                                self._last_received_tide_end, True,
                                                tide_packet.start_range, False)
        self._last_received_tide_end = tide_packet.end_range
        # The first gap that we need to consider starts at start_range (inclusive)
        last_processed_tie_id = tide_packet.start_range
        minimum_inclusive = True   # TODO: Have a special test case for this
        # Process the TIDE
        for header_in_tide in tide_packet.headers:
            # Make sure all tie_ids in the TIDE in the range advertised by the TIDE
            if header_in_tide.tieid < last_processed_tie_id:
                # TODO: Handle error (not sorted)
                assert False
            # Start/mid-gap processing: send TIEs that are in our TIE DB but missing in TIDE
            self.start_sending_db_ties_in_range(start_sending_tie_keys,
                                                last_processed_tie_id, minimum_inclusive,
                                                header_in_tide.tieid, False)
            last_processed_tie_id = header_in_tide.tieid
            minimum_inclusive = False
            # Process all tie_ids in the TIDE
            db_tie = self.find_tie(header_in_tide.tieid)
            if db_tie is None:
                # We don't have the TIE, request it
                request_tie_keys.append(header_in_tide.to_key())
            elif db_tie.content.tie.header.seq_nr < header_in_tide.seq_nr:
                # We have an older version of the TIE, request the newer version
                request_tie_keys.append(header_in_tide.to_key())
            elif db_tie.content.tie.header.seq_nr > header_in_tide.seq_nr:
                # We have a newer version of the TIE, send it
                start_sending_tie_keys.append(db_tie.content.tie.header.to_key())
            else:
                # We have the same version of the TIE, if we are trying to send it, stop it
                assert db_tie.content.tie.header.seq_nr == header_in_tide.seq_nr
                stop_sending_tie_keys.append(db_tie.content.tie.header.to_key())
        # End-gap processing: send TIEs that are in our TIE DB but missing in TIDE
        self.start_sending_db_ties_in_range(start_sending_tie_keys,
                                            last_processed_tie_id, minimum_inclusive,
                                            tide_packet.end_range, True)
        return (request_tie_keys, start_sending_tie_keys, stop_sending_tie_keys)

    def process_received_tire_packet(self, protocol_packet):
        tire_packet = protocol_packet.content.tire
        assert tire_packet is not None
        request_tie_keys = []
        start_sending_tie_keys = []
        acked_tie_keys = []
        for header_in_tire in tire_packet.headers:
            db_tie = self.find_tie(header_in_tire.tieid)
            if db_tie is not None:
                tire_seq_nr = header_in_tire.seq_nr
                db_seq_nr = db_tie.content.tie.header.seq_nr
                if db_seq_nr < tire_seq_nr:
                    # TIE in TIE-DB is older than TIRE, request newer TIE from neighbor
                    request_tie_keys.append(header_in_tire.to_key())
                elif db_seq_nr > tire_seq_nr:
                    # TIE in TIE-DB is newer than TIRE, send newer TIE to neighbor
                    start_sending_tie_keys.append(db_tie.content.tie.header.to_key())
                else:
                    # TIE in TIE-DB is same version as TIRE, treat it as an ACK
                    assert db_seq_nr == tire_seq_nr
                    acked_tie_keys.append(header_in_tire.to_key())
        return (request_tie_keys, start_sending_tie_keys, acked_tie_keys)

    def tie_db_table(self):
        tab = table.Table()
        tab.add_row(self.cli_summary_headers())
        for tie in self.ties.values():
            tab.add_row(self.cli_summary_attributes(tie))
        return tab

    @staticmethod
    def cli_summary_headers():
        return [
            "Direction",
            "Originator",
            "Type",
            "TIE Nr",
            "Seq Nr",
            "Contents"]

    def cli_summary_attributes(self, tie):
        tie_id = tie.content.tie.header.tieid
        return [
            direction_str(tie_id.direction),
            tie_id.originator,
            tietype_str(tie_id.tietype),
            tie_id.tie_nr,
            tie.content.tie.header.seq_nr,
            element_str(tie_id.tietype, tie.content.tie.element)
        ]
