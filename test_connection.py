from sqlentities import Context
import art
import config
import pandas as pd
import numpy as np
import sqlalchemy
import psycopg2

art.tprint(config.name, "big")
print("Test PostgreSql Connection")
print("==========================")
print(f"V{config.version}")
print(config.copyright)
print(pd.__version__, np.__version__, sqlalchemy.__version__, psycopg2.__version__)

print(f"Try to connect to {config.connection_string}")
context = Context()
context.create()
db_size = context.db_size()
print(f"Database {context.db_name}: {db_size:.0f} Mo")
print("OK")
