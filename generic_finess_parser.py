import art
import config
import pandas
import argparse
import os
from sqlentities import Context


class GenericFinessParser:

    def __init__(self, context):
        self.context = context

    def scan(self, path: str, schema):
        print(f"Scan {path}")
        l = os.listdir(path)
        for f in l:
            if f.endswith(".csv"):
                self.load(path, f, schema)

    def get_name_from_file(self, file: str) -> str:
        index = file.rindex("_")
        s = file[0:index]
        return s.lower()

    def read_csv(self, path: str) -> pandas.DataFrame:
        dtype = {"nofinesset": str, "nofinessj": str, "AN":int}
        try:
            df = pandas.read_csv(path, sep=";", dtype=dtype, low_memory=False)
        except UnicodeDecodeError:
            df = pandas.read_csv(path, sep=";", dtype=dtype, encoding="latin_1", low_memory=False)
        return df

    def load(self, path: str, file: str, schema: str):
        path = f"{path}/{file}"
        print(f"Load {path}")
        name = self.get_name_from_file(file)
        df = self.read_csv(path)
        df.columns= df.columns.str.strip().str.lower()
        context.create_engine()
        with context.engine.begin() as connection:
            df.to_sql(name, connection, schema=schema, if_exists="replace", index_label='id')

if __name__ == '__main__':
    art.tprint(config.name, "big")
    print("Generic Finess Parser")
    print("=====================")
    print(f"V{config.version}")
    print(config.copyright)
    print()
    parser = argparse.ArgumentParser(description="Genric Finess Parser")
    parser.add_argument("path", help="Directory path")
    parser.add_argument("-e", "--echo", help="Sql Alchemy echo", action="store_true")
    args = parser.parse_args()
    context = Context()
    context.create(echo=args.echo)
    db_size = context.db_size()
    print(f"Database {context.db_name}: {db_size:.0f} Mb")
    gfp = GenericFinessParser(context)
    gfp.scan(args.path, "generic")
    new_db_size = context.db_size()
    print(f"Database {context.db_name}: {new_db_size:.0f} Mb")
    print(f"Database grows: {new_db_size - db_size:.0f} Mb ({((new_db_size - db_size) / db_size) * 100:.1f}%)")

    # data/generic