from threading import Thread
from urllib import request
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
            if nb_retry_to_4 == 0:
                print(f"WARNING URLError n°{nb_retry_to_4 + 1}: {ex}")
            if nb_retry_to_4 == 4:
                raise ex
            else:
                time.sleep(nb_retry_to_4 * 10 + 1)
                coef = 1
                if nb_retry_to_4 == 1:
                    coef = -1
                elif nb_retry_to_4 == 2:
                    coef = 2
                elif nb_retry_to_4 == 3:
                    coef = -2
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

    nb_error = 0

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

    def get_iris_by_id(self, id: int) -> Iris:
        return self.context.session.get(Iris, id)

    def any_in(self, l: list[str], s: str) -> bool:
        s = s.upper()
        for value in l:
            if value in s:
                return True
        return False

    def get_heure_pleine(self, min: int, commune1: Commune, commune2: Commune) -> int:
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

    def gh_distance_from_iriss(self, iris1: Iris, iris2: Iris) -> tuple[int | None, int | None]:
        if iris1.lon is not None and iris2.lon is not None:
            js = self.service.get_json_from_lon_lat(iris1.lon, iris1.lat, iris2.lon, iris2.lat)
            km, min = self.service.get_distances_from_json(js)
            return km, min
        return None, None

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
            commune_matrix.route_hp_min = self.get_heure_pleine(min, commune1, commune2)

    def gh_distance_for_iris(self, iris_matrix: IrisMatrix):
        iris1 = self.get_iris_by_id(iris_matrix.iris_id_from)
        iris2 = self.get_iris_by_id(iris_matrix.iris_id_to)
        time1 = time.perf_counter()
        if iris_matrix.google_km is not None:
            iris_matrix.route_km = iris_matrix.google_km
            iris_matrix.route_min = int(iris_matrix.google_hc * 1.05)
            if iris1.commune is None or iris2.commune is None:  # todo a virer
                print("ERROR 2")
                quit(2)
            iris_matrix.route_hp_min = self.get_heure_pleine(iris_matrix.google_hc, iris1.commune, iris2.commune)
        else:
            km, min = self.gh_distance_from_iriss(iris1, iris2)
            if km is not None:
                duration1 = time.perf_counter() - time1
                duration0 = time.perf_counter() - time0
                if self.num_thread == 0:
                    print(f"Thread {self.num_thread} {iris_matrix.id} "
                          f"{iris_matrix.iris_id_from}=>{iris_matrix.iris_id_to}: {km}km {min}min "
                          f"@{duration1:.1f}s/query {self.nb_entity + 1} rows ({(self.nb_entity / self.total) * 100:.2f}%)"
                          f" in {int(duration0)}s")
                iris_matrix.route_km = km
                iris_matrix.route_min = min
                if iris1.commune is None or iris2.commune is None:  # todo a virer
                    print("ERROR 1")
                    quit(1)
                iris_matrix.route_hp_min = self.get_heure_pleine(min, iris1.commune, iris2.commune)

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
                GraphHopperIrisService.nb_error += 1
                print(f"Error GraphHopper n°{GraphHopperIrisService.nb_error} on {e} in thread {self.num_thread}: {ex}")
                time.sleep(10)

    def gh_distances_for_iriss(self):
        l = self.context.session.query(IrisMatrix).filter(
            (IrisMatrix.route_km.is_(None)) &
            (IrisMatrix.direct_km.isnot(None)) &
            (IrisMatrix.direct_km >= self.distance_min) &
            (IrisMatrix.direct_km <= self.distance_max) &
            (IrisMatrix.id % self.total_thread == self.num_thread)).all()
        self.total = len(l)
        print(f"Found {self.total} entities in thread {self.num_thread}")
        for e in l:
            try:
                self.gh_distance_for_iris(e)
                self.nb_entity += 1
                self.context.session.commit()
            except Exception as ex:
                GraphHopperIrisService.nb_error += 1
                print(f"Error GraphHopper n°{GraphHopperIrisService.nb_error} on {e} in thread {self.num_thread}: {ex}")
                time.sleep(5)

    def run(self):
        print(f"Starting thread {self.num_thread}")
        self.gh_distances_for_iriss()


class GraphHopperLauncher:

    def __init__(self, graphhopper_service: GraphHopperService, distance_min: int, distance_max: int, nb_thread=50):
        self.service = graphhopper_service
        self.distance_min = distance_min
        self.distance_max = distance_max
        self.nb_thread = nb_thread + np.random.randint(max(1, nb_thread // 10))
        self.threads: list[GraphHopperIrisService] = []

    def start(self):
        print(f"Starting GraphHopper clients in {self.nb_thread} threads")
        for i in range(self.nb_thread):
            context = Context()
            context.create(echo=args.echo, expire_on_commit=False)
            gs = GraphHopperIrisService(context, service, num_thread=i, total_thread=self.nb_thread,
                                        distance_min=self.distance_min, distance_max=self.distance_max)
            gs.start()
            time.sleep(10)
            self.threads.append(gs)
        for thread in self.threads:
            thread.join()


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
    args = parser.parse_args()
    service = GraphHopperService(args.port)
    launcher = GraphHopperLauncher(service, args.min, args.max, args.nb_thread)
    launcher.start()

    # -m 5 -d 5 -t 1

    # -m 3 -d 150 -t 100 pour le serveur

    # >3 <100 : 22M = 506j
    # >5 <50 : 8M = 185j
    # 1M = 23j
    # 50 threads
    # 1M = 11h
    # 8M = 4j
    # 22M = 10j
