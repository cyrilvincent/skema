from sqlentities import Context
import art
import config

art.tprint(config.name, "big")
print("Test PostgreSql Connection")
print("==========================")
print(f"V{config.version}")
print(config.copyright)
print()
print(f"Try to connect to {config.connection_string}")
context = Context()
context.create()
db_size = context.db_size()
print(f"Database {context.db_name}: {db_size:.0f} Mo")
print("OK")
