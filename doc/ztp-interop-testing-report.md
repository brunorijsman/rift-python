# Routing In Fat Trees (RIFT) Zero Touch Provisioning (ZTP) Preliminary Interoperability Testing Report

## Summary

This document reports the preliminary results for interoperability testing of the Zero Touch Provisioning (ZTP) Finite State Machine (FSM) between the open source Python RIFT implementation and the Juniper RIFT implementation.

So far, no major interoperability issues have been found: the two implementations could successfully auto-discover level values and establish 3-way adjacencies.

Here is the output from the automated interoperability testing suite running between RIFT-Python and RIFT-Juniper:

<pre>
(env) $ <b>tests/interop.py</b>
2n_l0_l1-node1... Pass
2n_l0_l1-node2... Pass
2n_l0_l2-node1... Pass
2n_l0_l2-node2... Pass
2n_l1_l3-node1... Pass
2n_l1_l3-node2... Pass
3n_l0_l1_l2-node1... Pass
3n_l0_l1_l2-node2... Pass
3n_l0_l1_l2-node3... Pass
3n_l0_l1_l2-node1-node2... Pass
3n_l0_l1_l2-node2-node3... Pass
3n_l0_l1_l2-node1-node3... Pass
2n_un_l1-node1... Pass
2n_un_l1-node2... Pass
</pre>

The meaning of this output is explained in detail in the [Automated Testing Framework documentation](automated-testing.md)

Some minor issues were discovered during the interoperability testing, all of which have been resolved after discussions on the RIFT mailing list and/or direct emails to the RIFT authors and/or discussions during the RIFT weekly technical conference call.

All discovered issues have been documented in the [RIFT Draft Comments Living Document on Google Docs](http://bit.ly/rift-comments). This is the one document to read if you want to see a complete list of all issues that were found during interoperability testing (not just ZTP FSM interop testing, but also LIE FSM interop testing). It also contains the responses to those issues from the specification authors.

The most important issues have also been discussed in great detail on the [RIFT mailing list](http://bit.ly/rift-mailing-list) and/or the [RIFT-Python Github issues list](http://bit.ly/rift-python-issues-list) and/or the RIFT weekly technical conference calls.

A few of the discovered issue will require non-trivial changes to the protocol (e.g. the introduction of a distinct MultipleNeighbors state). The vast majority of discovered issues only require clarifications in the text of the specification. I will be the first to admit that some of the comments border on the pedantic.

The ZTP FSM testing is not yet complete: far more test cases for more complex scenarios are needed. This report will be updated when those test cases have been implemented and executed.

## Introduction

This is a follow-up on the first round of interoperability testing between this RIFT implementation ("RIFT-Python") and Juniper's RIFT implementation ("RIFT-Juniper").

The first routing of interoperability testing was done at the IETF 102 Hackathon in Montreal; there we tested the Link Information Element (LIE) Finite State Machine (FSM) and verified that the two
implementations could successfully establish a 3-way adjacency.

See the [IETF 102 Hackathon Interop Testing Report](../ietf-102/ietf-102-rift-hackathon-detailed-report.md) for a detailed report on the results of the first round of interop testing.

In this second round of interoperability testing I tested the Zero Touch Provisioning (ZTP) mechanism, which is also referred to as "automatic level derivation" or the "level determination procedure" in the specification.

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

I have tagged the version that I used for the first round of ZTP interoperability testing with [version tag ztp-interop-1](https://github.com/brunorijsman/rift-python/releases/tag/ztp-interop-1)

You can checkout this specific version of code using the following git command:

<pre>
$ <b>git clone https://github.com/brunorijsman/rift-python.git</b>
...
$ <b>git checkout ztp-interop-1</b>
...
</pre>

## Testing Framework

In this round of testing I spent a lot of effort to fully automate all testing: unit testing, system testing, and interoperability testing.

Here I briefly introduce the automated testing framework; see the [Automated Testing Framework](automated-testing.md) documentation for details on how to run the tests and how to diagnose test failures.

### Unit Tests

The unit tests use [pytest](https://docs.pytest.org/en/latest/) to test an individual Python class or a small group or related Python classes.

### System Tests

The system tests create a topology of multiple RIFT nodes, and use [Python Expect](https://pexpect.readthedocs.io/en/stable/) in combination with pytest to verify whether all nodes in the topology behave as expected using the following mechanisms:

* Use *show* commands in the Command Line Interface (CLI) session to observe the state of the system (nodes, interfaces, etc.) after initial convergence and after some event (e.g. a link failure) occurred. The *show* commands in RIFT-Python provide extremely detailed output specifically for the purpose of enabling automated testing.

* Use *set* commands in the Command Line Interface (CLI) session to perform actions such as simulating a uni-directional or bi-directional link failure.

* Analyze the logs to determine whether various events (e.g. finite state machine transitions) occurred when they were expected to occur. The debug-level RIFT-Python logging is very detailed and very structured specifically for the purpose of enabling automated testing. 

The [tests directory in RIFT-Python](https://github.com/brunorijsman/rift-python/tree/master/tests) contains all the test cases as well as two helper modules (`rift_expect_session.py` and `log_expect_session.py`) to ease the task of writing automated tests.

### Interoperability Tests

The interoperability tests build upon the system tests. The interoperability tests run the exact same topologies and test cases as in the system tests, except that one or more RIFT-Python nodes are replaced by RIFT-Juniper nodes.

### Log Visualization Tool

Once you start testing non-trivial topologies, it becomes extremely difficult to read the log files and to undertand what is really happening. The [Log Visualization Tool](log-visualization.md) converts a log file into a graphical ladder diagram, which is _much_ easier to understand.

### Continuous Integration

I use [Travis Continuous Integration (CI)](https://travis-ci.org/brunorijsman/rift-python) For every commit, Travis CI automatically runs pylint, the full unit test suite, and the full system test suite. The interoperability test suite is not automatically run - it must be run manually. I use [codecov](https://codecov.io/gh/brunorijsman/rift-python) for visualizing the code coverage results. See [Continuous Integration](continuous-integration.md) for more details.

## Interoperability Testing Results

All results of the interoperability testing have already been extensively documented and discussed in other places. Rather than duplicate the information here, I will provide pointers to those existing documents:

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

## Why a Preliminary Report?

This is a _preliminary_ ZTP interoperability testing report, not yet the final report.

I have already put a framework in place for fully automated interoperability testing. There is already a good number of automated tests for the LIE FSM, and there are a few initial automated tests for the ZTP FSM. 

That said, the automated ZTP FSM test cases that have been implemented thus far test only the most basic of scenarios; in fact, there are only 2 fully automated scenarios at this time. Many more ZTP test cases are needed including:

* 2 nodes: undefined and level 2
* 2 nodes: undefined and level 0
* 2 nodes: undefined and undefined
* 3 nodes: undefined and undefined and level 99
* 3 nodes: level0 and undefined and level 99
* most realistic Clos topologies
* topologies with PODs
* topologies with miscabling
* etc. etc. etc.

Now that the automated testing framework is in place, it is realitvey straightforward to implement these, and it is my hope that others will contribute.

Even though much more work is needed on the ZTP test cases, I decided to provide an interim update for a number of reasons:

* First, we have already discovered a number of minor issues, which I wanted to socialize as soon as possible.
* Second, I have put in place a rich framework for automated interop testing which I wanted to publicize, so that other open source developers can start to add additional test cases.
* Third, I wanted to get these results out before I go on a long 3-week hike in the Canadian Rockies (during which time I will not be reachable). I will pick up the work when I return.







