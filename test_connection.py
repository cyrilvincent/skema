import difflib
from typing import Dict, List, Tuple, Optional, Set
from sqlalchemy.orm import joinedload
from sqlentities import Context, Cabinet, PS, AdresseRaw, AdresseNorm, PSCabinetDateSource, PAAdresse, PSMerge
from base_parser import BaseParser
import argparse
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
