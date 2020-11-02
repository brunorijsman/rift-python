# Feature List

## Supported version

RIFT draft version: [draft-ietf-rift-rift-12](https://tools.ietf.org/pdf/draft-ietf-rift-rift-12.pdf)

Thrift data model version: 4.1

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

| Feature | Supported | GitHub Issue |
| --- | --- | --- |
| Receive all types of TIE packets | Yes | |
| Store received TIE packets in TIE-DB | Yes | |
| Age TIE packets in TIE-DB and remove when they expire | Yes | |
| Add neighbor's newer TIEs to request queue | Yes | |
| Add neighbor's older TIEs to send queue | Yes | |
| Add neighbor's same TIEs to acknowledge queue | Yes | |
| Re-transmit TIEs if they are not acknowledged | Yes | |
| Periodically serve all queues (TX, RTX, REQ, ACK) | Yes | |
| Propagate TIE packets without decoding and re-encoding | Yes | |
| Send / Process Node TIE packets | Yes | |
| Send / Process North Prefix TIE packets (configured prefixes)  | Yes | |
| Send / Process South Prefix TIE packets (default prefixes)  | Yes | |
| Send / Process Positive Disaggregation TIE packets | Yes | |
| Send / Process Negative Disaggregation TIE packets | Yes | |
| Send / Process Policy Guided Prefix TIE packets | No | [32](https://github.com/brunorijsman/rift-python/issues/32) |
| Send / Process Key Value TIE packets | No | [33](https://github.com/brunorijsman/rift-python/issues/33) |
| Process received TIDE packets | Yes | |
| Request missing TIEs based on received TIDE packets | Yes | |
| Send newer TIEs based on received TIDE packets | Yes | |
| Detect extra TIEs based on gaps inside received TIDE packets | Yes | |
| Detect extra TIEs based on gaps between received TIDE packets | Yes | |
| Acknowledge same TIEs based on received TIDE packets | Yes | |
| Periodically originate TIDE packets | Yes | |
| Process received TIRE packets | Yes | |
| Start sending TIES requested in received TIRE packet | Yes | |
| Stop sending TIES acknowledged in received TIRE packet | Yes | |
| Apply flooding scope rules when sending TIE packets | Yes | |
| Apply flooding scope rules when sending TIDE packets | Yes | |
| Apply flooding scope rules when sending TIRE packets | Yes | |
| Southbound Default Route Origination  | Yes | |
| Northbound TIE Flooding Reduction  | Yes | |
| Applying Policy  | No | [32](https://github.com/brunorijsman/rift-python/issues/32) |
| Store Policy-Guided Prefix for Route Computation and Regeneration  | No | [32](https://github.com/brunorijsman/rift-python/issues/32) |
| Re-origination | Yes | |
| Flood IPv4 Prefixes | Yes | |
| Flood IPv6 Prefixes | Yes | |

## Route Calculation

| Feature | Supported | GitHub Issue |
| --- | --- | --- |
| Reachability Computation  | Yes | |
| Northbound SPF  | Yes | |
| Southbound SPF  | Yes | |
| Leaf-to-leaf shortcuts  | No | [40](https://github.com/brunorijsman/rift-python/issues/40) |
| Equal-Cost Multi-Path (ECMP) | Yes | |
| Fabric bandwidth balancing / Non-Equal-Cost Multi-Path (NECMP) | Yes | |
| Use non-best paths (Eppstein k-shortest) | No | [41](https://github.com/brunorijsman/rift-python/issues/41) |
| Route Calculation for Positive Disaggregation | Yes | |
| Route Calculation for Negative Disaggregation | Yes | |
| Routing Information Base (RIB) | Yes | |
| Forwarding Information Base (FIB) abstraction | Yes | |
| Store FIB routes into kernel route table (on Linux only) | Yes | |

## Additional Features

| Feature | Supported | GitHub Issue |
| --- | --- | --- |
| Attaching Prefixes  | Yes | |
| Attaching Policy-Guided Prefixes  | No | [32](https://github.com/brunorijsman/rift-python/issues/32) |
| Positive Disaggregation on Link & Node Failures  | Yes | |
| Negative Disaggregation on Link & Node Failures  | Yes | |
| Overload Bit  | No | [42](https://github.com/brunorijsman/rift-python/issues/42) |
| Optimized Route Computation on Leafs  | No | [43](https://github.com/brunorijsman/rift-python/issues/43) |
| Mobility  | No | [44](https://github.com/brunorijsman/rift-python/issues/44) |
| Anycast  | No | [45](https://github.com/brunorijsman/rift-python/issues/45) |
| Overlays and Signaling  | Yes | |
| Key/Value Store  | No | [33](https://github.com/brunorijsman/rift-python/issues/33) |
| Interactions with BFD  | No | [46](https://github.com/brunorijsman/rift-python/issues/46) |
| Fabric Bandwidth Balancing  | No | [38](https://github.com/brunorijsman/rift-python/issues/38) |
| Label Binding  | No | [47](https://github.com/brunorijsman/rift-python/issues/47) |
| Segment Routing Support with RIFT  | No | [48](https://github.com/brunorijsman/rift-python/issues/48) |
| Leaf to Leaf Procedures  | No | [40](https://github.com/brunorijsman/rift-python/issues/40) |
| Address Family and Multi Topology Considerations  | Yes | |
| Reachability of Internal Nodes in the Fabric  | Yes | |
| One-Hop Healing of Levels with East-West Links  | No | [40](https://github.com/brunorijsman/rift-python/issues/40) |
| Considerations for Leaf-Only Implementation  | Yes | |
| Adaptations to Other Proposed Data Center Topologies  | Yes | |
| Originating Non-Default Route Southbound  | No | [49](https://github.com/brunorijsman/rift-python/issues/49) |
| Multicast Routing  | No | [39](https://github.com/brunorijsman/rift-python/issues/39) |

## Management

| Feature | Supported | GitHub Issue |
| --- | --- | --- |
| Telnet client | Yes | |
| SSH client | No | [31](https://github.com/brunorijsman/rift-python/issues/31) |
| Command Line Interface (CLI) | Yes | |
| CLI Command History | Yes | |
| CLI Tab Completion | No | [50](https://github.com/brunorijsman/rift-python/issues/50) |
| CLI Context-Sensitive Help | Partial | [51](https://github.com/brunorijsman/rift-python/issues/51) |
| Logging | Yes | |
| YANG support | No | [52](https://github.com/brunorijsman/rift-python/issues/52) |
| Startup Configuration File | Yes | |
| Run-time Configuration Changes | Partial | [53](https://github.com/brunorijsman/rift-python/issues/53) |
| Multi-Node Topologies | Yes | |

## Infrastructure

### Finite State Machine

| Feature | Supported |
| --- | --- |
| Formal Finite State Machine (FSM) framework | Yes |
| Generate FSM documentation from code | Yes |
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
