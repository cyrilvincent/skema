import psycopg2
from sqlentities import Context, DateSource
from base_parser import time0
import argparse
import time
import art
import config
import pandas as pd


class FiloParser:

    def __init__(self, context):
        self.context = context
        self.df = None
        self.year = 0
        self.is_dec = False
        self.sep = ";"

    def parse_year_dec(self, path: str):
        try:
            i = path.index("20")
            self.year = int(path[i+2:i+4])
            self.is_dec = "DEC" in path
            print(f"Found is_dec:{self.is_dec} for 20{self.year}")
        except IndexError:
            print("ERROR: file must have date like this: file_2021_DEC.csv")
            quit(1)

    def load(self, path):
        print(f"Parse {path}")
        self.parse_year_dec(path)
        pd.set_option('display.max_columns', None)
        pd.set_option('display.width', None)
        self.sep = "," if self.year == 19 and self.is_dec else ";"
        self.df = pd.read_csv(path, low_memory=False, sep=self.sep, decimal=",", na_values=["", "ns", "so", "nd", "s"])
        for col in self.df.columns:
            if self.is_dec and col.startswith("DEC_"):
                self.df = self.df.rename(columns={col: col[4:]})
            elif not self.is_dec and col.startswith("DISP_"):
                self.df = self.df.rename(columns={col: col[5:]})
        for col in self.df.columns:
            if col.endswith(str(self.year)):
                self.df = self.df.rename(columns={col: col[:-2]})
        self.df.columns = self.df.columns.str.strip().str.lower()
        if self.is_dec:
            self.df["ppat"] = None
            self.df["ppsoc"] = None
            self.df["ppfam"] = None
            self.df["ppmini"] = None
            self.df["pplogt"] = None
            self.df["pimpot"] = None
        self.df["iris_string"] = self.df["iris"]
        self.df["iris"] = self.df["iris"].replace("2A", "201", regex=True).replace("2B", "202", regex=True)
        self.df["iris"] = self.df["iris"].astype(int)
        self.df["is_dec"] = self.is_dec
        self.df["year"] = self.year
        print(self.df)

    def commit(self):
        print("Deleting old values")
        table_name = "filo"
        try:
            conn = psycopg2.connect(config.connection_string)
            sql = f"delete from iris.{table_name} where year={self.year} and is_dec is {str(self.is_dec).lower()}"
            with conn.cursor() as cur:
                cur.execute(sql)
            conn.commit()
            conn.close()
        except:
            pass
        print("Committing")
        self.df.to_sql(table_name, config.connection_string, schema="iris", chunksize=10000, if_exists="append", index=False)
        print("Committed")


if __name__ == '__main__':
    art.tprint(config.name, "big")
    print("Filo Parser")
    print("===========")
    print(f"V{config.version}")
    print(config.copyright)
    print()
    parser = argparse.ArgumentParser(description="Filo Parser")
    parser.add_argument("path", help="Path")
    parser.add_argument("-e", "--echo", help="Sql Alchemy echo", action="store_true")
    args = parser.parse_args()
    context = Context()
    context.create(echo=args.echo, expire_on_commit=False)
    db_size = context.db_size()
    print(f"Database {context.db_name}: {db_size:.0f} MB")
    fp = FiloParser(context)
    fp.load(args.path)
    fp.commit()
    fp.load(args.path.replace("_DEC", "_DISP"))
    fp.commit()
    new_db_size = context.db_size()
    print(f"Database {context.db_name}: {new_db_size:.0f} MB")
    print(f"Database grows: {new_db_size - db_size:.0f} MB ({((new_db_size - db_size) / db_size) * 100:.1f}%)")

    # D'après : https://www.insee.fr/fr/statistiques/8229323 & https://www.insee.fr/fr/recherche/recherche-statistiques?q=revenus%2C%20pauvret%C3%A9%20et+niveau+de+vie+iris&debut=0&idprec=4295611&categorie=5
    # data/filo/BASE_TD_FILO_IRIS_2021_DEC.csv
    # data/filo/BASE_TD_FILO_DEC_IRIS_2020.csv
