import argparse
from typing import Optional

import art
import config
import pandas
import os
from sqlalchemy import create_engine
from sqlentities import Context, DateSource


class EhpadParser:

    def __init__(self):
        self.yy = 0
        self.mm = 0

    def parse_date(self, path):
        # noinspection PyBroadException
        try:
            self.yy = int(path[-12:-10])
            if self.yy < 13:
                self.mm = self.yy
                self.yy = int(path[-14:-12])
        except:
            print("ERROR: file must have date like this: *-YYYY-brute.csv or *-YYYYMM-brute.csv")

    def check_date(self, path):
        self.parse_date(path)
        context = Context()
        context.create()
        db_date = context.session.query(DateSource).get(self.yy * 100 + self.mm)
        if db_date is None:
            ds = DateSource(self.yy, self.mm)
            print(f"Added date {ds}")
            context.session.add(ds)
            context.session.commit()

    def load(self, path):
        print(f"Load {path}")
        self.check_date(path)
        df = pandas.read_csv(path, delimiter=";", na_values=["\\0", "\\N", ""], encoding="ANSI", decimal=",")
        df.columns = df.columns.str.strip().str.lower()
        if __name__ == '__main__':
            df["datesource_id"] = self.yy * 100 + self.mm
        print(df)
        engine = create_engine(config.connection_string, echo=False)
        with engine.begin() as connection:
            df.to_sql("ehpad", con=connection, if_exists="append", index=False)
            # Pb Pandas 2.2 need SqlAlchemy 2
            # Pandas 2.1 need SqlAlchemy 1.4.36 (I have 1.4.29)

    def scan(self, path: str):
        print(f"Scan {path}")
        l = os.listdir(path)
        for f in l:
            if f.endswith(".csv"):
                self.load(path + f)


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
    # p.scan("data/ehpad/")
    # data/ehpad/cnsa-export-prix-ehpad-2018-brute.csv
    # 32444 => 18945
    # select * from ehpad where "finessEt" = '010002228'
    # 5 => 3
