# Topology Information Element DataBase (TIE_DB)

import sortedcontainers

import common.ttypes
import encoding.ttypes
import neighbor
import packet_common
import table
import timer

# TODO: We currently only store the decoded TIE messages.
# Also store the encoded TIE messages for the following reasons:
# - Encode only once, instead of each time the message is sent
# - Ability to flood the message immediately before it is decoded

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

    # TODO: Use constant from Thrift file (it is currently not there, but Tony said he added it)
    # Don't use the actual lowest value 0 (which is enum value Illegal) for direction or tietype,
    # but value 1 (direction South) or value 2 (tietype TieTypeNode). Juniper RIFT doesn't accept
    # illegal values.
    MIN_TIE_ID = encoding.ttypes.TIEID(
        direction=common.ttypes.TieDirectionType.South,
        originator=0,
        tietype=common.ttypes.TIETypeType.NodeTIEType,
        tie_nr=0)
    # For the same reason don't use DirectionMaxValue or TIETypeMaxValue but North and
    # KeyValueTIEType instead
    MAX_TIE_ID = encoding.ttypes.TIEID(
        direction=common.ttypes.TieDirectionType.North,
        originator=packet_common.MAX_U64,
        tietype=common.ttypes.TIETypeType.KeyValueTIEType,
        tie_nr=packet_common.MAX_U32)

    def __init__(self):
        self.ties = sortedcontainers.SortedDict()
        # Statefull record of the end of the range of the most recently received TIDE. This is used
        # to detect gaps between the range end of one received TIDE and the range beginning of the
        # next received TIDE, and start sending any TIEs in our TIE DB that fall in that gap.
        # When we have not yet received any TIDE yet, this is initialized to the lowest possible
        # TIEID value.
        self._last_received_tide_end = self.MIN_TIE_ID
        self._age_ties_timer = timer.Timer(
            interval=1.0,
            expire_function=self.age_ties,
            periodic=True,
            start=True)

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

    def tie_is_self_originated(self, tie_header, my_system_id):
        return tie_header.tieid.originator == my_system_id

    def tie_originator_level(self, tie_header):
        # We cannot determine the level of the originator just by looking at the TIE header; we have
        # to look in the TIE-DB to determine it. We can be confident the TIE is in the TIE-DB
        # because we wouldn't be here, considering sending a TIE to a neighbor, if we did not have
        # the TIE in the TIE-DB.
        db_tie = self.find_tie(tie_header.tieid)
        if db_tie is None:
            # Just in case it unexpectedly not in the TIE-DB
            return None
        else:
            return db_tie.header.level

    def is_flood_allowed(self, tie_header, neighbor_direction, my_system_id, my_level):
        # TODO: Implement Top-of-Fabric flag (for now assume not top of fabric). Question: whose
        # ToF is being checked here? Ours? The neighbor's? The originator's?
        top_of_fabric = False
        if tie_header.tieid.direction == common.ttypes.TieDirectionType.South:
            # The TIE is a South-TIE
            if tie_header.tieid.tietype == common.ttypes.TIETypeType.NodeTIEType:
                # The TIE is a Node South-TIE
                if neighbor_direction == neighbor.Neighbor.Direction.SOUTH:
                    # Only flood a Node South-TIE to a South-Neighbor if it is self-originated
                    if self.tie_is_self_originated(tie_header, my_system_id):
                        return (True, "Node S-TIE to S: self-originated")
                    else:
                        return (False, "Node S-TIE to S: not self-originated")
                elif neighbor_direction == neighbor.Neighbor.Direction.NORTH:
                    # Only flood a Node South-TIE to a North-Neighbor if TIE originator level is
                    # higher than my own level.
                    originator_level = self.tie_originator_level(tie_header)
                    if originator_level is None:
                        return (False, "Node S-TIE to N: could not determine originator level")
                    elif originator_level > my_level:
                        return (True, "Node S-TIE to N: originator level is higher than mine")
                    else:
                        return (False, "Node S-TIE to N: originator level is not higher than mine")
                elif neighbor_direction == neighbor.Neighbor.Direction.EAST_WEST:
                    # Only flood a Node South-TIE to an East-West-Neighbor if not Top-of-Fabric
                    if top_of_fabric:
                        return (False, "Node S-TIE to EW: top of fabric")
                    else:
                        return (True, "Node S-TIE to EW: not top of fabric")
                else:
                    # We cannot determine the direction of the neighbor; don't flood
                    assert neighbor_direction is None
                    return (False, "Node S-TIE to ?: never flood")
            else:
                # The TIE is a non-Node South-TIE
                if neighbor_direction == neighbor.Neighbor.Direction.SOUTH:
                    # Only flood a Node South-TIE to a South-Neighbor if it is self-originated
                    if self.tie_is_self_originated(tie_header, my_system_id):
                        return (True, "Non-node S-TIE to S: self-originated")
                    else:
                        return (False, "Non-node S-TIE to S: not self-originated")
                elif neighbor_direction == neighbor.Neighbor.Direction.NORTH:
                    # Only flood a Node South-TIE to a North-Neighbor if TIE originator level is
                    # equal peer.
                    # TODO: Does "is equal peer" mean "is same level as ME" or "is same level as
                    # NEIGHBOR"? I need to think about that. For now, I assume the former.
                    originator_level = self.tie_originator_level(tie_header)
                    if originator_level is None:
                        return (False, "Non-node S-TIE to N: could not determine originator level")
                    elif originator_level == my_level:
                        return (True, "Non-node S-TIE to N: originator level is same as mine")
                    else:
                        return (False, "Non-node S-TIE to N: originator level is not same as mine")
                elif neighbor_direction == neighbor.Neighbor.Direction.EAST_WEST:
                    # Only flood a Node South-TIE to an East-West-Neighbor if self-originated and
                    # not Top-of-Fabric
                    if top_of_fabric:
                        return (False, "Non-node S-TIE to EW: top of fabric")
                    elif self.tie_is_self_originated(tie_header, my_system_id):
                        return (True, "Non-node S-TIE to EW: self-originated and not top of fabric")
                    else:
                        return (False, "Non-node S-TIE to EW: not self-originated")
                else:
                    # We cannot determine the direction of the neighbor; don't flood
                    assert neighbor_direction is None
                    return (False, "None-node S-TIE to ?: never flood")
        else:
            # The TIE is a North-TIE
            assert tie_header.tieid.direction == common.ttypes.TieDirectionType.North
            if neighbor_direction == neighbor.Neighbor.Direction.SOUTH:
                # Never flood a North-TIE to a South-Neighbor
                return (False, "N-TIE to S: never flood")
            elif neighbor_direction == neighbor.Neighbor.Direction.NORTH:
                # Always flood a North-TIE to a North-Neighbor
                return (True, "N-TIE to N: always flood")
            elif neighbor_direction == neighbor.Neighbor.Direction.EAST_WEST:
                # Only flood a North-TIE to an East-West-Neighbor if Top-of-Fabric
                if top_of_fabric:
                    return (True, "N-TIE to EW: top of fabric")
                else:
                    return (False, "N-TIE to EW: not top of fabric")
            else:
                # We cannot determine the direction of the neighbor; don't flood
                assert neighbor_direction is None
                return (False, "N-TIE to ?: never flood")

    def generate_tide(self, neighbor_direction, system_id, level):
        # We generate a single TIDE packet which covers the entire range and we report all TIE
        # headers in that single TIDE packet. We simple assume that it will fit in a single UDP
        # packet which can be up to 64K. And if a single TIE gets added or removed we swallow the
        # cost of regenerating and resending the entire TIDE packet.
        tide_protocol_packet = packet_common.make_tide(
            sender=system_id,
            level=level,
            start_range=self.MIN_TIE_ID,
            end_range=self.MAX_TIE_ID)
        # Apply flooding scope: only include TIEs corresponding to the requested direction
        # The scoping rules in the specification (table 3), somewhat vaguely, say to only "include
        # TIES in flooding scope" in the TIDE. We interpret this to mean that we should only
        # announce a TIE in our TIDE packet, if we were willing to send a TIE to that particular
        # type of neighbor (N, S, EW).
        for tie_protocol_packet in self.ties.values():
            tie_header = tie_protocol_packet.content.tie.header
            (allowed, _reason) = self.is_flood_allowed(tie_header, neighbor_direction,
                                                       system_id, level)
            ##@@ TODO log message
            # if allowed:
            #     outcome = "allowed"
            # else:
            #     outcome = "filtered"
            # self.debug(self._tx_log, ("Add TIE {} to TIDE is {} because {}"
            #                           .format(tie_header, outcome, reason)))
            if allowed:
                packet_common.add_tie_header_to_tide(tide_protocol_packet, tie_header)
        return tide_protocol_packet

    def tie_db_table(self):
        tab = table.Table()
        tab.add_row(self.cli_summary_headers())
        for tie in self.ties.values():
            tab.add_row(self.cli_summary_attributes(tie))
        return tab

    def age_ties(self):
        expired_key_ids = []
        for tie_id, db_tie in self.ties.items():
            db_tie.content.tie.header.remaining_lifetime -= 1
            if db_tie.content.tie.header.remaining_lifetime <= 0:
                expired_key_ids.append(tie_id)
        for key_id in expired_key_ids:
            ##@@ log a message
            del self.ties[key_id]

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
            packet_common.direction_str(tie_id.direction),
            tie_id.originator,
            packet_common.tietype_str(tie_id.tietype),
            tie_id.tie_nr,
            tie.content.tie.header.seq_nr,
            tie.content.tie.header.remaining_lifetime,
            packet_common.element_str(tie_id.tietype, tie.content.tie.element)
        ]
