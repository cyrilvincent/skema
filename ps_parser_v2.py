from datetime import datetime
from typing import Dict, List, Tuple, Optional, Iterable
from sqlalchemy.orm import joinedload
from ps_parser import PSParser
from sqlentities import Context, PS, AdresseNorm, Profession, Personne, Coord, Activite
import argparse
import art
import config


class PSParserV2(PSParser):

    def __init__(self, context):
        super().__init__(context)
        self.inpps_dept: Dict[Tuple[str, str, int], Dict[Tuple[int, str, int, str], Personne]] = {}
        self.inpps_nom: Dict[Tuple[str, int], Dict[Tuple[int, str, int, str], Personne]] = {}
        self.nb_rule = 12

    # personne 1-* activite 1-* coord
    #          1-* diplome_obtenu

    def load_cache_inpp(self):
        print("Making cache level 2")
        personnes: List[Personne] = self.context.session.query(Personne) \
            .options(joinedload(Personne.activites).options(joinedload(Activite.coord_activites))) \
            .options(joinedload(Personne.diplome_obtenus)) \
            .filter(Personne.nom != '').all() # .filter((Personne.nom != '') & (Personne.prenom != '')).all()
        print(datetime.now()) #1min50 30Go vs 1min40 27Go
        for p in personnes:
            for a in p.activites:
                for c in a.coord_activites:
                    self.make_keys(p, c)

    def make_keys(self, p: Personne, c: Coord):
        if c is not None and c.cp is not None and c.cp.isnumeric():
            nom = self.normalize_string(p.nom)
            prenom = self.normalize_string(p.prenom)
            dept = self.get_dept_from_cp(c.cp)
            if dept in self.depts_int:
                key_dept = nom, prenom, dept
                voie = self.normalize_string(c.voie) if c.voie is not None else ""
                commune = self.normalize_string(c.commune) if c.commune is not None else ""
                numero = int(c.numero) if c.numero is not None and c.numero.isnumeric() else None
                if c.adresse_norm_id is not None:
                    a = self.adresse_norms_id[int(c.adresse_norm_id)]
                    voie = a.rue1
                    commune = a.commune
                    numero = a.numero
                key_dept_2 = numero, voie, int(c.cp), commune
                key_nom = nom, dept
                if key_dept not in self.inpps_dept:
                    self.inpps_dept[key_dept] = {key_dept_2: p}
                else:
                    self.inpps_dept[key_dept][key_dept_2] = p
                if key_nom not in self.inpps_nom:
                    self.inpps_nom[key_nom] = {key_dept_2: p}
                else:
                    self.inpps_nom[key_nom][key_dept_2] = p
                self.nb_ram += 1

    def match_profession_code_profession(self, profession: Profession, personne: Personne) -> bool:
        for a in personne.activites:
            for c in profession.code_professions:
                if a.code_profession_id == c.id:
                    return True
        return False

    def match_profession_diplome(self, profession: Profession, personne: Personne) -> bool:
        if len(personne.diplome_obtenus) == 0:
            return True
        for do in personne.diplome_obtenus:
            for d in profession.diplomes:
                if do.code_diplome == d.code_diplome:
                    return True
        return False

    def match_specialite(self, profession: Optional[Profession], personne: Personne) -> bool:
        if profession is None:
            return False
        res = self.match_profession_code_profession(profession, personne)
        if res:
            return self.match_profession_diplome(profession, personne)
        return False

    # nom + prenom + numero + rue1 + cp + commune
    def rule1(self, ps: PS, a: AdresseNorm, _: Optional[Profession]) -> Optional[Personne]:
        key_dept = self.normalize_string(ps.nom), self.normalize_string(ps.prenom), self.get_dept_from_cp(a.cp)
        if key_dept not in self.inpps_dept:
            return None
        dico = self.inpps_dept[key_dept]
        key_dept_2 = a.numero, a.rue1, a.cp, a.commune
        if key_dept_2 in dico:
            p = dico[key_dept_2]
            return p
        return None

    # nom + prenom + rue1 + cp + commune + specialite
    def rule2(self, ps: PS, a: AdresseNorm, profession: Optional[Profession]) -> Optional[Personne]:
        key_dept = self.normalize_string(ps.nom), self.normalize_string(ps.prenom), self.get_dept_from_cp(a.cp)
        if key_dept not in self.inpps_dept:
            return None
        dico = self.inpps_dept[key_dept]
        l = [dico[k] for k in dico.keys() if (k[1] == a.rue1 and k[2] == a.cp and k[3] == a.commune)]
        l = list(set(l))
        if profession is not None:
            l = [p for p in l if self.match_specialite(profession, p)]
        if len(l) == 1:
            return l[0]
        return None

    # nom + prenom + numero + rue1 + departement + commune + specialite
    def rule3(self, ps: PS, a: AdresseNorm, profession: Optional[Profession]) -> Optional[Personne]:
        key_dept = self.normalize_string(ps.nom), self.normalize_string(ps.prenom), self.get_dept_from_cp(a.cp)
        if key_dept not in self.inpps_dept:
            return None
        dico = self.inpps_dept[key_dept]
        l = [dico[k] for k in dico.keys() if (k[1] == a.rue1 and k[0] == a.numero and k[3] == a.commune)]
        l = list(set(l))
        if profession is not None:
            l = [p for p in l if self.match_specialite(profession, p)]
        if len(l) == 1:
            return l[0]
        return None

    # nom + numero + rue1 + cp + commune + specialite
    def rule4(self, ps: PS, a: AdresseNorm, profession: Optional[Profession]) -> Optional[Personne]:
        key_nom = self.normalize_string(ps.nom), self.get_dept_from_cp(a.cp)
        if key_nom not in self.inpps_nom:
            return None
        dico = self.inpps_nom[key_nom]
        key_dept_2 = a.numero, a.rue1, a.cp, a.commune
        if key_dept_2 in dico:
            personne = dico[key_dept_2]
            if profession is None:
                return personne
            if self.match_specialite(profession, personne):
                return personne
        return None

    # nom + prenom + rue1 + cp + commune
    def rule5(self, ps: PS, a: AdresseNorm, _: Optional[Profession]) -> Optional[Personne]:
        return self.rule2(ps, a, None)

    # nom + rue1 + cp + commune + specialite
    def rule6(self, ps: PS, a: AdresseNorm, profession: Optional[Profession]) -> Optional[Personne]:
        key_nom = self.normalize_string(ps.nom), self.get_dept_from_cp(a.cp)
        if key_nom not in self.inpps_nom:
            return None
        dico = self.inpps_nom[key_nom]
        l = [dico[k] for k in dico.keys() if (k[1] == a.rue1 and k[2] == a.cp and k[3] == a.commune)]
        l = list(set(l))
        if profession is not None:
            l = [p for p in l if self.match_specialite(profession, p)]
        if len(l) == 1:
            return l[0]
        return None

    # prenom + nom + rue1 (75%) + cp + commune + specialite
    def rule7(self, ps: PS, a: AdresseNorm, profession: Optional[Profession]) -> Optional[Personne]:
        key_dept = self.normalize_string(ps.nom), self.normalize_string(ps.prenom), self.get_dept_from_cp(a.cp)
        if key_dept not in self.inpps_dept:
            return None
        dico = self.inpps_dept[key_dept]
        dico2 = {}
        for k in dico.keys():
            if k[2] == a.cp and k[3] == a.commune:
                dico2[k] = dico[k]
        if len(list(dico2.keys())) > 0:
            personne = self.match_rue_inpp_gestalt(a.rue1, dico2)
            if profession is None or personne is None:
                return personne
            if self.match_specialite(profession, personne):
                return personne
        return None

    # prenom + nom + cp + commune + specialite
    def rule8(self, ps: PS, a: AdresseNorm, profession: Optional[Profession]) -> Optional[Personne]:
        key_dept = self.normalize_string(ps.nom), self.normalize_string(ps.prenom), self.get_dept_from_cp(a.cp)
        if key_dept not in self.inpps_dept:
            return None
        dico = self.inpps_dept[key_dept]
        l = [dico[k] for k in dico.keys() if (k[2] == a.cp and k[3] == a.commune)]
        l = list(set(l))
        if profession is not None:
            l = [p for p in l if self.match_specialite(profession, p)]
        if len(l) == 1:
            return l[0]
        return None

    # prenom + nom + (numero + rue1 + cp + commune à 75%) + specialite
    def rule9(self, ps: PS, a: AdresseNorm, profession: Optional[Profession]) -> Optional[Personne]:
        key_dept = self.normalize_string(ps.nom), self.normalize_string(ps.prenom), self.get_dept_from_cp(a.cp)
        if key_dept not in self.inpps_dept:
            return None
        dico = self.inpps_dept[key_dept]
        personne = self.match_key_inpp_gestalt(a, dico)
        if profession is None or personne is None:
            return personne
        if self.match_specialite(profession, personne):
            return personne
        return None

    # nom + cp + commune + specialite
    def rule10(self, ps: PS, a: AdresseNorm, profession: Optional[Profession]) -> Optional[Personne]:
        key_nom = self.normalize_string(ps.nom), self.get_dept_from_cp(a.cp)
        if key_nom not in self.inpps_nom:
            return None
        dico = self.inpps_nom[key_nom]
        l = [dico[k] for k in dico.keys() if (k[2] == a.cp and k[3] == a.commune)]
        l = list(set(l))
        if profession is not None:
            l = [p for p in l if self.match_specialite(profession, p)]
        if len(l) == 1:
            return l[0]
        return None

    # prenom + nom + dept + commune + specialite
    def rule11(self, ps: PS, a: AdresseNorm, profession: Optional[Profession]) -> Optional[Personne]:
        key_dept = self.normalize_string(ps.nom), self.normalize_string(ps.prenom), self.get_dept_from_cp(a.cp)
        if key_dept not in self.inpps_dept:
            return None
        dico = self.inpps_dept[key_dept]
        l = [dico[k] for k in dico.keys() if k[3] == a.commune]
        l = list(set(l))
        if profession is not None:
            l = [p for p in l if self.match_specialite(profession, p)]
        if len(l) == 1:
            return l[0]
        return None

    # prenom + nom + dept + specialite
    def rule12(self, ps: PS, a: AdresseNorm, profession: Optional[Profession]) -> Optional[Personne]:
        key_dept = self.normalize_string(ps.nom), self.normalize_string(ps.prenom), self.get_dept_from_cp(a.cp)
        if key_dept not in self.inpps_dept:
            return None
        dico = self.inpps_dept[key_dept]
        l = list(set(dico.values()))
        if profession is not None:
            l = [p for p in l if self.match_specialite(profession, p)]
        if len(l) == 1:
            return l[0]
        return None


    def match_inpp(self, ps: PS, profession: Profession, a: AdresseNorm) -> Tuple[Optional[str], int]:
        if ps.key in self.ps_merges:
            return self.ps_merges[ps.key], 0
        key_cache = self.normalize_string(ps.nom), self.normalize_string(ps.prenom), a.numero, a.rue1, a.cp, a.commune
        if key_cache in self.inpps_cache:
            return self.inpps_cache[key_cache], 0
        self.nb_unique_ps += 1

        for n in range(1, self.nb_rule + 1):
            res = self.rule(n, ps, a, profession)
            self.inpps_cache[key_cache] = res.inpp if res is not None else None
            if res is not None:
                self.nb_inpps += 1
                return res.inpp, n

        ps2 = self.create_ps_with_split_names(ps)
        if ps2 is not None:
            for n in range(1, self.nb_rule): # -1 rule
                res = self.rule(n, ps, a, profession)
                self.inpps_cache[key_cache] = res.inpp if res is not None else None
                if res is not None:
                    self.nb_inpps += 1
                    return res.inpp, n

        return None, -1

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
                if 0 < rule_nb < self.entities[e.key].rule_nb:
                    self.entities[e.key].rule_nb = rule_nb
                e = self.entities[e.key]
                self.nb_existing_entity += 1
            else:
                if rule_nb > 0:
                    e.rule_nb = rule_nb
                self.entities[e.key] = e
                self.nb_new_entity += 1
                self.context.session.add(e)
            c = self.create_update_cabinet(e, row)
            c.adresse_raw = a
            if not args.nosave:
                self.context.session.commit()
        else:
            self.nb_out_dept += 1


if __name__ == '__main__':
    art.tprint(config.name, "big")
    print("PS Parser V2")
    print("============")
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
    print(f"Database {context.db_name}: {db_size:.0f} Mb")
    out_file = None
    if args.trace:
        out_file = open("data/ps/out/out.csv", "w")
    psp = PSParserV2(context)
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
    print(f"Database {context.db_name}: {new_db_size:.0f} Mb")
    print(f"Database grows: {new_db_size - db_size:.0f} Mb ({((new_db_size - db_size) / db_size) * 100:.1f}%)")

    # PlasticienV2 [548, 6, 30, 7, 4, 0, 57, 36, 19, 1, 12, 15] 735/852: 86% NewPS 108 soit 13%
    # PlacticienV1 [645, 7, 33, 7, 0, 0, 78, 31, 25, 2, 5, 1] 834/852: 98%
    # PediatreV1 [1970, 19, 38, 41, 0, 2, 219, 59, 40, 4, 2, 8] 2402/2495: 96%
    # PediatreV2 [1327, 11, 17, 22, 4, 0, 104, 90, 18, 6, 32, 53] 1684/2495: 67%
    # +structure [1314, 11, 17, 22, 4, 0, 111, 96, 19, 7, 30, 53] 1684/2495: 67%
    # +personne  [1362, 10, 16, 23, 6, 1, 109, 100, 17, 15, 28, 53] 1740/2495: 70%
    # 2107 Matching INPP: 99750/152230: 66%
    # Matched rules: [83540, 730, 1531, 502, 869, 14, 4413, 3545, 1530, 246, 876, 1954]
    # Benjamin gagne quand même la jointure vers profession_diplome

    # data/ps/plasticien-00-00.csv -n -t -e
    # data/ps/ps-tarifs-small-00-00.csv -e
    # data/ps/ps-tarifs-21-03.csv 88% 584s 89% 701s
    # "data/UFC/ps-tarifs-UFC Santé, Pédiatres 2016 v1-3-16-00.csv"

    # select t.id, p.id, p.libelle, cp.* from tarif t
    # join profession p on t.profession_id = p.id
    # join profession_code_profession pcp ON pcp.profession_id = p.id
    # join code_profession cp on cp.id = pcp.code_profession_id
    # limit 10
    #
    # select p.id, p.inpp, cp.*, pro.id, pro.libelle from personne p
    # join exercice_pro ep on ep.personne_id = p.id
    # join code_profession cp on cp.id = ep.code_profession_id
    # join profession_code_profession pcp ON pcp.code_profession_id = cp.id
    # join profession pro on pro.id = pcp.profession_id
    # limit 10
    #
    # select p.id, p.inpp, cp.*, pro.id, pro.libelle from personne p
    # join activite a on a.personne_id = p.id
    # join code_profession cp on cp.id = a.code_profession_id
    # join profession_code_profession pcp ON pcp.code_profession_id = cp.id
    # join profession pro on pro.id = pcp.profession_id
    # limit 10
    #
    # select p.id, p.inpp, d.id, d.libelle_diplome from personne p
    # join diplome_obtenu dob on dob.personne_id = p.id
    # join diplome d on d.id = dob.diplome_id
    # join profession_diplome pd on pd.diplome_id = d.id
    # -- join profession pr on pr.id = pd.profession_id
    # limit 10 retourne rien

    # Faire tourner rpps_correspondance_parser avant
