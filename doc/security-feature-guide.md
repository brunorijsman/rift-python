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
