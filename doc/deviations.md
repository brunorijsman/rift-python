# Deviations

This section describes places where this Python RIFT engine implementation consciously an purposly deviates from the draft-ietf-rift-rift-02 specification.

| ID | Short description |
| --- | --- |
| DEV-1 | [Remove event WithdrawNeighborOffer from the ZTP FSM](#remove-event-withdrawneighboroffer-from-the-ztp-fsm) |
| DEV-2 | [Remove event UpdateZTPOffer from the LIE FSM](#remove-event-updateztpoffer-from-the-lie-fsm) |
| DEV-3 | [Do not actually remove offers but mark them as removed](#do-not-actually-remove-offers-but-mark-them-as-removed) |
| DEV-4 | [Rules for accepting a received LIE message](#rules-for-accepting-a-received-lie-message)
| DEV-5 | [Remove event ChangeLocalLeafIndications from ZTP FSM](#remove-event-changelocalleafindications-from-ztp-fsm) |
| DEV-6 | [Use real ZTP hold timer](#use-real-ztp-hold-timer) |

## Remove event WithdrawNeighborOffer from the ZTP FSM

The ZTP state machine has an event "NeighborOffer". In the description of this event it is explictly mentioned that the level is optional, i.e. the level could be absent which means UNDEFINED_LEVEL. I interpret the absence of a level field to mean that the offer is withdrawn. This assumption is confirmed by the fact that the action for the event NeighborOffer has an explicit "if no level offered then REMOVE_OFFER else ...". 

If these interpretations are correct, then why is there a separate event WithdrawNeighborOffer which causes an unconditional action "REMOVE_OFFER"? What is the difference between the event NeighborOffer with an absent level, and the event WithdrawNeighborOffer? It seems to me we don't need the WithdrawNeighborOffer event.

This implementation only implements the NeighborOffer event. The actions for this event also handle the case that the offer is absent (i.e. the offer is withdrawn)

This is not expected to cause any interoperability issues with other implementations. Just is just a simplification of the internal state machine which does not change the external behavior in any observable way.

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

## Do not actually remove offers but mark them as removed

There are various scenarios where a received LIE message contains the optional level field, but offer is removed anyway, such as:

* The flag not_a_ztp_offer is true

* The received level <= leaf_level

* The hold timer expires

Instead of actually removing the offer, we keep the offer, but mark it with a removed flag and a removed-reason string. This makes debugging and trouble-shooting easier.

## Rules for accepting a received LIE message

Section 4.2.2 contains 8 bullet points that specify the conditions for accepting a received LIE message and estabilishing a three-way adjacency.

Section B.1.4 also contains rules for accepting a received LIE message and establishing a three-way adjacency.

The rules in section 4.2.2 are *not* consistent with the rules in section B.1.4, specifically:

* Rules 4.2.2.1 and 4.2.2.3 about PoD membership are missing from section B.1.4

* Rule 4.2.2.5 about the different system IDs is missing from section B.1.4

* Rule 4.2.2.6 about the same MTU is missing from section B.1.4

* The rules in section 4.2.2.8 are different from the corresponding rules in section B.1.4.2.

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

## Use real ZTP hold timer

The ZTP FSM uses a hold timer to manage the time spent in state HoldingDown. There is a ShortTic event that is generated at fixed intervals. The timer is implemented "manually" by counting the number of ShortTic events, and when a threshold is reached, a HoldDownExpired event is generated. I call this a "manual" implementation of a timer.

The Timer class in Python RIFT supports "real" timers. You can start a timer with an arbitrary expiry time, and an event can be generated when the timer expires, without the need for counting ticks.

We use a "real" timer to implement the ZTP holddown timer, and hence we don't need any ShortTic events.

