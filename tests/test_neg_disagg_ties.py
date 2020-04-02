from rift_expect_session import RiftExpectSession
from common.constants import infinite_distance

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

def test_neg_disagg_ties():
    # Disable debug logging for large topologies such as multiple (it makes convergence too slow)
    res = RiftExpectSession("multiplane", start_converge_secs=20.0, reconverge_secs=30.0,
                            log_debug=False)
    # Break spine_1_1_1 interfaces connected to ToFs to reach a fallen leaf situation
    res.interface_failure(node="spine_1_1_1", interface="if2", failure="failed")
    res.interface_failure(node="spine_1_1_1", interface="if3", failure="failed")
    # Both ToFs of plane 1 should store neg disagg TIE
    check_neg_tie_in_tof(res)
    # Spines should store the neg disagg TIE
    check_neg_tie_in_spines(res)
    # Neg disagg TIE should be also propagated from spine to leafs
    check_neg_tie_in_leafs(res)
    res.stop()
