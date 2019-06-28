This directory contains multiple YAML topology description files to run `RIFT` binaries. 
**The schema is bound to change anytime** but this file keep documentation of the allowed 
format below. We use an intuitive, loose format. The multiplicity is presented as follow: 

    {1}  - exactly one
    {+}  - one or more
    {?}  - at most one
    {*}  - zero or more
    X    - may not be supported in all released versions

    # comments
    {1} const:
    {?} keys:                              {8}
        {+} - id: <24-bit key number>
        {1}   algorithm: [hmac-sha-256]
        {1}   secret: <string>   
        {?}   private-secret: <string>     {7}
    {1} shards: 
        {+} - id: <64-bit integer shard identifier> 
            {1}   nodes: 
                {*}   - name: <node name string>
                {?}      passive (1)
                {1}      level: [<numerical level> | undefined | leaf | leaf-2-leaf | top-of-fabric ] (2) 
                {1}      systemid: <64-bit integer>
                {?}      rx_lie_mcast_address: <unique V4 multicast address used to receive LIEs 
                                                in dotted notation, e.g. 224.0.0.2>  (5)
                {?}      rx_lie_v6_mcast_address: <unique v6 multicast address, e.g. FF02::0:2> (5)
                {1}      rx_lie_port: <node-wide UDP Port used to receive LIEs> (4)
                {?}X     state_thrift_services_port: <TCP port to run state services>
                {?}X     config_thrift_services_port: <TCP port to run config services>
                {?}      generate_defaults: <boolean indicating whether southbound defaults are 
                                             generated, default is true>
                {?}      active_key: <24-bit key number>
                {?}      tie_validation: [none|permissive|loose|strict]  (6)
                {1}      interfaces:
                {*}         - name: <interface name string>
                {?}           bandwidth: <in megabit units, if not given, schema default is used>
                {?}           metric: <positive numerical metric > 0, if not given, schema default>
                {?}           tx_lie_port: <UDP Port used to send LIEs, 
                                            must match remote node's rx_lie_port and be 
                                            unique within the configuration> (3)
                {?}           rx_lie_port: <UDP Port used to receive LIEs, 
                                            must match remote node's tx_lie_port and be 
                                            unique within the configuration> (3)
                {?}           rx_tie_port: <UDP Port used to receive TIEs, 
                                            automatically carried on LIEs, must be unique 
                                            within the configuration> (3)
                {?}           advertise_subnet: <boolean indicating whether the interface subnet
                                                 is advertised in RIFT northbound, default is false>
                {?}           active_key: <8-bit key number> 
                {?}           accept_keys: <set of 8-bit key number>
                {?}           link_validation: [none|permissive|loose|strict]  (6)       
                {?}      v4prefixes:
                {*}         - address: <IPv4 address in dotted notation, e.g. 1.1.1.0>
                {1}           mask: <numeric mask length>
                {1}           metric: <positive numerical metric > 0>
                {?}      v6prefixes:
                {*}         - address: <IPv6 address in dotted notation, e.g. fe80::1.1.1.1>
                {1}           mask: <numeric mask length>
                {1}           metric: <positive numerical metric > 0>
    
(1) Passive nodes are not started but just used to match up correct ports and addresses. This 
    is very useful in e.g. interoperability testing where such a node can be started as 
    a different application and send/receive on the configured ports.      

(2) ZTP is possible via the level clause.

(3) When running sharding observe that you still have to keep UDP ports unique given 
    multicast scope. Machines must be one within TTL scope of one from each other.
    YAML topology or sharding does NOT support binding to specific physical 
    interfaces on reception and hence separates "interfaces" by matching the multicast 
    addresses and UDP port pairs. It matches the source and destination node by the same 
    LIE receive and transmit port. 
    
(4) overrides per interface `rx_lie_port`, for testing purposes on platforms that 
    support per node lie rx socket only.

(5) either of the multicast addresses (or both) may be specified. 

(6) if not specified default is none, i.e. received fingerprints are ignored, modes signify
        
        - strict: always check, do not accept without key ID and fingerprint
        - permissive: accept if key id unknown
        - loose: check if authentication present, otherwise accept 
        
{7} only necessary if it's a private/public key pair

{8} 