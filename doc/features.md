# Feature List

## Adjacencies

| Feature | Supported |
| --- | --- |
| Link Information Element (LIE) Packet | Yes |
| Link Information Element (LIE) Finite State Machine (FSM) | Yes |
| Adjacencies using IPv4 Link and Multicast Addresses | Yes |
| Adjacencies using IPv6 Link and Multicast Addresses | Yes |

## Zero Touch Provisioning (ZTP)

| Feature | Supported |
| --- | --- |
| Automatic SystemID Selection  | Yes |
| Zero Touch Provisioning (ZTP) Finite State Machine (FSM) | Yes |
| Automatic Level Determination Procedure  | Yes |

## Flooding

| Feature | Supported |
| --- | --- |
| Receive all types of TIE packets | Yes |
| Store received TIE packets in TIE-DB | Yes |
| Age TIE packets in TIE-DB and remove when they expire | Yes |
| Add neighbor's newer TIEs to request queue | Yes |
| Add neighbor's older TIEs to send queue | Yes |
| Add neighbor's same TIEs to acknowledge queue | Yes |
| Re-transmit TIEs if they are not acknowledged | Yes |
| Periodically serve all queues (TX, RTX, REQ, ACK) | Yes |
| Propagate TIE packets without decoding and re-encoding | Yes |
| Send / Process Node TIE packets | Yes |
| Send / Process North Prefix TIE packets (configured prefixes)  | Yes |
| Send / Process South Prefix TIE packets (default prefixes)  | Yes |
| Send / Process Positive Disaggregation TIE packets | Yes |
| Send / Process Negative Disaggregation TIE packets | Yes |
| Send / Process Policy Guided Prefix TIE packets | No |
| Send / Process Key Value TIE packets | No |
| Process received TIDE packets | Yes |
| Request missing TIEs based on received TIDE packets | Yes |
| Send newer TIEs based on received TIDE packets | Yes |
| Detect extra TIEs based on gaps inside received TIDE packets | Yes |
| Detect extra TIEs based on gaps between received TIDE packets | Yes |
| Acknowledge same TIEs based on received TIDE packets | Yes |
| Periodically originate TIDE packets | Yes |
| Process received TIRE packets | Yes |
| Start sending TIES requested in received TIRE packet | Yes |
| Stop sending TIES acknowledged in received TIRE packet | Yes |
| Apply flooding scope rules when sending TIE packets | Yes |
| Apply flooding scope rules when sending TIDE packets | Yes |
| Apply flooding scope rules when sending TIRE packets | Yes |
| Southbound Default Route Origination  | Yes |
| Northbound TIE Flooding Reduction  | Yes |
| Ingress Filtering  | No |
| Applying Policy  | No |
| Store Policy-Guided Prefix for Route Computation and Regeneration  | No |
| Re-origination | Yes |
| Overlap with Disaggregated Prefixes  | No |
| Multicast Routing  | No |

## Route Calculation

| Feature | Supported |
| --- | --- |
| Reachability Computation  | Yes |
| Northbound SPF  | Yes |
| Southbound SPF  | Yes |
| East-West Forwarding Within a Level  | No |
| Equal-Cost Multi-Path (ECMP) | Yes |
| Non-Equal-Cost Multi-Path (NECMP) | No |
| Use non-best paths (Eppstein k-shortest) | No |
| Route Calculation for Positive Disaggregation | Yes |
| Route Calculation for Negative Disaggregation | Yes |
| Routing Information Base (RIB) | Yes |
| Forwarding Information Base (FIB) abstraction | Yes |
| Store FIB routes into kernel route table (on Linux only) | Yes |

## Additional Features

| Feature | Supported |
| --- | --- |
| Attaching Prefixes  | Yes |
| Attaching Policy-Guided Prefixes  | No |
| Positive Disaggregation on Link & Node Failures  | Yes |
| Negative Disaggregation on Link & Node Failures  | Yes |
| Stability Considerations  | No |
| Further Mechanisms  | No |
| Overload Bit  | No |
| Optimized Route Computation on Leafs  | No |
| Mobility  | No |
| Clock Comparison  | No |
| Interaction between Time Stamps and Sequence Counters  | No |
| Anycast vs Unicast  | No |
| Overlays and Signaling  | No |
| Key/Value Store  | No |
| Interactions with BFD  | No |
| Fabric Bandwidth Balancing  | No |
| Northbound Direction  | No |
| Southbound Direction  | No |
| Label Binding  | No |
| Segment Routing Support with RIFT  | No |
| Global Segment Identifiers Assignment  | No |
| Distribution of Topology Information  | No |
| Leaf to Leaf Procedures  | No |
| Other End-to-End Services  | No |
| Address Family and Multi Topology Considerations  | No |
| Reachability of Internal Nodes in the Fabric  | No |
| One-Hop Healing of Levels with East-West Links  | No |
| Considerations for Leaf-Only Implementation  | No |
| Adaptations to Other Proposed Data Center Topologies  | No |
| Originating Non-Default Route Southbound  | No |
| Flood IPv4 Prefixes | Yes |
| Flood IPv6 Prefixes | Yes |

## Management

| Feature | Supported |
| --- | --- |
| Telnet client | Yes |
| SSH client | No |
| Command Line Interface (CLI) | Yes |
| CLI Command History | Yes |
| CLI Tab Completion | No |
| CLI Context-Sensitive Help | Partial |
| Logging | Yes |
| YANG support | No |
| Startup Configuration File | Yes |
| Run-time Configuration Changes | Partial |
| Multi-Node Topologies | Yes |

## Infrastructure

### Finite State Machine

| Feature | Supported |
| --- | --- |
| Formal Finite State Machine (FSM) framework | Yes |
| Generate FSM documentation from code | Yes |
| Check FSM for correctness | No |
| Report history of transitions | Yes |
| Visualize history of FSM transitions | Yes |
| Distinguish boring (verbose) vs interesting (non-verbose) transactions | Yes |

### Continuous Integration (CI)

| Feature | Supported |
| --- | --- |
| Travis Continuous Integration | Yes |
| Codecov code coverage measuring and reporting | Yes |
| Automated Pylint | Yes |
| Automated Pytest Unit Tests | Yes |
| Automated System Tests | Yes |
| Automated Interoperability Tests | Yes, with Juniper RIFT |
| Automated Chaos Tests | Yes |
