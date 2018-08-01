import argparse
import re

TICK_Y_START = 40
TICK_Y_INTERVAL = 20
TIMESTAMP_X = 10
NODE_X = 220
NODE_X_INTERVAL = 100
IF_X_INTERVAL = 10

def tick_y_top(tick):
    return TICK_Y_START + tick * TICK_Y_INTERVAL

def tick_y_bottom(tick):
    return tick_y_top(tick) + TICK_Y_INTERVAL

def tick_y_mid(tick):
    return (tick_y_top(tick) + tick_y_bottom(tick)) // 2

class Obj:

    nodes = {}
    next_node_index = 0

    def __init__(self, object_id):
        self.object_id = object_id
        if '-' in object_id:
            self.type = 'if'
            split_object_id = object_id.split('-', 1)
            self.node_id = split_object_id[0]
            self.if_id = split_object_id[1]
            node = Obj.nodes[self.node_id]
            self.if_index = node.next_if_index
            node.next_if_index += 1
            self.xpos = node.xpos + (self.if_index + 1) * IF_X_INTERVAL
        else:
            self.type = 'node'
            self.node_id = object_id
            self.if_id = None
            self.node_index = Obj.next_node_index
            Obj.next_node_index += 1
            self.next_if_index = 0
            Obj.nodes[self.node_id] = self
            self.xpos = NODE_X + self.node_index * NODE_X_INTERVAL

class Record:

    regex = re.compile(r"(....-..-.. ..:..:..[^:]*):([^:]*):([^:]*):\[(.*)\] (.*)$")

    def __init__(self, tick, logline):
        self.tick = tick
        match_result = self.regex.search(logline)
        self.timestamp = match_result.group(1)
        self.severity = match_result.group(2)
        self.subsystem = match_result.group(3)
        self.object_id = match_result.group(4)
        self.msg = match_result.group(5)

class Visualizer:

    def __init__(self, logfile_name, svg_file_name):
        self.logfile_name = logfile_name
        self.svg_file_name = svg_file_name
        self.objects = {}
        self.tick = 0
        self.logfile = None
        self.svgfile = None

    def run(self):
        with open(self.svg_file_name, "w") as self.svgfile:
            self.svg_start()
            with open(self.logfile_name, "r") as self.logfile:
                for logline in self.logfile:
                    record = self.parse_log_line(logline)
                    self.record_object(record)
                    self.show_all_object_ticks()
                    self.show_record(record)
            self.svg_end()

    def parse_log_line(self, logline):
        self.tick += 1
        return Record(self.tick, logline)

    def record_object(self, record):
        if record.object_id in self.objects:
            return
        obj = Obj(record.object_id)
        self.objects[record.object_id] = obj
        self.show_object_id(obj)

    def show_record(self, record):
        self.show_timestamp(self.tick, record.timestamp)

    def show_timestamp(self, tick, timestamp):
        xpos = TIMESTAMP_X
        ypos = tick_y_mid(tick)
        text = timestamp
        self.svg_text(xpos, ypos, text)

    def show_all_object_ticks(self):
        for obj in self.objects.values():
            self.show_object_tick(obj)

    def show_object_id(self, obj):
        xpos = obj.xpos
        ypos = tick_y_top(self.tick)
        text = obj.object_id
        self.svg_text(xpos, ypos, text)

    def show_object_tick(self, obj):
        xpos = obj.xpos
        ystart = tick_y_top(self.tick)
        yend = tick_y_bottom(self.tick)
        self.svg_line(xpos, ystart, xpos, yend)

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

    def svg_text(self, xpos, ypos, text):
        self.svgfile.write('<text '
                           'x="{}" '
                           'y="{}" '
                           'style="font-family:monospace">'
                           '{}'
                           '</text>\n'
                           .format(xpos, ypos, text))

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
