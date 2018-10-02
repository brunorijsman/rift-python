# Feature List

## Adjacencies

| Feature | Supported |
| --- | --- |
| Link Information Element (LIE) Packet | Yes |
| Link Information Element (LIE) Finite State Machine (FSM) | Yes |
| Adjacencies using IPv4 Link and Multicast Addresses | Yes |
| Adjacencies using IPv6 Link and Multicast Addresses | No |

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
| Propagate all types of received TIE packets | Yes |
| Propagate TIE packets without decoding and re-encoding | No |
| Originate Node TIE packets | Yes |
| Originate Prefix TIE packets | No |
| Originate Positive Disaggregation TIE packets | No |
| Originate Negative Disaggregation TIE packets | No |
| Originate Policy Guided Prefix TIE packets | No |
| Originate Key Value TIE packets | No |
| Apply flooding scope rules when sending TIE packets | No |
| Process received TIDE packets | Yes |
| Request missing TIEs based on received TIDE packets | Yes |
| Send newer TIEs based on received TIDE packets | Yes |
| Acknowledge same TIEs based on received TIDE packets | Yes |
| Originate TIDE packets | Yes |
| Apply flooding scope rules when sending TIDE packets | No |
| Process received TIRE packets | Yes |
| Start sending TIES requested in received TIRE packet | Yes |
| Stop sending TIES acknowledged in received TIRE packet | Yes |
| Southbound Default Route Origination  | No |
| Northbound TIE Flooding Reduction  | No |
| Ingress Filtering  | No |
| Applying Policy  | No |
| Store Policy-Guided Prefix for Route Computation and Regeneration  | No |
| Re-origination  | No |
| Overlap with Disaggregated Prefixes  | No |

## Route Calculation

| Feature | Supported |
| --- | --- |
| Reachability Computation  | No |
| Northbound SPF  | No |
| Southbound SPF  | No |
| East-West Forwarding Within a Level  | No |

## Additional Features

| Feature | Supported |
| --- | --- |
| Attaching Prefixes  | No |
| Attaching Policy-Guided Prefixes  | No |
| Automatic Disaggregation on Link & Node Failures  | No |
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
| Southbound  | No |
| Northbound  | No |
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
| Flood IPv6 Prefixes | No |

## Management

| Feature | Supported |
| --- | --- |
| Telnet client for operational commands | Partial |
| SSH client for operational commands | No |
| Command Line Interface (CLI) for Operational Commands | Yes |
| CLI Command History (^P and ^N) | Partial |
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
