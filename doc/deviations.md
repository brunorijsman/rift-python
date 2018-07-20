# Deviations

This section describes places where this Python RIFT engine implementation consciously an purposly deviates from the draft-ietf-rift-rift-02 specification.

| ID | Short description |
| --- | --- |
| 1 | [Remove event WithdrawNeighborOffer from the ZTP FSM](#remove-event-withdrawneighboroffer-from-the-ztp-fsm) |

## Remove event WithdrawNeighborOffer from the ZTP FSM

The ZTP state machine has an event "NeighborOffer". In the description of this event it is explictly mentioned that the level is optional, i.e. the level could be absent which means UNDEFINED_LEVEL. I interpret the absence of a level field to mean that the offer is withdrawn. This assumption is confirmed by the fact that the action for the event NeighborOffer has an explicit "if no level offered then REMOVE_OFFER else ...". 

If these interpretations are correct, then why is there a separate event WithdrawNeighborOffer which causes an unconditional action "REMOVE_OFFER"? What is the difference between the event NeighborOffer with an absent level, and the event WithdrawNeighborOffer? It seems to me we don't need the WithdrawNeighborOffer event.

This implementation only implements the NeighborOffer event. The actions for this event also handle the case that the offer is absent (i.e. the offer is withdrawn)

This is not expected to cause any interoperability issues with other implementations. Just is just a simplification of the internal state machine which does not change the external behavior in any observable way.
s