from typing import Dict, List, Tuple, Optional
from sqlalchemy.orm import joinedload
from sqlentities import Context, PersonneActivite, PAAdresse, Dept, CodeProfession, Diplome, DateSource, AdresseNorm, \
    PAAdresseNormDateSource
from base_parser import BaseParser, time0
import argparse
import time
import art
import config


class PersonneActiviteParser(BaseParser):

    def __init__(self, context):
        super().__init__(context)
        self.pa_adresses: Dict[Tuple[int, str, str, str], PAAdresse] = {}
        self.code_professions: Dict[int, CodeProfession] = {}
        self.savoir_faires: Dict[str, Diplome] = {}
        self.nb_new_adresse = 0
        self.nb_new_adresse_norm = 0
        self.adresse_norms: Dict[Tuple[int, str, int, str], AdresseNorm] = {}
        self.pa_adresse_norm_date_sources: Dict[Tuple[int, int, int], PAAdresseNormDateSource] = {}

    def load_cache(self):
        print("Making cache")
        l = self.context.session.query(Dept).all()
        for d in l:
            self.depts[d.num] = d
            self.depts_int[d.id] = d
            self.nb_ram += 2
        l = self.context.session.query(CodeProfession).all()
        for c in l:
            self.code_professions[c.id] = c
            self.nb_ram += 1
        l = self.context.session.query(Diplome).filter(Diplome.is_savoir_faire == True)  # Ne pas mettre is True
        for s in l:
            self.savoir_faires[s.key] = s
            self.nb_ram += 1
        print(f"{self.nb_ram} objects in cache")
        l: List[PersonneActivite] = (self.context.session.query(PersonneActivite)
                                     .options(joinedload(PersonneActivite.diplomes))
                                     .options(joinedload(PersonneActivite.code_professions))
                                     .all())
        for e in l:
            self.entities[e.inpp] = e
            self.nb_ram += 1
        print(f"{self.nb_ram} objects in cache")
        l: List[PAAdresse] = self.context.session.query(PAAdresse)\
            .options(joinedload(PAAdresse.personne_activites)).all()
        for a in l:
            self.pa_adresses[a.key] = a
            self.nb_ram += 1
        print(f"{self.nb_ram} objects in cache")
        l: list[PAAdresseNormDateSource] = self.context.session.query(PAAdresseNormDateSource).all()
        for a in l:
            self.pa_adresse_norm_date_sources[a.key] = a
            self.nb_ram += 1
        print(f"{self.nb_ram} objects in cache")
        l: list[AdresseNorm] = self.context.session.query(AdresseNorm).all()
        for a in l:
            # a.numero, a.rue, a.cp, a.commune
            key = a.numero, a.rue1, a.cp, a.commune
            self.adresse_norms[key] = a
            self.nb_ram += 1
        print(f"{self.nb_ram} objects in cache")

    def parse_date(self, path):
        try:
            yy = int(path[-14:-12])
            mm = int(path[-12:-10])
            self.date_source = DateSource(annee=yy, mois=mm)
        except IndexError:
            print("ERROR: file must have date like this: file_YY-MM.csv")
            quit(1)

    def mapper(self, row) -> PersonneActivite:
        pa = PersonneActivite()
        try:
            pa.inpp = row["Identification nationale PP"]
            if len(row["Nom d'exercice"]) > 0:
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
            a.code_commune = self.get_nullable(row["Code commune (coord. structure)"])
        except Exception as ex:
            print(f"ERROR pa_adresse row {self.row_num}: {a}\n{ex}\n{row}")
            quit(4)
        return a

    def code_profession_mapper(self, row) -> CodeProfession:
        cp = CodeProfession()
        try:
            cp.id = int(row["Code profession"])
            cp.libelle = row["Libellé profession"]
        except Exception as ex:
            print(f"ERROR Profession row {self.row_num} {cp}\n{ex}\n{row}")
            quit(5)
        return cp

    def savoir_faire_mapper(self, row) -> Optional[Diplome]:
        d = Diplome()
        try:
            s = self.get_nullable(row["Code savoir-faire"])
            if s is None:
                return None
            d = self.savoir_faires[s]
        except Exception as ex:
            print(f"ERROR Savoir faire row {self.row_num} {d}\n{ex}\n{row}\nRun diplome_parser first")
            quit(6)
        return d

    def create_update_adresse(self, e: PersonneActivite, row):
        a = self.pa_adresse_mapper(row)
        if a is not None:
            if a.key in self.pa_adresses:
                code_commune = a.code_commune
                a = self.pa_adresses[a.key]
                if code_commune is not None and a.code_commune != code_commune:
                    a.code_commune = code_commune
            else:
                self.nb_new_adresse += 1
                self.pa_adresses[a.key] = a
            keys = [a.key for a in e.pa_adresses]
            if a.key not in keys:
                e.pa_adresses.append(a)
            self.create_update_adresse_norm(e, a)

    def create_update_code_profession(self, e: PersonneActivite, row):
        c = self.code_profession_mapper(row)
        if c is not None:
            if c.id in self.code_professions:
                c = self.code_professions[c.id]
            else:
                self.code_professions[c.id] = c
            if c not in e.code_professions:
                e.code_professions.append(c)

    def create_update_adresse_norm(self, e: PersonneActivite, a: PAAdresse):
        key = a.numero, a.rue, a.cp, a.commune
        if key not in self.adresse_norms:
            norm = AdresseNorm()
            norm.numero = a.numero
            norm.rue1 = a.rue
            norm.cp = a.cp
            norm.commune = a.commune
            norm.dept = a.dept
            self.adresse_norms[key] = norm
            self.nb_new_adresse_norm += 1
            pa_norm_datesource = PAAdresseNormDateSource()
            pa_norm_datesource.adresse_norm = norm
            pa_norm_datesource.date_source = self.date_source
            e.pa_adresse_norm_date_sources.append(pa_norm_datesource)
        else:
            norm = self.adresse_norms[key]
            key = e.id, norm.id, self.date_source.id
            if key not in self.pa_adresse_norm_date_sources or e.id == 0:
                pa_norm_datesource = PAAdresseNormDateSource()
                pa_norm_datesource.adresse_norm = norm
                pa_norm_datesource.date_source = self.date_source
                e.pa_adresse_norm_date_sources.append(pa_norm_datesource)
                if e.id != 0:
                    self.pa_adresse_norm_date_sources[key] = pa_norm_datesource

    def add_savoir_faire(self, e: PersonneActivite, row):
        s = self.savoir_faire_mapper(row)
        if s is not None:
            if s not in e.diplomes:
                e.diplomes.append(s)

    def parse_row(self, row):
        e = self.mapper(row)
        if e.inpp in self.entities:
            e = self.entities[e.inpp]
        else:
            self.nb_new_entity += 1
            self.entities[e.inpp] = e
            self.context.session.add(e)
        self.create_update_adresse(e, row)
        self.create_update_code_profession(e, row)
        self.add_savoir_faire(e, row)
        self.context.session.commit()

    def load(self, path: str):
        super().load(path, delimiter='|', encoding="UTF-8", header=True)


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
    print(f"Database {context.db_name}: {db_size:.0f} MB")
    psp = PersonneActiviteParser(context)
    psp.load(args.path)
    print(f"New personne: {psp.nb_new_entity}")
    print(f"New adresse: {psp.nb_new_adresse}")
    print(f"New adresse norm: {psp.nb_new_adresse_norm}")
    new_db_size = context.db_size()
    print(f"Database {context.db_name}: {new_db_size:.0f} MB")
    print(f"Database grows: {new_db_size - db_size:.0f} MB ({((new_db_size - db_size) / db_size) * 100:.1f}%)")
    print(f"Parse {psp.row_num} rows in {time.perf_counter() - time0:.0f} s")

    # data/ps_libreacces/PS_LibreAcces_Personne_activite_small.txt -e
    # data/ps_libreacces/PS_LibreAcces_Personne_activite_202010071006.txt
