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

    def process_received_tide_packet(self, protocol_packet):
        tide_packet = protocol_packet.content.tide
        request_tie_ids = []
        start_sending_tie_ids = []
        stop_sending_tie_ids = []
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
            db_ties = self.ties.irange(minimum=self._last_received_tide_end,
                                       maximum=tide_packet.start_range,
                                       inclusive=(True, False))
            for db_tie_id in db_ties:
                start_sending_tie_ids.append(db_tie_id)
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
            db_ties = self.ties.irange(minimum=last_processed_tie_id,
                                       maximum=header_in_tide.tieid,
                                       inclusive=(minimum_inclusive, False))
            for db_tie_id in db_ties:
                start_sending_tie_ids.append(db_tie_id)
            last_processed_tie_id = header_in_tide.tieid
            minimum_inclusive = False
            # Process all tie_ids in the TIDE
            db_tie = self.find_tie(header_in_tide.tieid)
            if db_tie is None:
                # We don't have the TIE, request it
                request_tie_ids.append(header_in_tide.tieid)
            elif db_tie.content.tie.header.seq_nr < header_in_tide.seq_nr:
                # We have an older version of the TIE, request the newer version
                request_tie_ids.append(header_in_tide.tieid)
            elif db_tie.content.tie.header.seq_nr > header_in_tide.seq_nr:
                # We have a newer version of the TIE, send it
                start_sending_tie_ids.append(header_in_tide.tieid)
            else:
                # We have the same version of the TIE, if we are trying to send it, stop it
                assert db_tie.content.tie.header.seq_nr == header_in_tide.seq_nr
                stop_sending_tie_ids.append(header_in_tide.tieid)
        # End-gap processing: send TIEs that are in our TIE DB but missing in TIDE
        db_ties = self.ties.irange(minimum=last_processed_tie_id,
                                   maximum=tide_packet.end_range,
                                   inclusive=(minimum_inclusive, True))
        for db_tie_id in db_ties:
            start_sending_tie_ids.append(db_tie_id)
        return (request_tie_ids, start_sending_tie_ids, stop_sending_tie_ids)

    def tie_db_table(self):
        tab = table.Table()
        tab.add_row(self.cli_summary_headers())
        for tie in self.ties.values():
            tab.add_row(self.cli_summary_attributes(tie))
        return tab

    _direction_to_str = {
        common.ttypes.TieDirectionType.South: "South",
        common.ttypes.TieDirectionType.North: "North"
    }

    def direction_str(self, direction):
        if direction in self._direction_to_str:
            return self._direction_to_str[direction]
        else:
            return str(direction)

    _tietype_to_str = {
        common.ttypes.TIETypeType.NodeTIEType: "Node",
        common.ttypes.TIETypeType.PrefixTIEType: "Prefix",
        common.ttypes.TIETypeType.TransitivePrefixTIEType: "TransitivePrefix",
        common.ttypes.TIETypeType.PGPrefixTIEType: "PolicyGuidedPrefix",
        common.ttypes.TIETypeType.KeyValueTIEType: "KeyValue"
    }

    def tietype_str(self, tietype):
        if tietype in self._tietype_to_str:
            return self._tietype_to_str[tietype]
        else:
            return str(tietype)

    @staticmethod
    def ipv4_prefix_str(ipv4_prefix):
        address = ipv4_prefix.address
        length = ipv4_prefix.prefixlen
        return str(ipaddress.IPv4Network((address, length)))

    @staticmethod
    def ipv6_prefix_str(ipv6_prefix):
        address = ipv6_prefix.address.rjust(16, b"\x00")
        length = ipv6_prefix.prefixlen
        return str(ipaddress.IPv6Network((address, length)))

    def ip_prefix_str(self, ip_prefix):
        assert (ip_prefix.ipv4prefix is None) or (ip_prefix.ipv6prefix is None)
        assert (ip_prefix.ipv4prefix is not None) or (ip_prefix.ipv6prefix is not None)
        result = ""
        if ip_prefix.ipv4prefix:
            result += self.ipv4_prefix_str(ip_prefix.ipv4prefix)
        if ip_prefix.ipv6prefix:
            result += self.ipv6_prefix_str(ip_prefix.ipv6prefix)
        return result

    def node_element_str(self, _element):
        # TODO: Implement this
        return "TODO"

    def prefix_element_str(self, element):
        lines = []
        sorted_prefixes = sortedcontainers.SortedDict(element.prefixes)
        for prefix, attributes in sorted_prefixes.items():
            line = "Prefix: " + self.ip_prefix_str(prefix)
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

    def transitive_prefix_element_str(self, _element):
        # TODO: Implement this
        return "TODO"

    def pg_prefix_element_str(self, _element):
        # TODO: Implement this
        return "TODO"

    def key_value_element_str(self, _element):
        # TODO: Implement this
        return "TODO"

    def unknown_element_str(self, _element):
        # TODO: Implement this
        return "TODO"

    def element_str(self, tietype, element):
        if tietype == common.ttypes.TIETypeType.NodeTIEType:
            return self.node_element_str(element.node)
        elif tietype == common.ttypes.TIETypeType.PrefixTIEType:
            return self.prefix_element_str(element.prefixes)
        elif tietype == common.ttypes.TIETypeType.TransitivePrefixTIEType:
            return self.transitive_prefix_element_str(element.transitive_prefixes)
        elif tietype == common.ttypes.TIETypeType.PGPrefixTIEType:
            return self.pg_prefix_element_str(element)   # TODO
        elif tietype == common.ttypes.TIETypeType.KeyValueTIEType:
            return self.key_value_element_str(element.keyvalues)
        else:
            return self.unknown_element_str(element)

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
            self.direction_str(tie_id.direction),
            tie_id.originator,
            self.tietype_str(tie_id.tietype),
            tie_id.tie_nr,
            tie.content.tie.header.seq_nr,
            self.element_str(tie_id.tietype, tie.content.tie.element)
        ]
