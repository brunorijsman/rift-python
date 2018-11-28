import select
from timer import TIMER_SCHEDULER
from fsm import Fsm

class Scheduler:

    def __init__(self):
        self._handlers_by_rx_fd = {}
        self._handlers_by_tx_fd = {}
        self._rx_fds = []
        self._tx_fds = []

    def register_handler(self, handler, invoke_ready_to_read, invoke_ready_to_write):
        if invoke_ready_to_read:
            rx_fd = handler.rx_fd()
            self._handlers_by_rx_fd[rx_fd] = handler
            self._rx_fds.append(rx_fd)
        if invoke_ready_to_write:
            tx_fd = handler.tx_fd()
            self._handlers_by_tx_fd[tx_fd] = handler
            self._tx_fds.append(tx_fd)

    def unregister_handler(self, handler):
        if hasattr(handler, "rx_fd"):
            rx_fd = handler.rx_fd()
        else:
            rx_fd = None
        if rx_fd is not None and rx_fd in self._handlers_by_rx_fd:
            del self._handlers_by_rx_fd[rx_fd]
            self._rx_fds.remove(rx_fd)
        if hasattr(handler, "tx_fd"):
            tx_fd = handler.tx_fd()
        else:
            tx_fd = None
        if tx_fd is not None and tx_fd in self._handlers_by_tx_fd:
            del self._handlers_by_tx_fd[tx_fd]
            self._tx_fds.remove(tx_fd)

    def run(self):
        while True:
            # Process timers in two places because FSM event processing might cause timers to be
            # created, and timer expire processing might cause FSM events to be queued.
            timeout = TIMER_SCHEDULER.trigger_all_expired_timers()
            rx_ready, tx_ready, _ = select.select(self._rx_fds, self._tx_fds, [], timeout)
            for rx_fd in rx_ready:
                handler = self._handlers_by_rx_fd[rx_fd]
                handler.ready_to_read()
            for tx_fd in tx_ready:
                handler = self._handlers_by_tx_fd[tx_fd]
                handler.ready_to_write()
            TIMER_SCHEDULER.trigger_all_expired_timers()
            Fsm.process_queued_events()

SCHEDULER = Scheduler()
