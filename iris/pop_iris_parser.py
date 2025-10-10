import art
import psycopg2
import sqlalchemy
import config
import pandas as pd
import argparse
import numpy as np
from sqlentities import Context, DateSource


class PopIrisParser:

    def __init__(self, context):
        self.context = context
        self.year = 0
        self.dataframe = None

    def parse_date(self, path):
        try:
            self.year = int(path[-6:-4])
        except IndexError:
            print("ERROR: file must have date like this: base-ic-evol-struct-pop-20YY.CSV")
            quit(1)

    def read_csv(self, path: str):
        self.dataframe = pd.read_csv(path, sep=";", low_memory=False)
        self.dataframe.columns = self.dataframe.columns.str.strip().str.lower()
        for col in self.dataframe.columns:
            if col.startswith(f"p{self.year}") or col.startswith(f"c{self.year}"):
                self.dataframe = self.dataframe.rename(columns={col: col[4:]})
        self.dataframe["iris_id"] = self.dataframe["iris"].str.replace("2A", "201", regex=True)
        self.dataframe["iris_id"] = self.dataframe["iris_id"].str.replace("2B", "202", regex=True)
        self.dataframe["iris_id"] = self.dataframe["iris_id"].astype(np.int32)
        self.dataframe["year"] = self.year
        self.dataframe = self.dataframe[["year", "iris_id"] + list(self.dataframe.columns[:-2])]

    def load(self, path: str):
        print(f"Load {path}")
        self.parse_date(path)
        self.read_csv(path)

    def commit(self):
        print("Deleting old values")
        try:
            conn = psycopg2.connect(config.connection_string)
            sql = f"delete from iris.pop_iris where year={self.year}"
            with conn.cursor() as cur:
                cur.execute(sql)
            conn.commit()
            conn.close()
        except:
            pass
        print("Commiting")
        self.dataframe.to_sql("pop_iris", config.connection_string, schema="iris", if_exists="append", index=False)
        print("Commited")


if __name__ == '__main__':
    art.tprint(config.name, "big")
    print("Pop Iris Parser")
    print("===============")
    print(f"V{config.version}")
    print(config.copyright)
    print()
    parser = argparse.ArgumentParser(description="Pop Iris Parser")
    parser.add_argument("path", help="Directory path")
    parser.add_argument("-e", "--echo", help="Sql Alchemy echo", action="store_true")
    args = parser.parse_args()
    context = Context()
    context.create(echo=args.echo)
    db_size = context.db_size()
    print(f"Database {context.db_name}: {db_size:.0f} MB")
    dp = PopIrisParser(context)
    dp.load(args.path)
    dp.commit()
    new_db_size = context.db_size()
    print(f"Database {context.db_name}: {new_db_size:.0f} MB")
    print(f"Database grows: {new_db_size - db_size:.0f} MB ({((new_db_size - db_size) / db_size) * 100:.1f}%)")

    # data/iris/base-ic-evol-struct-pop-2020.CSV