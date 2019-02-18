import operator

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
            if not exclude_zero or not member.is_zero():
                tab.add_row([member.description(), member.value_display_str()])
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
        self._value = 0
        group.add_member(self)

    def add(self, add_value):
        self._value += add_value

    def increase(self):
        self._value += 1

    def description(self):
        return self._description

    def is_zero(self):
        return self._value == 0

    def value_display_str(self):
        if self._value == 1:
            return str(self._value) + ' ' + self._unit_singular
        else:
            return str(self._value) + ' ' + self._unit_plural

class MultiCounter:

    def __init__(self, group, description, units_singular, units_plural=None):
        assert isinstance(units_singular, list)
        if units_plural is None:
            units_plural = list(map(lambda word: word + 's', units_singular))
        assert isinstance(units_plural, list)
        assert len(units_singular) == len(units_plural)
        self._group = group
        self._description = description
        self._units_singular = units_singular
        self._units_plural = units_plural
        self._nr_values = len(units_singular)
        self._values = []
        for _index in range(0, self._nr_values):
            self._values.append(0)
        group.add_member(self)

    def add(self, add_values):
        assert isinstance(add_values, list)
        assert len(add_values) == len(self._values)
        self._values = list(map(operator.add, self._values, add_values))

    def description(self):
        return self._description

    def is_zero(self):
        for count in self._values:
            if count:
                return False
        return True

    def value_display_str(self):
        value_strs = []
        for index, value in enumerate(self._values):
            if value == 1:
                value_str = str(value) + ' ' + self._units_singular[index]
            else:
                value_str = str(value) + ' ' + self._units_plural[index]
            value_strs.append(value_str)
        return ", ".join(value_strs)
