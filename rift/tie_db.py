# Topology Information Element DataBase (TIE_DB)

import copy
import sortedcontainers
from py._path import common

import common.ttypes
import common.constants
import encoding.ttypes
import neighbor
import packet_common
import table
import timer

NODE_SOUTH_TIE_NR = 1
NODE_NORTH_TIE_NR = 2

ORIGINATE_LIFETIME = common.constants.default_lifetime
FLUSH_LIFETIME = 60

# TODO: We currently only store the decoded TIE messages.
# Also store the encoded TIE messages for the following reasons:
# - Encode only once, instead of each time the message is sent
# - Ability to flood the message immediately before it is decoded
# Note: the encoded TIE protocol packet that we send is different from the encoded TIE protocol
# packet that we send (specifically, the content is the same but the header reflect us as the
# sender)

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
    if age_diff > common.constants.lifetime_diff2ignore:
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

    def __init__(self, name=None, log=None):
        self._name = name
        self._log = log
        # The ties dictionary contains all TIEPacket objects (not ProtocolPacket objects) indexed
        # by TIEID.
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

    def debug(self, msg):
        if self._log is not None:
            self._log.debug("[%s] %s", self._name, msg)

    def store_tie(self, tie_packet):
        tie_id = tie_packet.header.tieid
        self.ties[tie_id] = tie_packet

    def find_tie(self, tie_id):
        # Returns None if tie_id is not in database
        return self.ties.get(tie_id)

    def start_sending_db_ties_in_range(self, start_sending_tie_headers, start_id, start_incl,
                                       end_id, end_incl):
        db_ties = self.ties.irange(start_id, end_id, (start_incl, end_incl))
        for db_tie_id in db_ties:
            db_tie = self.ties[db_tie_id]
            # TODO: Make sure that lifetime is decreased by at least one before propagating
            start_sending_tie_headers.append(db_tie.header)

    def process_received_tide_packet(self, tide_packet, my_system_id):
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
                if header_in_tide.tieid.originator == my_system_id:
                    # Self-originate an empty TIE with a higher sequence number.
                    bumped_own_tie_header = self.bump_own_tie(db_tie, header_in_tide.tieid)
                    start_sending_tie_headers.append(bumped_own_tie_header)
                else:
                    # We don't have the TIE, request it
                    # To request a a missing TIE, we have to set the seq_nr to 0. This is not
                    # mentioned in the RIFT draft, but it is described in ISIS ISO/IEC 10589:1992
                    # section 7.3.15.2 bullet b.4
                    request_header = header_in_tide
                    request_header.seq_nr = 0
                    request_header.remaining_lifetime = 0
                    request_header.origination_time = None
                    request_tie_headers.append(request_header)
            else:
                comparison = compare_tie_header_age(db_tie.header, header_in_tide)
                if comparison < 0:
                    if header_in_tide.tieid.originator == my_system_id:
                        # Re-originate DB TIE with higher sequence number than the one in TIDE
                        bumped_own_tie_header = self.bump_own_tie(db_tie, header_in_tide.tieid)
                        start_sending_tie_headers.append(bumped_own_tie_header)
                    else:
                        # We have an older version of the TIE, request the newer version
                        request_tie_headers.append(header_in_tide)
                elif comparison > 0:
                    # We have a newer version of the TIE, send it
                    start_sending_tie_headers.append(db_tie.header)
                else:
                    # We have the same version of the TIE, if we are trying to send it, stop it
                    stop_sending_tie_headers.append(db_tie.header)
        # End-gap processing: send TIEs that are in our TIE DB but missing in TIDE
        self.start_sending_db_ties_in_range(start_sending_tie_headers,
                                            last_processed_tie_id, minimum_inclusive,
                                            tide_packet.end_range, True)
        return (request_tie_headers, start_sending_tie_headers, stop_sending_tie_headers)

    def process_received_tire_packet(self, tire_packet):
        request_tie_headers = []
        start_sending_tie_headers = []
        acked_tie_headers = []
        for header_in_tire in tire_packet.headers:
            db_tie = self.find_tie(header_in_tire.tieid)
            if db_tie is not None:
                comparison = compare_tie_header_age(db_tie.header, header_in_tire)
                if comparison < 0:
                    # We have an older version of the TIE, request the newer version
                    request_tie_headers.append(header_in_tire)
                elif comparison > 0:
                    # We have a newer version of the TIE, send it
                    start_sending_tie_headers.append(db_tie.header)
                else:
                    # We have the same version of the TIE, treat it as an ACK
                    acked_tie_headers.append(db_tie.header)
        return (request_tie_headers, start_sending_tie_headers, acked_tie_headers)

    def find_according_real_node_tie(self, rx_tie):
        # We have to originate an empty node TIE for the purpose of flushing it. Use the same
        # contents as the real node TIE that we actually originated, except don't report any
        # neighbors.
        real_node_tie_id = copy.deepcopy(rx_tie.header.tieid)
        if rx_tie.header.tieid.direction == common.ttypes.TieDirectionType.South:
            real_node_tie_id.tie_nr = NODE_SOUTH_TIE_NR
        elif rx_tie.header.tieid.direction == common.ttypes.TieDirectionType.North:
            real_node_tie_id.tie_nr = NODE_NORTH_TIE_NR
        else:
            assert False
        real_node_tie = self.find_tie(real_node_tie_id)
        assert real_node_tie is not None
        return real_node_tie

    def make_according_empty_tie(self, rx_tie):
        new_tie_header = packet_common.make_tie_header(
            rx_tie.header.tieid.direction,
            rx_tie.header.tieid.originator,
            rx_tie.header.tieid.tietype,
            rx_tie.header.tieid.tie_nr,
            rx_tie.header.seq_nr + 1,     # Higher sequence number
            FLUSH_LIFETIME)                     # Short remaining life time
        tietype = rx_tie.header.tieid.tietype
        if tietype == common.ttypes.TIETypeType.NodeTIEType:
            real_node_tie_packet = self.find_according_real_node_tie(rx_tie)
            new_element = copy.deepcopy(real_node_tie_packet.element)
            new_element.node.neighbors = {}
        elif tietype == common.ttypes.TIETypeType.PrefixTIEType:
            empty_prefixes = encoding.ttypes.PrefixTIEElement()
            new_element = encoding.ttypes.TIEElement(prefixes=empty_prefixes)
        elif tietype == common.ttypes.TIETypeType.PositiveDisaggregationPrefixTIEType:
            empty_prefixes = encoding.ttypes.PrefixTIEElement()
            new_element = encoding.ttypes.TIEElement(
                positive_disaggregation_prefixes=empty_prefixes)
        elif tietype == common.ttypes.TIETypeType.NegativeDisaggregationPrefixTIEType:
            # TODO: Policy guided prefixes are not yet in model in specification
            assert False
        elif tietype == common.ttypes.TIETypeType.PGPrefixTIEType:
            # TODO: Policy guided prefixes are not yet in model in specification
            assert False
        elif tietype == common.ttypes.TIETypeType.KeyValueTIEType:
            empty_keyvalues = encoding.ttypes.KeyValueTIEElement()
            new_element = encoding.ttypes.TIEElement(keyvalues=empty_keyvalues)
        else:
            assert False
        according_empty_tie = encoding.ttypes.TIEPacket(
            header=new_tie_header,
            element=new_element)
        return according_empty_tie

    def bump_own_tie(self, db_tie, rx_tie):
        if db_tie is None:
            # We received a TIE (rx_tie) which appears to be self-originated, but we don't have that
            # TIE in our database. Re-originate the "according" (same TIE ID) TIE, but then empty
            # (i.e. no neighbor, no prefixes, no key-values, etc.), with a higher sequence number,
            # and a short remaining life time
            according_empty_tie_packet = self.make_according_empty_tie(rx_tie)
            self.store_tie(according_empty_tie_packet)
            return according_empty_tie_packet.header
        else:
            # Re-originate DB TIE with higher sequence number than the one in RX TIE
            db_tie.header.seq_nr = rx_tie.header.seq_nr + 1
            return db_tie.header

    def process_received_tie_packet(self, rx_tie, my_system_id):
        start_sending_tie_header = None
        ack_tie_header = None
        rx_tie_header = rx_tie.header
        rx_tie_id = rx_tie_header.tieid
        db_tie = self.find_tie(rx_tie_id)
        if db_tie is None:
            if rx_tie_id.originator == my_system_id:
                # Self-originate an empty TIE with a higher sequence number.
                start_sending_tie_header = self.bump_own_tie(db_tie, rx_tie)
            else:
                # We don't have this TIE in the database, store and ack it
                self.store_tie(rx_tie)
                ack_tie_header = rx_tie_header
        else:
            comparison = compare_tie_header_age(db_tie.header, rx_tie_header)
            if comparison < 0:
                # We have an older version of the TIE, ...
                if rx_tie_id.originator == my_system_id:
                    # Re-originate DB TIE with higher sequence number than the one in RX TIE
                    start_sending_tie_header = self.bump_own_tie(db_tie, rx_tie)
                else:
                    # We did not originate the TIE, store the newer version and ack it
                    self.store_tie(rx_tie)
                    ack_tie_header = rx_tie.header
            elif comparison > 0:
                # We have a newer version of the TIE, send it
                start_sending_tie_header = db_tie.header
            else:
                # We have the same version of the TIE, ACK it
                ack_tie_header = db_tie.header
        return (start_sending_tie_header, ack_tie_header)

    def tie_is_self_originated(self, tie_header, my_system_id):
        return tie_header.tieid.originator == my_system_id

    def tie_originator_level(self, tie_header):
        # We cannot determine the level of the originator just by looking at the TIE header; we have
        # to look in the TIE-DB to determine it. We can be confident the TIE is in the TIE-DB
        # because we wouldn't be here, considering sending a TIE to a neighbor, if we did not have
        # the TIE in the TIE-DB. Also, this question can only be asked about Node TIEs (other TIEs
        # don't store the level of the originator in the TIEPacket)
        assert tie_header.tieid.tietype == common.ttypes.TIETypeType.NodeTIEType
        db_tie = self.find_tie(tie_header.tieid)
        if db_tie is None:
            # Just in case it unexpectedly not in the TIE-DB
            return None
        else:
            return db_tie.element.node.level

    def is_flood_allowed(self, tie_header, neighbor_direction, neighbor_system_id, my_system_id,
                         my_level, i_am_top_of_fabric):
        # Note: there is exactly one rule below (the one marked with [*]) which actually depend on
        # the neighbor_system_id. If that rule wasn't there we would have been able to encode a TIDE
        # only one per direction (N, S, EW) instead of once per neighbor, and still follow all the
        # flooding scope rules. We have chosen to follow the rules strictly (not doing so causes all
        # sorts of other complications), so -alas- we swallow the performance overhead of encoding
        # separate TIDE packets for every individual neighbor. TODO: I may revisit this decision
        # when the exact nature of the "other complications" (namely persistent oscillations) are
        # better understood (correctness first, performance later).
        # See https://www.dropbox.com/s/b07dnhbxawaizpi/zoom_0.mp4?dl=0 for a video recording of a
        # discussion where these complications were discussed in detail.
        if tie_header.tieid.direction == common.ttypes.TieDirectionType.South:
            # S-TIE
            if tie_header.tieid.tietype == common.ttypes.TIETypeType.NodeTIEType:
                # Node S-TIE
                if neighbor_direction == neighbor.Neighbor.Direction.SOUTH:
                    # Node S-TIE to S: Flood if level of originator is same as level of this node
                    if self.tie_originator_level(tie_header) == my_level:
                        return (True, "Node S-TIE to S: originator level is same as mine")
                    else:
                        return (False, "Node S-TIE to S: originator level is not same as mine")
                elif neighbor_direction == neighbor.Neighbor.Direction.NORTH:
                    # Node S-TIE to N: flood if level of originator is higher than level of this
                    # node
                    originator_level = self.tie_originator_level(tie_header)
                    if originator_level is None:
                        return (False, "Node S-TIE to N: could not determine originator level")
                    elif originator_level > my_level:
                        return (True, "Node S-TIE to N: originator level is higher than mine")
                    else:
                        return (False, "Node S-TIE to N: originator level is not higher than mine")
                elif neighbor_direction == neighbor.Neighbor.Direction.EAST_WEST:
                    # Node S-TIE to EW: Flood only if this node is not top of fabric
                    if i_am_top_of_fabric:
                        return (False, "Node S-TIE to EW: this node is top of fabric")
                    else:
                        return (True, "Node S-TIE to EW: this node is not top of fabric")
                else:
                    # Node S-TIE to ?: We can't determine the direction of the neighbor; don't flood
                    assert neighbor_direction is None
                    return (False, "Node S-TIE to ?: never flood")
            else:
                # Non-Node S-TIE
                if neighbor_direction == neighbor.Neighbor.Direction.SOUTH:
                    # Non-Node S-TIE to S: Flood self-originated only
                    if self.tie_is_self_originated(tie_header, my_system_id):
                        return (True, "Non-node S-TIE to S: self-originated")
                    else:
                        return (False, "Non-node S-TIE to S: not self-originated")
                elif neighbor_direction == neighbor.Neighbor.Direction.NORTH:
                    # [*] Non-Node S-TIE to N: Flood only if the neighbor is the originator of
                    # the TIE
                    if neighbor_system_id == tie_header.tieid.originator:
                        return (True, "Non-node S-TIE to N: neighbor is originator of TIE")
                    else:
                        return (False, "Non-node S-TIE to N: neighbor is not originator of TIE")
                elif neighbor_direction == neighbor.Neighbor.Direction.EAST_WEST:
                    # Non-Node S-TIE to EW: Flood only if if self-originated and this node is not
                    # ToF
                    if i_am_top_of_fabric:
                        return (False, "Non-node S-TIE to EW: this top of fabric")
                    elif self.tie_is_self_originated(tie_header, my_system_id):
                        return (True, "Non-node S-TIE to EW: self-originated and not top of fabric")
                    else:
                        return (False, "Non-node S-TIE to EW: not self-originated")
                else:
                    # We cannot determine the direction of the neighbor; don't flood
                    assert neighbor_direction is None
                    return (False, "None-node S-TIE to ?: never flood")
        else:
            # S-TIE
            assert tie_header.tieid.direction == common.ttypes.TieDirectionType.North
            if neighbor_direction == neighbor.Neighbor.Direction.SOUTH:
                # S-TIE to S: Never flood
                return (False, "N-TIE to S: never flood")
            elif neighbor_direction == neighbor.Neighbor.Direction.NORTH:
                # S-TIE to N: Always flood
                return (True, "N-TIE to N: always flood")
            elif neighbor_direction == neighbor.Neighbor.Direction.EAST_WEST:
                # S-TIE to EW: Flood only if this node is top of fabric
                if i_am_top_of_fabric:
                    return (True, "N-TIE to EW: top of fabric")
                else:
                    return (False, "N-TIE to EW: not top of fabric")
            else:
                # S-TIE to ?: We cannot determine the direction of the neighbor; don't flood
                assert neighbor_direction is None
                return (False, "N-TIE to ?: never flood")

    def generate_tide_packet(self, neighbor_direction, neighbor_system_id, my_system_id, my_level,
                             i_am_top_of_fabric):
        # We generate a single TIDE packet which covers the entire range and we report all TIE
        # headers in that single TIDE packet. We simple assume that it will fit in a single UDP
        # packet which can be up to 64K. And if a single TIE gets added or removed we swallow the
        # cost of regenerating and resending the entire TIDE packet.
        tide_packet = packet_common.make_tide_packet(
            start_range=self.MIN_TIE_ID,
            end_range=self.MAX_TIE_ID)
        # Apply flooding scope: only include TIEs corresponding to the requested direction
        # The scoping rules in the specification (table 3), somewhat vaguely, say to only "include
        # TIES in flooding scope" in the TIDE. We interpret this to mean that we should only
        # announce a TIE in our TIDE packet, if we were willing to send a TIE to that particular
        # type of neighbor (N, S, EW).
        for tie_packet in self.ties.values():
            tie_header = tie_packet.header
            (allowed, reason) = self.is_flood_allowed(tie_header, neighbor_direction,
                                                      neighbor_system_id, my_system_id, my_level,
                                                      i_am_top_of_fabric)
            if allowed:
                outcome = "allowed"
            else:
                outcome = "filtered"
            self.debug("Add TIE {} to TIDE is {} because {}".format(tie_header, outcome, reason))
            if allowed:
                packet_common.add_tie_header_to_tide(tide_packet, tie_header)
        return tide_packet

    def tie_db_table(self):
        tab = table.Table()
        tab.add_row(self.cli_summary_headers())
        for tie in self.ties.values():
            tab.add_row(self.cli_summary_attributes(tie))
        return tab

    def age_ties(self):
        expired_key_ids = []
        for tie_id, db_tie in self.ties.items():
            db_tie.header.remaining_lifetime -= 1
            if db_tie.header.remaining_lifetime <= 0:
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

    def cli_summary_attributes(self, tie_packet):
        tie_id = tie_packet.header.tieid
        return [
            packet_common.direction_str(tie_id.direction),
            tie_id.originator,
            packet_common.tietype_str(tie_id.tietype),
            tie_id.tie_nr,
            tie_packet.header.seq_nr,
            tie_packet.header.remaining_lifetime,
            packet_common.element_str(tie_id.tietype, tie_packet.element)
        ]
