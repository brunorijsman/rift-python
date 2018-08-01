import argparse
import re

TICK_Y_START = 40
TICK_Y_INTERVAL = 20
TIMESTAMP_X = 10
NODE_X = 220
NODE_X_INTERVAL = 100
IF_X_INTERVAL = 10
DOT_RADIUS = 5
TIMESTAMP_COLOR = "gray"
TARGET_COLOR = "black"
FSM_COLOR = "red"

def tick_y_top(tick):
    return TICK_Y_START + tick * TICK_Y_INTERVAL

def tick_y_bottom(tick):
    return tick_y_top(tick) + TICK_Y_INTERVAL

def tick_y_mid(tick):
    return (tick_y_top(tick) + tick_y_bottom(tick)) // 2

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

class Record:

    record_regex = re.compile(r"(....-..-.. ..:..:..[^:]*):([^:]*):([^:]*):\[(.*)\] (.*)$")
    push_event_regex = re.compile(r"FSM push event, "
                                   "event=(.*)")
    transition_regex = re.compile(r"FSM transition "
                                   "sequence-nr=(.*) "
                                   "from-state=(.*) "
                                   "event=(.*) "
                                   "actions-and-pushed-events=(.*) "
                                   "to-state=(.*) "
                                   "implicit=(.*)")

    def __init__(self, tick, logline):
        self.tick = tick
        match_result = Record.record_regex.search(logline)
        self.timestamp = match_result.group(1)
        self.severity = match_result.group(2)
        self.subsystem = match_result.group(3)
        self.target_id = match_result.group(4)
        self.target = None
        self.msg = match_result.group(5)
        match_result = Record.push_event_regex.match(self.msg)
        if match_result:
            self.type = "push-event"
            self.event = match_result.group(1)
            print(self.type)
            return
        match_result = Record.transition_regex.match(self.msg)
        if match_result:
            self.type = "transition"
            self.sequence_nr = match_result.group(1)
            self.from_state = match_result.group(2)
            self.event = match_result.group(3)
            self.actions_and_pushed_events = match_result.group(4)
            self.to_state = match_result.group(5)
            self.implicit = match_result.group(6)
            print(self.type, self.to_state)
            return
        self.type = "other"

class Visualizer:

    def __init__(self, logfile_name, svg_file_name):
        self.logfile_name = logfile_name
        self.svg_file_name = svg_file_name
        self.targets = {}
        self.tick = 0
        self.logfile = None
        self.svgfile = None

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
        return Record(self.tick, logline)

    def target_for_record(self, record):
        if record.target_id in self.targets:
            return self.targets[record.target_id]
        target = Target(record.target_id)
        self.targets[record.target_id] = target
        self.show_target_id(target)

    def show_record(self, record):
        self.show_timestamp(self.tick, record.timestamp)
        if record.type == 'push-event':
            self.show_push_event(record)
        elif record.type == 'transition':
            self.show_transition(record)

    def show_timestamp(self, tick, timestamp):
        xpos = TIMESTAMP_X
        ypos = tick_y_mid(tick)
        text = timestamp
        self.svg_text(xpos, ypos, text, TIMESTAMP_COLOR)

    def show_all_target_ticks(self):
        for target in self.targets.values():
            self.show_target_tick(target)

    def show_target_id(self, target):
        xpos = target.xpos
        ypos = tick_y_top(self.tick)
        text = target.target_id
        self.svg_text(xpos, ypos, text, TARGET_COLOR)

    def show_target_tick(self, target):
        xpos = target.xpos
        ystart = tick_y_top(self.tick)
        yend = tick_y_bottom(self.tick)
        self.svg_line(xpos, ystart, xpos, yend)

    def show_push_event(self, record):
        xpos = record.target.xpos
        ypos = tick_y_mid(record.tick)
        self.svg_dot(xpos, ypos, DOT_RADIUS, FSM_COLOR)
        xpos += 2 * DOT_RADIUS
        text = record.event
        self.svg_text(xpos, ypos, text, FSM_COLOR)

    def show_transition(self, record):
        print("show")
        xpos = record.target.xpos
        ypos = tick_y_mid(record.tick)
        self.svg_dot(xpos, ypos, DOT_RADIUS, FSM_COLOR)
        xpos += 2 * DOT_RADIUS
        text = (record.event + " " + record.from_state + " > " +
                record.actions_and_pushed_events + " " + record.to_state)
        self.svg_text(xpos, ypos, text, FSM_COLOR)

    def svg_start(self):
        self.svgfile.write('<svg '
                           'xmlns="http://www.w3.org/2000/svg '
                           'xmlns:xlink="http://www.w3.org/1999/xlink" '
                           'width=100000 '
                           'height=100000>\n')

    def svg_end(self):
        self.svgfile.write('</svg>\n')

    def svg_line(self, xstart, ystart, xend, yend):
        self.svgfile.write('<line '
                           'x1="{}" '
                           'y1="{}" '
                           'x2="{}" '
                           'y2="{}" '
                           'style="stroke:black;">'
                           '</line>\n'
                           .format(xstart, ystart, xend, yend))

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
