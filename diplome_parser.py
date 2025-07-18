from typing import Dict, List

from sqlalchemy.orm import joinedload
from sqlentities import Context, Diplome, INPPDiplome, DateSource
from base_parser import BaseParser, time0
import argparse
import time
import art
import config


class DiplomeParser(BaseParser):

    def __init__(self, context, savoir=False):
        super().__init__(context)
        self.nb_new_diplome = 0
        self.diplomes: Dict[str, Diplome] = {}
        self.savoir = savoir

    def load_cache(self):
        print("Making cache")
        l: List[INPPDiplome] = self.context.session.query(INPPDiplome).options(joinedload(INPPDiplome.diplome)).all()
        for e in l:
            self.entities[e.key] = e
        l: List[Diplome] = self.context.session.query(Diplome).all()
        for d in l:
            self.diplomes[d.key] = d

    def parse_date(self, path):
        try:
            yy = int(path[-14:-12])
            mm = int(path[-12:-10])
            self.date_source = DateSource(annee=yy, mois=mm)
        except IndexError:
            print("ERROR: file must have date like this: file_YY-MM.csv")
            quit(1)

    def mapper(self, row) -> INPPDiplome:
        i = INPPDiplome()
        try:
            i.inpp = row["Identification nationale PP"]
        except Exception as ex:
            print(f"ERROR INPPDiplome row {self.row_num} {i}\n{ex}\n{row}")
            quit(1)
        return i

    def diplome_mapper(self, row) -> Diplome:
        d = Diplome()
        try:
            d.is_savoir_faire = False
            d.code_type_diplome = row["Code type diplôme obtenu"]
            if d.code_type_diplome == "AUT614":
                pass
            d.libelle_type_diplome = row["Libellé type diplôme obtenu"]
            d.code_diplome = row["Code diplôme obtenu"]
            d.libelle_diplome = row["Libellé diplôme obtenu"]
        except Exception as ex:
            print(f"ERROR Diplome row {self.row_num} {d}\n{ex}\n{row}")
            quit(2)
        return d

    def savoir_faire_mapper(self, row) -> Diplome:
        d = Diplome()
        try:
            d.is_savoir_faire = True
            d.code_type_diplome = row["Code type savoir-faire"]
            d.libelle_type_diplome = row["Libellé type savoir-faire"]
            d.code_diplome = row["Code savoir-faire"]
            d.libelle_diplome = row["Libellé savoir-faire"]
        except Exception as ex:
            print(f"ERROR Diplome savoir faire row {self.row_num} {d}\n{ex}\n{row}")
            quit(3)
        return d

    def parse_row(self, row):
        e = self.mapper(row)
        if self.savoir:
            d = self.savoir_faire_mapper(row)
        else:
            d = self.diplome_mapper(row)
        if d.key in self.diplomes:
            d = self.diplomes[d.key]
        else:
            self.diplomes[d.key] = d
            self.nb_new_diplome += 1
        if (e.inpp, d.key) not in self.entities:
            self.entities[(e.inpp, d.key)] = e
            e.diplome = d
            self.nb_new_entity += 1
            self.context.session.add(e)
        self.context.session.commit()

    def load(self, path: str):
        super().load(path, delimiter='|', encoding="UTF-8", header=True)


if __name__ == '__main__':
    art.tprint(config.name, "big")
    print("PS Parser")
    print("=========")
    print(f"V{config.version}")
    print(config.copyright)
    print()
    parser = argparse.ArgumentParser(description="PS Parser")
    parser.add_argument("path", help="Path")
    parser.add_argument("-e", "--echo", help="Sql Alchemy echo", action="store_true")
    parser.add_argument("-s", "--savoir", help="Savoir faire", action="store_true")
    args = parser.parse_args()
    context = Context()
    context.create(echo=args.echo, expire_on_commit=False)
    db_size = context.db_size()
    print(f"Database {context.db_name}: {db_size:.0f} Mb")
    psp = DiplomeParser(context, args.savoir)
    psp.load(args.path)
    print(f"New INPP-Diplome: {psp.nb_new_entity}")
    print(f"New diplome: {psp.nb_new_diplome}")
    new_db_size = context.db_size()
    print(f"Database {context.db_name}: {new_db_size:.0f} Mb")
    print(f"Database grows: {new_db_size - db_size:.0f} Mb ({((new_db_size - db_size) / db_size) * 100:.1f}%)")
    print(f"Parse {psp.row_num} rows in {time.perf_counter() - time0:.0f} s")

    # data/ps_libreacces/PS_LibreAcces_Dipl_AutExerc_202211130507.txt
    # data/ps_libreacces/PS_LibreAcces_SavoirFaire_202211130507.txt -s
    # data/ps_libreacces/PS_LibreAcces_Dipl_AutExerc_202506210923.txt

    # {"Type d'identifiant PP": '8', 'Identifiant PP': '10006164171', 'Identification nationale PP': '810006164171', "Nom d'exercice": 'PODEVIN', "Prénom d'exercice": 'EMMANUEL', 'Code type diplôme obtenu': 'DE', 'Libellé type diplôme obtenu': "Diplôme d'Etat français ", 'Code diplôme obtenu': 'DE09', 'Libellé diplôme obtenu': "Diplôme d'Etat français d'Infirmier", 'Code type autorisation': 'A', 'Libellé type autorisation': 'B', 'Code discipline autorisation': 'C', 'Libellé discipline autorisation': 'D', '': 'E'}
