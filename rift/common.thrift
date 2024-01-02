/**
    Thrift file with common definitions for RIFT
*/


namespace py common

/** @note MUST be interpreted in implementation as unsigned 64 bits.
 */
typedef i64      SystemIDType
typedef i32      IPv4Address
typedef i32      MTUSizeType
/** @note MUST be interpreted in implementation as unsigned
    rolling over number */
typedef i64      SeqNrType
/** @note MUST be interpreted in implementation as unsigned */
typedef i32      LifeTimeInSecType
/** @note MUST be interpreted in implementation as unsigned */
typedef i8       LevelType
typedef i16      PacketNumberType
/** @note MUST be interpreted in implementation as unsigned */
typedef i32      PodType
/** @note MUST be interpreted in implementation as unsigned.
/** this has to be long enough to accomodate prefix */
typedef binary   IPv6Address
/** @note MUST be interpreted in implementation as unsigned */
typedef i16      UDPPortType
/** @note MUST be interpreted in implementation as unsigned */
typedef i32      TIENrType
/** @note MUST be interpreted in implementation as unsigned
          This is carried in the
          security envelope and must hence fit into 8 bits. */
typedef i8       VersionType
/** @note MUST be interpreted in implementation as unsigned */
typedef i16      MinorVersionType
/** @note MUST be interpreted in implementation as unsigned */
typedef i32      MetricType
/** @note MUST be interpreted in implementation as unsigned
          and unstructured */
typedef i64      RouteTagType
/** @note MUST be interpreted in implementation as unstructured
          label value */
typedef i32      LabelType
/** @note MUST be interpreted in implementation as unsigned */
typedef i32      BandwithInMegaBitsType
/** @note Key Value key ID type */
typedef i32      KeyIDType
/** node local, unique identification for a link (interface/tunnel
  * etc. Basically anything RIFT runs on). This is kept
  * at 32 bits so it aligns with BFD [RFC5880] discriminator size.
  */
typedef i32    LinkIDType
/** @note MUST be interpreted in implementation as unsigned,
          especially since we have the /128 IPv6 case. */
typedef i8     PrefixLenType
/** timestamp in seconds since the epoch */
typedef i64    TimestampInSecsType
/** security nonce.
    @note MUST be interpreted in implementation as rolling
          over unsigned value */
typedef i16    NonceType
/** LIE FSM holdtime type */
typedef i16    TimeIntervalInSecType
/** Transaction ID type for prefix mobility as specified by RFC6550,
    value MUST be interpreted in implementation as unsigned  */
typedef i8     PrefixTransactionIDType
/** Timestamp per IEEE 802.1AS, all values MUST be interpreted in
    implementation as unsigned.  */
struct IEEE802_1ASTimeStampType {
    1: required     i64     AS_sec;
    2: optional     i32     AS_nsec;
}
/** generic counter type */
typedef i64 CounterType
/** Platform Interface Index type, i.e. index of interface on hardware,
    can be used e.g. with RFC5837 */
typedef i32 PlatformInterfaceIndex

/** Flags indicating node configuration in case of ZTP.
 */
enum HierarchyIndications {
    /** forces level to `leaf_level` and enables according procedures */
    leaf_only                            = 0,
    /** forces level to `leaf_level` and enables according procedures */
    leaf_only_and_leaf_2_leaf_procedures = 1,
    /** forces level to `top_of_fabric` and enables according
        procedures */
    top_of_fabric                        = 2,
}

const PacketNumberType  undefined_packet_number    = 0
/** used when node is configured as top of fabric in ZTP.*/
const LevelType   top_of_fabric_level              = 24
/** default bandwidth on a link */
const BandwithInMegaBitsType  default_bandwidth    = 100
/** fixed leaf level when ZTP is not used */
const LevelType   leaf_level                  = 0
const LevelType   default_level               = leaf_level
const PodType     default_pod                 = 0
const LinkIDType  undefined_linkid            = 0

/** invalid key for key value */
const KeyIDType   invalid_key_value_key    = 0
/** default distance used */
const MetricType  default_distance         = 1
/** any distance larger than this will be considered infinity */
const MetricType  infinite_distance       = 0x7FFFFFFF
/** represents invalid distance */
const MetricType  invalid_distance        = 0
const bool overload_default               = false
const bool flood_reduction_default        = true
/** default LIE FSM LIE TX internval time */
const TimeIntervalInSecType   default_lie_tx_interval  = 1
/** default LIE FSM holddown time */
const TimeIntervalInSecType   default_lie_holdtime  = 3
/** multipler for default_lie_holdtime to hold down multiple neighbors */
const i8                      multiple_neighbors_lie_holdtime_multipler = 4
/** default ZTP FSM holddown time */
const TimeIntervalInSecType   default_ztp_holdtime  = 1
/** by default LIE levels are ZTP offers */
const bool default_not_a_ztp_offer        = false
/** by default everyone is repeating flooding */
const bool default_you_are_flood_repeater = true
/** 0 is illegal for SystemID */
const SystemIDType IllegalSystemID        = 0
/** empty set of nodes */
const set<SystemIDType> empty_set_of_nodeids = {}
/** default lifetime of TIE is one week */
const LifeTimeInSecType default_lifetime      = 604800
/** default lifetime when TIEs are purged is 5 minutes */
const LifeTimeInSecType purge_lifetime        = 300
/** optional round down interval when TIEs are sent with security hashes
    to prevent excessive computation. **/
const LifeTimeInSecType rounddown_lifetime_interval = 60
/** any `TieHeader` that has a smaller lifetime difference
    than this constant is equal (if other fields equal). */
const LifeTimeInSecType lifetime_diff2ignore  = 400

/** default UDP port to run LIEs on */
const UDPPortType     default_lie_udp_port       =  914
/** default UDP port to receive TIEs on, that can be peer specific */
const UDPPortType     default_tie_udp_flood_port =  915

/** default MTU link size to use */
const MTUSizeType     default_mtu_size           = 1400
/** default link being BFD capable */
const bool            bfd_default                = true

/** type used to target nodes with key value */
typedef i64 KeyValueTargetType

/** default target for key value are all nodes. */
const KeyValueTargetType    keyvaluetarget_default = 0
/** value for _all leaves_ addressing. Represented by all bits set. */
const KeyValueTargetType    keyvaluetarget_all_south_leaves = -1

/** undefined nonce, equivalent to missing nonce */
const NonceType       undefined_nonce            = 0;
/** outer security key id, MUST be interpreted as in implementation
    as unsigned */
typedef i8            OuterSecurityKeyID
/** security key id, MUST be interpreted as in implementation
    as unsigned */
typedef i32           TIESecurityKeyID
/** undefined key */
const TIESecurityKeyID undefined_securitykey_id   = 0;
/** Maximum delta (negative or positive) that a mirrored nonce can
    deviate from local value to be considered valid. */
const i16                     maximum_valid_nonce_delta   = 5;
const TimeIntervalInSecType   nonce_regeneration_interval = 300;

/** Direction of TIEs. */
enum TieDirectionType {
    Illegal           = 0,
    South             = 1,
    North             = 2,
    DirectionMaxValue = 3,
}

/** Address family type. */
enum AddressFamilyType {
   Illegal                = 0,
   AddressFamilyMinValue  = 1,
   IPv4                   = 2,
   IPv6                   = 3,
   AddressFamilyMaxValue  = 4,
}

/** IPv4 prefix type. */
struct IPv4PrefixType {
    1: required IPv4Address    address;
    2: required PrefixLenType  prefixlen;
} 

/** IPv6 prefix type. */
struct IPv6PrefixType {
    1: required IPv6Address    address;
    2: required PrefixLenType  prefixlen;
} 

/** IP address type. */
union IPAddressType {
    /** Content is IPv4 */
    1: optional IPv4Address   ipv4address;
    /** Content is IPv6 */
    2: optional IPv6Address   ipv6address;
} 

/** Prefix advertisement.

    @note: for interface
        addresses the protocol can propagate the address part beyond
        the subnet mask and on reachability computation that has to
        be normalized. The non-significant bits can be used
        for operational purposes.
*/
union IPPrefixType {
    1: optional IPv4PrefixType   ipv4prefix;
    2: optional IPv6PrefixType   ipv6prefix;
} 

/** Sequence of a prefix in case of move.
 */
struct PrefixSequenceType {
    1: required IEEE802_1ASTimeStampType  timestamp;
    /** Transaction ID set by client in e.g. in 6LoWPAN. */
    2: optional PrefixTransactionIDType   transactionid;
}

/** Type of TIE.
*/
enum TIETypeType {
    Illegal                                     = 0,
    TIETypeMinValue                             = 1,
    /** first legal value */
    NodeTIEType                                 = 2,
    PrefixTIEType                               = 3,
    PositiveDisaggregationPrefixTIEType         = 4,
    NegativeDisaggregationPrefixTIEType         = 5,
    PGPrefixTIEType                             = 6,
    KeyValueTIEType                             = 7,
    ExternalPrefixTIEType                       = 8,
    PositiveExternalDisaggregationPrefixTIEType = 9,
    TIETypeMaxValue                             = 10,
}

/** RIFT route types.
    @note: The only purpose of those values is to introduce an
           ordering whereas an implementation can choose internally
           any other values as long the ordering is preserved
 */
enum RouteType {
    Illegal               =  0,
    RouteTypeMinValue     =  1,
    /** First legal value. */
    /** Discard routes are most preferred */
    Discard               =  2,

    /** Local prefixes are directly attached prefixes on the
     *  system such as e.g. interface routes.
     */
    LocalPrefix           =  3,
    /** Advertised in S-TIEs */
    SouthPGPPrefix        =  4,
    /** Advertised in N-TIEs */
    NorthPGPPrefix        =  5,
    /** Advertised in N-TIEs */
    NorthPrefix           =  6,
    /** Externally imported north */
    NorthExternalPrefix   =  7,
    /** Advertised in S-TIEs, either normal prefix or positive
        disaggregation */
    SouthPrefix           =  8,
    /** Externally imported south */
    SouthExternalPrefix   =  9,
    /** Negative, transitive prefixes are least preferred */
    NegativeSouthPrefix   = 10,
    RouteTypeMaxValue     = 11,
}

enum   KVTypes {
    Experimental = 1,
    WellKnown    = 2,
    OUI          = 3,
}




