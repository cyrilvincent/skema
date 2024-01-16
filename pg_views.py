import psycopg2
import argparse

class PGIntrospection:

    def __init__(self, connection_string, echo=True):
        self.echo = echo
        print(f"Connect to {connection_string}")
        self.connection = psycopg2.connect(connection_string)

    def execute(self, sql):
        c = self.connection.cursor()
        if self.echo:
            print(f"Execute {sql}")
        c.execute(sql)
        return c.fetchall()

    def get_columns_from_table(self, table: str, schema="public"):
        sql = f"SELECT * FROM information_schema.columns WHERE table_schema = '{schema}' AND table_name = '{table}'"
        rows = self.execute(sql)
        cols = [row[3] for row in rows]
        return cols

    def get_columns_view_from_table(self, table:str, schema="public"):
        cols = self.get_columns_from_table(table, schema)
        table = table.replace('"',"").replace(" ", "")
        if schema == "public":
            cols = [f"{table}.{col} as {table}_{col}" for col in cols]
        else:
            cols = [f"{schema}.{table}.{col} as {schema}_{table}_{col}" for col in cols]
        return ", ".join(cols)

    def get_tables_from_schema(self, schema: str):
        sql = f"select * from pg_tables where schemaname='{schema}'"
        rows = self.execute(sql)
        tables = [row[1] for row in rows]
        return tables

    def get_view_from_schema(self, schema: str):
        tables = self.get_tables_from_schema(schema)
        cols = [self.get_columns_view_from_table(table, schema) for table in tables]
        return ",\n\t".join(cols)

    def __del__(self):
        try:
            self.connection.close()
        except:
            pass


if __name__ == '__main__':
    print("PG Views")
    print("====================")
    print()
    parser = argparse.ArgumentParser(description="PG Introspection View")
    parser.add_argument("connection_string", help="Connection String")
    parser.add_argument("-e", "--echo", help="Sql Alchemy echo", action="store_true")
    parser.add_argument("-t", "--table", help="Column list for the table")
    parser.add_argument("-s", "--schema", help="View that concatenate all table of the schema")
    args = parser.parse_args()
    pg = PGIntrospection(args.connection_string, args.echo)
    if args.table:
        res = pg.get_columns_view_from_table(args.table)
        print(res)
    elif args.schema:
        res = pg.get_view_from_schema(args.schema)
        print(res)


    # "postgresql://postgres:sa@localhost/icip" -e -t personne
    # "postgresql://postgres:sa@localhost/icip" -e -s sae