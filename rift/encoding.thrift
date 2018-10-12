/**
    Thrift file for packet encodings for RIFT
*/

include "common.thrift"

namespace py encoding

/** represents protocol encoding schema major version */
const i32 protocol_major_version = 19
/** represents protocol encoding schema minor version */
const i32 protocol_minor_version = 0

/** common RIFT packet header */
struct PacketHeader {
    1: required common.VersionType major_version = protocol_major_version;
    2: required common.VersionType minor_version = protocol_minor_version;
    /** this is the node sending the packet, in case of LIE/TIRE/TIDE
        also the originator of it */
    3: required common.SystemIDType  sender;
    /** level of the node sending the packet, required on everything except
      * LIEs. Lack of presence on LIEs indicates UNDEFINED_LEVEL and is used
      * in ZTP procedures.
     */
    4: optional common.LevelType     level;
}

/** Community serves as community for PGP purposes */
struct Community {
    1: required i32          top;
    2: required i32          bottom;
}

/** Neighbor structure  */
struct Neighbor {
    1: required common.SystemIDType        originator;
    2: required common.LinkIDType          remote_id;
}

/** Capabilities the node supports */
struct NodeCapabilities {
    /** can this node participate in flood reduction */
    1: optional bool                           flood_reduction =
            common.flood_reduction_default;
    /** does this node restrict itself to be top-of-fabric or
        leaf only (in ZTP) and does it support leaf-2-leaf procedures */
    2: optional common.HierarchyIndications    hierarchy_indications;
}

/** RIFT LIE packet

    @note this node's level is already included on the packet header */
struct LIEPacket {
    /** optional node or adjacency name */
    1: optional string                    name;
    /** local link ID */
    2: required common.LinkIDType         local_id;
    /** UDP port to which we can receive flooded TIEs */
    3: required common.UDPPortType        flood_port =
            common.default_tie_udp_flood_port;
    /** layer 3 MTU, used to discover to mismatch */
    4: optional common.MTUSizeType        link_mtu_size =
            common.default_mtu_size;
    /** local link bandwidth on the interface */
    5: optional common.BandwithInMegaBitsType link_bandwidth =
            common.default_bandwidth;
    /** this will reflect the neighbor once received to provid
        3-way connectivity */
    6: optional Neighbor                  neighbor;
    7: optional common.PodType            pod = common.default_pod;
    /** optional local nonce used for security computations */
    8: optional common.NonceType          nonce;
    /** optional neighbor's reflected nonce for security purposes. Significant delta
        in nonces seen compared to current local nonce can be used to prevent replays */
    9: optional common.NonceType          last_neighbor_nonce;
    /** optional node capabilities shown in the LIE. The capabilies
        MUST match the capabilities shown in the Node TIEs, otherwise
        the behavior is unspecified. A node detecting the mismatch
        SHOULD generate according error.
     */
   10: optional NodeCapabilities          capabilities;
    /** required holdtime of the adjacency, i.e. how much time
        MUST expire without LIE for the adjacency to drop
     */
   11: required common.TimeIntervalInSecType  holdtime =
            common.default_lie_holdtime;
    /** indicates that the level on the LIE MUST NOT be used
        to derive a ZTP level by the receiving node. */
   12: optional bool                      not_a_ztp_offer =
            common.default_not_a_ztp_offer;
   /** indicates to northbound neighbor that it should
       be reflooding this node's N-TIEs to achieve flood reducuction and
       balancing for northbound flooding. To be ignored if received from a
       northbound adjacency. */
   13: optional bool                      you_are_flood_repeater =
             common.default_you_are_flood_repeater;
   /** optional downstream assigned locally significant label
       value for the adjacency. */
   14: optional common.LabelType          label;
}

/** LinkID pair describes one of parallel links between two nodes */
struct LinkIDPair {
    /** node-wide unique value for the local link */
    1: required common.LinkIDType      local_id;
    /** received remote link ID for this link */
    2: required common.LinkIDType      remote_id;
    /** more properties of the link can go in here */
}

/** ID of a TIE

    @note: TIEID space is a total order achieved by comparing the elements
           in sequence defined and comparing each value as an
           unsigned integer of according length.
*/
struct TIEID {
    /** indicates direction of the TIE */
    1: required common.TieDirectionType    direction;
    /** indicates originator of the TIE */
    2: required common.SystemIDType        originator;
    3: required common.TIETypeType         tietype;
    4: required common.TIENrType           tie_nr;
}

/** Header of a TIE.

   @note: TIEID space is a total order achieved by comparing the elements
              in sequence defined and comparing each value as an
              unsigned integer of according length. `origination_time` is
              disregarded for comparison purposes.
*/
struct TIEHeader {
    2: required TIEID                             tieid;
    3: required common.SeqNrType                  seq_nr;
    /** remaining lifetime that expires down to 0 just like in ISIS.
        TIEs with lifetimes differing by less than `lifetime_diff2ignore` MUST
        be considered EQUAL. */
    4: required common.LifeTimeInSecType          remaining_lifetime;
    /** optional absolute timestamp when the TIE
        was generated. This can be used on fabrics with
        synchronized clock to prevent lifetime modification attacks. */
   10: optional common.IEEE802_1ASTimeStampType   origination_time;
   /** optional original lifetime when the TIE
       was generated. This can be used on fabrics with
       synchronized clock to prevent lifetime modification attacks. */
   12: optional common.LifeTimeInSecType          origination_lifetime;
}

/** A TIDE with sorted TIE headers, if headers unsorted, behavior is undefined */
struct TIDEPacket {
    /** all 00s marks starts */
    1: required TIEID           start_range;
    /** all FFs mark end */
    2: required TIEID           end_range;
    /** _sorted_ list of headers */
    3: required list<TIEHeader> headers;
}

/** A TIRE packet */
struct TIREPacket {
    1: required set<TIEHeader> headers;
}

/** Neighbor of a node */
struct NodeNeighborsTIEElement {
    /** Level of neighbor */
    1: required common.LevelType              level;
    /**  Cost to neighbor.

         @note: All parallel links to same node
         incur same cost, in case the neighbor has multiple
         parallel links at different cost, the largest distance
         (highest numerical value) MUST be advertised
         @note: any neighbor with cost <= 0 MUST be ignored in computations */
    3: optional common.MetricType               cost = common.default_distance;
    /** can carry description of multiple parallel links in a TIE */
    4: optional set<LinkIDPair>                 link_ids;

    /** total bandwith to neighbor, this will be normally sum of the
        bandwidths of all the parallel links. */
    5: optional common.BandwithInMegaBitsType   bandwidth =
            common.default_bandwidth;
}

/** Flags the node sets */
struct NodeFlags {
    /** node is in overload, do not transit traffic through it */
    1: optional bool         overload = common.overload_default;
}

/** Description of a node.

    It may occur multiple times in different TIEs but if either
        * capabilities values do not match or
        * flags values do not match or
        * neighbors repeat with different values or
        * visible in same level/having partition upper do not match
    the behavior is undefined and a warning SHOULD be generated.
    Neighbors can be distributed across multiple TIEs however if
    the sets are disjoint.

    @note: observe that absence of fields implies defined defaults
*/
struct NodeTIEElement {
    1: required common.LevelType            level;
    /** if neighbor systemID repeats in other node TIEs of same node
        the behavior is undefined. Equivalent to |A_(n,s)(N) in spec. */
    2: required map<common.SystemIDType,
                NodeNeighborsTIEElement>    neighbors;
    3: optional NodeCapabilities            capabilities;
    4: optional NodeFlags                   flags;
    /** optional node name for easier operations */
    5: optional string                      name;
}

struct PrefixAttributes {
    2: required common.MetricType            metric = common.default_distance;
    /** generic unordered set of route tags, can be redistributed to other protocols or use
        within the context of real time analytics */
    3: optional set<common.RouteTagType>     tags;
    /** optional monotonic clock for mobile addresses */
    4: optional common.PrefixSequenceType    monotonic_clock;
}

/** multiple prefixes */
struct PrefixTIEElement {
    /** prefixes with the associated attributes.
        if the same prefix repeats in multiple TIEs of same node
        behavior is unspecified */
    1: required map<common.IPPrefixType, PrefixAttributes> prefixes;
}

/** keys with their values */
struct KeyValueTIEElement {
    /** if the same key repeats in multiple TIEs of same node
        or with different values, behavior is unspecified */
    1: required map<common.KeyIDType,string>    keyvalues;
}

/** single element in a TIE. enum common.TIETypeType
    in TIEID indicates which elements MUST be present
    in the TIEElement. In case of mismatch the unexpected
    elements MUST be ignored. In case of lack of expected
    element the TIE an error MUST be reported and the TIE
    MUST be ignored.
 */
union TIEElement {
    /** in case of enum common.TIETypeType.NodeTIEType */
    1: optional NodeTIEElement            node;
    /** in case of enum common.TIETypeType.PrefixTIEType */
    2: optional PrefixTIEElement          prefixes;
    /** positive prefixes (always southbound)
        It MUST NOT be advertised within a North TIE.
    */
    3: optional PrefixTIEElement          positive_disaggregation_prefixes;
    /** transitive, negative prefixes (always southbound) which
        MUST be aggregated and propagated
        according to the specification
        southwards towards lower levels to heal
        pathological upper level partitioning, otherwise
        blackholes may occur in multiplane fabrics.
        It MUST NOT be advertised within a North TIE.
    */
    4: optional PrefixTIEElement          negative_disaggregation_prefixes;
    /** externally reimported prefixes */
    5: optional PrefixTIEElement          external_prefixes;
    /** Key-Value store elements */
    6: optional KeyValueTIEElement        keyvalues;
    /** @todo: policy guided prefixes */
}

/** @todo: flood header separately in UDP to allow changing lifetime and SHA without reserialization

 */
struct TIEPacket {
    1: required TIEHeader  header;
    2: required TIEElement element;
}

union PacketContent {
    1: optional LIEPacket     lie;
    2: optional TIDEPacket    tide;
    3: optional TIREPacket    tire;
    4: optional TIEPacket     tie;
}

/** protocol packet structure */
struct ProtocolPacket {
    1: required PacketHeader  header;
    2: required PacketContent content;
}
