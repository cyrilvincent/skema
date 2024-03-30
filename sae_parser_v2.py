import difflib
import os
from typing import Dict, List, Tuple, Optional, Set
from sqlalchemy.orm import joinedload
from sqlentities import Context, Cabinet, PS, AdresseRaw, AdresseNorm, PSCabinetDateSource, PAAdresse, PSMerge, \
    Profession, PersonneActivite, SAE0
from base_parser import BaseParser
import argparse
import art
import config
import psycopg2
import pandas

class SAEParser(BaseParser):

    def __init__(self, context, echo=False):
        super().__init__(context)
        self.echo = echo
        self.saes: Tuple[Dict[Tuple[str, int], int], Dict[Tuple[str, int], int]] = ({}, {})
        self.sae_num = 0
        self.file: Optional[str] = None
        self.encoding = "utf-8"
        self.connection = psycopg2.connect(self.context.connection_string)
        self.dataframe: Optional[pandas.DataFrame] = None
        self.columns: Tuple[Dict[str, str], Dict[str, str]] = ({}, {})
        self.bor = ""

    def __del__(self):
        try:
            self.connection.close()
        except:
            pass

    def load_cache(self):
        print("Making cache")
        l: List[SAE0] = self.context.session.query(SAE0).all()
        for e in l:
            self.saes[0][e.key] = e.id
            self.nb_ram += 1
        print(f"{self.nb_ram} objects in cache")
        self.context.session.commit()

    def execute(self, sql) -> List[Tuple]:
        c = self.execute_void(sql)
        return c.fetchall()

    def execute_one(self, sql) -> Tuple:
        c = self.execute_void(sql)
        return c.fetchone()

    def execute_void(self, sql):
        c = self.connection.cursor()
        if self.echo:
            print(f"Execute {sql}")
        c.execute(sql)
        return c

    def columns_from_sae(self, table: str, schema="public"):
        sql = f"SELECT * FROM information_schema.columns WHERE table_schema = '{schema}' AND table_name = '{table}'"
        rows = self.execute(sql)
        for row in rows:
            self.columns[self.sae_num][row[3]] = row[7] if row[8] is None else f"{row[7]}[{row[8]}]"

    def alter_table(self, table: str, column: str, type: str, schema="public"):
        sql = f"ALTER TABLE {schema}.{table} ADD {column} {type}"
        self.execute_void(sql)
        self.connection.commit()

    def update_row(self, key: Tuple[str, int], cols):
        sql = f"UPDATE sae{self.sae_num}"
        first = True
        for col in cols.keys():
            if str(cols[col]) != "nan":
                if first:
                    first = False
                    sql += f" SET {self.column_name(col)}='{cols[col]}'"
                else:
                    sql += f",{self.column_name(col)}='{cols[col]}'"
        sql += f" WHERE nofinesset='{key[0]}' AND an={key[1]}"
        if first == False:
            self.execute_void(sql)
            self.connection.commit()

    def bor_from_file(self):
        index = self.file.rindex("_")
        self.bor = self.file[:index].lower()

    def column_name(self, name: str):
        name = name.lower()
        if name.startswith(f"{self.bor}_"):
            return name
        return f"{self.bor}_{name}"

    def convert_pandas_type(self, s):
        if s == "float64":
            return "FLOAT"
        if s == "integer":
            return "INTEGER"
        return "VARCHAR[255]"

    def mapper(self, row):
        sae = SAE0() #if self.sae_num == 0 else SAE1()
        try:
            sae.an = row["AN"]
            sae.nofinesset = row["nofinesset"]
            sae.nofinessej = row["nofinessej"]
        except Exception as ex:
            print(f"ERROR SAE {self.file} row {self.row_num} {sae}\n{ex}")
            quit(1)
        return sae

    def parse_row(self, row):
        e = self.mapper(row[1])
        if e.key not in self.saes[self.sae_num]:
            self.saes[self.sae_num][e.key] = e.id
            self.context.session.add(e)
            self.context.session.commit()
        self.update_row(e.key, row[1][4:])


    def check_columns(self):
        for c in self.dataframe.columns[4:]:
            name = self.column_name(c)
            if name not in self.columns[self.sae_num]:
                type = self.convert_pandas_type(str(self.dataframe[c].dtype))
                print(f"Create columns {name} of type {type}")
                self.alter_table(f"sae{self.sae_num}", name, type)

    def load_dataframe(self, path: str):
        dtype = {"nofinesset": str, "nofinessj": str, "AN":int, "BOR":str}
        self.encoding = "utf-8"
        try:
            self.dataframe = pandas.read_csv(path, sep=";", dtype=dtype, low_memory=False)
        except UnicodeDecodeError:
            self.encoding = "latin_1"
            self.dataframe = pandas.read_csv(path, sep=";", dtype=dtype, encoding=self.encoding, low_memory=False)
        print(f"Found {len(self.dataframe)} lines")

    def load_sae(self, file: str):
        self.load_cache()
        self.file = file
        print(f"Load {self.path + self.file}")
        self.bor_from_file()
        self.load_dataframe(self.path + self.file)
        self.columns_from_sae(f"sae{self.sae_num}")
        self.check_columns()
        for row in self.dataframe.iterrows():
            self.parse_row(row)

    def scan(self, path: str):
        print(f"Scan {path}")
        self.path = path
        l = os.listdir(path)
        for f in l:
            if f.endswith(".csv"):
                self.load_sae(f)

if __name__ == '__main__':
    art.tprint(config.name, "big")
    print("SAE Parser V2")
    print("=============")
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
    sp = SAEParser(context)
    # sp.scan(args.path, args.echo)
    sp.path = args.path
    sp.echo = False
    sp.load_sae("BIO_2019.csv")
    new_db_size = context.db_size()
    print(f"Number of columns: {len(sp.columns[0])}+{len(sp.columns[1])}")
    print(f"Database {context.db_name}: {new_db_size:.0f} Mb")
    print(f"Database grows: {new_db_size - db_size:.0f} Mb ({((new_db_size - db_size) / db_size) * 100:.1f}%)")

    # data/sae/