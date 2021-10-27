from typing import Dict, Optional, List, Tuple

import sqlalchemy.orm.identity
from sqlalchemy.orm import joinedload, subqueryload, selectinload
from sqlentities import Context, DateSource, Cabinet, PS, AdresseRaw, Dept, AdresseNorm, Source
from icipv2_etab import BaseParser
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
        print("Making cache")
        super().load_cache()
        l: List[PS] = self.context.session.query(PS).options(joinedload(PS.cabinets)).all()
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
            print(f"ERROR row {self.row_nb} {ps}\n{ex}")
            quit(1)
        return ps

    def cabinet_mapper(self, row) -> Cabinet:
        c = Cabinet()
        try:
            c.nom = f"{row[1]} {row[2]}" if row[3] == '' else row[3]
            c.telephone = self.get_nullable(row[9])
            c.key = f"{c.nom}_{row[7]}_{row[5]}".replace(" ", "_")[:255]
        except Exception as ex:
            print(f"ERROR row {self.row_nb} {c}\n{ex}")
            quit(1)
        return c

    def create_update_cabinet(self, e: PS, row):
        c = self.cabinet_mapper(row)
        if c.key in self.cabinets:
            c = self.cabinets[c.key]
        else:
            self.nb_cabinet += 1
            self.cabinets[c.key] = c
        keys = [cabinet.key for cabinet in e.cabinets]
        if c.key not in keys:
            e.cabinets.append(c)

    def adresse_row_mapper(self, c: Cabinet, row):
        pass
        # Garder adresse3 et 4 dans l'ordre c'est la normalisation qui changera l'ordre si necessaire

    def parse_row(self, row):
        self.row_nb += 1
        e = self.mapper(row)
        if e.key in self.entities:
            e = self.entities[e.key]
        else:
            self.entities[e.key] = e
            self.nb_new_entity += 1
            self.context.session.add(e)
        self.create_update_cabinet(e, row)  # TODO Remettre le null et passer tout en joinedLoad
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
    time0 = time.perf_counter()
    context = Context()
    context.create(echo=args.echo, expire_on_commit=False)
    db_size = context.db_size()
    print(f"Database {context.db_name}: {db_size:.0f} Mo")
    ep = PSParser(context)
    ep.load(args.path)
    print(f"New PS: {ep.nb_new_entity}")
    print(f"New cabinet: {ep.nb_cabinet}")
    print(f"New tarif: {ep.nb_tarif}")
    print(f"New adresse: {ep.nb_new_adresse}")
    print(f"New adresse normalized: {ep.nb_new_norm}")
    new_db_size = context.db_size()
    print(f"Database {context.db_name}: {new_db_size:.0f} Mo")
    print(f"Database grows: {new_db_size - db_size:.0f} Mo ({((new_db_size - db_size) / db_size) * 100:.1f}%)")
    print(f"Parse {ep.row_nb} rows in {time.perf_counter() - time0:.0f} s")

    # data/ps/ps-tarifs-small-00-00.csv -e
