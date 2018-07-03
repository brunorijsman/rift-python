import select 
from timer import timer_scheduler

class SocketScheduler:

    def __init__(self):
        self._handlers_by_fd = {}
        self._sockets = []

    def register_handler(self, handler):
        self._handlers_by_fd[handler.socket().fileno()] = handler
        self._sockets.append(handler.socket())

    def unregister_handler(self, handler):
        del self._handlers_by_fd[handler.socket().fileno()]
        self._sockets.remove(handler.socket())

    def run(self):
        while True:
            timeout = timer_scheduler.trigger_all_expired_timers_and_return_time_until_next_expire()
            rx_ready, tx_ready, _ = select.select(self._sockets, self._sockets, [], timeout)
            for sock in rx_ready:
                handler = self._handlers_by_fd[sock.fileno()]
                handler.ready_to_read()
            for sock in tx_ready:
                handler = self._handlers_by_fd[sock.fileno()]
                handler.ready_to_write()

socket_scheduler = SocketScheduler()