import art
import config
import pandas
import argparse
from sqlentities import Context
from sae_parser import SAEParser

class POPParser(SAEParser):

    def read_csv(self, path: str) -> pandas.DataFrame:
        df = pandas.read_csv(path, sep=",", encoding="latin_1", low_memory=False)
        return df

    def load(self, path: str):
        print(f"Load {path}")
        df = self.read_csv(path)
        df.columns= df.columns.str.strip().str.lower()
        context.create_engine()
        with context.engine.begin() as connection:
            df.to_sql("pop", connection, if_exists="replace", index_label='id')

if __name__ == '__main__':
    art.tprint(config.name, "big")
    print("POP Parser")
    print("==========")
    print(f"V{config.version}")
    print(config.copyright)
    print()
    parser = argparse.ArgumentParser(description="POP Parser")
    parser.add_argument("path", help="file path")
    parser.add_argument("-e", "--echo", help="Sql Alchemy echo", action="store_true")
    args = parser.parse_args()
    context = Context()
    context.create(echo=args.echo)
    db_size = context.db_size()
    print(f"Database {context.db_name}: {db_size:.0f} Mb")
    sp = POPParser(context)
    sp.load(args.path)
    new_db_size = context.db_size()
    print(f"Database {context.db_name}: {new_db_size:.0f} Mb")
    print(f"Database grows: {new_db_size - db_size:.0f} Mb ({((new_db_size - db_size) / db_size) * 100:.1f}%)")