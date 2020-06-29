import select
import time
from timer import TIMER_SCHEDULER
from fsm import Fsm

class Scheduler:

    def __init__(self):
        self._handlers_by_rx_fd = {}
        self._rx_fds = []
        self.slip_count_10ms = 0
        self.slip_count_100ms = 0
        self.slip_count_1000ms = 0
        self.max_pending_events_proc_time = 0.0
        self.max_expired_timers_proc_time = 0.0
        self.max_select_proc_time = 0.0
        self.max_ready_to_read_proc_time = 0.0

    def register_handler(self, handler):
        rx_fd = handler.rx_fd()
        self._handlers_by_rx_fd[rx_fd] = handler
        self._rx_fds.append(rx_fd)

    def unregister_handler(self, handler):
        rx_fd = handler.rx_fd()
        if rx_fd is not None and rx_fd in self._handlers_by_rx_fd:
            del self._handlers_by_rx_fd[rx_fd]
            self._rx_fds.remove(rx_fd)

    def run(self):
        while True:
            # This needs to be a loop because processing an event can create a timer and processing
            # an expired timer can create an event.
            while Fsm.events_pending() or TIMER_SCHEDULER.expired_timers_pending():
                # Process all queued events
                start_time = time.monotonic()
                Fsm.process_queued_events()
                duration = time.monotonic() - start_time
                self.max_pending_events_proc_time = max(self.max_pending_events_proc_time, duration)
                # Process all expired timers
                start_time = time.monotonic()
                timeout = TIMER_SCHEDULER.trigger_all_expired_timers()
                duration = time.monotonic() - start_time
                self.max_expired_timers_proc_time = max(self.max_expired_timers_proc_time, duration)
            # Wait for ready to read or expired timer
            start_time = time.monotonic()
            rx_ready, _, _ = select.select(self._rx_fds, [], [], timeout)
            duration = time.monotonic() - start_time
            self.max_select_proc_time = max(self.max_select_proc_time, duration)
            # Check for timer slips
            if timeout is not None:
                slip_time = duration - timeout
                if slip_time > 0.01:
                    self.slip_count_10ms += 1
                if slip_time > 0.1:
                    self.slip_count_100ms += 1
                if slip_time > 1.0:
                    self.slip_count_1000ms += 1
            # Process all handlers that are ready to read
            for rx_fd in rx_ready:
                start_time = time.monotonic()
                handler = self._handlers_by_rx_fd[rx_fd]
                handler.ready_to_read()
                duration = time.monotonic() - start_time
                self.max_ready_to_read_proc_time = max(self.max_ready_to_read_proc_time, duration)

SCHEDULER = Scheduler()
