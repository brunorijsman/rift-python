import select 
from timer import timer_scheduler

class SocketScheduler:

    def __init__(self):
        self._handlers_by_fd = {}
        self._rx_sockets = []
        self._tx_sockets = []

    def register_handler(self, handler, invoke_ready_to_read, invoke_ready_to_write):
        self._handlers_by_fd[handler.socket().fileno()] = handler
        if invoke_ready_to_read:
            self._rx_sockets.append(handler.socket())
        if invoke_ready_to_write:
            self._tx_sockets.append(handler.socket())

    def unregister_handler(self, handler):
        del self._handlers_by_fd[handler.socket().fileno()]
        sock = handler.socket()
        if sock in self._rx_sockets:
            self._rx_sockets.remove(sock)
        if sock in self._tx_sockets:
            self._tx_sockets.remove(sock)

    def run(self):
        while True:
            timeout = timer_scheduler.trigger_all_expired_timers_and_return_time_until_next_expire()
            rx_ready, tx_ready, _ = select.select(self._rx_sockets, self._tx_sockets, [], timeout)
            for sock in rx_ready:
                handler = self._handlers_by_fd[sock.fileno()]
                handler.ready_to_read()
            for sock in tx_ready:
                handler = self._handlers_by_fd[sock.fileno()]
                handler.ready_to_write()

socket_scheduler = SocketScheduler()