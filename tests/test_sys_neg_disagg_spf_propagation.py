
from common.constants import infinite_distance
from rift_expect_session import RiftExpectSession

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
