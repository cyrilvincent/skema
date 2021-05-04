import config
import time
import argparse
import art
from custommatcher import CustomMatcherBase
from typing import List, Optional

time0 = time.perf_counter()


class CustomEntity:
    originalnb = 33
    nb = 45 #+12 with id +11 else

    def __init__(self):
        self.scores = []
        self.v = []
        for i in range(CustomEntity.nb):
            self.v.append("")
        self.rownum = 0

    @property
    def adresse2(self):
        return self.v[4]

    @property
    def adresse3(self):
        return self.v[5]

    @property
    def cp(self):
        return self.v[7]

    @property
    def commune(self):
        return self.v[8]

    @property
    def score(self):
        if len(self.scores) == 0:
            return 0.0
        return sum([s for s in self.scores]) / len(self.scores)

    @property
    def rownum(self):
        return self.v[34]

    @rownum.setter
    def rownum(self, value):
        self.v[34] = value

    @property
    def adresseid(self):
        return self.v[35]

    @adresseid.setter
    def adresseid(self, value):
        self.v[35] = value

    @property
    def matchadresse(self):
        return self.v[36]

    @matchadresse.setter
    def matchadresse(self, value):
        self.v[36] = value

    @property
    def codeinsee(self):
        return self.v[37]

    @codeinsee.setter
    def codeinsee(self, value):
        self.v[37] = value

    @property
    def lon(self):
        return self.v[38]

    @lon.setter
    def lon(self, value):
        self.v[38] = value

    @property
    def lat(self):
        return self.v[39]

    @lat.setter
    def lat(self, value):
        self.v[39] = value

    @property
    def x(self):
        return self.v[40]

    @x.setter
    def x(self, value):
        self.v[40] = value

    @property
    def y(self):
        return self.v[41]

    @y.setter
    def y(self, value):
        self.v[41] = value

    @property
    def adressescore(self):
        return self.v[42]

    @adressescore.setter
    def adressescore(self, value):
        self.v[42] = value

    @property
    def matchcp(self):
        return self.v[43]

    @matchcp.setter
    def matchcp(self, value):
        self.v[43] = value

    @property
    def source(self):
        return self.v[44]

    @source.setter
    def source(self, value):
        self.v[44] = value


class MyMatcherBase(CustomMatcherBase):

    def parse(self, dept: int):
        """
        Fonction principale, charge PS et match un département
        :param dept: un département
        """
        self.rownum = 0
        for row in self.csv:
            self.i += 1
            self.rownum += 1
            self.nb += 1
            entity = CustomEntity()
            entity.rownum = self.rownum
            self.custom_repo.row2entity(entity, row)
            self.parse_entity(entity)

    def load_by_depts(self, file: str, depts: Optional[List[int]] = None, cache=False):
        depts = [1]
        self.log(f"Load {file}")
        self.csv = self.custom_repo.load(file)
        self.init_load(depts, cache)
        for dept in depts:
            self.log(f"Load dept {dept}")
            self.db, self.communes_db, self.cps_db, self.insees_db = self.a_repo.load_adresses(dept)
            self.parse(dept)
        self.display()
        self.custom_db.sort(key=lambda e: e.rownum)
        file = file.replace(".csv", "-adresses.csv")
        try:
            self.custom_repo.save_entities(file, self.custom_db)
            if self.nbnewadresse > 0 and cache:
                self.a_repo.save_adresses_db(self.adresses_db)
        except PermissionError as pe:
            print(pe)
            input("Close the file and press Enter")
            self.custom_repo.save_entities(file, self.custom_db)
            if self.nbnewadresse > 0 and cache:
                self.a_repo.save_adresses_db(self.adresses_db)
        self.log(f"Saved {self.nb} PS")


class MyMatcher(MyMatcherBase):

    def __init__(self, path, dept, cache):
        super().__init__()
        if dept is None:
            self.load_by_depts(path, None, cache)
        else:
            self.load_by_depts(path, eval(dept), cache)


if __name__ == '__main__':
    art.tprint(config.name, "big")
    print("My Matcher")
    print("==========")
    print(f"V{config.version}")
    print(config.copyright)
    print()
    parser = argparse.ArgumentParser(description="My Matcher")
    parser.add_argument("path", help="Path")
    parser.add_argument("-d", "--dept", help="Departments list in python format, eg [5,38,06]")
    parser.add_argument("-c", "--cache", help="Using ps_adresses.csv", action="store_true")
    args = parser.parse_args()
    am = MyMatcher(args.path, args.dept, args.cache)
