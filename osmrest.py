import urllib.request
import urllib.parse
import json
import repositories
import math
import config
import art
import time

time0 = time.perf_counter()


class NominatimRest:

    def __init__(self):
        self.uri = "https://nominatim.openstreetmap.org/search.php?format=jsonv2&country=France&"
        self.repo = repositories.AdresseRepository()
        self.db = {}

    def get_lon_lat_from_adresse(self, street, commune, cp):
        street = urllib.parse.quote(street)
        commune = urllib.parse.quote(commune)
        url = f"{self.uri}street={street}&city={commune}&postalcode={cp}"
        with urllib.request.urlopen(url) as response:
            s = response.read()
        js = json.loads(s)
        lat = lon = cp = 0
        if len(js) > 0:
            lat = float(js[0]["lat"])
            lon = float(js[0]["lon"])
            s = js[0]["display_name"]
            index = s.rindex(",")
            cp = s[index - 5: index].strip()
            if len(cp) == 4:
                cp = "0" + cp
        return lon, lat, cp

    def load(self):
        self.db = self.repo.load_adresses_db()
        for k in list(self.db.keys()):
            v = self.db[k]
            if v.source == "BAN" and v.score < 0.83:
                commune = v.commune
                if " CEDEX" in commune:
                    index = commune.index(" CEDEX")
                    commune = commune[:index]
                q = 0
                lon, lat, matchcp = self.get_lon_lat_from_adresse(v.adresse3, commune, v.cp)
                if lat == 0:
                    lon, lat, matchcp = self.get_lon_lat_from_adresse(v.adresse3, commune, "")
                    q = 1
                if lat == 0:
                    lon, lat, matchcp = self.get_lon_lat_from_adresse(v.adresse3, "", v.cp)
                    q = 2
                if lat == 0:
                    lon, lat, matchcp = self.get_lon_lat_from_adresse("", commune, v.cp[:2])
                    q = 3
                if lat == 0:
                    lon, lat, matchcp = self.get_lon_lat_from_adresse("", "", v.cp)
                    q = 4
                if lat == 0:
                    print(f"{v.adresse3} {v.cp} {v.commune} @{int(v.score * 100)}% => No match")
                else:
                    banscore = v.score
                    dist = self.calc_distance(lon, lat, v.lon, v.lat)
                    score = max(0.9 + banscore / 100, 1 - dist / 10000 - q / 100)
                    v.source = "OSM"
                    if dist < 500:
                        v.source = "BAN+OSM"
                    elif q > 0 and dist < 1000:
                        v.source = f"BAN+OSM"
                        score = 0.91 + banscore / 100
                    elif q > 0 and dist < 3000:
                        score = config.adresse_quality + 0.04 + banscore / 100
                    elif banscore < config.adresse_quality and q > 0:
                        score = config.adresse_quality + banscore / 100 + 0.03 - q / 100
                    elif q > 2:
                        v.source = "BAN"
                        score = banscore
                    elif q > 0:
                        score = banscore
                    print(f"{v.adresse3} {v.cp} {v.commune} @{int(v.score * 100)}% =>"
                          f" {lon},{lat} {dist}m {v.source}{q} @{int(score * 100)}%")
                    if v.source == "OSM":
                        v.lon, v.lat, v.matchcp = lon, lat, matchcp
                    if "OSM" in v.source:
                        v.source += str(q)
                    v.score = score
                    self.db[k] = v

    def save(self):
        try:
            self.repo.save_adresses_db(self.db)
        except PermissionError as pe:
            print(pe)
            input("Close the file and press Enter")
            self.repo.save_adresses_db(self.db)

    def calc_distance(self, lon1, lat1, lon2, lat2):
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
        return int(distance * 1000)


if __name__ == '__main__':
    art.tprint(config.name, "big")
    print("OSM Rest")
    print("========")
    print(f"V{config.version}")
    print(config.copyright)
    print()
    rest = NominatimRest()
    rest.load()
    rest.save()

