from rift_expect_session import RiftExpectSession


# pylint: disable=line-too-long
# pylint: disable=bad-continuation

def check_neg_tie_in_tof(res):
    res.check_tie_in_db("tof_1_2_1",
                        patterns=[
                            r"| South | 121 | Neg-Dis-Prefix | .* | .* | .* | Neg-Dis-Prefix: 200.0.0.0/24 |",
                            r"|       |     |                |    |    |    |   Metric: 4                  |",
                            r"|       |     |                |    |    |    | Neg-Dis-Prefix: 200.0.1.0/24 |",
                            r"|       |     |                |    |    |    |   Metric: 4                  |",
                        ])

    res.check_tie_in_db("tof_1_2_2",
                        patterns=[
                            r"| South | 122 | Neg-Dis-Prefix | .* | .* | .* | Neg-Dis-Prefix: 200.0.0.0/24 |",
                            r"|       |     |                |    |    |    |   Metric: 4                  |",
                            r"|       |     |                |    |    |    | Neg-Dis-Prefix: 200.0.1.0/24 |",
                            r"|       |     |                |    |    |    |   Metric: 4                  |",
                        ])


def check_neg_tie_in_spines(res):
    for spine_n in range(2, 5):
        res.check_tie_in_db("spine_%d_1_1" % spine_n,
                            patterns=[
                                r"| South | 121 | Neg-Dis-Prefix | .* | .* | .* | Neg-Dis-Prefix: 200.0.0.0/24 |",
                                r"|       |     |                |    |    |    |   Metric: 4                  |",
                                r"|       |     |                |    |    |    | Neg-Dis-Prefix: 200.0.1.0/24 |",
                                r"|       |     |                |    |    |    |   Metric: 4                  |",
                                r"| South | 122 | Neg-Dis-Prefix | .* | .* | .* | Neg-Dis-Prefix: 200.0.0.0/24 |",
                                r"|       |     |                |    |    |    |   Metric: 4                  |",
                                r"|       |     |                |    |    |    | Neg-Dis-Prefix: 200.0.1.0/24 |",
                                r"|       |     |                |    |    |    |   Metric: 4                  |",
                            ])


def test_neg_disagg_ties():
    res = RiftExpectSession("multiplane", reconvergence_secs=20.0)

    # Break spine_1_1_1 interfaces connected to ToFs to reach a fallen leaf situation
    res.interface_failure(node="spine_1_1_1", interface="if2", failure="failed")
    res.interface_failure(node="spine_1_1_1", interface="if3", failure="failed")

    check_neg_tie_in_tof(res)

    check_neg_tie_in_spines(res)

    res.stop()
