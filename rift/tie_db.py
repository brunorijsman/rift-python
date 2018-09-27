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

# Extend the generated class TIEHeader with additional methods
# TODO: add remaining_lifetime
# TODO: add origination_time

encoding.ttypes.TIEHeader.cli_summary_headers = (
    lambda self: ["Direction", "Originator", "Type", "TIE-Nr", "Seq-Nr"])

encoding.ttypes.TIEHeader.cli_summary_attributes = (
    lambda self: [direction_str(self.tie_id.direction),
                  self.tie_id.originator,
                  tietype_str(self.tie_id.tietype),
                  self.tie_id.tie_nr,
                  self.seq_nr])

def compare_tie_header_age(header1, header2):
    # Returns -1 is header1 is older, returns +1 if header1 is newer, 0 if "same" age
    # It is not allowed to call this function with headers with different TIE-IDs.
    assert header1.tieid == header2.tieid
    # Highest sequence number is newer
    if header1.seq_nr < header2.seq_nr:
        return -1
    if header1.seq_nr > header2.seq_nr:
        return 1
    # When a node advertises remaining_lifetime 0 in a TIRE, it means a request (I don't have
    # that TIRE, please send it). Thus, if one header has remaining_lifetime 0 and the other
    # does not, then the one with non-zero remaining_lifetime is always newer.
    if (header1.remaining_lifetime == 0) and (header2.remaining_lifetime != 0):
        return -1
    if (header1.remaining_lifetime != 0) and (header2.remaining_lifetime == 0):
        return 1
    # The header with the longest remaining lifetime is considered newer. However, if the
    # difference in remaining lifetime is less than 5 minutes (300 seconds), they are considered
    # to be the same age.
    age_diff = abs(header1.remaining_lifetime - header2.remaining_lifetime)
    if age_diff > 300:
        if header1.remaining_lifetime < header2.remaining_lifetime:
            return -1
        if header1.remaining_lifetime > header2.remaining_lifetime:
            return 1
    # TODO: Figure out what to do with origination_time
    # If we get this far, we have a tie (same age)
    return 0

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

    def store_tie(self, protocol_packet):
        assert protocol_packet.content.tie is not None
        tie_id = protocol_packet.content.tie.header.tieid
        self.ties[tie_id] = protocol_packet

    def find_tie(self, tie_id):
        return self.ties.get(tie_id)

    def start_sending_db_ties_in_range(self, start_sending_tie_headers, start_id, start_incl,
                                       end_id, end_incl):
        db_ties = self.ties.irange(start_id, end_id, (start_incl, end_incl))
        for db_tie_id in db_ties:
            db_tie = self.ties[db_tie_id]
            # TODO: Decrease TIE lifetime to account for time spent on this router
            # TODO: Decrease TIE lifetime by at least 1
            start_sending_tie_headers.append(db_tie.content.tie.header)

    def process_received_tide_packet(self, protocol_packet):
        tide_packet = protocol_packet.content.tide
        assert tide_packet is not None
        request_tie_headers = []
        start_sending_tie_headers = []
        stop_sending_tie_headers = []
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
            self.start_sending_db_ties_in_range(start_sending_tie_headers,
                                                self._last_received_tide_end, True,
                                                tide_packet.start_range, False)
        self._last_received_tide_end = tide_packet.end_range
        # The first gap that we need to consider starts at start_range (inclusive)
        last_processed_tie_id = tide_packet.start_range
        minimum_inclusive = True
        # Process the TIDE
        for header_in_tide in tide_packet.headers:
            # Make sure all tie_ids in the TIDE in the range advertised by the TIDE
            if header_in_tide.tieid < last_processed_tie_id:
                # TODO: Handle error (not sorted)
                assert False
            # Start/mid-gap processing: send TIEs that are in our TIE DB but missing in TIDE
            self.start_sending_db_ties_in_range(start_sending_tie_headers,
                                                last_processed_tie_id, minimum_inclusive,
                                                header_in_tide.tieid, False)
            last_processed_tie_id = header_in_tide.tieid
            minimum_inclusive = False
            # Process all tie_ids in the TIDE
            db_tie = self.find_tie(header_in_tide.tieid)
            if db_tie is None:
                # We don't have the TIE, request it
                # To request a a missing TIE, we have to set the seq_nr to 0. This is not mentioned
                # in the RIFT draft, but it is described in ISIS ISO/IEC 10589:1992 section 7.3.15.2
                # bullet b.4
                request_header = header_in_tide
                request_header.seq_nr = 0
                request_header.remaining_lifetime = 0
                request_header.origination_time = None
                request_tie_headers.append(request_header)
            else:
                comparison = compare_tie_header_age(db_tie.content.tie.header, header_in_tide)
                if comparison < 0:
                    # We have an older version of the TIE, request the newer version
                    request_tie_headers.append(header_in_tide)
                elif comparison > 0:
                    # We have a newer version of the TIE, send it
                    start_sending_tie_headers.append(db_tie.content.tie.header)
                else:
                    # We have the same version of the TIE, if we are trying to send it, stop it
                    stop_sending_tie_headers.append(db_tie.content.tie.header)
        # End-gap processing: send TIEs that are in our TIE DB but missing in TIDE
        self.start_sending_db_ties_in_range(start_sending_tie_headers,
                                            last_processed_tie_id, minimum_inclusive,
                                            tide_packet.end_range, True)
        return (request_tie_headers, start_sending_tie_headers, stop_sending_tie_headers)

    def process_received_tire_packet(self, protocol_packet):
        tire_packet = protocol_packet.content.tire
        assert tire_packet is not None
        request_tie_headers = []
        start_sending_tie_headers = []
        acked_tie_headers = []
        for header_in_tire in tire_packet.headers:
            db_tie = self.find_tie(header_in_tire.tieid)
            if db_tie is not None:
                comparison = compare_tie_header_age(db_tie.content.tie.header, header_in_tire)
                if comparison < 0:
                    # We have an older version of the TIE, request the newer version
                    request_tie_headers.append(header_in_tire)
                elif comparison > 0:
                    # We have a newer version of the TIE, send it
                    start_sending_tie_headers.append(db_tie.content.tie.header)
                else:
                    # We have the same version of the TIE, treat it as an ACK
                    acked_tie_headers.append(db_tie.content.tie.header)
        return (request_tie_headers, start_sending_tie_headers, acked_tie_headers)

    def process_received_tie_packet(self, protocol_packet, node_system_id):
        tie_packet = protocol_packet.content.tie
        assert tie_packet is not None
        start_sending_tie_header = None
        ack_tie_header = None
        rx_tie_header = tie_packet.header
        rx_tie_id = rx_tie_header.tieid
        db_tie = self.find_tie(rx_tie_id)
        if db_tie is None:
            if rx_tie_id.originator == node_system_id:
                # TODO: re-originate with higher sequence number
                pass
            else:
                # We don't have this TIE in the database, store and ack it
                self.store_tie(protocol_packet)
                ack_tie_header = rx_tie_header
        else:
            comparison = compare_tie_header_age(db_tie.content.tie.header, rx_tie_header)
            if comparison < 0:
                # We have an older version of the TIE, ...
                if rx_tie_id.originator == node_system_id:
                    # TODO: We originated the TIE, re-originate with higher sequence number
                    pass
                else:
                    # We did not originate the TIE, store the newer version and ack it
                    self.store_tie(tie_packet)
                    ack_tie_header = db_tie.content.tie.header
            elif comparison > 0:
                # We have a newer version of the TIE, send it
                start_sending_tie_header = db_tie.content.tie.header
            else:
                # We have the same version of the TIE, ACK it
                ack_tie_header = db_tie.content.tie.header
        return (start_sending_tie_header, ack_tie_header)

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
            "Lifetime",
            "Contents"]

    def cli_summary_attributes(self, tie):
        tie_id = tie.content.tie.header.tieid
        return [
            direction_str(tie_id.direction),
            tie_id.originator,
            tietype_str(tie_id.tietype),
            tie_id.tie_nr,
            tie.content.tie.header.seq_nr,
            tie.content.tie.header.remaining_lifetime,
            element_str(tie_id.tietype, tie.content.tie.element)
        ]
