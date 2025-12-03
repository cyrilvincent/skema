import art
import config
import argparse
from sae.generic_finess_parser import GenericFinessParser
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

# Solution 1 : pg_views : b de la limite des colonnes et des colonnes AN qui sont dupliquées
# Solution 2 : Parser dynamique qui créé 1 seule (ou 2, voir 3) table SAE avec les colonnes id, nofinness et an commune et qui créer dynamiquement la colonne au besoin en la prefixant par le nom de l'ancienne table si pas présent
#   avant chaque insert, il vérifie l'an et la colonne si la colonne n'existe pas il fait un alter puis un update
#   on commence dont pas une table contenant uniquement id, nofiness et an, le reste est créé automatiquement
#   CREATE TABLE IF NOT EXISTS sae{i} (id ...);
#   Beaucoup de numérique => Créer la colonne en float si erreur passer en varchar => avoir la structure de la table en dict(nomcol:type)
#   Insert from dict (hélas pas de update) : https://stackoverflow.com/questions/29461933/insert-python-dictionary-using-psycopg2
# Parser directement les fichiers originaux

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

