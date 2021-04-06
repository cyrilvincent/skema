import urllib.request
import urllib.parse
import json
import repositories
import config
import math

uri = "https://nominatim.openstreetmap.org/search.php?format=jsonv2&country=France&"


def get_lon_lat_from_adresse(num, street, commune, cp):
    if num != 0:
        street = f"{num} {street}"
    street = urllib.parse.quote(street)
    commune = urllib.parse.quote(commune)
    url = uri+f"street={street}&city={commune}&postalcode={cp}"
    with urllib.request.urlopen(url) as response:
        s = response.read()
    js = json.loads(s)
    # print(js)
    lat = lon = 0
    if len(js) > 0:
        lat = float(js[0]["lat"])
        lon = float(js[0]["lon"])
    return lon, lat


def load():
    repo = repositories.AdresseRepository()
    db = repo.load_adresses_db()
    for k in db:
        lon, lat = get_lon_lat_from_adresse(0, k[2], k[1], k[0])
        if lat == 0:
            lon, lat = get_lon_lat_from_adresse(0, k[2], k[1], "")
        v = db[k]
        dist = calc_distance(lon, lat, v[3], v[4]) if lat != 0 else "?"
        print(f"{k[2]} {k[0]} {k[1]} @{int(v[1]*100)}% => {lon},{lat} {dist}m")


def calc_distance(lon1, lat1, lon2, lat2):
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


def calc_distance_cyril(lon1, lat1, lon2, lat2):
    d = math.sqrt((lon1 - lon2) ** 2 + (lat1 - lat2) ** 2)
    d = d * 40075 / 720
    return int(d * 1000)


if __name__ == '__main__':
    load()

