from typing import Dict, List, Tuple, Optional

from sqlalchemy.orm import joinedload
from sqlentities import Context, PersonneActivite, PAAdresse, Dept
from etab_parser import BaseParser, time0
import argparse
import time
import art
import config


class PersonneActiviteParser(BaseParser):

    def __init__(self, context):
        super().__init__(context)
        self.pa_adresses: Dict[Tuple[int, str, str, str], PAAdresse] = {}
        self.nb_new_adresse = 0

    def load_cache(self):
        print("Making cache")
        l = self.context.session.query(Dept).all()
        for d in l:
            self.depts[d.num] = d
            self.depts_int[d.id] = d
        l: List[PersonneActivite] = self.context.session.query(PersonneActivite).all()
        for e in l:
            self.entities[e.inpp] = e
        l: List[PAAdresse] = self.context.session.query(PAAdresse)\
            .options(joinedload(PAAdresse.personne_activites)).all()
        for a in l:
            self.pa_adresses[a.key] = a

    def check_date(self, path):
        pass

    def mapper(self, row) -> PersonneActivite:
        pa = PersonneActivite()
        try:
            pa.inpp = row["Identification nationale PP"]
            pa.nom = self.normalize_string(row["Nom d'exercice"])
            pa.prenom = self.normalize_string(row["Prénom d'exercice"])
        except Exception as ex:
            print(f"ERROR PersonneActivite row {self.row_num} {pa}\n{ex}\n{row}")
            quit(1)
        return pa

    def pa_adresse_mapper(self, row) -> Optional[PAAdresse]:
        a = PAAdresse()
        try:
            cp = row["Code postal (coord. structure)"]
            if cp is not None and cp.isdigit():
                a.cp = int(cp)
            else:
                return None
            commune = row["Libellé commune (coord. structure)"]
            if commune == '':
                commune = row["Bureau cedex (coord. structure)"]
                if commune == '':
                    return None
                else:
                    cp = commune[:5]
                    if cp.isdigit() and len(commune) >= 6:
                        commune = commune[6:]
            a.commune = self.normalize_commune(commune)
            dept_num = self.get_dept_from_cp(a.cp)
            if dept_num not in self.depts_int:
                return None
            a.dept = self.depts_int[dept_num]
            num = row["Numéro Voie (coord. structure)"]
            if num is not None and num.isdigit():
                a.numero = int(num)
            if row["Libellé Voie (coord. structure)"] != '':
                a.rue = row["Libellé Voie (coord. structure)"]
                if row["Libellé type de voie (coord. structure)"] != '':
                    a.rue = row["Libellé type de voie (coord. structure)"] + " " + a.rue
            if a.rue is not None:
                a.rue = self.normalize_street(a.rue)
        except Exception as ex:
            print(f"ERROR pa_adresse row {self.row_num}: {a}\n{ex}\n{row}")
            quit(4)
        return a

    def create_update_adresse(self, e: PersonneActivite, row):
        a = self.pa_adresse_mapper(row)
        if a is not None:
            if a.key in self.pa_adresses:
                a = self.pa_adresses[a.key]
            else:
                self.nb_new_adresse += 1
                self.pa_adresses[a.key] = a
            keys = [a.key for a in e.pa_adresses]
            if a.key not in keys:
                e.pa_adresses.append(a)

    def parse_row(self, row):
        e = self.mapper(row)
        if e.inpp in self.entities:
            e = self.entities[e.inpp]
        else:
            self.nb_new_entity += 1
            self.entities[e.inpp] = e
            self.context.session.add(e)
        self.create_update_adresse(e, row)
        self.context.session.commit()


if __name__ == '__main__':
    art.tprint(config.name, "big")
    print("Personne Activite Parser")
    print("========================")
    print(f"V{config.version}")
    print(config.copyright)
    print()
    parser = argparse.ArgumentParser(description="Personne Activite Parser")
    parser.add_argument("path", help="Path")
    parser.add_argument("-e", "--echo", help="Sql Alchemy echo", action="store_true")
    args = parser.parse_args()
    context = Context()
    context.create(echo=args.echo, expire_on_commit=False)
    db_size = context.db_size()
    print(f"Database {context.db_name}: {db_size:.0f} Mo")
    psp = PersonneActiviteParser(context)
    psp.load(args.path, delimiter='|', encoding="UTF-8", header=True)
    print(f"New personne: {psp.nb_new_entity}")
    print(f"New adresse: {psp.nb_new_adresse}")
    new_db_size = context.db_size()
    print(f"Database {context.db_name}: {new_db_size:.0f} Mo")
    print(f"Database grows: {new_db_size - db_size:.0f} Mo ({((new_db_size - db_size) / db_size) * 100:.1f}%)")
    print(f"Parse {psp.row_num} rows in {time.perf_counter() - time0:.0f} s")

    # data/ps_libreacces/PS_LibreAcces_Personne_activite_small.txt -e
    # data/ps_libreacces/PS_LibreAcces_Personne_activite_202112020908.txt
