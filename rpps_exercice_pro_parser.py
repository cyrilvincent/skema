from typing import Dict, List, Tuple, Optional
from sqlalchemy.orm import joinedload

from rpps_personne_parser import RPPSPersonneParser
from sqlentities import Context, PersonneActivite, PAAdresse, Dept, CodeProfession, Diplome, Personne, ExercicePro, \
    CategoriePro
from base_parser import BaseParser, time0
import argparse
import time
import art
import config


class RPPSExerciceProParser(RPPSPersonneParser):

    def __init__(self, context):
        super().__init__(context)
        self.personnes: Dict[str, Personne] = {}
        self.code_professions: Dict[int, CodeProfession] = {}
        self.categorie_pros: Dict[str, CategoriePro] = {}

    def load_cache(self):
        print("Making cache")
        l: List[ExercicePro] = self.context.session.query(ExercicePro).all()
        for e in l:
            self.entities[e.key] = e
        l: List[Personne] = self.context.session.query(Personne).all()
        for p in l:
            self.personnes[p.inpp] = p
        l: List[CodeProfession] = self.context.session.query(CodeProfession).all()
        for c in l:
            self.code_professions[c.id] = c
        l: List[CategoriePro] = self.context.session.query(CategoriePro).all()
        for c in l:
            self.categorie_pros[c.code] = c

    def mapper(self, row) -> ExercicePro:
        e = ExercicePro()
        try:
            e.inpp = row["Identification nationale PP"]
            e.civilite = self.get_nullable(row["Code civilité d'exercice"])
            e.nom = row["Nom d'exercice"].upper()
            e.prenom = row["Prénom d'exercice"].upper()
            e.code_categorie_pro = self.get_nullable(row["Code catégorie professionnelle"])
            e.code_profession_id = int(row["Code profession"])
            e.date_fin = self.get_nullable_date(row["Date de fin exercice"])
            e.date_maj = self.get_nullable_date(row["Date de mise à jour exercice"])
            e.date_effet = self.get_nullable_date(row["Date effet exercice"])
            e.ae = self.get_nullable(row["Code AE 1e inscription"])
            e.date_debut_inscription = self.get_nullable_date(row["Date début 1e inscription"])
            e.departement_inscription = self.get_nullable(row["Département 1e inscription"])
        except Exception as ex:
            print(f"ERROR ExercicePro row {self.row_num} {e}\n{ex}\n{row}")
            quit(1)
        return e

    def make_relations(self, e: ExercicePro, row):
        try:
            e.personne = self.personnes[e.inpp]
            e.code_profession = self.code_professions[e.code_profession_id]
            if e.code_categorie_pro not in self.categorie_pros:
                c = CategoriePro()
                c.code = e.code_categorie_pro
                c.libelle = row["Libellé catégorie professionnelle"]
                self.categorie_pros[c.code] = c
            e.categorie_pro = self.categorie_pros[e.code_categorie_pro]
        except Exception as ex:
            print(f"ERROR ExercicePro unknow FK row {self.row_num} {e}\n{ex}")
            quit(2)

    def update(self, e: ExercicePro):
        if e.date_fin is not None:
            self.entities[e.key].date_fin = e.date_fin
        if e.date_maj is not None:
            self.entities[e.key].date_maj = e.date_maj
        self.nb_update_entity += 1

    def parse_row(self, row):
        e = self.mapper(row)
        if e.key in self.entities:
            same = e.equals(self.entities[e.key])
            if not same:
                self.update(e)
            e = self.entities[e.key]
        else:
            self.nb_new_entity += 1
            self.entities[e.key] = e
            self.make_relations(e, row)
            self.context.session.add(e)
        self.context.session.commit()


if __name__ == '__main__':
    art.tprint(config.name, "big")
    print("RPPS Exercice Pro Parser")
    print("========================")
    print(f"V{config.version}")
    print(config.copyright)
    print()
    parser = argparse.ArgumentParser(description="RPPS Exercice Pro Parser")
    parser.add_argument("path", help="Path")
    parser.add_argument("-e", "--echo", help="Sql Alchemy echo", action="store_true")
    args = parser.parse_args()
    context = Context()
    context.create(echo=args.echo, expire_on_commit=False)
    db_size = context.db_size()
    print(f"Database {context.db_name}: {db_size:.0f} Mb")
    rpp = RPPSExerciceProParser(context)
    rpp.load(args.path, delimiter=';', encoding="UTF-8", header=True)
    print(f"New exercice pro: {rpp.nb_new_entity}")
    print(f"Nb exercice pro update: {rpp.nb_update_entity}")
    new_db_size = context.db_size()
    print(f"Database {context.db_name}: {new_db_size:.0f} Mb")
    print(f"Database grows: {new_db_size - db_size:.0f} Mb ({((new_db_size - db_size) / db_size) * 100:.1f}%)")
    print(f"Parse {rpp.row_num} rows in {time.perf_counter() - time0:.0f} s")

    # data/rpps/ExercPro_small.csv
    # data/rpps/Extraction_RPPS_Profil4_ExercPro_202310250948.csv
