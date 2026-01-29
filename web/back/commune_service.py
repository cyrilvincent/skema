from collections import OrderedDict
import threading
from indexer import Indexer
import time


class CommuneService:

    _instance = None
    lock = threading.RLock()

    def __init__(self, limit=30):
        self.limit = limit
        self.ix = Indexer.factory()
        self.cscores = {"CC": 0, "CR": 5, "CD": 2, "CE": 20, "CA": 50, "CP": 99, "CF": 15}

    @staticmethod
    def factory():
        with CommuneService.lock:
            if CommuneService._instance is None:
                CommuneService._instance = CommuneService()
        return CommuneService._instance

    def score(self, q: str, v: tuple[str, str]) -> int:
        score = len(v[1])
        if not v[1].startswith(q):
            score += 99
        score += self.cscores[v[0][:2]]
        if len(q) == 2 and q.isdigit() and v[0][:2] == "CD":
            score = 1
        if len(q) == 5 and q.isdigit() and v[0][:2] in ["CC", "CP"]:
            score = 0
        return score

    def find(self, q: str) -> list[tuple[str, str]]:
        q = self.ix.normalize_string(q.strip())
        if q not in self.ix.db:
            return []
        res = self.ix.db[q]
        res = OrderedDict(sorted(res.items(), key=lambda v: self.score(q, v)))
        return list(res.items())[:self.limit]


if __name__ == '__main__':
    s = CommuneService()
    time.sleep(1)
    print(s.find("LANS"))
    print(s.find("38250"))
    print(s.find("Vercors"))
    print(s.find("Y"))
    print(s.find("DE"))
    print(s.find("FRANCE"))

