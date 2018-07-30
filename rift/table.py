from enum import Enum

# TODO: Implement EXTEND_ABOVE_CELL

class Table:

    class Format(Enum):
        EXTEND_LEFT_CELL = 1
        EXTEND_ABOVE_CELL = 2

    def __init__(self, separators=True):
        self._separators = separators
        self._rows = []
        self._column_widths = {}

    def add_row(self, row):
        self._rows.append(row)

    def add_rows(self, rows):
        for row in rows:
            self._rows.append(row)

    def make_line_list(self, line):
        if isinstance(line, list):
            return line
        if isinstance(line, self.Format):
            return []
        return [line]

    def determine_column_widths(self):
        # TODO: First pass: ignore extended columns
        # TODO: If necessary, grow columns to make extended columns fit
        self._column_widths = {}
        for row in self._rows:
            column_nr = 0
            for column in row:
                if not column_nr in self._column_widths:
                    self._column_widths[column_nr] = 0
                line_list = self.make_line_list(column)
                for line in line_list:
                    if not isinstance(line, str):
                        line = "{}".format(line)
                    if len(line) > self._column_widths[column_nr]:
                        self._column_widths[column_nr] = len(line)
                column_nr += 1

    def determine_row_height(self, row):
        row_height = 0
        for column in row:
            line_list = self.make_line_list(column)
            if len(line_list) > row_height:
                row_height = len(line_list)
        return row_height

    def row_string(self, row):
        row_str = ""
        row_height = self.determine_row_height(row)
        for line_nr in range(row_height):
            row_str += "|"
            column_nr = 0
            for column in row:
                line_list = self.make_line_list(column)
                if line_nr < len(line_list):
                    line = line_list[line_nr]
                else:
                    line = ""
                if not isinstance(line, str):
                    line = "{}".format(line)
                width = self._column_widths[column_nr]
                row_str += " {line:{width}}".format(line=line, width=width) + " "
                if (len(row) > column_nr+1) and (row[column_nr+1] == self.Format.EXTEND_LEFT_CELL):
                    row_str += " "
                else:
                    row_str += "|"
                column_nr += 1
            row_str += '\n'
        return row_str

    def separator_string(self):
        sep_str = ""
        for _, width in self._column_widths.items():
            sep_str += "+-" + "-" * width + "-"
        sep_str += "+\n"
        return sep_str

    def to_string(self):
        self.determine_column_widths()
        table_str = ""
        table_str += self.separator_string()
        for row in self._rows:
            table_str += self.row_string(row)
            if self._separators:
                table_str += self.separator_string()
        if not self._separators:
            table_str += self.separator_string()
        return table_str

    def print(self):
        print(self.to_string())
