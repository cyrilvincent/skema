import threading
import time


class ChargeManager:
    _instance = None
    lock = threading.RLock()

    def __init__(self):
        self.time0 = time.perf_counter()
        self.total_seconds = 0.

    def total_duration(self) -> float:
        duration = time.perf_counter() - self.time0
        return duration

    def start(self) -> float:
        return time.perf_counter()

    def stop(self, start: float) -> float:
        duration = time.perf_counter() - start
        with ChargeManager.lock:
            self.total_seconds += duration
        return duration


    @staticmethod
    def factory():
        with ChargeManager.lock:
            if ChargeManager._instance is None:
                ChargeManager._instance = ChargeManager()
        return ChargeManager._instance


if __name__ == '__main__':
    m = ChargeManager.factory()
    start = m.start()
    time.sleep(1)
    duration = m.stop(start)
    print(duration, m.total_seconds)
    start = m.start()
    time.sleep(2)
    duration = m.stop(start)
    print(duration, m.total_seconds)
