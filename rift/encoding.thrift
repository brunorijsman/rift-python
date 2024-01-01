/**
    Thrift file for packet encodings for RIFT

*/

include "common.thrift"

namespace py encoding

/** Represents protocol encoding schema major version */
const common.VersionType protocol_major_version = 8
/** Represents protocol encoding schema minor version */
const common.MinorVersionType protocol_minor_version =  0

/** Common RIFT packet header. */
struct PacketHeader {
    /** Major version of protocol. */
    1: required common.VersionType      major_version =
            protocol_major_version;
    /** Minor version of protocol. */
    2: required common.MinorVersionType minor_version =
            protocol_minor_version;
    /** Node sending the packet, in case of LIE/TIRE/TIDE
        also the originator of it. */
    3: required common.SystemIDType  sender;
    /** Level of the node sending the packet, required on everything
        except LIEs. Lack of presence on LIEs indicates UNDEFINED_LEVEL
        and is used in ZTP procedures.
     */
    4: optional common.LevelType            level;
}

/** Prefix community. */
struct Community {
    /** Higher order bits */
    1: required i32          top;
    /** Lower order bits */
    2: required i32          bottom;
} 

/** Neighbor structure.  */
struct Neighbor {
    /** System ID of the originator. */
    1: required common.SystemIDType        originator;
    /** ID of remote side of the link. */
    2: required common.LinkIDType          remote_id;
} 

/** Capabilities the node supports. */
struct NodeCapabilities {
    /** Must advertise supported minor version dialect that way. */
    1: required common.MinorVersionType        protocol_minor_version =
            protocol_minor_version;
    /** indicates that node supports flood reduction. */
    2: optional bool                           flood_reduction =
            common.flood_reduction_default;
    /** indicates place in hierarchy, i.e. top-of-fabric or
        leaf only (in ZTP) or support for leaf-2-leaf
        procedures. */
    3: optional common.HierarchyIndications    hierarchy_indications;


} 

/** Link capabilities. */
struct LinkCapabilities {
    /** Indicates that the link is supporting BFD. */
    1: optional bool                           bfd =
            common.bfd_default;
    /** Indicates whether the interface will support IPv4 forwarding. */
    2: optional bool                           ipv4_forwarding_capable =
            true;
} 

/** RIFT LIE Packet.

    @note: this node's level is already included on the packet header
*/
struct LIEPacket {
    /** Node or adjacency name. */
    1: optional string                    name;
    /** Local link ID. */
    2: required common.LinkIDType         local_id;
    /** UDP port to which we can receive flooded TIEs. */
    3: required common.UDPPortType        flood_port =
            common.default_tie_udp_flood_port;
    /** Layer 3 MTU, used to discover mismatch. */
    4: optional common.MTUSizeType        link_mtu_size =
            common.default_mtu_size;
    /** Local link bandwidth on the interface. */
    5: optional common.BandwithInMegaBitsType
            link_bandwidth = common.default_bandwidth;
    /** Reflects the neighbor once received to provide
        3-way connectivity. */
    6: optional Neighbor                  neighbor;
    /** Node's PoD. */
    7: optional common.PodType            pod =
            common.default_pod;
    /** Node capabilities supported. */
   10: required NodeCapabilities          node_capabilities;
   /** Capabilities of this link. */
   11: optional LinkCapabilities          link_capabilities;
   /** Required holdtime of the adjacency, i.e. for how
       long a period should adjacency be kept up without valid LIE reception. */
   12: required common.TimeIntervalInSecType
            holdtime = common.default_lie_holdtime;
   /** Optional, unsolicited, downstream assigned locally significant label
       value for the adjacency. */
   13: optional common.LabelType          label;
    /** Indicates that the level on the LIE must not be used
        to derive a ZTP level by the receiving node. */
   21: optional bool                      not_a_ztp_offer =
            common.default_not_a_ztp_offer;
   /** Indicates to northbound neighbor that it should
       be reflooding TIEs received from this node to achieve flood
       reduction and balancing for northbound flooding. */
   22: optional bool                      you_are_flood_repeater =
             common.default_you_are_flood_repeater;
   /** Indicates to neighbor to flood node TIEs only and slow down
       all other TIEs. Ignored when received from southbound neighbor. */
   23: optional bool                      you_are_sending_too_quickly =
             false;
   /** Instance name in case multiple RIFT instances running on same
       interface. */
   24: optional string                    instance_name;
   /** It provides the optional ID of the Fabric configured. This MUST match the information advertised
       on the node element. */
   35: optional common.FabricIDType       fabric_id = common.default_fabric_id;

}

/** LinkID pair describes one of parallel links between two nodes. */
struct LinkIDPair {
    /** Node-wide unique value for the local link. */
    1: required common.LinkIDType      local_id;
    /** Received remote link ID for this link. */
    2: required common.LinkIDType      remote_id;

    /** Describes the local interface index of the link. */
   10: optional common.PlatformInterfaceIndex platform_interface_index;
   /** Describes the local interface name. */
   11: optional string                        platform_interface_name;
   /** Indicates whether the link is secured, i.e. protected by
       outer key, absence of this element means no indication,
       undefined outer key means not secured. */
   12: optional common.OuterSecurityKeyID
                trusted_outer_security_key;
   /** Indicates whether the link is protected by established
       BFD session. */
   13: optional bool                          bfd_up;
   /** Optional indication which address families are up on the
       interface */
   14: optional set<common.AddressFamilyType> 
                       address_families;
}  

/** Unique ID of a TIE. */
struct TIEID {
    /** direction of TIE */
    1: required common.TieDirectionType    direction;
    /** indicates originator of the TIE */
    2: required common.SystemIDType        originator;
    /** type of the tie */
    3: required common.TIETypeType         tietype;
    /** number of the tie */
    4: required common.TIENrType           tie_nr;
} 

/** Header of a TIE. */
struct TIEHeader {
    /** ID of the tie. */
    2: required TIEID                             tieid;
    /** Sequence number of the tie. */
    3: required common.SeqNrType                  seq_nr;

    /** Absolute timestamp when the TIE was generated. */
   10: optional common.IEEE802_1ASTimeStampType   origination_time;
   /** Original lifetime when the TIE was generated.  */
   12: optional common.LifeTimeInSecType          origination_lifetime;
} 

/** Header of a TIE as described in TIRE/TIDE.
*/
struct TIEHeaderWithLifeTime {
    1: required     TIEHeader                       header;
    /** Remaining lifetime. */
    2: required     common.LifeTimeInSecType        remaining_lifetime;
} 

/** TIDE with *sorted* TIE headers. */
struct TIDEPacket {
    /** First TIE header in the tide packet. */
    1: required TIEID                       start_range;
    /** Last TIE header in the tide packet. */
    2: required TIEID                       end_range;
    /** _Sorted_ list of headers. */
    3: required list<TIEHeaderWithLifeTime> 
                     headers;
}

/** TIRE packet */
struct TIREPacket {
    1: required set<TIEHeaderWithLifeTime>  
                     headers;
}

/** neighbor of a node */
struct NodeNeighborsTIEElement {
    /** level of neighbor */
    1: required common.LevelType                level;
    /**  Cost to neighbor. Ignore anything larger than `infinite_distance` and `invalid_distance` */
    3: optional common.MetricType               cost
                = common.default_distance;
    /** can carry description of multiple parallel links in a TIE */
    4: optional set<LinkIDPair>                 
                         link_ids;
    /** total bandwith to neighbor as sum of all parallel links */
    5: optional common.BandwithInMegaBitsType
                bandwidth = common.default_bandwidth;
} 

/** Indication flags of the node. */
struct NodeFlags {
    /** Indicates that node is in overload, do not transit traffic
        through it. */
     1: optional bool         overload = common.overload_default;
} 

/** Description of a node. */
struct NodeTIEElement {
    /** Level of the node. */
    1: required common.LevelType            level;
    /** Node's neighbors. Multiple node TIEs can carry disjoint sets of neighbors. */
    2: required map<common.SystemIDType,
                NodeNeighborsTIEElement>    neighbors;
    /** Capabilities of the node. */
    3: required NodeCapabilities            capabilities;
    /** Flags of the node. */
    4: optional NodeFlags                   flags;
    /** Optional node name for easier operations. */
    5: optional string                      name;
    /** PoD to which the node belongs. */
    6: optional common.PodType              pod;
    /** optional startup time of the node */
    7: optional common.TimestampInSecsType  startup_time;

    /** If any local links are miscabled, this indication is flooded. */
   10: optional set<common.LinkIDType>      
                     miscabled_links;

   /** ToFs in the same plane. Only carried by ToF. Multiple Node TIEs can carry disjoint sets of ToFs
       which MUST be joined to form a single set. */
   12: optional set<common.SystemIDType>
                     same_plane_tofs;

   /** It provides the optional ID of the Fabric configured */
   20: optional common.FabricIDType             fabric_id = common.default_fabric_id;


} 

/** Attributes of a prefix. */
struct PrefixAttributes {
    /** Distance of the prefix. */
    2: required common.MetricType            metric
            = common.default_distance;
    /** Generic unordered set of route tags, can be redistributed
        to other protocols or use within the context of real time
        analytics. */
    3: optional set<common.RouteTagType>     
                      tags;
    /** Monotonic clock for mobile addresses.  */
    4: optional common.PrefixSequenceType    monotonic_clock;
    /** Indicates if the prefix is a node loopback. */
    6: optional bool                         loopback = false;
    /** Indicates that the prefix is directly attached. */
    7: optional bool                         directly_attached = true;
    /** link to which the address belongs to.  */
   10: optional common.LinkIDType            from_link;
    /** Optional, per prefix significant label. */
   12: optional common.LabelType             label;
} 

/** TIE carrying prefixes */
struct PrefixTIEElement {
    /** Prefixes with the associated attributes. */
    1: required map<common.IPPrefixType, PrefixAttributes> prefixes;
} 

/** Defines the targeted nodes and the value carried. */
struct KeyValueTIEElementContent {
    1: optional common.KeyValueTargetType        targets = common.keyvaluetarget_default;
    2: optional binary                           value;
}

/** Generic key value pairs. */
struct KeyValueTIEElement {
    1: required map<common.KeyIDType, KeyValueTIEElementContent>    keyvalues;
} 

/** Single element in a TIE. */
union TIEElement {
    /** Used in case of enum common.TIETypeType.NodeTIEType. */
    1: optional NodeTIEElement     node;
    /** Used in case of enum common.TIETypeType.PrefixTIEType. */
    2: optional PrefixTIEElement          prefixes;
    /** Positive prefixes (always southbound). */
    3: optional PrefixTIEElement   positive_disaggregation_prefixes;
    /** Transitive, negative prefixes (always southbound) */
    5: optional PrefixTIEElement   negative_disaggregation_prefixes;
    /** Externally reimported prefixes. */
    6: optional PrefixTIEElement          external_prefixes;
    /** Positive external disaggregated prefixes (always southbound). */
    7: optional PrefixTIEElement
            positive_external_disaggregation_prefixes;
    /** Key-Value store elements. */
    9: optional KeyValueTIEElement keyvalues;
} 

/** TIE packet */
struct TIEPacket {
    1: required TIEHeader  header;
    2: required TIEElement element;
}

/** Content of a RIFT packet. */
union PacketContent {
    1: optional LIEPacket     lie;
    2: optional TIDEPacket    tide;
    3: optional TIREPacket    tire;
    4: optional TIEPacket     tie;
}

/** RIFT packet structure. */
struct ProtocolPacket {
    1: required PacketHeader  header;
    2: required PacketContent content;
}
