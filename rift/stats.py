import operator
import time

import table
import utils

RATE_HISTORY_SECS = 10       # Compute the rate of the past 10 seconds

TIME_FUNCTION = time.time    # So that we can stub it for unit testing

class Group:

    def __init__(self, sum_group=None):
        self._stats = []
        self._sum_group = sum_group

    def add_stat(self, stat):
        self._stats.append(stat)
        if self._sum_group:
            # pylint:disable=protected-access
            sum_stat = self._sum_group.find_stat_by_description(stat._description)
            if sum_stat:
                assert sum_stat._units_singular == stat._units_singular
                assert sum_stat._units_plural == stat._units_plural
            else:
                sum_stat = stat.standalone_copy()
                sum_stat._sum_stats = []
                self._sum_group.add_stat(sum_stat)
            stat.add_sum_stat(sum_stat)

    def clear(self):
        for stat in self._stats:
            stat.clear()

    def find_stat_by_description(self, description):
        for stat in self._stats:
            # pylint:disable=protected-access
            if stat._description == description:
                return stat
        return None

    def table(self, exclude_zero, sort_by_description=False):
        rows = []
        for stat in self._stats:
            if not exclude_zero or not stat.is_zero():
                rows.append([
                    stat.description(),
                    stat.value_display_str(),
                    stat.rate_display_str(),
                    stat.last_change_display_str()
                ])
        if sort_by_description:
            rows = sorted(rows, key=operator.itemgetter(0))
        tab = table.Table()
        tab.add_row([
            "Description",
            "Value",
            ["Rate Over", "Last {} Seconds".format(RATE_HISTORY_SECS)],
            ["Last Change"]
        ])
        tab.add_rows(rows)
        return tab

class StatBase:

    def __init__(self, group, description, units_singular, units_plural, sum_stats):
        self._group = group
        self._description = description
        self._units_singular = units_singular
        assert isinstance(units_singular, list)
        if units_plural is None:
            units_plural = list(map(lambda word: word + 's', units_singular))
        assert isinstance(units_plural, list)
        assert len(units_singular) == len(units_plural)
        self._units_plural = units_plural
        self._nr_values = len(self._units_singular)
        self._change_history_buckets = None
        self._last_shift_time = None
        self._last_change_time = None
        if sum_stats is None:
            self._sum_stats = []
        else:
            self._sum_stats = sum_stats
        self.clear()
        if group is not None:
            group.add_stat(self)

    def standalone_copy(self):
        return StatBase(None, self._description, self._units_singular, self._units_plural, None)

    def clear(self):
        # Current values.
        zero_values = [0] * self._nr_values
        self._values = zero_values
        self._last_change_time = None
        # To compute the rates of the values, we keep a list of "history buckets" that contain the
        # recent value deltas per second. There is one history bucket for the current partial
        # second in progress, and RATE_HISTORY_SECS additional buckets for completed full seconds.
        nr_buckets = RATE_HISTORY_SECS + 1
        self._change_history_buckets = [zero_values] * nr_buckets
        # Shift the history buckets every second. Rather that running a timer and actually doing
        # this every second, we "catch up" whenever we write to or read from the history buckets.
        self._last_shift_time = TIME_FUNCTION()

    def add_to_group(self, group):
        # This is to allow sum counters to be created first, and added to a group later so that
        # they appear at the desired row in the group table.
        assert group is not None
        assert self._group is None
        self._group = group
        group.add_stat(self)

    def add_sum_stat(self, sum_stat):
        self._sum_stats.append(sum_stat)

    def _shift_history_buckets_if_needed(self):
        now = TIME_FUNCTION()
        secs_since_last_shift = now - self._last_shift_time
        if secs_since_last_shift < 1.0:
            return
        nr_buckets = RATE_HISTORY_SECS + 1
        shift_nr_buckets = int(secs_since_last_shift)
        zero_values = [0] * self._nr_values
        if shift_nr_buckets >= nr_buckets:
            new_buckets = [zero_values] * nr_buckets
        else:
            keep_nr_buckets = nr_buckets - shift_nr_buckets
            keep_buckets = self._change_history_buckets[:keep_nr_buckets]
            pad_buckets = [zero_values] * shift_nr_buckets
            new_buckets = pad_buckets + keep_buckets
        self._change_history_buckets = new_buckets
        # Record the shift as having happened at the time that it was scheduled to happen, not
        # necessarily at the current time. This is needed to make the next shift happen at the
        # correct time.
        self._last_shift_time += float(shift_nr_buckets)

    def _record_change_in_history_buckets(self, add_values):
        self._shift_history_buckets_if_needed()
        self._change_history_buckets[0] = list(map(operator.add, self._change_history_buckets[0],
                                                   add_values))

    def add_values(self, add_values):
        assert isinstance(add_values, list)
        assert len(add_values) == len(self._values)
        # pylint:disable=attribute-defined-outside-init
        self._values = list(map(operator.add, self._values, add_values))
        self._record_change_in_history_buckets(add_values)
        for sum_stat in self._sum_stats:
            sum_stat.add_values(add_values)
        self._last_change_time = TIME_FUNCTION()

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
        self._shift_history_buckets_if_needed()
        # Add up the deltas over the last RATE_HISTORY_SECS but skip the "current second in
        # progress" because it is a partial second.
        sum_values = [0] * self._nr_values
        nr_buckets = RATE_HISTORY_SECS + 1
        for bnr in range(1, nr_buckets):
            sum_values = list(map(operator.add, sum_values, self._change_history_buckets[bnr]))
        count_to_rate = lambda count: float(count) / float(RATE_HISTORY_SECS)
        rate_values = list(map(count_to_rate, sum_values))
        rate_values_and_units = zip(rate_values, self._units_plural)
        rate_strs = ["{:.2f} {}/Sec".format(rate, unit) for (rate, unit) in rate_values_and_units]
        return ", ".join(rate_strs)

    def last_change_display_str(self):
        if self._last_change_time is None:
            return ''
        secs = TIME_FUNCTION() - self._last_change_time
        return utils.secs_to_dmhs_str(secs)

class MultiCounter(StatBase):

    def __init__(self, group, description, units_singular, units_plural=None, sum_counters=None):
        StatBase.__init__(self, group, description, units_singular, units_plural, sum_counters)

    def add(self, add_values):
        self.add_values(add_values)

    def values(self):
        return self._values

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

    def value(self):
        return self._values[0]
