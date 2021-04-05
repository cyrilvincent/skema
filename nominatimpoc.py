import urllib.request
import urllib.parse
import json
import repositories
import config

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
        lat = js[0]["lat"]
        lon = js[0]["lon"]
    return lon, lat


def load():
    repo = repositories.AdresseRepository()
    db = repo.load_adresses_db()
    for k in db:
        lon, lat = get_lon_lat_from_adresse(0, k[2], k[1], k[0])
        print(f"{k[2]} {k[0]} {k[1]} @{int(db[k][1]*100)}% => {lon},{lat}")


if __name__ == '__main__':
    load()

