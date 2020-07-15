# System test: test_sys_2n_l0_l1
#
# Test all CLI commands. We invoke each command and check that the prompt returns (i.e. it does not
# crash). For show commands, we do a bare-bones minimum check of a couple of fields in the output
# to make sure the command produces some output. We make no attempt to verify the sanity of every
# single field in the output. For set commands, we do a basic check to see if the desired change
# takes effect.

# Allow long test names
# pylint: disable=invalid-name

from rift_expect_session import RiftExpectSession

def check_clear_engine_statistics(res):
    res.sendline("clear interface if1 statistics")
    res.wait_prompt()

def check_clear_interface_statistics(res):
    res.sendline("clear engine statistics")
    res.wait_prompt()

def check_clear_node_statistics(res):
    res.sendline("clear node statistics")
    res.wait_prompt()

def check_set_interface_failure(res):
    res.sendline("set interface if1 failure failed")
    res.wait_prompt()
    res.sendline("set interface if1 failure ok")
    res.wait_prompt()

def check_show_engine(res):
    res.sendline("show engine")
    res.table_expect("| Telnet Port File | None |")
    res.wait_prompt()

def check_show_engine_statistics(res):
    res.sendline("show engine statistics")
    res.table_expect("All Node ZTP FSMs:")
    res.table_expect("| Events NEIGHBOR_OFFER | .* Event.* |")
    res.table_expect("All Interfaces Traffic:")
    res.table_expect("| RX IPv4 LIE Packets | .* Packets, .* Bytes |")
    res.table_expect("All Interface LIE FSMs:")
    res.table_expect("| Events TIMER_TICK | .* Event.* |")
    res.wait_prompt()

def check_show_flooding_reduction(res):
    res.sendline("set node node2")
    res.wait_prompt()
    res.sendline("show flooding-reduction")
    res.table_expect("Parents:")
    res.table_expect("| if1 | 1 | node1:if1 | 0 | 1: 0-0 | False |")
    res.table_expect("Grandparents:")
    res.table_expect("Interfaces:")
    res.table_expect("| if1 | node1:if1 | 1 | THREE_WAY | North | False | Not Applicable |")
    res.wait_prompt()
    res.sendline("set node node1")
    res.wait_prompt()

def check_show_forwarding(res):
    res.sendline("show forwarding")
    res.table_expect("IPv4 Routes:")
    res.table_expect("| 2.2.1.0/24 | Positive | if1")
    res.table_expect("IPv6 Routes:")
    res.wait_prompt()

def check_show_forwarding_prefix(res):
    res.sendline("show forwarding prefix 2.2.2.2/32")
    res.table_expect("| 2.2.2.2/32 | Positive | if1")
    res.wait_prompt()

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
    res.table_expect("| Name | node2:if1 |")
    res.table_expect("| System ID | 2 |")
    res.wait_prompt()

def check_show_interface_fsm_history(res):
    res.sendline("show interface if1 fsm history")
    res.table_expect("| TWO_WAY | VALID_REFLECTION | increase_tx_nonce_local | THREE_WAY | False |")
    res.table_expect("| ONE_WAY | NEW_NEIGHBOR | SEND_LIE | TWO_WAY | False |")
    res.wait_prompt()

def check_show_interface_fsm_verbose_history(res):
    res.sendline("show interface if1 fsm verbose-history")
    res.table_expect("| .* | LIE_RECEIVED | process_lie | None | False |")
    res.table_expect("| .* | SEND_LIE | send_lie | None | False |")
    res.wait_prompt()

def check_show_interface_queues(res):
    res.sendline("show interface if1 queues")
    res.table_expect("Transmit queue:")
    res.table_expect("Request queue:")
    res.table_expect("Acknowledge queue:")
    res.wait_prompt()

def check_show_interface_sockets(res):
    res.sendline("show interface if1 sockets")
    res.table_expect("| LIEs | Receive | IPv4 |")
    res.table_expect("| LIEs | Send | IPv4 |")
    res.table_expect("| Flooding | Receive |")
    res.table_expect("| Flooding | Send |")
    res.wait_prompt()

def check_show_interface_statistics(res):
    res.sendline("show interface if1 statistics")
    res.table_expect("Traffic:")
    res.table_expect("| RX IPv4 LIE Packets | .* Packets, .* Bytes |")
    res.table_expect("LIE FSM:")
    res.table_expect("| Events TIMER_TICK | .* Event.* |")
    res.wait_prompt()

def check_show_interface_statistics_exclude_zero(res):
    res.sendline("show interface if1 statistics exclude-zero")
    res.table_expect("Traffic:")
    res.table_expect("LIE FSM:")
    res.wait_prompt()

def check_show_interfaces(res):
    res.sendline("show interfaces")
    res.table_expect("| if1 | node2:if1 | 2 | THREE_WAY |")
    res.wait_prompt()

def check_show_kernel_addresses(res):
    res.sendline("show kernel addresses")
    res.wait_prompt()

def check_show_kernel_links(res):
    res.sendline("show kernel links")
    res.wait_prompt(timeout=10.0)   # This can take a long time if there are many veth links

def check_show_kernel_routes(res):
    res.sendline("show kernel routes")
    res.wait_prompt()

def check_show_kernel_routes_table(res):
    res.sendline("show kernel routes table main")
    res.wait_prompt()

def check_show_kernel_routes_table_prefix(res):
    res.sendline("show kernel routes table main prefix 0.0.0.0/0 ")
    res.wait_prompt()

def check_show_node(res):
    res.sendline("show node")
    res.table_expect("Node:")
    res.table_expect("| Name | node1 |")
    res.table_expect("| Configured Level  | 1 |")
    res.table_expect("Received Offers:")
    res.table_expect("| if1 | 2 | 0 | False | THREE_WAY | False | False | True | Level is leaf |")
    res.table_expect("Sent Offers:")
    res.table_expect("| if1 | 1 | 1 | False | THREE_WAY |")
    res.wait_prompt()

def check_show_node_fsm_history(res):
    res.sendline("show node fsm history")
    res.table_expect("| COMPUTE_BEST_OFFER | COMPUTATION_DONE | update_all_lie_fsms |"
                     " UPDATING_CLIENTS | False |")
    res.wait_prompt()

def check_show_node_fsm_verbose_history(res):
    res.sendline("show node fsm verbose-history")
    res.table_expect("| UPDATING_CLIENTS | NEIGHBOR_OFFER | update_or_remove_offer | None | "
                     "False |")
    res.wait_prompt()

def check_show_node_statistics(res):
    res.sendline("show node statistics")
    res.table_expect("ZTP FSM:")
    res.table_expect("| Events NEIGHBOR_OFFER | .* Event.* |")
    res.table_expect("Node Interfaces Traffic:")
    res.table_expect("| RX IPv4 LIE Packets | .* Packets, .* Bytes |")
    res.table_expect("Node Interface LIE FSMs:")
    res.table_expect("| Events TIMER_TICK | .* Event.* |")
    res.wait_prompt()

def check_show_node_statistics_exclude_zero(res):
    res.sendline("show node statistics exclude-zero")
    res.wait_prompt()

def check_show_nodes(res):
    res.sendline("show nodes")
    res.table_expect("| node1 | 1 | True |")
    res.wait_prompt()

def check_show_nodes_level(res):
    res.sendline("show nodes level")
    res.table_expect("| node1 | 1 | True | 1 | 1 |")
    res.wait_prompt()

def check_show_routes(res):
    res.sendline("show routes")
    res.table_expect("IPv4 Routes:")
    res.table_expect("| 2.2.1.0/24 | South SPF | Positive | if1")
    res.table_expect("IPv6 Routes:")
    res.wait_prompt()

def check_show_routes_prefix(res):
    res.sendline("show routes prefix 2.2.1.0/24")
    res.table_expect("| 2.2.1.0/24 | South SPF | Positive | if1")
    res.wait_prompt()

def check_show_routes_prefix_owner(res):
    res.sendline("show routes prefix 2.2.1.0/24 owner south-spf")
    res.table_expect("| 2.2.1.0/24 | South SPF | Positive | if1")
    res.wait_prompt()

def check_show_spf(res):
    res.sendline("set node node2")
    res.wait_prompt()
    res.sendline("show spf")
    res.table_expect("SPF Statistics:")
    res.table_expect("| SPF Runs |")
    res.table_expect("South SPF Destinations:")
    res.table_expect("| 2 .node2. | 0 | True |")
    res.table_expect("| 2.2.1.0/24 | 1 | True | 2 |")
    res.table_expect("North SPF Destinations:")
    res.table_expect("| 1 .node1. | 1 | False |")
    res.table_expect("| 0.0.0.0/0 | 2 | False | 1 |")
    res.sendline("set node node1")
    res.wait_prompt()

def check_show_spf_direction(res):
    res.sendline("set node node2")
    res.wait_prompt()
    res.sendline("show spf direction south")
    res.table_expect("South SPF Destinations:")
    res.table_expect("| 2 .node2.  | 0 | True |")
    res.table_expect("| 2.2.1.0/24 | 1 | True | 2 |")
    res.wait_prompt()
    res.sendline("set node node1")
    res.wait_prompt()

def check_show_spf_direction_destination(res):
    res.sendline("set node node2")
    res.wait_prompt()
    res.sendline("show spf direction south destination 2.2.1.0/24")
    res.table_expect("| 2.2.1.0/24 | 1 | True | 2 |")
    res.wait_prompt()
    res.sendline("set node node1")
    res.wait_prompt()

def check_show_tie_db(res):
    res.sendline("set node node2")
    res.wait_prompt()
    res.sendline("show tie-db")
    res.table_expect("| South     | 1 | Node   | 1 | .* | .* | Name: node1 |")
    res.wait_prompt()
    res.sendline("set node node1")
    res.wait_prompt()

def check_show_tie_db_dir(res):
    res.sendline("set node node2")
    res.wait_prompt()
    res.sendline("show tie-db direction south")
    res.table_expect("| South     | 1 | Node   | 1 | .* | .* | Name: node1 |")
    res.wait_prompt()
    res.sendline("set node node1")
    res.wait_prompt()

def check_show_tie_db_dir_orig(res):
    res.sendline("set node node2")
    res.wait_prompt()
    res.sendline("show tie-db direction south originator 1")
    res.table_expect("| South     | 1 | Node   | 1 | .* | .* | Name: node1 |")
    res.wait_prompt()
    res.sendline("set node node1")
    res.wait_prompt()

def check_show_tie_db_dir_orig_type(res):
    res.sendline("set node node2")
    res.wait_prompt()
    res.sendline("show tie-db direction south originator 1 type node")
    res.table_expect("| South     | 1 | Node   | 1 | .* | .* | Name: node1 |")
    res.wait_prompt()
    res.sendline("set node node1")
    res.wait_prompt()

def check_set_level(_res):
    # Not implemented properly yet. This test fails. See issue #78
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
    res.sendline("set node node1")
    res.wait_prompt("node1")

def check_stop(res):
    res.sendline("stop")

def test_cli_commands():
    res = RiftExpectSession("2n_l0_l1")
    check_clear_engine_statistics(res)
    check_clear_interface_statistics(res)
    check_clear_node_statistics(res)
    check_set_interface_failure(res)
    check_set_level(res)
    check_set_node(res)
    check_show_engine(res)
    check_show_engine_statistics(res)
    check_show_flooding_reduction(res)
    check_show_forwarding(res)
    check_show_forwarding_prefix(res)
    check_show_fsm_lie(res)
    check_show_fsm_ztp(res)
    check_show_interface(res)
    check_show_interface_fsm_history(res)
    check_show_interface_fsm_verbose_history(res)
    check_show_interface_queues(res)
    check_show_interface_sockets(res)
    check_show_interface_statistics(res)
    check_show_interface_statistics_exclude_zero(res)
    check_show_interfaces(res)
    check_show_kernel_addresses(res)
    check_show_kernel_links(res)
    check_show_kernel_routes(res)
    check_show_kernel_routes_table(res)
    check_show_kernel_routes_table_prefix(res)
    check_show_node(res)
    check_show_node_fsm_history(res)
    check_show_node_fsm_verbose_history(res)
    check_show_node_statistics(res)
    check_show_node_statistics_exclude_zero(res)
    check_show_nodes(res)
    check_show_nodes_level(res)
    check_show_routes(res)
    check_show_routes_prefix(res)
    check_show_routes_prefix_owner(res)
    check_show_spf(res)
    check_show_spf_direction(res)
    check_show_spf_direction_destination(res)
    check_set_level(res)
    check_set_node(res)
    check_stop(res)
    res.stop()
