from collections import OrderedDict

from indexer import Indexer
import time


class CommuneService:

    def __init__(self, limit=10):
        self.limit = limit
        self.ix = Indexer()
        self.ix.start()
        self.cscores = {"CC": 0, "CR": 10, "CD": 2, "CE": 20, "CA": 50, "CP": 15}

    def score(self, q: str, v: tuple[str, str]) -> int:
        score = len(v[1])
        if not v[1].startswith(q):
            score += 99
        score += self.cscores[v[0][:2]]
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

