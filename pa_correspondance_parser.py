from typing import Dict, List, Tuple, Optional

from sqlalchemy.orm import joinedload
from sqlentities import Context, Diplome, Profession, CodeProfession
from base_parser import BaseParser, time0
import argparse
import time
import art
import config


class PACorrespondanceParser(BaseParser):

    def __init__(self, context):
        super().__init__(context)
        self.savoir_faires: Dict[str, Diplome] = {}
        self.code_professions: Dict[int, CodeProfession] = {}

    def load_cache(self):
        print("Making cache")
        l = self.context.session.query(Diplome).filter(Diplome.is_savoir_faire == True)
        for s in l:
            self.savoir_faires[s.key] = s
        l = self.context.session.query(CodeProfession).all()
        for c in l:
            self.code_professions[c.id] = c
        l: List[Profession] = self.context.session.query(Profession) \
            .options(joinedload(Profession.code_professions)).options(joinedload(Profession.diplomes)).all()
        for p in l:
            self.entities[p.id] = p

    def check_date(self, path):
        pass

    def mapper(self, row) -> Tuple[Optional[int], Optional[str], Optional[int]]:
        profession_id: Optional[int] = None
        savoir_faire_code: Optional[str] = None
        code_profession: Optional[int] = None
        try:
            profession_id = self.get_nullable_int(row["\ufeffprofession"])
            savoir_faire_code = self.get_nullable(row["Code savoir-faire"])
            code_profession = self.get_nullable_int(row["code profession"])
        except Exception as ex:
            print(f"ERROR Correspondance row {self.row_num} {profession_id} {savoir_faire_code}\n{ex}\n{row}")
            quit(1)
        return (profession_id, savoir_faire_code, code_profession)

    def parse_row(self, row):
        id, code, cp = self.mapper(row)
        if id is not None:
            p: Profession = self.entities[id]
            update = False
            if code is not None:
                s: Diplome = self.savoir_faires[code]
                if s not in p.diplomes:
                    update = True
                    p.diplomes.append(s)
            if cp is not None:
                if cp in self.code_professions:
                    c: CodeProfession = self.code_professions[cp]
                    if c not in p.code_professions:
                        update = True
                        p.code_professions.append(c)
            if update:
                self.nb_new_entity += 1
                self.context.session.commit()


if __name__ == '__main__':
    art.tprint(config.name, "big")
    print("Personne Activite Correspondance Parser")
    print("=======================================")
    print(f"V{config.version}")
    print(config.copyright)
    print()
    parser = argparse.ArgumentParser(description="Personne Activite Correspondance Parser")
    parser.add_argument("path", help="Path")
    parser.add_argument("-e", "--echo", help="Sql Alchemy echo", action="store_true")
    args = parser.parse_args()
    context = Context()
    context.create(echo=args.echo, expire_on_commit=False)
    db_size = context.db_size()
    print(f"Database {context.db_name}: {db_size:.0f} Mo")
    psp = PACorrespondanceParser(context)
    psp.load(args.path, delimiter=',', encoding="UTF-8", header=True)
    print(f"New correspondance: {psp.nb_new_entity}")
    new_db_size = context.db_size()
    print(f"Database {context.db_name}: {new_db_size:.0f} Mo")
    print(f"Database grows: {new_db_size - db_size:.0f} Mo ({((new_db_size - db_size) / db_size) * 100:.1f}%)")
    print(f"Parse {psp.row_num} rows in {time.perf_counter() - time0:.0f} s")

    # data/ps_libreacces/Correspondance.csv
    # Ajout à la main : "S"	"Spécialité ordinale"	"SM55"	"Radio-diagnostic et Radio-thérapie"
