#!/usr/bin/env python3

import argparse
import re

import log_record

TICK_Y_START = 40
TICK_Y_INTERVAL = 20
TIMESTAMP_X = 10
NODE_X = 270
NODE_X_INTERVAL = 100
IF_X_INTERVAL = 10
DOT_RADIUS = 5
TIMESTAMP_COLOR = "gray"
TARGET_COLOR = "black"
IF_FSM_COLOR = "red"
NODE_FSM_COLOR = "coral"
IPV4_MSG_COLOR = "#1F618D"   # Dark blue
IPV6_MSG_COLOR = "#3498DB"    # Light blue
CLI_COLOR = "green"
LOG_COLOR = "orange"
DEFAULT_COLOR = "black"
END_OF_SVG = """
<g id="tooltip" visibility="hidden" >
    <rect x="2" y="2" width="80" height="24" fill="black" opacity="0.4" rx="2" ry="2"/>
    <rect width="80" height="24" fill="yellow" rx="2" ry="2"/>
    <text x="4" 
          y="16"
          style="font-family:monospace;stroke:black;fill:black">
    Tooltip
    </text>
</g>

<script type="text/javascript"><![CDATA[

(function() {
    var tooltip = document.getElementById('tooltip');
})();

var svg = document.getElementById('tooltip-svg');

function ShowTooltip(evt) {
    var CTM = svg.getScreenCTM();
    var x = (evt.clientX - CTM.e + 6) / CTM.a;
    var y = (evt.clientY - CTM.f + 20) / CTM.d;
    tooltip.setAttributeNS(null, "transform", "translate(" + x + " " + y + ")");  
    var tooltipText = tooltip.getElementsByTagName('text')[0];
    var startX = tooltipText.getAttributeNS(null, 'x');
    var fc = tooltipText.firstChild;
    while (fc) {
        tooltipText.removeChild(fc);
        fc = tooltipText.firstChild;
    }
    lines = evt.target.getAttributeNS(null, "data-tooltip-text").split("$");
    var length = 0;
    var height = 0
    for (var i = 0; i < lines.length; i++) {
        line = lines[i];
        var tspanElement = document.createElementNS("http://www.w3.org/2000/svg", "tspan");
        tspanElement.setAttributeNS(null, "x", startX);
        if (i > 0) {
            tspanElement.setAttributeNS(null, "dy", 20);
        }
        var textNode = document.createTextNode(line);
        tspanElement.appendChild(textNode);
        tooltipText.appendChild(tspanElement);
        var thisLength = tspanElement.getComputedTextLength();
        if (thisLength > length) {
            length = thisLength;
        }
        height += 20
    }
    var tooltipRects = tooltip.getElementsByTagName('rect');
    for (var i = 0; i < tooltipRects.length; i++) {
        tooltipRects[i].setAttributeNS(null, "width", length + 8);
        tooltipRects[i].setAttributeNS(null, "height", height + 8);
    }  
	tooltip.setAttributeNS(null, "visibility", "visible");
}

function HideTooltip() {
    tooltip.setAttributeNS(null, "visibility", "hidden");
}

var triggers = document.getElementsByClassName('tooltip-trigger');

for (var i = 0; i < triggers.length; i++) {
    triggers[i].addEventListener('mouseover', ShowTooltip);
    triggers[i].addEventListener('mouseout', HideTooltip);
}

]]></script>

</svg>
"""

def tick_y_top(tick):
    return TICK_Y_START + tick * TICK_Y_INTERVAL

def tick_y_bottom(tick):
    return tick_y_top(tick) + TICK_Y_INTERVAL

def tick_y_mid(tick):
    return (tick_y_top(tick) + tick_y_bottom(tick)) // 2

def log_record_color(record):
    if record.type in ["start-fsm", "push-event", "transition"]:
        if record.target.type == "if":
            return IF_FSM_COLOR
        elif record.target.type == "node":
            return NODE_FSM_COLOR
    elif record.type in ["send", "receive"]:
        if record.packet_family == "IPv4":
            return IPV4_MSG_COLOR
        else:
            return IPV6_MSG_COLOR
    elif record.type == "cli":
        return CLI_COLOR
    elif record.type == "log":
        return LOG_COLOR
    return DEFAULT_COLOR

def log_record_class(record):
    if record.type in ["start-fsm", "push-event", "transition"]:
        if record.target.type == "if":
            return "if_fsm"
        if record.target.type == "node":
            return "node_fsm"
    if record.type == "cli":
        return "cli"
    if record.type == "log":
        return "log"
    if record.packet_type == "LIE":
        return "lie_msg"
    if record.packet_type == "TIE":
        return "tie_msg"
    if record.packet_type == "TIDE":
        return "tide_msg"
    if record.packet_type == "TIRE":
        return "tire_msg"
    return "other"

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
        direction = re.search(r"TIEID\(.*direction=([-0-9]+).*?\)", old_tie_str).group(1)
        if direction == "1":
            direction = "South"
        elif direction == "2":
            direction = "North"
        originator = re.search(r"TIEID\(.*originator=([-0-9]+).*?\)", old_tie_str).group(1)
        tietype = re.search(r"TIEID\(.*tietype=([-0-9]+).*?\)", old_tie_str).group(1)
        if tietype == "2":
            tietype = "Node"
        elif tietype == "3":
            tietype = "Prefix"
        elif tietype == "4":
            tietype = "Pos-Dis-Prefix"
        elif tietype == "5":
            tietype = "Neg-Dis-Prefix"
        elif tietype == "6":
            tietype = "PG-Prefix"
        elif tietype == "7":
            tietype = "Ext-Prefix"
        elif tietype == "8":
            tietype = "Key-Value"
        tie_nr = re.search(r"TIEID\(.*tie_nr=([-0-9]+).*?\)", old_tie_str).group(1)
        new_tie_str = ("TIEID<direction={}, originator={}, tietype={}, tie_nr={}>"
                       .format(direction, originator, tietype, tie_nr))
        new_msg_str = re.sub(r"(TIEID\(.*?\))", new_tie_str, new_msg_str, count=1)
    return new_msg_str

def pretty_format_rift_msg(msg_str, newline='\n'):
    # Space used to be Unicode "\u00A0" but that does not render properly on Safari
    # A regular space " " works neither on Chrome nor on Safari - multiple spaces get merged
    space = "."
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
                    pretty_str += "," + newline + space * indent * 4
                continue
            if char not in ")}]":
                pending_newline = False
                pretty_str += newline + space * indent * 4
        if char == " ":
            if indent == 0:
                pretty_str += char
        elif char == ",":
            if one_line_depth > 0:
                pretty_str += char + " "
            else:
                pretty_str += char + newline + space * indent * 4
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
                pretty_str += char + newline + space * indent * 4
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
    pretty_str = pretty_str.replace(" protocol-packet=", newline)
    pretty_str = normalize_tie_ids(pretty_str)
    return pretty_str

class Target:

    nodes = {}
    next_node_index = 0

    def __init__(self, subsystem, target_id):
        self.target_id = target_id
        if subsystem.startswith("node.if"):
            self.type = 'if'
            split_target_id = target_id.rsplit(':', 1)
            self.node_id = split_target_id[0]
            self.if_id = split_target_id[1]
            node = Target.nodes[self.node_id]
            self.if_index = node.next_if_index
            node.next_if_index += 1
            self.xpos = node.xpos + (self.if_index + 1) * IF_X_INTERVAL
        else:
            self.type = 'node'
            self.node_id = target_id
            self.if_id = None
            self.node_index = Target.next_node_index
            Target.next_node_index += 1
            self.next_if_index = 0
            Target.nodes[self.node_id] = self
            self.xpos = NODE_X + self.node_index * NODE_X_INTERVAL

class SentMessage:

    def __init__(self, xstart, ystart):
        self.xstart = xstart
        self.ystart = ystart

class Visualizer:

    def __init__(self, logfile_name, svg_file_name):
        self.logfile_name = logfile_name
        self.logfile = None
        self.svg_file_name = svg_file_name
        self.svgfile = None
        self.tick = 0
        self.targets = {}
        self.sent_messages = {}

    def run(self):
        with open(self.svg_file_name, "w") as self.svgfile:
            self.html_start()
            self.svg_start()
            with open(self.logfile_name, "r") as self.logfile:
                for logline in self.logfile:
                    record = self.parse_log_line(logline)
                    record.target = self.target_for_record(record)
                    self.show_all_target_ticks()
                    self.show_record(record)
            self.svg_end()

    def parse_log_line(self, logline):
        self.tick += 1
        return log_record.LogRecord(self.tick, logline)

    def target_for_record(self, record):
        if record.target_id in self.targets:
            return self.targets[record.target_id]
        target = Target(record.subsystem, record.target_id)
        self.targets[record.target_id] = target
        self.show_target_id(target)
        return target

    def show_record(self, record):
        self.show_timestamp(self.tick, record.timestamp)
        if record.type == 'start-fsm':
            self.show_start_fsm(record)
        elif record.type == 'push-event':
            self.show_push_event(record)
        elif record.type == 'transition':
            self.show_transition(record)
        elif record.type == 'send':
            self.show_send(record)
        elif record.type == 'receive':
            self.show_receive(record)
        elif record.type == 'cli':
            self.show_cli(record)
        elif record.type == 'log':
            self.show_log(record)

    def show_timestamp(self, tick, timestamp):
        xpos = TIMESTAMP_X
        ypos = tick_y_mid(tick)
        tick_str = "{:06d}".format(tick)
        text = tick_str + " " + timestamp
        self.svg_text(xpos, ypos, text, TIMESTAMP_COLOR, "other")

    def show_all_target_ticks(self):
        for target in self.targets.values():
            self.show_target_tick(target)

    def show_target_id(self, target):
        xpos = target.xpos + 2
        ypos = tick_y_mid(self.tick)
        text = target.target_id
        self.svg_text(xpos, ypos, text, TARGET_COLOR, "other")

    def show_target_tick(self, target):
        xpos = target.xpos
        ystart = tick_y_top(self.tick)
        yend = tick_y_bottom(self.tick)
        self.svg_line(xpos, ystart, xpos, yend, TARGET_COLOR, "other")

    def show_start_fsm(self, record):
        xpos = record.target.xpos
        ypos = tick_y_mid(record.tick)
        color = log_record_color(record)
        the_class = log_record_class(record)
        self.svg_dot(xpos, ypos, DOT_RADIUS, color, the_class)
        xpos += 2 * DOT_RADIUS
        text = "[" + record.state + "]"
        self.svg_text(xpos, ypos, text, color, the_class)

    def show_push_event(self, record):
        xpos = record.target.xpos
        ypos = tick_y_mid(record.tick)
        color = log_record_color(record)
        the_class = log_record_class(record)
        self.svg_dot(xpos, ypos, DOT_RADIUS, color, the_class)
        xpos += 2 * DOT_RADIUS
        text = "Push " + record.event
        self.svg_text(xpos, ypos, text, color, the_class)

    def show_transition(self, record):
        xpos = record.target.xpos
        ypos = tick_y_mid(record.tick)
        color = log_record_color(record)
        the_class = log_record_class(record)
        self.svg_dot(xpos, ypos, DOT_RADIUS, color, the_class)
        xpos += 2 * DOT_RADIUS
        text = ("Transition " + record.event + " [" + record.from_state + "] > " +
                record.actions_and_pushed_events + " [" + record.to_state + "]")
        self.svg_text(xpos, ypos, text, color, the_class)

    def record_sent_message(self, sent_msg_record):
        xpos = sent_msg_record.target.xpos
        ypos = tick_y_mid(sent_msg_record.tick)
        self.sent_messages[sent_msg_record.msg_id] = SentMessage(xpos, ypos)

    def show_send(self, record):
        xpos = record.target.xpos
        ypos = tick_y_mid(record.tick)
        color = log_record_color(record)
        the_class = log_record_class(record)
        pretty_msg = pretty_format_rift_msg(record.packet, newline="$")
        self.svg_dot(xpos, ypos, DOT_RADIUS, color, the_class, pretty_msg)
        self.record_sent_message(record)
        xpos += 2 * DOT_RADIUS
        text = "TX " + record.packet_family + " " + record.packet_type + " " + record.packet
        self.svg_text(xpos, ypos, text, color, the_class)

    def find_sent_message(self, received_msg_record):
        if received_msg_record.msg_id in self.sent_messages:
            return self.sent_messages[received_msg_record.msg_id]
        return None

    def show_receive(self, record):
        xpos = record.target.xpos
        ypos = tick_y_mid(record.tick)
        color = log_record_color(record)
        the_class = log_record_class(record)
        pretty_msg = pretty_format_rift_msg(record.packet, newline="$")
        self.svg_dot(xpos, ypos, DOT_RADIUS, color, the_class, pretty_msg)
        sent_msg = self.find_sent_message(record)
        if sent_msg is not None:
            xstart = sent_msg.xstart
            ystart = sent_msg.ystart
            xend = record.target.xpos
            yend = tick_y_mid(record.tick)
            self.svg_line(xstart, ystart, xend, yend, color, the_class)
        xpos += 2 * DOT_RADIUS
        text = "RX " + record.packet_family + " " + record.packet_type + " " + record.packet
        self.svg_text(xpos, ypos, text, color, the_class)

    def show_cli(self, record):
        xpos = record.target.xpos
        ypos = tick_y_mid(record.tick)
        color = log_record_color(record)
        the_class = log_record_class(record)
        self.svg_dot(xpos, ypos, DOT_RADIUS, color, the_class)
        xpos += 2 * DOT_RADIUS
        text = record.cli_command
        self.svg_text(xpos, ypos, text, color, the_class)

    def show_log(self, record):
        xpos = record.target.xpos
        ypos = tick_y_mid(record.tick)
        color = log_record_color(record)
        the_class = log_record_class(record)
        self.svg_dot(xpos, ypos, DOT_RADIUS, color, the_class)
        xpos += 2 * DOT_RADIUS
        text = record.msg
        self.svg_text(xpos, ypos, text, color, the_class)

    def html_start(self):
        self.svgfile.write('<script '
                           'src="https://ajax.googleapis.com/ajax/libs/jquery/1.9.1/jquery.min.js">'
                           '</script>\n')
        buttons = [("Interface FSM", "if_fsm"),
                   ("Node FSM", "node_fsm"),
                   ("CLI", "cli"),
                   ("Log >= WARNING", "log"),
                   ("LIE Messages", "lie_msg"),
                   ("TIE Messages", "tie_msg"),
                   ("TIDE Messages", "tide_msg"),
                   ("TIRE Messages", "tire_msg")]
        for (description, the_class) in buttons:
            self.html_checkbox(description, the_class)
        self.svgfile.write('<script type="text/javascript">\n')
        for (description, the_class) in buttons:
            self.script_checkbox(the_class)
        self.svgfile.write('</script>\n')

    def html_checkbox(self, description, the_class):
        self.svgfile.write('<input type="checkbox" '
                           'class="{0}_checkbox" '
                           'onchange="{0}_change()" '
                           'checked> {1} <br>\n'
                           .format(the_class, description))

    def script_checkbox(self, the_class):
        self.svgfile.write('function {0}_change()\n'
                           '{{\n'
                           '  if($(".{0}_checkbox").is(":checked"))\n'
                           '    $(".{0}").show();\n'
                           '  else\n'
                           '    $(".{0}").hide();\n'
                           '}}\n'.format(the_class))

    def svg_start(self):
        self.svgfile.write('<svg '
                           'xmlns="http://www.w3.org/2000/svg '
                           'xmlns:xlink="http://www.w3.org/1999/xlink" '
                           'width=1000000 '
                           'height=1000000 '
                           'id="tooltip-svg">\n')

    def svg_end(self):
        self.svgfile.write(END_OF_SVG)

    def svg_line(self, xstart, ystart, xend, yend, color, the_class):
        self.svgfile.write('<line '
                           'x1="{}" '
                           'y1="{}" '
                           'x2="{}" '
                           'y2="{}" '
                           'style="stroke:{};" '
                           'class="{}">'
                           '</line>\n'
                           .format(xstart, ystart, xend, yend, color, the_class))

    def svg_dot(self, xpos, ypos, radius, color, the_class, tooltip=None):
        classes = the_class
        if tooltip is None:
            tooltip_attr = ''
        else:
            classes += " tooltip-trigger"
            tooltip_attr = ' data-tooltip-text="{}"'.format(tooltip)
        self.svgfile.write('<circle '
                           'cx="{}" '
                           'cy="{}" '
                           'r="{}" '
                           'style="stroke:{color};fill:{color}"'
                           'class="{}"'
                           '{}>'
                           '</circle>\n'
                           .format(xpos, ypos, radius, classes, tooltip_attr, color=color))

    def svg_text(self, xpos, ypos, text, color, the_class):
        self.svgfile.write('<text '
                           'x="{}" '
                           'y="{}" '
                           'style="font-family:monospace;stroke:{}"'
                           'class="{}">'
                           '{}'
                           '</text>\n'
                           .format(xpos, ypos, color, the_class, text))

def main():
    args = parse_command_line_arguments()
    visualizer = Visualizer(args.logfile, args.svgfile)
    visualizer.run()

def parse_command_line_arguments():
    parser = argparse.ArgumentParser(description='Visualize RIFT log')
    parser.add_argument('logfile', nargs='?', default='rift.log', help='RIFT log file')
    parser.add_argument('svgfile', nargs='?', default='rift.log.html',
                        help='Visualized RIFT log file')
    args = parser.parse_args()
    return args

if __name__ == "__main__":
    main()
