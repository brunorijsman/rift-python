# Routing In Fat Trees (RIFT) Zero Touch Provisioning (ZTP) Preliminary Interoperability Testing Report

## Summary

This document reports the preliminary results for interoperability testing of the Zero Touch Provisioning (ZTP) Finite State Machine (FSM) between the open source Python RIFT implementation and the Juniper RIFT implementation.

So far, no major interoperability issues have been found: the two implementations could successfully auto-discover level values and establish 3-way adjacencies.

Some minor issues were discovered during the interoperability testing. All of these issues have been documented in the [RIFT Draft Comments Living Document on Google Docs](http://bit.ly/rift-comments). A subset of these issues have been discussed in great detail on the [RIFT mailing list](http://bit.ly/rift-mailing-list) and/or the [RIFT-Python Github issues list](http://bit.ly/rift-python-issues-list) and/or the RIFT weekly technical conference calls.

A few of the discovered issue will require non-trivial changes to the protocol (e.g. the introduction of a distinct MultipleNeighbors state). The vast majority of discovered issues only require clarifications in the text of the specification. I will be the first to admit that some of the comments border on the pedantic.

The ZTP FSM testing is not yet complete: more test cases for more complex scenarios are needed. This report will be updated when those test cases have been implemented and executed.

## Introduction

This is a follow-up on the first round of interoperability testing between this RIFT implementation
("RIFT-Python") and Juniper's RIFT implementation ("RIFT-Juniper").

The first routing of interoperability testing was done at the IETF 102 hackathon in Montreal; there
we tested the Link Information Element (LIE) Finite State Machine (FSM) and verified that the two
implementations could successfully establish a 3-way adjacency.

In this second round of interoperability testing I tested the Zero Touch Provisioning (ZTP)
mechanism, which is also referred to as "automatic level derivation" or the "level determination
procedure" in the specification.

## Tested Versions

### RIFT-Juniper Version

I used RIFT-Juniper version 0.6 (customer experimental distribution) for my interoperability testing.

<pre>
$ <b>rift-environ --version</b>

====================================================
ROUTING IN FAT TREES (RIFT) Experimental Environment
Copyright (c) 2016-, Juniper Networks, Inc.
All rights reserved.
====================================================
 
version: experimental 0.6.0

features: ["redis", "extensive-logging", "standalone-version", "YAML PLATFORM"]

thrift encoding schema: 11.0
thrift statistics schema: 7.0
thrift services schema: 12.1

git: 2018-07-09 #926acb7
</pre>

I used both the macOS binary and the Linux binary. I found that small 2 or 3 node topology worked fine on macOS, but significantly larger topologies only worked on Linux (I was not willing to mess with my macOS settings to tune networking to make large topologies work). 

See the [IETF 102 Hackathon Interop Testing Report](http://bit.ly/ietf-102-rift-hackathon-interop-report) for details on how to obtain and install the rift-juniper binary image.

### RIFT-Python Version

The RIFT-Python code is open source and publicly [available on Github](http://bit.ly/rift-python).

See the [Installation guide](#installation.md) for detailed instructions on how to obtain and install RIFT-Python.

At the time of writing (16-Aug-2018), the RIFT-Python code is not yet a complete implementation. It supports the Link Information Element (LIE) Finite State Machine (FSM) and it supports the Zero Touch Provisioning (ZTP) FSM, but it does not yet support flooding. See the [Feature list](#features.md) for details.

I have tagged the version that I used for the first round of ZTP interoperability testing with version tag ztp-interop-1. 

@@@ Do this and provide link

You can checkout this specific version of code using the following git command:

<pre>
$ <b>git clone https://github.com/brunorijsman/rift-python.git</b>
...
$ <b>git checkout ztp-interop-1</b>
...
</pre>


## Why Preliminary?

This is a _preliminary_ ZTP interoperability testing report, not yet the final report.

I have already put a framework in place for fully automated interoperability testing. There is already a good number of automated tests for the LIE FSM, and there are a few initial automated tests for the ZTP FSM. However, more automated tests for the ZTP FSM are needed.

Even though the ZTP FSM tests cases are not complete yet, I decided to provide an interim update for a number of reasons. 

* First, we have already discovered a number of issues, which I wanted to socialize. 
* Second, I have put in place a rich framework for automated interop testing which I wanted to publisize, just in case other open source contributors are included to help by writing additional test cases.
* Third, I wanted to get these results out before I go on a long 3-week hike in the Canadian Rockies (during which time I will not be reachable). I will pick up the work when I return.

## Testing Framework

In this round of testing I spent a lot of effort to fully automate all testing: unit testing, system testing, and interoperability testing.

### Unit Tests

The unit tests use [pytest](https://docs.pytest.org/en/latest/) to test an individual Python class or a small group or related Python classes.

See @@@ for more details on the unit tests.

### System Tests

The system tests create a topology of multiple RIFT nodes, and use [Python Expect](https://pexpect.readthedocs.io/en/stable/) in combination with pytest to verify whether all nodes in the topology behave as expected using the following mechanisms:

* Use *show* commands in the Command Line Interface (CLI) session to observe the state of the system (nodes, interfaces, etc.) after initial convergence and after some event (e.g. a link failure) occurred. The *show* commands in RIFT-Python provide extremely detailed output specifically for the purpose of enabling automated testing.

* Use *set* commands in the Command Line Interface (CLI) session to perform actions such as simulating a uni-directional or bi-directional link failure.

* Analyze the logs to determine whether various events (e.g. finite state machine transitions) occurred when they were expected to occur. The debug-level RIFT-Python logging is very detailed and very structured specifically for the purpose of enabling automated testing. 

The [tests directory in RIFT-Python](https://github.com/brunorijsman/rift-python/tree/master/tests) contains two helper modules (rift\_expect\_session.py and log\_expect\_session) to ease the task of writing automated tests.

See @@@ for more details on the system tests.

### Interoperability Tests

The interoperability tests build upon the system tests. The interoperability tests run the exact same topologies and test cases as in the system tests, except that one or more rift-python nodes are replaced by rift-juniper nodes.

For detailed instructions on how to run the interoperability tests see @@@.

See @@@ for more details on the interoperability tests.

### Log Visualization Tool

@@@

### Continuous Integration

I use [Travis Continuous Integration (CI)](https://travis-ci.org/brunorijsman/rift-python) For every commit, Travis CI automatically runs pylint, the full unit test suite, and the full system test suite. The interoperability test suite is not automatically run - it must be run manually.

I use [codecov](https://codecov.io/gh/brunorijsman/rift-python) for visualizing the code coverage results.

See [Continuous Integration](continuous-integration.md) for more details.


## Documented Results

The results of the ZTP interoperability testing have been documented in the following places:

### RIFT Draft Comments Living Document

The [RIFT Draft Comments Living Document](http://bit.ly/rift-comments) is a document on Google docs that I have been using to document all issues that I find in the RIFT specifications.

If you only want to look at a single document to see all the discovered issues and their resolutions, this is the place to look.

It is a living document in the sense that I edit it each time I find a new issue, and the specification authors (specifically Tony) also edit it with their responses to document whether or not they agree with the comment, and if so, what corresponding change was made in the specification.

Prior to the ZTP FSM testing, this document already contained all issues discovered during the LIE FSM testing, along with Tony's responses to those comments.

I have now updated the document to add the issues discovered during the ZTP FSM interop testing. Look for the section that starts with "ADDITIONAL COMMENTS AFTER ZTP FSM IMPLEMENTATION AND INTEROP TESTING."

As mentioned in the introduction, some of the comments are very nit-picky, bordering on the pedantic. I included them anyway.

### RIFT Mailing List

A few issues were discussed in detail on the RIFT mailing list:

* [Clarify that 2 non-leaf neighbor nodes with hard-configured levels should accept each other's offers but not establish a 3-way adjacency.](https://mailarchive.ietf.org/arch/msg/rift/xUmagBLsuykIewmnlN-y4nls5JE)

* [More than 2 RIFT neighbors on a LAN causes a storm of LIE messages.](https://mailarchive.ietf.org/arch/msg/rift/k0_nvTMdxHlFQe2PEwevdsA_tSI)

* [Clarify the expected value of the not_a_ztp_offer flag for a sending RIFT node.](https://mailarchive.ietf.org/arch/browse/rift/?index=LgJcv-_JFK5Ixho79Mjwm_vtYD8&gbt=1)

### Github Issues

One issue was discussed in detail as an issue in the RIFT-Python github repository:

* [A discussion on the correct ordering of events: chained events versus external events](http://bit.ly/rift-python-chained-event-issue)

### Github Deviations

Whenever I made a conscious decission to implement the RIFT-Python code in a way that does not comply with the letter of the RIFT specification, I documented a so-called "deviation" in the [deviations document](http://bit.ly/rift-python-deviations).

Each deviation is numbered (DEV-1, DEV-2, etc.) and corresponding comments in the RIFT-Python code have comments with this number to point out where the deviations are in the code.

### RIFT Technical Calls

All of the above issues that were discussed on the RIFT mailing list were also discussed in the weekly RIFT technical conference call.

I mention this because the conclusions during the call have not always made it back to the mailing list.

Specifically, we agreed to solve the LIE message storm by introducing an new explicit MultipleNeighbor state in the LIE FSM. We also agreed to continue to hold the position that multipoints LANs is a non-requirement for RIFT (there was some dicussion on whether that is really true for containters inside a server).





