from sqlalchemy.orm import joinedload

from ps_parser import PSParser
from sqlentities import Context, PS, PSMerge
import argparse
import art
import config


class PSChangeKey(PSParser):

    def __init__(self, context):
        super().__init__(context)

    def find_and_change(self, source: str, dest: str) -> PS:
        ps = self.context.session.query(PS).filter(PS.key == source).one_or_none()
        if ps is None:
            print(f"{source} does not exist")
            quit(1)
        print(f"Found {ps}")
        ps.key = dest
        merge = PSMerge()
        merge.key = source
        merge.inpp = dest
        self.context.session.add(merge)
        print(f"Change to {ps}")
        self.nb_new_entity += 1
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
    print(f"Nb key changed: {psm.nb_new_entity}")