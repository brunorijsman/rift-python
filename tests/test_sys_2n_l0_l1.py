from rift_expect_session import RiftExpectSession

def test_basic():
    res = RiftExpectSession("2n_l0_l1")
    # A very basic test for now: expect 3-way adjacency
    res.sendline("show interfaces")
    res.expect("| if1 +| node2-if1 +| 2 +| THREE_WAY +|")
    res.stop()
