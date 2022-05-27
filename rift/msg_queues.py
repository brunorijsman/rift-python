import collections
import datetime
import inspect
import encoding.ttypes
import packet_common
import table
import timer

_SHORT_DELAY_TICKS = 1
_LONG_DELAY_TICKS = 5
_TICK_INTERVAL = 0.2

# Set these to debug tie database synchronization
DEBUG_PRINT = False                # True to enable debug printing
DEBUG_CHECK_TIE_ENCODING = False   # True to check whether pre-encoded TIEs are correct
DEBUG_NODE_NAME = None             # None for all nodes, or name of specific node to debug
DEBUG_TIE_DIRECTION = None         # None for all directions, or direction constant
DEBUG_TIE_ORIGINATOR = None        # None for all originators, or system id or originator
DEBUG_TIE_TYPE = None              # None for all tie types, or tie type constant

class _MsgQueueBase:

    """
    The message queue base class (MsgQueueBase) is the base class that abstracts the common
    behavior for enqueueing, transmiting, and potentially retransmiting TIE messages and TIRE
    messages (i.e. TIE requests and TIE acknowledgements).

    It currently encapsulated the following common behavior for all message queues:
    - Manage the queue of TIE messages to be sent.
    - Manage the queue of TIEs to be requested in a TIRE message.
    - Manage the queue of TIEs to be acknowledged in a TIRE message.
    - When something is queued to be sent for the first time, send it out after a very short delay,
      namely after INITAL_DELAY_TICKS timer ticks. The short delay is intended to enable the packing
      of multiple items into a single message.
    - After that, as long as the item remains in the queue, it is re-transmitted every
      RETRANSMIT_DELAY_TICKS timer ticks after that.

    It may seem like overkill to put all of this in a base class, but it opens up the path to
    potential enhancements in the future, such as:
    - For TIE messages (but not TIRE messages): send them immediately instead of after a short
      delay when they are first enqueued (TIREs messages need packing, but TIE messages not).
    - Combine the TIE-request TIRE message and the TIE-ack TIRE message into a single TIRE message.
    - Pacing messages (i.e. avoiding large bursts of messages).
    - Dynamic pacing, based on the drop rate inferred from gaps in the sequence number in received
      messages.
    """

    def __init__(self, name, interface, with_lifetime):
        self._name = name
        self._interface = interface
        self._with_lifetime = with_lifetime
        # Queue key is TIE-ID
        # Queue value is (delay_ticks, TIEHeaderWithLifeTime)
        self._queue = collections.OrderedDict()

    def _debug_tie_id(self, tie_id):
        node_name = self._interface.node.name
        if DEBUG_NODE_NAME is not None and node_name != DEBUG_NODE_NAME:
            return False
        if DEBUG_TIE_DIRECTION is not None and tie_id.direction != DEBUG_TIE_DIRECTION:
            return False
        if DEBUG_TIE_ORIGINATOR is not None and tie_id.originator != DEBUG_TIE_ORIGINATOR:
            return False
        if DEBUG_TIE_TYPE is not None and tie_id.tietype != DEBUG_TIE_TYPE:
            return False
        return True

    @staticmethod
    def _timestamp():
        return datetime.datetime.now().strftime("%Y-%m-%d-%H:%M:%S.%f")

    def _debug(self, operation, tie_id, seq_nr):
        if not DEBUG_PRINT or not self._debug_tie_id(tie_id):
            return
        print("{} {}: {} {} queue for interface {}, tie_id={} seq_nr={}"
              .format(self._timestamp(), self._interface.node.name, operation, self._name,
                      self._interface.name, tie_id, seq_nr))
        stack = inspect.stack()
        stack = stack[:-6]
        for frame in stack[1:]:
            print("  {}:{}:{} ".format(frame.filename, frame.lineno, frame.function))

    def add_tie_header(self, tie_header):
        assert not self._with_lifetime
        assert tie_header.__class__ == encoding.ttypes.TIEHeader
        tie_header_lifetime = encoding.ttypes.TIEHeaderWithLifeTime(
            header=tie_header, remaining_lifetime=0)
        self._add_tie_header_common(tie_header_lifetime)

    def add_tie_header_lifetime(self, tie_header_lifetime):
        assert self._with_lifetime
        assert tie_header_lifetime.__class__ == encoding.ttypes.TIEHeaderWithLifeTime
        self._add_tie_header_common(tie_header_lifetime)

    def _add_tie_header_common(self, tie_header_lifetime):
        tie_header = tie_header_lifetime.header
        tie_id = tie_header.tieid
        # Decide how fast we want to send the message
        if tie_id in self._queue:
            (old_delay_ticks, old_tie_header_lifetime) = self._queue[tie_id]
            if tie_header.seq_nr > old_tie_header_lifetime.header.seq_nr:
                # Message is newer version than the one on the queue. Short delay.
                new_delay_ticks = _SHORT_DELAY_TICKS
            else:
                # Message is same versionas the one on the queue. Keep same delay as queued msg.
                new_delay_ticks = old_delay_ticks
        else:
            # Message is not yet on queue. Short delay.
            new_delay_ticks = _SHORT_DELAY_TICKS
        # Put message on queue with updated delay.
        self._queue[tie_id] = (new_delay_ticks, tie_header_lifetime)
        self._debug("add to", tie_header.tieid, tie_header.seq_nr)

    def remove_tie_id(self, tie_id):
        if tie_id in self._queue:
            del self._queue[tie_id]
            self._debug("remove from", tie_id, None)

    def search_tie_id(self, tie_id):
        result = self._queue.get(tie_id)
        if result:
            (_delay_ticks, tie_header_lifetime) = result
            return tie_header_lifetime
        return None

    def clear(self):
        self._queue.clear()

    def need_timer(self):
        return len(self._queue) > 0

    def service_queue(self):
        # This is not the most efficient implementation in the world. We iterate over the entire
        # queue every time tick. But that is okay. Most of the time, these queues are empty, and
        # when they are not, they tend to be very short.
        if not self._queue:
            return
        new_queue = collections.OrderedDict()
        added_at_least_one = False
        for tie_id, value in self._queue.items():
            (delay_ticks, tie_header_lifetime) = value
            assert tie_header_lifetime.header.tieid == tie_id
            assert delay_ticks > 0
            delay_ticks -= 1
            if delay_ticks == 0:
                if not added_at_least_one:
                    self.start_message()
                if self.add_to_message(tie_header_lifetime):
                    added_at_least_one = True
                delay_ticks = _LONG_DELAY_TICKS
            new_queue[tie_id] = (delay_ticks, tie_header_lifetime)
        if added_at_least_one:
            self.end_message()
        self._queue = new_queue

    def _add_row_to_cli_table(self, tab, delay_ticks, tie_header_lifetime):
        header = tie_header_lifetime.header
        lifetime = tie_header_lifetime.remaining_lifetime
        row = [packet_common.direction_str(header.tieid.direction),
               header.tieid.originator,
               packet_common.tietype_str(header.tieid.tietype),
               header.tieid.tie_nr,
               header.seq_nr]
        if self._with_lifetime:
            row.append(lifetime)
        row.append("{:.2f}".format(delay_ticks * _TICK_INTERVAL))
        tab.add_row(row)

    def cli_table(self):
        tab = table.Table()
        header_row = ["Direction", "Originator", "Type", "TIE Nr", "Seq Nr"]
        if self._with_lifetime:
            header_row.append(["Remaining", "Lifetime"])
        header_row.append(["Send", "Delay"])
        tab.add_row(header_row)
        for value in self._queue.values():
            (delay_ticks, tie_header_lifetime) = value
            self._add_row_to_cli_table(tab, delay_ticks, tie_header_lifetime)
        return tab


class _TIEQueue(_MsgQueueBase):

    def __init__(self, interface):
        _MsgQueueBase.__init__(self, "tie", interface, with_lifetime=False)

    def start_message(self):
        pass

    def end_message(self):
        pass

    def add_to_message(self, tie_header_lifetime):
        # Send a separate TIE message each time this function is called.
        # We only look at the TIE-ID in the queue and not at the header. If we have a more
        # recent version of the TIE in the TIE-DB than the one requested in the queue, send the
        # one we have.
        tie_id = tie_header_lifetime.header.tieid
        node = self._interface.node
        db_tie_packet_info = node.find_tie_packet_info(tie_id)
        if db_tie_packet_info is None:
            if DEBUG_PRINT and self._debug_tie_id(tie_id):
                # Print a message for debugging
                print("{} {}: interface {} could not send tie-id {} (not in tie-db)"
                      .format(self._timestamp(), self._interface.node.name, self._interface.name,
                              tie_id))
                return False
        if DEBUG_PRINT and self._debug_tie_id(tie_id):
            # Print a message for debugging
            print("{} {}: interface {} send tie-id {} tie {}"
                  .format(self._timestamp(), self._interface.node.name, self._interface.name,
                          tie_id, db_tie_packet_info))
        if DEBUG_CHECK_TIE_ENCODING and self._debug_tie_id(tie_id):
            # Check whehter the pre-computed encoded packet is correct.
            check_packet_info = packet_common.encode_protocol_packet(
                db_tie_packet_info.protocol_packet, self._interface.active_outer_key)
            if (db_tie_packet_info.encoded_protocol_packet !=
                    check_packet_info.encoded_protocol_packet):
                print("{} {}: interface {} tie-id {} encoding is INCORRECT"
                      .format(self._timestamp(), self._interface.node.name,
                              self._interface.name, tie_id))
        self._interface.send_packet_info(db_tie_packet_info, flood=True)
        return True


class _TIEReqQueue(_MsgQueueBase):

    def __init__(self, interface):
        _MsgQueueBase.__init__(self, "req", interface, with_lifetime=False)
        self._tire_packet = None

    def start_message(self):
        self._tire_packet = packet_common.make_tire_packet()

    def end_message(self):
        node = self._interface.node
        packet_content = encoding.ttypes.PacketContent(tire=self._tire_packet)
        packet_header = encoding.ttypes.PacketHeader(sender=node.system_id,
                                                     level=node.level_value())
        protocol_packet = encoding.ttypes.ProtocolPacket(header=packet_header,
                                                         content=packet_content)
        self._interface.send_protocol_packet(protocol_packet, flood=True)
        self._tire_packet = None

    def add_to_message(self, tie_header_with_lifetime):
        # We don't request a TIE from our neighbor if the flooding scope rules say that the
        # neighbor is not allowed to flood the TIE to us. Why? Because the neighbor is allowed
        # to advertise extra TIEs in the TIDE, and if we request them we will get an
        # oscillation.
        tie_header = tie_header_with_lifetime.header
        tie_id = tie_header.tieid
        node = self._interface.node
        (allowed, reason) = node.flood_allowed_from_nbr_to_node(
            tie_header=tie_header,
            neighbor_direction=self._interface.neighbor_direction(),
            neighbor_system_id=self._interface.neighbor_lie.system_id,
            neighbor_level=self._interface.neighbor_lie.level,
            neighbor_is_top_of_fabric=self._interface.neighbor_lie.top_of_fabric(),
            node_system_id=node.system_id)
        if allowed:
            # TIE requests in a TIRE must have remaining lifetime zero
            tie_header_lifetime = packet_common.expand_tie_header_with_lifetime(tie_header, 0)
            packet_common.add_tie_header_to_tire(self._tire_packet, tie_header_lifetime)
            return True
        self._interface.warning(
            "TIE %s, which was in %s queue, could not be sent because %s", tie_id, self._name,
            reason)
        return False


class _TIEAckQueue(_MsgQueueBase):

    def __init__(self, interface):
        _MsgQueueBase.__init__(self, "ack", interface, with_lifetime=True)
        self._tire_packet = None

    def start_message(self):
        self._tire_packet = packet_common.make_tire_packet()

    def end_message(self):
        node = self._interface.node
        packet_content = encoding.ttypes.PacketContent(tire=self._tire_packet)
        packet_header = encoding.ttypes.PacketHeader(sender=node.system_id,
                                                     level=node.level_value())
        protocol_packet = encoding.ttypes.ProtocolPacket(header=packet_header,
                                                         content=packet_content)
        self._interface.send_protocol_packet(protocol_packet, flood=True)
        self._tire_packet = None

    def add_to_message(self, tie_header_lifetime):
        packet_common.add_tie_header_to_tire(self._tire_packet, tie_header_lifetime)
        return True


class MsgQueues:

    def __init__(self, interface):
        self._tie_queue = _TIEQueue(interface)
        self._tie_req_queue = _TIEReqQueue(interface)
        self._tie_ack_queue = _TIEAckQueue(interface)
        self._tick_timer = timer.Timer(
            interval=_TICK_INTERVAL,
            expire_function=self._tick_timer_expired,
            periodic=True,
            start=False)

    def add_to_tie_queue(self, tie_header):
        self._tie_queue.add_tie_header(tie_header)
        self._start_or_stop_timer_as_needed()

    def remove_from_tie_queue(self, tie_id):
        self._tie_queue.remove_tie_id(tie_id)
        self._start_or_stop_timer_as_needed()

    def add_to_tie_req_queue(self, tie_header):
        self._tie_req_queue.add_tie_header(tie_header)
        self._start_or_stop_timer_as_needed()

    def remove_from_tie_req_queue(self, tie_id):
        self._tie_req_queue.remove_tie_id(tie_id)
        self._start_or_stop_timer_as_needed()

    def add_to_tie_ack_queue(self, tie_header_lifetime):
        self._tie_ack_queue.add_tie_header_lifetime(tie_header_lifetime)
        self._start_or_stop_timer_as_needed()

    def remove_from_tie_ack_queue(self, tie_id):
        self._tie_ack_queue.remove_tie_id(tie_id)
        self._start_or_stop_timer_as_needed()

    def search_tie_ack_queue(self, tie_id):
        return self._tie_ack_queue.search_tie_id(tie_id)

    def remove_from_all_queues(self, tie_id):
        self._tie_queue.remove_tie_id(tie_id)
        self._tie_req_queue.remove_tie_id(tie_id)
        self._tie_ack_queue.remove_tie_id(tie_id)
        self._start_or_stop_timer_as_needed()

    def clear_all_queues(self):
        self._tie_queue.clear()
        self._tie_req_queue.clear()
        self._tie_ack_queue.clear()
        self._start_or_stop_timer_as_needed()

    def _start_or_stop_timer_as_needed(self):
        # Start or stop fast timer for initial transmissions, as needed.
        need_timer = (self._tie_queue.need_timer() or
                      self._tie_req_queue.need_timer() or
                      self._tie_ack_queue.need_timer())
        if need_timer:
            # Start timer if it is not already running.
            if not self._tick_timer.running():
                self._tick_timer.start()
        else:
            # Stop timer if it is running.
            if self._tick_timer.running():
                self._tick_timer.stop()

    def _tick_timer_expired(self):
        self._tie_queue.service_queue()
        self._tie_req_queue.service_queue()
        self._tie_ack_queue.service_queue()

    def _tie_table(self):
        return self._tie_queue.cli_table()

    def _tie_req_table(self):
        return self._tie_req_queue.cli_table()

    def _tie_ack_table(self):
        return self._tie_ack_queue.cli_table()

    def command_show_intf_queues(self, cli_session):
        cli_session.print("Transmit queue:")
        tab = self._tie_table()
        cli_session.print(tab.to_string())
        cli_session.print("Request queue:")
        tab = self._tie_req_table()
        cli_session.print(tab.to_string())
        cli_session.print("Acknowledge queue:")
        tab = self._tie_ack_table()
        cli_session.print(tab.to_string())
