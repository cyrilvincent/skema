import pandas
import art
import config
import argparse
import re
import os
import importlib


class PSQuery:

    def __init__(self, path, fn, module):
        self.db = []
        self.path = path
        self.fn = fn
        self.module = module

    def scan(self):
        """
        Scan directory
        """
        print(f"Scan {self.path}")
        for item in os.listdir(self.path):
            if item.endswith(".csv"):
                dataframe = self.load(f"{self.path}/{item}")
                if dataframe is not None:
                    self.db.append(dataframe)
        dataframe = pandas.concat(self.db, ignore_index=True, sort=False)
        print(dataframe)
        file = f"{self.path}/results/psquery-{self.fn}.csv"
        dataframe.to_csv(file, header=None, index=False)
        print(f"Saved {file}")

    def load(self, path):
        print(f"Load {path}")
        regex = r"(\d{2})-(\d{2})"
        match = re.search(regex, path)
        if match is None:
            print("Bad file format, must have YY-MM")
            return None
        else:
            year = int(match[1])
            month = int(match[2])
            try:
                dataframe = pandas.read_csv(path, delimiter=";", header=None)
                print(dataframe.shape)
                s = f"self.module.{self.fn}(dataframe)"
                res = eval(s)
                res.assign(year=year)
                res.assign(month=month)
                return res
            except UnicodeDecodeError:
                print("Not working on original files, use adressesmatcher before")
                return None


if __name__ == '__main__':
    art.tprint(config.name, "big")
    print("PS Query")
    print("========")
    print(f"V{config.version}")
    print(config.copyright)
    print()
    parser = argparse.ArgumentParser(description="PS Query")
    parser.add_argument("path", help="Path")
    parser.add_argument("fn", help="Function name")
    parser.add_argument("-m", "--module", help="psfilter module name")
    args = parser.parse_args()
    module = "psfilter" if args.module is None else args.module
    module = importlib.import_module(module)
    ps = PSQuery(args.path, args.fn, module)
    ps.scan()
