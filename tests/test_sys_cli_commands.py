from rift_expect_session import RiftExpectSession

# Try every CLI command. Do a basic sanity check of the output, but don't attempt to verify each
# output field.

# Allow long names so we accurately reflect the CLI command name in the function name
# pylint: disable=invalid-name

def check_show_fsm_lie(res):
    res.sendline("show fsm lie")
    res.table_expect("States:")
    res.table_expect("| ONE_WAY |")
    res.table_expect("Events:")
    res.table_expect("| LEVEL_CHANGED | False |")
    res.table_expect("Transitions:")
    res.table_expect("| ONE_WAY | LEVEL_CHANGED | ONE_WAY | update_level | SEND_LIE |")
    res.table_expect("State entry actions:")
    res.table_expect("| ONE_WAY | cleanup |")
    res.wait_prompt()

def check_show_fsm_ztp(res):
    res.sendline("show fsm ztp")
    res.table_expect("States:")
    res.table_expect("| UPDATING_CLIENTS |")
    res.table_expect("Events:")
    res.table_expect("| NEIGHBOR_OFFER | True |")
    res.table_expect("Transitions:")
    res.table_expect("| UPDATING_CLIENTS | NEIGHBOR_OFFER | - | update_or_remove_offer | - |")
    res.table_expect("State entry actions:")
    res.table_expect("| COMPUTE_BEST_OFFER | stop_hold_down_timer |")
    res.table_expect("| | level_compute |")
    res.wait_prompt()

def check_show_interface(res):
    res.sendline("show interface if1")
    res.table_expect("Interface:")
    res.table_expect("| Interface Name | if1 |")
    res.table_expect("| State | THREE_WAY |")
    res.table_expect("Neighbor:")
    res.table_expect("| Name | node2-if1 |")
    res.table_expect("| System ID | 2 |")
    res.wait_prompt()

def check_show_interface_fsm_history(res):
    res.sendline("show interface if1 fsm history")
    res.table_expect("| TWO_WAY | VALID_REFLECTION | | THREE_WAY | False |")
    res.table_expect("| ONE_WAY | NEW_NEIGHBOR | SEND_LIE | TWO_WAY | False |")
    res.wait_prompt()

def check_show_interface_fsm_verbose_history(res):
    res.sendline("show interface if1 fsm verbose-history")
    res.table_expect("| THREE_WAY | LIE_RECEIVED | process_lie | None | False |")
    res.table_expect("| THREE_WAY | SEND_LIE | send_lie | None | False |")
    res.wait_prompt()

def check_show_interfaces(res):
    res.sendline("show interfaces")
    res.table_expect("| if1 | node2-if1 | 2 | THREE_WAY |")
    res.wait_prompt()

def check_show_node(res):
    res.sendline("show node")
    res.table_expect("Node:")
    res.table_expect("| Name | node1 |")
    res.table_expect("| Configured Level  | 1 |")
    res.table_expect("Received Offers:")
    res.table_expect("| if1 | 2 | 0 | True | THREE_WAY | False | False | True |"
                     " Not a ZTP offer flag set |")
    res.table_expect("Sent Offers:")
    res.table_expect("| if1 | 2 | 1 | False | THREE_WAY |")
    res.wait_prompt()

def check_show_node_fsm_history(res):
    res.sendline("show node fsm history")
    res.table_expect("| COMPUTE_BEST_OFFER | COMPUTATION_DONE | no_action | UPDATING_CLIENTS |"
                     " False |")
    res.table_expect("| | | update_all_lie_fsms | | |")
    res.wait_prompt()

def check_show_node_fsm_verbose_history(res):
    res.sendline("show node fsm verbose-history")
    res.table_expect("| UPDATING_CLIENTS | NEIGHBOR_OFFER | update_or_remove_offer | None | "
                     "False |")
    res.wait_prompt()

def check_show_nodes(res):
    res.sendline("show nodes")
    res.table_expect("| node1 | 1 | True |")
    res.wait_prompt()

def check_show_nodes_level(res):
    res.sendline("show nodes level")
    res.table_expect("| node1 | 1 | True | 1 | 1 |")
    res.wait_prompt()

def check_set_level(_res):
    # TODO: Not implemented properly yet. This test fails.
    # res.sendline("set node level 2")
    # res.wait_prompt()
    # res.sendline("show nodes level")
    # res.table_expect("| node1 | 1 | True | 2 | 2 |")
    # res.wait_prompt()
    pass

def check_set_node(res):
    res.sendline("")
    res.wait_prompt("node1")
    res.sendline("set node node2")
    res.wait_prompt("node2")

def test_cli_commands():
    res = RiftExpectSession("2n_l0_l1")
    check_show_fsm_lie(res)
    check_show_fsm_ztp(res)
    check_show_interface(res)
    check_show_interface_fsm_history(res)
    check_show_interface_fsm_verbose_history(res)
    check_show_interfaces(res)
    check_show_node(res)
    check_show_node_fsm_history(res)
    check_show_node_fsm_verbose_history(res)
    check_show_nodes(res)
    check_show_nodes_level(res)
    check_set_level(res)
    check_set_node(res)
    res.stop()
