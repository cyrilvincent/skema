from typing import Dict, Optional, List, Tuple
from sqlalchemy.orm import joinedload
from sqlentities import Context, DateSource, Etablissement, EtablissementType, AdresseRaw, Dept
import argparse
import csv
import time
import art
import config


class EtabParser:

    def __init__(self, context):
        self.context = context
        self.row_nb = 0
        self.nb_new_etab = 0
        self.nb_new_adresse = 0
        self.nb_update_etab = 0
        self.date_source: Optional[DateSource] = None
        self.cache: Dict[int, DateSource] = {}
        self.etablissement_types = List[EtablissementType]
        self.depts: Dict[str, Dept] = {}
        self.adresse_raws: [Dict[Tuple[str, str, str]], AdresseRaw] = {}

    def parse_date(self, path):
        yy = int(path[-9:-7])
        mm = int(path[-6:-4])
        self.date_source = DateSource(annee=yy, mois=mm)

    def check_date(self, path):
        self.parse_date(path)
        db_date = self.context.session.query(DateSource).get(self.date_source.id)
        if db_date is None:
            print(f"Added date {self.date_source}")
            self.context.session.add(self.date_source)
            self.context.session.commit()
        else:
            self.date_source = db_date

    def get_value(self, v):
        return None if v == "" else v

    def load_cache(self):
        print("Making cache")
        l = self.context.session.query(Etablissement).options(joinedload(Etablissement.date_sources)) \
                                                .options(joinedload(Etablissement.adresse_raw)).all()
        for e in l:
            self.cache[e.id] = e
        self.etablissement_types = self.context.session.query(EtablissementType).all()
        l = self.context.session.query(Dept).all()
        for d in l:
            self.depts[d.num] = d
        l = self.context.session.query(AdresseRaw).all()
        for a in l:
            self.adresse_raws[a.key] = a

    def mapper(self, row) -> Etablissement:
        e = Etablissement()
        try:
            e.id = int(row[0])
            e.nom = row[1]
            e.numero = row[3]
            l = ["Public", "Privé non lucratif", "Privé commercial"]
            e.type = self.etablissement_types[l.index(row[5])]
            e.telephone = self.get_value(row[37])
            e.mail = self.get_value(row[38])
            e.nom2 = row[39]
            e.url = self.get_value(row[40])
        except Exception as ex:
            print(f"ERROR row {self.row_nb} {e}\n{ex}")
            quit(1)
        return e

    def pseudo_equal(self, obj1: object, obj2) -> bool:
        for a in obj1.__dict__:
            if type(obj1.__getattribute__(a)) in [str, float, None] and a not in ['id'] and not a.startswith('_'):
                if obj1.__getattribute__(a) != obj2.__getattribute__(a):
                    return False
        return True

    def pseudo_clone(self, from_obj: object, to_obj):
        for a in from_obj.__dict__:
            if type(from_obj.__getattribute__(a)) in [str, float, None] and a not in ['id'] and not a.startswith('_'):
                to_obj.__setattr__(a, from_obj.__getattribute__(a))

    def adresse_raw_mapper(self, row) -> AdresseRaw:
        a = AdresseRaw()
        try:
            a.adresse3 = self.get_value(row[32])
            a.cp = row[33]
            a.dept = self.depts[row[34]]
            a.commune = row[36]
        except Exception as ex:
            print(f"ERROR row {self.row_nb} {a}\n{ex}")
            quit(1)
        return a

    def create_upate_adresse(self, e: Etablissement, a: AdresseRaw):
        if a.key not in self.adresse_raws:
            e.adresse_raw = a
            self.adresse_raws[a.key] = a
            self.nb_new_adresse += 1
        else:
            e.adresse_raw = self.adresse_raws[a.key]

    def parse_row(self, row):
        self.row_nb += 1
        e = self.mapper(row)
        if e.id in self.cache:
            same = self.pseudo_equal(e, self.cache[e.id])
            if not same:
                self.pseudo_clone(e, self.cache[e.id])
                self.nb_update_etab += 1
            e = self.cache[e.id]
            if self.date_source not in e.date_sources:
                e.date_sources.append(self.date_source)
            a = self.adresse_raw_mapper(row)
            same = self.pseudo_equal(a, e.adresse_raw)
            if not same:
                self.create_upate_adresse(e, a)
        else:
            self.cache[e.id] = e
            self.nb_new_etab += 1
            e.date_sources.append(self.date_source)
            a = self.adresse_raw_mapper(row)
            self.create_upate_adresse(e, a)
            self.context.session.add(e)
        self.context.session.commit()

    def load(self, path):
        self.check_date(path)
        self.load_cache()
        with open(path, encoding="utf8") as f:
            reader = csv.reader(f, delimiter=';')
            for row in reader:
                self.parse_row(row)


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
    print(f"Loading {args.path}")
    ep.load(args.path)
    print(f"New etablissement: {ep.nb_new_etab}")
    print(f"Update etablissement: {ep.nb_update_etab}")
    print(f"New adresse: {ep.nb_new_adresse}")
    new_db_size = context.db_size()
    print(f"Database {context.db_name}: {new_db_size:.0f} Mo")
    print(f"Database grows: {new_db_size - db_size:.0f} Mo ({((new_db_size - db_size) / db_size) * 100:.1f}%)")
    print(f"Parse {ep.row_nb} rows in {time.perf_counter() - time0:.0f} s")
