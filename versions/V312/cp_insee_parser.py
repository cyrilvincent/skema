from typing import List
from sqlentities import Context, CPInsee
from base_parser import BaseParser
import argparse
import art
import config


class CPInseeParser(BaseParser):

    def __init__(self, context):
        super().__init__(context)

    def check_date(self, path):
        pass

    def load_cache(self):
        print("Making cache")
        l: List[CPInsee] = self.context.session.query(CPInsee).all()
        for c in l:
            self.entities[c.key] = c
            self.nb_ram += 1
        print(f"{self.nb_ram} objects in cache")

    def mapper(self, row) -> CPInsee:
        ci = CPInsee()
        try:
            ci.cp = int(row["Code Postal / CEDEX"])
            ci.libelle = row["Libellé"]
            ci.insee = row["Code INSEE"]
            ci.is_cedex = True if row["Type de code"] == "Code CEDEX" else False
            ci.commune = row["Nom de la commune"]
            ci.departement = row["Nom du département"]
            ci.epci = row["Nom de l'EPCI"]
            ci.region = row["Nom de la région"]
        except Exception as ex:
            print(f"ERROR OD row {self.row_num} {ci}\n{ex}")
            quit(1)
        return ci

    def parse_row(self, row):
        e = self.mapper(row)
        if e.key in self.entities:
            e = self.entities[e.key]
        else:
            self.entities[e.key] = e
            self.nb_new_entity += 1
            self.context.session.add(e)
        self.context.session.commit()


if __name__ == '__main__':
    art.tprint(config.name, "big")
    print("CP INSEE Parser")
    print("===============")
    print(f"V{config.version}")
    print(config.copyright)
    print()
    parser = argparse.ArgumentParser(description="CP INSEE Parser")
    parser.add_argument("path", help="Path")
    parser.add_argument("-e", "--echo", help="Sql Alchemy echo", action="store_true")
    args = parser.parse_args()
    context = Context()
    context.create(echo=args.echo, expire_on_commit=False)
    db_size = context.db_size()
    print(f"Database {context.db_name}: {db_size:.0f} Mb")
    odp = CPInseeParser(context)
    odp.load(args.path, encoding="utf-8", header=True, delimiter=';')
    print(f"New CP-INSEE: {odp.nb_new_entity}")
    new_db_size = context.db_size()
    print(f"Database {context.db_name}: {new_db_size:.0f} Mb")
    print(f"Database grows: {new_db_size - db_size:.0f} Mb ({((new_db_size - db_size) / db_size) * 100:.1f}%)")

    # data/cedex/correspondance-code-cedex-code-insee.csv
