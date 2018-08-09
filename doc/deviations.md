# Deviations

This section describes places where this Python RIFT engine implementation consciously an purposly deviates from the draft-ietf-rift-rift-02 specification.

| ID | Short description |
| --- | --- |
| DEV-1 | [Remove event WithdrawNeighborOffer from the ZTP FSM](#remove-event-withdrawneighboroffer-from-the-ztp-fsm) |
| DEV-2 | [Remove event UpdateZTPOffer from the LIE FSM](#remove-event-updateztpoffer-from-the-lie-fsm) |
| DEV-3 | [Do not actually remove offers but mark them as removed](#do-not-actually-remove-offers-but-mark-them-as-removed) |
| DEV-4 | [Rules for accepting a received LIE message](#rules-for-accepting-a-received-lie-message)
| DEV-5 | [Remove event ChangeLocalLeafIndications from ZTP FSM](#remove-event-changelocalleafindications-from-ztp-fsm) |
| DEV-6 | [Use real ZTP hold down timer](#use-real-ztp-hold-down-timer) |
| DEV-6 | [Use real ZTP hold down timer](#use-real-ztp-hold-down-timer) |
| DEV-7 | [Pushed events vs chained event](#pushed-events-vs-chained-events) |
## Remove event WithdrawNeighborOffer from the ZTP FSM

The ZTP state machine has an event "NeighborOffer". In the description of this event it is explictly mentioned that the level is optional, i.e. the level could be absent which means UNDEFINED_LEVEL. I interpret the absence of a level field to mean that the offer is withdrawn. This assumption is confirmed by the fact that the action for the event NeighborOffer has an explicit "if no level offered then REMOVE_OFFER else ...". 

If these interpretations are correct, then why is there a separate event WithdrawNeighborOffer which causes an unconditional action "REMOVE_OFFER"? What is the difference between the event NeighborOffer with an absent level, and the event WithdrawNeighborOffer? It seems to me we don't need the WithdrawNeighborOffer event.

This implementation only implements the NeighborOffer event. The actions for this event also handle the case that the offer is absent (i.e. the offer is withdrawn)

This is not expected to cause any interoperability issues with other implementations. Just is just a simplification of the internal state machine which does not change the external behavior in any observable way.

**PRZ 8/18 Comment: OK, I'll remove from the ZTP FSM in the spec. Reason for the event is that they may be internal implementation events that forces offer removal on FSM even if the peer did not remove it.**

## Remove event UpdateZTPOffer from the LIE FSM

The LIE FSM contains an event UpdateZTPOffer. This event is handled exactly the same in all three states: the action is always "send offer to ZTP FSM", and the to-state is always the same as the from-state (i.e. no state change). Futhermore, the event UpdateZTPOffer is pushed in exactly one place, namely in section B.1.4.2 in the PROCESS_LIE procedure.

This implementation simplifies the FSM. Instead of pushing event UpdateZTPOffer in PROCESS_LIE, which causes an action "send offer to ZTP FSM" later on when the event is processed, we can simply invoke action "send offer to ZTP FSM" in PROCESS_LIE immediately without needing an event UpdateZTPOffer.

Not only does this simplify the state machine, but it also reduces the number of events in the logs  and in the FSM history reports, because currently there is an UpdateZTPOffer every time a LIE message is received, i.e. every second by default.

If execute the action "send offer to ZTP FSM" immediately when the LIE is received instead of pushing an UpdateZTPOffer event, then the "send offer to ZTP FSM" action happens "later" instead of "now". We need to consider carefully if the state of the RIFT engine could have changed between "now" and "later":

* The level and not_a_ztp_offer fields in the received LIE message don't change, they are what they are.

* No other events could possible be pushed between "now" and "later", because if any events are pushed in PROCESS_LIE, the UpdateZTPOffer event is always the first event that is pushed

* No LIE FSM state change can happen between "now" and "later", because (a) the UpdateZTPOffer event is only pushed in the PROCESS_LIE procedure and (b) the PROCESS_LIE procedure is only invoked in transitions that are triggered by the LieRcvd event and (c) none of the LieRcvd events *directly* cause the state of the FSM to change and (d) the PROCESS_LIE procedure can cause the state of the FSM to change but only through pushed events and (e) those pushed events that might cause the state to change are always pushed after the UpdateZTPOffer event is pushed.

Thus, since nothing relevant changes between "now" and "later" it is safe to perform the "send offer to ZTP FSM" "now" instead of pushing an UpdateZTPOffer event and doing it "later". In other words, it is safe to remove event UpdateZTPOffer from the FSM.

Note this is related to deviation DEV-1. Since the LIE FSM only mentions an action "send offer to ZTP FSM" and never mentions any action "withdraw offer from ZTP FSM", this further strengthens the position that the event WithdrawNeighborOffer can be removed as suggested in deviation DEV-1.

This is not expected to cause any interoperability issues with other implementations. Just is just a simplification of the internal state machine which does not change the external behavior in any observable way.

**PRZ 8/18 Comment: The state changed between now and later is precisely the FSM event queue processing discussion we had today. I think having the event can be beneficial in couple things, first, each state can have different code in the action it executes for e.g. stats purposes, beside, the FSM has to return something when sending fails and if you have a separate action it makes for much simpler debugging since PROCESS_LIE is one big transition and can produce bunch of failures in real scenarios. Having said that, an implementation is _perfectly_ free to do what you suggest as long it exhibits external behaviour identical to the spec FSM.**

## Do not actually remove offers but mark them as removed

There are various scenarios where a received LIE message contains the optional level field, but offer is removed anyway, such as:

* The flag not_a_ztp_offer is true

* The received level <= leaf_level

* The hold timer expires

Instead of actually removing the offer, we keep the offer, but mark it with a removed flag and a removed-reason string. This makes debugging and trouble-shooting easier.

**PRZ 8/18 Comment: Suggest a text in the spec and I'll include as mild implementation guideline**

## Rules for accepting a received LIE message

Section 4.2.2 contains 8 bullet points that specify the conditions for accepting a received LIE message and estabilishing a three-way adjacency.

Section B.1.4 also contains rules for accepting a received LIE message and establishing a three-way adjacency.

The rules in section 4.2.2 are *not* consistent with the rules in section B.1.4, specifically:

* Rules 4.2.2.1 and 4.2.2.3 about PoD membership are missing from section B.1.4

* Rule 4.2.2.5 about the different system IDs is missing from section B.1.4

* Rule 4.2.2.6 about the same MTU is missing from section B.1.4

* The rules in section 4.2.2.8 are different from the corresponding rules in section B.1.4.2.

**PRZ 8/18 Comment: Perfect catches due to spec evolving ;-) 
  MTU & PoD events added & drop to oneway just like UnacceptableHeader;
  I think I catch both invalid ID and own system ID both already, check committed -03 on repo;
  be more specific on 4.2.2.8 you see differing;
  I'll regenerate the FSM section after I wrote this comments;**
  
**PRZ 8/18 Comment: Generally it's interesting whether we should scrap 4.2.2 completely and refer to 
  FSM or say "FSM is indicative, 4.2.2 is normative"** 

## Remove event ChangeLocalLeafIndications from ZTP FSM

In this implementation, the configured level and the leaf flags are combined into one single configurable parameter, called the "configured level symbol".

The configured level symbol determines the configured level, the leaf flags, as well as the superspine flag (which is not mentioned in the ZTP FSM) as follows:

| Configured level symbol | Configured level | Leaf only flag | leaf-2-leaf flag | superspine flag |
| --- | ---| --- | --- | --- |
| undefined | undefined | false | false | false |
| leaf | 0 | true | false | false |
| leaf-2-leaf | 0 | true | true | false |
| superspine | 24 | false | false | true |
| integer value | integer value | true iff value == 0 | false | false |

As a result, the events ChangeLocalLeafIndications and ChangeLocalConfiguredLevel are combined into a single event ChangeLocalConfiguredLevel.

The ChangeLocalConfiguredLevel is pushed whenever the conifigured level is changed. The action is store_level which also updates the leaf flags and the superspine flag.

**PRZ 8/18 Comment: All fine as long behavior is equivalent to FSM. Superspine flag will become prominent with the
  new sections on partitioned fabric.**

## Use real ZTP hold down timer

The ZTP FSM uses a hold down timer to manage the time spent in state HoldingDown. There is a ShortTic event that is generated at fixed intervals. The timer is implemented "manually" by counting the number of ShortTic events, and when a threshold is reached, a HoldDownExpired event is generated. I call this a "manual" implementation of a timer.

The Timer class in Python RIFT supports "real" timers. You can start a timer with an arbitrary expiry time, and an event can be generated when the timer expires, without the need for counting ticks.

We use a "real" timer to implement the ZTP hold down timer, and hence we don't need any ShortTic events.

**PRZ 8/18 Comment: All fine as long behavior is equivalent to FSM.**

## Pushed events vs chained event

There are two circumstances in the specification that may case an event to be pushed to a Finite 
State Machine (FSM):

1) Events that are pushed by external events (timer expiry, message reception, etc.) Let's call
these "normal" events.

2) Events that are pushed as part of a FSM transition. Let's call these "chained" events.

The specification doesn't mention anything about these two types of events being processed any
differently.

In our implementation we *do* treat normal events and chained events slightly differently in the
order in which they are processed:

1) Normal events are queued in a the "normal" event queue (attribute _event_queue in class Fsm).

2) Chained events are queued in a separate "chained" event queue (attribute _chained_event_queue
in class Fsm).

Events in the chained event queue are always processed before event in the normal event queue.
This means that if a transition causes any "chained" events to be pushed, those events will be
processed immediately before any "normal" events causes by external factors will be processed.

Why is this needed? Consider the following example from the LIE FSM:
imagine a LIE message is received, and immediately after that, the timer expires.

If all pushed events (both normal and chained) were processed in the order in which they are 
pushed, the following would happen:

| State | Event / Transition | Root cause |
| --- | --- | --- | --- |
| ONE \_WAY | LIE received, push LIE \_RECEIVED event | LIE message receipt |
| ONE \_WAY | Timer expires, push TIMER \_TICK event | Timer expiry |
| ONE \_WAY | LIE \_RECEIVED [ONE \_WAY] > process \_lie, NEW \_NEIGHBOR [None] | LIE message receipt |
| ONE \_WAY | TIMER \_TICK [ONE \_WAY] > SEND \_LIE [None] | Timer expiry |
| ONE \_WAY | NEW \_NEIGHBOR [ONE \_WAY] > SEND \_LIE [TWO \_WAY] | LIE message receipt |
| TWO \_WAY | SEND \_LIE [TWO \_WAY] > send \_lie [None] | Timer expiry |

Note that the events and transitions which are the result of the LIE message receipt are 
interleaved with the event and transitions which are the result of the timer expiry.

In particular, note that the timer expired in state ONE \_WAY, but the corresponding send \_lie
action happens in the TWO \_WAY state. In this particular example, it doesn't matter that much,
but one can imagine FSMs where it would be disastrous is an event leads to a sequence of actions
where some actions are execute in one state and other actions are executed in another state.

With the new rule of always finishing chained actions before considering the next normal action,
we get the following sequence of events:

| State | Type event | Event / Transition | Root cause |
| --- | --- | --- | --- |
| ONE \_WAY | N/A | LIE received, push LIE \_RECEIVED event | LIE message receipt |
| ONE \_WAY | N/A | Timer expires, push TIMER \_TICK event | Timer expiry |
| ONE \_WAY | Normal | LIE \_RECEIVED [ONE \_WAY] > process \_lie, NEW \_NEIGHBOR [None] | LIE message receipt |
| ONE \_WAY | Chained | NEW \_NEIGHBOR [ONE \_WAY] > SEND \_LIE [TWO \_WAY] | LIE message receipt |
| TWO \_WAY | Normal | TIMER \_TICK [TWO \_WAY] > SEND \_LIE [None] | Timer expiry |
| TWO \_WAY | Chained | SEND \_LIE [TWO \_WAY] > send \_lie [None] | Timer expiry |

Not only does this rule avoid hypothetical incorrect behavior, it is also much easier to 
understand and hence debug.

**PRZ 8/18 Comment: We discussed that out today on the bug section.**