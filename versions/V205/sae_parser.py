import art
import config
import pandas
import argparse
import os
from sqlentities import Context


class SAEParser:

    def __init__(self, context):
        self.context = context

    def scan(self, path: str):
        print(f"Scan {path}")
        l = os.listdir(path)
        for f in l:
            if f.endswith(".csv"):
                self.load(path, f)

    def get_name_from_file(self, file: str) -> str:
        index = file.rindex("_")
        s = file[0:index]
        return s.lower()

    def read_csv(self, path: str) -> pandas.DataFrame:
        dtype = {"nofinesset": str, "nofinessj": str}
        try:
            df = pandas.read_csv(path, sep=";", dtype=dtype, low_memory=False)
        except UnicodeDecodeError:
            df = pandas.read_csv(path, sep=";", dtype=dtype, encoding="latin_1", low_memory=False)
        return df

    def load(self, path: str, file: str):
        path = f"{path}/{file}"
        print(f"Load {path}")
        name = self.get_name_from_file(file)
        df = self.read_csv(path)
        df.columns= df.columns.str.strip().str.lower()
        # df = df.drop(columns=["bor"])
        context.create_engine()
        with context.engine.begin() as connection:
            df.to_sql(name, connection, schema="sae", if_exists="replace", index_label='id')

if __name__ == '__main__':
    art.tprint(config.name, "big")
    print("SAE Parser")
    print("==========")
    print(f"V{config.version}")
    print(config.copyright)
    print()
    parser = argparse.ArgumentParser(description="SAE Parser")
    parser.add_argument("path", help="Directory path")
    parser.add_argument("-e", "--echo", help="Sql Alchemy echo", action="store_true")
    args = parser.parse_args()
    context = Context()
    context.create(echo=args.echo)
    db_size = context.db_size()
    print(f"Database {context.db_name}: {db_size:.0f} Mo")
    sp = SAEParser(context)
    sp.scan(args.path)
    new_db_size = context.db_size()
    print(f"Database {context.db_name}: {new_db_size:.0f} Mo")
    print(f"Database grows: {new_db_size - db_size:.0f} Mo ({((new_db_size - db_size) / db_size) * 100:.1f}%)")

# data/sae

# Warning low_memory=True
# Load data/sae/PN_2020.csv
# C:\Users\conta\git-CVC\Skema\git-skema\sae_parser.py:37: DtypeWarning: Columns (14,32) have mixed types.Specify dtype option on import or set low_memory=False.
# pn_a74 text devrait être int
# Load data/sae/Q20_2020.csv
# C:\Users\conta\git-CVC\Skema\git-skema\sae_parser.py:37: DtypeWarning: Columns (1,2,3,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23) have mixed types.Specify dtype option on import or set low_memory=False.
# header dupliqué
# Load data/sae/Q23_2020.csv
# C:\Users\conta\git-CVC\Skema\git-skema\sae_parser.py:37: DtypeWarning: Columns (2,3) have mixed types.Specify dtype option on import or set low_memory=False.
# no problem
# Load data/sae/SYGEN_2020.csv
# C:\Users\conta\git-CVC\Skema\git-skema\sae_parser.py:37: DtypeWarning: Columns (212) have mixed types.Specify dtype option on import or set low_memory=False.
# 212 on s'en fout