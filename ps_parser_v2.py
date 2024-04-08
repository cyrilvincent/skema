import difflib
from operator import and_
from typing import Dict, List, Tuple, Optional
from sqlalchemy.orm import joinedload
from ps_parser import PSParser
from sqlentities import Context, Cabinet, PS, AdresseRaw, AdresseNorm, PSCabinetDateSource, PSMerge, Profession, \
    Personne, Coord, Activite, DiplomeObtenu
from base_parser import BaseParser
import argparse
import art
import config


class PSParserV2(PSParser):

    def __init__(self, context):
        super().__init__(context)
        self.nb_rule = 13



if __name__ == '__main__':
    art.tprint(config.name, "big")
    print("PS Parser V2")
    print("============")
    print(f"V{config.version}")
    print(config.copyright)
    print()
    parser = argparse.ArgumentParser(description="PS Parser")
    parser.add_argument("path", help="Path")
    parser.add_argument("-e", "--echo", help="Sql Alchemy echo", action="store_true")
    parser.add_argument("-n", "--nosave", help="No save", action="store_true")
    parser.add_argument("-t", "--trace", help="Trace in out.csv file", action="store_true")
    args = parser.parse_args()
    context = Context()
    context.create(echo=args.echo, expire_on_commit=False)
    db_size = context.db_size()
    print(f"Database {context.db_name}: {db_size:.0f} Mb")
    out_file = None
    if args.trace:
        out_file = open("data/ps/out/out.csv", "w")
    psp = PSParserV2(context)
    psp.load(args.path, encoding=None)
    if args.trace:
        out_file.close()
    print(f"New PS: {psp.nb_new_entity}")
    print(f"Update PS: {psp.nb_update_entity}")
    print(f"New cabinet: {psp.nb_cabinet}")
    print(f"New adresse: {psp.nb_new_adresse}")
    print(f"New adresse normalized: {psp.nb_new_norm}")
    print(f"Matching INPP: {psp.nb_inpps}/{psp.nb_unique_ps}: {(psp.nb_inpps / psp.nb_unique_ps) * 100:.0f}%")
    print(f"Matched rules: {psp.rules}")
    new_db_size = context.db_size()
    print(f"Database {context.db_name}: {new_db_size:.0f} Mb")
    print(f"Database grows: {new_db_size - db_size:.0f} Mb ({((new_db_size - db_size) / db_size) * 100:.1f}%)")

    # Avant de refaire tourner valider vider la table ps_merge

    # data/ps/plasticien-00-00.csv -n
    # data/ps/ps-tarifs-small-00-00.csv -e
    # data/ps/ps-tarifs-21-03.csv 88% 584s 89% 701s
    # "data/UFC/ps-tarifs-UFC Santé, Pédiatres 2016 v1-3-16-00.csv" /!\ update genre

    # select cast(data1.count1 as float)/ cast(data2.count2 as float)
    # from
    # (select count(*) as count1 from ps where has_inpp is true) data1,
    # (select count(*) as count2 from ps) data2

    # select cast(data1.count1 as float)/ cast(data2.count2 as float)
    # from
    # (select count(*) as count1 from ps, ps_cabinet_date_source
    #  	where ps_cabinet_date_source.ps_id = ps.id
    #  	and ps_cabinet_date_source.date_source_id = 2112
    #  	and has_inpp is true) data1,
    # (select count(*) as count2 from ps, ps_cabinet_date_source
    # 	where ps_cabinet_date_source.ps_id = ps.id
    #  	and ps_cabinet_date_source.date_source_id = 2112
    # ) data2
