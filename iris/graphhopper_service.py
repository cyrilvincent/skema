from typing import Optional, Tuple
from sqlentities import Context, BAN, OSM, AdresseNorm
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


class GraphhopperService:

    def __init__(self, context):
        self.context = context
        self.uri = "http://localhost:8989/route?key"
        self.nb_entity = 0

# curl -i -X POST \
    #    -H "Content-Type:application/json" \
    #    -d \
    # '{"points":[[5.554176,45.1084288],[5.5676,45.101058]],"profile":"car","elevation":true,"instructions":true,"locale":"fr_FR","points_encoded":true,"points_encoded_multiplier":1000000,"details":["road_class","road_environment","max_speed","average_speed"],"snap_preventions":["ferry"],"alternative_route.max_paths":3,"algorithm":"alternative_route"}' \
    #  'http://localhost:8989/route?key'
    #
    #
    #  body = {"points":[[5.554176,45.1084288],[5.5676,45.101058]],"profile":"car","elevation":true,"instructions":true,"locale":"fr_FR","points_encoded":true,"points_encoded_multiplier":1000000,"details":["road_class","road_environment","max_speed","average_speed"],"snap_preventions":["ferry"],"alternative_route.max_paths":3,"algorithm":"alternative_route"}
    #
    #  body simplifié = {"points":[[5.554176,45.1084288],[5.5676,45.101058]],"profile":"car","alternative_route.max_paths":5,"algorithm":"alternative_route"}
    #  cea = {"points":[[5.554176,45.1084288],[5.7,45.203]],"profile":"car","alternative_route.max_paths":5,"algorithm":"alternative_route"}
    #
    #  {
    # "hints":{
    # "visited_nodes.sum": 510,
    # "visited_nodes.average": 510.0
    # },
    # "info":{
    # "copyrights":[
    # "GraphHopper",
    # "OpenStreetMap contributors"
    # ],
    # "took": 8,
    # "road_data_timestamp": "2025-06-25T20:20:40Z"
    # },
    # "paths":[
    # {"distance": 26954.86, "weight": 4275.752871, "time": 1849815, "transfers": 0, "points_encoded": true,…}
    # ]
    # }
    # => / 60 / 1000 = 31 min

    def get_json_from_lon_lat(self, lon1: float, lat1: float, lon2: float, lat2: float):
        dict = {"profile": "car", "alternative_route.max_paths": 1, "algorithm": "alternative_route"}
        dict["points"] = [[lon1, lat1], [lon2, lat2]]
        s = json.dumps(dict)


        try:
            with urllib.request.urlopen(url) as response:
                s = response.read()
                js = json.loads(s)
                return js
        except Exception as ex:
            print(f"WARNING URLError: {ex}")


    def get_osm_from_adresse(self, numero: Optional[int], rue: Optional[str],
                             commune: Optional[str], cp: Optional[int]) -> Optional[OSM]:
        url = self.uri
        osm = OSM()
        if rue is not None:
            if numero is None:
                url += f"&street={urllib.parse.quote(rue)}"
            else:
                url += f"&street={numero}%20{urllib.parse.quote(rue)}"
        if commune is not None:
            if commune.endswith("CEDE"):
                commune = commune[:-5]
            url += f"&city={urllib.parse.quote(commune)}"
        if cp is not None:
            url += f"&postalcode={cp}"
        js = self.get_json_from_url(url)
        if len(js) > 0:
            try:
                osm.lat = float(js[0]["lat"])
                osm.lon = float(js[0]["lon"])
                osm.adresse = js[0]["display_name"][:255]
                index = osm.adresse.rindex(",")
                cp: str = osm.adresse[index - 5: index].strip()
                if cp.isdigit():
                    osm.cp = int(cp)
            except ValueError:
                return None
            return osm
        return None

    def purge(self):
        print("Purge")
        osms = self.session.query(OSM).filter(~OSM.bans.any())
        for osm in osms:
            self.session.delete(osm)
        self.session.commit()

    def has_num(self, s: str) -> bool:
        regex = r"(\d+)"
        match = re.match(regex, s)
        return match is not None

    def match_norm(self, row: AdresseNorm) -> Tuple[Optional[OSM], float]:
        osm = self.get_osm_from_adresse(row.numero, row.rue1, row.commune, row.cp)
        if osm is not None:
            if self.has_num(osm.adresse):
                return osm, 1  # 1260
            if osm.adresse.count(",") >= 7:
                return osm, 0.85  # 2000
            return osm, 0.65  # 350
        if row.rue2 is not None:
            osm = self.get_osm_from_adresse(None, row.rue2, row.commune, row.cp)
            if osm is not None:
                if self.has_num(osm.adresse):
                    return osm, 1
                if osm.adresse.count(",") >= 7:
                    return osm, 0.97  # 490
                return osm, 0.77  # 20
        if row.numero is not None:
            osm = self.get_osm_from_adresse(None, row.rue1, None, row.cp)
            if osm is not None:
                if osm.adresse.count(",") >= 7:
                    return osm, 0.84  # 330
                return osm, 0.64  # 14
        osm = self.get_osm_from_adresse(None, None, row.commune, row.cp)
        if osm is not None:
            if osm.adresse.count(",") >= 6:
                return osm, 0.7  # 1500
            return osm, 0.5
        osm = self.get_osm_from_adresse(row.numero, row.rue1, row.commune, None)
        if osm is not None:
            if self.has_num(osm.adresse):
                return osm, 0.8  # 30
            if osm.adresse.count(",") >= 7:
                return osm, 0.6
            return osm, 0.5
        # osm = self.get_osm_from_adresse(None, None, row.commune, None)
        # if osm is not None:
        #     return osm, 0.5
        return None, 0

    def match(self):
        self.stats()
        rows = self.session.query(AdresseNorm).filter(self.filter_force).order_by(AdresseNorm.ban_score)
        if not self.force:
            rows = rows.filter(self.filter_no_force)
        for row in rows:
            self.row_num += 1
            osm, score = self.match_norm(row)
            self.total_scores.append(score)
            if osm is None:
                if self.echo:
                    print(f"{row.rue1} {row.cp} {row.commune} => No match")
            else:
                ban_score = 0 if row.ban_score is None else row.ban_score
                if self.echo:
                    print(f"{row.numero} {row.rue1} {row.cp} {row.commune} @{ban_score * 100:.0f}% "
                          f"=> {osm.adresse[:70]} {osm.cp} @{score * 100:.0f}%")
            row.osm_score = score
            if osm is not None:
                row.osm = osm
            self.session.commit()
            if self.row_num % 10 == 0:
                print(f"Found {self.row_num} addresses {(self.row_num / self.total_nb_norm) * 100:.1f}% "
                      f"in {int(time.perf_counter() - time0)}s")
        self.purge()

    def test_osm(self):
        print(f"Test OSM")
        url = f"{self.uri}&street=1571%20chemin%20des%20blancs&postalcode=38250&city=lans%20en%vercors"
        js = self.get_json_from_url(url)
        print(js)
        lat = int(float(js[0]["lat"]))
        if lat == 45:
            print("OSM is OK")
        else:
            print(f"Network problem {lat}")
            quit(1)


if __name__ == '__main__':
    art.tprint(config.name, "big")
    print("OSM Matcher")
    print("===========")
    print(f"V{config.version}")
    print(config.copyright)
    print()
    parser = argparse.ArgumentParser(description="OSM Matcher")
    parser.add_argument("-e", "--echo", help="Sql Alchemy echo", action="store_true")
    parser.add_argument("-f", "--force", help="Force matching", action="store_true")
    parser.add_argument("-l", "--log", help="Log (OSM echo)", action="store_true")
    args = parser.parse_args()
    context = Context()
    context.create(echo=args.echo, expire_on_commit=False)
    om = OSMMatcher(context, args.force, args.log, args.echo)
    om.test_osm()
    print(f"Database {om.context.db_name}: {om.context.db_size():.0f} Mb")
    om.match()
    mean = np.mean(np.array(om.total_scores))
    std = np.std(np.array(om.total_scores))
    print(f"Score average {mean * 100:.1f}%")
    print(f"Score median {np.median(np.array(om.total_scores)) * 100:.1f}%")
    print(f"Score std {std * 100:.1f}%")
    print(f"Parse {om.row_num} adresses in {time.perf_counter() - time0:.0f} s")

    # -e -l -d [5]
