# Topology Information Element DataBase (TIE_DB)

import sortedcontainers

import common.ttypes
import table

# TODO: We currently only store the decoded TIE messages.
# Also store the encoded TIE messages for the following reasons:
# - Encode only once, instead of each time the message is sent
# - Ability to flood the message immediately before it is decoded

class TIE_DB:

    def __init__(self):
        self.ties = sortedcontainers.SortedDict()

    def store_tie(self, tie):
        tie_id = tie.content.tie.header.tieid
        self.ties[tie_id] = tie

    def command_show_tie_db(self, cli_session):
        tab = table.Table()
        tab.add_row(self.cli_summary_headers())
        for tie in self.ties.values():
            tab.add_row(self.cli_summary_attributes(tie))
        cli_session.print(tab.to_string(cli_session.current_end_line()))

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

    def node_element_str(self, _element):
        # TODO: Implement this
        return "TODO"

    def prefix_element_str(self, _element):
        # TODO: Implement this
        return "TODO"

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
            return self.node_element_str(element)
        elif tietype == common.ttypes.TIETypeType.PrefixTIEType:
            return self.prefix_element_str(element)
        elif tietype == common.ttypes.TIETypeType.TransitivePrefixTIEType:
            return self.transitive_prefix_element_str(element)
        elif tietype == common.ttypes.TIETypeType.PGPrefixTIEType:
            return self.pg_prefix_element_str(element)
        elif tietype == common.ttypes.TIETypeType.KeyValueTIEType:
            return self.key_value_element_str(element)
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
