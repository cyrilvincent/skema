import json
import urllib.request
import urllib.parse

class GoogleMapDistanceService:

    def __init__(self):
        self.key = self.get_key()
        self.url = (
            "https://maps.googleapis.com/maps/api/distancematrix/json"
            "?origins={origin}"
            "&destinations={destination}"
            "&mode=driving"
            "&language=fr-FR"
            f"&key={self.key}"
        )

    def get_key(self) -> str:
        with open("data/google_map/map.key") as f:
            return f.read()

    def get_js_from_origin_destination(self, origin: str, destination: str) -> dict:
        origin = urllib.parse.quote_plus(origin)
        destination = urllib.parse.quote_plus(destination)
        url = self.url.replace("{origin}", origin).replace("{destination}", destination)
        print(url)
        with urllib.request.urlopen(url) as response:
            s = response.read()
            js = json.loads(s)
            return js

    def get_distance_from_js(self, js: dict) -> tuple[int | None, int | None]:
        if len(js["rows"]) > 0:
            row = js["rows"][0]
            if len(row["elements"]) > 0:
                element = row["elements"][0]
                distance = element["distance"]["value"]
                distance = int(round(distance / 1000))
                duration = element["duration"]["value"]
                duration = int(round(duration / 60))
                return distance, duration
        return None, None


if __name__ == '__main__':
    service = GoogleMapDistanceService()
    js = service.get_js_from_origin_destination("lans en vercors", "grenoble")
    print(js)
    km, min = service.get_distance_from_js(js)
    print(km, min)

    # 5$ / 10000
