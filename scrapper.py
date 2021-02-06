import config
import requests
import loaders
import parsers
import sys
import time
import cyrilload

class AmeliScrapperService:

    def __init__(self, session, departments=list(range(1, 96)) + list(range(971, 977))):
        self.alphabet = "abcdefghijklmnopqrstuvwxyz".upper()
        self.departments = departments
        self.total = len(self.departments) * len(self.alphabet) ** 2
        self.i = 0
        self.nberror = 0
        self.nbrequest = 1
        self.session = session
        self.loader = loaders.AmeliLoader(session)
        self.page_loader = None
        self.details_loader = None
        self.db = {}

    def search_all(self):
        self.log("Search All", "", 0)
        for dept in self.departments:
            self.log("Search by dept", "", dept)
            self.search_by_dept(dept)
        cyrilload.save(self.db, "ameli", str(dept), "jsonpickle")
        cyrilload.save(self.db, "ameli", str(dept), "pickle")

    def search_by_dept(self, dept):
        for s1 in self.alphabet:
            for s2 in self.alphabet:
                q = s1+s2
                self.search_by_query_dept(q, dept)
                self.i+=1

    def search_by_query_dept(self, q, dept):
        self.log(f"Search {q}", q, dept)
        res = self.loader.post(q, dept)
        self.nbrequest += 1
        if self.loader.ok and res:
            page = 1
            nbpage = 1
            while page <= nbpage:
                self.log(f"Load page", q, dept, page, nbpage)
                self.page_loader = loaders.AmeliPageLoader(self.session, page)
                self.page_loader.load(config.nbtry * 2)
                self.nbrequest += 1
                if self.page_loader.ok:
                    parser = parsers.AmeliPageParser(self.page_loader.html)
                    parser.soups()
                    if nbpage == 1:
                        nbpage = parser.nbpage
                    # self._details(parser.items, q, dept, page, nbpage)
                    self._low_details(parser.entities, dept)
                else:
                    self.error(self.page_loader.url)
                    self.nberror += 19
                page += 1
        elif not self.loader.ok:
            self.error(self.loader.url)

    # def _details(self, items, q, dept, page, nbpage):
    #     for id in items.keys():
    #         if id not in self.db:
    #             self.log(f"Load {items[id]}@{id}", q, dept, page, nbpage)
    #             self.details_loader = loaders.AmeliDetailsLoader(self.session, id)
    #             self.details_loader.load()
    #             if self.details_loader.ok:
    #                 parser = parsers.AmeliDetailsParser(self.details_loader.html)
    #                 parser.soups()
    #                 entity = Entity(id, items[id], dept)
    #                 entity.phone = parser.phone
    #                 entity.convention = parser.convention
    #                 self.db[id] = entity
    #             else:
    #                 self.error(self.details_loader.url)

    def _low_details(self, items, dept):
        for id in items.keys():
            if id not in self.db:
                entity = items[id]
                entity.dept = dept
                self.db[id] = entity

    def log(self, msg, q, dept, page=1, nbpage=1):
        span = time.perf_counter() - zero_time + 1e-5
        s = f"{len(self.db)}({(self.i / self.total) * 100:.1f}% in {span:.1f}s @{self.nbrequest / span:.1f}p/s) "
        if self.nberror > 0:
            s+= f"Errors:{self.nberror} "
        s += f"Search:{q}-{dept:02d} "
        s += f"Page:{page}/{nbpage} "
        s += f" {msg} "
        print(s)

    def error(self, msg):
        self.nberror += 1
        print(f"ERROR: {msg}")


if __name__ == '__main__':

    print("Ameli Scrapper")
    print("==============")
    print(f"V{config.version}")
    print()

    print("Test Internet: ", end="")
    with requests.Session() as session:
        loader = loaders.GoogleLoader(session)
        loader.load()
        if loader.ok:
            print("OK")
        else:
            print(loader.response)
            sys.exit(1)
        service = AmeliScrapperService(session, [38])
        print("Test Ameli: ", end="")
        service.loader.load()
        if service.loader.ok:
            print("OK")
        else:
            print("NOK")
            sys.exit(2)
        zero_time = time.perf_counter()
        service.search_all()

        # 10%38 = 300s
        # All = 30000s = 8h
        # 38 = 3000s = 50min





