import difflib
from typing import Dict, List, Tuple, Optional, Set
from sqlalchemy.orm import joinedload
from sqlentities import Context, Cabinet, PS, AdresseRaw, AdresseNorm, PSCabinetDateSource, PAAdresse, PSMerge, OD
from base_parser import BaseParser
import argparse
import art
import config


class ODParser(BaseParser):

    def __init__(self, context):
        super().__init__(context)

    def check_date(self, path):
        pass

    def load_cache(self):
        print("Making cache")
        l: List[OD] = self.context.session.query(OD).all()
        for o in l:
            self.entities[o.key] = o
            self.nb_ram += 1
        print(f"{self.nb_ram} objects in cache")

    def mapper(self, row) -> OD:
        od = OD()
        try:
            od.com1 = row["COM1"]
            od.com2 = row["COM2"]
            od.km = float(row["KM"])
            od.hc = float(row["HC"])
            od.hp = float(row["HP"])
        except Exception as ex:
            print(f"ERROR OD row {self.row_num} {od}\n{ex}")
            quit(1)
        return od

    def parse_row(self, row):
        e = self.mapper(row)
        if e.key in self.entities:
            same = e.equals(self.entities[e.key])
            if not same:
                self.pseudo_clone(e, self.entities[e.key])
                self.nb_update_entity += 1
            e = self.entities[e.key]
        else:
            self.entities[e.key] = e
            self.nb_new_entity += 1
            self.context.session.add(e)
        self.context.session.commit()


if __name__ == '__main__':
    art.tprint(config.name, "big")
    print("OD Parser")
    print("=========")
    print(f"V{config.version}")
    print(config.copyright)
    print()
    parser = argparse.ArgumentParser(description="OD Parser")
    parser.add_argument("path", help="Path")
    parser.add_argument("-e", "--echo", help="Sql Alchemy echo", action="store_true")
    args = parser.parse_args()
    context = Context()
    context.create(echo=args.echo, expire_on_commit=False)
    db_size = context.db_size()
    print(f"Database {context.db_name}: {db_size:.0f} Mo")
    odp = ODParser(context)
    odp.load(args.path, encoding=None, header=True, delimiter=',')
    print(f"New OD: {odp.nb_new_entity}")
    print(f"Update OD: {odp.nb_update_entity}")
    new_db_size = context.db_size()
    print(f"Database {context.db_name}: {new_db_size:.0f} Mo")
    print(f"Database grows: {new_db_size - db_size:.0f} Mo ({((new_db_size - db_size) / db_size) * 100:.1f}%)")

    # data/od/ODfinale.csv
