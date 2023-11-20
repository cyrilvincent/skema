from typing import Dict, List, Tuple, Optional
from sqlalchemy.orm import joinedload

from rpps_diplome_obtenu_parser import RPPSDiplomeObtenuParser
from rpps_exercice_pro_parser import RPPSExerciceProParser
from rpps_personne_parser import RPPSPersonneParser
from sqlentities import Context, PersonneActivite, PAAdresse, Dept, CodeProfession, Diplome, Personne, ExercicePro, \
    Structure, Activite, DiplomeObtenu, Attribution, PersonneAttribution
from base_parser import BaseParser, time0
import argparse
import time
import art
import config


class RPPSAttributionParser(RPPSExerciceProParser):

    def __init__(self, context):
        super().__init__(context)
        self.attributions: Dict[str, Attribution] = {}
        self.nb_new_attribution = 0

    def load_cache(self):
        print("Making cache")
        l: List[PersonneAttribution] = self.context.session.query(PersonneAttribution).all()
        for e in l:
            self.entities[e.key] = e
        l: List[Personne] = self.context.session.query(Personne).all()
        for p in l:
            self.personnes[p.inpp] = p
        l: List[CodeProfession] = self.context.session.query(CodeProfession).all()
        for c in l:
            self.code_professions[c.id] = c
        l: List[Attribution] = self.context.session.query(Attribution).all()
        for a in l:
            self.attributions[a.code] = a

    def mapper(self, row) -> PersonneAttribution:
        e = PersonneAttribution()
        try:
            e.inpp = row["Identification nationale PP"]
            e.code = row["Code attribution"]
            e.code_profession_id = int(row["Code profession"])
            e.date_reconnaissance = self.get_nullable_date(row["Date de reconnaissance attribution"])
            e.date_abandon = self.get_nullable_date(row["Date d'abandon attribution"])
            e.date_maj = self.get_nullable_date(row["Date de mise à jour attribution"])
            e.categorie_pro = self.get_nullable(row["Code catégorie professionnelle"])
        except Exception as ex:
            print(f"ERROR Attribution row {self.row_num} {e}\n{ex}\n{row}")
            quit(1)
        return e

    def make_relations(self, e: PersonneAttribution, row):
        try:
            e.personne = self.personnes[e.inpp]
            e.code_profession = self.code_professions[e.code_profession_id]
            if e.code not in self.attributions:
                a = Attribution()
                a.code = e.code
                a.libelle = row["Libellé attribution"]
                self.attributions[a.code] = a
                self.nb_new_attribution += 1
            e.attribution = self.attributions[e.code]
        except Exception as ex:
            print(f"ERROR Attribution unknow FK row {self.row_num} {e}\n{ex}")
            quit(2)

    def update(self, e: PersonneAttribution):
        if e.date_maj is not None:
            self.entities[e.key].date_maj = e.date_maj
        if e.date_abandon is not None:
            self.entities[e.key].date_abandon = e.date_abandon
        self.nb_update_entity += 1

if __name__ == '__main__':
    art.tprint(config.name, "big")
    print("RPPS Attribution Perticuliere Parser")
    print("====================================")
    print(f"V{config.version}")
    print(config.copyright)
    print()
    parser = argparse.ArgumentParser(description="RPPS Attribution Parser")
    parser.add_argument("path", help="Path")
    parser.add_argument("-e", "--echo", help="Sql Alchemy echo", action="store_true")
    args = parser.parse_args()
    context = Context()
    context.create(echo=args.echo, expire_on_commit=False)
    db_size = context.db_size()
    print(f"Database {context.db_name}: {db_size:.0f} Mb")
    rpp = RPPSAttributionParser(context)
    rpp.load(args.path, delimiter=';', encoding="UTF-8", header=True)
    print(f"New personne attribution: {rpp.nb_new_entity}")
    print(f"Nb attribution update: {rpp.nb_update_entity}")
    print(f"New attribution : {rpp.nb_new_attribution}")
    new_db_size = context.db_size()
    print(f"Database {context.db_name}: {new_db_size:.0f} Mb")
    print(f"Database grows: {new_db_size - db_size:.0f} Mb ({((new_db_size - db_size) / db_size) * 100:.1f}%)")
    print(f"Parse {rpp.row_num} rows in {time.perf_counter() - time0:.0f} s")

    # data/rpps/Extraction_RPPS_Profil4_AttribPart_202310250948.csv

