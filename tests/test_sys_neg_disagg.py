from common.constants import infinite_distance
from rift_expect_session import RiftExpectSession


def check_ew_absence_in_south_spf(res):
    # E-W neighbor of tof_1_2_1 -> tof_1_2_2
    res.check_spf_absent(node="tof_1_2_1", direction="south", destination="122")
    # E-W neighbor of tof_2_2_1 -> tof_2_2_2
    res.check_spf_absent(node="tof_2_2_1", direction="south", destination="222")


def check_ew_in_special_spf(res):
    res.check_spf(node="tof_1_2_1",
                  expect_south_ew_spf=[r"| 221 \(tof_2_2_1\) | 1 | False | 121 | .* | if4"])
    res.check_spf(node="tof_1_2_2",
                  expect_south_ew_spf=[r"| 222 \(tof_2_2_2\) | 1 | False | 122 | .* | if4"])


def check_fall_leafs_s_spf(res):
    res.check_spf_absent(node="tof_1_2_1", direction="south", destination="101")
    res.check_spf_absent(node="tof_1_2_1", direction="south", destination="102")
    res.check_spf_absent(node="tof_1_2_2", direction="south", destination="101")
    res.check_spf_absent(node="tof_1_2_2", direction="south", destination="102")


def check_fall_leafs_sp_spf(res):
    res.check_spf(node="tof_1_2_1",
                  expect_south_ew_spf=[r"| 101 \(leaf_1_0_1\) | 3 | True | 112 | .* | if4"])
    res.check_spf(node="tof_1_2_1",
                  expect_south_ew_spf=[r"| 102 \(leaf_1_0_2\) | 3 | True | 112 | .* | if4"])
    res.check_spf(node="tof_1_2_2",
                  expect_south_ew_spf=[r"| 101 \(leaf_1_0_1\) | 3 | True | 112 | .* | if4"])
    res.check_spf(node="tof_1_2_2",
                  expect_south_ew_spf=[r"| 102 \(leaf_1_0_2\) | 3 | True | 112 | .* | if4"])


def check_spine_positive_next_hops(res):
    for node in ["spine_2_1_1", "spine_3_1_1", "spine_4_1_1"]:
        for prefix in ["200.0.0.0/24", "200.0.1.0/24"]:
            res.check_spf_disagg(node,
                                 prefix,
                                 cost=4,
                                 is_leaf=False,
                                 pos_or_neg="Positive",
                                 preds_and_nhs=[("122", "if3")])


def check_spine_negative_disagg_spf(res):
    for node in ["spine_2_1_1", "spine_3_1_1", "spine_4_1_1"]:
        for prefix in ["200.0.0.0/24", "200.0.1.0/24"]:
            res.check_spf_disagg(node,
                                 prefix,
                                 cost=infinite_distance,
                                 is_leaf=False,
                                 pos_or_neg="Negative",
                                 preds_and_nhs=[("121", "if2"), ("122", "if3")])


def check_leaf_negative_next_hops(res):
    for (node, pred) in [("leaf_2_0_1", 211), ("leaf_2_0_2", 211),
                         ("leaf_3_0_1", 311), ("leaf_3_0_2", 311),
                         ("leaf_4_0_1", 411), ("leaf_4_0_2", 411)]:
        for prefix in ["200.0.0.0/24", "200.0.1.0/24"]:
            res.check_spf_disagg(node,
                                 prefix,
                                 cost=infinite_distance,
                                 is_leaf=False,
                                 pos_or_neg="Negative",
                                 preds_and_nhs=[(pred, "if0")])

def check_neg_tie_in_tof(res):
    patterns = [
        r"| South | 121 | Neg-Dis-Prefix | .* | .* | .* | Neg-Dis-Prefix: 200.0.0.0/24 |",
        r"| | | | | | |   Metric: %d |" % infinite_distance,
        r"| | | | | | | Neg-Dis-Prefix: 200.0.1.0/24 |",
        r"| | | | | | |   Metric: %d |" % infinite_distance]
    res.check_tie_in_db("tof_1_2_1", "south", "121", "neg-dis-prefix", patterns)
    patterns = [
        r"| South | 122 | Neg-Dis-Prefix | .* | .* | .* | Neg-Dis-Prefix: 200.0.0.0/24 |",
        r"| | | | | | |   Metric: %d |" % infinite_distance,
        r"| | | | | | | Neg-Dis-Prefix: 200.0.1.0/24 |",
        r"| | | | | | |   Metric: %d |" % infinite_distance]
    res.check_tie_in_db("tof_1_2_2", "south", "122", "neg-dis-prefix", patterns)


def check_neg_tie_in_spines(res):
    for pod_n in range(2, 5):
        node = "spine_%d_1_1" % pod_n
        patterns = [
            r"| South | 121 | Neg-Dis-Prefix | .* | .* | .* | Neg-Dis-Prefix: 200.0.0.0/24 |",
            r"| | | | | | |   Metric: %d |" % infinite_distance,
            r"| | | | | | | Neg-Dis-Prefix: 200.0.1.0/24 |",
            r"| | | | | | |   Metric: %d |" % infinite_distance]
        res.check_tie_in_db(node, "south", "121", "neg-dis-prefix", patterns)
        patterns = [
            r"| South | 122 | Neg-Dis-Prefix | .* | .* | .* | Neg-Dis-Prefix: 200.0.0.0/24 |",
            r"| | | | | | |   Metric: %d |" % infinite_distance,
            r"| | | | | | | Neg-Dis-Prefix: 200.0.1.0/24 |",
            r"| | | | | | |   Metric: %d |" % infinite_distance]
        res.check_tie_in_db(node, "south", "122", "neg-dis-prefix", patterns)


def check_neg_tie_in_leafs(res):
    for pod_n in range(2, 5):
        originator = "%d11" % pod_n
        patterns = [
            r"| South | %s | Neg-Dis-Prefix | .* | .* | .* | Neg-Dis-Prefix: 200.0.0.0/24 |" \
            % originator,
            r"| | | | | | |   Metric: %d |" % infinite_distance,
            r"| | | | | | | Neg-Dis-Prefix: 200.0.1.0/24 |",
            r"| | | | | | |   Metric: %d |" % infinite_distance]
        for leaf_n in range(1, 3):
            node = "leaf_%d_0_%d" % (pod_n, leaf_n)
            res.check_tie_in_db(node, "south", originator, "neg-dis-prefix", patterns)


def test__large__neg_disagg():
    # __large__  means: don't run this test in a constrained environment (e.g. a small laptop)

    # Disable debug logging for large topologies such as multiple (it makes convergence too slow)
    res = RiftExpectSession("multiplane", start_converge_secs=45.0, reconverge_secs=20.0,
                            log_debug=False)

    # E-W neighbors should not be present in south SPF
    check_ew_absence_in_south_spf(res)

    # E-W neighbors must be present in special SPF
    check_ew_in_special_spf(res)

    # Break spine_1_1_1 interfaces connected to tof_1_2_1 (so a next hop should be removed from SPF)
    res.interface_failure(node="spine_1_1_1", interface="if2", failure="failed")

    # Check that spines lost a positive next hop for the negative disaggregated prefixes
    check_spine_positive_next_hops(res)

    # Break last spine_1_1_1 interface to reach a fallen leaf situation with first ToF plane
    res.interface_failure(node="spine_1_1_1", interface="if3", failure="failed")

    # Check that leaf_1_0_1 and leaf_1_0_2 are not reachable with south SPF of tof_1_1_1 and
    # tof_1_2_2
    check_fall_leafs_s_spf(res)

    # Check that leaf_1_0_1 and leaf_1_0_2 are reachable using special SPF of tof_1_1_1 and
    # tof_1_2_2
    check_fall_leafs_sp_spf(res)

    # Check that each spine loses all the positive next hops for the negative disaggregated prefixes
    # and computes only negative next hops
    check_spine_negative_disagg_spf(res)

    # Check that each leaf computed a negative next hops for the negative disaggregated prefixes
    check_leaf_negative_next_hops(res)

    # Both ToFs of plane 1 should store neg disagg TIE
    check_neg_tie_in_tof(res)

    # Spines should store the neg disagg TIE
    check_neg_tie_in_spines(res)

    # Neg disagg TIE should be also propagated from spine to leafs
    check_neg_tie_in_leafs(res)

    res.stop()
