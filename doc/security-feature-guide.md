# Security Feature Guide

## Introduction

RIFT-Python supports the following security features:

 * Configure keys: key identifier, key algorithm, and key secret.

 * Select one key as the active key to be used to compute the security fingerprints for sent
   messages.

 * Select zero or more additional keys as accept keys to allow other nodes to use a different
   active key during key roll-over scenarios.

 * Generate, parse, and validate the envelope for all packets:

   * Generate packet-nrs for all sent packets (increasing within the scope of packet-type and
     address-family of the UDP packet).

   * Parse packet-nr for all received packet, and keep statistics on out-of-order packets. But 
     no other action is taken, e.g. flooding speed is not automatically throttled
     based on observed packet drops.

   * The visualization tool uses packet-nrs to associate packets sent by one node with packets 
     received on another node.

 * Generate, parse, and validate the outer security envelope for all packets:

   * Generate the outer fingerprint for all sent packets according to the configured active
     key (if any).

   * Parse and validate the outer fingerprint for all received packets according to the
     configured active key and accept keys (if any).

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

 * Generate, parse, and validate the TIE origin security envelope for all packets:

   * Generate the TIE origin fingerprint for all sent TIE packets according to the configured active
     key (if any).

   * Parse and validate the TIE origin fingerprint for all received TIE packets according to the
     configured active key and accept keys (if any).

   * Ignore all packets with an unrecognized TIE origin key ID.

   * Ignore all packets with an incorrect TIE origin fingerprint.

 * Log and keep statistics on all types of outer security envelope authentication errors.

 * CLI command "show security" reports configured keys and detected authentication errors on all
   interfaces.

## Configure keys

You can configure the set of security keys at the top-level in the configuration file (also known
as the topology file) as follows:

<pre>
keys:
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

Each key is defined by:

 * A unique key ID. This is a number between 1 and 255.

 * The key algorithm. This is the algorithm used to calculate the fingerprint. The currently
   supported algorithms are: hmac-sha-1, hmac-sha-224, hmac-sha-256, hmac-sha-384, hmac-sha-512.
   These algorithms are defined in [RFC2104](https://tools.ietf.org/html/rfc2104).

 * The key secret. This is a string.

Note: in the current implementation the key secret is shown in plain text in both the configuration
file and in the output of show commands. Obfuscation of secrets is not yet supported.

Configuring a set of keys in itself and by itself does not cause any fingerprints to be generated
of checked. You must use the active-key element and optionally the accept-keys element (both
documented below) to enable to actual generation and checking of fingerprints.

## Configure the active key

The "active key" for a node is the key that the node uses to generate *all* fingerprints:

 * All outer fingerprints on all interfaces.

 * All TIE origin fingerprints.

For the sake of simplicity, RIFT-Python does currently not support using different outer keys on
different interfaces, nor does it support using a different outer key and TIE origin key.

As a consequence, RIFT-Python currently only supports the Fabric Association Model (FAM), and not
the the Node Association Model (NAM) or Port Association Model (PAM).

You can configure the active key at the node level in the configuration file (also known
as the topology file) as follows:

<pre>
shards:
  - id: 0
    nodes:
      - name: node-1
        level: 2
        systemid: 1
        <b>active_key: 1</b>
        interfaces:
          - name: if1
            [...]
</pre>

The active key must be a key ID in the range 1 - 255.

It is not allowed to set the active key to zero. If you wish to use null authentication on sent
packets you must omit the active key from the configuration.

The active key must match one of the key IDs in the keys section (see 
the ["configure keys"](configure-keys) section.)

If the active_key is not configured, then null authentication is used: the sent key-id is zero,
and the sent fingerprint is empty.


## Configure accept keys

For key roll-over scenarios you can configure a list of accept keys.

Nodes always end packets with a key-id and fingerprint that is determined by the active key.
But when a node receives a packet with a non-zero key-id and a non-empty fingerprint, it will
validate and accept the received packet if the received key-id matches the active key *or* any one
of the accept keys.

You can configure the list of accept keys at the node level in the configuration file (also known
as the topology file) as follows:

<pre>
shards:
  - id: 0
    nodes:
      - name: node-1
        level: 2
        systemid: 1
        active_key: 1
        <b>accept_keys: [2, 3]</b>
        interfaces:
          - name: if1
            [...]
</pre>

Each accept key must be a key ID in the range 0 - 255.

It is allowed to include key ID zero in the accept keys. This means that you are willing to accept
packets with null authentication.

Each non-zero accept key must match one of the key IDs in the keys section (see 
the ["configure keys"](configure-keys) section.)

See section TODO for more details on how to do key roll-overs.

## Fingerprints

RIFT-Python uses the configured active key to generate the key-id and the fingerprint in both the
outer security header for all sent packets, and in the TIE origin security header for TIE packets.

If no active key has been configured, RIFT-Python uses null authentication: it sets the key-id
to zero and it sets the fingerprint to an empty fingerprint.

For received packets, RIFT-Python compares the received key-id against both the active key
and the list of accept keys. It does this independently for the outer key-id and the TIE origin
key-id (if present). In other words, although RIFT-Python always sets the outer key-id and the
TIE origin key-id to the same value for all sent packets, it can handle different key-ids in the
outer security envelope and the TIE origin security envelope for received packets.

If no matching key is found, an "Unknown key id" authentication error is declared.

If a matching key is found, it is used to validate the fingerprint. If the fingerprint does
not match, an "Incorrect fingerprint" authentication error is declared.

There are also some less common other types of authentication errors. You can see a full list
in the output of "show interface ... statistics".

Whenever an authentication error occurs, the received packet is not processed any further and
ignored for further processing.

All authentication errors are logged as an ERROR, are counted in the statistics
("show ... statistics"), and are reported in "show security", for example:

<pre>
node-1> show interface if1 statistics
Traffic:
+---------------------------------------------------+------------------------+------------------------------------+-------------------+
| Description                                       | Value                  | Last Rate                          | Last Change       |
|                                                   |                        | Over Last 10 Changes               |                   |
+---------------------------------------------------+------------------------+------------------------------------+-------------------+
.                                                   .                        .                                    .                   .
.                                                   .                        .                                    .                   .
+---------------------------------------------------+------------------------+------------------------------------+-------------------+
| RX Incorrect outer fingerprint                    | 16 Packets, 2624 Bytes | 2.25 Packets/Sec, 368.91 Bytes/Sec | 0d 00h:00m:00.33s |
+---------------------------------------------------+------------------------+------------------------------------+-------------------+
.                                                   .                        .                                    .                   .
.                                                   .                        .                                    .                   .
+---------------------------------------------------+------------------------+------------------------------------+-------------------+
| Total RX Authentication Errors                    | 16 Packets, 2624 Bytes | 2.25 Packets/Sec, 368.91 Bytes/Sec | 0d 00h:00m:00.33s |
+---------------------------------------------------+------------------------+------------------------------------+-------------------+
</pre>

<pre>
node-1> show security
Security Keys:
+--------+--------------+------------------------------+--------+--------+
| Key ID | Algorithm    | Secret                       | Active | Accept |
+--------+--------------+------------------------------+--------+--------+
| 1      | hmac-sha-1   | this-is-the-secret-for-key-1 | Active |        |
+--------+--------------+------------------------------+--------+--------+
| 2      | hmac-sha-1   | this-is-the-secret-for-key-2 |        |        |
+--------+--------------+------------------------------+--------+--------+
| 3      | hmac-sha-1   | this-is-the-secret-for-key-3 |        |        |
+--------+--------------+------------------------------+--------+--------+
| 4      | hmac-sha-256 | this-is-the-secret-for-key-4 |        |        |
+--------+--------------+------------------------------+--------+--------+
| 5      | hmac-sha-256 | this-is-the-secret-for-key-5 |        |        |
+--------+--------------+------------------------------+--------+--------+

Authentication Errors:
+-----------+--------------------------------+--------------------------+------------------------------------+-------------------+
| Interface | Authentication                 | Error                    | Error                              | Last Change       |
|           | Errors                         | Count                    | Rate                               |                   |
+-----------+--------------------------------+--------------------------+------------------------------------+-------------------+
| if1       | RX Incorrect outer fingerprint | 188 Packets, 30832 Bytes | 2.25 Packets/Sec, 368.91 Bytes/Sec | 0d 00h:00m:00.67s |
+-----------+--------------------------------+--------------------------+------------------------------------+-------------------+
| if2       | RX Unknown outer key id        | 188 Packets, 30832 Bytes | 2.25 Packets/Sec, 368.80 Bytes/Sec | 0d 00h:00m:00.65s |
+-----------+--------------------------------+--------------------------+------------------------------------+-------------------+
</pre>

## Key roll-overs

The following proceduce is suggested to perform a roll-over from key A to key B:

* On each node, add key B to the list of keys, and add keys A and B to the accept keys. At this
  point, each node is still using key A as the active key, but is prepared to accept either key A or
  key B from other nodes.

* On each node, change the active key from key A to key B. At this point, the nodes that are still
  using key A as the active key are willing to accept key B from the nodes that have already been
  switched over. And the nodes that have already switched over to key B are willing to accept key A
  from the nodes that have not yet been switched over. Note that we need to worry also about nodes
  that are more than one hop away (because of the TIE origin fingerprint), and not just about
  neighbor nodes.

* After all nodes have been switched over, the accept keys configuration can be removed.

Note: currently RIFT-Python does not support run-time configuration changes. To change the
configuration, you must edit the configuration file (also known as the topology file) and restart
the RIFT-Python process.

## Nonces

RIFT-Python generates increasing local nonces for all sent packets.

The current implementation increases the local nonce by one for every sent packet. It does not
attempt to reduce the number of local nonce changes (and hence the number of times that the outer
fingerprint needs to be computed) by only changing the local nonce periodically, e.g. every minute
(plus every FSM state change).

RIFT-Python takes the local nonce from the most recently recieved LIE packet, and reflects it in
the remote nonce in all sent packets to that same node.

If debug logging is turned on (command line option "--log-level debug"), both the local nonce and
the remote nonce are reported in the logs for sent and received messages, for example:

<pre>
2019-04-22 19:22:55,179:DEBUG:node.if.tx:[node-1:if1] Send IPv4 TIE from 192.168.0.100:49307 to 192.168.0.100:10005 packet-nr=2 outer-key-id=1 <b>nonce-local=7 nonce-remote=5</b> remaining-lie-lifetime=604799 outer-fingerprint-len=5 origin-key-id=1 origin-fingerprint-len=5 protocol-packet=ProtocolPacket(...
</pre>

RIFT-Python checks whether its neighbor is reflecting nonces that are sufficiently close to the
most recently sent local noce: the received remote must be in the range [sent local nonce - 5 ... 
sent local nonce] (taking into account wrap-arounds).

If the received remote nonce is not in the expected range, a "Reflected nonce out of sync"
authentication error is declared.


As with any type of authentication error, the received packet is not processed any further and
ignored for further processing, the error is logged as an ERROR, is counted in the statistics
("show ... statistics"), and is reported in "show security", for example:

<pre>
node-1> show security
[...]

Authentication Errors:
+-----------+--------------------------------+------------------------+------------------------------------+-------------------+
| Interface | Authentication                 | Error                  | Error                              | Last Change       |
|           | Errors                         | Count                  | Rate                               |                   |
+-----------+--------------------------------+------------------------+------------------------------------+-------------------+
| if1       | RX Reflected nonce out of sync | 10 Packets, 1640 Bytes | 2.30 Packets/Sec, 376.98 Bytes/Sec | 0d 00h:00m:00.92s |
+-----------+--------------------------------+------------------------+------------------------------------+-------------------+
</pre>

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
