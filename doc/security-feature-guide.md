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

Each accept key must match one of the key IDs in the keys section (see 
the ["configure keys"](configure-keys) section.)

See section TODO for more details on how to do key roll-overs.
