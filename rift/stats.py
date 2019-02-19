import operator
import time

import collections
import table

RATE_HISTORY = 10            # Look at up to last N samples to calculate "recent rate"

TIME_FUNCTION = time.time    # So that we can stub it for unit testing

def secs_to_dmhs_str(secs):
    mins = 0
    hours = 0
    days = 0
    if secs >= 60.0:
        mins = int(secs / 60.0)
        secs -= mins * 60.0
    if mins >= 60:
        hours = mins // 60
        mins %= 60
    if hours >= 24:
        days = hours // 24
        hours %= 24
    return "{:d}d {:02d}h:{:02d}m:{:05.2f}s".format(days, hours, mins, secs)

class Group:

    def __init__(self):
        self._stats = []

    def add_stat(self, stat):
        self._stats.append(stat)

    def clear(self):
        for stat in self._stats:
            stat.clear()

    def table(self, exclude_zero):
        tab = table.Table()
        tab.add_row([
            "Description",
            "Value",
            ["Last Rate", "Over Last {} Changes".format(RATE_HISTORY)],
            ["Last Change"]
        ])
        for stat in self._stats:
            if not exclude_zero or not stat.is_zero():
                tab.add_row([
                    stat.description(),
                    stat.value_display_str(),
                    stat.rate_display_str(),
                    stat.last_change_display_str()
                ])
        return tab

class StatBase:

    def __init__(self, group, description, units_singular, units_plural, sum_counters):
        self._group = group
        self._description = description
        self._units_singular = units_singular
        if group is not None:
            group.add_stat(self)
        assert isinstance(units_singular, list)
        if units_plural is None:
            units_plural = list(map(lambda word: word + 's', units_singular))
        assert isinstance(units_plural, list)
        assert len(units_singular) == len(units_plural)
        self._units_singular = units_singular
        self._units_plural = units_plural
        self._nr_values = len(self._units_singular)
        if sum_counters is None:
            self._sum_counters = []
        else:
            self._sum_counters = sum_counters
        self.clear()

    def clear(self):
        self._values = [0] * self._nr_values
        self._samples = collections.deque([], RATE_HISTORY)

    def add_to_group(self, group):
        # This is to allow sum counters to be created first, and added to a group later so that
        # they appear at the desired row in the group table.
        assert group is not None
        assert self._group is None
        self._group = group
        group.add_stat(self)

    def add_values(self, add_values):
        assert isinstance(add_values, list)
        assert len(add_values) == len(self._values)
        # pylint:disable=attribute-defined-outside-init
        self._values = list(map(operator.add, self._values, add_values))
        sample = (TIME_FUNCTION(), self._values)
        self._samples.append(sample)
        for sum_counter in self._sum_counters:
            sum_counter.add_values(add_values)

    def is_zero(self):
        return all(value == 0 for value in self._values)

    def description(self):
        return self._description

    def value_display_str(self):
        value_strs = []
        for index, value in enumerate(self._values):
            if value == 1:
                value_str = str(value) + ' ' + self._units_singular[index]
            else:
                value_str = str(value) + ' ' + self._units_plural[index]
            value_strs.append(value_str)
        return ", ".join(value_strs)

    def rate_display_str(self):
        # pylint:disable=too-many-locals
        nr_samples = len(self._samples)
        if nr_samples < 2:
            return ''
        (oldest_sample_time, oldest_sample_values) = self._samples[0]
        (newest_sample_time, newest_sample_values) = self._samples[-1]
        assert len(oldest_sample_values) == len(newest_sample_values)
        assert len(oldest_sample_values) >= 1
        time_diff = newest_sample_time - oldest_sample_time
        assert time_diff >= 0.0
        rate_strs = []
        zipped_list = zip(oldest_sample_values, newest_sample_values, self._units_plural)
        for oldest_sample_value, newest_sample_value, unit in zipped_list:
            value_diff = newest_sample_value - oldest_sample_value
            if time_diff == 0.0:
                rate_str = "Infinite {}/Sec".format(unit)
            else:
                rate = value_diff / time_diff
                rate_str = "{:.2f} {}/Sec".format(rate, unit)
            rate_strs.append(rate_str)
        return ", ".join(rate_strs)

    def last_change_display_str(self):
        if not self._samples:
            return ''
        (newest_sample_time, _) = self._samples[-1]
        secs = TIME_FUNCTION() - newest_sample_time
        return secs_to_dmhs_str(secs)

class MultiCounter(StatBase):

    def __init__(self, group, description, units_singular, units_plural=None, sum_counters=None):
        StatBase.__init__(self, group, description, units_singular, units_plural, sum_counters)

    def add(self, add_values):
        self.add_values(add_values)

class Counter(StatBase):

    def __init__(self, group, description, unit_singular, unit_plural=None, sum_counters=None):
        if unit_plural is None:
            units_plural = None
        else:
            units_plural = [unit_plural]
        StatBase.__init__(self, group, description, [unit_singular], units_plural, sum_counters)

    def add(self, add_value):
        self.add_values([add_value])

    def increase(self):
        self.add_values([1])
