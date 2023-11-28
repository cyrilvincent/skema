from typing import Dict, List
from rpps_exercice_pro_parser import RPPSExerciceProParser
from sqlentities import Context, Personne, Langue, PersonneLangue
from base_parser import time0
import argparse
import time
import art
import config


class RPPSLangueParser(RPPSExerciceProParser):

    def __init__(self, context):
        super().__init__(context)
        self.langues: Dict[str, Langue] = {}

    def load_cache(self):
        print("Making cache")
        l: List[PersonneLangue] = self.context.session.query(PersonneLangue).all()
        for e in l:
            self.entities[e.key] = e
        l: List[Langue] = self.context.session.query(Langue).all()
        for e in l:
            self.langues[e.code] = e
        l: List[Personne] = self.context.session.query(Personne).all()
        for p in l:
            self.personnes[p.inpp] = p

    def mapper(self, row) -> PersonneLangue:
        e = PersonneLangue()
        try:
            e.inpp = row["Identification nationale PP"]
            e.code = self.get_nullable(row["Code langue"])
            e.date_maj = self.get_nullable_date(row["Date mise à jour langue"])
        except Exception as ex:
            print(f"ERROR PersonneLangue row {self.row_num} {e}\n{ex}\n{row}")
            quit(1)
        return e

    def make_relations(self, e: PersonneLangue, row):
        try:
            e.personne = self.personnes[e.inpp]
            if e.code not in self.langues:
                l = Langue()
                l.code = e.code
                l.libelle = row["Libellé langue"]
                self.langues[e.code] = l
            e.langue = self.langues[e.code]
        except Exception as ex:
            print(f"ERROR PersonneLangue unknow FK row {self.row_num} {e}\n{ex}")
            quit(2)

    def update(self, e: PersonneLangue):
        self.entities[e.key].date_maj = e.date_maj
        self.nb_update_entity += 1


if __name__ == '__main__':
    art.tprint(config.name, "big")
    print("RPPS Langue Parser")
    print("==================")
    print(f"V{config.version}")
    print(config.copyright)
    print()
    parser = argparse.ArgumentParser(description="RPPS Langue Parser")
    parser.add_argument("path", help="Path")
    parser.add_argument("-e", "--echo", help="Sql Alchemy echo", action="store_true")
    args = parser.parse_args()
    context = Context()
    context.create(echo=args.echo, expire_on_commit=False)
    db_size = context.db_size()
    print(f"Database {context.db_name}: {db_size:.0f} Mb")
    rpp = RPPSLangueParser(context)
    rpp.load(args.path, delimiter=';', encoding="UTF-8", header=True)
    print(f"New personne langue: {rpp.nb_new_entity}")
    print(f"Nb update: {rpp.nb_update_entity}")
    new_db_size = context.db_size()
    print(f"Database {context.db_name}: {new_db_size:.0f} Mb")
    print(f"Database grows: {new_db_size - db_size:.0f} Mb ({((new_db_size - db_size) / db_size) * 100:.1f}%)")
    print(f"Parse {rpp.row_num} rows in {time.perf_counter() - time0:.0f} s")

    # data/rpps/Langue_small.csv
    # data/rpps/Extraction_RPPS_Profil4_Langue_202310250948.csv
