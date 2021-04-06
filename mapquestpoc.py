import urllib.request
import urllib.parse
import json
import repositories
import config
import math

uri = "http://open.mapquestapi.com/geocoding/v1/address?key=SP3uDKFpTXYZaXyU9HnzPu1tIkxTU6xT&location="


def get_lon_lat_from_adresse(adresse):
    adresse += " FRANCE"
    adresse = urllib.parse.quote(adresse)
    url = uri+adresse
    with urllib.request.urlopen(url) as response:
        s = response.read()
    js = json.loads(s)
    js = js["results"]
    lat = lon = 0
    if len(js) > 0:
        lat = float(js[0]["locations"][0]["latLng"]["lat"])
        lon = float(js[0]["locations"][0]["latLng"]["lng"])
        if lon < -100:
            lon = lat = 0
    return lon, lat


def load():
    repo = repositories.AdresseRepository()
    db = repo.load_adresses_db()
    for k in db:
        lon, lat = get_lon_lat_from_adresse(f"{k[2]} {k[0]} {k[1]}")
        # lon, lat = get_lon_lat_from_adresse(f"1571 chemin des blancs 38250 lans en vercors".upper())
        print(f"{k[2]} {k[0]} {k[1]} @{int(db[k][1]*100)}% => {lon},{lat}")


if __name__ == '__main__':
    load()

