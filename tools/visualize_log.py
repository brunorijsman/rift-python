#!/usr/bin/env python

import argparse

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
MSG_COLOR = "blue"
CLI_COLOR = "green"
DEFAULT_COLOR = "black"

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
        return MSG_COLOR
    elif record.type == "cli":
        return CLI_COLOR
    return DEFAULT_COLOR

class Target:

    nodes = {}
    next_node_index = 0

    def __init__(self, target_id):
        self.target_id = target_id
        if '-' in target_id:
            self.type = 'if'
            split_target_id = target_id.split('-', 1)
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

    def __init__(self, nonce, xstart, ystart):
        self.nonce = nonce
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
        target = Target(record.target_id)
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

    def show_timestamp(self, tick, timestamp):
        xpos = TIMESTAMP_X
        ypos = tick_y_mid(tick)
        tick_str = "{:06d}".format(tick)
        text = tick_str + " " + timestamp
        self.svg_text(xpos, ypos, text, TIMESTAMP_COLOR)

    def show_all_target_ticks(self):
        for target in self.targets.values():
            self.show_target_tick(target)

    def show_target_id(self, target):
        xpos = target.xpos + 2
        ypos = tick_y_mid(self.tick)
        text = target.target_id
        self.svg_text(xpos, ypos, text, TARGET_COLOR)

    def show_target_tick(self, target):
        xpos = target.xpos
        ystart = tick_y_top(self.tick)
        yend = tick_y_bottom(self.tick)
        self.svg_line(xpos, ystart, xpos, yend, TARGET_COLOR)

    def show_start_fsm(self, record):
        xpos = record.target.xpos
        ypos = tick_y_mid(record.tick)
        color = log_record_color(record)
        self.svg_dot(xpos, ypos, DOT_RADIUS, color)
        xpos += 2 * DOT_RADIUS
        text = "[" + record.state + "]"
        self.svg_text(xpos, ypos, text, color)

    def show_push_event(self, record):
        xpos = record.target.xpos
        ypos = tick_y_mid(record.tick)
        color = log_record_color(record)
        self.svg_dot(xpos, ypos, DOT_RADIUS, color)
        xpos += 2 * DOT_RADIUS
        text = "Push " + record.event
        self.svg_text(xpos, ypos, text, color)

    def show_transition(self, record):
        xpos = record.target.xpos
        ypos = tick_y_mid(record.tick)
        color = log_record_color(record)
        self.svg_dot(xpos, ypos, DOT_RADIUS, color)
        xpos += 2 * DOT_RADIUS
        text = ("Transition " + record.event + " [" + record.from_state + "] > " +
                record.actions_and_pushed_events + " [" + record.to_state + "]")
        self.svg_text(xpos, ypos, text, color)

    def show_send(self, record):
        xpos = record.target.xpos
        ypos = tick_y_mid(record.tick)
        color = log_record_color(record)
        self.svg_dot(xpos, ypos, DOT_RADIUS, color)
        if record.nonce is not None:
            self.sent_messages[record.nonce] = SentMessage(record.nonce, xpos, ypos)
        xpos += 2 * DOT_RADIUS
        text = "TX " + record.packet_type + " " + record.packet
        self.svg_text(xpos, ypos, text, color)

    def show_receive(self, record):
        xpos = record.target.xpos
        ypos = tick_y_mid(record.tick)
        color = log_record_color(record)
        self.svg_dot(xpos, ypos, DOT_RADIUS, color)
        if (record.nonce is not None) and (record.nonce in self.sent_messages):
            xstart = self.sent_messages[record.nonce].xstart
            ystart = self.sent_messages[record.nonce].ystart
            xend = record.target.xpos
            yend = tick_y_mid(record.tick)
            self.svg_line(xstart, ystart, xend, yend, color)
        xpos += 2 * DOT_RADIUS
        text = "RX " + record.packet_type + " " + record.packet
        self.svg_text(xpos, ypos, text, color)

    def show_cli(self, record):
        xpos = record.target.xpos
        ypos = tick_y_mid(record.tick)
        color = log_record_color(record)
        self.svg_dot(xpos, ypos, DOT_RADIUS, color)
        xpos += 2 * DOT_RADIUS
        text = record.cli_command
        self.svg_text(xpos, ypos, text, color)

    def svg_start(self):
        self.svgfile.write('<svg '
                           'xmlns="http://www.w3.org/2000/svg '
                           'xmlns:xlink="http://www.w3.org/1999/xlink" '
                           'width=1000000 '
                           'height=1000000>\n')

    def svg_end(self):
        self.svgfile.write('</svg>\n')

    def svg_line(self, xstart, ystart, xend, yend, color):
        self.svgfile.write('<line '
                           'x1="{}" '
                           'y1="{}" '
                           'x2="{}" '
                           'y2="{}" '
                           'style="stroke:{};">'
                           '</line>\n'
                           .format(xstart, ystart, xend, yend, color))

    def svg_dot(self, xpos, ypos, radius, color):
        self.svgfile.write('<circle '
                           'cx="{}" '
                           'cy="{}" '
                           'r="{}" '
                           'style="stroke:{};fill:{}">'
                           '</circle>\n'
                           .format(xpos, ypos, radius, color, color))

    def svg_text(self, xpos, ypos, text, color):
        self.svgfile.write('<text '
                           'x="{}" '
                           'y="{}" '
                           'style="font-family:monospace;stroke:{}">'
                           '{}'
                           '</text>\n'
                           .format(xpos, ypos, color, text))

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
