from rift_expect_session import RiftExpectSession


def check_ew_absence_in_south_spf(res):
    # E-W neighbor of tof_1_2_1 -> tof_1_2_2
    res.check_spf_absent(node="tof_1_2_1", direction="south-with-ew", destination="122")
    # E-W neighbor of tof_2_2_1 -> tof_2_2_2
    res.check_spf_absent(node="tof_2_2_1", direction="south-with-ew", destination="222")


def check_ew_in_special_spf(res):
    res.check_spf(node="tof_1_2_1",
                  expect_south_ew_spf=[r"| 221 \(tof_2_2_1\) | 1 | 121 | .* | if4"])
    res.check_spf(node="tof_1_2_2",
                  expect_south_ew_spf=[r"| 222 \(tof_2_2_2\) | 1 | 122 | .* | if4"])


def check_fall_leafs_s_spf(res):
    res.check_spf_absent(node="tof_1_2_1", direction="south-with-ew", destination="101")
    res.check_spf_absent(node="tof_1_2_1", direction="south-with-ew", destination="102")
    res.check_spf_absent(node="tof_1_2_2", direction="south-with-ew", destination="101")
    res.check_spf_absent(node="tof_1_2_2", direction="south-with-ew", destination="102")


def check_fall_leafs_sp_spf(res):
    res.check_spf(node="tof_1_2_1",
                  expect_south_ew_spf=[r"| 101 \(leaf_1_0_1\) | 3 | 112 | .* | if4"])
    res.check_spf(node="tof_1_2_1",
                  expect_south_ew_spf=[r"| 102 \(leaf_1_0_2\) | 3 | 112 | .* | if4"])
    res.check_spf(node="tof_1_2_2",
                  expect_south_ew_spf=[r"| 101 \(leaf_1_0_1\) | 3 | 112 | .* | if4"])
    res.check_spf(node="tof_1_2_2",
                  expect_south_ew_spf=[r"| 102 \(leaf_1_0_2\) | 3 | 112 | .* | if4"])


def test_neg_disagg_spf():
    res = RiftExpectSession("multiplane", reconvergence_secs=15.0, expect_timeout=10.0)

    # E-W neighbors should not be present in south SPF
    check_ew_absence_in_south_spf(res)
    # E-W neighbors must be present in special SPF
    check_ew_in_special_spf(res)

    # Break spine_1_1_1 interfaces connected to ToFs to reach a fallen leaf situation
    res.interface_failure(node="spine_1_1_1", interface="if2", failure="failed")
    res.interface_failure(node="spine_1_1_1", interface="if3", failure="failed")

    # Check that leaf_1_0_1 and leaf_1_0_2 are not reachable
    # with south SPF of tof_1_1_1 and tof_1_2_2
    check_fall_leafs_s_spf(res)

    # Check that leaf_1_0_1 and leaf_1_0_2 are reachable
    # using special SPF of tof_1_1_1 and tof_1_2_2
    check_fall_leafs_sp_spf(res)

    res.stop()
