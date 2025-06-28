import csv
from sqlalchemy.orm import joinedload
from sqlentities import Context, Cabinet, PS, AdresseRaw, PSCabinetDateSource, Profession, Dept, Commune, Iris
from base_parser import BaseParser
import argparse
import art
import config
import numpy as np



class IrisParser(BaseParser):

    def __init__(self, context):
        super().__init__(context)
        csv.field_size_limit(1000000)
        self.depts: dict[str, Dept] = {}
        self.communes: dict[str, Commune] = {}
        self.nb_new_commune = 0
        # todo add dept field to server & schema iris


    def load_cache(self):
        l = self.context.session.query(Dept).all()
        for d in l:
            self.depts[d.num] = d
            self.nb_ram += 1
        l = self.context.session.query(Commune).all()
        for c in l:
            self.communes[c.code] = c
            self.nb_ram += 1
        l = self.context.session.query(Iris).all()
        for i in l:
            self.entities[i.code] = i
            self.nb_ram += 1
        print(f"{self.nb_ram} objects in cache")

    def check_date(self, path):
        pass

    def dept_mapper(self, row) -> Dept:
        e = Dept()
        try:
            e.num = row["Code Officiel Département"]
            e.name = row["Nom Officiel Département"]
            e.region_id = self.get_nullable_int(row["Code Officiel Région"])
            e.region_name = row["Nom Officiel Région"]
        except Exception as ex:
            print(f"ERROR dept row {self.row_num} {e}\n{ex}")
            quit(1)
        return e

    def commune_mapper(self, row) -> Commune:
        e = Commune()
        try:
            e.code = row["Code Officiel Commune"]
            code: str = e.code
            if code.startswith("2A"):
                code = code.replace("2A", "201")
            elif code.startswith("2B"):
                code = code.replace("2B", "202")
            e.id = int(code)
            e.nom = row["Nom Officiel Commune"]
            e.nom_norm = self.normalize_string(e.nom).upper()
            e.epci_id = self.get_nullable_int(row["Code Officiel EPCI"])
            e.epci_nom = self.get_nullable(row["Nom Officiel EPCI"])
            e.bassin_vie_id = row["Code Officiel Bassin vie 2022"]
            e.bassin_vie_nom = row["Nom Officiel Bassin vie 2022"]
            e.zone_emploi_id = self.get_nullable_int(row["Code Officiel Zone emploi 2020"])
            e.zone_emploi_nom = self.get_nullable(row["Nom Officiel Zone emploi 2020"])
            e.arr_dept_id = row["Code Officiel Arrondissement départemental"]
            e.arr_dept_nom = row["Nom Officiel Arrondissement départemental"]
        except Exception as ex:
            print(f"ERROR commune row {self.row_num} {e}\n{ex}")
            quit(1)
        return e

    def mapper(self, row) -> Iris:
        e = Iris()
        try:
            e.code = row["Code Officiel IRIS"]
            code: str = e.code
            if code.startswith("2A"):
                code = code.replace("2A", "201")
            elif code.startswith("2B"):
                code = code.replace("2B", "202")
            e.id = int(code)
            e.is_irisee = True
            e.nom = row["Nom Officiel IRIS"]
            if e.nom.endswith("(commune non irisée)"):
                e.nom = e.nom[:-20].strip()
                e.is_irisee = False
            e.nom_norm = self.normalize_string(e.nom).upper()
            lat_lons = row["\ufeffGeo Point"].split(",")
            e.lon = float(lat_lons[1].strip())
            e.lat = float(lat_lons[0].strip())
            e.arrondissement_code = self.get_nullable(row["Code Officiel Commune / Arrondissement Municipal"])
            e.arrondissement_nom = self.get_nullable(row["Nom Officiel Commune / Arrondissement Municipal"])
            if row["Type"] == "commune":
                e.type = "C"
            elif row["Type"] == "iris divers":
                e.type = "D"
            else:
                e.type = row["Type"].upper()[8]
            e.grd_quart_code = self.get_nullable(row["Code Grand Quartier"])
            e.grd_quart_nom = self.get_nullable(row["Libellé Grand Quartier"])
            if e.grd_quart_nom == "Sans objet ou non disponible":
                e.grd_quart_nom = None
            e.in_ctu = row["Fait Partie d'une CTU"] == "Oui"
        except Exception as ex:
            print(f"ERROR iris row {self.row_num} {e}\n{ex}")
            quit(2)
        return e

    def parse_row(self, row):
        dept_temp = self.dept_mapper(row)
        if dept_temp.num in self.depts:
            dept = self.depts[dept_temp.num]
            if dept.name is None:
                dept.name = dept_temp.name
                dept.region_id = dept_temp.region_id
                dept.region_name = dept_temp.region_name
            commune = self.commune_mapper(row)
            if commune.code not in self.communes:
                self.communes[commune.code] = commune
                commune.dept = dept
                self.context.session.add(commune)
                self.nb_new_commune += 1
            commune = self.communes[commune.code]
            iris = self.mapper(row)
            if iris.code not in self.entities:
                self.entities[iris.code] = iris
                iris.commune = commune
                self.context.session.add(iris)
                self.context.session.commit()
                self.nb_new_entity += 1
            iris = self.entities[iris.code]

    def compute_commune_lon_lat(self):
        print("Compute commune lon & lat")
        communes = (self.context.session.query(Commune)
                    .options(joinedload(Commune.iriss)).filter(Commune.lon.is_(None)).all())
        for commune in communes:
            if len(commune.iriss) > 0:
                matrix = [[iris.lon, iris.lat] for iris in commune.iriss]
                matrix = np.array(matrix)
                vector = np.mean(matrix, axis=0)
                commune.lon = vector[0]
                commune.lat = vector[1]
        self.context.session.commit()



if __name__ == '__main__':
    art.tprint(config.name, "big")
    print("IRIS Parser")
    print("=========")
    print(f"V{config.version}")
    print(config.copyright)
    print()
    parser = argparse.ArgumentParser(description="IRIS Parser")
    parser.add_argument("path", help="Path")
    parser.add_argument("-e", "--echo", help="Sql Alchemy echo", action="store_true")
    args = parser.parse_args()
    context = Context()
    context.create(echo=args.echo, expire_on_commit=False)
    db_size = context.db_size()
    print(f"Database {context.db_name}: {db_size:.0f} MB")
    ip = IrisParser(context)
    ip.load(args.path, encoding="utf8", header=True)
    ip.compute_commune_lon_lat()
    print(f"New iris: {ip.nb_new_entity}")
    print(f"New commune: {ip.nb_new_commune}")
    new_db_size = context.db_size()
    print(f"Database {context.db_name}: {new_db_size:.0f} MB")
    print(f"Database grows: {new_db_size - db_size:.0f} MB ({((new_db_size - db_size) / db_size) * 100:.1f}%)")

    # data/iris/georef-france-iris.csv

    # Nb commune = 34806
    # Commune² = 1 211 457 636
    # Commune² / 2 - Commune = 605 694 012
    # OD = 16 615 447
    # OD COM1 distinct = 34875 = COM2 uniquement avec le département voisins
    # adresse_norm + ban = 14063 iris, 5877 cp
