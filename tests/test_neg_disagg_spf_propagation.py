from rift_expect_session import RiftExpectSession
from common.constants import infinite_distance


def check_spine_positive_next_hops(res):
    res.check_spf(node="spine_2_1_1",
                  expect_north_spf=[r"| 200.0.0.0/24 \(Disagg\) | 4 | 122 | | Positive | if3 .* | if3 .* |"])
    res.check_spf(node="spine_2_1_1",
                  expect_north_spf=[r"| 200.0.1.0/24 \(Disagg\) | 4 | 122 | | Positive | if3 .* | if3 .* |"])
    res.check_spf(node="spine_3_1_1",
                  expect_north_spf=[r"| 200.0.0.0/24 \(Disagg\) | 4 | 122 | | Positive | if3 .* | if3 .* |"])
    res.check_spf(node="spine_3_1_1",
                  expect_north_spf=[r"| 200.0.1.0/24 \(Disagg\) | 4 | 122 | | Positive | if3 .* | if3 .* |"])
    res.check_spf(node="spine_4_1_1",
                  expect_north_spf=[r"| 200.0.0.0/24 \(Disagg\) | 4 | 122 | | Positive | if3 .* | if3 .* |"])
    res.check_spf(node="spine_4_1_1",
                  expect_north_spf=[r"| 200.0.1.0/24 \(Disagg\) | 4 | 122 | | Positive | if3 .* | if3 .* |"])


def check_spine_negative_disagg_spf(res):
    res.check_spf(node="spine_2_1_1",
                  expect_north_spf=[
                      r"| 200.0.0.0/24 \(Disagg\) | %d | 121 | | Negative | if2 .* | if2 .* |" % infinite_distance
                  ])
    res.check_spf(node="spine_2_1_1", expect_north_spf=[r"| | | 122 | | | if3 .* | if3 .* |"])
    res.check_spf(node="spine_2_1_1",
                  expect_north_spf=[
                      r"| 200.0.1.0/24 \(Disagg\) | %d | 121 | | Negative | if2 .* | if2 .* |" % infinite_distance
                  ])
    res.check_spf(node="spine_2_1_1", expect_north_spf=[r"| | | 122 | | | if3 .* | if3 .* |"])
    res.check_spf(node="spine_3_1_1",
                  expect_north_spf=[
                      r"| 200.0.0.0/24 \(Disagg\) | %d | 121 | | Negative | if2 .* | if2 .* |" % infinite_distance
                  ])
    res.check_spf(node="spine_3_1_1", expect_north_spf=[r"| | | 122 | | | if3 .* | if3 .* |"])
    res.check_spf(node="spine_3_1_1",
                  expect_north_spf=[
                      r"| 200.0.1.0/24 \(Disagg\) | %d | 121 | | Negative | if2 .* | if2 .* |" % infinite_distance
                  ])
    res.check_spf(node="spine_3_1_1", expect_north_spf=[r"| | | 122 | | | if3 .* | if3 .* |"])
    res.check_spf(node="spine_4_1_1",
                  expect_north_spf=[
                      r"| 200.0.0.0/24 \(Disagg\) | %d | 121 | | Negative | if2 .* | if2 .* |" % infinite_distance
                  ])
    res.check_spf(node="spine_4_1_1", expect_north_spf=[r"| | | 122 | | | if3 .* | if3 .* |"])
    res.check_spf(node="spine_4_1_1",
                  expect_north_spf=[
                      r"| 200.0.1.0/24 \(Disagg\) | %d | 121 | | Negative | if2 .* | if2 .* |" % infinite_distance
                  ])
    res.check_spf(node="spine_4_1_1", expect_north_spf=[r"| | | 122 | | | if3 .* | if3 .* |"])


def test_neg_disagg_spf_propagation():
    # Disable debug logging for large topologies such as multiple (it makes convergence too slow)
    res = RiftExpectSession("multiplane", start_converge_secs=45.0, reconverge_secs=30.0,
                            log_debug=False)

    # Break spine_1_1_1 interfaces connected to tof_1_2_1 (so a next hop should be removed from SPF)
    res.interface_failure(node="spine_1_1_1", interface="if2", failure="failed")

    # Check that spines lost a next hop
    check_spine_positive_next_hops(res)

    # Break last spine_1_1_1 interface to reach a fallen leaf situation with first ToF plane
    res.interface_failure(node="spine_1_1_1", interface="if3", failure="failed")

    # Check that leaf_1_0_1 and leaf_1_0_2 are not reachable
    # with south SPF of tof_1_1_1 and tof_1_2_2
    check_spine_negative_disagg_spf(res)

    #
    # # Check that leaf_1_0_1 and leaf_1_0_2 are reachable
    # # using special SPF of tof_1_1_1 and tof_1_2_2
    # check_fall_leafs_sp_spf(res)

    res.stop()
