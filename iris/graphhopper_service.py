from threading import Thread
from typing import Optional, Tuple
from urllib import parse, request

from sqlalchemy.orm import joinedload

from sqlentities import Context, BAN, OSM, AdresseNorm, Commune, CommuneMatrix
import argparse
import time
import art
import config
import numpy as np
import ssl
import urllib.request
import urllib.parse
import urllib.error
import json
import re

time0 = time.perf_counter()


class GraphHopperService:

    def __init__(self, port=8989):
        self.url = f"http://localhost:{port}/route?key"

    def get_json_from_lon_lat(self, lon1: float, lat1: float, lon2: float, lat2: float) -> str:
        dict = {"profile": "car", "alternative_route.max_paths": 1, "algorithm": "astarbi",
                "elevation": False, "instructions": False, "details": [], "snap_preventions": [],
                "points": [[lon1, lat1], [lon2, lat2]]}
        data = json.dumps(dict).encode("utf-8")
        req = request.Request(self.url, data=data, headers={'Content-Type': 'application/json'})
        with urllib.request.urlopen(req) as response:
            s = response.read()
            return s

    def get_distances_from_json(self, js: str) -> tuple[int, int] | None:
        dict = json.loads(js)
        if len(dict["paths"]) > 0:
            path = dict["paths"][0]
            return int(round(path["distance"] / 1000)), int(round(path["time"] / 60000))
        return None

    def test(self):
        print(f"Test GraphHopper")
        js = self.get_json_from_lon_lat(5.554176, 45.1084288, 5.7, 45.203)
        print(js)
        km, min = self.get_distances_from_json(js)
        print(km, min)
        if km > 20 and min > 20:
            print("Graphhopper is OK")
        else:
            print(f"Graphhopper problem")
            quit(1)


class GraphHopperIrisService(Thread):

    def __init__(self, context, graphhopper_service: GraphHopperService,
                 num_thread: int, total_thread: int, distance_min: int, distance_max: int):
        super().__init__()
        self.context = context
        self.service = graphhopper_service
        self.num_thread = num_thread
        self.total_thread = total_thread
        self.distance_min = distance_min
        self.distance_max = distance_max
        self.nb_entity = 0
        self.total = 0

    def get_commune_by_id(self, id: int) -> Commune:
        return self.context.session.get(Commune, id)

    def get_commune_by_code(self, code: str) -> Commune:
        return self.context.session.query(Commune.code == code).one()

    def any_in(self, l: list[str], s: str) -> bool:
        s = s.upper()
        for value in l:
            if value in s:
                return True
        return False

    def get_heure_pleine(self, min: int, commune1: Commune, commune2: Commune) -> int:  # todo paris puis bordeaux, toulouse, marseille, lyon puis epci
        coef = 1.0
        top5 = ["LYON", "MARSEILLE", "BORDEAUX", "NICE"]
        if "PARIS" in commune1.epci_nom.upper() and "PARIS" in commune2.epci_nom.upper():
            coef = 1.7
        if "PARIS" in commune1.epci_nom.upper() or "PARIS" in commune2.epci_nom.upper():
            coef = 1.5
        elif self.any_in(top5, commune1.epci_nom) and self.any_in(top5, commune2.epci_nom):
            coef = 1.4
        elif self.any_in(top5, commune1.epci_nom) or self.any_in(top5, commune2.epci_nom):
            coef = 1.3
        elif len(commune1.iriss) > 4 or len(commune2.iriss) > 4:
            coef = 1.2
        elif len(commune1.iriss) > 1 or len(commune2.iriss) > 1:
            coef = 1.1
        return int(min * coef) + 1

    def gh_distance_from_communes(self, commune1: Commune, commune2: Commune) -> tuple[int | None, int | None]:
        if commune1.lon is not None and commune2.lon is not None:
            js = self.service.get_json_from_lon_lat(commune1.lon, commune1.lat, commune2.lon, commune2.lat)
            km, min = self.service.get_distances_from_json(js)
            return km, min
        return None, None

    def gh_distance(self, commune_matrix: CommuneMatrix):
        commune1 = self.get_commune_by_id(commune_matrix.code_id_low)
        commune2 = self.get_commune_by_id(commune_matrix.code_id_high)
        time1 = time.perf_counter()
        km, min = self.gh_distance_from_communes(commune1, commune2)
        if km is not None:
            duration1 = time.perf_counter() - time1
            duration0 = time.perf_counter() - time0
            print(f"Thread {self.num_thread} {commune_matrix.id} "
                  f"{commune_matrix.code_id_low}=>{commune_matrix.code_id_high}: {km}km {min}min "
                  f"@{duration1:.1f}s/query {self.nb_entity + 1} rows ({(self.nb_entity / self.total) * 100:.2f}%) in "
                  f"{int(duration0)}s")
            commune_matrix.route_km = km
            commune_matrix.route_min = min
            commune_matrix.route_hp_km = self.get_heure_pleine(min, commune1, commune2)

    def gh_distances(self):
        print("Compute GraphHopper distances")
        l = self.context.session.query(CommuneMatrix).filter(
            (CommuneMatrix.route_km.is_(None)) &
            (CommuneMatrix.direct_km.isnot(None)) &
            (CommuneMatrix.direct_km >= self.distance_min) &
            (CommuneMatrix.direct_km <= self.distance_max) &
            (CommuneMatrix.id % self.total_thread == self.num_thread)).all()
        self.total = len(l)
        print(f"Found {self.total} entities")
        for e in l:
            self.gh_distance(e)
            self.nb_entity += 1
            self.context.session.commit()

    def run(self):
        self.gh_distances()


if __name__ == '__main__':
    art.tprint(config.name, "big")
    print("GraphHopper Service")
    print("===================")
    print(f"V{config.version}")
    print(config.copyright)
    print()
    parser = argparse.ArgumentParser(description="GraphHopper Service")
    parser.add_argument("-e", "--echo", help="Sql Alchemy echo", action="store_true")
    parser.add_argument("-p", "--port", help="TCP Port", type=int, default=8989)
    args = parser.parse_args()
    service = GraphHopperService(args.port)
    total_thread = 50
    threads = []
    for i in range(total_thread):  # todo put this code into a launcher class
        context = Context()
        context.create(echo=args.echo, expire_on_commit=False)
        gs = GraphHopperIrisService(context, service, num_thread=i, total_thread=total_thread, distance_min=5, distance_max=10)
        gs.start()
        threads.append(gs)
    threads[0].join()
    print(f"Database {threads[0].context.db_name}: {threads[0].context.db_size():.0f} Mb")

    # >3 <100 : 22M = 506j
    # >5 <50 : 8M = 185j
    # 1M = 23j
    # 50 thread passe facile
