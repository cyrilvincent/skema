from typing import Dict, Optional, List, Tuple, Set, Iterable
from sqlalchemy.orm import joinedload
from sqlentities import Context, Cedex, BAN, EtablissementType, AdresseRaw, Dept, AdresseNorm, Source
import argparse
import time
import art
import config
import difflib

time0 = time.perf_counter()


class BANMatcher:

    def __init__(self, depts: List[Dept], force=False, ban_echo=False, sa_echo=False):
        self.context = Context()
        self.context.create_engine(echo=sa_echo)
        self.session = self.context.get_session(False)
        self.depts = depts
        self.force = force
        self.echo = ban_echo
        self.row_num = 0
        self.total_nb_norm = 0
        self.dept = 0
        self.csv = []
        self.cedexs: Dict[int, int] = {}
        self.cps: Dict[int, Set[str]] = {}
        self.cp_communes: [Tuple[int, str], Set[str]] = {}
        self.cp_commune_rues: [Tuple[int, str, str], List[BAN]] = {}
        self.norm: Optional[AdresseNorm] = None
        self.scores = []
        self.total_scores = []  # Tous les scores pour moyenne
        print(f"Database {self.context.db_name}: {self.context.db_size():.0f} Mo")
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
            self.total_nb_norm = self.session.query(AdresseNorm).filter(AdresseNorm.ban_id is not None).count()
        print(f"Found {self.total_nb_norm} adresses to match")

    def find_nearest_less_cp(self, cp: int) -> int:
        min = 99999
        res = 0
        for k in self.cps:
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
        elif cp in self.cedexs:
            cp, score = self.match_cp(self.cedexs[cp])
            return cp, score * 0.95
        else:
            res = self.find_nearest_less_cp(cp)
            if self.echo:
                print(f"ERROR CP DOES NOT EXIST {cp}=>{res}")
            return res, 0.5

    def denormalize_street(self, street: str) -> str:
        street = street.replace("CHEMIN", "CH").replace("AVENUE", "AV").replace("PLACE", "PL")
        street = street.replace("BOULEVARD", "BD").replace("ROUTE", "RT").replace("IMPASSE", "IMP")
        return street

    def gestalt(self, s1: str, s2: str):
        sm = difflib.SequenceMatcher(None, s1, s2)
        return sm.ratio()

    def gestalts(self, s: str, l: Iterable[str]):
        if s == "" or s is None:
            return None, 0
        max = -1
        res = None
        s = self.denormalize_street(s)
        for item in l:
            if item != "":
                if s == item:
                    return item, 1
                elif item.startswith(s) or s.startswith(item):
                    return item, 0.99
                deno = self.denormalize_street(item)
                ratio = self.gestalt(s, deno)
                if ratio > max:
                    max = ratio
                    res = item
                if max < 0.5 and s in deno:
                    max = 0.5
        return res, max

    def match_commune(self, commune: str, communes: Set[str], cp: int) -> Tuple[str, float]:
        if commune in communes:
            return commune, 1
        elif len(communes) == 1:
            return list(communes)[0], 0.95
        else:
            res, score = self.gestalts(commune, communes)
            if self.echo and score < 0.8:
                print(f"WARNING COMMUNE {cp} {commune}=>{res} @{int(score*100)}%")
            return res, score

    def match_norm(self, row: AdresseNorm):
        cp, score = self.match_cp(row.cp)
        self.scores = [score]
        communes = self.cps[cp]
        commune, score = self.match_commune(row.commune, communes, cp)
        self.scores.append(score)
        if self.score < 0.75:
            pass
            # get_cp_by_commune

    def match_dept(self, d: int):
        self.make_cache1(d)
        rows = self.session.query(AdresseNorm).filter(AdresseNorm.dept_id == d)
        if not self.force:
            rows = rows.filter(AdresseNorm.ban_id.is_(None))
        for row in rows:
            self.row_num += 1
            self.match_norm(row)
            if self.row_num % 100 == 0:
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
    bm.match()
    print(f"Parse {bm.row_num} adresses in {time.perf_counter() - time0:.0f} s")

    # -e -l -d [5]
