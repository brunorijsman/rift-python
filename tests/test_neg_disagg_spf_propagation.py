from common.constants import infinite_distance
from rift_expect_session import RiftExpectSession


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
                      r"| 200.0.0.0/24 \(Disagg\) | %d | 121 | | Negative | if2 .* | if2 .* |\s+"
                      r"| | | 122 | | | if3 .* | if3 .* |" % infinite_distance
                  ])
    res.check_spf(node="spine_2_1_1",
                  expect_north_spf=[
                      r"| 200.0.1.0/24 \(Disagg\) | %d | 121 | | Negative | if2 .* | if2 .* |\s+"
                      r"| | | 122 | | | if3 .* | if3 .* |" % infinite_distance
                  ])
    res.check_spf(node="spine_3_1_1",
                  expect_north_spf=[
                      r"| 200.0.0.0/24 \(Disagg\) | %d | 121 | | Negative | if2 .* | if2 .* |\s+"
                      r"| | | 122 | | | if3 .* | if3 .* |" % infinite_distance
                  ])
    res.check_spf(node="spine_3_1_1",
                  expect_north_spf=[
                      r"| 200.0.1.0/24 \(Disagg\) | %d | 121 | | Negative | if2 .* | if2 .* |\s+"
                      r"| | | 122 | | | if3 .* | if3 .* |" % infinite_distance
                  ])
    res.check_spf(node="spine_4_1_1",
                  expect_north_spf=[
                      r"| 200.0.0.0/24 \(Disagg\) | %d | 121 | | Negative | if2 .* | if2 .* |\s+"
                      r"| | | 122 | | | if3 .* | if3 .* |" % infinite_distance
                  ])
    res.check_spf(node="spine_4_1_1",
                  expect_north_spf=[
                      r"| 200.0.1.0/24 \(Disagg\) | %d | 121 | | Negative | if2 .* | if2 .* |\s+"
                      r"| | | 122 | | | if3 .* | if3 .* |" % infinite_distance
                  ])

def check_leaf_negative_next_hops(res):
    res.check_spf(node="leaf_2_0_1",
                  expect_north_spf=[
                      r"| 200.0.0.0/24 \(Disagg\) | %d | 211 | | Negative | if0 .* | if0 .* |" % infinite_distance])
    res.check_spf(node="leaf_2_0_1",
                  expect_north_spf=[
                      r"| 200.0.1.0/24 \(Disagg\) | %d | 211 | | Negative | if0 .* | if0 .* |" % infinite_distance])
    res.check_spf(node="leaf_2_0_2",
                  expect_north_spf=[
                      r"| 200.0.0.0/24 \(Disagg\) | %d | 211 | | Negative | if0 .* | if0 .* |" % infinite_distance])
    res.check_spf(node="leaf_2_0_2",
                  expect_north_spf=[
                      r"| 200.0.1.0/24 \(Disagg\) | %d | 211 | | Negative | if0 .* | if0 .* |" % infinite_distance])
    res.check_spf(node="leaf_3_0_1",
                  expect_north_spf=[
                      r"| 200.0.0.0/24 \(Disagg\) | %d | 311 | | Negative | if0 .* | if0 .* |" % infinite_distance])
    res.check_spf(node="leaf_3_0_1",
                  expect_north_spf=[
                      r"| 200.0.1.0/24 \(Disagg\) | %d | 311 | | Negative | if0 .* | if0 .* |" % infinite_distance])
    res.check_spf(node="leaf_3_0_2",
                  expect_north_spf=[
                      r"| 200.0.0.0/24 \(Disagg\) | %d | 311 | | Negative | if0 .* | if0 .* |" % infinite_distance])
    res.check_spf(node="leaf_3_0_2",
                  expect_north_spf=[
                      r"| 200.0.1.0/24 \(Disagg\) | %d | 311 | | Negative | if0 .* | if0 .* |" % infinite_distance])
    res.check_spf(node="leaf_4_0_1",
                  expect_north_spf=[
                      r"| 200.0.0.0/24 \(Disagg\) | %d | 411 | | Negative | if0 .* | if0 .* |" % infinite_distance])
    res.check_spf(node="leaf_4_0_1",
                  expect_north_spf=[
                      r"| 200.0.1.0/24 \(Disagg\) | %d | 411 | | Negative | if0 .* | if0 .* |" % infinite_distance])
    res.check_spf(node="leaf_4_0_2",
                  expect_north_spf=[
                      r"| 200.0.0.0/24 \(Disagg\) | %d | 411 | | Negative | if0 .* | if0 .* |" % infinite_distance])
    res.check_spf(node="leaf_4_0_2",
                  expect_north_spf=[
                      r"| 200.0.1.0/24 \(Disagg\) | %d | 411 | | Negative | if0 .* | if0 .* |" % infinite_distance])


def test_neg_disagg_spf_propagation():
    # Disable debug logging for large topologies such as multiple (it makes convergence too slow)
    res = RiftExpectSession("multiplane", start_converge_secs=45.0, reconverge_secs=30.0,
                            log_debug=False)

    # Break spine_1_1_1 interfaces connected to tof_1_2_1 (so a next hop should be removed from SPF)
    res.interface_failure(node="spine_1_1_1", interface="if2", failure="failed")

    # Check that spines lost a positive next hop for the negative disaggregated prefixes
    check_spine_positive_next_hops(res)

    # Break last spine_1_1_1 interface to reach a fallen leaf situation with first ToF plane
    res.interface_failure(node="spine_1_1_1", interface="if3", failure="failed")

    # Check that each spine loses all the positive next hops for the negative disaggregated prefixes
    # and computes only negative next hops
    check_spine_negative_disagg_spf(res)

    # Check that each leaf computed a negative next hops for the negative disaggregated prefixes
    check_leaf_negative_next_hops(res)

    res.stop()
