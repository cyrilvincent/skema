import difflib
from typing import Dict, List, Tuple, Optional

from sqlalchemy import false
from sqlalchemy.orm import joinedload
from sqlentities import Context, Cabinet, PS, AdresseRaw, AdresseNorm, PSCabinetDateSource, PAAdresse, PersonneActivite
from etab_parser import BaseParser, time0
import argparse
import time
import art
import config


class PSInppPatcher:

    def __init__(self, context):
        self.context = context
        self.entities: Dict[Tuple[str, str], List[PersonneActivite]] = {}
        self.nb_ram = 0
        self.nb = 0
        self.nb_update = 0
        self.nb_no_match = 0
        self.nb_ambiguity = 0

    def load_cache(self):
        print("Making cache")
        session = self.context.get_session()
        pas = session.query(PersonneActivite).all()
        for pa in pas:
            key1 = pa.nom, pa.prenom
            if key1 not in self.entities:
                self.entities[key1] = [pa]
            else:
                self.entities[key1].append(pa)
            self.nb_ram += 1
        print(f"{self.nb_ram} objects in cache")

    def patch(self):
        pss = self.context.session.query(PS).filter(PS.has_inpp.is_(False))
        for ps in pss:
            self.nb += 1
            pas = self.context.session.query(PersonneActivite).filter(
                (PersonneActivite.nom == ps.nom) & (PersonneActivite.prenom == ps.prenom)
            )
            inpps = set([pa.inpp for pa in pas])
            if len(inpps) == 1:
                self.nb_update += 1
                ps.key = list(inpps)[0]
                ps.has_inpp = True
                # self.context.session.commit()
            elif len(inpps) == 0:
                self.nb_no_match += 1
            else:
                self.nb_ambiguity += 1


if __name__ == '__main__':
    art.tprint(config.name, "big")
    print("PS INPP Patcher")
    print("===============")
    print(f"V{config.version}")
    print(config.copyright)
    print()
    parser = argparse.ArgumentParser(description="PS INPP Patcher")
    parser.add_argument("-e", "--echo", help="Sql Alchemy echo", action="store_true")
    args = parser.parse_args()
    context = Context()
    context.create(echo=args.echo, expire_on_commit=False)
    db_size = context.db_size()
    print(f"Database {context.db_name}: {db_size:.0f} Mo")
    psp = PSInppPatcher(context)
    psp.patch()
    print(f"Nb No INPP: {psp.nb}")
    print(f"INPP update: {psp.nb_update}")
    print(f"INPP no_match: {psp.nb_no_match}")
    print(f"INPP ambiguity: {psp.nb_ambiguity}")

    # PS = 172404 au total 137671 au 2112
    # has_inpp = 137671 soit 88% au 2112, 74% au total
    # update = 25670 => 91%
    # no_match = 5%
    # ambiguity = 3%

    # select count(*) from ps, cabinet, ps_cabinet_date_source
    # where ps_cabinet_date_source.cabinet_id = cabinet.id
    # and ps_cabinet_date_source.date_source_id = 2103
    # and ps_cabinet_date_source.ps_id = ps.id
    # and ps.has_inpp = true

    # NE PAS UTILISER CAR PS_TARIF_PARSER ne marcherait plus
    # Utiliser ps_parser qui va faire les update automatiquement, à vérifier

