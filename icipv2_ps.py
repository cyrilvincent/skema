from typing import Dict, Optional, List, Tuple

import sqlalchemy.orm.identity
from sqlalchemy.orm import joinedload, subqueryload, selectinload
from sqlentities import Context, DateSource, Cabinet, PS, AdresseRaw, Dept, AdresseNorm, PSCabinetDateSource
from icipv2_etab import BaseParser, time0
import argparse
import csv
import time
import art
import config
import re


class PSParser(BaseParser):

    def __init__(self, context):
        super().__init__(context)
        self.nb_tarif = 0
        self.nb_cabinet = 0
        self.cabinets: Dict[str, Cabinet] = {}

    def load_cache(self):
        super().load_cache()
        l: List[PS] = self.context.session.query(PS) \
            .options(joinedload(PS.ps_cabinet_date_sources).joinedload(PSCabinetDateSource.cabinet)).all()
        for e in l:
            self.entities[e.key] = e
        l: List[Cabinet] = self.context.session.query(Cabinet).all()
        for c in l:
            self.cabinets[c.key] = c

    def mapper(self, row) -> PS:
        ps = PS()
        try:
            ps.genre = row[0]
            ps.nom = row[1]
            ps.prenom = row[2]
            ps.key = f"{ps.nom}_{ps.prenom}_{row[7]}".replace(" ", "_")[:255]
        except Exception as ex:
            print(f"ERROR PS row {self.row_num} {ps}\n{ex}")
            quit(1)
        return ps

    def cabinet_mapper(self, row) -> Cabinet:
        c = Cabinet()
        try:
            c.nom = f"{row[1]} {row[2]}" if row[3] == '' else row[3]
            c.telephone = self.get_nullable(row[9])
            c.key = f"{c.nom}_{row[7]}_{row[5]}".replace(" ", "_")[:255]
        except Exception as ex:
            print(f"ERROR cabinet row {self.row_num} {c}\n{ex}")
            quit(1)
        return c

    def create_update_cabinet(self, e: PS, row) -> Cabinet:
        c = self.cabinet_mapper(row)
        if c.key in self.cabinets:
            c = self.cabinets[c.key]
        else:
            self.nb_cabinet += 1
            self.cabinets[c.key] = c
        keys = [pcds.key for pcds in e.ps_cabinet_date_sources]
        if (e.id, c.id, self.date_source.id) not in keys:
            pcds = PSCabinetDateSource()
            pcds.date_source = self.date_source
            pcds.cabinet = c
            e.ps_cabinet_date_sources.append(pcds)
        return c

    def get_dept_from_cp(self, cp):
        cp = str(cp)
        if len(cp) == 4:
            cp = "0" + cp
        dept = cp[:2]
        if dept == "20":
            dept = cp[:3]
        return int(dept)

    def adresse_raw_mapper(self, row):
        a = AdresseRaw()
        try:
            a.adresse2 = self.get_nullable(row[4])
            a.adresse3 = self.get_nullable(row[5])
            a.adresse4 = self.get_nullable(row[6])
            a.cp = int(row[7])
            a.commune = row[8]
            a.dept = self.depts_int[self.get_dept_from_cp(a.cp)]
        except Exception as ex:
            print(f"ERROR raw row {self.row_num} {a}\n{ex}")
            quit(1)
        return a

    def create_update_adresse_raw(self, c: Cabinet, row):
        a = self.adresse_raw_mapper(row)
        if a.key in self.adresse_raws:
            a = self.adresse_raws[a.key]
        else:
            self.nb_new_adresse += 1
            self.adresse_raws[a.key] = a
        c.adresse_raw = a

    def choose_best_rue(self, a: AdresseRaw) -> int:
        l = ["CHEMIN", "AVENUE", "PLACE", "BOULEVARD", "IMPASSE", "ROUTE"]
        if a.adresse3 is not None:
            num, rue = self.split_num(a.adresse3)
            if num is not None:
                return 3
            rue = self.normalize_street(rue)
            for w in l:
                if w in rue:
                    return 3
        if a.adresse2 is not None:
            num, rue = self.split_num(a.adresse2)
            if num is not None:
                return 2
            rue = self.normalize_street(rue)
            for w in l:
                if w in rue:
                    return 2
        return 3

    def normalize(self, a: AdresseRaw) -> AdresseNorm:
        n = AdresseNorm()
        n.cp = a.cp
        n.commune = self.normalize_commune(a.commune)
        n.dept = a.dept
        best = self.choose_best_rue(a)
        if best == 3 and a.adresse3 is not None:
            n.numero, n.rue1 = self.split_num(a.adresse3)
            n.rue1 = self.normalize_street(n.rue1)
            n.rue2 = self.normalize_street(a.adresse2) if a.adresse2 is not None else None
        elif best == 2 and a.adresse2 is not None:
            n.numero, n.rue1 = self.split_num(a.adresse2)
            n.rue1 = self.normalize_street(n.rue1)
            n.rue2 = self.normalize_street(a.adresse3) if a.adresse3 is not None else None
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

    def parse_row(self, row):
        dept = self.get_dept_from_cp(row[7])
        if dept in self.depts_int:
            e = self.mapper(row)
            if e.key in self.entities:
                e = self.entities[e.key]
            else:
                self.entities[e.key] = e
                self.nb_new_entity += 1
                self.context.session.add(e)
            c = self.create_update_cabinet(e, row)
            self.create_update_adresse_raw(c, row)
            self.create_update_norm(c.adresse_raw)
            self.context.session.commit()


if __name__ == '__main__':
    art.tprint(config.name, "big")
    print("PS Parser")
    print("=========")
    print(f"V{config.version}")
    print(config.copyright)
    print()
    parser = argparse.ArgumentParser(description="PS Parser")
    parser.add_argument("path", help="Path")
    parser.add_argument("-e", "--echo", help="Sql Alchemy echo", action="store_true")
    args = parser.parse_args()
    context = Context()
    context.create(echo=args.echo, expire_on_commit=False)
    db_size = context.db_size()
    print(f"Database {context.db_name}: {db_size:.0f} Mo")
    psp = PSParser(context)
    psp.load(args.path, encoding=None)
    print(f"New PS: {psp.nb_new_entity}")
    print(f"New cabinet: {psp.nb_cabinet}")
    print(f"New tarif: {psp.nb_tarif}")
    print(f"New adresse: {psp.nb_new_adresse}")
    print(f"New adresse normalized: {psp.nb_new_norm}")
    new_db_size = context.db_size()
    print(f"Database {context.db_name}: {new_db_size:.0f} Mo")
    print(f"Database grows: {new_db_size - db_size:.0f} Mo ({((new_db_size - db_size) / db_size) * 100:.1f}%)")
    print(f"Parse {psp.row_num} rows in {time.perf_counter() - time0:.0f} s")

    # data/ps/ps-tarifs-small-00-00.csv -e
    # data/ps/ps-tarifs-21-03.csv
    # "data/UFC/ps-tarifs-UFC Santé, Pédiatres 2016 v1-3-16-00.csv"
    # data/SanteSpecialite/ps-tarifs-Santé_Spécialité_1_Gynécologues_201306_v0-97-13-00.csv
