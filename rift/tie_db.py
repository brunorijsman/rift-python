# Topology Information Element DataBase (TIE_DB)

import ipaddress
import sortedcontainers

import common.ttypes
import table

# TODO: We currently only store the decoded TIE messages.
# Also store the encoded TIE messages for the following reasons:
# - Encode only once, instead of each time the message is sent
# - Ability to flood the message immediately before it is decoded

# pylint: disable=invalid-name
class TIE_DB:

    def __init__(self):
        self.ties = sortedcontainers.SortedDict()

    def store_tie(self, tie):
        tie_id = tie.content.tie.header.tieid
        self.ties[tie_id] = tie

    def find_tie(self, tie_id):
        return self.ties.get(tie_id)

    def find_tie_range(self, start_tid_id_exclusive, end_tie_id_inclusive):
        return self.ties.irange(minimum=start_tid_id_exclusive,
                                maximum=end_tie_id_inclusive,
                                inclusive=(False, True))

    def process_received_tide_packet(self, tide_packet):
        request_tie_ids = []
        start_sending_tie_ids = []
        stop_sending_tie_ids = []
        # TODO: ignoring this rule for now:
        # if TIDE.start_range > LAST_RCVD_TIDE_END then add all headers in TIDE to TXKEYS and then
        last_processed_tie_id = tide_packet.start_range
        for header_in_tide in tide_packet.headers:
            # Make sure all tie_ids in the TIDE in the range advertised by the TIDE
            if header_in_tide.tieid < last_processed_tie_id:
                # TODO: Handle error (not sorted)
                assert False
            # Process all tie_ids in the TIDE
            db_tie = self.find_tie(header_in_tide.tieid)
            if db_tie is None:
                # We don't have the TIE, request it
                request_tie_ids.append(header_in_tide.tieid)
            elif db_tie.header.seq_nr < header_in_tide.seq_nr:
                # We have an older version of the TIE, request the newer version
                request_tie_ids.append(header_in_tide.tieid)
            elif db_tie.header.seq_nr > header_in_tide.seq_nr:
                # We have a newer version of the TIE, send it
                start_sending_tie_ids.append(header_in_tide.tieid)
            else:
                # db_tie.header.seq_nr == header_in_tide.seq_nr
                # We have the same version of the TIE, if we are trying to send it, stop it
                stop_sending_tie_ids.append(header_in_tide.tieid)
            # Process the TIEs that we have in our TIE DB but which are missing in the TIDE
            db_ties = self.find_tie_range(last_processed_tie_id, tide_packet.end_range)
            for db_tie in db_ties:
                # We have a TIE that our neighbor does not have, start sending it
                start_sending_tie_ids.append(db_tie.header.tieid)
        return (request_tie_ids, start_sending_tie_ids, stop_sending_tie_ids)

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
            "Nr",
            "Contents"]

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

    def cli_summary_attributes(self, tie):
        tie_id = tie.content.tie.header.tieid
        return [
            self.direction_str(tie_id.direction),
            tie_id.originator,
            self.tietype_str(tie_id.tietype),
            tie_id.tie_nr,
            self.element_str(tie_id.tietype, tie.content.tie.element)
        ]
