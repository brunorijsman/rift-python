import table

class Group:

    def __init__(self):
        self._members = []

    def add_member(self, member):
        self._members.append(member)

    def table(self, exclude_zero):
        tab = table.Table()
        tab.add_row(["Description", "Value"])
        for member in self._members:
            if not exclude_zero or member.value:
                tab.add_row([member.description, member.value_with_units])
        return tab

class Counter:

    def __init__(self, group, description, unit_singular, unit_plural=None):
        self._group = group
        self._description = description
        self._unit_singular = unit_singular
        if unit_plural is None:
            self._unit_plural = unit_singular + 's'
        else:
            self._unit_plural = unit_plural
        self._count = 0
        group.add_member(self)

    def add(self, value):
        self._count += value

    def increase(self):
        self.add(1)

    @property
    def description(self):
        return self._description

    @property
    def value(self):
        return self._count

    @property
    def value_with_units(self):
        if self._count == 1:
            return str(self._count) + ' ' + self._unit_singular
        else:
            return str(self._count) + ' ' + self._unit_plural
