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

    def register_handler(self, handler):
        rx_fd = handler.rx_fd()
        self._handlers_by_rx_fd[rx_fd] = handler
        self._rx_fds.append(rx_fd)

    def unregister_handler(self, handler):
        rx_fd = handler.rx_fd()
        del self._handlers_by_rx_fd[rx_fd]
        self._rx_fds.remove(rx_fd)

    def run(self):
        while True:
            # This needs to be a loop because processing an event can create a timer and processing
            # an expired timer can create an event.
            while Fsm.events_pending() or TIMER_SCHEDULER.expired_timers_pending():
                Fsm.process_queued_events()
                timeout = TIMER_SCHEDULER.trigger_all_expired_timers()
            # Wait for ready to read or expired timer
            start_time = time.monotonic()
            rx_ready, _, _ = select.select(self._rx_fds, [], [], timeout)
            # Check for timer slips
            if timeout:
                duration = time.monotonic() - start_time
                slip_time = duration - timeout
                if slip_time > 0.01:
                    self.slip_count_10ms += 1
                if slip_time > 0.1:
                    self.slip_count_100ms += 1
                if slip_time > 1.0:
                    self.slip_count_1000ms += 1
            # Process all handlers that are ready to read
            for rx_fd in rx_ready:
                handler = self._handlers_by_rx_fd[rx_fd]
                handler.ready_to_read()

SCHEDULER = Scheduler()
