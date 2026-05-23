import datetime
import threading
import time


class ChargeManager:
    _instance = None
    lock = threading.RLock()

    def __init__(self, interval):
        self.time0 = datetime.datetime.now().timestamp()
        self.interval = interval
        self.mesures: list[tuple[float, float]] = [(0, 0)]

    @staticmethod
    def factory(interval=600):
        with ChargeManager.lock:
            if ChargeManager._instance is None:
                ChargeManager._instance = ChargeManager(interval)
        return ChargeManager._instance

    def start(self) -> float:
        return datetime.datetime.now().timestamp() - self.time0

    def stop(self, start: float) -> float:
        try:
            duration = self.start() - start
            with ChargeManager.lock:
                self.mesures.append((int(datetime.datetime.now().timestamp() - self.time0), duration))
            self._remove_old_mesures(self.interval)
            return duration
        except:
            return 0

    def _remove_old_mesures(self, interval: int):
        if len(self.mesures) > 0:
            last = self.mesures[-1][0]
            filtered = [m for m in self.mesures if m[0] > last - interval][:10000]
            with ChargeManager.lock:
                self.mesures = filtered

    @property
    def charge(self) -> int:
        try:
            res = (m[1] for m in self.mesures)
            return int(sum(res))
        except:
            return 0

    @property
    def charge_pc(self) -> int:
        try:
            res = (m[1] for m in self.mesures)
            return int(sum(res) * 100 / self.interval)
        except:
            return 0

    @property
    def req_min(self) -> int:
        try:
            return int(len(self.mesures) * 60 / self.interval)
        except:
            return 0

    @property
    def last_charge(self) -> int:
        try:
            if len(self.mesures) > 0:
                return int(self.mesures[-1][1])
            return 0
        except:
            return 0


if __name__ == '__main__':
    m = ChargeManager.factory(8)
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
    print(m.charge, m.req_min, m.last_charge)
    m.mesures = []
    print(m.charge, m.req_min, m.last_charge)
    start = m.start()
    m.stop(start)
    print(m.mesures)

