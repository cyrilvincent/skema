import difflib
from typing import Dict, List, Tuple, Optional, Set
from sqlalchemy.orm import joinedload
from sqlentities import Context, Cabinet, PS, AdresseRaw, AdresseNorm, PSCabinetDateSource, PAAdresse, PSMerge, \
    Profession, PersonneActivite
from base_parser import BaseParser
import argparse
import art
import config


class PSParser(BaseParser):

    def __init__(self, context):
        super().__init__(context)
        self.nb_cabinet = 0
        self.nb_inpps = 0
        self.nb_unique_ps = 0
        self.cabinets: Dict[str, Cabinet] = {}
        self.inpps_dept: Dict[Tuple[str, str, int], Dict[Tuple[int, str, int, str], PersonneActivite]] = {}
        #self.inpps_france: Dict[Tuple[str, str], Set[PersonneActivite]] = {}
        self.inpps_nom: Dict[Tuple[str, int], Dict[Tuple[int, str, int, str], PersonneActivite]] = {}
        self.inpps_cache: Dict[Tuple[str, str, int, str, int, str], Optional[str]] = {}
        self.ps_merges: Dict[str, str] = {}
        self.professions: Dict[int, Profession] = {}
        # self.personne_activites: Dict[str, PersonneActivite] = {} Peut être faut il stocker PErsonneActivite au lieu de INPP dans les précédent dico, ce dico serait alors inutile pour match_specialite
        self.nb_rule = 20
        self.rules: List[int] = [0 for _ in range(self.nb_rule)]

    def load_cache(self):
        super().load_cache()
        l: List[PS] = self.context.session.query(PS) \
            .options(joinedload(PS.ps_cabinet_date_sources).joinedload(PSCabinetDateSource.cabinet)).all()
        for e in l:
            self.entities[e.key] = e
            self.nb_ram += 1
        l: List[Cabinet] = self.context.session.query(Cabinet).all()
        for c in l:
            self.cabinets[c.key] = c
            self.nb_ram += 1
        l: List[PSMerge] = self.context.session.query(PSMerge).all()
        for p in l:
            self.ps_merges[p.key] = p.inpp
            self.nb_ram += 1
        l: List[Profession] = self.context.session.query(Profession) \
            .options(joinedload(Profession.diplomes)).options(joinedload(Profession.code_professions)).all()
        for p in l:
            self.professions[p.id] = p
            self.nb_ram += 1
        print(f"{self.nb_ram} objects in cache")
        self.load_cache_inpp()
        print(f"{self.nb_ram} objects in cache")

    def load_cache_inpp(self):
        print("Making cache level 2")
        session = self.context.get_session()
        pa_adresses = session.query(PAAdresse) \
            .options(joinedload(PAAdresse.personne_activites)\
                .options(joinedload(PersonneActivite.code_professions))
                .options(joinedload(PersonneActivite.diplomes)))\
            .all()
        for a in pa_adresses:
            for pa in a.personne_activites:
                nom = self.normalize_string(pa.nom)
                key_dept = nom, pa.prenom, self.get_dept_from_cp(a.cp)
                key_dept_2 = a.numero, a.rue, a.cp, a.commune
                key_france = nom, pa.prenom
                key_nom = nom, self.get_dept_from_cp(a.cp)
                if key_dept not in self.inpps_dept:
                    self.inpps_dept[key_dept] = {key_dept_2: pa}
                else:
                    self.inpps_dept[key_dept][key_dept_2] = pa
                # if key_france not in self.inpps_france:
                #     self.inpps_france[key_france] = {pa}
                # else:
                #     self.inpps_france[key_france].add(pa)
                if key_nom not in self.inpps_nom:
                    self.inpps_nom[key_nom] = {key_dept_2: pa}
                else:
                    self.inpps_nom[key_nom][key_dept_2] = pa
                self.nb_ram += 1
            session.expunge(a)
        print(f"{self.nb_ram} objects in cache")
        # self.load_cache_inpp_3()

    # def load_cache_inpp_3(self):
    #     print("Making cache level 3")
    #     session = self.context.get_session()
    #     personne_activites = session.query(PersonneActivite) \
    #         .options(joinedload(PersonneActivite.code_professions)).options(joinedload(PersonneActivite.diplomes)).all()
    #     for p in personne_activites:
    #         self.personne_activites[p.inpp] = p
    #         self.nb_ram += 1

    def mapper(self, row) -> PS:
        ps = PS()
        try:
            ps.genre = self.get_nullable(row[0])
            ps.nom = row[1]
            ps.prenom = row[2]
            ps.key = f"{ps.nom}_{ps.prenom}_{row[7]}".replace(" ", "_")[:255]
            ps.has_inpp = False
        except Exception as ex:
            print(f"ERROR PS row {self.row_num} {ps}\n{ex}")
            quit(1)
        return ps

    def profession_mapper(self, row) -> Optional[Profession]:
        p = None
        try:
            id = self.get_nullable_int(row[10])
            p = self.professions[id]
        except Exception as ex:
            print(f"ERROR PS row {self.row_num} {p}\n{ex}")
            quit(3)
        return p

    def cabinet_mapper(self, row) -> Cabinet:
        c = Cabinet()
        try:
            c.nom = f"{row[1]} {row[2]}" if row[3] == '' else row[3]
            c.telephone = self.get_nullable(row[9])
            c.key = f"{c.nom}_{row[7]}_{row[5]}".replace(" ", "_")[:255]
        except Exception as ex:
            print(f"ERROR cabinet row {self.row_num} {c}\n{ex}")
            quit(2)
        return c

    def create_update_cabinet(self, e: PS, row) -> Cabinet:
        c = self.cabinet_mapper(row)
        if c.key in self.cabinets:
            c = self.cabinets[c.key]
        else:
            self.nb_cabinet += 1
            self.cabinets[c.key] = c
        keys = [pcds.key for pcds in e.ps_cabinet_date_sources]
        if (e.id, c.id, self.date_source.id) not in keys:
            pcds = PSCabinetDateSource()
            pcds.date_source = self.date_source
            pcds.cabinet = c
            e.ps_cabinet_date_sources.append(pcds)
        return c

    def adresse_raw_mapper(self, row) -> AdresseRaw:
        a = AdresseRaw()
        try:
            a.adresse2 = self.get_nullable(row[4])
            a.adresse3 = self.get_nullable(row[5])
            a.adresse4 = self.get_nullable(row[6])
            a.cp = int(row[7])
            a.commune = row[8]
            a.dept = self.depts_int[self.get_dept_from_cp(a.cp)]
        except Exception as ex:
            print(f"ERROR raw row {self.row_num} {a}\n{ex}")
            quit(4)
        return a

    def create_update_adresse_raw(self, row) -> AdresseRaw:
        a = self.adresse_raw_mapper(row)
        if a.key in self.adresse_raws:
            a = self.adresse_raws[a.key]
        else:
            self.nb_new_adresse += 1
            self.adresse_raws[a.key] = a
        # c.adresse_raw = a
        return a

    def choose_best_rue(self, a: AdresseRaw) -> int:
        if a.adresse2 is None:
            return 3
        l = ["CHEMIN", "AVENUE", "PLACE", "BOULEVARD", "IMPASSE", "ROUTE", "RUE"]
        if a.adresse3 is not None:
            num, rue = self.split_num(a.adresse3)
            if num is not None:
                return 3
            rue = self.normalize_street(rue)
            for w in l:
                if w in rue:
                    return 3
        if a.adresse2 is not None:
            num, rue = self.split_num(a.adresse2)
            if num is not None:
                return 2
            rue = self.normalize_street(rue)
            for w in l:
                if w in rue:
                    return 2
        return 3

    def normalize(self, a: AdresseRaw) -> AdresseNorm:
        n = AdresseNorm()
        n.cp = a.cp
        n.commune = self.normalize_commune(a.commune)
        n.dept = a.dept
        best = self.choose_best_rue(a)
        if best == 3 and a.adresse3 is not None:
            n.numero, n.rue1 = self.split_num(a.adresse3)
            n.rue1 = self.normalize_street(n.rue1)
            n.rue2 = self.normalize_street(a.adresse2) if a.adresse2 is not None else None
        elif best == 2 and a.adresse2 is not None:
            n.numero, n.rue1 = self.split_num(a.adresse2)
            n.rue1 = self.normalize_street(n.rue1)
            n.rue2 = self.normalize_street(a.adresse3) if a.adresse3 is not None else None
        if n.rue1 == '':
            n.rue1 = None
        if n.rue1 is None and n.numero is not None:
            n.numero = None
        return n

    def convert_key_to_rue_string(self, key: Tuple[Optional[int], Optional[str], int, str]) -> str:
        s = f"{key[2]} {key[3]}"
        if key[1] is not None:
            s = f"{key[1]} {s}"
        if key[0] is not None:
            s = f"{key[0]} {s}"
        return s

    def gestalt(self, s1: str, s2: str):
        if s1 is None or s2 is None:
            return 0
        sm = difflib.SequenceMatcher(None, s1, s2)
        return sm.ratio()

    def match_key_inpp_gestalt(self, a: AdresseNorm,
                           dico: Dict[Tuple[int, str, int, str], PersonneActivite]) -> Optional[PersonneActivite]:
        s = self.convert_key_to_rue_string((a.numero, a.rue1, a.cp, a.commune))
        max = 0
        inpp = None
        for k in dico.keys():
            s2 = self.convert_key_to_rue_string(k)
            score = self.gestalt(s, s2)
            if score > max:
                max = score
                inpp = dico[k]
        if max > 0.75:
            return inpp
        return None

    def match_rue_inpp_gestalt(self, rue: str,
                               dico: Dict[Tuple[int, str, int, str], PersonneActivite]) -> Optional[PersonneActivite]:
        max = 0
        pa = None
        for k in dico.keys():
            score = self.gestalt(rue, k[1])
            if score > max:
                max = score
                pa = dico[k]
        if max > 0.75:
            return pa
        return None

    def match_rue(self, rue1: Optional[str], rue2: Optional[str]):
        if self.date_source.id == 1206 or self.date_source.id == 1306:  # SanteSpecialite
            return False
        if rue1 is None or rue2 is None:
            return True
        if rue1 == rue2:
            return True
        if rue1 is not None and rue2 is not None:
            if rue1.startswith(rue2) or rue2.startswith(rue1):
                return True
        return False

    def match_profession_code_profession(self, profession: Profession, pa: PersonneActivite) -> bool:
        for c in pa.code_professions:
            for c2 in profession.code_professions:
                if c.id == c2.id:
                    return True
        return False

    def match_profession_savoir_faire(self, profession: Profession, pa: PersonneActivite) -> bool:
        if len(pa.diplomes) == 0:
            return True
        for d in pa.diplomes:
            for d2 in profession.diplomes:
                if d.code_diplome == d2.code_diplome:
                    return True
        return False

    def match_specialite(self, p: Optional[Profession], pa: PersonneActivite) -> bool:
        if p is None:
            return False
        res = self.match_profession_code_profession(p, pa)
        if res:
            return self.match_profession_savoir_faire(p, pa)
        return False

    def get_pa_france(self, nom: str, prenom: Optional[str]) -> Optional[PersonneActivite]:
        if prenom is None:
            return self.context.session.query(PersonneActivite).filter(PersonneActivite.nom == nom).all()
        return self.context.session.query(PersonneActivite).\
            filter((PersonneActivite.nom == nom) & (PersonneActivite.prenom == prenom)).all()

    def create_ps_with_split_names(self, ps: PS) -> Optional[PS]:
        if " " in ps.nom or " " in ps.prenom:
            nom = ps.nom
            if " " in ps.nom:
                nom = str(ps.nom).split(" ")[0]
                if len(nom) < 4:
                    return None
            prenom = ps.prenom
            if " " in ps.prenom:
                prenom = str(ps.prenom).split(" ")[0]
                if len(prenom) < 4:
                    return None
            res = PS()
            res.nom = nom
            res.prenom = prenom
            return res
        return None

    def rule(self, n: int, ps: PS, a: AdresseNorm, p: Profession) -> Optional[PersonneActivite]:
        fn = self.__getattribute__(f"rule{n}")
        res = fn(ps, a, p)
        return res

    def rule1(self, ps: PS, a: AdresseNorm, _: Optional[Profession]) -> Optional[PersonneActivite]:
        key_dept = self.normalize_string(ps.nom), ps.prenom, self.get_dept_from_cp(a.cp)
        if key_dept not in self.inpps_dept:
            return None
        dico = self.inpps_dept[key_dept]
        key_dept_2 = a.numero, a.rue1, a.cp, a.commune
        if key_dept_2 in dico:
            pa = dico[key_dept_2]
            return pa
        return None

    def rule2(self, ps: PS, a: AdresseNorm, p: Optional[Profession]) -> Optional[PersonneActivite]:
        key_dept = self.normalize_string(ps.nom), ps.prenom, self.get_dept_from_cp(a.cp)
        if key_dept not in self.inpps_dept:
            return None
        dico = self.inpps_dept[key_dept]
        l = [dico[k] for k in dico.keys() if (k[1] == a.rue1 and k[2] == a.cp and k[3] == a.commune)]
        l = list(set(l))
        if p is not None:
            l = [pa for pa in l if self.match_specialite(p, pa)]
        if len(l) == 1:
            return l[0]
        return None

    def rule3(self, ps: PS, a: AdresseNorm, p: Optional[Profession]) -> Optional[PersonneActivite]:
        key_dept = self.normalize_string(ps.nom), ps.prenom, self.get_dept_from_cp(a.cp)
        if key_dept not in self.inpps_dept:
            return None
        dico = self.inpps_dept[key_dept]
        l = [dico[k] for k in dico.keys() if (k[1] == a.rue1 and k[0] == a.numero and k[3] == a.commune)]
        l = list(set(l))
        if p is not None:
            l = [pa for pa in l if self.match_specialite(p, pa)]
        if len(l) == 1:
            return l[0]
        return None

    def rule4(self, ps: PS, a: AdresseNorm, p: Optional[Profession]) -> Optional[PersonneActivite]:
        key_nom = self.normalize_string(ps.nom), self.get_dept_from_cp(a.cp)
        if key_nom not in self.inpps_nom:
            return None
        dico = self.inpps_nom[key_nom]
        key_dept_2 = a.numero, a.rue1, a.cp, a.commune
        if key_dept_2 in dico:
            pa = dico[key_dept_2]
            if p is None:
                return pa
            if self.match_specialite(p, pa):
                return pa
        return None

    def rule5(self, ps: PS, a: AdresseNorm, _: Optional[Profession]) -> Optional[PersonneActivite]:
        return self.rule2(ps, a, None)

    def rule6(self, ps: PS, a: AdresseNorm, p: Optional[Profession]) -> Optional[PersonneActivite]:
        key_nom = self.normalize_string(ps.nom), self.get_dept_from_cp(a.cp)
        if key_nom not in self.inpps_nom:
            return None
        dico = self.inpps_nom[key_nom]
        l = [dico[k] for k in dico.keys() if (k[1] == a.rue1 and k[2] == a.cp and k[3] == a.commune)]
        l = list(set(l))
        if p is not None:
            l = [pa for pa in l if self.match_specialite(p, pa)]
        if len(l) == 1:
            return l[0]
        return None

    def rule7(self, ps: PS, a: AdresseNorm, p: Optional[Profession]) -> Optional[PersonneActivite]:
        key_dept = self.normalize_string(ps.nom), ps.prenom, self.get_dept_from_cp(a.cp)
        if key_dept not in self.inpps_dept:
            return None
        dico = self.inpps_dept[key_dept]
        dico2 = {}
        for k in dico.keys():
            if k[2] == a.cp and k[3] == a.commune:
                dico2[k] = dico[k]
        if len(list(dico2.keys())) > 0:
            pa = self.match_rue_inpp_gestalt(a.rue1, dico2)
            if p is None or pa is None:
                return pa
            if self.match_specialite(p, pa):
                return pa
        return None

    def rule8(self, ps: PS, a: AdresseNorm, p: Optional[Profession]) -> Optional[PersonneActivite]:
        key_dept = self.normalize_string(ps.nom), ps.prenom, self.get_dept_from_cp(a.cp)
        if key_dept not in self.inpps_dept:
            return None
        dico = self.inpps_dept[key_dept]
        l = [dico[k] for k in dico.keys() if (k[2] == a.cp and k[3] == a.commune)]
        l = list(set(l))
        if p is not None:
            l = [pa for pa in l if self.match_specialite(p, pa)]
        if len(l) == 1:
            return l[0]
        return None

    def rule9(self, ps: PS, a: AdresseNorm, p: Optional[Profession]) -> Optional[PersonneActivite]:
        key_dept = self.normalize_string(ps.nom), ps.prenom, self.get_dept_from_cp(a.cp)
        if key_dept not in self.inpps_dept:
            return None
        dico = self.inpps_dept[key_dept]
        pa = self.match_key_inpp_gestalt(a, dico)
        if p is None or pa is None:
            return pa
        if self.match_specialite(p, pa):
            return pa
        return None

    def rule10(self, ps: PS, a: AdresseNorm, _: Optional[Profession]) -> Optional[PersonneActivite]:
        return self.rule7(ps, a, None)

    def rule11(self, ps: PS, a: AdresseNorm, _: Optional[Profession]) -> Optional[PersonneActivite]:
        return self.rule8(ps, a, None)

    def rule12(self, ps: PS, a: AdresseNorm, p: Optional[Profession]) -> Optional[PersonneActivite]:
        key_nom = self.normalize_string(ps.nom), self.get_dept_from_cp(a.cp)
        if key_nom not in self.inpps_nom:
            return None
        dico = self.inpps_nom[key_nom]
        l = [dico[k] for k in dico.keys() if (k[2] == a.cp and k[3] == a.commune)]
        l = list(set(l))
        if p is not None:
            l = [pa for pa in l if self.match_specialite(p, pa)]
        if len(l) == 1:
            return l[0]
        return None

    def rule13(self, ps: PS, a: AdresseNorm, p: Optional[Profession]) -> Optional[PersonneActivite]:
        key_dept = self.normalize_string(ps.nom), ps.prenom, self.get_dept_from_cp(a.cp)
        if key_dept not in self.inpps_dept:
            return None
        dico = self.inpps_dept[key_dept]
        l = [dico[k] for k in dico.keys() if k[3] == a.commune]
        l = list(set(l))
        if p is not None:
            l = [pa for pa in l if self.match_specialite(p, pa)]
        if len(l) == 1:
            return l[0]
        return None

    def rule14(self, ps: PS, a: AdresseNorm, p: Optional[Profession]) -> Optional[PersonneActivite]:
        key_dept = self.normalize_string(ps.nom), ps.prenom, self.get_dept_from_cp(a.cp)
        if key_dept not in self.inpps_dept:
            return None
        dico = self.inpps_dept[key_dept]
        l = list(set(dico.values()))
        if p is not None:
            l = [pa for pa in l if self.match_specialite(p, pa)]
        if len(l) == 1:
            return l[0]
        return None

    def rule15(self, ps: PS, a: AdresseNorm, _: Optional[Profession]) -> Optional[PersonneActivite]:
        return self.rule14(ps, a, None)

    def rule16(self, ps: PS, _: AdresseNorm, p: Optional[Profession]) -> Optional[PersonneActivite]:
        l = list(self.get_pa_france(self.normalize_string(ps.nom), ps.prenom))
        if p is not None:
            l = [pa for pa in l if self.match_specialite(p, pa)]
        if len(l) == 1:
            return l[0]
        return None

    def rule17(self, ps: PS, a: AdresseNorm, _: Optional[Profession]) -> Optional[PersonneActivite]:
        return self.rule16(ps, a, None)

    def rule18(self, ps: PS, _: AdresseNorm, p: Optional[Profession]) -> Optional[PersonneActivite]:
        l = list(set(self.get_pa_france(self.normalize_string(ps.nom), None)))
        if p is not None:
            l = [pa for pa in l if self.match_specialite(p, pa)]
        if len(l) == 1:
            return l[0]
        return None

    def rule19(self, ps: PS, a: AdresseNorm, _: Optional[Profession]) -> Optional[PersonneActivite]:
        return self.rule18(ps, a, None)

    def rule20(self, _: PS, __: AdresseNorm, ___: Optional[Profession]) -> Optional[PersonneActivite]:
        return None

    def match_inpp(self, ps: PS, p: Profession, a: AdresseNorm) -> Tuple[Optional[str], int]:
        if ps.key in self.ps_merges:
            return self.ps_merges[ps.key], 0
        key_cache = self.normalize_string(ps.nom), ps.prenom, a.numero, a.rue1, a.cp, a.commune
        print(key_cache)
        if key_cache in self.inpps_cache:
            return self.inpps_cache[key_cache], 0
        self.nb_unique_ps += 1

        for n in range(1, self.nb_rule + 1):
            res = self.rule(n, ps, a, p)
            self.inpps_cache[key_cache] = res.inpp if res is not None else None
            if res is not None:
                print(f"Match {n}: {res.inpp}")
                self.nb_inpps += 1
                return res.inpp, n

        ps = self.create_ps_with_split_names(ps)
        if ps is not None:
            self.nb_unique_ps -= 1
            inpp, _ = self.match_inpp(ps, p, a)
            if inpp is not None:
                return inpp, 20

        return None, -1

    def create_update_norm(self, a: AdresseRaw) -> AdresseNorm:
        n = self.normalize(a)
        if n.key in self.adresse_norms:
            n = self.adresse_norms[n.key]
        else:
            self.adresse_norms[n.key] = n
            self.nb_new_norm += 1
        if a.adresse_norm is None:
            a.adresse_norm = n
        else:
            same = a.adresse_norm.equals(n)
            if not same:
                a.adresse_norm = n
        return n

    def parse_row(self, row):
        dept = self.get_dept_from_cp(row[7])
        if dept in self.depts_int:
            if args.trace:
                out_file.write(",".join([str(x.strip()) for x in row]))
            e = self.mapper(row)
            a = self.create_update_adresse_raw(row)
            n = self.create_update_norm(a)
            p = self.profession_mapper(row)
            inpp, rule_nb = self.match_inpp(e, p, n)
            if args.trace:
                out_file.write(f",{inpp},{rule_nb}\n")
            if inpp is not None:
                e.key = inpp
                e.has_inpp = True
                if rule_nb > 0:
                    self.rules[rule_nb - 1] += 1
            if e.key in self.entities:
                same = e.equals(self.entities[e.key])
                if not same:
                    if e.genre is not None:
                        self.entities[e.key].genre = e.genre
                        self.nb_update_entity += 1
                e = self.entities[e.key]
            else:
                self.entities[e.key] = e
                self.nb_new_entity += 1
                self.context.session.add(e)
            c = self.create_update_cabinet(e, row)
            c.adresse_raw = a
            if not args.nosave:
                self.context.session.commit()


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
    parser.add_argument("-n", "--nosave", help="No save", action="store_true")
    parser.add_argument("-t", "--trace", help="Trace in out.csv file", action="store_true")
    args = parser.parse_args()
    context = Context()
    context.create(echo=args.echo, expire_on_commit=False)
    db_size = context.db_size()
    print(f"Database {context.db_name}: {db_size:.0f} Mo")
    out_file = None
    if args.trace:
        out_file = open("data/ps/out/out.csv", "w")
    psp = PSParser(context)
    psp.load(args.path, encoding=None)
    if args.trace:
        out_file.close()
    print(f"New PS: {psp.nb_new_entity}")
    print(f"Update PS: {psp.nb_update_entity}")
    print(f"New cabinet: {psp.nb_cabinet}")
    print(f"New adresse: {psp.nb_new_adresse}")
    print(f"New adresse normalized: {psp.nb_new_norm}")
    print(f"Matching INPP: {psp.nb_inpps}/{psp.nb_unique_ps}: {(psp.nb_inpps / psp.nb_unique_ps) * 100:.0f}%")
    print(f"Matched rules: {psp.rules}")
    new_db_size = context.db_size()
    print(f"Database {context.db_name}: {new_db_size:.0f} Mo")
    print(f"Database grows: {new_db_size - db_size:.0f} Mo ({((new_db_size - db_size) / db_size) * 100:.1f}%)")

    # Avant de refaire tourner valider vider la table ps_merge

    # data/ps/plasticien-00-00.csv -n
    # data/ps/ps-tarifs-small-00-00.csv -e
    # data/ps/ps-tarifs-21-03.csv 88% 584s 89% 701s
    # "data/UFC/ps-tarifs-UFC Santé, Pédiatres 2016 v1-3-16-00.csv" /!\ update genre

    # select cast(data1.count1 as float)/ cast(data2.count2 as float)
    # from
    # (select count(*) as count1 from ps where has_inpp is true) data1,
    # (select count(*) as count2 from ps) data2

    # select cast(data1.count1 as float)/ cast(data2.count2 as float)
    # from
    # (select count(*) as count1 from ps, ps_cabinet_date_source
    #  	where ps_cabinet_date_source.ps_id = ps.id
    #  	and ps_cabinet_date_source.date_source_id = 2112
    #  	and has_inpp is true) data1,
    # (select count(*) as count2 from ps, ps_cabinet_date_source
    # 	where ps_cabinet_date_source.ps_id = ps.id
    #  	and ps_cabinet_date_source.date_source_id = 2112
    # ) data2
