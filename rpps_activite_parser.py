from typing import Dict, List

from rpps_exercice_pro_parser import RPPSExerciceProParser
from sqlentities import Context, CodeProfession, Personne, Structure, Activite, Fonction
from base_parser import time0
import argparse
import time
import art
import config


class RPPSActiviteParser(RPPSExerciceProParser):

    def __init__(self, context):
        super().__init__(context)
        self.personnes: Dict[str, Personne] = {}
        self.structures : Dict[str, Structure] = {}
        self.code_professions: Dict[int, CodeProfession] = {}
        self.fonctions: Dict[str, Fonction] = {}

    def load_cache(self):
        print("Making cache")
        l: List[Activite] = self.context.session.query(Activite).all()
        for e in l:
            self.entities[e.key] = e
        l: List[Personne] = self.context.session.query(Personne).all()
        for p in l:
            self.personnes[p.inpp] = p
        l: List[CodeProfession] = self.context.session.query(CodeProfession).all()
        for c in l:
            self.code_professions[c.id] = c
        l: List[Structure] = self.context.session.query(Structure).all()
        for s in l:
            self.structures[s.key] = s
        l: List[Fonction] = self.context.session.query(Fonction).all()
        for f in l:
            self.fonctions[f.code] = f

    def mapper(self, row) -> Activite:
        e = Activite()
        try:
            e.activite_id = row["Identifiant de l'activité"]
            e.inpp = row["Identification nationale PP"]
            e.id_technique_structure = self.get_nullable(row["Identifiant technique de la structure"])
            e.code_fonction = self.get_nullable(row["Code fonction"])
            e.mode_exercice = self.get_nullable(row["Code mode exercice"])
            e.categorie_pro = self.get_nullable(row["Code catégorie professionnelle"])
            e.date_debut = self.get_nullable_date(row["Date de début activité"])
            e.date_fin = self.get_nullable_date(row["Date de fin activité"])
            e.date_maj = self.get_nullable_date(row["Date de mise à jour activité"])
            e.region = self.get_nullable(row["Code région exercice"])
            e.genre = self.get_nullable(row["Code genre activité"])
            e.motif_fin = self.get_nullable(row["Code motif de fin d'activité"])
            e.section_tableau_pharmaciens = self.get_nullable(row["Code section tableau pharmaciens"])
            e.sous_section_tableau_pharmaciens = self.get_nullable(row["Code sous-section tableau pharmaciens"])
            e.type_activite_liberale = self.get_nullable(row["Code type activité libérale"])
            e.statut_ps_ssa = self.get_nullable(row["Code statut des PS du SSA"])
            e.statut_hospitalier = self.get_nullable(row["Code statut hospitalier"])
            e.code_profession_id = int(row["Code profession"])
            e.categorie_pro = self.get_nullable(row["Code catégorie professionnelle"])
        except Exception as ex:
            print(f"ERROR Activite row {self.row_num} {e}\n{ex}\n{row}")
            quit(1)
        return e

    def make_relations(self, e: Activite, row):
        try:
            e.personne = self.personnes[e.inpp]
            if e.id_technique_structure in self.structures:
                e.structure = self.structures[e.id_technique_structure]
            e.code_profession = self.code_professions[e.code_profession_id]
            if e.code_fonction not in self.fonctions:
                f = Fonction()
                f.code = e.code_fonction
                f.libelle = row["Libellé fonction"]
                self.fonctions[f.code] = f
            e.fonction = self.fonctions[e.code_fonction]
        except Exception as ex:
            print(f"ERROR Activite unknow FK row {self.row_num} {e}\n{ex}")
            quit(2)

    def update(self, e: Activite):
        if e.date_fin is not None:
            self.entities[e.key].date_fin = e.date_fin
        if e.date_maj is not None:
            self.entities[e.key].date_maj = e.date_maj
        self.nb_update_entity += 1


if __name__ == '__main__':
    art.tprint(config.name, "big")
    print("RPPS Activite Parser")
    print("====================")
    print(f"V{config.version}")
    print(config.copyright)
    print()
    parser = argparse.ArgumentParser(description="RPPS Activite Parser")
    parser.add_argument("path", help="Path")
    parser.add_argument("-e", "--echo", help="Sql Alchemy echo", action="store_true")
    args = parser.parse_args()
    context = Context()
    context.create(echo=args.echo, expire_on_commit=False)
    db_size = context.db_size()
    print(f"Database {context.db_name}: {db_size:.0f} Mb")
    rpp = RPPSActiviteParser(context)
    rpp.load(args.path, delimiter=';', encoding="UTF-8", header=True)
    print(f"New activite: {rpp.nb_new_entity}")
    print(f"Nb activite update: {rpp.nb_update_entity}")
    new_db_size = context.db_size()
    print(f"Database {context.db_name}: {new_db_size:.0f} Mb")
    print(f"Database grows: {new_db_size - db_size:.0f} Mb ({((new_db_size - db_size) / db_size) * 100:.1f}%)")
    print(f"Parse {rpp.row_num} rows in {time.perf_counter() - time0:.0f}s")

    # data/rpps/Activite_small.csv
    # data/rpps/Extraction_RPPS_Profil4_Activite_202310250948.csv
