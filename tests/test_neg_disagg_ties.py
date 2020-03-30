from rift_expect_session import RiftExpectSession
from common.constants import infinite_distance

# pylint: disable=line-too-long
# pylint: disable=bad-continuation


def check_neg_tie_in_tof(res):
    res.check_tie_in_db("tof_1_2_1",
                        patterns=[
                            r"| South | 121 | Neg-Dis-Prefix | .* | .* | .* | Neg-Dis-Prefix: 200.0.0.0/24 |",
                            r"|       |     |                |    |    |    |   Metric: %d         |" % infinite_distance,
                            r"|       |     |                |    |    |    | Neg-Dis-Prefix: 200.0.1.0/24 |",
                            r"|       |     |                |    |    |    |   Metric: %d         |" % infinite_distance,
                        ])

    res.check_tie_in_db("tof_1_2_2",
                        patterns=[
                            r"| South | 122 | Neg-Dis-Prefix | .* | .* | .* | Neg-Dis-Prefix: 200.0.0.0/24 |",
                            r"|       |     |                |    |    |    |   Metric: %d         |" % infinite_distance,
                            r"|       |     |                |    |    |    | Neg-Dis-Prefix: 200.0.1.0/24 |",
                            r"|       |     |                |    |    |    |   Metric: %d         |" % infinite_distance,
                        ])


def check_neg_tie_in_spines(res):
    for pod_n in range(2, 5):
        res.check_tie_in_db("spine_%d_1_1" % pod_n,
                            patterns=[
                                r"| South | 121 | Neg-Dis-Prefix | .* | .* | .* | Neg-Dis-Prefix: 200.0.0.0/24 |",
                                r"|       |     |                |    |    |    |   Metric: %d         |" % infinite_distance,
                                r"|       |     |                |    |    |    | Neg-Dis-Prefix: 200.0.1.0/24 |",
                                r"|       |     |                |    |    |    |   Metric: %d         |" % infinite_distance,
                                r"| South | 122 | Neg-Dis-Prefix | .* | .* | .* | Neg-Dis-Prefix: 200.0.0.0/24 |",
                                r"|       |     |                |    |    |    |   Metric: %d         |" % infinite_distance,
                                r"|       |     |                |    |    |    | Neg-Dis-Prefix: 200.0.1.0/24 |",
                                r"|       |     |                |    |    |    |   Metric: %d         |" % infinite_distance,
                            ])


def check_neg_tie_in_leafs(res):
    for pod_n in range(2, 5):
        for leaf_n in range(1, 3):
            res.check_tie_in_db("leaf_%d_0_%d" % (pod_n, leaf_n),
                                patterns=[
                                    r"| South | %d11 | Neg-Dis-Prefix | .* | .* | .* | Neg-Dis-Prefix: 200.0.0.0/24 |" % pod_n,
                                    r"|       |     |                |    |    |    |   Metric: %d         |" % infinite_distance,
                                    r"|       |     |                |    |    |    | Neg-Dis-Prefix: 200.0.1.0/24 |",
                                    r"|       |     |                |    |    |    |   Metric: %d         |" % infinite_distance,
                                ])


def test_neg_disagg_ties():
    res = RiftExpectSession("multiplane", reconvergence_secs=20.0)

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
