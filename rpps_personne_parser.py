from typing import Dict, List, Tuple, Optional
from sqlalchemy.orm import joinedload
from sqlentities import Context, PersonneActivite, PAAdresse, Dept, CodeProfession, Diplome, Personne
from base_parser import BaseParser, time0
import argparse
import time
import art
import config


class RPPSPersonneParser(BaseParser):

    def __init__(self, context):
        super().__init__(context)

    def load_cache(self):
        print("Making cache")
        l: List[Personne] = self.context.session.query(Personne).all()
        for e in l:
            self.entities[e.inpp] = e

    def check_date(self, path):
        pass

    def mapper(self, row) -> Personne:
        p = Personne()
        try:
            p.inpp = self.strip_quotes(row["Identification nationale PP"])
            p.civilite = self.get_nullable(row["Code civilité"])
            p.nom = self.normalize_string(row["Nom d'usage"])
            p.prenom = self.normalize_string(row["Prénom d'usage"])
            p.nature = self.get_nullable(row["Nature"])
            p.code_nationalite = self.get_nullable(row["Code nationalité"])
            p.date_acquisition_nationalite = self.get_nullable_date(
                row["Date d'acquisition de la nationalité française"])
            p.date_effet = self.get_nullable_date(row["Date d'effet"])
            p.date_maj = self.get_nullable_date(row["Date de mise à jour personne"])
        except Exception as ex:
            print(f"ERROR Personne row {self.row_num} {p}\n{ex}\n{row}")
            quit(1)
        return p

    def update(self, e: Personne):
        self.entities[e.inpp].nom = e.nom
        self.entities[e.inpp].civilite = e.civilite
        if e.nature is not None:
            self.entities[e.inpp].nature = e.nature
        if e.code_nationalite is not None:
            self.entities[e.inpp].code_nationalite = e.code_nationalite
        if e.date_acquisition_nationalite is not None:
            self.entities[e.inpp].date_acquisition_nationalite = e.date_acquisition_nationalite
        if e.date_effet is not None:
            self.entities[e.inpp].date_effet = e.date_effet
        if e.date_maj is not None:
            self.entities[e.inpp].date_maj = e.date_maj
        self.nb_update_entity += 1

    def load(self, path: str, delimiter=';', encoding="utf8", header=False):
        out_path = path.replace(".csv", ".temp")
        self.strip_double_quotes_writer(path, out_path, encoding)
        super().load(out_path, delimiter, encoding, header)


    def parse_row(self, row):
        e = self.mapper(row)
        if e.inpp in self.entities:
            same = e.equals(self.entities[e.inpp])
            if not same:
                self.update(e)
            e = self.entities[e.inpp]
        else:
            self.nb_new_entity += 1
            self.entities[e.inpp] = e
            self.context.session.add(e)
        self.context.session.commit()


if __name__ == '__main__':
    art.tprint(config.name, "big")
    print("RPPS Personne Parser")
    print("====================")
    print(f"V{config.version}")
    print(config.copyright)
    print()
    parser = argparse.ArgumentParser(description="RPPS Personne Parser")
    parser.add_argument("path", help="Path")
    parser.add_argument("-e", "--echo", help="Sql Alchemy echo", action="store_true")
    args = parser.parse_args()
    context = Context()
    context.create(echo=args.echo, expire_on_commit=False)
    db_size = context.db_size()
    print(f"Database {context.db_name}: {db_size:.0f} Mb")
    rpp = RPPSPersonneParser(context)
    rpp.load(args.path, delimiter=';', encoding="UTF-8", header=True)
    print(f"New personne: {rpp.nb_new_entity}")
    print(f"Nb personne update: {rpp.nb_update_entity}")
    new_db_size = context.db_size()
    print(f"Database {context.db_name}: {new_db_size:.0f} Mb")
    print(f"Database grows: {new_db_size - db_size:.0f} Mb ({((new_db_size - db_size) / db_size) * 100:.1f}%)")
    print(f"Parse {rpp.row_num} rows in {time.perf_counter() - time0:.0f} s")

    # data/rpps/Personne_small.csv -e
    # data/rpps/Extraction_RPPS_Profil4_Personne_202310250948.csv
