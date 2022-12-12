from sqlalchemy.orm import joinedload

from ps_parser import PSParser
from sqlentities import Context, PS, PSMerge
import argparse
import art
import config


class PSChangeKey(PSParser):

    def __init__(self, context):
        super().__init__(context)

    def merge_factory(self, key: str, inpp: str) -> PSMerge:
        merge = PSMerge()
        merge.key = key
        merge.inpp = inpp
        exist = self.context.session.query(PSMerge) \
            .filter((PSMerge.key == merge.key) & (PSMerge.inpp == merge.inpp)).one_or_none()
        if exist is None:
            print(f"Create merge {merge}")
            self.context.session.add(merge)
        return merge

    def merge_ps(self, ps1: PS, ps2: PS) -> PS:
        print(f"Merge {ps1} to {ps2}")
        for pcd1 in list(ps1.ps_cabinet_date_sources):
            key1 = pcd1.cabinet_id, pcd1.date_source_id
            l2 = [(pcd2.cabinet_id, pcd2.date_source_id) for pcd2 in ps2.ps_cabinet_date_sources]
            ps1.ps_cabinet_date_sources.remove(pcd1)
            if key1 not in l2:
                ps2.ps_cabinet_date_sources.append(pcd1)
                print(f"Move ps_cabinet_date_sources {pcd1} to {ps2}")
            else:
                self.context.session.delete(pcd1)
        for tarif1 in list(ps1.tarifs):
            l2 = [tarif2.key for tarif2 in ps2.tarifs]
            ps1.tarifs.remove(tarif1)
            if tarif1.key not in l2:
                ps2.tarifs.append(tarif1)
                print(f"Move tarif {tarif1} to {ps2}")
            else:
                self.context.session.delete(tarif1)
        self.context.session.delete(ps1)
        self.merge_factory(ps1.key, ps2.key)
        return ps2

    def find_and_change(self, source: str, dest: str) -> PS:
        if len(dest) > 12:
            print(f"{dest} must have less than 12 char")
            quit(2)
        ps = self.context.session.query(PS).options(joinedload(PS.ps_cabinet_date_sources))\
            .options(joinedload(PS.tarifs)).filter(PS.key == source).one_or_none()
        if ps is None:
            print(f"PS key {source} does not exist")
            quit(1)
        print(f"Found {ps}")
        ps_dest = self.context.session.query(PS).options(joinedload(PS.ps_cabinet_date_sources))\
            .options(joinedload(PS.tarifs)).filter(PS.key == dest).one_or_none()
        if ps_dest is None:
            ps.key = dest
            self.merge_factory(source, dest)
            print(f"Change to {ps}")
            self.nb_new_entity += 1
        else:
            print(f"Found {ps_dest}")
            self.merge_ps(ps, ps_dest)
        return ps

    def change(self, source: str, dest: str):
        self.find_and_change(source, dest)
        self.context.session.commit()


if __name__ == '__main__':
    art.tprint(config.name, "big")
    print("PS Change Key")
    print("=============")
    print(f"V{config.version}")
    print(config.copyright)
    print()
    parser = argparse.ArgumentParser(description="PS Fusion")
    parser.add_argument("source", help="PS old key")
    parser.add_argument("dest", help="PS new key")
    parser.add_argument("-e", "--echo", help="Sql Alchemy echo", action="store_true")
    args = parser.parse_args()
    context = Context()
    context.create(echo=args.echo, expire_on_commit=False)
    psm = PSChangeKey(context)
    psm.change(args.source, args.dest)
