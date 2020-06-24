import time
import sortedcontainers

class TimerScheduler:

    def __init__(self):
        self._timers_by_expire_time = sortedcontainers.SortedDict()

    def now(self):
        return time.time()

    def schedule(self, timer):
        expire_time = timer.expire_time()
        assert expire_time is not None
        if expire_time in self._timers_by_expire_time:
            self._timers_by_expire_time[expire_time].append(timer)
        else:
            self._timers_by_expire_time[expire_time] = [timer]

    def unschedule(self, timer):
        expire_time = timer.expire_time()
        assert expire_time is not None
        assert expire_time in self._timers_by_expire_time
        timers_with_matching_expire = self._timers_by_expire_time[expire_time]
        assert timer in timers_with_matching_expire
        timers_with_matching_expire.remove(timer)
        if timers_with_matching_expire == []:
            self._timers_by_expire_time.pop(expire_time)

    def expired_timers_pending(self):
        if not self._timers_by_expire_time:
            return False
        now = self.now()
        next_expire_time = self._timers_by_expire_time.peekitem(0)[0]
        if next_expire_time > now:
            return False
        return True

    def trigger_all_expired_timers(self):
        # Trigger all expired timers and return time until next expire
        now = self.now()
        while True:
            if not self._timers_by_expire_time:
                return None
            next_expire_time = self._timers_by_expire_time.peekitem(0)[0]
            if next_expire_time > now:
                return next_expire_time - now
            expired_timers = self._timers_by_expire_time.popitem(0)[1]
            for timer in expired_timers:
                timer.trigger_expire()

    def stop_all_timers(self):
        while self._timers_by_expire_time:
            timers = self._timers_by_expire_time.peekitem(0)[1]
            for timer in timers:
                timer.stop()

TIMER_SCHEDULER = TimerScheduler()

class Timer:

    def __init__(self, interval, expire_function, periodic=True, start=True):
        self._running = False
        self._periodic = periodic
        self._interval = interval
        self._expire_time = None
        self._expire_function = expire_function
        if start:
            self.start()

    def __del__(self):
        self.stop()

    def running(self):
        return self._running

    def interval(self):
        return self._interval

    def expire_time(self):
        return self._expire_time

    def remaining_time_str(self):
        if self._running:
            secs_left = self._expire_time - TIMER_SCHEDULER.now()
            return "{:06f} secs".format(secs_left)
        else:
            return "Stopped"

    def start(self):
        if self._running:
            self.stop()
        self._running = True
        self._expire_time = TIMER_SCHEDULER.now() + self._interval
        TIMER_SCHEDULER.schedule(self)

    def stop(self):
        if self._running:
            TIMER_SCHEDULER.unschedule(self)
            self._running = False
            self._expire_time = None

    def trigger_expire(self):
        if self._expire_function is not None:
            self._expire_function()
        if self._periodic:
            # Next expire is not now + interval but current expire_time + interval because the
            # expire function may be called too late when the system is busy, in which case we
            # try to catch up.
            self._expire_time += self._interval
            TIMER_SCHEDULER.schedule(self)
        else:
            self._running = False
            self._expire_time = None
