/**
    Thrift file for packet encodings for RIFT

*/

include "common.thrift"

namespace rs models
namespace py encoding

/** Represents protocol encoding schema major version */
const common.VersionType protocol_major_version = 2
/** Represents protocol encoding schema minor version */
const common.MinorVersionType protocol_minor_version =  0

/** common RIFT packet header */
struct PacketHeader {
    /** major version type of protocol */
    1: required common.VersionType major_version = protocol_major_version;
    /** minor version type of protocol */
    2: required common.VersionType minor_version = protocol_minor_version;
    /** node sending the packet, in case of LIE/TIRE/TIDE
      * also the originator of it */
    3: required common.SystemIDType  sender;
    /** level of the node sending the packet, required on everything except
      * LIEs. Lack of presence on LIEs indicates UNDEFINED_LEVEL and is used
      * in ZTP procedures.
     */
    4: optional common.LevelType            level;
}

/** community */
struct Community {
    1: required i32          top;
    2: required i32          bottom;
}

/** neighbor structure  */
struct Neighbor {
    /** system ID of the originator */
    1: required common.SystemIDType        originator;
    /** ID of remote side of the link */
    2: required common.LinkIDType          remote_id;
}

/** capabilities the node supports. The schema may add to this
    field future capabilities to indicate whether it will support
    interpretation of future schema extensions on the same major
    revision. Such fields MUST be optional and have an implicit or
    explicit false default value. If a future capability changes route
    selection or generates blackholes if some nodes are not supporting
    it then a major version increment is unavoidable.
*/
struct NodeCapabilities {
    /** must advertise supported minor version dialect that way */
    1: required common.MinorVersionType        protocol_minor_version =
            protocol_minor_version;
    /** can this node participate in flood reduction */
    2: optional bool                           flood_reduction =
            common.flood_reduction_default;
    /** does this node restrict itself to be top-of-fabric or
        leaf only (in ZTP) and does it support leaf-2-leaf procedures */
    3: optional common.HierarchyIndications    hierarchy_indications;
}

/** link capabilities */
struct LinkCapabilities {
    /** indicates that the link is supporting BFD */
    1: optional bool                           bfd =
            common.bfd_default;
    /** indicates whether the interface will support v4 forwarding. This MUST
      * be set to true when LIEs from a v4 address are sent and MAY be set
      * to true in LIEs on v6 address. If v4 and v6 LIEs indicate contradicting
      * information the behavior is unspecified. */
    2: optional bool                           v4_forwarding_capable =
            true;
}

/** RIFT LIE packet

    @note this node's level is already included on the packet header */
struct LIEPacket {
    /** node or adjacency name */
    1: optional string                        name;
    /** local link ID */
    2: required common.LinkIDType             local_id;
    /** UDP port to which we can receive flooded TIEs */
    3: required common.UDPPortType            flood_port =
            common.default_tie_udp_flood_port;
    /** layer 3 MTU, used to discover to mismatch. */
    4: optional common.MTUSizeType            link_mtu_size =
            common.default_mtu_size;
    /** local link bandwidth on the interface */
    5: optional common.BandwithInMegaBitsType link_bandwidth =
            common.default_bandwidth;
    /** reflects the neighbor once received to provide
        3-way connectivity */
    6: optional Neighbor                      neighbor;
    /** node's PoD */
    7: optional common.PodType                pod =
            common.default_pod;
    /** node capabilities shown in the LIE. The capabilies
        MUST match the capabilities shown in the Node TIEs, otherwise
        the behavior is unspecified. A node detecting the mismatch
        SHOULD generate according error */
   10: required NodeCapabilities              node_capabilities;
   /** capabilities of this link */
   11: optional LinkCapabilities              link_capabilities;
   /** required holdtime of the adjacency, i.e. how much time
       MUST expire without LIE for the adjacency to drop */
   12: required common.TimeIntervalInSecType  holdtime =
            common.default_lie_holdtime;
   /** unsolicited, downstream assigned locally significant label
       value for the adjacency */
   13: optional common.LabelType              label;
    /** indicates that the level on the LIE MUST NOT be used
        to derive a ZTP level by the receiving node */
   21: optional bool                          not_a_ztp_offer =
            common.default_not_a_ztp_offer;
   /** indicates to northbound neighbor that it should
       be reflooding this node's N-TIEs to achieve flood reduction and
       balancing for northbound flooding. To be ignored if received from a
       northbound adjacency */
   22: optional bool                          you_are_flood_repeater =
             common.default_you_are_flood_repeater;
   /** can be optionally set to indicate to neighbor that packet losses are seen on
       reception based on packet numbers or the rate is too high. The receiver SHOULD
       temporarily slow down flooding rates
    */
   23: optional bool                          you_are_sending_too_quickly =
             false;
   /** instance name in case multiple RIFT instances running on same interface */
   24: optional string                        instance_name;
}

/** LinkID pair describes one of parallel links between two nodes */
struct LinkIDPair {
    /** node-wide unique value for the local link */
    1: required common.LinkIDType      local_id;
    /** received remote link ID for this link */
    2: required common.LinkIDType      remote_id;

    /** describes the local interface index of the link */
   10: optional common.PlatformInterfaceIndex       platform_interface_index;
   /** describes the local interface name */
   11: optional string                              platform_interface_name;
   /** indication whether the link is secured, i.e. protected by outer key, absence
       of this element means no indication, undefined outer key means not secured */
   12: optional common.OuterSecurityKeyID           trusted_outer_security_key;
   /** indication whether the link is protected by established BFD session */
   13: optional bool                                bfd_up;
}

/** ID of a TIE

    @note: TIEID space is a total order achieved by comparing the elements
           in sequence defined and comparing each value as an
           unsigned integer of according length.
*/
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

/** Header of a TIE.

   @note: TIEID space is a total order achieved by comparing the elements
              in sequence defined and comparing each value as an
              unsigned integer of according length.

   @note: After sequence number the lifetime received on the envelope
              must be used for comparison before further fields.

   @note: `origination_time` and `origination_lifetime` are disregarded
              for comparison purposes and carried purely for debugging/security
              purposes if present.
*/
struct TIEHeader {
    /** ID of the tie */
    2: required TIEID                             tieid;
    /** sequence number of the tie */
    3: required common.SeqNrType                  seq_nr;

    /** absolute timestamp when the TIE
        was generated. This can be used on fabrics with
        synchronized clock to prevent lifetime modification attacks. */
   10: optional common.IEEE802_1ASTimeStampType   origination_time;
   /** original lifetime when the TIE
       was generated. This can be used on fabrics with
       synchronized clock to prevent lifetime modification attacks. */
   12: optional common.LifeTimeInSecType          origination_lifetime;
}

/** Header of a TIE as described in TIRE/TIDE.
*/
struct TIEHeaderWithLifeTime {
    1: required     TIEHeader                         header;
    /** remaining lifetime that expires down to 0 just like in ISIS.
        TIEs with lifetimes differing by less than `lifetime_diff2ignore` MUST
        be considered EQUAL. */
    2: required     common.LifeTimeInSecType          remaining_lifetime;
}

/** TIDE with sorted TIE headers, if headers are unsorted, behavior is undefined */
struct TIDEPacket {
    /** first TIE header in the tide packet */
    1: required TIEID                       start_range;
    /** last TIE header in the tide packet */
    2: required TIEID                       end_range;
    /** _sorted_ list of headers */
    3: required list<TIEHeaderWithLifeTime> headers;
}

/** TIRE packet */
struct TIREPacket {
    1: required set<TIEHeaderWithLifeTime>  headers;
}

/** neighbor of a node */
struct NodeNeighborsTIEElement {
    /** level of neighbor */
    1: required common.LevelType                level;
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
    /** indicates that node is in overload, do not transit traffic through it */
    1: optional bool         overload = common.overload_default;
}

/** Description of a node.

    It may occur multiple times in different TIEs but if either
        * capabilities values do not match or
        * flags values do not match or
        * neighbors repeat with different values

    the behavior is undefined and a warning SHOULD be generated.
    Neighbors can be distributed across multiple TIEs however if
    the sets are disjoint. Miscablings SHOULD be repeated in every
    node TIE, otherwise the behavior is undefined.

    @note: observe that absence of fields implies defined defaults
*/
struct NodeTIEElement {
    /** level of the node */
    1: required common.LevelType            level;
    /** node's neighbors. If neighbor systemID repeats in other node TIEs of
        same node the behavior is undefined */
    2: required map<common.SystemIDType,
                NodeNeighborsTIEElement>    neighbors;
    /** capabilities of the node */
    3: required NodeCapabilities            capabilities;
    /** flags of the node */
    4: optional NodeFlags                   flags;
    /** optional node name for easier operations */
    5: optional string                      name;
    /** PoD to which the node belongs */
    6: optional common.PodType              pod;

    /** if any local links are miscabled, the indication is flooded */
   10: optional set<common.LinkIDType>      miscabled_links;

}

struct PrefixAttributes {
    /** distance of the prefix */
    2: required common.MetricType            metric = common.default_distance;
    /** generic unordered set of route tags, can be redistributed to other protocols or use
        within the context of real time analytics */
    3: optional set<common.RouteTagType>     tags;
    /** monotonic clock for mobile addresses */
    4: optional common.PrefixSequenceType    monotonic_clock;
    /** indicates if the interface is a node loopback */
    6: optional bool                         loopback = false;
    /** indicates that the prefix is directly attached, i.e. should be routed to even if
        the node is in overload. **/
    7: optional bool                         directly_attached = true;

    /** in case of locally originated prefixes, i.e. interface addresses this can
        describe which link the address belongs to. */
   10: optional common.LinkIDType            from_link;
}

/** TIE carrying prefixes */
struct PrefixTIEElement {
    /** prefixes with the associated attributes.
        if the same prefix repeats in multiple TIEs of same node
        behavior is unspecified */
    1: required map<common.IPPrefixType, PrefixAttributes> prefixes;
}

/** Generic key value pairs */
struct KeyValueTIEElement {
    /** if the same key repeats in multiple TIEs of same node
        or with different values, behavior is unspecified */
    1: required map<common.KeyIDType,string>    keyvalues;
}

/** single element in a TIE. enum `common.TIETypeType`
    in TIEID indicates which elements MUST be present
    in the TIEElement. In case of mismatch the unexpected
    elements MUST be ignored. In case of lack of expected
    element the TIE an error MUST be reported and the TIE
    MUST be ignored.

    This type can be extended with new optional elements
    for new `common.TIETypeType` values without breaking
    the major but if it is necessary to understand whether
    all nodes support the new type a node capability must
    be added as well.
 */
union TIEElement {
    /** used in case of enum common.TIETypeType.NodeTIEType */
    1: optional NodeTIEElement            node;
    /** used in case of enum common.TIETypeType.PrefixTIEType */
    2: optional PrefixTIEElement          prefixes;
    /** positive prefixes (always southbound)
        It MUST NOT be advertised within a North TIE and ignored otherwise
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
    5: optional PrefixTIEElement          negative_disaggregation_prefixes;
    /** externally reimported prefixes */
    6: optional PrefixTIEElement          external_prefixes;
    /** positive external disaggregated prefixes (always southbound).
        It MUST NOT be advertised within a North TIE and ignored otherwise
    */
    7: optional PrefixTIEElement          positive_external_disaggregation_prefixes;
    /** Key-Value store elements */
    9: optional KeyValueTIEElement        keyvalues;
}

/** TIE packet */
struct TIEPacket {
    1: required TIEHeader  header;
    2: required TIEElement element;
}

/** content of a RIFT packet */
union PacketContent {
    1: optional LIEPacket     lie;
    2: optional TIDEPacket    tide;
    3: optional TIREPacket    tire;
    4: optional TIEPacket     tie;
}

/** RIFT packet structure */
struct ProtocolPacket {
    1: required PacketHeader  header;
    2: required PacketContent content;
}