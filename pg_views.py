from typing import List, Tuple

import psycopg2
import argparse

class PGIntrospection:

    def __init__(self, connection_string, echo=True):
        self.echo = echo
        print(f"Connect to {connection_string}")
        self.connection = psycopg2.connect(connection_string)
        self.nb_col = 0

    def execute(self, sql):
        c = self.connection.cursor()
        if self.echo:
            print(f"Execute {sql}")
        c.execute(sql)
        return c.fetchall()

    def get_schema_from_table_name(self, table: str) -> Tuple[str, str]:
        if "." in table:
            schema, table = table.split(".")
        else:
            schema = "public"
        return schema, table

    def get_columns_from_table(self, table: str, schema: str):
        sql = f"SELECT * FROM information_schema.columns WHERE table_schema = '{schema}' AND table_name = '{table}'"
        rows = self.execute(sql)
        cols = [row[3] for row in rows]
        return cols

    def get_columns_view_from_table(self, table: str, except_cols: List[str]=[]):
        schema, table = self.get_schema_from_table_name(table)
        cols = self.get_columns_from_table(table, schema)
        table = table.replace('"',"").replace(" ", "")
        if schema == "public":
            cols = [f"{table}.{col} as {table}_{col}" for col in cols if col not in except_cols]
        else:
            cols = [f"{schema}.{table}.{col} as {schema}_{table}_{col}" for col in cols if col not in except_cols]
        self.nb_col += len(cols)
        return ", ".join(cols)

    def get_tables_from_schema(self, schema: str, except_table:List[str]=["covid19"]):
        sql = f"select * from pg_tables where schemaname='{schema}'"
        rows = self.execute(sql)
        tables = [f"{schema}.{row[1]}" for row in rows if row[1] not in except_table]
        return tables

    def get_view_from_schema(self, view_name: str, from_table: str, schema: str, parent_key: str, child_key: str):
        tables = self.get_tables_from_schema(schema)
        return self.get_view_from_tables(view_name, from_table, tables, parent_key, child_key)

    def get_view_from_table_list(self, view_name: str, from_table: str, table_list: str, parent_key: str, child_key: str):
        tables = table_list.split(",")
        return self.get_view_from_tables(view_name, from_table, tables, parent_key, child_key)

    def get_view_from_tables(self, view_name: str, from_table: str, tables: List[str], parent_key: str, child_key: str):
        cols = [self.get_columns_view_from_table(table, ["id", "nofinessej", "bor", child_key]) for table in tables]
        view = f"CREATE OR REPLACE VIEW {view_name} AS\n"
        view += f"SELECT {from_table}.*,\n\t"
        view += ",\n\t".join(cols)
        view += f"\nFROM {from_table}\n"
        for table in tables:
            view += f"FULL JOIN {table} ON {from_table}.{parent_key} = {table}.{child_key}\n"
        return view

    def __del__(self):
        try:
            self.connection.close()
        except:
            pass


if __name__ == '__main__':
    print("PG Views")
    print("========")
    print()
    parser = argparse.ArgumentParser(description="PG Introspection View")
    parser.add_argument("connection_string", help="Connection String")
    parser.add_argument("-e", "--echo", help="Sql Alchemy echo", action="store_true")
    parser.add_argument("-f", "--from_table", help="The from table if -s or column list for the table")
    parser.add_argument("-s", "--schema", help="View that concatenate all table of the schema, must have -f")
    parser.add_argument("-l", "--table_list", help="Table list for the view, separate by comma, must have -f")
    parser.add_argument("-p", "--parent_key", help="Parent key")
    parser.add_argument("-c", "--child_key", help="Child key")
    parser.add_argument("-v", "--view_name", help="View name")
    args = parser.parse_args()
    pg = PGIntrospection(args.connection_string, args.echo)
    if args.schema and args.table_list:
        res = pg.get_view_from_table_list(args.view_name, args.from_table, args.table_list, args.parent_key, args.child_key)
        print(res)
    elif args.table_list:
        res = pg.get_view_from_table_list(args.view_name, args.from_table, args.table_list, args.parent_key, args.child_key)
        print(res)
    else:
        res = pg.get_view_from_schema(args.view_name, args.from_table, args.schema, args.parent_key, args.child_key)
        print(res)
    print(f"Found {pg.nb_col} columns")


    # "postgresql://postgres:sa@localhost/icip" -e -s sae -f structure -c nofinesset -p finess -v structure_sae