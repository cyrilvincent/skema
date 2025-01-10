from typing import Dict, List

from rpps_diplome_obtenu_parser import RPPSDiplomeObtenuParser
from rpps_exercice_pro_parser import RPPSExerciceProParser
from sqlentities import Context, Diplome, Personne, DiplomeObtenu, Lieu
from base_parser import time0
import argparse
import time
import art
import config


class RPPSLieuParser(RPPSDiplomeObtenuParser):

    def __init__(self, context):
        super().__init__(context)

    def load_cache(self):
        print("Making cache")
        l: List[Lieu] = self.context.session.query(Lieu).all()
        for e in l:
            self.entities[e.key] = e

    def mapper(self, row) -> Lieu:
        e = Lieu()
        try:
            e.lieu = row["Code lieu obtention"]
            e.libelle = row["Libellé lieu obtention"]
        except Exception as ex:
            print(f"ERROR Lieu row {self.row_num} {e}\n{ex}\n{row}")
            quit(1)
        return e

    def make_relations(self, e, row):
        pass

    def update(self, e):
        pass


if __name__ == '__main__':
    art.tprint(config.name, "big")
    print("RPPS Lieu Parser")
    print("=================")
    print(f"V{config.version}")
    print(config.copyright)
    print()
    parser = argparse.ArgumentParser(description="RPPS Lieu Parser")
    parser.add_argument("path", help="Path")
    parser.add_argument("-e", "--echo", help="Sql Alchemy echo", action="store_true")
    args = parser.parse_args()
    context = Context()
    context.create(echo=args.echo, expire_on_commit=False)
    db_size = context.db_size()
    print(f"Database {context.db_name}: {db_size:.0f} Mb")
    rpp = RPPSLieuParser(context)
    rpp.load(args.path, delimiter=';', encoding="UTF-8", header=True)
    print(f"New lieu: {rpp.nb_new_entity}")
    new_db_size = context.db_size()
    print(f"Database {context.db_name}: {new_db_size:.0f} Mb")
    print(f"Database grows: {new_db_size - db_size:.0f} Mb ({((new_db_size - db_size) / db_size) * 100:.1f}%)")
    print(f"Parse {rpp.row_num} rows in {time.perf_counter() - time0:.0f} s")

    # data/rpps/DiplomeObtenu_small.csv
    # data/rpps/Extraction_RPPS_Profil4_DiplObt_202310250948.csv

