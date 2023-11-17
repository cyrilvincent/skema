from typing import Dict, List, Tuple, Optional
from sqlalchemy.orm import joinedload

from rpps_diplome_obtenu_parser import RPPSDiplomeObtenuParser
from rpps_exercice_pro_parser import RPPSExerciceProParser
from rpps_personne_parser import RPPSPersonneParser
from sqlentities import Context, PersonneActivite, PAAdresse, Dept, CodeProfession, Diplome, Personne, ExercicePro, \
    Structure, Activite, DiplomeObtenu, SavoirFaireObtenu
from base_parser import BaseParser, time0
import argparse
import time
import art
import config


class RPPSSavoirFaireParser(RPPSDiplomeObtenuParser):

    def __init__(self, context):
        super().__init__(context)
        self.exercices_pro: Dict[Tuple[str, str, int], ExercicePro] = {}

    def load_cache(self):
        print("Making cache")
        l: List[SavoirFaireObtenu] = self.context.session.query(SavoirFaireObtenu).all()
        for e in l:
            self.entities[e.key] = e
        l: List[ExercicePro] = self.context.session.query(ExercicePro).all()
        for e in l:
            self.exercices_pro[e.key] = e
        l: List[Diplome] = self.context.session.query(Diplome).all()
        for d in l:
            self.diplomes[d.key] = d

    def mapper(self, row) -> SavoirFaireObtenu:
        e = SavoirFaireObtenu()
        try:
            e.inpp = row["Identification nationale PP"]
            e.code_sf = row["Code savoir-faire"]
            e.type_sf = row["Code type savoir-faire"]
            e.code_profession = int(row["Code profession"])
            e.categorie_pro = self.get_nullable(row["Code catégorie professionnelle"])
            e.date_reconnaissance = self.get_nullable_date(row["Date reconnaissance savoir-faire"])
            e.date_maj = self.get_nullable_date(row["Date de mise à jour savoir-faire"])
            e.date_abandon = self.get_nullable_date(row["Date abandon savoir-faire"])
        except Exception as ex:
            print(f"ERROR SavoirFaireObtenu row {self.row_num} {e}\n{ex}\n{row}")
            quit(1)
        return e

    def make_relations(self, e: SavoirFaireObtenu, row):
        try:
            e.exercice_pro = self.exercices_pro[(e.inpp, e.categorie_pro, e.code_profession)]
            if e.code_sf in self.diplomes:
                e.diplome = self.diplomes[e.code_sf]
            else:
                d = Diplome()
                d.code_diplome = e.code_sf
                d.code_type_diplome = e.type_sf
                d.libelle_type_diplome = row["Libellé type savoir-faire"]
                d.libelle_diplome = row["Libellé savoir-faire"]
                d.is_savoir_faire = True
                e.diplome = d
                self.diplomes[d.key] = d
                self.nb_new_diplome += 1
        except Exception as ex:
            print(f"ERROR SavoirFaireObtenu unknow FK row {self.row_num} {e}\n{ex}")
            quit(2)

    def update(self, e: SavoirFaireObtenu):
        self.entities[e.key].date_maj = e.date_maj
        if e.date_abandon is not None:
            self.entities[e.key].date_abandon = e.date_abandon
        self.nb_update_entity += 1

if __name__ == '__main__':
    art.tprint(config.name, "big")
    print("RPPS Savoir Faire Parser")
    print("========================")
    print(f"V{config.version}")
    print(config.copyright)
    print()
    parser = argparse.ArgumentParser(description="RPPS Savoir Faire Parser")
    parser.add_argument("path", help="Path")
    parser.add_argument("-e", "--echo", help="Sql Alchemy echo", action="store_true")
    args = parser.parse_args()
    context = Context()
    context.create(echo=args.echo, expire_on_commit=False)
    db_size = context.db_size()
    print(f"Database {context.db_name}: {db_size:.0f} Mb")
    rpp = RPPSSavoirFaireParser(context)
    rpp.load(args.path, delimiter=';', encoding="UTF-8", header=True)
    print(f"New savoir faire obtenu: {rpp.nb_new_entity}")
    print(f"Nb savoir faire update: {rpp.nb_update_entity}")
    print(f"New savoir faire diplomes : {rpp.nb_new_diplome}")
    new_db_size = context.db_size()
    print(f"Database {context.db_name}: {new_db_size:.0f} Mb")
    print(f"Database grows: {new_db_size - db_size:.0f} Mb ({((new_db_size - db_size) / db_size) * 100:.1f}%)")
    print(f"Parse {rpp.row_num} rows in {time.perf_counter() - time0:.0f} s")

    # data/rpps/SavoirFaire_small.csv
    # data/rpps/Extraction_RPPS_Profil4_SavoirFaire_202310250948.csv

