from typing import Dict, List, Tuple, Optional
from sqlalchemy.orm import joinedload

from rpps_exercice_pro_parser import RPPSExerciceProParser
from rpps_personne_parser import RPPSPersonneParser
from sqlentities import Context, PersonneActivite, PAAdresse, Dept, CodeProfession, Diplome, Personne, ExercicePro, \
    Structure, Activite, DiplomeObtenu
from base_parser import BaseParser, time0
import argparse
import time
import art
import config


class RPPSDiplomeObtenuParser(RPPSExerciceProParser):

    def __init__(self, context):
        super().__init__(context)
        self.personnes: Dict[str, Personne] = {}
        self.diplomes : Dict[str, Diplome] = {}
        self.nb_new_diplome = 0

    def load_cache(self):
        print("Making cache")
        l: List[DiplomeObtenu] = self.context.session.query(DiplomeObtenu).all()
        for e in l:
            self.entities[e.key] = e
        l: List[Personne] = self.context.session.query(Personne).all()
        for p in l:
            self.personnes[p.inpp] = p
        l: List[Diplome] = self.context.session.query(Diplome).all()
        for d in l:
            self.diplomes[d.key] = d

    def mapper(self, row) -> DiplomeObtenu:
        e = DiplomeObtenu()
        try:
            e.inpp = row["Identification nationale PP"]
            e.type_diplome = row["Code type diplôme obtenu"]
            e.code_diplome = row["Code diplôme obtenu"]
            e.lieu_obtention = row["Code lieu obtention"]
            e.date_obtention = self.get_nullable_date(row["Date d'obtention diplôme"])
            e.date_maj = self.get_nullable_date(row["Date de mise à jour diplôme obtenu"])
            e.numero = self.get_nullable(row["Numéro diplôme"])
        except Exception as ex:
            print(f"ERROR Diplome row {self.row_num} {e}\n{ex}\n{row}")
            quit(1)
        return e

    def make_relations(self, e: DiplomeObtenu, row):
        try:
            e.personne = self.personnes[e.inpp]
            if e.code_diplome in self.diplomes:
                e.diplome = self.diplomes[e.code_diplome]
            else:
                d = Diplome()
                d.code_diplome = e.code_diplome
                d.code_type_diplome = e.type_diplome
                d.libelle_type_diplome = row["Libellé type diplôme obtenu"]
                d.libelle_diplome = row["Libellé diplôme obtenu"]
                d.is_savoir_faire = False
                e.diplome = d
                self.diplomes[d.key] = d
                self.nb_new_diplome += 1
        except Exception as ex:
            print(f"ERROR DiplomeObtenu unknow FK row {self.row_num} {e}\n{ex}")
            quit(2)

    def update(self, e: DiplomeObtenu):
        if e.date_maj is not None:
            self.entities[e.key].date_maj = e.date_maj
        if e.numero is not None:
            self.entities[e.key].numero = e.numero
        self.nb_update_entity += 1

if __name__ == '__main__':
    art.tprint(config.name, "big")
    print("RPPS Diplome Obtenu Parser")
    print("==========================")
    print(f"V{config.version}")
    print(config.copyright)
    print()
    parser = argparse.ArgumentParser(description="RPPS Diplome Obtenu Parser")
    parser.add_argument("path", help="Path")
    parser.add_argument("-e", "--echo", help="Sql Alchemy echo", action="store_true")
    args = parser.parse_args()
    context = Context()
    context.create(echo=args.echo, expire_on_commit=False)
    db_size = context.db_size()
    print(f"Database {context.db_name}: {db_size:.0f} Mb")
    rpp = RPPSDiplomeObtenuParser(context)
    rpp.load(args.path, delimiter=';', encoding="UTF-8", header=True)
    print(f"New diplome obtenu: {rpp.nb_new_entity}")
    print(f"Nb diplome obtenu update: {rpp.nb_update_entity}")
    print(f"New diplome : {rpp.nb_new_diplome}")
    new_db_size = context.db_size()
    print(f"Database {context.db_name}: {new_db_size:.0f} Mb")
    print(f"Database grows: {new_db_size - db_size:.0f} Mb ({((new_db_size - db_size) / db_size) * 100:.1f}%)")
    print(f"Parse {rpp.row_num} rows in {time.perf_counter() - time0:.0f} s")

    # data/rpps/DiplomeObtenu_small.csv
    # data/rpps/Extraction_RPPS_Profil4_DiplObt_202310250948.csv

