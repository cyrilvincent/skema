import argparse

import art
import config
import pandas
from sqlalchemy import create_engine

from sqlentities import Context, DateSource


class EhpadParser:

    def __init__(self):
        self.date_source = None

    def parse_date(self, path):
        try:
            yy = int(path[-12:-10])
            self.date_source = DateSource(annee=yy, mois=0)
        except Exception:
            print("ERROR: file must have date like this: *-YYYY-brute.csv")

    def check_date(self, path):
        self.parse_date(path)
        context = Context()
        context.create()
        db_date = context.session.query(DateSource).get(self.date_source.id)
        if db_date is None:
            print(f"Added date {self.date_source}")
            context.session.add(self.date_source)
            context.session.commit()

    def load(self, path):
        print(f"Load {path}")
        self.check_date(path)
        df = pandas.read_csv(path, delimiter=";", na_values="\\N", encoding="ANSI", decimal=",")
        df["datesource_id"] = self.date_source.annee * 100
        print(df)
        engine = create_engine(config.connection_string, echo=False)
        with engine.begin() as connection:
            df.to_sql("ehpad", con=connection, if_exists="append", index=False)


if __name__ == '__main__':
    art.tprint(config.name, "big")
    print("Ehpad Parser")
    print("============")
    print(f"V{config.version}")
    print(config.copyright)
    print()
    parser = argparse.ArgumentParser(description="Ehpad Parser")
    parser.add_argument("path", help="Path")
    args = parser.parse_args()
    p = EhpadParser()
    p.load(args.path)

    # data/ehpad/cnsa-export-prix-ehpad-2018-brute.csv

