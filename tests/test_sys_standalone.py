# System test: test_sys_standalone
#
# Test running RIFT in standalone mode, i.e. without any topology file.

from rift_expect_session import RiftExpectSession

def check_show_node(res):
    res.sendline("show node")
    res.table_expect("Node:")
    res.table_expect("| Configured Level | undefined |")
    res.table_expect("Sent Offers:")
    res.table_expect("| .* | .* | None | False | ONE_WAY |")
    res.wait_prompt()

def check_show_nodes(res):
    res.sendline("show nodes")
    res.table_expect("| .* | .* | True |")
    res.wait_prompt()

def test_standalone():
    res = RiftExpectSession()
    check_show_node(res)
    check_show_nodes(res)
    res.stop()
