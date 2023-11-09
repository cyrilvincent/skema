import sys
import argparse
import time
import art
import config
from iris_matcher import IrisMatcher

time0 = time.perf_counter()

class IrisCsvMatcher:

    def __init__(self, path):
        self.path = path
        self.matcher = IrisMatcher(False, True, False)
        self.matcher.test_pyris()
        self.row_num = 0
        self.nb_iris = 0
        self.nb_error = 0

    def parse_row(self, row: str, out):
        self.row_num += 1
        values = row.split(",")
        lon = float(values[-2].strip())
        lat = float(values[-1].strip())
        if lon > lat:
            lon, lat = lat, lon
        iris = self.matcher.get_iris_from_lon_lat(lon, lat)
        if iris is None:
            self.nb_error += 1
            iris = 0
        else:
            self.nb_iris += 1
        out.write(f"{row.strip()},{iris}\n")

    def load(self):
        print(f"Load {self.path}")
        if ".csv" not in self.path:
            print("Error the file must have extension .csv")
            sys.exit(1)
        with open(self.path) as f:
            out_path = self.path.replace(".csv", ".iris.csv")
            print(f"Create {out_path}")
            row = f.readline()
            if "," not in row:
                print("Error separator must be ,")
                sys.exit(2)
            with open(out_path, "w") as out:
                out.write(row.strip() + ",iris\n")
                self.row_num += 1
                for row in f:
                    self.parse_row(row, out)

if __name__ == '__main__':
    art.tprint(config.name, "big")
    print("IRIS CSV Matcher")
    print("================")
    print(f"V{config.version}")
    print(config.copyright)
    print()
    parser = argparse.ArgumentParser(description="IRIS CSV Matcher")
    parser.add_argument("path", help="Path")
    args = parser.parse_args()
    icm = IrisCsvMatcher(args.path)
    icm.load()
    print(f"Nb iris: {icm.nb_iris}")
    print(f"Nb error: {icm.nb_error}")
    print(f"Parse {icm.row_num - 1} geolocalisations in {time.perf_counter() - time0:.0f} s")


