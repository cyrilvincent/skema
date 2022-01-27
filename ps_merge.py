import difflib
from typing import Dict, List, Tuple, Optional, Set
from sqlalchemy.orm import joinedload

from ps_parser import PSParser
from sqlentities import Context, Cabinet, PS, AdresseRaw, AdresseNorm, PSCabinetDateSource, PAAdresse, PSMerge
from base_parser import BaseParser, time0
import argparse
import time
import art
import config


class PSMerger(PSParser):

    def __init__(self, context):
        super().__init__(context)
        self.nb_cabinet_merged = 0
        self.nb_tarif_merged = 0

    def merge_ps(self, ps1: PS, ps2: PS) -> PS:
        print(f"Merge {ps1} to {ps2}")
        for pcd1 in list(ps1.ps_cabinet_date_sources):
            key1 = pcd1.cabinet_id, pcd1.date_source_id
            l2 = [(pcd2.cabinet_id, pcd2.date_source_id) for pcd2 in ps2.ps_cabinet_date_sources]
            ps1.ps_cabinet_date_sources.remove(pcd1)
            if key1 not in l2:
                ps2.ps_cabinet_date_sources.append(pcd1)
                self.nb_cabinet_merged += 1
            else:
                self.context.session.delete(pcd1)
        for tarif1 in list(ps1.tarifs):
            l2 = [tarif2.key for tarif2 in ps2.tarifs]
            ps1.tarifs.remove(tarif1)
            if tarif1.key not in l2:
                ps2.tarifs.append(tarif1)
                self.nb_tarif_merged += 1
            else:
                self.context.session.delete(tarif1)
        self.context.session.delete(ps1)
        merge = PSMerge()
        merge.key = ps1.key
        merge.inpp = ps2.key
        exist = self.context.session.query(PSMerge)\
            .filter((PSMerge.key == merge.key) & (PSMerge.inpp == merge.inpp)).one_or_none()
        if exist is None:
            self.context.session.add(merge)
        return ps2

    def find_and_merge(self, source: str, dest: str) -> PS:
        ps1 = self.context.session.query(PS).options(joinedload(PS.ps_cabinet_date_sources))\
            .options(joinedload(PS.tarifs)).filter(PS.key == source).one_or_none()
        if ps1 is None:
            print(f"{source} does not exist")
            quit(1)
        ps2 = self.context.session.query(PS).options(joinedload(PS.ps_cabinet_date_sources))\
            .options(joinedload(PS.tarifs)).filter(PS.key == dest).one_or_none()
        self.find_and_merge(ps1, ps2)
        return ps2

    def fusion(self, source: str, dest: str):
        self.find_and_merge(source, dest)
        self.context.session.commit()


if __name__ == '__main__':
    art.tprint(config.name, "big")
    print("PS Fusion")
    print("=========")
    print(f"V{config.version}")
    print(config.copyright)
    print()
    parser = argparse.ArgumentParser(description="PS Fusion")
    parser.add_argument("source", help="PS key from fusion")
    parser.add_argument("dest", help="INPP to fusion")
    parser.add_argument("-e", "--echo", help="Sql Alchemy echo", action="store_true")
    args = parser.parse_args()
    context = Context()
    context.create(echo=args.echo, expire_on_commit=False)
    psm = PSMerger(context)
    psm.fusion(args.source, args.dest)
    print(f"Nb Cabinet merged: {psm.nb_cabinet_merged}")
    print(f"Nb Tarif merged: {psm.nb_tarif_merged}")

    # select * from ps, ps_cabinet_date_source
    # where key = 'BENYOUB_DA_SILVA_KARIMA_01000'
    # and ps.id = ps_cabinet_date_source.ps_id
    # 16
    #
    # select * from ps, ps_cabinet_date_source
    # where key = '810100779536'
    # and ps.id = ps_cabinet_date_source.ps_id
    # 12
    #
    # select * from ps, tarif
    # where key = 'BENYOUB_DA_SILVA_KARIMA_01000'
    # and ps.id = tarif.ps_id
    # 27
    #
    # select * from ps, tarif
    # where key = '810100779536'
    # and ps.id = tarif.ps_id
    # 9


