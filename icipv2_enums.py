from sqlentities import Context, EtablissementType
from typing import Set
import csv
import config
import art
import unidecode
import time
import os


class EnumsCreator:

    def etablissementType(self):
        print("EtablissementType")
        context = Context()
        context.create()
        et = EtablissementType()
        et.id = 1
        et.type = "Public"
        context.session.add(et)
        et = EtablissementType()
        et.id = 2
        et.type = "Privé non lucratif"
        context.session.add(et)
        et = EtablissementType()
        et.id = 3
        et.type = "Privé commercial"
        context.session.add(et)
        context.session.commit()


if __name__ == '__main__':
    art.tprint(config.name, "big")
    print("Sql Enums")
    print("=========")
    print(f"V{config.version}")
    print(config.copyright)
    print()
    e = EnumsCreator()
    e.etablissementType()
