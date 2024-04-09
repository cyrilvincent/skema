from typing import Dict, List, Tuple, Optional, Iterable
from sqlalchemy.orm import joinedload
from ps_parser import PSParser
from sqlentities import Context, PS, AdresseNorm, Profession, Personne, Coord, Activite, DiplomeObtenu
import argparse
import art
import config


class PSParserV2(PSParser):

    def __init__(self, context):
        super().__init__(context)
        self.inpps_dept: Dict[Tuple[str, str, int], Dict[Tuple[int, str, int, str], Personne]] = {}
        self.inpps_nom: Dict[Tuple[str, int], Dict[Tuple[int, str, int, str], Personne]] = {}
        self.nb_rule = 13

    # personne 1-* exercice_pro *-1 code_profession *-* profession
    #                           1-*(1) reference_ae
    #                           1-*(1) savoir_faire_obtenu *-1 diplome
    #                           *-1 categorie_pro
    #          1-* activite *-1 structure
    #                       *-1 code_profession *-* profession
    #                       1-* coord
    #          1-* diplome_obtenu *-1 diplome *-* profession (vue direct profession)
    #          1-* coord *-1 adresse_norm
    #                    *-1 activite *-1 code_profession *-* profession

    def load_cache_inpp(self):
        print("Making cache level 2")
        session = self.context.get_session()
        personnes: List[Personne] = session.query(Personne) \
            .options(joinedload(Personne.coord_personnes) \
                     .options(joinedload(Coord.adresse_norm))) \
            .options(joinedload(Personne.diplome_obtenus) \
                     .options(joinedload(DiplomeObtenu.diplome))) \
            .options(joinedload(Coord.activite)) \
            .all()
        for p in personnes:
            for c in p.coord_personnes:
                nom = self.normalize_string(p.nom)
                prenom = self.normalize_string(p.prenom)
                key_dept = nom, prenom, self.get_dept_from_cp(c.adresse_norm.cp)
                key_dept_2 = c.adresse_norm.numero, c.adresse_norm.rue1, c.adresse_norm.cp, c.adresse_norm.commune
                key_nom = nom, self.get_dept_from_cp(c.adresse_norm.cp)
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
                if d.code_diplome == do.diplome.code_diplome:
                    return True
        return False

    def match_specialite(self, profession: Optional[Profession], personne: Personne) -> bool:
        if profession is None:
            return False
        res = self.match_profession_code_profession(profession, personne)
        if res:
            return self.match_profession_diplome(profession, personne)
        return False

    def get_personne_france(self, nom: str, prenom: Optional[str]) -> Iterable[Personne]:
        if prenom is None:
            return self.context.session.query(Personne).filter(Personne.nom == nom).all()
        return self.context.session.query(Personne).filter((Personne.nom == nom) & (Personne.prenom == prenom)).all()

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

    # prenom + nom + specialite A VIRER
    def rule13(self, ps: PS, _: AdresseNorm, p: Optional[Profession]) -> Optional[Personne]:
        l = list(self.get_personne_france(self.normalize_string(ps.nom), self.normalize_string(ps.prenom)))
        if p is not None:
            l = [pa for pa in l if self.match_specialite(p, pa)]
        if len(l) == 1:
            return l[0]
        return None

    def match_inpp(self, ps: PS, p: Profession, a: AdresseNorm) -> Tuple[Optional[str], int]:
        if ps.key in self.ps_merges:
            return self.ps_merges[ps.key], 0
        key_cache = self.normalize_string(ps.nom), self.normalize_string(ps.prenom), a.numero, a.rue1, a.cp, a.commune
        if key_cache in self.inpps_cache:
            return self.inpps_cache[key_cache], 0
        self.nb_unique_ps += 1

        for n in range(1, self.nb_rule + 1):
            res = self.rule(n, ps, a, p)
            self.inpps_cache[key_cache] = res.inpp if res is not None else None
            if res is not None:
                self.nb_inpps += 1
                return res.inpp, n

        ps2 = self.create_ps_with_split_names(ps)
        if ps2 is not None:
            for n in range(1, self.nb_rule): # -1 rule
                res = self.rule(n, ps, a, p)
                self.inpps_cache[key_cache] = res.inpp if res is not None else None
                if res is not None:
                    self.nb_inpps += 1
                    return res.inpp, n

        return None, -1



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

    # Avant de refaire tourner valider vider la table ps_merge

    # data/ps/plasticien-00-00.csv -n
    # data/ps/ps-tarifs-small-00-00.csv -e
    # data/ps/ps-tarifs-21-03.csv 88% 584s 89% 701s
    # "data/UFC/ps-tarifs-UFC Santé, Pédiatres 2016 v1-3-16-00.csv" /!\ update genre

    # select pa.id, cp.* from personne_activite pa
    # join personne_activite_code_profession pacp ON pacp.personne_activite_id = pa.id
    # join code_profession cp on cp.id = pacp.code_profession_id
    # limit 10
    #
    # select pa.id, d.id, d.code_diplome, d.libelle_diplome, d.is_savoir_faire from personne_activite pa
    # join personne_activite_diplome pad ON pad.personne_activite_id = pa.id
    # join diplome d on d.id = pad.diplome_id
    # limit 10
    #
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
