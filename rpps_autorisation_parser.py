from typing import Dict, List, Tuple, Optional
from sqlalchemy.orm import joinedload

from rpps_exercice_pro_parser import RPPSExerciceProParser
from rpps_personne_parser import RPPSPersonneParser
from sqlentities import Context, PersonneActivite, PAAdresse, Dept, CodeProfession, Diplome, Personne, ExercicePro, \
    Structure, Activite, EtatCivil, Langue, PersonneLangue, PersonneAutorisation, Autorisation
from base_parser import BaseParser, time0
import argparse
import time
import art
import config


class RPPSAutorisationParser(RPPSExerciceProParser):

    def __init__(self, context):
        super().__init__(context)
        self.autorisations: Dict[str, Autorisation] = {}


    def load_cache(self):
        print("Making cache")
        l: List[PersonneAutorisation] = self.context.session.query(PersonneAutorisation).all()
        for e in l:
            self.entities[e.key] = e
        l: List[Autorisation] = self.context.session.query(Autorisation).all()
        for e in l:
            self.autorisations[e.code] = e
        l: List[Personne] = self.context.session.query(Personne).all()
        for p in l:
            self.personnes[p.inpp] = p
        l: List[CodeProfession] = self.context.session.query(CodeProfession).all()
        for c in l:
            self.code_professions[c.id] = c

    def mapper(self, row) -> PersonneAutorisation:
        e = PersonneAutorisation()
        try:
            e.inpp = row["Identification nationale PP"]
            e.code = self.get_nullable(row["Code type autorisation"])
            e.date_effet = self.get_nullable_date(row["Date effet autorisation"])
            e.date_maj = self.get_nullable_date(row["Date fin autorisation"])
            e.date_maj = self.get_nullable_date(row["Date de mise à jour autorisation"])
            e.discipline = self.get_nullable(row["Code discipline autorisation"])
            e.code_profession_id = int(row["Code profession"])
        except Exception as ex:
            print(f"ERROR Autorisation row {self.row_num} {e}\n{ex}\n{row}")
            quit(1)
        return e

    def make_relations(self, e: PersonneAutorisation, row):
        try:
            e.personne = self.personnes[e.inpp]
            e.code_profession = self.code_professions[e.code_profession_id]
            if e.code not in self.autorisations:
                l = Autorisation()
                l.code = e.code
                l.libelle = row["Libellé type autorisation"]
                self.autorisations[e.code] = l
            e.autorisation = self.autorisations[e.code]
        except Exception as ex:
            print(f"ERROR Autorisation unknow FK row {self.row_num} {e}\n{ex}")
            quit(2)

    def update(self, e: PersonneAutorisation):
        self.entities[e.key].date_maj = e.date_maj
        if e.date_fin is not None:
            self.entities[e.key].date_fin = e.date_fin
        self.nb_update_entity += 1


if __name__ == '__main__':
    art.tprint(config.name, "big")
    print("RPPS Autorisation Parser")
    print("========================")
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
    rpp = RPPSAutorisationParser(context)
    rpp.load(args.path, delimiter=';', encoding="UTF-8", header=True)
    print(f"New personne autorisation: {rpp.nb_new_entity}")
    print(f"Nb autorisation update: {rpp.nb_update_entity}")
    new_db_size = context.db_size()
    print(f"Database {context.db_name}: {new_db_size:.0f} Mb")
    print(f"Database grows: {new_db_size - db_size:.0f} Mb ({((new_db_size - db_size) / db_size) * 100:.1f}%)")
    print(f"Parse {rpp.row_num} rows in {time.perf_counter() - time0:.0f} s")

    # data/rpps/Autorisation_small.csv
    # data/rpps/Extraction_RPPS_Profil4_AutExerc_202310250948.csv
