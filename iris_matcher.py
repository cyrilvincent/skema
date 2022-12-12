import json
import urllib.request
import urllib.parse
import urllib.error
from typing import Optional
from sqlentities import AdresseNorm
from OSM_matcher import OSMMatcher
import argparse
import time
import art
import config


time0 = time.perf_counter()


class IrisMatcher(OSMMatcher):

    def __init__(self, force=False, echo=False, sa_echo=False):
        super().__init__(force, echo, sa_echo)
        self.uri = "https://pyris.datajazz.io/api/coords?geojson=false"
        self.row_num = 0
        self.total_nb_norm = 0
        self.nb_iris = 0
        self.filter_no_force = (AdresseNorm.iris.is_(None) & AdresseNorm.lat.isnot(None) & AdresseNorm.lon.isnot(None))
        self.filter_force = (AdresseNorm.lat.isnot(None) & AdresseNorm.lon.isnot(None))

    def stats(self):
        norm = self.session.query(AdresseNorm).count()
        print(f"Found {norm} adresses")
        if self.force:
            query = self.session.query(AdresseNorm).filter(self.filter_force)
            self.total_nb_norm = query.count()
        else:
            query = self.session.query(AdresseNorm).filter(self.filter_no_force)
            self.total_nb_norm = query.filter(self.filter_no_force).count()
        print(f"Found {self.total_nb_norm} adresses to match")
        if self.total_nb_norm == 0:
            print("Everything is up to date")
            quit(0)

    def get_json_from_url(self, url, _=0):
        if self.echo:
            print(url)
        try:
            with urllib.request.urlopen(url) as response:
                s = response.read()
                js = json.loads(s)
                return js
        except Exception as ex:
            print(url)
            print(f"ERROR URLError: {ex}")
            return None

    def get_iris_from_lon_lat(self, lon: float, lat: float) -> Optional[str]:
        iris = None
        url = f"{self.uri}&lat={lat}&lon={lon}"
        js = self.get_json_from_url(url)
        if js is not None and len(js) > 0:
            try:
                s = js["complete_code"].strip()
                if s.isdigit():
                    iris = s
                else:
                    print(f"ERROR {self.row_num}: IRIS is not a number {iris}")
            except ValueError:
                return None
        return iris

    def match(self):
        self.stats()
        if self.force:
            rows = self.session.query(AdresseNorm).filter(self.filter_force)
        else:
            rows = self.session.query(AdresseNorm).filter(self.filter_no_force)
        for row in rows:
            self.row_num += 1
            iris = self.get_iris_from_lon_lat(row.lon, row.lat)
            if self.echo:
                print(f"{row.cp} {row.commune} ({row.lon}, {row.lat}) => {iris}")
            if iris is not None:
                row.iris = iris
                self.nb_iris += 1
                self.session.commit()
            if self.row_num % 10 == 0:
                print(f"Found {self.row_num} adresses {(self.row_num / self.total_nb_norm) * 100:.1f}% "
                      f"in {int(time.perf_counter() - time0)}s")


if __name__ == '__main__':
    art.tprint(config.name, "big")
    print("IRIS Matcher")
    print("============")
    print(f"V{config.version}")
    print(config.copyright)
    print()
    parser = argparse.ArgumentParser(description="IRIS Matcher")
    parser.add_argument("-e", "--echo", help="Sql Alchemy echo", action="store_true")
    parser.add_argument("-f", "--force", help="Force matching", action="store_true")
    parser.add_argument("-l", "--log", help="Log (Pyris echo)", action="store_true")
    args = parser.parse_args()
    im = IrisMatcher(args.force, args.log, args.echo)
    print(f"Database {im.context.db_name}: {im.context.db_size():.0f} Mo")
    im.match()
    print(f"Nb address {im.total_nb_norm}")
    print(f"Nb iris {im.nb_iris}")
    print(f"Parse {im.row_num} adresses in {time.perf_counter() - time0:.0f} s")


