import psycopg2
from sqlentities import Context
from base_parser import time0
import argparse
import time
import art
import config
import pandas as pd


class PSLibreAccesRawParser:

    def __init__(self, context):
        self.date_source_id = None
        self.df = None

    def parse_date(self, path):
        try:
            yy = int(path[-14:-12])
            mm = int(path[-12:-10])
            self.date_source_id = yy*100+mm
        except IndexError:
            print("ERROR: file must have date like this: file_YY-MM.csv")
            quit(1)

    def load(self, path):
        self.parse_date(path)
        print("Loading")
        self.df = pd.read_csv(path, delimiter="|", low_memory=False,
                              dtype={'Identifiant PP': 'str', 'Identification nationale PP': 'str'})
        self.df["inpp"] = self.df["Identification nationale PP"]
        self.df["code_mode_exercice"] = self.df["Code mode exercice"]
        self.df["cp"] = self.df["Code postal (coord. structure)"]
        self.df["code_diplome"] = self.df["Code savoir-faire"]
        self.df["dep"] = self.df["Code Département (structure)"]
        self.df = self.df[["inpp", "code_mode_exercice", "cp", "code_diplome"]]
        self.df["date_source_id"] = self.date_source_id
        self.df = self.df.dropna()

    def commit(self):
        print("Deleting old values")
        try:
            conn = psycopg2.connect(config.connection_string)
            sql = f"delete from apl.ps_libreacces where date_source_id={self.date_source_id}"
            with conn.cursor() as cur:
                cur.execute(sql)
            conn.commit()
            conn.close()
        except:
            pass
        print("Commiting")
        self.df.to_sql("ps_libreacces", config.connection_string, schema="apl", chunksize=1000, if_exists="append", index=False)
        print("Commited")


if __name__ == '__main__':
    art.tprint(config.name, "big")
    print("PS LibreAcces Parser")
    print("====================")
    print(f"V{config.version}")
    print(config.copyright)
    print()
    parser = argparse.ArgumentParser(description="PS LibreAcces Parser")
    parser.add_argument("path", help="Path")
    parser.add_argument("-e", "--echo", help="Sql Alchemy echo", action="store_true")
    args = parser.parse_args()
    context = Context()
    context.create(echo=args.echo, expire_on_commit=False)
    db_size = context.db_size()
    print(f"Database {context.db_name}: {db_size:.0f} MB")
    psp = PSLibreAccesRawParser(context)
    psp.load(args.path)
    psp.commit()
    new_db_size = context.db_size()
    print(f"Database {context.db_name}: {new_db_size:.0f} MB")
    print(f"Database grows: {new_db_size - db_size:.0f} MB ({((new_db_size - db_size) / db_size) * 100:.1f}%)")

    # data/ps_libreacces/PS_LibreAcces_Personne_activite_small_202010071006.txt -e
    # data/ps_libreacces/PS_LibreAcces_Personne_activite_202010071006.txt
    # PS_LibreAcces_Personne_activite_202112020908.txt
