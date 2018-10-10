import re
import time

import pytest

import timer

# pylint: disable=redefined-outer-name
@pytest.fixture
def context():

    class Context:

        def __init__(self):
            # Make sure there are no timers running from previous tests
            timer.TIMER_SCHEDULER.stop_all_timers()
            self.clear_counters()

        def clear_counters(self):
            self.timer1_expired_count = 0
            self.timer2_expired_count = 0
            self.timer3_expired_count = 0
            self.timer4_expired_count = 0
            self.timer5_expired_count = 0

        def timer1_expired(self):
            self.timer1_expired_count += 1

        def timer2_expired(self):
            self.timer2_expired_count += 1

        def timer3_expired(self):
            self.timer3_expired_count += 1

        def timer4_expired(self):
            self.timer4_expired_count += 1

        def timer5_expired(self):
            self.timer5_expired_count += 1

    context = Context()
    yield context

    timer.TIMER_SCHEDULER.stop_all_timers()

def test_periodic(context):
    # Timer1: interval 0.8 sec (expires 2x in 2.0 sec), started in constructor
    # Rely on default values for periodic and start parameters
    _timer1 = timer.Timer(
        interval=0.8,
        expire_function=context.timer1_expired)
    # Timer2: interval 2.2 sec (expires 0x in 2.0 sec), started outside constructor
    timer2 = timer.Timer(
        interval=2.2,
        expire_function=context.timer2_expired,
        periodic=True,
        start=False)
    timer2.start()
    # Timer3: interval 2.4 sec (expires 0x in 2.0 sec), started in constructor
    _timer3 = timer.Timer(
        interval=2.4,
        expire_function=context.timer3_expired,
        periodic=True,
        start=True)
    # Timer4: interval 0.8 sec (same as timer1, expires 2x in 2.0 sec), started outside constructor
    timer4 = timer.Timer(
        interval=0.8,
        expire_function=context.timer4_expired,
        periodic=True,
        start=False)
    timer4.start()
    # Timer5: interval 1.9 sec (expires 1x in 2.0 sec), started in constructor
    _timer5 = timer.Timer(
        interval=1.9,
        expire_function=context.timer5_expired,
        periodic=True,
        start=True)
    time.sleep(2.0)
    # Now is 2.0
    timer.TIMER_SCHEDULER.trigger_all_expired_timers()
    assert context.timer1_expired_count == 2   # Expired at 0.8 and 1.6, next at 2.4
    assert context.timer2_expired_count == 0   # No expiry, next at 2.2
    assert context.timer3_expired_count == 0   # No expiry, next at 2.4
    assert context.timer4_expired_count == 2   # Expired at 0.8 and 1.6, next at 2.4
    assert context.timer5_expired_count == 1   # Expired at 1.9, next at 3.8
    time.sleep(1.5)
    # Now is 3.4
    context.clear_counters()
    timer.TIMER_SCHEDULER.trigger_all_expired_timers()
    assert context.timer1_expired_count == 2   # Expired at 2.4 and 3.2, next at 4.0
    assert context.timer2_expired_count == 1   # Expired at 2.2, next at 4.4
    assert context.timer3_expired_count == 1   # Expired at 2.4, next at 4.8
    assert context.timer4_expired_count == 2   # Expired at 2.4 and 3.2, next at 4.0
    assert context.timer5_expired_count == 0   # Did not expire, next at 3.8

def test_oneshot(context):
    # Timer1: interval 0.8 sec (expires 1x in 2.0 sec), started in constructor
    # Rely on default values for start parameter
    _timer1 = timer.Timer(
        interval=0.8,
        expire_function=context.timer1_expired,
        periodic=False)
    # Timer2: interval 2.2 sec (expires 0x in 2.0 sec), started outside constructor
    timer2 = timer.Timer(
        interval=2.2,
        expire_function=context.timer1_expired,
        periodic=False,
        start=False)
    timer2.start()
    # Timer3: interval 2.5 sec (expires 0x in 2.0 sec), never started
    _timer3 = timer.Timer(
        interval=2.5,
        expire_function=context.timer3_expired,
        periodic=False,
        start=False)
    # Timer4: interval 0.8 sec (same as timer1, expires 1x in 2.0 sec), started outside constructor
    timer4 = timer.Timer(
        interval=0.8,
        expire_function=context.timer4_expired,
        periodic=False,
        start=False)
    timer4.start()
    # Timer5: interval 1.4 sec (expires 1x in 2.0 sec), not started
    _timer5 = timer.Timer(
        interval=1.4,
        expire_function=context.timer5_expired,
        periodic=False,
        start=False)
    time.sleep(2.0)
    timer.TIMER_SCHEDULER.trigger_all_expired_timers()
    assert context.timer1_expired_count == 1
    assert context.timer2_expired_count == 0
    assert context.timer3_expired_count == 0
    assert context.timer4_expired_count == 1
    assert context.timer5_expired_count == 0

def test_start_stop(context):
    # Timer1: interval 0.8 sec (expires 2x in 2.0 sec), started in constructor
    timer1 = timer.Timer(
        interval=0.8,
        expire_function=context.timer1_expired)
    # Start timer1 when it is already running
    timer1.start()
    # Timer1: one-shot interval 0.6 sec (expires 3x in 2.0 sec), started outside constructor
    timer2 = timer.Timer(
        interval=0.6,
        expire_function=context.timer2_expired,
        periodic=True,
        start=False)
    timer2.start()
    # Timer3: one-shot interval 0.8 sec (expires 1x in 2.0 sec), started in constructor
    timer3 = timer.Timer(
        interval=0.8,
        expire_function=context.timer3_expired,
        periodic=True,
        start=True)
    # Stop timer3 (will not expire)
    timer3.stop()
    time.sleep(2.0)
    timer.TIMER_SCHEDULER.trigger_all_expired_timers()
    assert context.timer1_expired_count == 2
    assert context.timer2_expired_count == 3
    assert context.timer3_expired_count == 0

def test_remaining_time(context):
    # Haven't created any timers yet
    time_to_next_expire = timer.TIMER_SCHEDULER.trigger_all_expired_timers()
    assert time_to_next_expire is None
    # Timer1: periodic interval 0.8 sec
    timer1 = timer.Timer(
        interval=0.8,
        expire_function=context.timer1_expired)
    # Timer2: one-shot interval 0.8 sec
    _timer2 = timer.Timer(
        interval=0.8,
        expire_function=context.timer2_expired,
        periodic=False)
    time.sleep(2.0)
    # Now is 2.0
    time_to_next_expire = timer.TIMER_SCHEDULER.trigger_all_expired_timers()
    assert context.timer1_expired_count == 2   # Expired at 0.8 and 1.6. Next expiry at 2.4
    assert context.timer2_expired_count == 1   # Expired at 0.8. No next expiry.
    assert time_to_next_expire == pytest.approx(0.4, abs=0.1)
    time.sleep(0.5)
    # Now is 2.5
    context.clear_counters()
    time_to_next_expire = timer.TIMER_SCHEDULER.trigger_all_expired_timers()
    assert context.timer1_expired_count == 1   # Expired at 2.4. Next expiry at 3.2.
    assert context.timer2_expired_count == 0   # Not running.
    assert time_to_next_expire == pytest.approx(0.7, abs=0.1)
    # Stop timer1. At this point no timer is running, so there no time_to_next_expire.
    timer1.stop()
    time_to_next_expire = timer.TIMER_SCHEDULER.trigger_all_expired_timers()
    assert time_to_next_expire is None
    time.sleep(1.0)
    context.clear_counters()
    time_to_next_expire = timer.TIMER_SCHEDULER.trigger_all_expired_timers()
    assert time_to_next_expire is None
    assert context.timer1_expired_count == 0  # Not running
    assert context.timer2_expired_count == 0  # Not running

def test_attributes(context):
    # Timer1: periodic interval 0.8 sec
    timer1 = timer.Timer(
        interval=0.8,
        expire_function=context.timer1_expired)
    # Timer2: one-shot interval 0.7 sec
    timer2 = timer.Timer(
        interval=0.7,
        expire_function=context.timer2_expired,
        periodic=False)
    assert timer1.running() is True
    assert timer1.interval() == pytest.approx(0.8)
    assert re.match(r"0\.[0-9][0-9][0-9][0-9][0-9][0-9] secs", timer1.remaining_time_str())
    assert timer2.running() is True
    assert timer2.interval() == pytest.approx(0.7)
    assert re.match(r"0\.[0-9][0-9][0-9][0-9][0-9][0-9] secs", timer2.remaining_time_str())
    time.sleep(1.0)
    timer.TIMER_SCHEDULER.trigger_all_expired_timers()
    assert timer1.running() is True
    assert timer1.interval() == pytest.approx(0.8)
    assert re.match(r"0\.[0-9][0-9][0-9][0-9][0-9][0-9] secs", timer1.remaining_time_str())
    assert timer2.running() is False
    assert timer2.interval() == pytest.approx(0.7)
    assert timer2.remaining_time_str() == "Stopped"
