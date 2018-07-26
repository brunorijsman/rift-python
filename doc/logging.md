# Logging

The RIFT protocol engine write very detailed logging information to the file rift.log in the same directory as where the RIFT engine was started.

You can monitor the log file by running "tail -f":

<pre>
$ <b>tail -f rift.log</b>
2018-07-15 07:47:07,064:INFO:node.if.tx:[667f3a2b1a73cb01-en0] Send LIE ProtocolPacket(header=PacketHeader(level=0, major_version=11, sender=7385685870712703745, minor_version=0), content=PacketContent(tie=None, lie=LIEPacket(holdtime=3, neighbor=Neighbor(remote_id=1, originator=7385685870712594177), not_a_ztp_offer=False, flood_port=10001, name='Brunos-MacBook1-en0', you_are_not_flood_repeater=False, link_mtu_size=1500, local_id=1, pod=0, nonce=6638665728137929476, label=None, capabilities=NodeCapabilities(flood_reduction=True, leaf_indications=1)), tide=None, tire=None))
2018-07-15 07:47:07,065:INFO:node.if.rx:[667f3a2b1a721f01-en0] Receive ProtocolPacket(header=PacketHeader(minor_version=0, major_version=11, level=0, sender=7385685870712703745), content=PacketContent(tide=None, tire=None, tie=None, lie=LIEPacket(local_id=1, name='Brunos-MacBook1-en0', you_are_not_flood_repeater=False, pod=0, capabilities=NodeCapabilities(flood_reduction=True, leaf_indications=1), label=None, flood_port=10001, nonce=6638665728137929476, link_mtu_size=1500, not_a_ztp_offer=False, holdtime=3, neighbor=Neighbor(originator=7385685870712594177, remote_id=1))))
2018-07-15 07:47:07,065:INFO:node.if.rx:[667f3a2b1a73cb01-en0] Receive ProtocolPacket(header=PacketHeader(level=0, major_version=11, sender=7385685870712703745, minor_version=0), content=PacketContent(tie=None, lie=LIEPacket(holdtime=3, neighbor=Neighbor(remote_id=1, originator=7385685870712594177), not_a_ztp_offer=False, flood_port=10001, name='Brunos-MacBook1-en0', you_are_not_flood_repeater=False, link_mtu_size=1500, local_id=1, pod=0, nonce=6638665728137929476, label=None, capabilities=NodeCapabilities(flood_reduction=True, leaf_indications=1)), tide=None, tire=None))
2018-07-15 07:47:07,065:INFO:node.if.fsm:[667f3a2b1a721f01-en0] FSM push event, event=LIE_RECEIVED
2018-07-15 07:47:07,065:INFO:node.if:[667f3a2b1a73cb01-en0] Ignore looped back LIE packet
2018-07-15 07:47:07,065:INFO:node.if.fsm:[667f3a2b1a721f01-en0] FSM process event, state=THREE_WAY event=LIE_RECEIVED event_data=(ProtocolPacket(header=PacketHeader(minor_version=0, major_version=11, level=0, sender=7385685870712703745), content=PacketContent(tide=None, tire=None, tie=None, lie=LIEPacket(local_id=1, name='Brunos-MacBook1-en0', you_are_not_flood_repeater=False, pod=0, capabilities=NodeCapabilities(flood_reduction=True, leaf_indications=1), label=None, flood_port=10001, nonce=6638665728137929476, link_mtu_size=1500, not_a_ztp_offer=False, holdtime=3, neighbor=Neighbor(originator=7385685870712594177, remote_id=1)))), ('192.168.2.163', 55048))
2018-07-15 07:47:07,065:INFO:node.if.fsm:[667f3a2b1a721f01-en0] FSM invoke state-transition action, action=process_lie
2018-07-15 07:47:07,065:INFO:node.if.fsm:[667f3a2b1a721f01-en0] FSM push event, event=UPDATE_ZTP_OFFER
2018-07-15 07:47:07,065:INFO:node.if.fsm:[667f3a2b1a721f01-en0] FSM process event, state=THREE_WAY event=UPDATE_ZTP_OFFER
...
</pre>

The format of the log messages is designed to make it easy to "grep" for particular subsets of information that you might be interested in.

TODO: Provide grep patterns
