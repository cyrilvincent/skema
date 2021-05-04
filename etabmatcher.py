import config
import time
import argparse
import art
import adresses2pickles
from custommatcher import CustomMatcherBase

time0 = time.perf_counter()


class CustomEntity:
    originalnb = 33
    nb = 80

    def __init__(self):
        self.scores = []
        self.v = []
        for i in range(CustomEntity.nb):
            self.v.append("")
        self.rownum = 0

    @property
    def adresse2(self):
        return ""

    @property
    def adresse3(self):
        return ap.normalize(self.v[32])

    @property
    def cp(self):
        return self.v[33]

    @property
    def commune(self):
        return ap.normalize(self.v[36])

    @property
    def score(self):
        if len(self.scores) == 0:
            return 0.0
        return sum([s for s in self.scores]) / len(self.scores)

    @property
    def rownum(self):
        return self.v[70]

    @rownum.setter
    def rownum(self, value):
        self.v[70] = value

    @property
    def adresseid(self):
        return self.v[71]

    @adresseid.setter
    def adresseid(self, value):
        self.v[71] = value

    @property
    def matchadresse(self):
        return self.v[72]

    @matchadresse.setter
    def matchadresse(self, value):
        self.v[72] = value

    @property
    def codeinsee(self):
        return self.v[73]

    @codeinsee.setter
    def codeinsee(self, value):
        self.v[73] = value

    @property
    def lon(self):
        return self.v[74]

    @lon.setter
    def lon(self, value):
        self.v[74] = value

    @property
    def lat(self):
        return self.v[75]

    @lat.setter
    def lat(self, value):
        self.v[75] = value

    @property
    def x(self):
        return self.v[76]

    @x.setter
    def x(self, value):
        self.v[76] = value

    @property
    def y(self):
        return self.v[77]

    @y.setter
    def y(self, value):
        self.v[77] = value

    @property
    def adressescore(self):
        return self.v[78]

    @adressescore.setter
    def adressescore(self, value):
        self.v[78] = value

    @property
    def matchcp(self):
        return self.v[79]

    @matchcp.setter
    def matchcp(self, value):
        self.v[79] = value

    @property
    def source(self):
        return self.v[80]

    @source.setter
    def source(self, value):
        self.v[80] = value


class MyMatcherBase(CustomMatcherBase):

    def parse(self):
        self.rownum = 0
        for row in self.csv:
            self.i += 1
            self.rownum += 1
            self.nb += 1
            entity = CustomEntity()
            entity.rownum = self.rownum
            self.custom_repo.row2entity(entity, row)
            self.parse_entity(entity)

    def load_by_depts(self, file: str, cache=False):
        depts = [1]
        self.log(f"Load {file}")
        self.csv = self.custom_repo.load(file)
        self.init_load(depts, cache)
        for dept in depts:
            self.db, self.communes_db, self.cps_db, self.insees_db = self.a_repo.load_adresses(dept)
            self.parse()
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

    def __init__(self, path, cache):
        super().__init__()
        self.load_by_depts(path, cache)


if __name__ == '__main__':
    art.tprint(config.name, "big")
    print("My Matcher")
    print("==========")
    print(f"V{config.version}")
    print(config.copyright)
    print()
    parser = argparse.ArgumentParser(description="My Matcher")
    parser.add_argument("path", help="Path")
    parser.add_argument("-c", "--cache", help="Using ps_adresses.csv", action="store_true")
    args = parser.parse_args()
    ap = adresses2pickles.AdresseParser()
    am = MyMatcher(args.path, args.cache)
