from typing import Dict, Optional, List, Tuple, Set, Iterable
from sqlalchemy.orm import joinedload
from sqlentities import Context, Cedex, BAN, Dept, AdresseNorm
import argparse
import time
import art
import config
import difflib
import numpy as np

time0 = time.perf_counter()


class BANMatcher:

    def __init__(self, depts: List[int], force=False, ban_echo=False, sa_echo=False):
        self.context = Context()
        self.context.create_engine(echo=sa_echo)
        self.session = self.context.get_session(False)
        self.depts = depts
        self.force = force
        self.echo = ban_echo
        self.row_num = 0
        self.total_nb_norm = 0
        self.dept = 0
        self.cedexs: Dict[int, int] = {}
        self.cps: Dict[int, Set[str]] = {}
        self.cp_communes: Dict[Tuple[int, str], Set[str]] = {}
        self.cp_commune_rues: Dict[Tuple[int, str, str], List[BAN]] = {}
        self.communes: Dict[str, Set[int]] = {}
        self.commune_rue_numeros: Dict[Tuple[str, str, Optional[int]], BAN] = {}
        self.cp_rue_numeros: Dict[Tuple[int, str, Optional[int]], BAN] = {}
        self.commune_rues: Dict[Tuple[str, str], BAN] = {}
        self.scores = []
        self.total_scores = []
        self.nb_error = 0
        self.filter_no_force = AdresseNorm.ban_score.is_(None) & AdresseNorm.score.is_(None)
        if self.depts is None:
            self.depts = list(range(1, 20)) + list(range(21, 96)) + [201, 202]

    @property
    def score(self):
        return sum(self.scores) / len(self.scores)

    def make_cache0(self):
        print(f"Make cache level 0")
        l: List[Cedex] = self.session.query(Cedex).all()
        for c in l:
            if c.cp is not None:
                self.cedexs[c.cedex] = c.cp

    def make_cache1(self, d: int):
        print(f"Make cache level 1 for dept {d}")
        self.session = self.context.get_session(False)
        self.dept = self.session.query(Dept).options(joinedload(Dept.bans)).get(d)
        print(f"Make cache levels 2 and 3 for dept {d}")
        self.cps = {}
        self.cp_communes = {}
        self.cp_commune_rues = {}
        self.communes = {}
        self.commune_rue_numeros = {}
        self.cp_rue_numeros = {}
        self.commune_rues = {}
        self.scores = []
        for ban in self.dept.bans:
            if ban.code_postal not in self.cps:
                self.cps[ban.code_postal] = set()
            if ban.nom_commune not in self.cps[ban.code_postal]:
                self.cps[ban.code_postal].add(ban.nom_commune)
            if ban.nom_ancienne_commune is not None and ban.nom_ancienne_commune not in self.cps[ban.code_postal]:
                self.cps[ban.code_postal].add(ban.nom_ancienne_commune)
            self.make_cache23(ban.code_postal, ban.nom_commune, ban.nom_voie, ban)
            self.make_cache23(ban.code_postal, ban.nom_commune, ban.libelle_acheminement, ban)
            self.make_cache23(ban.code_postal, ban.nom_commune, ban.nom_afnor, ban)
            self.make_cache23(ban.code_postal, ban.nom_ancienne_commune, ban.nom_voie, ban)
            self.make_cache23(ban.code_postal, ban.nom_ancienne_commune, ban.libelle_acheminement, ban)
            self.make_cache23(ban.code_postal, ban.nom_ancienne_commune, ban.nom_afnor, ban)
            if ban.nom_commune not in self.communes:
                self.communes[ban.nom_commune] = set()
            if ban.code_postal not in self.communes[ban.nom_commune]:
                self.communes[ban.nom_commune].add(ban.code_postal)
            self.commune_rue_numeros[ban.nom_commune, ban.nom_voie, ban.numero] = ban
            self.cp_rue_numeros[ban.code_postal, ban.nom_voie, ban.numero] = ban
            self.commune_rues[ban.nom_commune, ban.nom_voie] = ban

    def make_cache23(self, cp, commune, rue, ban):
        if commune is not None and rue is not None:
            key = cp, commune
            if key not in self.cp_communes:
                self.cp_communes[key] = set()
            if rue not in self.cp_communes[key]:
                self.cp_communes[key].add(rue)
            key = cp, commune, rue
            if key not in self.cp_commune_rues:
                self.cp_commune_rues[key] = []
            self.cp_commune_rues[key].append(ban)

    def stats(self):
        ban = self.session.query(BAN).count()
        print(f"Found {ban} BAN")
        norm = self.session.query(AdresseNorm).count()
        print(f"Found {norm} adresses")
        if self.force:
            self.total_nb_norm = norm
        else:
            self.total_nb_norm = self.session.query(AdresseNorm).filter(self.filter_no_force).count()
        print(f"Found {self.total_nb_norm} adresses to match")
        if self.total_nb_norm == 0:
            print("Everything is up to date")
            quit(0)

    def find_nearest_less_cp(self, cp: int) -> int:
        min = 99999
        res = None
        for k in self.cps:
            if res is None:
                res = k
            dif = cp - k
            if 0 <= dif < min:
                min = dif
                res = k
        return res

    def match_cp(self, cp: int) -> Tuple[int, float]:
        if cp in self.cps:
            return cp, 1
        elif 1000 > cp >= 97000:
            return 0, 0
        elif 75100 <= cp < 75200:
            cp, score = self.match_cp(cp - 100)
            return cp, score * 0.9
        elif cp == 75000:
            return 75001, 0.1
        elif cp in self.cedexs:
            cp, score = self.match_cp(self.cedexs[cp])
            return cp, score * 0.95
        else:
            res = self.find_nearest_less_cp(cp)
            return res, 0.5

    def denormalize(self, street: str) -> str:
        street = street.replace("CHEMIN", "CH").replace("AVENUE", "AV").replace("PLACE", "PL")
        street = street.replace("BOULEVARD", "BD").replace("ROUTE", "RT").replace("IMPASSE", "IMP")
        street = street.replace("SAINT", "ST")
        return street

    def gestalt(self, s1: str, s2: str):
        sm = difflib.SequenceMatcher(None, s1, s2)
        return sm.ratio()

    def gestalts(self, s: str, l: Iterable[str]):
        if s == "" or s is None:
            return None, 0
        max = -1
        res = None
        s = self.denormalize(s)
        for item in l:
            if item != "":
                if s == item:
                    return item, 1
                elif item.startswith(s) or s.startswith(item):
                    return item, 0.99
                deno = self.denormalize(item)
                ratio = self.gestalt(s, deno)
                if ratio > max:
                    max = ratio
                    res = item
                if max < 0.5 and s in deno:
                    max = 0.5
        return res, max

    def match_commune(self, commune: str, communes: Set[str]) -> Tuple[str, float]:
        if commune in communes:
            return commune, 1
        elif len(communes) == 1:
            return list(communes)[0], 0.95
        else:
            res, score = self.gestalts(commune, communes)
            return res, score

    def get_cp_by_commune(self, commune: str) -> Tuple[int, str, float]:
        if commune in self.communes:
            l = list(self.communes[commune])
            return l[0], commune, 1 / len(l)
        return 0, commune, 0

    def match_rue(self, commune: str, rue1: Optional[str], rue2: Optional[str], cp: int) -> Tuple[str, float]:
        if rue1 is None:
            rue1 = "MAIRIE EGLISE"
        # rue1 ??= "MAIRIE EGLISE"
        if (cp, commune, rue1) in self.cp_commune_rues:
            return rue1, 1
        if rue2 is not None and (cp, commune, rue2) in self.cp_commune_rues:
            return rue2, 0.95
        rues = self.cp_communes[(cp, commune)]
        res, score = self.gestalts(rue1, rues)
        if score > 0.8:
            return res, score
        if rue2 is not None:
            res2, score2 = self.gestalts(rue2, rues)
            if score2 > score:
                res, score = res2, score2
        # if self.echo and score < 0.7:
        #     print(f"WARNING RUE {cp} {commune} {rue1}=>{res} @{int(score * 100)}%")
        return res, score

    def match_numero(self, cp: int, commune: str, rue: str, num: Optional[int]) \
            -> Tuple[Optional[BAN], float]:
        try:
            l = self.cp_commune_rues[(cp, commune, rue)]
            if num is None:
                for ban in l:
                    if ban.numero is None:
                        return ban, 1
                return l[0], 0.9
            min = 99999
            res = l[0]
            for ban in l:
                if ban.numero == num:
                    return ban, 1
                if ban.numero is None:
                    diff = num
                else:
                    diff = abs(ban.numero - num)
                if diff % 2 == 1:
                    diff *= 3
                if diff < min:
                    res = ban
                    min = diff
            if res.numero is None:
                score = 0.6
            else:
                score = max(0.8 - abs(res.numero - num) / (num * 0.1), 0.4)
            return res, score
        except KeyError:
            print(f"ERROR: No numero matching from {(cp, commune, rue)}")
            self.nb_error += 1
            return None, 0

    def check_low_quality(self, row: AdresseNorm, ban: BAN) -> BAN:
        ban_id = ban.id
        if self.scores[0] < 1:
            if (row.commune, row.rue1, row.numero) in self.commune_rue_numeros:
                ban = self.commune_rue_numeros[(row.commune, row.rue1, row.numero)]
                if ban_id == ban.id:
                    self.scores = [0.9, 1, 1, 1]
                else:
                    self.scores = [0.5, 1, 1, 1]
                return ban
        if self.scores[1] < 1:
            if (row.cp, row.rue1, row.numero) in self.cp_rue_numeros:
                ban = self.cp_rue_numeros[(row.cp, row.rue1, row.numero)]
                if ban_id == ban.id:
                    self.scores = [1, 0.9, 1, 1]
                else:
                    self.scores = [1, 0.5, 1, 1]
                return ban
            if self.score < 0.67:
                if (row.commune, row.rue1) in self.commune_rues:
                    ban = self.commune_rues[(row.commune, row.rue1)]
                    if ban_id == ban.id:
                        self.scores = [0.6, 1, 1, 0.4]
                    else:
                        self.scores = [0.5, 1, 1, 0.2]
                    return ban
        return ban

    def match_norm(self, row: AdresseNorm, commit=True):
        cp, score = self.match_cp(row.cp)
        if cp == 0:
            if self.echo:
                print(f"ERROR: BAD CP {cp}, cannot match")
                self.nb_error += 1
        else:
            self.scores = [score]
            communes = self.cps[cp]
            commune, score = self.match_commune(row.commune, communes)
            self.scores.append(score)
            if self.score < 0.75:
                cp2, _, score2 = self.get_cp_by_commune(row.commune)
                if score2 > self.score:
                    # print(f"WARNING BAD CP {cp} {commune}=>{cp2}")
                    cp = cp2
                    commune = row.commune
                    self.scores = [score2 / 2, 1]
            rue, score = self.match_rue(commune, row.rue1, row.rue2, cp)
            self.scores.append(score)
            ban, score = self.match_numero(cp, commune, rue, row.numero)
            if ban is not None:
                self.scores.append(score)
                if self.score < config.ban_mean - 2 * config.ban_std:
                    ban = self.check_low_quality(row, ban)
                if self.echo and self.score < config.ban_mean - 3 * config.ban_std:
                    print(f"WARNING {row.numero} {row.rue1} {row.cp} {row.commune}  =>"
                          f" {ban.numero} {ban.nom_voie} {ban.code_postal} {ban.nom_commune} @{self.score * 100:.1f}%")
                row.ban_score = self.score
                row.ban = ban
            else:
                row.ban_score = 0
            if commit:
                self.session.commit()

    def match_dept(self, d: int):
        self.make_cache1(d)
        rows = self.session.query(AdresseNorm).filter(AdresseNorm.dept_id == d)
        if not self.force:
            rows = rows.filter(self.filter_no_force)
        for row in rows:
            self.row_num += 1
            self.match_norm(row)
            self.total_scores.append(self.score)
            if self.row_num % 1000 == 0 or self.row_num == 10 or self.row_num == 100:
                print(f"Found {self.row_num} adresses {(self.row_num / self.total_nb_norm) * 100:.1f}% "
                      f"in {int(time.perf_counter() - time0)}s")

    def match(self):
        self.stats()
        self.make_cache0()
        for d in self.depts:
            print(f"Match dept {d}")
            self.match_dept(d)


if __name__ == '__main__':
    art.tprint(config.name, "big")
    print("BAN Matcher")
    print("===========")
    print(f"V{config.version}")
    print(config.copyright)
    print()
    parser = argparse.ArgumentParser(description="BAN Matcher")
    parser.add_argument("-e", "--echo", help="Sql Alchemy echo", action="store_true")
    parser.add_argument("-f", "--force", help="Force matching", action="store_true")
    parser.add_argument("-l", "--log", help="Log (BAN echo)", action="store_true")
    parser.add_argument("-d", "--dept", help="Departments list in python format, eg [5,38,06]")
    args = parser.parse_args()
    depts = None if args.dept is None else eval(args.dept)
    bm = BANMatcher(depts, args.force, args.log, args.echo)
    print(f"Database {bm.context.db_name}: {bm.context.db_size():.0f} Mo")
    bm.match()
    mean = np.mean(np.array(bm.total_scores))
    std = np.std(np.array(bm.total_scores))
    print(f"Nb Error: {bm.nb_error}")
    print(f"Score average {mean * 100:.1f}%")
    print(f"Score median {np.median(np.array(bm.total_scores)) * 100:.1f}%")
    print(f"Score min {np.min(np.array(bm.total_scores)) * 100:.1f}%")
    print(f"Score std {std * 100:.1f}%")
    print(f"Score average-std {(mean - std) * 100:.1f}%")
    print(f"Score average-3std {(mean - 3 * std) * 100:.1f}%")
    print(f"Parse {bm.row_num} adresses in {time.perf_counter() - time0:.0f} s")

    # -e -l -d [5]
