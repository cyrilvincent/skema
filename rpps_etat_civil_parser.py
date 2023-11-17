from typing import Dict, List, Tuple, Optional
from sqlalchemy.orm import joinedload

from rpps_exercice_pro_parser import RPPSExerciceProParser
from rpps_personne_parser import RPPSPersonneParser
from sqlentities import Context, PersonneActivite, PAAdresse, Dept, CodeProfession, Diplome, Personne, ExercicePro, \
    Structure, Activite, EtatCivil
from base_parser import BaseParser, time0
import argparse
import time
import art
import config


class RPPSEtatCivilParser(RPPSExerciceProParser):

    def __init__(self, context):
        super().__init__(context)

    def load_cache(self):
        print("Making cache")
        l: List[EtatCivil] = self.context.session.query(EtatCivil).all()
        for e in l:
            self.entities[e.key] = e
        l: List[Personne] = self.context.session.query(Personne).all()
        for p in l:
            self.personnes[p.inpp] = p

    def mapper(self, row) -> EtatCivil:
        e = EtatCivil()
        try:
            e.inpp = row["Identification nationale PP"]
            e.statut = self.get_nullable(row["Code statut état-civil"])
            e.sexe = self.get_nullable(row["Code sexe"])
            e.nom = row["Nom de famille"]
            e.nom_norm = self.normalize_string(e.nom)
            e.prenoms = row["Prénoms"]
            e.prenom_norm =  self.normalize_string(e.prenoms.split("'")[0] if "'" in e.prenoms else e.prenoms)
            e.date_naissance = self.get_nullable_date(row["Date de naissance"])
            e.lieu_naissance = self.get_nullable(row["Lieu de naissance"])
            e.date_deces = self.get_nullable_date(row["Date de décès"])
            e.date_effet = self.get_nullable_date(row["Date d'effet de l'état-civil"])
            e.code_commune = self.get_nullable(row["Code commune de naissance"])
            e.commune = self.get_nullable(row["Libellé commune de naissance"])
            e.code_pays = self.get_nullable(row["Code pays de naissance"])
            e.pays = self.get_nullable(self.normalize_string(row["Libellé pays de naissance"]))
            e.date_maj = self.get_nullable_date(row["Date de mise à jour état-civil"])
        except Exception as ex:
            print(f"ERROR EtatCivil row {self.row_num} {e}\n{ex}\n{row}")
            quit(1)
        return e

    def make_relations(self, e: Activite, _):
        try:
            e.personne = self.personnes[e.inpp]
        except Exception as ex:
            print(f"ERROR EtatCivil unknow FK row {self.row_num} {e}\n{ex}")
            quit(2)

    def update(self, e: EtatCivil):
        self.entities[e.key].statut = e.statut
        self.entities[e.key].date_effet = e.date_effet
        if e.date_deces is not None:
            self.entities[e.key].date_deces = e.date_deces
        if e.date_maj is not None:
            self.entities[e.key].date_maj = e.date_maj
        self.nb_update_entity += 1


if __name__ == '__main__':
    art.tprint(config.name, "big")
    print("RPPS Etat Civil Parser")
    print("======================")
    print(f"V{config.version}")
    print(config.copyright)
    print()
    parser = argparse.ArgumentParser(description="RPPS Etat Civil Parser")
    parser.add_argument("path", help="Path")
    parser.add_argument("-e", "--echo", help="Sql Alchemy echo", action="store_true")
    args = parser.parse_args()
    context = Context()
    context.create(echo=args.echo, expire_on_commit=False)
    db_size = context.db_size()
    print(f"Database {context.db_name}: {db_size:.0f} Mb")
    rpp = RPPSEtatCivilParser(context)
    rpp.load(args.path, delimiter=';', encoding="UTF-8", header=True)
    print(f"New etat civil: {rpp.nb_new_entity}")
    print(f"Nb etat civil update: {rpp.nb_update_entity}")
    new_db_size = context.db_size()
    print(f"Database {context.db_name}: {new_db_size:.0f} Mb")
    print(f"Database grows: {new_db_size - db_size:.0f} Mb ({((new_db_size - db_size) / db_size) * 100:.1f}%)")
    print(f"Parse {rpp.row_num} rows in {time.perf_counter() - time0:.0f} s")

    # data/rpps/EtatCivil_small.csv
    # data/rpps/Extraction_RPPS_Profil4_EtatCiv_202310250948.csv
