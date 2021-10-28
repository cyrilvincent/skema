from typing import Dict, Optional, List, Tuple
from sqlentities import Context, Cedex, BAN, EtablissementType, AdresseRaw, Dept, AdresseNorm, Source
import argparse
import csv
import time
import art
import config


class CedexParser:

    def __init__(self, context):
        self.context = context
        self.row_nb = 0
        self.nb_cedex = 0

    def mapper(self, row) -> Cedex:
        c = Cedex()
        try:
            c.cedex = int(row["cedex"])
            c.libelle = row["libelle"]
            c.insee = row["insee"]
            ban = self.context.session.query(BAN).filter(BAN.code_insee == c.insee).first()
            if ban is not None:
                c.cp = ban.code_postal
        except Exception as ex:
            print(f"ERROR row {self.row_nb} {c}\n{ex}")
            quit(1)
        return c

    def parse_row(self, row):
        self.row_nb += 1
        c = self.mapper(row)
        self.nb_cedex += 1
        self.context.session.add(c)
        self.context.session.commit()

    def load(self, path, delimiter=';', encoding="utf8"):
        print(f"Loading {path}")
        with open(path, encoding=encoding) as f:
            reader = csv.DictReader(f, delimiter=delimiter)
            for row in reader:
                self.parse_row(row)


if __name__ == '__main__':
    art.tprint(config.name, "big")
    print("Cedex Parser")
    print("============")
    print(f"V{config.version}")
    print(config.copyright)
    print()
    parser = argparse.ArgumentParser(description="Cedex Parser")
    parser.add_argument("path", help="Path")
    parser.add_argument("-e", "--echo", help="Sql Alchemy echo", action="store_true")
    args = parser.parse_args()
    time0 = time.perf_counter()
    context = Context()
    context.create(echo=args.echo)
    db_size = context.db_size()
    print(f"Database {context.db_name}: {db_size:.0f} Mo")
    ep = CedexParser(context)
    ep.load(args.path)
    print(f"Nb Cedex: {ep.nb_cedex}")
    new_db_size = context.db_size()
    print(f"Database {context.db_name}: {new_db_size:.0f} Mo")
    print(f"Database grows: {new_db_size - db_size:.0f} Mo ({((new_db_size - db_size) / db_size) * 100:.1f}%)")
    print(f"Parse {ep.row_nb} rows in {time.perf_counter() - time0:.0f} s")

    # data/cedex/liste-des-cedex.csv -e
