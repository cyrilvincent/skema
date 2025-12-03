from typing import Dict, List, Tuple
from rpps_exercice_pro_parser import RPPSExerciceProParser
from sqlentities import Context, ExercicePro, EtatCivil, ReferenceAE
from base_parser import time0
import argparse
import time
import art
import config


class RPPSReferenceAEParser(RPPSExerciceProParser):

    def __init__(self, context):
        super().__init__(context)
        self.exercices_pro: Dict[Tuple[str, str, int], ExercicePro] = {}

    def load_cache(self):
        print("Making cache")
        l: List[ReferenceAE] = self.context.session.query(ReferenceAE).all()
        for e in l:
            self.entities[e.key] = e
        l: List[ExercicePro] = self.context.session.query(ExercicePro).all()
        for e in l:
            self.exercices_pro[e.key] = e

    def mapper(self, row) -> ReferenceAE:
        e = ReferenceAE()
        try:
            e.inpp = row["Identification nationale PP"]
            e.ae = self.get_nullable(row["Code AE"])
            e.date_debut = self.get_nullable_date(row["Date début inscription"])
            e.date_fin = self.get_nullable_date(row["Date fin inscription"])
            e.date_maj = self.get_nullable_date(row["Date de mise à jour inscription"])
            e.statut = self.get_nullable(row["Code statut inscription"])
            e.departement = self.get_nullable(row["Code département inscription"])
            e.departement_acceuil = self.get_nullable(row["Code département accueil"])
            e.code_profession = int(row["Code profession"])
            e.categorie_pro = self.get_nullable(row["Code catégorie professionnelle"])
        except Exception as ex:
            print(f"ERROR ReferenceAE row {self.row_num} {e}\n{ex}\n{row}")
            quit(1)
        return e

    def make_relations(self, e: ReferenceAE, _):
        try:
            e.exercice_pro = self.exercices_pro[(e.inpp, e.categorie_pro, e.code_profession)]
        except Exception as ex:
            print(f"ERROR ReferenceAE unknow FK row {self.row_num} {e}\n{ex}")
            quit(2)

    def update(self, e: EtatCivil):
        if e.date_fin is not None:
            self.entities[e.key].date_fin = e.date_fin
        if e.date_maj is not None:
            self.entities[e.key].date_maj = e.date_maj
        self.nb_update_entity += 1


if __name__ == '__main__':
    art.tprint(config.name, "big")
    print("RPPS Reference AE Parser")
    print("========================")
    print(f"V{config.version}")
    print(config.copyright)
    print()
    parser = argparse.ArgumentParser(description="RPPS Reference AE Parser")
    parser.add_argument("path", help="Path")
    parser.add_argument("-e", "--echo", help="Sql Alchemy echo", action="store_true")
    args = parser.parse_args()
    context = Context()
    context.create(echo=args.echo, expire_on_commit=False)
    db_size = context.db_size()
    print(f"Database {context.db_name}: {db_size:.0f} Mb")
    rpp = RPPSReferenceAEParser(context)
    rpp.load(args.path, delimiter=';', encoding="UTF-8", header=True)
    print(f"New reference AE: {rpp.nb_new_entity}")
    print(f"Nb reference AE update: {rpp.nb_update_entity}")
    new_db_size = context.db_size()
    print(f"Database {context.db_name}: {new_db_size:.0f} Mb")
    print(f"Database grows: {new_db_size - db_size:.0f} Mb ({((new_db_size - db_size) / db_size) * 100:.1f}%)")
    print(f"Parse {rpp.row_num} rows in {time.perf_counter() - time0:.0f}s")

    # data/rpps/ReferenceAE_small.csv
    # data/rpps/Extraction_RPPS_Profil4_ReferAe_202310250948.csv
