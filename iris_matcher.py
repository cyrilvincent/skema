import json
import urllib3.request
import urllib3
import urllib.parse
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
        self.http = urllib3.PoolManager()

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
            response = self.http.request("GET", url, timeout=10)
            if response.status == 404:
                print(f"ERROR 404")
                return 404
            s = response.data
            response.close()
            js = json.loads(s)
            return js
        except Exception as ex:
            print(f"ERROR Exception: {ex}")
            return None

    def get_iris_from_js(self, js) -> Optional[str] | int:
        if js == 404:
            return 404
        iris = None
        if js is not None and len(js) > 0:
            try:
                s: str = js["complete_code"].strip()
                if len(s) == 9:
                    if s.isdigit() or s.startswith("2A") or s.startswith("2B"):
                        iris = s
                    else:
                        print(f"ERROR {self.row_num}: IRIS is not a number {s}")
                else:
                    print(f"ERROR {self.row_num}: IRIS {s} not have 9 digits")
            except ValueError:
                return None
        return iris

    def get_iris_from_lon_lat(self, lon: float, lat: float) -> Optional[str]:
        url = f"{self.uri}&lat={lat}&lon={lon}"
        js = self.get_json_from_url(url)
        return self.get_iris_from_js(js)

    def get_iris_from_address(self, numero: Optional[int], rue: Optional[str], cp: int, commune: str) -> Optional[str]:
        url = f"{self.uri.replace('coords', 'search')}&q="
        s = ""
        if rue is not None:
            if numero is None:
                s += f"{rue} "
            else:
                s += f"{numero} {rue} "
        s += f"{cp} "
        if commune.endswith("CEDE"):
            commune = commune[:-5]
        s += commune
        url += urllib.parse.quote(s)
        js = self.get_json_from_url(url)
        return self.get_iris_from_js(js)

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
            if iris == 404 and row.cp is not None and row.commune is not None:
                iris = self.get_iris_from_address(row.numero, row.rue1, row.cp, row.commune)
            if iris is not None:
                row.iris = iris
                self.nb_iris += 1
                self.session.commit()
            if self.row_num % 10 == 0:
                print(f"Found {self.row_num} IRIS {(self.row_num / self.total_nb_norm) * 100:.1f}% "
                      f"in {int(time.perf_counter() - time0)}s")
            time.sleep(0.1)


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
    print(f"Database {im.context.db_name}: {im.context.db_size():.0f} Mb")
    im.match()
    print(f"Nb address {im.total_nb_norm}")
    print(f"Nb iris {im.nb_iris}")
    print(f"Parse {im.row_num} adresses in {time.perf_counter() - time0:.0f} s")


