import art
import config
import argparse
from generic_finess_parser import GenericFinessParser
from sqlentities import Context


class SAEParser(GenericFinessParser):

    def __init__(self, context):
        super().__init__(context)

if __name__ == '__main__':
    art.tprint(config.name, "big")
    print("SAE Parser")
    print("==========")
    print(f"V{config.version}")
    print(config.copyright)
    print()
    parser = argparse.ArgumentParser(description="SAE Parser")
    parser.add_argument("path", help="Directory path")
    parser.add_argument("-e", "--echo", help="Sql Alchemy echo", action="store_true")
    args = parser.parse_args()
    context = Context()
    context.create(echo=args.echo)
    db_size = context.db_size()
    print(f"Database {context.db_name}: {db_size:.0f} Mb")
    sp = SAEParser(context)
    sp.scan(args.path, "sae")
    new_db_size = context.db_size()
    print(f"Database {context.db_name}: {new_db_size:.0f} Mb")
    print(f"Database grows: {new_db_size - db_size:.0f} Mb ({((new_db_size - db_size) / db_size) * 100:.1f}%)")

# data/sae

# Pour mettre un FK sur nofinesset
# ALTER TABLE IF EXISTS sae.bio
#     ADD CONSTRAINT fk_sae_bio_nofinesset FOREIGN KEY (nofinesset)
#     REFERENCES public.etablissement (nofinesset) MATCH SIMPLE
#     ON UPDATE NO ACTION
#     ON DELETE NO ACTION
#     NOT VALID;
# NOT VALID vérifie uniquement la FK sur les insert et updates
# ALTER TABLE sae.bio DISABLE TRIGGER ALL; -- désactive les FK
# update sae.bio set nofinesset = '010000024X' where nofinesset = '010000024'
# ALTER TABLE sae.bio ENABLE TRIGGER ALL;
# Ou alors virer les finess non existant dans etablissement
# select * from sae.bio where nofinesset not in (select nofinesset from etablissement)

