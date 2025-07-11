import csv
import datetime

from sqlalchemy.orm import joinedload

from OSM_matcher import OSMMatcher
from sqlentities import Context, Cabinet, PS, AdresseRaw, PSCabinetDateSource, Profession, Dept, Commune, Iris
from base_parser import BaseParser
import argparse
import art
import config
import numpy as np


class OldVCommuneParser(BaseParser):

    def __init__(self, context):
        super().__init__(context)
        self.depts: dict[str, Dept] = {}
        self.communes: dict[str, Commune] = {}
        self.nb_new_commune = 0
        self.nb_update_commune = 0

    def load_cache(self):
        l = self.context.session.query(Dept).all()
        for d in l:
            self.depts[d.num] = d
            self.nb_ram += 1
        l = self.context.session.query(Commune).all()
        for c in l:
            self.communes[c.code] = c
            self.nb_ram += 1
        print(f"{self.nb_ram} objects in cache")

    def check_date(self, path):
        pass

    def mapper(self, row) -> Commune:
        e = Commune()
        try:
            e.code = row["COM"]
            code: str = e.code
            if code.startswith("2A"):
                code = code.replace("2A", "201")
            elif code.startswith("2B"):
                code = code.replace("2B", "202")
            e.id = int(code)
            e.type = row["TYPECOM"]
            e.nom = row["LIBELLE"]
            e.nom_norm = self.normalize_string(e.nom).upper()
            e.parent = self.get_nullable(row["COMPARENT"])
        except Exception as ex:
            print(f"ERROR v_commune row {self.row_num} {e}\n{ex}")
            quit(2)
        return e

    def parse_row(self, row):
        dept_num = row["COM"][:2]
        if dept_num in self.depts:
            commune = self.mapper(row)
            if commune.code not in self.communes:  # Old commune with new id
                print(f"Cas anormal 99 {commune}")
                quit(99)
            else:  # Old commune with same id
                if commune.type == "COM" and commune.parent is not None:
                    print(f"Cas anormal 98 {commune}")
                    quit(98)
                if commune.type != "COM" and commune.parent is None:
                    print(f"Cas anormal 97 {commune}")
                    quit(97)
                if commune.type != "COM" and commune.parent is not None:
                    parent = self.communes[commune.parent]
                    commune = self.communes[commune.code]
                    if commune.date_fin is not None:
                        if commune.parent is None:
                            commune.lon = parent.lon
                            commune.lat = parent.lat
                            commune.epci_id = parent.epci_id
                            commune.epci_nom = parent.epci_nom
                            commune.bassin_vie_id = parent.bassin_vie_id
                            commune.bassin_vie_nom = parent.bassin_vie_nom
                            commune.zone_emploi_id = parent.zone_emploi_id
                            commune.zone_emploi_nom = parent.zone_emploi_nom
                            commune.arr_dept_id = parent.arr_dept_id
                            commune.arr_dept_nom = parent.arr_dept_nom
                            commune.parent = parent.code
                            self.context.session.commit()
                            self.nb_update_commune += 1


class OldVCommuneDepuis1943Parser(OldVCommuneParser):

    def __init__(self, context):
        super().__init__(context)

    def get_date(self, s: str) -> datetime.date:
        return datetime.date.fromisoformat(s)

    def mapper(self, row) -> Commune:
        e = Commune()
        try:
            e.code = row["COM"]
            code: str = e.code
            if code.startswith("2A"):
                code = code.replace("2A", "201")
            elif code.startswith("2B"):
                code = code.replace("2B", "202")
            e.id = int(code)
            e.type = row["TYPECOM"]
            e.nom = row["LIBELLE"]
            e.nom_norm = self.normalize_string(e.nom).upper()
            e.date_debut = self.get_nullable_date(row["DATE_DEBUT"])
            e.date_fin = self.get_nullable_date(row["DATE_FIN"])
        except Exception as ex:
            print(f"ERROR v_commune_depuis_1943 row {self.row_num} {e}\n{ex}")
            quit(2)
        return e

    def parse_row(self, row):
        dept_num = row["COM"][:2]
        if dept_num in self.depts:
            commune = self.mapper(row)
            if commune.code not in self.communes:  # Old commune with new id
                dept = self.depts[dept_num]
                commune.dept = dept
                commune.bassin_vie_id = commune.bassin_vie_nom = commune.arr_dept_id = commune.arr_dept_nom = ""
                self.communes[commune.code] = commune
                self.context.session.add(commune)
                # self.context.session.commit()
                self.nb_new_commune += 1
            else:  # Old commune with same id
                old_commune = commune
                commune = self.communes[old_commune.code]
                if old_commune.date_fin is not None:
                    if commune.date_fin is None and commune.old_nom is None:
                        commune.old_type = old_commune.type
                        commune.old_nom = old_commune.nom
                        commune.old_nom_norm = old_commune.nom_norm
                        commune.old_date_fin = old_commune.date_fin
                        self.context.session.commit()
                        self.nb_update_commune += 1
                elif commune.date_debut is None:
                    commune.date_debut = old_commune.date_debut
                    self.context.session.commit()
                    self.nb_update_commune += 1


class OldCommuneOSM:

    def __init__(self, context):
        self.osm = OSMMatcher()
        self.context = context

    def match(self):
        l: list[Commune] = self.context.session.query(Commune).filter(Commune.lon.is_(None)).all()
        for commune in l:
            osm = self.osm.get_osm_from_adresse(None, None, commune.nom_norm, None)
            if osm is not None:
                print(f"{commune.nom_norm} => ({osm.lon},{osm.lat})")
                commune.lon = osm.lon
                commune.lat = osm.lat
                self.context.session.commit()
            else:
                print(f"{commune.nom_norm} => None")






if __name__ == '__main__':
    art.tprint(config.name, "big")
    print("Old Commune Parser")
    print("==================")
    print(f"V{config.version}")
    print(config.copyright)
    print()
    parser = argparse.ArgumentParser(description="Old Commune Parser")
    parser.add_argument("-e", "--echo", help="Sql Alchemy echo", action="store_true")
    args = parser.parse_args()
    context = Context()
    context.create(echo=args.echo, expire_on_commit=False)
    db_size = context.db_size()
    print(f"Database {context.db_name}: {db_size:.0f} MB")
    # ocd1943p = OldVCommuneDepuis1943Parser(context)
    # ocd1943p.load("data/iris/cog_ensemble_2025_csv/v_commune_depuis_1943.csv", delimiter=",", encoding="utf8",
    #               header=True, quotechar='"')
    # print(f"New commune: {ocd1943p.nb_new_commune}")
    # print(f"Update commune: {ocd1943p.nb_update_commune}")
    ovcp = OldVCommuneParser(context)
    ovcp.load("data/iris/cog_ensemble_2025_csv/v_commune_2025.csv", delimiter=",", encoding="utf8", header=True,
              quotechar='"')
    print(f"Update commune: {ovcp.nb_update_commune}")
    # oco = OldCommuneOSM(context)
    # oco.match()
    new_db_size = context.db_size()
    print(f"Database {context.db_name}: {new_db_size:.0f} MB")
    print(f"Database grows: {new_db_size - db_size:.0f} MB ({((new_db_size - db_size) / db_size) * 100:.1f}%)")
