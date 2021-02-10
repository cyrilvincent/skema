import config
import requests
import loaders
import parsers
import sys
import time
import cyrilload
import argparse


class AmeliScrapperService:

    def __init__(self, session, departments=None):
        if departments is None:
            departments = list(range(1, 20)) + list(range(21, 96)) + list(range(971, 977)) + ["2A", "2B"]
        self.alphabet = "abcdefghijklmnopqrstuvwxyz".upper()
        #self.alphabet = "ab".upper()
        self.departments = departments
        self.total = len(self.departments) * len(self.alphabet) ** 2
        self.i = 0
        self.nberror = 0
        self.totalerror = 0
        self.nbrequest = 1
        self.session = session
        self.loader = loaders.AmeliLoader(session)
        self.page_loader = None
        self.details_loader = None
        self.db = {}

    def strategy2d(self):
        self.log("Search All", "Strategy", "2")
        for dept in self.departments:
            dept = str(dept)
            if len(dept) < 2:
                dept = "0"+dept
            self.log("Search by dept", "All", dept)
            self.search_by_2letters_dept(dept)
            cyrilload.save(self.db, f"data/ameli-{dept}-{len(self.db)}-E{self.nberror}", method="pickle")
            cyrilload.save(self.db, f"data/ameli-{dept}-{len(self.db)}-E{self.nberror}", method="jsonpickle")
            self.db = {}
            self.totalerror += self.nberror
            self.nberror = 0

    def strategy3d(self):
        self.log("Search by dept", "Strategy", "3")
        len(self.departments) * len(self.alphabet) ** 3
        for dept in self.departments:
            dept = str(dept)
            if len(dept) < 2:
                dept = "0"+dept
            self.log("Search by dept", "All", dept)
            self.search_by_3letters_dept(dept)
            cyrilload.save(self.db, f"data/ameli-3-{dept}-{len(self.db)}-E{self.nberror}", method="pickle")
            self.db = {}
            self.totalerror += self.nberror
            self.nberror = 0

    def strategy4(self):
        self.total = len(self.alphabet) ** 4
        self.log("Search All", "Strategy", "4")
        for s1 in self.alphabet:
            for s2 in self.alphabet:
                for s3 in self.alphabet:
                    for s4 in self.alphabet:
                        q = s1 + s2 + s3 + s4
                        self.search_by_query_dept(q, "")
                        self.i += 1
        cyrilload.save(self.db, f"data/ameli-all4-{len(self.db)}-E{self.nberror}", method="pickle")
        self.totalerror = self.nberror

    def strategy3(self):
        self.total = len(self.alphabet) ** 3
        self.log("Search All", "Strategy", "3")
        for s1 in self.alphabet:
            for s2 in self.alphabet:
                for s3 in self.alphabet:
                    q = s1 + s2 + s3
                    self.search_by_query_dept(q, "")
                    self.i += 1
        cyrilload.save(self.db, f"data/ameli-all3-{len(self.db)}-E{self.nberror}", method="pickle")
        self.totalerror = self.nberror

    def strategy2(self):
        self.total = len(self.alphabet) ** 2
        self.log("Search All", "Strategy", "2")
        self.search_by_2letters_dept("")
        cyrilload.save(self.db, f"data/ameli-all2-{len(self.db)}-E{self.nberror}", method="pickle")
        self.totalerror = self.nberror

    def search_by_2letters_dept(self, dept):
        for s1 in self.alphabet:
            for s2 in self.alphabet:
                q = s1+s2
                self.search_by_query_dept(q, dept)
                self.i += 1

    def search_by_3letters_dept(self, dept):
        for s1 in self.alphabet:
            for s2 in self.alphabet:
                for s3 in self.alphabet:
                    q = s1+s2+s3
                    self.search_by_query_dept(q, dept)
                    self.i += 1

    def search_by_query_dept(self, q, dept, asc=True):
        self.log(f"Search {q}", q, dept)
        res = self.loader.post(q, dept)
        self.nbrequest += 1
        if self.loader.ok and res:
            page = 1
            nbpage = 1
            while page <= nbpage:
                self.page_loader = loaders.AmeliPageLoader(self.session, page)
                if asc:
                    self.log(f"Load page", q, dept, page, nbpage)
                    self.page_loader.load()
                else:
                    self.log(f"Load page desc", q, dept, page, nbpage)
                    self.page_loader.load_desc()
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
                page += 1
            if nbpage >= config.nbpage_limit and asc:
                self.search_by_query_dept(q, dept, False)
        elif not self.loader.ok:
            self.error(self.loader.url)

    def _low_details(self, items, dept):
        for id in items.keys():
            if id not in self.db:
                entity = items[id]
                entity.dept = dept
                self.db[id] = entity

    def log(self, msg, q, dept, page=1, nbpage=1):
        span = time.perf_counter() - zero_time + 1e-5
        s = f"{len(self.db)}({(self.i / self.total) * 100:.1f}% "
        if span < 3600:
            s += f"in {int(span)}s "
        else:
            s += f"in {int(span / 3600)}h{int((span % 3600) / 60)}m "
        s += f"@{self.nbrequest / span:.1f}p/s) "
        if self.nberror > 0:
            s += f"Errors:{self.nberror} "
        s += f"Search:{q}"
        if dept != "":
            s+=f"-{dept}"
        s += f" Page:{page}/{nbpage} "
        s += f"{msg} "
        print(s)

    def error(self, msg):
        self.nberror += 1
        print(f"ERROR: {msg}")


if __name__ == '__main__':

    print("Ameli Scrapper")
    print("==============")
    print(f"V{config.version}")
    print()

    parser = argparse.ArgumentParser(description="Ameli Scrapper")
    parser.add_argument("-d", "--dept", help="Departments list in python format, eg [38,06]")
    parser.add_argument("-s2d", "--strategy2d", help="By 2 letters and departments (default)", action="store_true")
    parser.add_argument("-s3d", "--strategy3d", help="By 3 letters and departments, to combine with -d [69,75]", action="store_true")
    parser.add_argument("-s2", "--strategy2", help="By 2 letters", action="store_true")
    parser.add_argument("-s3", "--strategy3", help="By 3 letters", action="store_true")
    parser.add_argument("-s4", "--strategy4", help="By 4 letters", action="store_true")
    args = parser.parse_args()

    print("Test Internet: ", end="")
    with requests.Session() as session:
        loader = loaders.GoogleLoader(session)
        loader.load()
        if loader.ok:
            print("OK")
        else:
            print(loader.response)
            sys.exit(1)
        if args.dept is None:
            service = AmeliScrapperService(session)
        else:
            ds = list(eval(args.dept))
            service = AmeliScrapperService(session, ds)
        print("Test Ameli: ", end="")
        service.loader.load()
        if service.loader.ok:
            print("OK")
        else:
            print("NOK")
            sys.exit(2)
        zero_time = time.perf_counter()
        if args.strategy4:
            service.strategy4()
        elif args.strategy3:
            service.strategy3()
        elif args.strategy2:
            service.strategy2()
        elif args.strategy3d:
            service.strategy3d()
        else:
            service.strategy2d()
        print(f"Total errors:{service.totalerror}")

        # 10%38 = 300s
        # All = 30000s = 8h
        # 38 = 3000s = 50min

    # Prévision 638K
    # S2D: 484K 24h
    # S2: 140K E80 +0 1h
    # S3: 18h




