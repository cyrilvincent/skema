from collections import OrderedDict

from indexer import Indexer
import time


class CommuneService:

    def __init__(self, limit=20):
        self.limit = limit
        self.ix = Indexer()
        self.ix.start()

    def find(self, q: str) -> list[tuple[str, str]]:
        q = self.ix.normalize_string(q)
        if q not in self.ix.db:
            return []
        res = self.ix.db[q]
        res = OrderedDict(sorted(res.items(), key=lambda v: len(v[1]) if v[1].startswith(q) else 99+len(v[1])))
        return list(res.items())[:self.limit]


if __name__ == '__main__':
    s = CommuneService()
    time.sleep(1)
    print(s.find("LANS"))
    print(s.find("38250"))
    print(s.find("Vercors"))
    print(s.find("Y"))
    print(s.find("DE"))

