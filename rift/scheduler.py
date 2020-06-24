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
            if timeout:
                start_time = time.monotonic()
            rx_ready, _, _ = select.select(self._rx_fds, [], [], timeout)
            if timeout:
                actual_select_time = time.monotonic() - start_time
                if actual_select_time > timeout:
                    slip_time = start_time - timeout
                    if slip_time > 0.01:
                        self.slip_count_10ms += 1
                    if slip_time > 0.1:
                        self.slip_count_100ms += 1
                    if slip_time > 1.0:
                        self.slip_count_1000ms += 1
            for rx_fd in rx_ready:
                ###@@@vvv
                start_time = time.monotonic()
                ###@@@^^^
                handler = self._handlers_by_rx_fd[rx_fd]
                handler.ready_to_read()
                ###@@@vvv
                read_time = time.monotonic() - start_time
                if read_time > 1.0:
                    print("LONG READ TIME:", read_time)
                ###@@@^^^


SCHEDULER = Scheduler()
