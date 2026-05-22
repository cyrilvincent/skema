import datetime
import threading
import time

class ChargeManager:
    _instance = None
    lock = threading.RLock()

    def __init__(self):
        self.time0 = datetime.datetime.now().timestamp()
        self.interval = 600
        self.mesures: list[tuple[float, float]] = [(0, 0)]

    def start(self) -> float:
        return datetime.datetime.now().timestamp() - self.time0

    def stop(self, start: float) -> float:
        duration = self.start() - start
        if duration > 0.1:
            with ChargeManager.lock:
                self.mesures.append((int(datetime.datetime.now().timestamp() - self.time0), duration))
            self._remove_old_mesures(self.interval)
        return duration

    def _remove_old_mesures(self, interval: int):
        last = self.mesures[-1][0]
        filtered = [m for m in self.mesures if m[0] > last - interval][:10000]
        with ChargeManager.lock:
            self.mesures = filtered

    @property
    def charge(self) -> int:
        res = (m[1] for m in self.mesures)
        return int(sum(res))

    @property
    def charge_pc(self) -> int:
        res = (m[1] for m in self.mesures)
        return int(sum(res) / self.interval)

    @property
    def req_min(self) -> int:
        return int(len(self.mesures) * 60 / self.interval)




    @staticmethod
    def factory():
        with ChargeManager.lock:
            if ChargeManager._instance is None:
                ChargeManager._instance = ChargeManager()
        return ChargeManager._instance


if __name__ == '__main__':
    m = ChargeManager.factory()
    m.interval = 8
    start = m.start()
    time.sleep(1)
    duration = m.stop(start)
    print(duration, m.charge, m.mesures)
    start = m.start()
    time.sleep(2)
    duration = m.stop(start)
    print(duration, m.charge, m.mesures)
    start = m.start()
    time.sleep(0.01)
    duration = m.stop(start)
    print(duration, m.charge, m.mesures)
    start = m.start()
    time.sleep(0.2)
    duration = m.stop(start)
    print(duration, m.charge, m.mesures)
    start = m.start()
    time.sleep(4)
    duration = m.stop(start)
    print(duration, m.charge, m.mesures)
    start = m.start()
    time.sleep(6)
    duration = m.stop(start)
    print(duration, m.charge, m.mesures)
    for _ in range(10):
        start = m.start()
        time.sleep(1)
        for __ in range(10000):
            m.mesures.append((0, 0))
        duration = m.stop(start)
        print(duration, m.charge, m.mesures)

