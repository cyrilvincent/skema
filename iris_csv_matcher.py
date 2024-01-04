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
        self.nb_iris_a = 0
        self.nb_error_a = 0

    def parse_row(self, row: str, out, with_address=False):
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
        out.write(f"{row.strip()},{iris}")
        if with_address:
            a = values[-3].strip()
            iris_a = self.matcher.get_iris_from_concatenate_address(a)
            if iris_a is None:
                self.nb_error_a += 1
                iris_a = 0
            else:
                self.nb_iris_a += 1
            out.write(f",{iris_a}")
        out.write("\n")
        time.sleep(0.1)

    def load(self, with_address=False):
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
                out.write(row.strip() + ",iris")
                if with_address:
                    out.write(",iris_a")
                out.write("\n")
                self.row_num += 1
                for row in f:
                    self.parse_row(row, out, with_address)

if __name__ == '__main__':
    art.tprint(config.name, "big")
    print("IRIS CSV Matcher")
    print("================")
    print(f"V{config.version}")
    print(config.copyright)
    print()
    parser = argparse.ArgumentParser(description="IRIS CSV Matcher")
    parser.add_argument("path", help="Path")
    parser.add_argument("-a", "--address", help="PYRIS address", action="store_true")
    args = parser.parse_args()
    icm = IrisCsvMatcher(args.path)
    icm.load(args.address)
    print(f"Nb iris: {icm.nb_iris}")
    print(f"Nb error: {icm.nb_error}")
    print(f"Nb iris with address: {icm.nb_iris_a}")
    print(f"Nb error with address: {icm.nb_error_a}")
    print(f"Parse {icm.row_num - 1} rows in {time.perf_counter() - time0:.0f} s")


