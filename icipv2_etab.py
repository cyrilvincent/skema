from typing import Dict, Optional, List, Tuple
from sqlalchemy.orm import joinedload
from sqlentities import Context, DateSource, Etablissement, EtablissementType, AdresseRaw, Dept, AdresseNorm, Source
from abc import ABCMeta, abstractmethod
import argparse
import csv
import time
import art
import config
import re


class BaseParser(metaclass=ABCMeta):

    def __init__(self, context):
        self.context = context
        self.row_nb = 0
        self.entities: Dict[int, DateSource] = {}
        self.nb_new_adresse = 0
        self.nb_new_entity = 0
        self.nb_update_entity = 0
        self.nb_new_norm = 0
        self.date_source: Optional[DateSource] = None
        self.depts: Dict[str, Dept] = {}
        self.sources: Dict[int, Source] = {}
        self.adresse_raws: [Dict[Tuple[str, str, str, str, str]], AdresseRaw] = {}
        self.adresse_norms: [Dict[Tuple[int, str, str, str, str]], AdresseNorm] = {}

    def load_cache(self):
        print("Making cache")
        l = self.context.session.query(Dept).all()
        for d in l:
            self.depts[d.num] = d
        l = self.context.session.query(Source).all()
        for s in l:
            self.sources[s.id] = s
        l = self.context.session.query(AdresseRaw).options(joinedload(AdresseRaw.adresse_norm)).all()
        for a in l:
            self.adresse_raws[a.key] = a
        l = self.context.session.query(AdresseNorm).all()
        for a in l:
            self.adresse_norms[a.key] = a

    def parse_date(self, path):
        try:
            yy = int(path[-9:-7])
            mm = int(path[-6:-4])
            self.date_source = DateSource(annee=yy, mois=mm)
        except IndexError:
            print("ERROR: file must have date like this: file_YY-MM.csv")

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

    # def pseudo_equal(self, obj1: object, obj2) -> bool:
    #     for a in obj1.__dict__:
    #         if type(obj1.__getattribute__(a)) in [str, float, None] and a not in ['id'] and not a.startswith('_'):
    #             if obj1.__getattribute__(a) != obj2.__getattribute__(a):
    #                 return False
    #     return True

    def pseudo_clone(self, from_obj: object, to_obj):
        for a in from_obj.__dict__:
            if type(from_obj.__getattribute__(a)) in [str, float, None] and a not in ['id'] and not a.startswith('_'):
                to_obj.__setattr__(a, from_obj.__getattribute__(a))

    def split_num(self, s: str) -> Tuple[int, str]:
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
        street = " " + street.upper()
        dico = {"'": " ", "-": " ", ".": "", "/": " ", '"': "",
                " BP": "", " CH ": " CHEMIN ", " AV ": " AVENUE ", "PL ": " PLACE ", " BD ": " BOULEVARD ",
                " IMP ": " IMPASSE ", " ST ": " SAINT ", " RT ": " ROUTE ", " RTE ": " ROUTE ", " GAL ": " GENERAL "}
        street = self.replace_all(street, dico)
        return street.strip()

    def normalize_commune(self, commune: str) -> str:
        commune = " " + commune.upper()
        if "CEDEX" in commune:
            index = commune.index("CEDEX")
            commune = commune[:index]
        dico = {"'": " ", "-": " ", ".": "", "/": " ", '"': "",
                " ST ": " SAINT ", " STE ": " SAINTE "}
        commune = self.replace_all(commune, dico)
        return commune.strip()

    def load(self, path, delimiter=';', encoding="utf8"):
        print(f"Loading {path}")
        self.check_date(path)
        self.load_cache()
        with open(path, encoding=encoding) as f:
            reader = csv.reader(f, delimiter=delimiter)
            for row in reader:
                self.parse_row(row)

    @abstractmethod
    def parse_row(self, row): ...

    @abstractmethod
    def mapper(self, row): ...


class EtabParser(BaseParser):

    def __init__(self, context):
        super().__init__(context)
        self.etablissement_types = List[EtablissementType]

    def load_cache(self):
        print("Making cache")
        super().load_cache()
        l = self.context.session.query(Etablissement).options(joinedload(Etablissement.date_sources)) \
            .options(joinedload(Etablissement.adresse_raw)).all()
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
            print(f"ERROR row {self.row_nb} {e}\n{ex}")
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
            print(f"ERROR row {self.row_nb} {a}\n{ex}")
            quit(1)
        return a

    def lat_lon_mapper(self, row) -> Tuple[float, float]:
        try:
            lat = row[41]
            lon = row[42]
            return lat, lon
        except Exception as ex:
            print(f"ERROR row {self.row_nb} bad lat lon\n{ex}")
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
            same = a.adresse_norm.equals(n) # self.pseudo_equal(a.adresse_norm, n)
            if not same:
                a.adresse_norm = n

    def create_update_lat_lon(self, row, n: AdresseNorm):
        lat, lon = self.lat_lon_mapper(row)
        if n.source_id != 3:
            n.lat = lat
            n.lon = lon
            n.source = self.sources[3]
            n.score = 1

    def parse_row(self, row):
        self.row_nb += 1
        e = self.mapper(row)
        if e.id in self.entities:
            same = e.equals(self.entities[e.id])  # self.pseudo_equal(e, self.entities[e.id])
            if not same:
                self.pseudo_clone(e, self.entities[e.id])
                self.nb_update_entity += 1
            e = self.entities[e.id]
            if self.date_source not in e.date_sources:
                e.date_sources.append(self.date_source)
            a = self.adresse_raw_mapper(row)
            same = a.equals(e.adresse_raw)  # self.pseudo_equal(a, e.adresse_raw)
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
    time0 = time.perf_counter()
    context = Context()
    context.create(echo=args.echo)
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
    print(f"Parse {ep.row_nb} rows in {time.perf_counter() - time0:.0f} s")

    # data/etab_00-00.csv -e
