import urllib.request
import urllib.parse
import json
import repositories
import math


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
            if v.source == "BAN" and v.score < 0.9:
                commune = v.commune
                if " CEDEX" in commune:
                    index = commune.index(" CEDEX")
                    commune = commune[:index]
                lon, lat, matchcp = self.get_lon_lat_from_adresse(v.adresse3, commune, v.cp)
                if lat == 0:
                    lon, lat, matchcp = self.get_lon_lat_from_adresse(v.adresse3, commune, "")
                    if lat != 0:
                        print(f"Found without cp: {matchcp}")
                banscore = v.score
                dist = self.calc_distance(lon, lat, v.lon, v.lat) if lat != 0 else math.inf
                score = 1 - dist / 10000
                if -math.inf < score < 0.9:
                    score = max((1 + banscore) / 2, 0.9)
                if score > 0.95:
                    banscore = 1.0
                v.source = "OSM"
                if banscore > score:
                    v.source = "BAN"
                    score = banscore
                    v.lon, v.lat, v.matchcp = lon, lat, matchcp
                print(f"{v.adresse3} {v.cp} {v.commune} @{int(v.score * 100)}% =>"
                      f" {lon},{lat} {dist}m {v.source} win @{int(score * 100)}%")
                v.score = score
                self.db[k] = v

    def save(self):
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
    rest = NominatimRest()
    rest.load()

