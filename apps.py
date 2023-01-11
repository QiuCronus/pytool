import abc
import signal
import time

__all__ = ["Application"]


class Signals(object):
    def __init__(self):
        self.recvd = []

        for name in ("SIGINT", "SIGTERM", "SIGHUP", "SIGQUIT", "SIGUSER1"):
            if not hasattr(signal, name):
                continue
            signal_ = getattr(signal, name)
            if signal_:
                signal.signal(signal_, self.handler)

    def handler(self, signal_, frame):
        if signal_ not in self.recvd:
            self.recvd.append(signal_)

    def check(self):
        if self.recvd:
            return self.recvd.pop(0)
        return None


class Application(object):
    def __init__(self):
        self.interrupted = False
        self.watchdog = Signals()

    def shutdown(self):
        self.interrupted = True

    @property
    def is_interrupted(self) -> bool:
        return self.interrupted

    def check_signals(self):
        signal_ = self.watchdog.check()
        if signal_:
            self.interrupted = True

    def run_forever(self):
        started, recovery = 0, 55
        while not self.interrupted:
            try:
                time.sleep(0.1)
            except Exception as err:
                self.handle_error(err)
                break

            self.check_signals()

            if int(time.time()) - started > recovery:
                try:
                    self.working()
                except Exception as err:
                    self.handle_error(err)
                finally:
                    started = int(time.time())

    @abc.abstractmethod
    def working(self):
        raise NotImplementedError

    @abc.abstractmethod
    def handle_error(self, error: Exception):
        pass
