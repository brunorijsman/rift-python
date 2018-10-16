import re

LIE = "TX LIE ProtocolPacket(header=PacketHeader(sender=2, major_version=19, level=0, minor_version=0), content=PacketContent(tide=None, tire=None, tie=None, lie=LIEPacket(neighbor=Neighbor(remote_id=1, originator=1), holdtime=3, last_neighbor_nonce=None, link_mtu_size=1400, flood_port=10002, pod=0, not_a_ztp_offer=False, local_id=1, nonce=8703250060085443132, capabilities=NodeCapabilities(flood_reduction=True, hierarchy_indications=1), you_are_flood_repeater=True, link_bandwidth=100, label=None, name='node2-if1')))"

TIDE = "TX TIDE ProtocolPacket(header=PacketHeader(sender=1, major_version=19, level=1, minor_version=0), content=PacketContent(tide=TIDEPacket(start_range=TIEID(originator=0, tietype=2, tie_nr=0, direction=1), end_range=TIEID(originator=-1, tietype=7, tie_nr=-1, direction=2), headers=[TIEHeader(remaining_lifetime=604800, seq_nr=2, tieid=TIEID(originator=1, tietype=2, tie_nr=1, direction=1), origination_time=None, origination_lifetime=None), TIEHeader(remaining_lifetime=604800, seq_nr=2, tieid=TIEID(originator=1, tietype=2, tie_nr=1, direction=1), origination_time=None, origination_lifetime=None)]), tire=None, tie=None, lie=None)) to 192.168.0.13:10002"

TIE = "TX TIE ProtocolPacket(header=PacketHeader(sender=1, major_version=19, level=1, minor_version=0), content=PacketContent(tide=None, tire=None, tie=TIEPacket(header=TIEHeader(remaining_lifetime=604799, seq_nr=2, tieid=TIEID(originator=1, tietype=2, tie_nr=1, direction=1), origination_time=None, origination_lifetime=None), element=TIEElement(external_prefixes=None, negative_disaggregation_prefixes=None, prefixes=None, node=NodeTIEElement(neighbors={2: NodeNeighborsTIEElement(link_ids=None, bandwidth=100, cost=1, level=0)}, name='node1', capabilities=None, flags=None, level=1), keyvalues=None, positive_disaggregation_prefixes=None)), lie=None)) to 192.168.0.13:10002"

TIRE = "TX TIRE ProtocolPacket(header=PacketHeader(sender=1, major_version=19, level=1, minor_version=0), content=PacketContent(tide=None, tire=TIREPacket(headers=[TIEHeader(remaining_lifetime=0, seq_nr=0, tieid=TIEID(originator=2, tietype=2, tie_nr=2, direction=2), origination_time=None, origination_lifetime=None)]), tie=None, lie=None)) to 192.168.0.13:10002"

def remove_none_fields(msg_str):
    new_msg_str = re.sub(r"[a-zA-Z_]+=None, ", "", msg_str)
    new_msg_str = re.sub(r", [a-zA-Z_]+=None\)", ")", new_msg_str)
    return new_msg_str

def normalize_tie_ids(msg_str):
    new_msg_str = msg_str
    while True:
        match = re.search(r"(TIEID\(.*?\))", new_msg_str)
        if match is None:
            return new_msg_str
        old_tie_str = match.group(1)
        direction = re.search(r"TIEID\(.*direction=([-0-9])+.*?\)", old_tie_str).group(1)
        if direction == "1":
            direction = "South"
        elif direction == "2":
            direction = "North"
        originator = re.search(r"TIEID\(.*originator=([-0-9])+.*?\)", old_tie_str).group(1)
        tietype = re.search(r"TIEID\(.*tietype=([-0-9])+.*?\)", old_tie_str).group(1)
        if tietype == "2":
            tietype = "Node"
        elif tietype == "3":
            tietype = "Prefix"
        elif tietype == "4":
            tietype = "PositiveDisaggregationPrefix"
        elif tietype == "5":
            tietype = "NegativeDisaggregationPrefix"
        elif tietype == "6":
            tietype = "PolicyGuidedPrefix"
        elif tietype == "7":
            tietype = "External"
        elif tietype == "8":
            tietype = "KeyValue"
        tie_nr = re.search(r"TIEID\(.*tie_nr=([-0-9])+.*?\)", old_tie_str).group(1)
        new_tie_str = ("TIEID<direction={}, originator={}, tietype={}, tie_nr={}>"
                       .format(direction, originator, tietype, tie_nr))
        new_msg_str = re.sub(r"(TIEID\(.*?\))", new_tie_str, new_msg_str, count=1)
    return new_msg_str

def pretty_format_rift_msg(msg_str):
    one_line_types = ["TIEID", "PacketHeader", "NodeNeighborsTIEElement"]
    new_msg_str = remove_none_fields(msg_str)
    pretty_str = ""
    indent = 0
    pending_newline = False
    one_line_depth = 0
    for char in new_msg_str:
        if pending_newline:
            if char == ",":
                if one_line_depth > 0:
                    pretty_str += ", "
                else:
                    pending_newline = False
                    pretty_str += ",\n" + " " * indent * 4
                continue
            elif char not in ")}]":
                pending_newline = False
                pretty_str += "\n" + " " * indent * 4
        if char == " ":
            if indent == 0:
                pretty_str += char
        elif char == ",":
            if one_line_depth > 0:
                pretty_str += char + " "
            else:
                pretty_str += char + "\n" + " " * indent * 4
        elif char in "({[":
            one_line = False
            for one_line_type in one_line_types:
                if pretty_str.endswith(one_line_type):
                    one_line = True
                    break
            if one_line:
                pretty_str += char
                one_line_depth += 1
            else:
                indent += 1
                pretty_str += char + "\n" + " " * indent * 4
        elif char in ")}]":
            pretty_str += char
            if one_line_depth > 0:
                one_line_depth -= 1
            else:
                indent -= 1
            if one_line_depth > 0:
                pending_newline = True
        else:
            pretty_str += char
    pretty_str = normalize_tie_ids(pretty_str)
    return pretty_str

print(pretty_format_rift_msg(TIE))
