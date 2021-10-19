from sqlentities import Context, DateSource, Etablissement
from typing import Dict, Optional
import csv
import config
import art
import time
import os
import argparse


class EtabParser:

    def __init__(self, context):
        self.context = context
        self.row_nb = 0
        self.nb_new_etab = 0
        self.date_source: Optional[DateSource] = None
        self.cache: Dict[int, DateSource] = {}

    def parse_date(self, path):
        yy = int(path[-9:-7])
        mm = int(path[-6:-4])
        self.date_source = DateSource(annee=yy, mois=mm)

    def check_date(self, path):
        self.parse_date(path)
        db_date = context.session.query(DateSource).get(self.date_source.id)
        if db_date is None:
            print(f"Added date {self.date_source}")
            context.session.add(self.date_source)
            context.session.commit()
        else:
            self.date_source = db_date

    def load_cache(self):
        self.cache = context.session.query(Etablissement).all()

    def mapper(self, row) -> Etablissement:
        e = Etablissement()
        try:
            e.id = int(row[0])
        except Exception as ex:
            print(f"ERROR row {self.row_nb} {e}\n{ex}")
            quit(1)
        return e

    def load(self, path):
        self.check_date(path)
        self.load_cache()
        with open(path) as f:
            reader = csv.reader(f, delimiter=';')
            for row in reader:
                self.row_nb += 1
                e = self.mapper(row)
                if e.id in self.cache:
                    # TODO eager load date_sources
                    # clone e in self.cache
                    # si date_source pas présent l'appender
                    pass
                else:
                    self.nb_new_etab += 1
                    e.date_sources.append(self.date_source)
                    self.context.session.add(e)
                # TODO self.context.session.commit()




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
    new_db_size = context.db_size()
    print(f"Database {context.db_name}: {new_db_size:.0f} Mo")
    print(f"Database grows: {new_db_size - db_size:.0f} Mo ({((new_db_size - db_size) / db_size) * 100:.1f}%)")
    print(f"Parse {ep.row_nb} rows in {time.perf_counter() - time0:.0f} s")
