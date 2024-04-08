import os
from typing import Dict, List, Tuple, Optional
from sqlentities import Context, SAE, Structure, Etablissement
from base_parser import BaseParser
import argparse
import art
import config
import psycopg2
import pandas
import numpy as np
class SAEParser(BaseParser):

    def __init__(self, context, echo=False):
        super().__init__(context)
        self.echo = echo
        self.saes: Dict[Tuple[str, int], int] = {}
        self.structures: Dict[str, int] = {}
        self.etablissements: Dict[str, int] = {}
        self.file: Optional[str] = None
        self.encoding = "utf-8"
        self.connection = psycopg2.connect(self.context.connection_string)
        self.dataframe: Optional[pandas.DataFrame] = None
        self.columns: Dict[str, str] = {}
        self.bor = ""
        self.varchar_limit = 10
        self.nb_unique = 0
        self.schema = "sae2"

    def __del__(self):
        try:
            self.connection.close()
        except:
            pass

    def load_cache(self):
        print("Making cache")
        l: List[SAE] = self.context.session.query(SAE).all()
        for e in l:
            self.saes[e.key] = e.id
            self.nb_ram += 1
        l: List[Structure] = self.context.session.query(Structure).filter(Structure.finess.is_not(None)).all()
        for e in l:
            self.structures[e.finess] = e.id
            self.nb_ram += 1
        l: List[Etablissement] = self.context.session.query(Etablissement).all()
        for e in l:
            self.etablissements[e.nofinesset] = e.id
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
            self.columns[row[3]] = row[7] if row[8] is None else f"{row[7]}[{row[8]}]"

    def alter_table(self, table: str, column: str, type: str, schema="public"):
        sql = f"ALTER TABLE {schema}.{table} ADD {column} {type}"
        self.execute_void(sql)
        self.connection.commit()

    def add_fk(self, table: str, fk: str, foreign_table: str, foreign_column: str, schema="public", foreign_schema="public"):
        name = f"fk_{table}_{fk}_{foreign_table}_{foreign_column}"
        sql = f"ALTER TABLE {schema}.{table} ADD CONSTRAINT {name} FOREIGN KEY {fk} REFERENCES {foreign_schema}.{foreign_table} ({foreign_column})"
        self.execute_void(sql)
        self.connection.commit()

    def update_row(self, key: Tuple[str, int], cols):
        sql = f"UPDATE {self.schema}.sae"
        first = True
        for col in cols.keys():
            if str(cols[col]) != "nan":
                value = str(cols[col]).replace("'", "''")[:self.varchar_limit]
                if first:
                    first = False
                    sql += f" SET {self.column_name(col)}='{value}'"
                else:
                    sql += f",{self.column_name(col)}='{value}'"
        sql += f" WHERE nofinesset='{key[0]}' AND an={key[1]}"
        if first == False:
            self.execute_void(sql)
        self.connection.commit()

    def insert_sae(self, nofinesset: str, nofinessej: str, an: int, structure_id: int, etablissement_id: int):
        if structure_id == None:
            structure_id = "null"
        if etablissement_id == None:
            etablissement_id = "null"
        sql = f"INSERT INTO {self.schema}.sae (nofinesset, nofinessej, an, structure_id, etablissement_id) "
        sql += f"VALUES ('{nofinesset}', '{nofinessej}', {an}, {structure_id}, {etablissement_id})"
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
        return f"VARCHAR({self.varchar_limit})"

    def mapper(self, row):
        sae = SAE() #if self.sae_num == 0 else SAE1()
        try:
            try:
                sae.an = row["AN"]
            except:
                sae.an = row["an"]
            sae.nofinesset = row["nofinesset"]
            sae.nofinessej = row["nofinessej"]
            if sae.nofinesset in self.structures:
                sae.structure_id = self.structures[sae.nofinesset]
            if sae.nofinesset in self.etablissements:
                sae.etablissement_id = self.etablissements[sae.nofinesset]
        except Exception as ex:
            print(f"ERROR SAE {self.file} row {self.row_num} {sae}\n{ex}")
            quit(1)
        return sae

    def parse_row(self, row):
        e = self.mapper(row[1])
        if e.key not in self.saes:
            self.saes[e.key] = e.id
            self.insert_sae(e.nofinesset, e.nofinessej, e.an, e.structure_id, e.etablissement_id)
        self.update_row(e.key, row[1][4:])


    def check_columns(self):
        for c in self.dataframe.columns[4:]:
            name = self.column_name(c)
            if not(name.startswith("nofiness")) and name not in self.columns:
                type = self.convert_pandas_type(str(self.dataframe[c].dtype))
                # print(f"Creating columns {name} {type}")
                self.alter_table(f"sae", name, type, self.schema)

    def check_unique(self):
        df = self.dataframe[["nofinesset", "AN"]]
        res = df.drop_duplicates()
        return len(res) == len(df)

    def modify_dataframe(self):
        self.dataframe.columns = self.dataframe.columns.str.strip().str.lower()
        s = []
        e = []
        for f in self.dataframe["nofinesset"].values:
            if f in self.structures:
                s.append(self.structures[f])
            else:
                s.append(None)
            if f in self.etablissements:
                e.append(self.etablissements[f])
            else:
                e.append(None)
        self.dataframe.insert(4, "structure_id", np.array(s))
        self.dataframe.insert(4, "etablissement_id", np.array(e))

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
        self.file = file
        print(f"Load {self.path + self.file}")
        self.bor_from_file()
        self.load_dataframe(self.path + self.file)
        if self.check_unique():
            print(f"Adding to table {self.schema}.sae")
            self.nb_unique += 1
            self.columns_from_sae("sae", self.schema)
            self.check_columns()
            for row in self.dataframe.iterrows():
                self.parse_row(row)
        else:
            self.modify_dataframe()
            print(f"Creating table {self.schema}.{self.bor}")
            context.create_engine()
            with context.engine.begin() as connection:
                self.dataframe.to_sql(self.bor, connection, schema=self.schema, if_exists="replace", index_label='id')
            print(f"Adding FKs")
            self.add_fk(self.bor, "structure_id", "structure", "id", "sae2")
            self.add_fk(self.bor, "etablissement_id", "etablissement", "id", "sae2")

    def scan(self, path: str):
        self.load_cache()
        print(f"Scan {path}")
        self.path = path
        l = os.listdir(path)
        for f in l:
            if f.endswith(".csv") and not(f.startswith("ID_")):
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
    sp = SAEParser(context, args.echo)
    sp.scan(args.path)
    # sp.path = args.path
    # sp.load_cache()
    # sp.load_sae("BLOCS_P_2020.csv")
    new_db_size = context.db_size()
    print(f"Number of unique nofinesset+an: {sp.nb_unique}")
    print(f"Number of columns: {len(sp.columns)}")
    print(f"Database {context.db_name}: {new_db_size:.0f} Mb")
    print(f"Database grows: {new_db_size - db_size:.0f} Mb ({((new_db_size - db_size) / db_size) * 100:.1f}%)")

    # data/sae/