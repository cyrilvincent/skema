from typing import Dict, List
from sqlentities import Context, Structure, CategorieJuridique, SecteurActivite
from base_parser import BaseParser, time0
import argparse
import time
import art
import config


class RPPSStructureParser(BaseParser):

    def __init__(self, context):
        super().__init__(context)
        self.categorie_juridiques: Dict[int, CategorieJuridique] = {}
        self.secteur_activites: Dict[str, SecteurActivite] = {}

    def load_cache(self):
        print("Making cache")
        l: List[Structure] = self.context.session.query(Structure).all()
        for e in l:
            self.entities[e.key] = e
        l: List[CategorieJuridique] = self.context.session.query(CategorieJuridique).all()
        for e in l:
            self.categorie_juridiques[e.id] = e
        l: List[SecteurActivite] = self.context.session.query(SecteurActivite).all()
        for e in l:
            self.secteur_activites[e.code] = e

    def check_date(self, path):
        pass

    def mapper(self, row) -> Structure:
        e = Structure()
        try:
            e.type = row["Type de structure"]
            e.id_technique = row["Identifiant technique de la structure"]
            e.id_national = row["Identification nationale de la structure"]
            e.siret = self.get_nullable(row["Numéro SIRET"])
            e.siren = self.get_nullable(row["Numéro SIREN"])
            e.finess = self.get_nullable(row["Numéro FINESS Etablissement"])
            e.rpps = self.get_nullable(row["RPPS rang"])
            e.adeli = self.get_nullable(row["ADELI rang"])
            e.licence = self.get_nullable(row["Numéro licence officine"])
            e.date_ouverture = self.get_nullable_date(row["Date d'ouverture structure"])
            e.date_fermeture = self.get_nullable_date(row["Date de fermeture structure"])
            e.date_maj = self.get_nullable_date(row["Date de mise à jour structure"])
            e.ape = self.get_nullable(row["Code APE"])
            e.categorie_juridique_id = self.get_nullable_int(row["Code catégorie juridique"].strip()[:5])
            e.code_secteur_activite = self.get_nullable(row["Code secteur d'activité"])
            e.raison_sociale = self.get_nullable(row["Raison sociale"])
            e.enseigne = self.get_nullable(row["Enseigne commerciale"])
        except Exception as ex:
            print(f"ERROR Structure row {self.row_num} {e}\n{ex}\n{row}")
            quit(1)
        return e

    def update(self, e: Structure):
        if e.siret is not None:
            self.entities[e.key].siret = e.siret
        if e.siren is not None:
            self.entities[e.key].siren = e.siren
        if e.licence is not None:
            self.entities[e.key].licence = e.licence
        if e.date_fermeture is not None:
            self.entities[e.key].date_fermeture = e.date_fermeture
        if e.date_maj is not None:
            self.entities[e.key].date_maj = e.date_maj
        if e.enseigne is not None:
            self.entities[e.key].enseigne = e.enseigne
        if e.raison_sociale is not None:
            self.entities[e.key].raison_sociale = e.raison_sociale
        self.nb_update_entity += 1

    def make_relations(self, e: Structure, row):
        try:
            if e.categorie_juridique_id is not None:
                if e.categorie_juridique_id not in self.categorie_juridiques:
                    c = CategorieJuridique()
                    c.id = e.categorie_juridique_id
                    c.libelle = row["Libellé catégorie juridique"]
                    self.categorie_juridiques[c.id] = c
                e.categorie_juridique = self.categorie_juridiques[e.categorie_juridique_id]
            if e.secteur_activite_id is not None:
                if e.code_secteur_activite not in self.secteur_activites:
                    s = SecteurActivite()
                    s.code = e.code_secteur_activite
                    s.libelle = row["Libellé secteur d'activité"]
                    self.secteur_activites[s.code] = s
                e.secteur_activite = self.secteur_activites[e.code_secteur_activite]
        except Exception as ex:
            print(f"ERROR Structure unknow FK row {self.row_num} {e}\n{ex}")
            quit(2)

    def load(self, path: str, delimiter=';', encoding="utf8", header=False):
        out_path = path.replace(".csv", ".temp")
        self.strip_double_quotes_writer(path, out_path, encoding)
        super().load(out_path, delimiter, encoding, header)

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
    print("RPPS Stucture Parser")
    print("====================")
    print(f"V{config.version}")
    print(config.copyright)
    print()
    parser = argparse.ArgumentParser(description="RPPS Structure Parser")
    parser.add_argument("path", help="Path")
    parser.add_argument("-e", "--echo", help="Sql Alchemy echo", action="store_true")
    args = parser.parse_args()
    context = Context()
    context.create(echo=args.echo, expire_on_commit=False)
    db_size = context.db_size()
    print(f"Database {context.db_name}: {db_size:.0f} Mb")
    rpp = RPPSStructureParser(context)
    rpp.load(args.path, delimiter=';', encoding="UTF-8", header=True)
    print(f"New structure: {rpp.nb_new_entity}")
    print(f"Nb structure update: {rpp.nb_update_entity}")
    new_db_size = context.db_size()
    print(f"Database {context.db_name}: {new_db_size:.0f} Mb")
    print(f"Database grows: {new_db_size - db_size:.0f} Mb ({((new_db_size - db_size) / db_size) * 100:.1f}%)")
    print(f"Parse {rpp.row_num} rows in {time.perf_counter() - time0:.0f} s")

    # data/rpps/Structure_small.csv
    # data/rpps/Extraction_RPPS_Profil4_Structure_202310250948.csv
