import collections
import encoding.ttypes
import packet_common
import table
import timer

class _MsgQueueBase:

    """
    The message queue base class (MsgQueueBase) is the base class that abstracts the common
    behavior for enqueueing, transmiting, and potentially retransmiting TIE messages and TIRE
    messages (i.e. TIE requests and TIE acknowledgements).

    It currently encapsulated the following common behavior for all message queues:
    - Manage the queue of TIE messages to be sent.
    - Manage the queue of TIEs to be requested in a TIRE message.
    - Manage the queue of TIEs to be acknowledged in a TIRE message.
    - When something is queued to be sent for the first time, send it out after a very short delay
      (the short delay is intended to enable the packing of multiple items into a single message)
    - When a header is added to the queue and it is not already there, put it in the fast queue,
      and start a fast timer, if it is not already running.
    - Use a slow timer to periodically retrasmit items on the queue if they are not removed.

    It may seem like overkill to put all of this in a base class, but it opens up the path to
    potential enhancements in the future, such as:
    - For TIE messages (but not TIRE messages): send them immediately instead of after a short
      delay when they are first enqueued (TIREs messages need packing, but TIE messages not).
    - Combine the TIE-request TIRE message and the TIE-ack TIRE message into a single TIRE message.
    - Pacing messages (i.e. avoiding large bursts of messages).
    - Dynamic pacing, based on the drop rate inferred from gaps in the sequence number in received
      messages.
    - More precise retransmits. Instead of having one slow timer tick, but retransmits into several
      buckets and service them with a more fine-grained timer.
    """

    def __init__(self, interface, with_lifetime):
        self._interface = interface
        self._with_lifetime = with_lifetime
        self._tx_queue = collections.OrderedDict()
        self._rtx_queue = collections.OrderedDict()

    def add_tie_header(self, tie_header):
        assert not self._with_lifetime
        assert tie_header.__class__ == encoding.ttypes.TIEHeader
        tie_header_lifetime = encoding.ttypes.TIEHeaderWithLifeTime(header=tie_header)
        self._add_tie_header_common(tie_header_lifetime)

    def add_tie_header_lifetime(self, tie_header_lifetime):
        assert self._with_lifetime
        self._add_tie_header_common(tie_header_lifetime)

    def _add_tie_header_common(self, tie_header_lifetime):
        assert tie_header_lifetime.__class__ == encoding.ttypes.TIEHeaderWithLifeTime
        tie_header = tie_header_lifetime.header
        tie_id = tie_header.tieid
        if tie_id in self._tx_queue:
            # Message is already on the fast initial transmit queue, just update the message.
            assert tie_id not in self._rtx_queue
            self._tx_queue[tie_id] = tie_header_lifetime
        elif tie_id in self._rtx_queue:
            # The message is already on slow retransmit queue.
            if tie_header.seq_nr > self._rtx_queue[tie_id].header.seq_nr:
                # This is a newer version of the TIE, move it to the fast initial transmit queue,
                # and update the message.
                del self._rtx_queue[tie_id]
                self._tx_queue[tie_id] = tie_header_lifetime
            else:
                # Not a newer version of the TIE, update the message on the slow retransmit queue.
                self._rtx_queue[tie_id] = tie_header_lifetime
        else:
            # Not in any queue yet. Add it to the intial fast transmit queue
            self._tx_queue[tie_id] = tie_header_lifetime

    def remove_tie_id(self, tie_id):
        if tie_id in self._tx_queue:
            del self._tx_queue[tie_id]
        if tie_id in self._rtx_queue:
            del self._rtx_queue[tie_id]

    def search_tie_id(self, tie_id):
        value = self._tx_queue.get(tie_id)
        if value:
            return value
        return self._tx_queue.get(tie_id)

    def clear(self):
        self._tx_queue.clear()
        self._rtx_queue.clear()

    def need_fast_timer(self):
        return len(self._tx_queue) > 0

    def need_slow_timer(self):
        return len(self._rtx_queue) > 0

    def service_tx_queue(self):
        self.service_queue(self._tx_queue)
        # Move all items from the tx_queue to the rtx_queue
        for tie_id, tie_header in self._tx_queue.items():
            self._rtx_queue[tie_id] = tie_header
        self._tx_queue.clear()

    def service_rtx_queue(self):
        self.service_queue(self._rtx_queue)

    def _add_row_to_cli_table(self, tab, value, transmission):
        if self._with_lifetime:
            header = value.header
            lifetime = value.remaining_lifetime
        else:
            header = value
            lifetime = None
        row = [packet_common.direction_str(header.tieid.direction),
               header.tieid.originator,
               packet_common.tietype_str(header.tieid.tietype),
               header.tieid.tie_nr,
               header.seq_nr]
        if self._with_lifetime:
            row.append(lifetime)
        row.append(transmission)
        tab.add_row(row)

    def cli_table(self):
        tab = table.Table()
        header_row = ["Direction", "Originator", "Type", "TIE Nr", "Seq Nr"]
        if self._with_lifetime:
            header_row.append(["Remaining", "Lifetime"])
        header_row.append("Transmission")
        tab.add_row(header_row)
        for value in self._tx_queue.values():
            self._add_row_to_cli_table(tab, value, "Initial")
        for value in self._rtx_queue.values():
            self._add_row_to_cli_table(tab, value, "Retransmission")
        return tab


class _TIEQueue(_MsgQueueBase):

    def __init__(self, interface):
        _MsgQueueBase.__init__(self, interface, with_lifetime=False)

    def service_queue(self, queue):
        node = self._interface.node
        for tie_id in queue.keys():
            # We only look at the TIE-ID in the queue and not at the header. If we have a more
            # recent version of the TIE in the TIE-DB than the one requested in the queue, send the
            # one we have.
            db_tie_packet_info = node.find_tie_packet_info(tie_id)
            if db_tie_packet_info is not None:
                ###@@@ DEBUG
                if tie_id.tietype == 5 and node.name == "spine-1-1":
                    if queue == self._tx_queue:
                        queue_name = "fast"
                    elif queue == self._rtx_queue:
                        queue_name = "slow"
                    self._interface._log.critical("[%s] send TIE %s on %s queue" %
                                                (self._interface._log_id, str(tie_id), queue_name))
                ###@@@
                self._interface.send_packet_info(db_tie_packet_info, flood=True)


class _TIEReqQueue(_MsgQueueBase):

    def __init__(self, interface):
        _MsgQueueBase.__init__(self, interface, with_lifetime=True)

    def service_queue(self, queue):
        if not queue:
            return
        interface = self._interface
        node = interface.node
        tire_packet = packet_common.make_tire_packet()
        for tie_header_lifetime in queue.values():
            # We don't request a TIE from our neighbor if the flooding scope rules say that the
            # neighbor is not allowed to flood the TIE to us. Why? Because the neighbor is allowed
            # to advertise extra TIEs in the TIDE, and if we request them we will get an
            # oscillation.
            (allowed, _reason) = node.flood_allowed_from_nbr_to_node(
                tie_header=tie_header_lifetime.header,
                neighbor_direction=interface.neighbor_direction(),
                neighbor_system_id=interface.neighbor.system_id,
                neighbor_level=interface.neighbor.level,
                neighbor_is_top_of_fabric=interface.neighbor.top_of_fabric(),
                node_system_id=node.system_id)
            if allowed:
                packet_common.add_tie_header_to_tire(tire_packet, tie_header_lifetime)
            else:
                # TODO: log message
                pass
        packet_content = encoding.ttypes.PacketContent(tire=tire_packet)
        packet_header = encoding.ttypes.PacketHeader(sender=node.system_id,
                                                     level=node.level_value())
        protocol_packet = encoding.ttypes.ProtocolPacket(header=packet_header,
                                                         content=packet_content)
        self._interface.send_protocol_packet(protocol_packet, flood=True)


class _TIEAckQueue(_MsgQueueBase):

    def __init__(self, interface):
        _MsgQueueBase.__init__(self, interface, with_lifetime=True)

    def service_queue(self, queue):
        if not queue:
            return
        node = self._interface.node
        tire_packet = packet_common.make_tire_packet()
        for tie_header_lifetime in queue.values():
            packet_common.add_tie_header_to_tire(tire_packet, tie_header_lifetime)
        packet_content = encoding.ttypes.PacketContent(tire=tire_packet)
        packet_header = encoding.ttypes.PacketHeader(sender=node.system_id,
                                                     level=node.level_value())
        protocol_packet = encoding.ttypes.ProtocolPacket(header=packet_header,
                                                         content=packet_content)
        self._interface.send_protocol_packet(protocol_packet, flood=True)


class MsgQueues:

    _FAST_INITIAL_TRANSMIT_INTERVAL = 0.05
    _SLOW_SUBSEQUENT_RETRANSMIT_INTERVAL = 1.0

    def __init__(self, interface):
        self._tie_queue = _TIEQueue(interface)
        self._tie_req_queue = _TIEReqQueue(interface)
        self._tie_ack_queue = _TIEAckQueue(interface)
        self._fast_timer = timer.Timer(
            interval=self._FAST_INITIAL_TRANSMIT_INTERVAL,
            expire_function=self._fast_initial_transmit_timer_expired,
            periodic=True,
            start=False)
        self._slow_timer = timer.Timer(
            interval=self._SLOW_SUBSEQUENT_RETRANSMIT_INTERVAL,
            expire_function=self._slow_subsequent_retransmit_timer_expired,
            periodic=True,
            start=False)

    def add_to_tie_queue(self, tie_header):
        self._tie_queue.add_tie_header(tie_header)
        self._start_or_stop_timers_as_needed()

    def remove_from_tie_queue(self, tie_id):
        self._tie_queue.remove_tie_id(tie_id)
        self._start_or_stop_timers_as_needed()

    def add_to_tie_req_queue(self, tie_header_lifetime):
        self._tie_req_queue.add_tie_header_lifetime(tie_header_lifetime)
        self._start_or_stop_timers_as_needed()

    def remove_from_tie_req_queue(self, tie_id):
        self._tie_req_queue.remove_tie_id(tie_id)
        self._start_or_stop_timers_as_needed()

    def add_to_tie_ack_queue(self, tie_header_lifetime):
        self._tie_ack_queue.add_tie_header_lifetime(tie_header_lifetime)
        self._start_or_stop_timers_as_needed()

    def remove_from_tie_ack_queue(self, tie_id):
        self._tie_ack_queue.remove_tie_id(tie_id)
        self._start_or_stop_timers_as_needed()

    def search_tie_ack_queue(self, tie_id):
        return self._tie_ack_queue.search_tie_id(tie_id)

    def remove_from_all_queues(self, tie_id):
        self._tie_queue.remove_tie_id(tie_id)
        self._tie_req_queue.remove_tie_id(tie_id)
        self._tie_ack_queue.remove_tie_id(tie_id)
        self._start_or_stop_timers_as_needed()

    def clear_all_queues(self):
        self._tie_queue.clear()
        self._tie_req_queue.clear()
        self._tie_ack_queue.clear()
        self._start_or_stop_timers_as_needed()

    def _start_or_stop_timers_as_needed(self):
        # Start or stop fast timer for initial transmissions, as needed.
        need_fast_timer = (self._tie_queue.need_fast_timer() or
                           self._tie_req_queue.need_fast_timer() or
                           self._tie_ack_queue.need_fast_timer())
        if need_fast_timer:
            # Start fast timer if it is not already running.
            if not self._fast_timer.running():
                self._fast_timer.start()
        else:
            # Stop fast timer if it is running.
            if self._fast_timer.running():
                self._fast_timer.stop()
        # Start or stop slow timer for subsequent retransmissions, as needed.
        need_slow_timer = (self._tie_queue.need_slow_timer() or
                           self._tie_req_queue.need_slow_timer() or
                           self._tie_ack_queue.need_slow_timer())
        if need_slow_timer:
            # Start slow timer if it is not already running.
            if not self._slow_timer.running():
                self._slow_timer.start()
        else:
            # Stop slow timer if it is running.
            if self._slow_timer.running():
                self._slow_timer.stop()

    def _fast_initial_transmit_timer_expired(self):
        self._tie_queue.service_tx_queue()
        self._tie_req_queue.service_tx_queue()
        self._tie_ack_queue.service_tx_queue()

    def _slow_subsequent_retransmit_timer_expired(self):
        self._tie_queue.service_rtx_queue()
        self._tie_req_queue.service_rtx_queue()
        self._tie_ack_queue.service_rtx_queue()

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
        tab = self._tie_req_table()
        cli_session.print(tab.to_string())
