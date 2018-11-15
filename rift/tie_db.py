# Topology Information Element DataBase (TIE_DB)

import collections
import copy
import heapdict
import sortedcontainers
from py._path import common

import common.ttypes
import common.constants
import encoding.ttypes
import neighbor
import packet_common
import table
import timer

MY_TIE_NR = 1

FLUSH_LIFETIME = 60

TIE_SOUTH = common.ttypes.TieDirectionType.South
TIE_NORTH = common.ttypes.TieDirectionType.North

NEIGHBOR_NORTH = neighbor.Neighbor.Direction.NORTH
NEIGHBOR_SOUTH = neighbor.Neighbor.Direction.SOUTH
NEIGHBOR_EAST_WEST = neighbor.Neighbor.Direction.EAST_WEST

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

class SPFNode:

    # TODO: Add support for Non-Equal Cost Multi-Path (NECMP)

    def __init__(self, cost):
        # Cost of best-known path to this node (is always a single cost, even in the case of ECMP)
        self.cost = cost
        # System-ID of node before this node (predecessor) on best known path (*)
        # (*) here and below means: contains more than one element in the case of ECMP
        self.predecessors = []
        # (if_name, addr) of direct next-hop from source node towards this node (*)
        self.direct_nexthops = []

    def add_predecessor(self, predecessor_system_id):
        self.predecessors.append(predecessor_system_id)

    def add_direct_next_hop(self, direct_next_hop_if, direct_next_hop_addr):
        direct_next_hop = (direct_next_hop_if, direct_next_hop_addr)
        if direct_next_hop not in self.direct_nexthops:
            self.direct_nexthops.append(direct_next_hop)

    def inherit_direct_next_hops(self, other_spf_node):
        for direct_next_hop in other_spf_node.direct_nexthops:
            if direct_next_hop not in self.direct_nexthops:
                self.direct_nexthops.append(direct_next_hop)

    def __repr__(self):
        return (
            "SPFInfo(" +
            "cost={}, ".format(self.cost) +
            "predecessors={}, ".format(self.predecessors) +
            "direct_nexthops={})".format(self.direct_nexthops))

# pylint: disable=invalid-name
class TIE_DB:

    # TODO: Use constant from Thrift file (it is currently not there, but Tony said he added it)
    # Don't use the actual lowest value 0 (which is enum value Illegal) for direction or tietype,
    # but value 1 (direction South) or value 2 (tietype TieTypeNode). Juniper RIFT doesn't accept
    # illegal values.
    MIN_TIE_ID = encoding.ttypes.TIEID(
        direction=TIE_SOUTH,
        originator=0,
        tietype=common.ttypes.TIETypeType.NodeTIEType,
        tie_nr=0)
    # For the same reason don't use DirectionMaxValue or TIETypeMaxValue but North and
    # KeyValueTIEType instead
    MAX_TIE_ID = encoding.ttypes.TIEID(
        direction=TIE_NORTH,
        originator=packet_common.MAX_U64,
        tietype=common.ttypes.TIETypeType.KeyValueTIEType,
        tie_nr=packet_common.MAX_U32)

    MIN_SPF_INTERVAL = 1.0
    SPF_TRIGGER_HISTORY_LENGTH = 10

    def __init__(self, name, system_id, parent_log=None):
        # TODO: Should we also pass my_level and i_am_top_of_fabric here? If so, make sure to update
        # them, because they can change as a result of ZTP.
        self._name = name
        self._system_id = system_id
        if parent_log is None:
            self._tie_db_log = None
            self._spf_log = None
        else:
            self._tie_db_log = parent_log.getChild("tie_db")
            self._spf_log = parent_log.getChild("spf")
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
        self._defer_spf_timer = None
        self._spf_triggers_count = 0
        self._spf_triggers_deferred_count = 0
        self._spf_deferred_trigger_pending = False
        self._spf_runs_count = 0
        self._spf_trigger_history = collections.deque([], self.SPF_TRIGGER_HISTORY_LENGTH)
        self._spf_nodes = {}

    def db_debug(self, msg):
        if self._tie_db_log is not None:
            self._tie_db_log.debug("[%s] %s", self._name, msg)

    def spf_debug(self, msg):
        if self._spf_log is not None:
            self._spf_log.debug("[%s] %s", self._name, msg)

    def ties_different_enough_to_trigger_spf(self, old_tie, new_tie):
        # Only TIEs with the same TIEID should be compared
        assert old_tie.header.tieid == new_tie.header.tieid
        # Any change in seq_nr triggers an SPF
        if old_tie.header.seq_nr != new_tie.header.seq_nr:
            return True
        # All remaining_lifetime values are the same, except zero, for the purpose of running SPF
        if (old_tie.header.remaining_lifetime == 0) and (new_tie.header.remaining_lifetime != 0):
            return True
        if (old_tie.header.remaining_lifetime != 0) and (new_tie.header.remaining_lifetime == 0):
            return True
        # Ignore any changes in origination_lifetime for the purpose of running SPF (TODO: really?)
        # Any change in the element contents (node, prefixes, etc.) trigger an SPF
        if old_tie.element != new_tie.element:
            return True
        # If we get here, nothing of relevance to SPF changed
        return False

    def store_tie(self, tie_packet):
        tie_id = tie_packet.header.tieid
        if tie_id in self.ties:
            old_tie_packet = self.ties[tie_id]
            trigger_spf = self.ties_different_enough_to_trigger_spf(old_tie_packet, tie_packet)
            if trigger_spf:
                reason = "TIE " + packet_common.tie_id_str(tie_id) + " changed"
        else:
            trigger_spf = True
            reason = "TIE " + packet_common.tie_id_str(tie_id) + " added"
        self.ties[tie_id] = tie_packet
        if trigger_spf:
            self.trigger_spf(reason)

    def remove_tie(self, tie_id):
        # It is not an error to attempt to delete a TIE which is not in the database
        if tie_id in self.ties:
            del self.ties[tie_id]
            reason = "TIE " + packet_common.tie_id_str(tie_id) + " removed"
            self.trigger_spf(reason)

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

    def process_received_tide_packet(self, tide_packet):
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
                if header_in_tide.tieid.originator == self._system_id:
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
                    if header_in_tide.tieid.originator == self._system_id:
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
        real_node_tie_id.tie_nr = MY_TIE_NR
        real_node_tie = self.find_tie(real_node_tie_id)
        assert real_node_tie is not None
        return real_node_tie

    def make_according_empty_tie(self, rx_tie):
        new_tie_header = packet_common.make_tie_header(
            rx_tie.header.tieid.direction,
            rx_tie.header.tieid.originator,
            rx_tie.header.tieid.tietype,
            rx_tie.header.tieid.tie_nr,
            rx_tie.header.seq_nr + 1,           # Higher sequence number
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
            # TODO: Negative disaggregation prefixes are not yet in model in specification
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

    def process_received_tie_packet(self, rx_tie):
        start_sending_tie_header = None
        ack_tie_header = None
        rx_tie_header = rx_tie.header
        rx_tie_id = rx_tie_header.tieid
        db_tie = self.find_tie(rx_tie_id)
        if db_tie is None:
            if rx_tie_id.originator == self._system_id:
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
                if rx_tie_id.originator == self._system_id:
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

    def tie_is_originated_by_node(self, tie_header, node_system_id):
        return tie_header.tieid.originator == node_system_id

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

    def is_flood_allowed(self,
                         tie_header,
                         to_node_direction,
                         to_node_system_id,
                         from_node_system_id,
                         from_node_level,
                         from_node_is_top_of_fabric):
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
        if tie_header.tieid.direction == TIE_SOUTH:
            # S-TIE
            if tie_header.tieid.tietype == common.ttypes.TIETypeType.NodeTIEType:
                # Node S-TIE
                if to_node_direction == NEIGHBOR_SOUTH:
                    # Node S-TIE to S: Flood if level of originator is same as level of this node
                    if self.tie_originator_level(tie_header) == from_node_level:
                        return (True, "Node S-TIE to S: originator level is same as from-node")
                    else:
                        return (False, "Node S-TIE to S: originator level is not same as from-node")
                elif to_node_direction == NEIGHBOR_NORTH:
                    # Node S-TIE to N: flood if level of originator is higher than level of this
                    # node
                    originator_level = self.tie_originator_level(tie_header)
                    if originator_level is None:
                        return (False, "Node S-TIE to N: could not determine originator level")
                    elif originator_level > from_node_level:
                        return (True, "Node S-TIE to N: originator level is higher than from-node")
                    else:
                        return (False,
                                "Node S-TIE to N: originator level is not higher than from-node")
                elif to_node_direction == NEIGHBOR_EAST_WEST:
                    # Node S-TIE to EW: Flood only if this node is not top of fabric
                    if from_node_is_top_of_fabric:
                        return (False, "Node S-TIE to EW: from-node is top of fabric")
                    else:
                        return (True, "Node S-TIE to EW: from-node is not top of fabric")
                else:
                    # Node S-TIE to ?: We can't determine the direction of the neighbor; don't flood
                    assert to_node_direction is None
                    return (False, "Node S-TIE to ?: never flood")
            else:
                # Non-Node S-TIE
                if to_node_direction == NEIGHBOR_SOUTH:
                    # Non-Node S-TIE to S: Flood self-originated only
                    if self.tie_is_originated_by_node(tie_header, from_node_system_id):
                        return (True, "Non-node S-TIE to S: self-originated")
                    else:
                        return (False, "Non-node S-TIE to S: not self-originated")
                elif to_node_direction == NEIGHBOR_NORTH:
                    # [*] Non-Node S-TIE to N: Flood only if the neighbor is the originator of
                    # the TIE
                    if to_node_system_id == tie_header.tieid.originator:
                        return (True, "Non-node S-TIE to N: to-node is originator of TIE")
                    else:
                        return (False, "Non-node S-TIE to N: to-node is not originator of TIE")
                elif to_node_direction == NEIGHBOR_EAST_WEST:
                    # Non-Node S-TIE to EW: Flood only if if self-originated and this node is not
                    # ToF
                    if from_node_is_top_of_fabric:
                        return (False, "Non-node S-TIE to EW: this top of fabric")
                    elif self.tie_is_originated_by_node(tie_header, from_node_system_id):
                        return (True, "Non-node S-TIE to EW: self-originated and not top of fabric")
                    else:
                        return (False, "Non-node S-TIE to EW: not self-originated")
                else:
                    # We cannot determine the direction of the neighbor; don't flood
                    assert to_node_direction is None
                    return (False, "None-node S-TIE to ?: never flood")
        else:
            # S-TIE
            assert tie_header.tieid.direction == TIE_NORTH
            if to_node_direction == NEIGHBOR_SOUTH:
                # S-TIE to S: Never flood
                return (False, "N-TIE to S: never flood")
            elif to_node_direction == NEIGHBOR_NORTH:
                # S-TIE to N: Always flood
                return (True, "N-TIE to N: always flood")
            elif to_node_direction == NEIGHBOR_EAST_WEST:
                # S-TIE to EW: Flood only if this node is top of fabric
                if from_node_is_top_of_fabric:
                    return (True, "N-TIE to EW: top of fabric")
                else:
                    return (False, "N-TIE to EW: not top of fabric")
            else:
                # S-TIE to ?: We cannot determine the direction of the neighbor; don't flood
                assert to_node_direction is None
                return (False, "N-TIE to ?: never flood")

    def is_flood_allowed_from_node_to_neighbor(self,
                                               tie_header,
                                               neighbor_direction,
                                               neighbor_system_id,
                                               node_system_id,
                                               node_level,
                                               node_is_top_of_fabric):
        return self.is_flood_allowed(
            tie_header=tie_header,
            to_node_direction=neighbor_direction,
            to_node_system_id=neighbor_system_id,
            from_node_system_id=node_system_id,
            from_node_level=node_level,
            from_node_is_top_of_fabric=node_is_top_of_fabric)

    def is_flood_allowed_from_neighbor_to_node(self,
                                               tie_header,
                                               neighbor_direction,
                                               neighbor_system_id,
                                               neighbor_level,
                                               neighbor_is_top_of_fabric,
                                               node_system_id):
        if neighbor_direction == NEIGHBOR_SOUTH:
            neighbor_reverse_direction = NEIGHBOR_NORTH
        elif neighbor_direction == NEIGHBOR_NORTH:
            neighbor_reverse_direction = NEIGHBOR_SOUTH
        else:
            neighbor_reverse_direction = neighbor_direction
        return self.is_flood_allowed(
            tie_header=tie_header,
            to_node_direction=neighbor_reverse_direction,
            to_node_system_id=node_system_id,
            from_node_system_id=neighbor_system_id,
            from_node_level=neighbor_level,
            from_node_is_top_of_fabric=neighbor_is_top_of_fabric)

    def generate_tide_packet(self,
                             neighbor_direction,
                             neighbor_system_id,
                             neighbor_level,
                             neighbor_is_top_of_fabric,
                             my_level,
                             i_am_top_of_fabric):
        # pylint:disable=too-many-locals
        #
        # The algorithm for deciding which TIE headers go into a TIDE packet are based on what is
        # described as "the solution to oscillation #1" in slide deck
        # http://bit.ly/rift-flooding-oscillations-v1. During the RIFT core team conference call on
        # 19 Oct 2018, Tony reported that the RIFT specification was already updated with the same
        # rules, but IMHO sections Table 3 / B.3.1. / B.3.2.1 in the draft are still ambiguous and
        # I am not sure if they specify the same behavior.
        #
        # We generate a single TIDE packet which covers the entire range and we report all TIE
        # headers in that single TIDE packet. We simple assume that it will fit in a single UDP
        # packet which can be up to 64K. And if a single TIE gets added or removed we swallow the
        # cost of regenerating and resending the entire TIDE packet.
        tide_packet = packet_common.make_tide_packet(
            start_range=self.MIN_TIE_ID,
            end_range=self.MAX_TIE_ID)
        # Look at every TIE in our database, and decide whether or not we want to include it in the
        # TIDE packet. This is a rather expensive process, which is why we want to minimize the
        # the number of times this function is run.
        for tie_packet in self.ties.values():
            tie_header = tie_packet.header
            # The first possible reason for including a TIE header in the TIDE is to announce that
            # we have a TIE that we want to send to the neighbor. In other words the TIE in the
            # flooding scope from us to the neighbor.
            (allowed, reason1) = self.is_flood_allowed_from_node_to_neighbor(
                tie_header,
                neighbor_direction,
                neighbor_system_id,
                self._system_id,
                my_level,
                i_am_top_of_fabric)
            if allowed:
                self.db_debug("Include TIE {} in TIDE because {} (perspective us to neighbor)"
                              .format(tie_header, reason1))
                packet_common.add_tie_header_to_tide(tide_packet, tie_header)
                continue
            # The second possible reason for including a TIE header in the TIDE is because the
            # neighbor might be considering to send the TIE to us, and we want to let the neighbor
            # know that we already have the TIE and what version it it.
            (allowed, reason2) = self.is_flood_allowed_from_neighbor_to_node(
                tie_header,
                neighbor_direction,
                neighbor_system_id,
                neighbor_level,
                neighbor_is_top_of_fabric,
                self._system_id)
            if allowed:
                self.db_debug("Include TIE {} in TIDE because {} (perspective neighbor to us)"
                              .format(tie_header, reason2))
                packet_common.add_tie_header_to_tide(tide_packet, tie_header)
                continue
            # If we get here, we decided not to include the TIE header in the TIDE
            self.db_debug("Exclude TIE {} in TIDE because {} (perspective us to neighbor) and "
                          "{} (perspective neighbor to us)".format(tie_header, reason1, reason2))
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
            self.remove_tie(key_id)

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

    def trigger_spf(self, reason):
        self._spf_triggers_count += 1
        self._spf_trigger_history.appendleft(reason)
        if self._defer_spf_timer is None:
            self.start_defer_spf_timer()
            self._spf_deferred_trigger_pending = False
            self.spf_debug("Trigger and run SPF: {}".format(reason))
            self.run_spf()
        else:
            self._spf_deferred_trigger_pending = True
            self._spf_triggers_deferred_count += 1
            self.spf_debug("Trigger and defer SPF: {}".format(reason))

    def start_defer_spf_timer(self):
        self._defer_spf_timer = timer.Timer(
            interval=self.MIN_SPF_INTERVAL,
            expire_function=self.defer_spf_timer_expired,
            periodic=False,
            start=True)

    def defer_spf_timer_expired(self):
        self._defer_spf_timer = None
        if self._spf_deferred_trigger_pending:
            self.start_defer_spf_timer()
            self._spf_deferred_trigger_pending = False
            self.spf_debug("Run deferred SPF")
            self.run_spf()

    def node_ties(self, direction, system_id):
        # Return an ordered list of all node TIEs from the given node and in the given direction
        node_ties = []
        start_tie_id = packet_common.make_tie_id(
            direction, system_id, common.ttypes.TIETypeType.NodeTIEType, 0)
        end_tie_id = packet_common.make_tie_id(
            direction, system_id, common.ttypes.TIETypeType.NodeTIEType, packet_common.MAX_U32)
        node_tie_ids = self.ties.irange(start_tie_id, end_tie_id, (True, True))
        for node_tie_id in node_tie_ids:
            node_tie = self.ties[node_tie_id]
            node_ties.append(node_tie)
        return node_ties

    def node_neighbors(self, node_ties, neighbor_direction):
        # A generator that yields (nbr_system_id, nbr_tie_element) tuples for all neighbors in the
        # specified direction of the nodes in the node_ties list.
        for node_tie in node_ties:
            node_level = node_tie.element.node.level
            for nbr_system_id, nbr_tie_element in node_tie.element.node.neighbors.items():
                nbr_level = nbr_tie_element.level
                if neighbor_direction == NEIGHBOR_SOUTH:
                    correct_direction = (nbr_level < node_level)
                elif neighbor_direction == NEIGHBOR_NORTH:
                    correct_direction = (nbr_level > node_level)
                elif neighbor_direction == NEIGHBOR_EAST_WEST:
                    correct_direction = (nbr_level == node_level)
                else:
                    assert False
                if correct_direction:
                    yield (nbr_system_id, nbr_tie_element)

    def run_spf(self):
        self._spf_runs_count += 1
        # TODO: Currently we simply always run both North-SPF and South-SPF, but maybe we can be
        # more intelligent about selectively triggering North-SPF and South-SPF separately.
        self.run_direction_spf(TIE_SOUTH)
        ###@@@ self.run_direction_spf(TIE_NORTH)

    def run_direction_spf(self, tie_direction):
        # pylint:disable=too-many-locals
        # pylint:disable=too-many-statements

        # For the intermediate daily commit -- disable the code for now
        # pylint:disable=W0101
        return

        ###@@@ While testing, only run SPF on node core_1
        if self._name != "core_1":
            return

        print("\n*** SPF run, name =", self._name, " direction =", tie_direction, "***\n")

        # Candidates is a priority queue that contains the system_ids of candidate nodes with the
        # best known cost thus far as the priority. A node is a candidate if we know some path to
        # the node, but we have not yet established whether or not that path is the best path.
        # We use module heapdict (as opposed to the more widely used heapq module) because we need
        # an efficient way to decrease the priority of an element which is already on the priority
        # queue. Heapq only allows you to do this by calling the internal method _siftdown (see
        # http://bit.ly/siftdown)
        candidates = heapdict.heapdict()

        # Initially, there is one node in the candidates heap, namely the starting node (i.e. this
        # node) with cost zero.
        candidates[self._system_id] = 0

        # Visited is a set that contains the system_ids of the nodes that have already been visited,
        # i.e. for which the best path has definitely been determined.
        visited = set()

        # spf_nodes contains all SPF-related information for each candidate and each visited
        # node. After the SPF run is complete, we maintain the spf_nodes for debugging purposes;
        # you can use the "show spf" command to see the results of the most recent SPF run.
        # TODO: implement that command
        self._spf_nodes = {}
        self._spf_nodes[self._system_id] = SPFNode(cost=0)

        # Which neighbors of the currently visited node are we considering?
        # TODO: When do we consider EAST-WEST as well?
        if tie_direction == TIE_SOUTH:
            nbr_direction = NEIGHBOR_SOUTH
            reverse_nbr_direction = NEIGHBOR_NORTH
            reverse_tie_direction = TIE_NORTH
        elif tie_direction == TIE_NORTH:
            nbr_direction = NEIGHBOR_NORTH
            reverse_nbr_direction = NEIGHBOR_SOUTH
            reverse_tie_direction = TIE_SOUTH
        else:
            assert False

        # Keep going until we have no more candidates
        while candidates:

            # Remove the candidate node with the lowest cost from the candidate priority queue.
            candidate_entry = candidates.popitem()
            (candidate_system_id, candidate_cost) = candidate_entry
            print("Removed from candidates: cost =", candidate_cost,
                  "system_id =", candidate_system_id)

            # If we have already visited the node (i.e. if we already definitely know the best path)
            # skip the candidate.
            if candidate_system_id in visited:
                print("Candidate already visited")
                continue

            # Locate the Dir-Node-TIE(s) of the visited node, where Dir is the direction of the SPF.
            # If we cannot find the Node-TIE, move on to the next candidate without adding the node
            # to the visited list.
            ###@@@: TODO: The spec clearly says that for the top node we need to use tie_direction
            # instead of reverse_tie_direction, but that doesn't work for the deeper nodes (about
            # which the spec is vaguer)
            candidate_node_ties = self.node_ties(reverse_tie_direction, candidate_system_id)
            if candidate_node_ties == []:
                print("Cannot locate Node TIEs for candidate")
                continue

            # Add that node to the visited list.
            visit_entry = candidate_entry
            (visit_system_id, visit_cost) = visit_entry
            visit_node_ties = candidate_node_ties
            visited.add(visit_system_id)
            print("Add to visited: cost =", visit_cost, "system_id =", visit_system_id)

            # Consider each neighbor of the visited node in the right direction.
            for nbr in self.node_neighbors(visit_node_ties, nbr_direction):

                # Debug print
                (nbr_system_id, nbr_tie_element) = nbr
                print("Considering neighbor: nbr_system_id =", nbr_system_id)

                # Locate the OpDir-Node-TIE(s) of the neighbor node, where OpDir is the opposite
                # direction of the SPF. If we cannot find the Node-TIE, move on to the next neighbor
                # without adding this neighbor to the candidate priority queue.
                nbr_node_ties = self.node_ties(reverse_tie_direction, nbr_system_id)
                if nbr_node_ties == []:
                    continue
                print("Neighbor has Node-TIE(s)")

                # Check for bi-directional connectivity: the neighbor must report the visited node
                # as an adjacency with the same link-id pair (in reverse). If connectivity is not
                # bi-directional, move on to the next neighbor without adding adding this neighbor
                # to the candidate priority queue.
                bidirectional = False
                for nbr_nbr in self.node_neighbors(nbr_node_ties, reverse_nbr_direction):
                    (nbr_nbr_system_id, nbr_nbr_tie_element) = nbr_nbr
                    # Does the neighbor report the visited node as its neighbor?
                    if nbr_nbr_system_id != visit_system_id:
                        continue
                    # Are the link_ids bidirectional?
                    if not self.bidirectional_link_ids(nbr_tie_element.link_ids,
                                                       nbr_nbr_tie_element.link_ids):
                        continue
                    # Yes, connectivity is bidirectional
                    bidirectional = True
                    break
                if not bidirectional:
                    continue
                print("Visited node and neighbor have bidirectional connectivity")

                # We have found a feasible path to the neighbor. What is the cost of this path?
                new_nbr_cost = visit_cost + nbr_tie_element.cost
                print("Discovered new path to neighbor: cost =", new_nbr_cost)

                # Did we already have some path to the neighbor?
                if nbr_system_id not in self._spf_nodes:

                    # TODO: Direct next-hop interface names and addresses for first hop

                    # Put the following in a common routine

                    # We did not have any previous path to the neighbor. The new path to the
                    # neighbor is the best path.
                    print("First candidate path to neighbor")
                    spf_node = SPFNode(new_nbr_cost)
                    spf_node.add_predecessor(visit_system_id)
                    spf_node.inherit_direct_next_hops(self._spf_nodes[visit_system_id])
                    self._spf_nodes[nbr_system_id] = spf_node

                    # Store the neighbor as a candidate
                    candidates[nbr_system_id] = new_nbr_cost

                else:

                    # We already had a previous path to the neighbor. How does the new path compare
                    # to the existing path in terms of cost?
                    nbr_spf_node = self._spf_nodes[nbr_system_id]
                    if new_nbr_cost > nbr_spf_node.cost:

                        # The new path is strictly worse than the existing path. Do nothing.
                        print("New path is worse than existing path - keep using old path")

                    elif new_nbr_cost < nbr_spf_node.cost:

                        # The new path is strictly better than the existing path. Replace the
                        # existing path with the new path.
                        print("New path is better than existing path - use new path")

                        # TODO: Implement this

                        # Update (lower) the cost of the candidate in the priority queue
                        candidates[nbr_system_id] = new_nbr_cost

                    else:

                        # The new path is equal cost to the existing path. Add an ECMP path to the
                        # existing path.
                        assert new_nbr_cost == nbr_spf_node.cost
                        print("New path is equal cost to existing path - use new path")
                        # TODO: Implement this



        print("SPF nodes:")
        for system_id, spf_node in self._spf_nodes.items():
            print(system_id, spf_node)

    def bidirectional_link_ids(self, link_ids_1, link_ids_2):
        # Does the set link_ids_1 contain any link-id (local_id, remote_id) which is present in
        # reverse (remote_id, local_id) in set link_ids_2?
        for id1 in link_ids_1:
            for id2 in link_ids_2:
                if (id1.local_id == id2.remote_id) and (id1.remote_id == id2.local_id):
                    return True
        return False
