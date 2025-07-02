from typing import Dict, List
from sqlalchemy.orm import joinedload
from sqlentities import Context, BAN, AdresseNorm, Source, OD, CommuneMatrix, Commune
import argparse
import time
import art
import config
import numpy as np
import math


time0 = time.perf_counter()


class CommuneMatrixService:

    def __init__(self, context, all):
        self.context = context
        self.all = all
        self.row_num = 0
        self.nb_ram = 0
        self.nb_entity = 0
        self.ods: dict[tuple[str, str], OD] = {}
        self.entities: dict[tuple[int, int], CommuneMatrix] = {}
        self.communes: dict[int, Commune] = {}
        self.ban_communes: set[int] = set()
        self.max_direct_distance = 200
        self.max_lon_lat = 2.0
        self.nb_commit = 100000

    def make_cache(self):
        print("Making cache")
        self.ods = {}
        l: List[Commune] = self.context.session.query(Commune).options(joinedload(Commune.dept)).all()
        for e in l:
            self.communes[e.id] = e
            self.nb_ram += 1
        print(f"{self.nb_ram} objects in cache")
        l: List[AdresseNorm] = (self.context.session.query(AdresseNorm).options(joinedload(AdresseNorm.ban))
                                .filter(AdresseNorm.ban_id.isnot(None)).all())
        for e in l:
            if e.ban.code_insee not in self.ban_communes:
                self.ban_communes.add(e.ban.code_insee)
                self.nb_ram += 1
        print(f"{self.nb_ram} objects in cache")
        l: List[CommuneMatrix] = self.context.session.query(CommuneMatrix).all()
        print(f"{self.nb_ram + 1} objects in cache")
        for e in l:
            self.entities[(e.code_id_low, e.code_id_high)] = e
            self.nb_ram += 1
        print(f"{self.nb_ram} objects in cache")

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

    def are_rapid_near(self, lon1, lat1, lon2, lat2) -> bool:
        lat = abs(lat1 - lat2)
        if lat > self.max_lon_lat:
            return False
        lon = abs(lon1 - lon2)
        return lon < self.max_lon_lat

    def compute_proximity(self, com1: Commune, com2: Commune) -> int:
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

    def create_from_od(self):
        print("Creating commune matrix for the first time")
        l: List[OD] = self.context.session.query(OD).filter(OD.com1 != OD.com2)
        print(f"Reading OD")
        for od in l:
            key = (od.com1, od.com2) if od.com1 < od.com2 else (od.com2, od.com1)
            if key not in self.ods:
                self.ods[key] = od
                if od.com1.isnumeric() and od.com2.isnumeric():
                    dept1 = int(od.com1[:2])
                    dept2 = int(od.com2[:2])
                    if dept1 < 96 and dept2 < 96:
                        e = CommuneMatrix(int(od.com1), int(od.com2))
                        if od.km != 9999:
                            e.google_km = int(round(od.km))
                            e.google_hc = int(od.hc)
                            e.google_hp = int(od.hp)
                        self.context.session.add(e)
                        if self.nb_entity % 100000 == 0:
                            duration = time.perf_counter() - time0 + 1e-6
                            print(f"Creating {self.nb_entity} entities in {int(duration)}s")
                        self.nb_entity += 1
                        if self.nb_entity % self.nb_commit == 0:
                            self.context.session.commit()
        self.context.session.commit()

    def compute_distances(self):
        print("Compute distances")
        total = len(self.communes) ** 2
        nb_pair = 0
        for com1 in self.communes.keys():
            for com2 in self.communes.keys():
                nb_pair += 1
                if com1 != com2:
                    key = (com1, com2) if com1 < com2 else (com2, com1)
                    if key not in self.entities:
                        e = CommuneMatrix(com1, com2)
                    else:
                        e = self.entities[key]
                    if e.direct_km is None:
                        if (self.all or e.google_km is not None or
                                str(e.code_id_low) in self.ban_communes or str(e.code_id_high) in self.ban_communes):
                            if e.code_id_low in self.communes and e.code_id_high in self.communes:
                                commune1 = self.communes[e.code_id_low]
                                commune2 = self.communes[e.code_id_high]
                                if self.are_rapid_near(commune1.lon, commune1.lat, commune2.lon, commune2.lat):
                                    d = self.compute_distance(commune1.lon, commune1.lat, commune2.lon, commune2.lat)
                                    km = int(round(d))
                                    if km < self.max_direct_distance:
                                        e.direct_km = km
                                        e.proximity = self.compute_proximity(commune1, commune2)
                                        self.entities[key] = e
                                        if e.id is None:
                                            self.context.session.add(e)
                                            self.nb_entity += 1
                                        if self.row_num % 100000 == 0:
                                            duration = time.perf_counter() - time0 + 1e-6
                                            print(f"Reading {self.row_num} entities {nb_pair * 100 / total:.1f}% in {int(duration)}s")
                                        self.row_num += 1
                                        if self.row_num % self.nb_commit == 0:
                                            self.context.session.commit()
        self.context.session.commit()








if __name__ == '__main__':
    art.tprint(config.name, "big")
    print("Commune Matrix Service")
    print("======================")
    print(f"V{config.version}")
    print(config.copyright)
    print()
    parser = argparse.ArgumentParser(description="Commune Matrix Service")
    parser.add_argument("-e", "--echo", help="Sql Alchemy echo", action="store_true")
    parser.add_argument("-a", "--all", help="All pairs", action="store_true")
    args = parser.parse_args()
    context = Context()
    context.create(echo=args.echo, expire_on_commit=False)
    cms = CommuneMatrixService(context, args.all)
    print(f"Database {cms.context.db_name}: {cms.context.db_size():.0f} MB")
    # cms.create_from_od()
    cms.make_cache()
    cms.compute_distances()
    print(f"Parse {cms.nb_entity} entities in {time.perf_counter() - time0:.0f} s")

    # 62 Million of pair / 605 Million
    # 61.6 Million of pairs with direct_km
    # sqrt * 2 = 16000
    # 34518 / 34806 communes low
    # 34521 / 34806 communes high

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

    # nb_row without google_km = 53798988 87%
    # nbrow with google_km = 8156576 23%
