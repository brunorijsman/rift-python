# Security Feature Guide

## Introduction

RIFT-Python supports the following security features:

 * Configure authentication keys: key identifier, key algorithm, and key secret.

 * Configure outer authentication:

   * "Outer authentication" is used to validate that a directly connected neighbor is properly
     authenticated.
 
   * Select one key as the active_authentication_key that is used to compute the outer security           fingerprints in sent messages, and to validate the outer security fingerprint in received
     messages.

   * Optionally select zero or more additional accept_authentication_keys that are used to validate
     the outer security fingerprint in received messages (in addition to the
     active_authentication_key).
     This is intended to allow neighboring nodes to temporarily use a different outer key during
     key roll-over scenarios.
   
   * The active_authentication_key and accept_authentication_keys can configured for the node and/or
     for each interface individually.

 * Configure origin authentication:

   * "Origin authentication" is used to validate that the originator of a flooded TIE packet is
     properly authenticated.
 
   * Select one key as the active_origin_authentication_key that is used to compute the origin
     security fingerprints in sent TIE messages, and to validate the origin security fingerprint in received TIE messages.

   * Optionally select zero or more additional accept_origin_authentication_keys that are used to
     validate the origin security fingerprint in received TIE messages (in addition to the
     active_origin_authentication_key).
     This is intended to allow any node in the network to temporarily use a different origin key
     during key roll-over scenarios.
   
   * The active_origin_authentication_key and accept_origin_authentication_keys can only be
     configured per node and not per interface (since one cannot predict on which interface a
     flooded TIE will arrive).

 * Outer authentication and origin authentication can be configured independently of each other.

 * Generate, parse, and validate the envelope for all packets:

   * Generate packet-nrs for all sent packets (increasing within the scope of packet-type and
     address-family of the UDP packet).

   * Parse packet-nr for all received packet, and keep statistics on out-of-order packets. But 
     no other action is taken, e.g. flooding speed is not automatically throttled
     based on observed packet drops.

   * The visualization tool uses packet-nrs to associate packets sent by one node with packets 
     received on another node.

 * Generate, parse, and validate the outer security envelope for all packets:

   * Generate the outer fingerprint for all sent packets according to the configured
     active_authentication_key (if any).

   * Parse and validate the outer fingerprint for all received packets according to the
     configured active_authentication_key and accept_authentication_keys (if any).

   * Ignore all packets with an unrecognized outer key ID.

   * Ignore all packets with an incorrect outer fingerprint.

   * Generate increasing local nonces for all sent packets.

   * Parse the local nonce in all received packets, and reflect it in the remote nonce on all
     sent packet.

   * Parse the remote nonce (reflected nonce) in all received packets.

   * Detect and ignore packets whose reflected nonce is too far out of sync with the local nonce.

   * Generate the appropriate TIE remaining lifetime for all sent packets (actual remaining lifetime
     for TIE packet, and all ones for other packets).

   * Parse and process the TIE remaining lifetime in all received packets.

 * Generate, parse, and validate the origin security envelope for TIE packets:

   * Generate the TIE origin fingerprint for all sent TIE packets according to the configured
     active_origin_authentication_key (if any).

   * Parse and validate the TIE origin fingerprint for all received TIE packets according to the
     configured active_origin_authentication_key and accept_origin_authentication_keys (if any).

   * Ignore all packets with an unrecognized TIE origin key ID.

   * Ignore all packets with an incorrect TIE origin fingerprint.

 * Log outer and origin security envelope authentication errors.

 * Keep and report detailed statistics on many types of authentication errors and successful
   validations.

 * CLI command "show security" reports configured keys and authentication statistics for the node.

 * CLI command "show interface <i>interface-name</i> security" reports configured keys and
   authentication statistics for the interface.

## Configure authentication keys

You can configure the set of security authentication_keys at the top-level in the configuration file
(also known as the topology file) as follows:

<pre>
authentication_keys:
  - id: 1
    algorithm: hmac-sha-1
    secret: this-is-the-secret-for-key-1
  - id: 2
    algorithm: hmac-sha-256
    secret: this-is-the-secret-for-key-2
  - id: 3
    algorithm: hmac-sha-512
    secret: this-is-the-secret-for-key-3
</pre>

Each autentication_key is defined by:

 * A unique key ID. This is a number between 1 and 66051. Keys with a key-id in range 1...255 can
   be used as outer keys and/or origin keys. Keys with a key-id greater than 255 can only be used
   as an origin key.

 * The key algorithm. This is the algorithm used to calculate the fingerprint. The currently
   supported algorithms are: hmac-sha-1, hmac-sha-224, hmac-sha-256, hmac-sha-384, hmac-sha-512,
   sha-1, sha-224, sha-256, sha-384, sha-512.
   The hmac-sha-xxx algorithms are defined in [RFC2104](https://tools.ietf.org/html/rfc2104).
   The sha-xxx algorithms compute the fingerprint using SHA-XXX(secret + payload).

 * The key secret. This is a string.

Note: in the current implementation the key secret is shown in plain text in both the configuration
file and in the output of show commands. Obfuscation of secrets is not yet supported.

Configuring a set of keys in itself and by itself does not cause any fingerprints to be generated
or checked. You must use the active_authentication_key element and optionally the
accept_authentication_keys element to enable to actual generation and checking of outer
fingerprints. Similarly you must use the active_origin_authentication_key element and optionally the
accept_origin_authentication_keys element to enable to actual generation and checking of origin
fingerprints. These configuration statements are documented below.

## Configure the active_authentication_key

The active_authentication_key is the key that is used to compute the outer
fingerprints for sent packets and to validate the outer fingerprint for received packets.

 * If you configure active_authentication_key at the node level, it is used for all interfaces on
   the node.

 * If you configure active_authentication_key at the interface level, it use only for that
   particular interface.

 * If you configure active_authentication_key both at the node level and the interface level,
   the interface level configuration takes precedence.

Example of configuring the active_authentication_key at the node level:

<pre>
shards:
  - id: 0
    nodes:
      - name: node-1
        level: 2
        systemid: 1
        <b>active_authentication_key: 1</b>
        interfaces:
          - name: if1
            [...]
</pre>

Example of configuring the active_authentication_key at the interface level:

<pre>
shards:
  - id: 0
    nodes:
      - name: node-1
        level: 2
        systemid: 1
        interfaces:
          - name: if1
            <b>active_authentication_key: 1</b>
            [...]
</pre>

The active_authentication_key must be a key ID in the range 1 - 255.

It is not allowed to set the active_authentication_key to zero. If you wish to use null
outer authentication on sent packets you must omit active_authentication_key from the configuration.

The active_authentication_key must match one of the key IDs in the keys section (see 
the ["configure keys"](configure-keys) section.)

If the active_authentication_key is not configured, then null outer authentication is used: the sent
outer key-id is zero, and the sent outer fingerprint is empty.

## Configure accept_authentication_keys

For key roll-over scenarios you can configure a list of accept_authentication_keys.

Nodes always send packets with an outer key-id and outer fingerprint that is determined by the active_authentication_key as described above.

If the outer key-id and fingerprint in received packet cannot be validated using the
active_authentication_key then the node will attempt a secondary validation using the keys in
accept_authentication_keys. If the outer key-id and fingerprint in received packet matches any one
of the keys in accept_authentication_keys, it will also be accepted.

This mechanism is inteded for key roll-over scenarios. Since it is not possible to change the
configuration on multiple nodes at exactly the same time, they will be temporary situations where
the active_authentication_key has already changed on one node but not yet on another node.

 * If you configure accept_authentication_keys at the node level, it is used for all interfaces on
   the node.

 * If you configure accept_authentication_keys at the interface level, it use only for that
   particular interface.

 * If you configure accept_authentication_keys both at the node level and the interface level,
   the interface level configuration takes precedence.

Example of configuring accept_authentication_keys at the node level:

<pre>
shards:
  - id: 0
    nodes:
      - name: node-1
        level: 2
        systemid: 1
        active_authentication_key: 1
        <b>accept_authentication_keys: [2, 4]</b>
        interfaces:
          - name: if1
            [...]
</pre>

Example of configuring accept_authentication_keys at the interface level:

<pre>
shards:
  - id: 0
    nodes:
      - name: node-1
        level: 2
        systemid: 1
        interfaces:
          - name: if1
            active_authentication_key: 1
            <b>accept_authentication_keys: [2, 4]</b>
            [...]
</pre>

Each key in accept_authentication_keys must be a key ID in the range 1 - 255.

It is allowed to include key ID zero in accept_authentication_keys. This means that you are willing
to accept packets with null authentication.

Each non-zero key in accept_authentication_keys must match one of the key IDs in the keys section
(see the ["configure keys"](configure-keys) section.)

Key validation is "strict": if a packet is received with an outer key-id that does not
match the key-id of the active_authentication_key and also does not match the key-id of any of the
keys in accept_authentication_keys, then the packet is rejected (discarded) due to an authentication
error.
That said, if accept_authentication_keys contains key-id zero, the interface will accept packets
with outer key-id 0 and an empty outer fingerprint (i.e. packets will null outer authentication).

## Configure the active_origin_authentication_key

The active_origin_authentication_key is the key that is used to compute the origin
fingerprints for sent TIE packets and to validate the origin fingerprint for received TIE packets.

The active_origin_authentication_key can only be configured at the node level and not at the
interface level. This is because it is typically not possible to predict on which interface a
flooded TIE packet will arrive.

Example of configuring the active_origin_authentication_key at the node level:

<pre>
shards:
  - id: 0
    nodes:
      - name: node-1
        level: 2
        systemid: 1
        <b>active_origin_authentication_key: 1</b>
        interfaces:
          - name: if1
            [...]
</pre>

The active_origin_authentication_key must be a key ID in the range 1 - 25516777215.

It is not allowed to set the active_origin_authentication_key to zero. If you wish to use null
origin authentication on sent TIE packets you must omit active_origin_authentication_key from the
configuration.

The active_origin_authentication_key must match one of the key IDs in the keys section (see 
the ["configure keys"](configure-keys) section.)

If the active_origin_authentication_key is not configured, then null origin authentication is used:
the sent origin key-id is zero, and the sent origin fingerprint is empty.

## Configure accept_origin_authentication_keys

For key roll-over scenarios you can configure a list of accept_origin_authentication_keys.

Nodes always send packets with an origin key-id and origin fingerprint that is determined by the active_origin_authentication_key as described above.

If the origin key-id and fingerprint in received TIE packet cannot be validated using the
active_origin_authentication_key then the node will attempt a secondary validation using the keys in
accept_origin_authentication_keys. If the origin key-id and fingerprint in received packet matches
any one of the keys in accept_origin_authentication_keys, it will also be accepted.

This mechanism is inteded for key roll-over scenarios. Since it is not possible to change the
configuration on multiple nodes at exactly the same time, they will be temporary situations where
the active_origin_authentication_key has already changed on one node but not yet on another node.

The accept_origin_authentication_keys can only be configured at the node level and not at the
interface level. This is because it is typically not possible to predict on which interface a
flooded TIE packet will arrive.

Example of configuring accept_origin_authentication_keys at the node level:

<pre>
shards:
  - id: 0
    nodes:
      - name: node-1
        level: 2
        systemid: 1
        active_origin_authentication_key: 1
        <b>accept_origin_authentication_keys: [2, 4]</b>
        interfaces:
          - name: if1
            [...]
</pre>

Each key in accept_authentication_keys must be a key ID in the range 1 - 25516777215.

It is allowed to include key ID zero in accept_origin_authentication_keys. This means that you are
willing to accept packets with null authentication.

Each non-zero key in accept_authenticatiaccept_origin_authentication_keyson_keys must match one of
the key IDs in the keys section (see the ["configure keys"](configure-keys) section.)

Key validation is "strict": if a TIE packet is received with an origin key-id that does not
match the key-id of the active_origin_authentication_key and also does not match the key-id of any
of the keys in accept_origin_authentication_keys, then the packet is rejected (discarded) due to an authentication error.
That said, if accept_origin_authentication_keys contains key-id zero, the node will accept TIE
packets with origin key-id 0 and an empty origin fingerprint (i.e. packets will null origin
authentication).

## Fingerprints

RIFT-Python computes the outer fingerprints for all sent packets as follows:

 * RIFT-Python uses the configured active_authentication_key to compute the outer key-id and the
   outer fingerprint for all sent packets.

 * If active_authentication_key is not configured, then the outer key-id is set to zero and the
   outer fingerprint is set to empty.

 * If active_authentication_key is not configured, then the outer key-id in the sent packet is set
   to zero and the outer fingerprint is set to empty.

RIFT-Python computes the origin fingerprints for sent TIE packets as follows:

 * RIFT-Python uses the configured active_origin_authentication_key to compute the origin key-id
   and the originr fingerprint for sent TIE packets.

 * If active_origin_authentication_key is not configured, then the origin key-id is set to zero and
   the origin fingerprint is set to empty.

 * If active_origin_authentication_key is not configured, then the outer key-id in the sent packet
   is set to zero and the outer fingerprint is set to empty.

RIFT-Python validates the outer fingerprints for all received packets as follows:

 * RIFT-Python checks whether the outer key-id in the received packet matches the configured
   active_authentication_key. If so, RIFT-Python validates the received outer fingerprint using that
   key.

 * Otherwise RIFT-Python checks whether the outer key-id in the received packet matches any of the
   keys in the configured accept_authentication_keys. If so, RIFT-Python validates the received
   outer fingerprint using that key.

 * If the received packet contains a zero outer key-id and an empty outer fingerprint, the packet
   will be accepted if and only if (a) active_authentication_key is not configured OR
   (b) accept_authentication_keys contains key-id zero.

RIFT-Python validates the origin fingerprints for received TIE packets as follows:

 * RIFT-Python checks whether the origin key-id in the received TIE packet matches the configured
   active_origin_authentication_key. If so, RIFT-Python validates the received origin fingerprint
   using that key.

 * Otherwise RIFT-Python checks whether the origin key-id in the received TIE packet matches any of
   the keys in the configured accept_origin_authentication_keys. If so, RIFT-Python validates the
   received origin fingerprint using that key.

 * If the received packet contains a zero origin key-id and an empty origin fingerprint, the packet
   will be accepted if and only if (a) active_orgin_authentication_key is not configured OR
   (b) accept_origin_authentication_keys contains key-id zero.

RIFT-Python keeps detailed statistics on both succesful outer and origin key validations, as well
as many types on non-successful outer and key validations.
You can view these statistics using the "show security" and "show interface <i>interface-name</i>
security" commands (see below for details).

All authentication errors are logged as an ERROR.

## Key roll-overs

The following proceduce is suggested to perform a roll-over from key A to key B.

In this example we illustrate a roll-over for the outer key, but the same procedure can also be
followed for origin key roll-overs.

* We assume that the starting scenario is that we have two nodes (node1 and node2) that both
  have active_authentication_key set to A.

* On node1, while keeping active_authentication_key set to A, set accepts_authentication_keys to
  [ A, B ].

* On node2, while keeping active_authentication_key set to A, set accepts_authentication_keys to
  [ A, B ].

* On node1, while keeping accepts_authentication_keys set to [ A, B ], change
  active_authentication_key to B.

* On node2, while keeping accepts_authentication_keys set to [ A, B ], change
  active_authentication_key to B.

* On node1, while keeping active_authentication_key set to A, unconfigure
  accepts_authentication_keys.

* On node2, while keeping active_authentication_key set to A, unconfigure
  accepts_authentication_keys.

Note: currently RIFT-Python does not support run-time configuration changes. To change the
configuration, you must edit the configuration file (also known as the topology file) and restart
the RIFT-Python process. This section is only intended how the concept of accept_key will enable
roll-overs if and when RIFT-Python does support run-time configuration changes at some point in the
future.

## Weak nonces

Note: in a recent update, the RIFT draft switched from "nonce" terminology to "weak nonce"
terminology. The RIFT-Python code still uses the term "nonce" (without the weak qualifier) in
the documentation and in the output of show commands and in log messages.

RIFT-Python generates the non-decreasing local-nonce for sent packets as follows:

 * The local-nonce is increases whenever a state transition occurs in the LIE FSM. This happens
   regardless of how fast state transitions occur (i.e. local-nonce increases due to state changes
   are currently not subject to any hold-down timer.)

 * The local-nonce is increased whenever a packet is sent, but not more frequently than once per
   minute. 

 * The local-nonce for the first sent packet is a random number between 1 and 65535.

RIFT-Python generates the reflected remote-nonce for sent packets as follows:

 * In state ONE_WAY remote-nonce is alway set to zero.
 
 * In states TWO_WAY and THREE_WAY, remote-nonce is set to the reflected local-nonce in the most
   recently received LIE packet from the neighbor.

RIFT-Python validates the reflected remote-nonce in received packets as follows:

 * If RXNonce is reflected remote-nonce in the received packet, and TXNonce is the local-nonce
   in the most recently sent packet, then RX-Nonce is accepted if and only if:
   
   TXNonce - 5 <= RXNonce <= TXNonce

 * The math for comparing nonces takes into account the possibility of a nonce rollover.

All of the logic for generating and validating nonces described above happens on a per-interface
basis.

If debug logging is turned on (command line option "--log-level debug"), both the local nonce and
the remote nonce are reported in the logs for sent and received messages, for example:

<pre>
2019-04-22 19:22:55,179:DEBUG:node.if.tx:[node-1:if1] Send IPv4 TIE from 192.168.0.100:49307 to 192.168.0.100:10005 packet-nr=2 outer-key-id=1 <b>nonce-local=7 nonce-remote=5</b> remaining-lie-lifetime=604799 outer-fingerprint-len=5 origin-key-id=1 origin-fingerprint-len=5 protocol-packet=ProtocolPacket(...
</pre>

If the received remote nonce is not in the expected range, a "Reflected nonce out of sync"
authentication error is declared.

As with any type of authentication error, the received packet is not processed any further and
ignored for further processing, the error is logged as an ERROR, is counted in the statistics
("show ... statistics"), and is reported in "show security" (see below for example output).

## Packet numbers

RIFT-Python generates packet numbers (packet-nrs) for each sent packet.

The packet-nr is unique within the scope of the packet-type and the address family of the UDP
packet. For example:

 * All the IPv4 TIE packets that a give node sends, have increasing packet-nrs: 1, 2, 3, 4, ...

 * The IPv4 TIE packets and the IPv4 TIDE packets sent by a given node each have their own
   independent sequence of increasing packet-nrs.

 * The IPv4 TIE packets and the IPv6 TIE packets sent by a given node each have their own
   independent sequence of increasing packet-nrs.

The reason for this is to avoid false positives of reordering for packets that are sent on different
sockets or by different threads.

If debug logging is turned on (command line option "--log-level debug"), the packet-nrs are reported
in the logs for sent and received messages, for example:

<pre>
2019-04-22 19:22:55,179:DEBUG:node.if.tx:[node-1:if1] Send IPv4 TIE from 192.168.0.100:49307 to 192.168.0.100:10005 <b>packet-nr=2</b> outer-key-id=1 nonce-local=7 nonce-remote=5 remaining-lie-lifetime=604799 outer-fingerprint-len=5 origin-key-id=1 origin-fingerprint-len=5 protocol-packet=ProtocolPacket(...
</pre>

RIFT-Python uses the packet-nr to detect packet misordering: if the packet-nr of a received packet
is not equal to the packet-nr plus one of the previously received packet (of the same packet-type 
and the same address-family), then the packet is declared to be misordered. 

Note that we use the generic term misordering, but in reality it could indicate re-ordered,
dropped or dupplicated packets.

Misordered packets are reported in the output of "show ... statistics" for example:

<pre>
node-1> <b>show interface if1 statistics</b>
Traffic:
+---------------------------------------------------+------------------------+------------------------------------+-------------------+
| Description                                       | Value                  | Last Rate                          | Last Change       |
|                                                   |                        | Over Last 10 Changes               |                   |
+---------------------------------------------------+------------------------+------------------------------------+-------------------+
.                                                   .                        .                                    .                   .
.                                                   .                        .                                    .                   .
.                                                   .                        .                                    .                   .
+---------------------------------------------------+------------------------+------------------------------------+-------------------+
| RX IPv4 LIE Misorders                             | 6 Packets              | 1.03 Packets/Sec                   | 0d 00h:00m:00.56s |
+---------------------------------------------------+------------------------+------------------------------------+-------------------+
| RX IPv6 LIE Misorders                             | 6 Packets              | 1.03 Packets/Sec                   | 0d 00h:00m:00.56s |
+---------------------------------------------------+------------------------+------------------------------------+-------------------+
| RX IPv4 TIE Misorders                             | 0 Packets              |                                    |                   |
+---------------------------------------------------+------------------------+------------------------------------+-------------------+
| RX IPv6 TIE Misorders                             | 0 Packets              |                                    |                   |
+---------------------------------------------------+------------------------+------------------------------------+-------------------+
| RX IPv4 TIDE Misorders                            | 1 Packet               |                                    | 0d 00h:00m:01.54s |
+---------------------------------------------------+------------------------+------------------------------------+-------------------+
| RX IPv6 TIDE Misorders                            | 0 Packets              |                                    |                   |
+---------------------------------------------------+------------------------+------------------------------------+-------------------+
| RX IPv4 TIRE Misorders                            | 2 Packets              | 1.00 Packets/Sec                   | 0d 00h:00m:02.45s |
+---------------------------------------------------+------------------------+------------------------------------+-------------------+
| RX IPv6 TIRE Misorders                            | 0 Packets              |                                    |                   |
+---------------------------------------------------+------------------------+------------------------------------+-------------------+
| Total RX IPv4 Misorders                           | 9 Packets              | 1.65 Packets/Sec                   | 0d 00h:00m:00.56s |
+---------------------------------------------------+------------------------+------------------------------------+-------------------+
| Total RX IPv6 Misorders                           | 6 Packets              | 1.03 Packets/Sec                   | 0d 00h:00m:00.56s |
+---------------------------------------------------+------------------------+------------------------------------+-------------------+
| Total RX Misorders                                | 15 Packets             | 3.00 Packets/Sec                   | 0d 00h:00m:00.56s |
+---------------------------------------------------+------------------------+------------------------------------+-------------------+
</pre>

No log message is generate when a misordered packet is detected.

RIFT-Python currently does not take any action when it observed misordered packets. For example, it
does not throttle flooding when misordered packets are observed.

The [log visualization tool](doc/log-visualization.md) uses the packet-nrs to associate a sent
message on one node with a received message on a neighbor node.

## Show security

The CLI command "show security" reports configured origin keys and security statistics for the
current node:

<pre>
node2> show security
Security Keys:
+--------+-----------+----------------------------------+
| Key ID | Algorithm | Secret                           |
+--------+-----------+----------------------------------+
| 0      | null      |                                  |
+--------+-----------+----------------------------------+
| 1      | sha-256   | this-is-the-secret-for-key-1     |
+--------+-----------+----------------------------------+
| 2      | sha-256   | this-is-the-secret-for-key-2     |
+--------+-----------+----------------------------------+
| 3      | sha-256   | this-is-the-secret-for-key-3     |
+--------+-----------+----------------------------------+
| 4      | sha-256   | this-is-the-secret-for-key-4     |
+--------+-----------+----------------------------------+
| 66051  | sha-256   | this-is-the-secret-for-key-66051 |
+--------+-----------+----------------------------------+

Origin Keys:
+--------------------+-----------+
| Key                | Key ID(s) |
+--------------------+-----------+
| Active Origin Key  | 4         |
+--------------------+-----------+
| Accept Origin Keys | 66051     |
+--------------------+-----------+

Security Statistics:
+------------------------------------------------+-------------------------+-------------------------------------+-------------------+
| Description                                    | Value                   | Last Rate                           | Last Change       |
|                                                |                         | Over Last 10 Changes                |                   |
+------------------------------------------------+-------------------------+-------------------------------------+-------------------+
| Missing outer security envelope                | 0 Packets, 0 Bytes      |                                     |                   |
+------------------------------------------------+-------------------------+-------------------------------------+-------------------+
| Zero outer key id not accepted                 | 0 Packets, 0 Bytes      |                                     |                   |
+------------------------------------------------+-------------------------+-------------------------------------+-------------------+
| Non-zero outer key id not accepted             | 0 Packets, 0 Bytes      |                                     |                   |
+------------------------------------------------+-------------------------+-------------------------------------+-------------------+
| Incorrect outer fingerprint                    | 0 Packets, 0 Bytes      |                                     |                   |
+------------------------------------------------+-------------------------+-------------------------------------+-------------------+
| Missing TIE origin security envelope           | 0 Packets, 0 Bytes      |                                     |                   |
+------------------------------------------------+-------------------------+-------------------------------------+-------------------+
| Zero TIE origin key id not accepted            | 0 Packets, 0 Bytes      |                                     |                   |
+------------------------------------------------+-------------------------+-------------------------------------+-------------------+
| Non-zero TIE origin key id not accepted        | 0 Packets, 0 Bytes      |                                     |                   |
+------------------------------------------------+-------------------------+-------------------------------------+-------------------+
| Unexpected TIE origin security envelope        | 0 Packets, 0 Bytes      |                                     |                   |
+------------------------------------------------+-------------------------+-------------------------------------+-------------------+
| Inconsistent TIE origin key id and fingerprint | 0 Packets, 0 Bytes      |                                     |                   |
+------------------------------------------------+-------------------------+-------------------------------------+-------------------+
| Incorrect TIE origin fingerprint               | 0 Packets, 0 Bytes      |                                     |                   |
+------------------------------------------------+-------------------------+-------------------------------------+-------------------+
| Reflected nonce out of sync                    | 0 Packets, 0 Bytes      |                                     |                   |
+------------------------------------------------+-------------------------+-------------------------------------+-------------------+
| Total Authentication Errors                    | 0 Packets, 0 Bytes      |                                     |                   |
+------------------------------------------------+-------------------------+-------------------------------------+-------------------+
| Non-empty outer fingerprint accepted           | 73 Packets, 16836 Bytes | 8.79 Packets/Sec, 2221.12 Bytes/Sec | 0d 00h:00m:00.50s |
+------------------------------------------------+-------------------------+-------------------------------------+-------------------+
| Non-empty origin fingerprint accepted          | 6 Packets, 1464 Bytes   | 2.56 Packets/Sec, 636.75 Bytes/Sec  | 0d 00h:00m:09.50s |
+------------------------------------------------+-------------------------+-------------------------------------+-------------------+
| Empty outer fingerprint accepted               | 0 Packets, 0 Bytes      |                                     |                   |
+------------------------------------------------+-------------------------+-------------------------------------+-------------------+
| Empty origin fingerprint accepted              | 0 Packets, 0 Bytes      |                                     |                   |
+------------------------------------------------+-------------------------+-------------------------------------+-------------------+
</pre>

Currently, they key secrets are shown in plain text in both the configuration and in the output
of "show security". Obfuscation of key secrets is not yet supported.

The authentication error statistics reported by "show security" are exactly the same as those
that are reported by "show ... statistics". However, in the latter case they are easily
overlooked because they are hidden in a sea of other statistics.

## Show interface <i>interface-name</i> security

The CLI command "show interface <i>interface-name</i>security" reports configured outer keys and
security statistics for the specified interface:

<pre>
node2> show interface if2 security
Outer Keys:
+-------------------+-----------+-----------------------+
| Key               | Key ID(s) | Configuration Source  |
+-------------------+-----------+-----------------------+
| Active Outer Key  | 2         | Interface Active Key  |
+-------------------+-----------+-----------------------+
| Accept Outer Keys | 3         | Interface Accept Keys |
+-------------------+-----------+-----------------------+

Nonces:
+--------------------------+----------------+
| Last Received LIE Nonce  | 45448          |
+--------------------------+----------------+
| Last Sent Nonce          | 30085          |
+--------------------------+----------------+
| Next Sent Nonce Increase | 27.605848 secs |
+--------------------------+----------------+

Security Statistics:
+------------------------------------------------+-------------------------+------------------------------------+-------------------+
| Description                                    | Value                   | Last Rate                          | Last Change       |
|                                                |                         | Over Last 10 Changes               |                   |
+------------------------------------------------+-------------------------+------------------------------------+-------------------+
| Missing outer security envelope                | 0 Packets, 0 Bytes      |                                    |                   |
+------------------------------------------------+-------------------------+------------------------------------+-------------------+
| Zero outer key id not accepted                 | 0 Packets, 0 Bytes      |                                    |                   |
+------------------------------------------------+-------------------------+------------------------------------+-------------------+
| Non-zero outer key id not accepted             | 0 Packets, 0 Bytes      |                                    |                   |
+------------------------------------------------+-------------------------+------------------------------------+-------------------+
| Incorrect outer fingerprint                    | 0 Packets, 0 Bytes      |                                    |                   |
+------------------------------------------------+-------------------------+------------------------------------+-------------------+
| Missing TIE origin security envelope           | 0 Packets, 0 Bytes      |                                    |                   |
+------------------------------------------------+-------------------------+------------------------------------+-------------------+
| Zero TIE origin key id not accepted            | 0 Packets, 0 Bytes      |                                    |                   |
+------------------------------------------------+-------------------------+------------------------------------+-------------------+
| Non-zero TIE origin key id not accepted        | 0 Packets, 0 Bytes      |                                    |                   |
+------------------------------------------------+-------------------------+------------------------------------+-------------------+
| Unexpected TIE origin security envelope        | 0 Packets, 0 Bytes      |                                    |                   |
+------------------------------------------------+-------------------------+------------------------------------+-------------------+
| Inconsistent TIE origin key id and fingerprint | 0 Packets, 0 Bytes      |                                    |                   |
+------------------------------------------------+-------------------------+------------------------------------+-------------------+
| Incorrect TIE origin fingerprint               | 0 Packets, 0 Bytes      |                                    |                   |
+------------------------------------------------+-------------------------+------------------------------------+-------------------+
| Reflected nonce out of sync                    | 0 Packets, 0 Bytes      |                                    |                   |
+------------------------------------------------+-------------------------+------------------------------------+-------------------+
| Total Authentication Errors                    | 0 Packets, 0 Bytes      |                                    |                   |
+------------------------------------------------+-------------------------+------------------------------------+-------------------+
| Non-empty outer fingerprint accepted           | 90 Packets, 19762 Bytes | 3.00 Packets/Sec, 686.58 Bytes/Sec | 0d 00h:00m:00.38s |
+------------------------------------------------+-------------------------+------------------------------------+-------------------+
| Non-empty origin fingerprint accepted          | 3 Packets, 692 Bytes    | 2.05 Packets/Sec, 481.11 Bytes/Sec | 0d 00h:00m:31.36s |
+------------------------------------------------+-------------------------+------------------------------------+-------------------+
| Empty outer fingerprint accepted               | 0 Packets, 0 Bytes      |                                    |                   |
+------------------------------------------------+-------------------------+------------------------------------+-------------------+
| Empty origin fingerprint accepted              | 0 Packets, 0 Bytes      |                                    |                   |
+------------------------------------------------+-------------------------+------------------------------------+-------------------+
</pre>

Currently, they key secrets are shown in plain text in both the configuration and in the output
of "show interface <i>interface-name</i> security". Obfuscation of key secrets is not yet supported.

The authentication error statistics reported by "show interface <i>interface-name</i> security" 
are exactly the same as those that are reported by "show interface <i>interface-name</i>
statistics". However, in the latter case they are easily overlooked because they are hidden in a sea
of other statistics.