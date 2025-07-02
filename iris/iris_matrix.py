from typing import Dict, List
from sqlalchemy.orm import joinedload
from sqlentities import Context, BAN, AdresseNorm, Source, OD, CommuneMatrix, Commune, IrisMatrix, Iris
import argparse
import time
import art
import config
import numpy as np
import math


time0 = time.perf_counter()


class IrisMatrixService:

    def __init__(self, context):
        self.context = context
        self.row_num = 0
        self.nb_ram = 0
        self.nb_entity = 0
        self.ods: dict[tuple[str, str], OD] = {}
        self.entities: set[tuple[int, int]] = set()
        self.iriss: dict[int, Iris] = {}
        self.max_direct_distance = 200
        self.max_lon_lat = 2
        self.nb_commit = 10000
        self.total = 0

    def make_cache(self):
        print("Making cache")
        l: List[Iris] = self.context.session.query(Iris).options(
            joinedload(Iris.commune).joinedload(Commune.dept)).all()
        for e in l:
            self.iriss[e.id] = e
            self.nb_ram += 1
        print(f"{self.nb_ram} objects in cache")
        l: List[OD] = self.context.session.query(OD).all()
        print(f"{self.nb_ram + 1} objects in cache")
        for e in l:
            self.ods[str(e.com1), str(e.com2)] = e
            self.nb_ram += 1
        print(f"{self.nb_ram} objects in cache")
        l: List[IrisMatrix] = self.context.session.query(IrisMatrix)
        print(f"{self.nb_ram + 1} objects in cache")
        for e in l:
            self.entities.add((e.iris_id_from, e.iris_id_to))
            self.nb_ram += 1
        print(f"{self.nb_ram} objects in cache")

    def are_rapid_near(self, lon1, lat1, lon2, lat2) -> bool:
        lat = abs(lat1 - lat2)
        if lat > self.max_lon_lat:
            return False
        lon = abs(lon1 - lon2)
        return lon < self.max_lon_lat

    def compute_distance(self, lon1, lat1, lon2, lat2):
        r = 6373.0
        lat1 = math.radians(lat1)
        lon1 = math.radians(lon1)
        lat2 = math.radians(lat2)
        lon2 = math.radians(lon2)
        dlon = lon2 - lon1
        dlat = lat2 - lat1
        a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        distance = r * c
        return distance

    def compute_proximity(self, iris1: Iris, iris2: Iris) -> int:
        if iris1.grd_quart_code is not None and iris2.grd_quart_code is not None:
            if iris1.grd_quart_code == iris2.grd_quart_code:
                return 1
        if iris1.arrondissement_code == iris2.arrondissement_code:
            return 2
        com1, com2 = iris1.commune, iris2.commune
        if com1.arr_dept_id == com2.arr_dept_id:
            return 3
        if com1.zone_emploi_id is not None and com2.zone_emploi_id is not None:
            if com1.zone_emploi_id == com2.zone_emploi_id:
                return 4
        if com1.bassin_vie_id == com2.bassin_vie_id:
            return 5
        if com1.epci_id is not None and com2.epci_id is not None and com1.epci_id == com2.epci_id:
            return 6
        if com1.dept_id == com2.dept_id:
            return 7
        if com1.dept.region_id == com2.dept.region_id:
            return 8
        return 9

    def create(self):
        print("Create iris matrix")
        self.total = len(self.iriss) ** 2
        for iris_id1 in self.iriss.keys():
            for iris_id2 in self.iriss.keys():
                self.row_num += 1
                if iris_id1 != iris_id2:
                    if (iris_id1, iris_id2) not in self.entities:
                        e = IrisMatrix(iris_id1, iris_id2)
                        if e.iris_id_from in self.iriss and e.iris_id_to in self.iriss:
                            iris1 = self.iriss[e.iris_id_from]
                            iris2 = self.iriss[e.iris_id_to]
                            if not iris1.is_irisee and not iris2.is_irisee:
                                od_key = (iris1.commune.code, iris2.commune.code)
                                if od_key in self.ods:
                                    od = self.ods[od_key]
                                    if od.km != 9999:
                                        e.google_km = int(round(od.km))
                                        e.google_hc = int(od.hc)
                                        e.google_hp = int(od.hp)
                            km = 9999
                            near = self.are_rapid_near(iris1.lon, iris1.lat, iris2.lon, iris2.lat)
                            if near:
                                d = self.compute_distance(iris1.lon, iris1.lat, iris2.lon, iris2.lat)
                                km = int(round(d))
                            if km < self.max_direct_distance or e.google_km is not None:
                                if near:
                                    e.direct_km = km
                                    e.proximity = self.compute_proximity(iris1, iris2)
                                self.context.session.add(e)
                                self.nb_entity += 1
                                if self.nb_entity % self.nb_commit == 0:
                                    duration = time.perf_counter() - time0
                                    print(f"Creating {self.nb_entity} rows "
                                          f"{self.row_num * 100 / self.total:.2f}% in {int(duration)}s")
                                    self.row_num += 1
                                    self.context.session.commit()
        self.context.session.commit()


if __name__ == '__main__':
    art.tprint(config.name, "big")
    print("Iris Matrix Service")
    print("===================")
    print(f"V{config.version}")
    print(config.copyright)
    print()
    parser = argparse.ArgumentParser(description="Iris Matrix Service")
    parser.add_argument("-e", "--echo", help="Sql Alchemy echo", action="store_true")
    args = parser.parse_args()
    context = Context()
    context.create(echo=args.echo, expire_on_commit=False)
    ims = IrisMatrixService(context)
    print(f"Database {ims.context.db_name}: {ims.context.db_size():.0f} MB")
    ims.make_cache()
    ims.create()
    print(f"Parse {ims.nb_entity} entities in {time.perf_counter() - time0:.0f} s")

    # select distinct(iris.commune.id) from iris.iris
    # join iris.commune on iris.iris.commune_id = iris.commune.id
    # where is_irisee = true
    # -- 1806
    #
    # SELECT iris.commune.* as c
    # FROM iris.commune
    # JOIN iris.iris ON iris.iris.commune_id = iris.commune.id
    # GROUP BY iris.commune.id
    # HAVING COUNT(iris.iris.id) > 1;
    # -- 1806

    # nbrow with google_km in commune_matrix = 8156576 23%
    # nbrow wih google_km 14.6M 3.7%
    # total 393M
