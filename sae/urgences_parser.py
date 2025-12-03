import art
import psycopg2
import config
import argparse
import pandas as pd
import os
from sqlentities import Context


class SAEUrgencesParser:

    def __init__(self, context):
        self.context = context
        self.df: pd.DataFrame | None = None
        self.finess_col = "FI"
        self.base = "URGENCES"
        self.postfix = "r"
        self.suffix = ""
        self.suffixes = ["", "2", "_P"]
        pd.set_option('display.max_columns', None)
        pd.set_option('display.width', None)

    def read_csv(self, path: str, finess_col: str) -> pd.DataFrame:
        dtype = {finess_col: str, "AN": int}
        try:
            df = pd.read_csv(path, sep=";", dtype=dtype, low_memory=False)
        except UnicodeDecodeError:
            df = pd.read_csv(path, sep=";", dtype=dtype, encoding="latin_1", low_memory=False)
        return df

    def load(self, path) -> pd.DataFrame:
        print(f"Load {path}")
        df = self.read_csv(path, self.finess_col)
        df.columns = df.columns.str.strip().str.lower()
        df = df.drop("bor", axis=1)
        if self.suffix != "":
            df = df.drop("fi_ej", axis=1)
            if "rs" in df.columns:
                df = df.drop("rs", axis=1)
        print(f"Found {len(df)} rows and {len(df.columns)} columns")
        return df

    def manage_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        if "hmed" not in df.columns:
            df["hmed"] = None
        if "hide" not in df.columns:
            df["hide"] = None
        if "gde" in df.columns:
            df = df.drop("gde", axis=1)
        if "effpl" not in df.columns:
            df["effpl"] = None
        if "effpa" not in df.columns:
            df["effpa"] = None
        if "etp" in df.columns:
            df = df.rename(columns={'etp': 'etpsal'})
        return df

    def loads_by_year(self, path, suffix, postfix, year) -> pd.DataFrame | None:
        print(f"Loads {self.base}{suffix} in {year} from {path}")
        self.suffix = suffix
        file_path = f"{path}{year}/{self.base}{suffix}_{year}{postfix}.csv"
        if os.path.exists(file_path):
            df = self.load(file_path)
            df = self.manage_columns(df)
            print(df)
            return df
        return None

    def loads(self, path, suffix):
        print(f"Loads all {self.base}{suffix} from {path}")
        for year in range(2024, 2019, -1):
            postfix = self.postfix if year != 2020 else ""
            self.df = self.loads_by_year(path, suffix, postfix, year)
            if self.df is not None:
                self.commit(year)

    def load3(self, path):
        for suffix in self.suffixes:
            self.loads(path, suffix)

    def commit(self, year):
        print("Deleting old values")
        table = f"{self.base[:-1] if self.base.endswith("S") else self.base}{self.suffix.replace("2", "_detail")}".lower()
        try:
            conn = psycopg2.connect(config.connection_string)
            sql = f"delete from sae.{table} where an={year}"
            with conn.cursor() as cur:
                cur.execute(sql)
            conn.commit()
            conn.close()
            print("Deleted")
        except Exception as ex:
            print(f"No table {table}")
        print(f"Committing into {table}")
        self.df.to_sql(table, config.connection_string, schema="sae", chunksize=10000, if_exists="append", index=False)
        print("Committed")


if __name__ == '__main__':
    art.tprint(config.name, "big")
    print("SAE Urgences Parser")
    print("===================")
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
    print(f"Database {context.db_name}: {db_size:.0f} Mb")
    p = SAEUrgencesParser(context)
    # p.loads(args.path, "")
    p.load3(args.path)
    new_db_size = context.db_size()
    print(f"Database {context.db_name}: {new_db_size:.0f} Mb")
    print(f"Database grows: {new_db_size - db_size:.0f} Mb ({((new_db_size - db_size) / db_size) * 100:.1f}%)")
