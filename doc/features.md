# Feature List

## Adjacenecies

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
| Topology Information Element (TIE) Packet | No |
| Topology Information Description Element (TIDE) Packet | No |
| Topology Information Request Element (TIRE) Packet | No |
| Topology Exchange (TIE Exchange) | No |
| Topology Information Elements | No |
| South- and Northbound Representation | No |
| Flooding  | No |
| TIE Flooding Scopes  | No |
| Initial and Periodic Database Synchronization  | No |
| Purging  | No |
| Southbound Default Route Origination  | No |
| Northbound TIE Flooding Reduction  | No |
| Policy-Guided Prefixes  | No |
| Ingress Filtering  | No |
| Applying Policy  | No |
| Store Policy-Guided Prefix for Route Computation and Regeneration  | No |
| Re-origination  | No |
| Overlap with Disaggregated Prefixes  | No |
| Reachability Computation  | No |
| Northbound SPF  | No |
| Southbound SPF  | No |
| East-West Forwarding Within a Level  | No |
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
| CLI Command History (^P and ^N) | No |
| CLI Tab Completion | No |
| CLI Context-Senstive Help | Partial |
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
| Automated Interoperability Tests | Yes |
