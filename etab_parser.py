from typing import Dict, Optional, List, Tuple
from sqlalchemy.orm import joinedload
import unidecode
import pyproj
from sqlentities import Context, DateSource, Etablissement, EtablissementType, AdresseRaw, Dept, AdresseNorm, Source
from abc import ABCMeta, abstractmethod
import argparse
import csv
import time
import art
import config
import re

time0 = time.perf_counter()


class BaseParser(metaclass=ABCMeta):

    def __init__(self, context):
        self.path = None
        self.context = context
        self.row_num = 0
        self.nb_row = 0
        self.entities = {}
        self.nb_new_adresse = 0
        self.nb_new_entity = 0
        self.nb_update_entity = 0
        self.nb_new_norm = 0
        self.nb_ram = 0
        self.date_source: Optional[DateSource] = None
        self.depts: Dict[str, Dept] = {}
        self.depts_int: Dict[int, Dept] = {}
        self.sources: Dict[int, Source] = {}
        self.adresse_raws: [Dict[Tuple[str, str, str, str, str]], AdresseRaw] = {}
        self.adresse_norms: [Dict[Tuple[int, str, str, str, str]], AdresseNorm] = {}

    def load_cache(self):
        print("Making cache")
        l = self.context.session.query(Dept).all()
        for d in l:
            self.depts[d.num] = d
            self.depts_int[d.id] = d
            self.nb_ram += 2
        l = self.context.session.query(Source).all()
        for s in l:
            self.sources[s.id] = s
            self.nb_ram += 1
        l = self.context.session.query(AdresseRaw).options(joinedload(AdresseRaw.adresse_norm)).all()
        # Erreur courante, quand le key ne matche pas c'est que le cp est en str
        for a in l:
            self.adresse_raws[a.key] = a
            self.nb_ram += 1
        l = self.context.session.query(AdresseNorm).all()
        for a in l:
            self.adresse_norms[a.key] = a
            self.nb_ram += 1
        print(f"{self.nb_ram} objects in cache")

    def test_file(self, path, encoding="utf8"):
        with open(path, encoding=encoding) as f:
            for _ in f:
                self.nb_row += 1
        print(f"Found {self.nb_row} rows")

    def parse_date(self, path):
        try:
            yy = int(path[-9:-7])
            mm = int(path[-6:-4])
            self.date_source = DateSource(annee=yy, mois=mm)
        except IndexError:
            print("ERROR: file must have date like this: file_YY-MM.csv")

    def get_dept_from_cp(self, cp):
        cp = str(cp)
        if len(cp) == 4:
            cp = "0" + cp
        dept = cp[:2]
        if dept == "20":
            dept = cp[:3]
        return int(dept)

    def check_date(self, path):
        self.parse_date(path)
        db_date = self.context.session.query(DateSource).get(self.date_source.id)
        if db_date is None:
            print(f"Added date {self.date_source}")
            self.context.session.add(self.date_source)
            self.context.session.commit()
        else:
            self.date_source = db_date

    def get_nullable(self, v):
        return None if v == "" else v

    def get_nullable_int(self, v):
        return None if v == "" else int(v)

    def pseudo_clone(self, from_obj: object, to_obj):
        for a in from_obj.__dict__:
            if type(from_obj.__getattribute__(a)) in [str, float, type(None)] and a not in ['id'] and not a.startswith('_'):
                to_obj.__setattr__(a, from_obj.__getattribute__(a))

    def split_num(self, s: str) -> Tuple[Optional[int], str]:
        regex = r"(\d+)"
        match = re.match(regex, s)
        if match is None:
            return None, s
        num = match[1]
        index = s.index(match[1])
        return int(num), s[index + len(num):].strip()

    def replace_all(self, s, dico: Dict[str, str]) -> str:
        for key in dico:
            s = s.replace(key, dico[key])
        return s

    def normalize_street(self, street: str) -> str:
        street = unidecode.unidecode(street)
        street = " " + street.upper()
        dico = {"'": " ", "-": " ", ".": "", "/": " ", '"': "",
                " BP": "", " CH ": " CHEMIN ", " AV ": " AVENUE ", " PL ": " PLACE ", " BD ": " BOULEVARD ",
                " IMP ": " IMPASSE ", " ST ": " SAINT ", " RT ": " ROUTE ", " RTE ": " ROUTE ", " GAL ": " GENERAL ",
                " BIS ": "", " TER ": "", " BAT ": ""}
        street = self.replace_all(street, dico).strip()
        if len(street) > 2 and street[1] == " ":
            street = street[2:]
        return street.strip()

    def normalize_commune(self, commune: str) -> str:
        commune = unidecode.unidecode(commune)
        commune = " " + commune.upper()
        if "CEDEX" in commune:
            index = commune.index("CEDEX")
            commune = commune[:index]
        dico = {"'": " ", "-": " ", ".": "", "/": " ", '"': "",
                " ST ": " SAINT ", " STE ": " SAINTE "}
        commune = self.replace_all(commune, dico)
        return commune.strip()

    def normalize_string(self, s: str) -> str:
        s = s.strip().upper()
        s = unidecode.unidecode(s).replace("'", " ").replace("-", " ").replace("/", " ").replace(".", "")
        return s

    def convert_lambert93_lon_lat(self, x: float, y: float) -> Tuple[float, float]:
        transformer = pyproj.Transformer.from_crs(2154, 4326, always_xy=True)
        lon, lat = transformer.transform(x, y)
        return lon, lat

    def load(self, path, delimiter=';', encoding="utf8", header=False):
        print(f"Loading {path}")
        self.path = path
        self.check_date(path)
        self.test_file(path, encoding)
        self.load_cache()
        duration_cache = time.perf_counter() - time0
        with open(path, encoding=encoding) as f:
            if header:
                reader = csv.DictReader(f, delimiter=delimiter)
            else:
                reader = csv.reader(f, delimiter=delimiter)
            for row in reader:
                self.row_num += 1
                self.parse_row(row)
                if self.row_num % 10000 == 0 or self.row_num == 10 or self.row_num == 100 \
                        or self.row_num == 1000 or self.row_num == self.nb_row:
                    duration = time.perf_counter() - time0 - duration_cache + 1e-6
                    print(f"Parse {self.row_num} rows {(self.row_num / self.nb_row) * 100:.1f}% "
                          f"in {(duration + duration_cache):.0f}s "
                          f"@{self.row_num / duration:.0f}row/s "
                          f"{((self.nb_row / self.row_num) * duration) - duration:.0f}s remaining ")


    @abstractmethod
    def parse_row(self, row): ...

    @abstractmethod
    def mapper(self, row): ...


class EtabParser(BaseParser):

    def __init__(self, context):
        super().__init__(context)
        self.etablissement_types = List[EtablissementType]

    def load_cache(self):
        super().load_cache()
        l = self.context.session.query(Etablissement).options(joinedload(Etablissement.type))\
            .options(joinedload(Etablissement.adresse_raw).joinedload(AdresseRaw.adresse_norm))\
            .options(joinedload(Etablissement.date_sources)).all()
        for e in l:
            self.entities[e.id] = e
        self.etablissement_types = self.context.session.query(EtablissementType).all()

    def mapper(self, row) -> Etablissement:
        e = Etablissement()
        try:
            e.id = int(row[0])
            e.nom = row[1]
            e.numero = row[3]
            l = ["Public", "Privé non lucratif", "Privé commercial"]
            e.type = self.etablissement_types[l.index(row[5])]
            e.telephone = self.get_nullable(row[37])
            e.mail = self.get_nullable(row[38])
            e.nom2 = row[39]
            e.url = self.get_nullable(row[40])
        except Exception as ex:
            print(f"ERROR row {self.row_num} {e}\n{ex}")
            quit(1)
        return e

    def adresse_raw_mapper(self, row) -> AdresseRaw:
        a = AdresseRaw()
        try:
            a.adresse3 = self.get_nullable(row[32])
            a.cp = row[33]
            a.dept = self.depts[row[34]]
            a.commune = row[36]
        except Exception as ex:
            print(f"ERROR row {self.row_num} {a}\n{ex}")
            quit(1)
        return a

    def lat_lon_mapper(self, row) -> Tuple[float, float]:
        try:
            lat = row[41]
            lon = row[42]
            return lat, lon
        except Exception as ex:
            print(f"ERROR row {self.row_num} bad lat lon\n{ex}")
            quit(1)

    def create_update_adresse(self, e: Etablissement, a: AdresseRaw):
        if a.key not in self.adresse_raws:
            e.adresse_raw = a
            self.adresse_raws[a.key] = a
            self.nb_new_adresse += 1
        else:
            e.adresse_raw = self.adresse_raws[a.key]

    def normalize(self, a: AdresseRaw) -> AdresseNorm:
        n = AdresseNorm()
        if a.adresse3 is not None:
            n.numero, n.rue1 = self.split_num(a.adresse3)
            n.rue1 = self.normalize_street(n.rue1)
        n.cp = a.cp
        n.commune = self.normalize_commune(a.commune)
        n.dept = a.dept
        return n

    def create_update_norm(self, a: AdresseRaw):
        n = self.normalize(a)
        if n.key in self.adresse_norms:
            n = self.adresse_norms[n.key]
        else:
            self.adresse_norms[n.key] = n
            self.context.session.add(n)
            self.nb_new_norm += 1
        if a.adresse_norm is None:
            a.adresse_norm = n
        else:
            same = a.adresse_norm.equals(n)
            if not same:
                a.adresse_norm = n

    def create_update_lat_lon(self, row, n: AdresseNorm):
        lat, lon = self.lat_lon_mapper(row)
        if n.source is not None and n.source_id != 3:
            n.lat = lat
            n.lon = lon
            n.source = self.sources[3]
            n.score = 1

    def parse_row(self, row):
        e = self.mapper(row)
        if e.id in self.entities:
            same = e.equals(self.entities[e.id])
            if not same:
                self.pseudo_clone(e, self.entities[e.id])
                self.nb_update_entity += 1
            e = self.entities[e.id]
            if self.date_source not in e.date_sources:
                e.date_sources.append(self.date_source)
            a = self.adresse_raw_mapper(row)
            same = a.equals(e.adresse_raw)
            if not same:
                self.create_update_adresse(e, a)
        else:
            self.entities[e.id] = e
            self.nb_new_entity += 1
            e.date_sources.append(self.date_source)
            a = self.adresse_raw_mapper(row)
            self.create_update_adresse(e, a)
            self.context.session.add(e)
        self.create_update_norm(e.adresse_raw)
        self.create_update_lat_lon(row, e.adresse_raw.adresse_norm)
        self.context.session.commit()


if __name__ == '__main__':
    art.tprint(config.name, "big")
    print("Etab Parser")
    print("===========")
    print(f"V{config.version}")
    print(config.copyright)
    print()
    parser = argparse.ArgumentParser(description="Etab Parser")
    parser.add_argument("path", help="Path")
    parser.add_argument("-e", "--echo", help="Sql Alchemy echo", action="store_true")
    args = parser.parse_args()
    context = Context()
    context.create(echo=args.echo, expire_on_commit=False)
    db_size = context.db_size()
    print(f"Database {context.db_name}: {db_size:.0f} Mo")
    ep = EtabParser(context)
    ep.load(args.path)
    print(f"New etablissement: {ep.nb_new_entity}")
    print(f"Update etablissement: {ep.nb_update_entity}")
    print(f"New adresse: {ep.nb_new_adresse}")
    print(f"New adresse normalized: {ep.nb_new_norm}")
    new_db_size = context.db_size()
    print(f"Database {context.db_name}: {new_db_size:.0f} Mo")
    print(f"Database grows: {new_db_size - db_size:.0f} Mo ({((new_db_size - db_size) / db_size) * 100:.1f}%)")

    # data/etab_00-00.csv -e
