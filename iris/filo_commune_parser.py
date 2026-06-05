import numpy as np
import psycopg2
from sqlentities import Context
import argparse
import art
import config
import pandas as pd


class FiloCommuneParser:

    def __init__(self, context):
        self.context = context
        self.df = None
        self.year = 2020
        self.sep = ";"

    def load(self, path):
        print(f"Parse {path}")
        pd.set_option('display.max_columns', None)
        pd.set_option('display.width', None)
        self.df = pd.read_csv(path, low_memory=False, sep=self.sep, decimal=",", na_values=["", "s", "vm"])
        self.df.columns = self.df.columns.str.strip().str.lower()
        self.df["pop"] = self.df["p22_pop"].astype("Int32")
        self.df["med"] = self.df["med_sl23"].astype("Int32")
        self.df["tp60"] = self.df["pr_md60_23"].astype("Float32")
        self.df = self.df[["codgeo", "pop", "med", "tp60"]]
        self.year = 2023
        print(self.df)

    def commit(self):
        print("Deleting old values")
        table_name = "filo_commune"
        try:
            conn = psycopg2.connect(config.connection_string)
            sql = f"delete from iris.{table_name} where year={self.year}"
            with conn.cursor() as cur:
                cur.execute(sql)
            conn.commit()
            conn.close()
        except:
            pass
        print("Committing")
        self.df.to_sql(table_name, config.connection_string, schema="iris", chunksize=10000, if_exists="append",
                       index=False)
        print("Committed")


if __name__ == '__main__':
    art.tprint(config.name, "big")
    print("Filo Commune Parser")
    print("===================")
    print(f"V{config.version}")
    print(config.copyright)
    print()
    # parser = argparse.ArgumentParser(description="Filo Commune Parser")
    # parser.add_argument("path", help="Path")
    # parser.add_argument("-e", "--echo", help="Sql Alchemy echo", action="store_true")
    # args = parser.parse_args()
    context = Context()
    context.create(echo=False, expire_on_commit=False)
    db_size = context.db_size()
    print(f"Database {context.db_name}: {db_size:.0f} MB")
    fp = FiloCommuneParser(context)
    fp.load("data/filo/base_cc_comparateur.csv")
    fp.commit()
    new_db_size = context.db_size()
    print(f"Database {context.db_name}: {new_db_size:.0f} MB")
    print(f"Database grows: {new_db_size - db_size:.0f} MB ({((new_db_size - db_size) / db_size) * 100:.1f}%)")

    # data/filo/base_cc_comparateur.csv

