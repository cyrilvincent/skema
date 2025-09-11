from threading import Thread
from urllib import request

from OSM_matcher import OSMMatcher
from sqlentities import Context, Commune, CommuneMatrix, Iris, IrisMatrix
import argparse
import time
import art
import config
import urllib.request
import urllib.parse
import urllib.error
import json
import numpy as np


time0 = time.perf_counter()


class GraphHopperService:

    def __init__(self, port=8989):
        self.url = f"http://localhost:{port}/route?key"

    def get_json_from_lon_lat(self, lon1: float, lat1: float, lon2: float, lat2: float, nb_retry_to_4=0) -> str:
        dict = {"profile": "car", "alternative_route.max_paths": 1, "algorithm": "astarbi",
                "elevation": False, "instructions": False, "details": [], "snap_preventions": [],
                "points": [[lon1, lat1], [lon2, lat2]]}
        data = json.dumps(dict).encode("utf-8")
        try:
            req = request.Request(self.url, data=data, headers={'Content-Type': 'application/json'})
            with urllib.request.urlopen(req) as response:
                s = response.read()
                return s
        except Exception as ex:
            # if nb_retry_to_4 == 0:
            #     print(f"WARNING URLError n°{nb_retry_to_4 + 1}: {ex}")
            if nb_retry_to_4 == 4:
                raise ex
            else:
                time.sleep(nb_retry_to_4 * 1 + 1)
                coef = 1
                if nb_retry_to_4 == 1:
                    coef = -1
                elif nb_retry_to_4 == 2:
                    coef = 2
                elif nb_retry_to_4 == 3:
                    coef = -2.5
                lon1 += 0.01 * coef
                lat1 += 0.01 * coef
                lon2 += 0.01 * coef
                lat2 += 0.01 * coef
                return self.get_json_from_lon_lat(lon1, lat1, lon2, lat2, nb_retry_to_4 + 1)

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
                 num_thread: int, total_thread: int, distance_min: int, distance_max: int, with_osm=False):
        super().__init__()
        self.context = context
        self.service = graphhopper_service
        self.num_thread = num_thread
        self.total_thread = total_thread
        self.distance_min = distance_min
        self.distance_max = distance_max
        self.nb_entity = 0
        self.total = 0
        self.nb_error = 0
        self.with_osm = with_osm
        if with_osm:
            self.osm_matcher = OSMMatcher(ban_echo=True)

    def get_commune_by_id(self, id: int) -> Commune:
        return self.context.session.get(Commune, id)

    def get_commune_by_code(self, code: str) -> Commune:
        return self.context.session.query(Commune.code == code).one()

    def get_iris_by_id(self, id: int) -> Iris:
        return self.context.session.get(Iris, id)

    def any_in(self, l: list[str], s: str) -> bool:
        for value in l:
            if value in s:
                return True
        return False

    def get_hp(self, min: int, commune1: Commune, commune2: Commune) -> int:
        coef = 1.0
        top5 = ["LYON", "MARSEILLE", "BORDEAUX", "NICE"]
        s1 = "" if commune1.epci_nom is None else commune1.epci_nom.upper()
        s2 = "" if commune2.epci_nom is None else commune2.epci_nom.upper()
        if "PARIS" in s1 and "PARIS" in s2:
            coef = 1.7
        elif "PARIS" in s1 or "PARIS" in s2:
            coef = 1.5
        elif self.any_in(top5, s1) and self.any_in(top5, s2):
            coef = 1.4
        elif self.any_in(top5, s1) or self.any_in(top5, s2):
            coef = 1.3
        elif len(commune1.iriss) > 9 and len(commune2.iriss) > 9:
            coef = 1.25
        elif len(commune1.iriss) > 9 or len(commune2.iriss) > 9:
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

    def gh_distance_from_iriss(self, iris1: Iris, iris2: Iris) -> tuple[int | None, int | None]:
        if iris1.lon is not None and iris2.lon is not None:
            js = self.service.get_json_from_lon_lat(iris1.lon, iris1.lat, iris2.lon, iris2.lat)
            km, min = self.service.get_distances_from_json(js)
            return km, min
        return None, None

    def gh_osm_distance_from_iriss(self, iris1: Iris, iris2: Iris) -> tuple[int | None, int | None]:
        if len(iris1.commune.iriss) == 1:
            osm1 = self.osm_matcher.get_osm_from_adresse(None, None, iris1.commune.nom_norm, None)
        else:
            osm1 = self.osm_matcher.get_osm_from_query(f"{iris1.nom_norm} {iris1.commune.nom_norm}")
        if osm1.lon is None:
            return None, None
        if len(iris2.commune.iriss) == 1:
            osm2 = self.osm_matcher.get_osm_from_adresse(None, None, iris2.commune.nom_norm, None)
        else:
            osm2 = self.osm_matcher.get_osm_from_query(f"{iris2.nom_norm} {iris2.commune.nom_norm}")
        if osm2.lon is None:
            return None, None
        js = self.service.get_json_from_lon_lat(osm1.lon, osm1.lat, osm2.lon, osm2.lat)
        km, min = self.service.get_distances_from_json(js)
        return km, min

    def gh_distance_for_commune(self, commune_matrix: CommuneMatrix):
        commune1 = self.get_commune_by_id(commune_matrix.code_id_low)
        commune2 = self.get_commune_by_id(commune_matrix.code_id_high)
        time1 = time.perf_counter()
        km, min = self.gh_distance_from_communes(commune1, commune2)
        if km is not None:
            duration1 = time.perf_counter() - time1
            duration0 = time.perf_counter() - time0
            if self.num_thread == 0:
                print(f"Thread {self.num_thread} {commune_matrix.id} "
                      f"{commune_matrix.code_id_low}=>{commune_matrix.code_id_high}: {km}km {min}min "
                      f"@{duration1:.1f}s/query {self.nb_entity + 1} rows ({(self.nb_entity / self.total) * 100:.2f}%)"
                      f" in {int(duration0)}s")
            commune_matrix.route_km = km
            commune_matrix.route_min = min
            commune_matrix.route_hp_min = self.get_hp(min, commune1, commune2)

    def gh_distance_for_iris(self, iris_matrix: IrisMatrix):
        iris1 = self.get_iris_by_id(iris_matrix.iris_id_from)
        iris2 = self.get_iris_by_id(iris_matrix.iris_id_to)
        time1 = time.perf_counter()
        if iris_matrix.od_km is not None:
            iris_matrix.route_km = iris_matrix.od_km
            iris_matrix.route_min = iris_matrix.od_hc
            iris_matrix.route_hp_min = iris_matrix.od_hp
        else:
            if self.with_osm:
                km, min = self.gh_osm_distance_from_iriss(iris1, iris2)
            else:
                km, min = self.gh_distance_from_iriss(iris1, iris2)
            if km is not None:
                duration1 = time.perf_counter() - time1
                duration0 = time.perf_counter() - time0
                if self.num_thread == 0:
                    print(f"Thread {self.num_thread} {iris_matrix.id} "
                          f"{iris_matrix.iris_id_from}=>{iris_matrix.iris_id_to}: {km}km {min}min "
                          f"@{duration1:.1f}s/query {self.nb_entity + 1} rows"
                          f" ({(self.nb_entity / self.total)* 100:.2f}%) in {int(duration0)}s")
                iris_matrix.route_km = km
                iris_matrix.route_min = min
                iris_matrix.route_hp_min = self.get_hp(min, iris1.commune, iris2.commune)

    def gh_distances_for_communes(self):
        l = self.context.session.query(CommuneMatrix).filter(
                (CommuneMatrix.route_km.is_(None)) &
                (CommuneMatrix.direct_km.isnot(None)) &
                (CommuneMatrix.direct_km >= self.distance_min) &
                (CommuneMatrix.direct_km <= self.distance_max) &
                (CommuneMatrix.id % self.total_thread == self.num_thread)).all()
        self.total = len(l)
        print(f"Found {self.total} entities in thread {self.num_thread}")
        for e in l:
            try:
                self.gh_distance_for_commune(e)
                self.nb_entity += 1
                self.context.session.commit()
            except Exception as ex:
                self.nb_error += 1
                print(f"Error GraphHopper n°{self.num_thread}.{self.nb_error} on {e}: {ex}")
                time.sleep(1)

    def gh_distances_for_iriss(self):
        if self.with_osm:
            print("Starting GraphHopper service with OSM")
            l: list[IrisMatrix] = self.context.session.query(IrisMatrix).filter(
                (IrisMatrix.direct_km.isnot(None)) &
                (IrisMatrix.direct_km >= self.distance_min) &
                (IrisMatrix.direct_km <= self.distance_max) &
                ((IrisMatrix.route_km.is_(None)) | ((IrisMatrix.route_km - IrisMatrix.direct_km) > 200))).all()
        else:
            l: list[IrisMatrix] = self.context.session.query(IrisMatrix).filter(
                (IrisMatrix.direct_km.isnot(None)) &
                (IrisMatrix.direct_km >= self.distance_min) &
                (IrisMatrix.direct_km <= self.distance_max) &
                (IrisMatrix.route_km.is_(None)) &
                (IrisMatrix.id % self.total_thread == self.num_thread)).all()
        self.total = len(l)
        print(f"Found {self.total} entities in thread {self.num_thread}")
        for e in l:
            try:
                self.nb_entity += 1
                if (e.iris_id_from > 2000000000 > e.iris_id_to) or (e.iris_id_from < 2000000000 < e.iris_id_to):
                    continue  # Corse
                self.gh_distance_for_iris(e)
                self.context.session.commit()
            except Exception as ex:
                self.nb_error += 1
                print(f"Error GraphHopper n°{self.num_thread}.{self.nb_error} on {e}: {ex}")
                time.sleep(1)

    def run(self):
        print(f"Starting thread {self.num_thread}/{self.total_thread}")
        # self.gh_distances_for_iriss()
        self.gh_distances_for_communes()
        print(f"Ending thread {self.num_thread}/{self.total_thread}")


class GraphHopperLauncher:

    def __init__(self, graphhopper_service: GraphHopperService,
                 distance_min: int, distance_max: int, nb_thread=50, sleep=10):
        self.service = graphhopper_service
        self.distance_min = distance_min
        self.distance_max = distance_max
        self.nb_thread = nb_thread
        self.threads: list[GraphHopperIrisService] = []
        self.sleep = sleep

    def start(self):
        print(f"Starting GraphHopper clients with {self.nb_thread} threads")
        for i in range(self.nb_thread):
            context = Context()
            context.create(echo=False, expire_on_commit=False)
            gs = GraphHopperIrisService(context, service, num_thread=i, total_thread=self.nb_thread,
                                        distance_min=self.distance_min, distance_max=self.distance_max)
            gs.start()
            self.threads.append(gs)
            time.sleep(self.sleep)
        print(f"All {self.nb_thread} threads started")
        for thread in self.threads:
            thread.join()
        print(f"All {self.nb_thread} threads are closed for {self.distance_min}km to {self.distance_max}km")



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
    parser.add_argument("-m", "--min", help="Minimum distance", type=int, default=3)
    parser.add_argument("-d", "--max", help="Maximum distance", type=int, default=100)
    parser.add_argument("-t", "--nb_thread", help="Number of thread", type=int, default=50)
    parser.add_argument("-s", "--thread_sleep", help="Sleeping between 2 threads", type=int, default=10)
    parser.add_argument("-o", "--with_osm", help="Use OSM", action="store_true")
    args = parser.parse_args()
    service = GraphHopperService(args.port)
    if args.with_osm:
        context = Context()
        context.create(echo=args.echo, expire_on_commit=False)
        gs = GraphHopperIrisService(context, service, 0, 1, args.min, args.max, True)
        gs.gh_distances_for_iriss()
    else:
        launcher = GraphHopperLauncher(service, args.min, args.max, args.nb_thread, args.thread_sleep)
        launcher.start()


    # -m 0 -d 999 -t 400 -s 60 pour le serveur

