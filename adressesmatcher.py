import re
import difflib
import config
import entities
import time
import argparse
import repositories
import art
from typing import Dict, Set, List, Tuple, Optional, Iterable

time0 = time.perf_counter()


class AdresseMatcher:
    """
    Fusionne ps-tarifs et adresses
    """

    def __init__(self):
        self.db: Dict[str, entities.AdresseEntity] = {}
        self.communes_db: Dict[str, Set[str]] = {}
        self.cps_db: Dict[int, Set[str]] = {}
        self.nb = 0
        self.nbbadcp = 0
        self.nbnostreet = 0
        self.nbscorelow = 0
        self.rownum = 0
        self.nberror500 = 0
        self.nbcedexbp = 0
        self.nonum = 0
        self.nbbadcommune = 0
        self.nbbadinsee = 0
        self.total = 1
        self.i = 0
        self.pss_db = []
        self.ps_repo = repositories.PSRepository()
        self.a_repo = repositories.AdresseRepository()
        self.keys_db = {}
        self.adresses_db = {}
        self.insees_db = {}
        self.cedex_db = {}
        self.csv = []

    def log(self, msg: str):
        """
        Log
        :param msg:
        """
        span = int(time.perf_counter() - time0)
        s = f"{span}s"
        if span >= 6000:
            s = f"{span // 3600}h{(span % 3600) // 60}m"
        elif span >= 600:
            s = f"{span // 60}m{span % 60}s"
        print(f"{s} {(self.i / self.total)*100:.1f}% [{self.rownum}] {msg}")

    def split_num(self, s: str) -> Tuple[int, str]:
        """
        Split s en fonction du numero
        :param s: chaine
        :return: tuple numéro, reste de la chaine
        """
        regex = r"(\d+)"
        match = re.match(regex, s)
        if match is None:
            self.nonum += 1
            return 0, s
        num = match[1]
        index = s.index(match[1])
        return int(num), s[index + len(num):].strip()

    def find_nearest_less_cp(self, cp: int) -> int:
        """
        Retrouve le code postal immédiatement inférieur pour les CEDEX
        :param cp:
        :return:
        """
        min = 99999
        res = 0
        for k in self.cps_db.keys():
            dif = cp - k
            if 0 <= dif < min:
                min = dif
                res = k
        return res

    def find_nearest_num(self, num: int, nums: List[int]) -> int:
        """
        Trouve le numéro de rue le plus proche de num parmis nums, encourange les mêmes côtés de rue
        :param num: le numéro à rechercher
        :param nums: la lsite de numéro dans lesquels chercher
        :return: le numéro proche trouvé
        """
        res = 0
        difmin = 99999
        for n in nums:
            dif = abs(num - n)
            if dif % 2 == 1:
                dif *= 3
            if dif < difmin:
                res = n
                difmin = dif
        return res

    def gestalts(self, s: str, l: Iterable[str]):
        """
        Machine Learning Gestalt
        Applique Gestalt sur s et tous les éléments de l
        :param s: la chaine de gauche
        :param l: la liste des chaine de droite à comparer
        :return: le meilleur score
        """
        if s == "":
            return "", 0
        max = -1
        res = 0
        for item in l:
            if item != "":
                if item.startswith(s) or s.startswith(item):
                    return item, 0.99
                sm = difflib.SequenceMatcher(None, s, item)
                if sm.ratio() > max:
                    max = sm.ratio()
                    res = item
        return res, max

    def normalize_street(self, street: str) -> str:
        """
        Normalise la rue
        :param street: rue
        :return: rue normalisée
        """
        street = street.upper().replace("'", " ").replace("-", " ").replace(".", "").replace("/", " ").replace('"', "")
        street = " " + street
        if " BP" in street:
            self.nbcedexbp += 1
            street.replace(" BP", "")
        street = street.replace(" CH ", " CHEMIN ").replace(" AV ", " AVENUE ").replace(" PL ", " PLACE ")
        street = street.replace(" BD ", " BOULEVARD ").replace(" IMP ", " IMPASSE ").replace(" ST ", " SAINT ")
        street = street.replace(" RT ", " ROUTE ").replace(" GAL ", " GENERAL ")
        return street.strip()

    def normalize_commune(self, commune: str) -> str:
        """
        Normalise la commune
        :param commune: commune
        :return: la commune normalisée
        """
        if "CEDEX" in commune:
            self.nbcedexbp += 1
            index = commune.index("CEDEX")
            commune = commune[:index]
        commune = commune.upper().replace("'", " ").replace("-", " ").replace(".", "").replace("/", " ")
        commune = " " + commune
        commune = commune.replace(" ST ", " SAINT ").replace(" STE ", " SAINTE ")
        return commune.strip()

    def match_cp(self, cp: int) -> Tuple[int, float]:
        """
        Match le code postal
        :param cp: le code postal
        :return: le code postal matché
        """
        # cp = special.cp_cedex(cp)
        if cp in self.cps_db:
            return cp, 1.0
        elif 1000 > cp >= 97000:
            self.nbbadcp += 1
            return 0, 0.0
        elif 75100 <= cp < 75200:
            self.nbbadcp += 1
            cp, score = self.match_cp(cp - 100)
            return cp, score * 0.9
        elif cp in self.cedex_db:
            insee = self.cedex_db[cp].code_insee
            if insee in self.insees_db:
                res = list(self.insees_db[insee])[0]
                self.log(f"WARNING CEDEX {cp}=>{res}")
                return res, 0.9
            else:
                self.nbbadinsee += 1
                self.nbbadcp += 1
                self.log(f"ERROR BAD INSEE {cp} {insee}")  # ERREUR GRAVE
                return self.find_nearest_less_cp(cp), 0.25
        else:
            self.nbbadcp += 1
            res = self.find_nearest_less_cp(cp)
            self.log(f"WARNING CP {cp}=>{res}")
            return res, 0.5

    def match_commune(self, commune: str, adresse4: str, communes: Set[str], cp: int) -> Tuple[str, float]:
        """
        Match la commune
        :param commune: la commune
        :param adresse4: adresse4
        :param communes: la liste des communes à matcher
        :param cp: le code postal
        :return: la commune matchée
        """
        # commune = special.commune(cp, commune)
        if commune in communes:
            return commune, 1.0
        elif len(communes) == 1:
            return list(communes)[0], 0.95
        elif adresse4 != "" and adresse4 in communes:
            return adresse4, 0.9
        else:
            res, score = self.gestalts(commune, communes)
            if score < 0.75 and adresse4 != "":
                res2, score2 = self.gestalts(adresse4, communes)
                if score2 > score + 0.1:
                    self.log(f"WARNING COMMUNE Adresse4 {cp} {commune} {adresse4}=>{res2} @{int(score2*100)}%")
                    return res2, score2
            self.log(f"WARNING COMMUNE {cp} {commune}=>{res} @{int(score*100)}%")
            return res, score

    def match_street(self, commune: str, adresse2: str, adresse3: str, cp: int) -> Tuple[str, float]:
        """
        Match l'adresse3
        :param commune: la commune
        :param adresse2: adresse2
        :param adresse3: adresse3
        :param cp: le code postal
        :return: la rue de la commune matchée
        """
        # adresse3 = special.street(cp, adresse3)
        ids = self.communes_db[commune]
        entities = [self.db[id] for id in ids]
        adresses = [e.nom_afnor for e in entities if e.code_postal == cp]
        adresses_voie = [e.nom_voie for e in entities if e.code_postal == cp]
        if adresse3 == "":
            self.nbnostreet += 1
            adresse3 = "MAIRIE EGLISE"
        if adresse3 in adresses:
            return adresse3, 1.0
        if adresse3 in adresses_voie:
            index = adresses_voie.index(adresse3)
            return adresses[index], 0.99
        res, score = self.gestalts(adresse3, adresses)
        if score > 0.8:
            return res, score
        res2, score2 = self.gestalts(adresse2, adresses)
        if score2 > 0.8:
            return res2, score2
        res3, score3 = self.gestalts(adresse3, adresses_voie)
        if score + 0.1 > max(score2, score3):
            return res, score
        if score2 > score3:
            return res2, score2 * 0.8
        index = adresses_voie.index(res3)
        return adresses[index], score3 * 0.9

    def match_num(self, commune: str, adresse: str, num: int) -> Tuple[Optional[entities.AdresseEntity], float]:
        """
        Match le numéro de rue
        :param commune: la commune
        :param adresse: la rue
        :param num: le numéro
        :return: le numéro de la rue matché
        """
        ids = self.communes_db[commune]
        adresses = [self.db[id] for id in ids]
        if num == 0:
            adresses = [e for e in adresses if e.nom_afnor == adresse]
            if len(adresses) > 0:
                if adresses[0].numero == 0:
                    return adresses[0], 1.0
                else:
                    return adresses[0], 0.9
            else:
                return None, 0.0
        else:
            founds = [e for e in adresses if e.nom_afnor == adresse and e.numero == num]
            if len(founds) > 0:
                return founds[0], 1.0
            else:
                nums = [e.numero for e in adresses if e.nom_afnor == adresse]
                res = self.find_nearest_num(num, nums)
                founds = [e for e in adresses if e.nom_afnor == adresse and e.numero == res]
                if len(founds) > 0:
                    score = max(1 - abs(res - num) / 10, 0.5)
                    return founds[0], score
                return None, 0.0  # Normalement impossible


    def update_entity(self, entity: entities.PSEntity, aentity: entities.AdresseEntity, score: float):
        """
        MAJ PS par rapport à l'adresse
        :param entity: PS
        :param aentity: adresse entity
        :param score: le score de matching
        """
        entity.adresseid = aentity.id
        entity.adressescore = score
        entity.lon = aentity.lon
        entity.lat = aentity.lat
        entity.x = aentity.x
        entity.y = aentity.y
        entity.codeinsee = aentity.code_insee
        entity.matchadresse = f"{aentity.numero} {aentity.nom_afnor} {aentity.code_postal} {aentity.commune}"
        entity.matchcp = aentity.code_postal

    def check_low_score(self, entity: entities.PSEntity,
                        adresse3: str, originalnum: int, aentity: entities.AdresseEntity) -> entities.AdresseEntity:
        # if entity.score < config.adresse_quality:
        #     res = self.last_chance(self.normalize_commune(entity.commune), self.normalize_street(adresse3),
        #                                   originalnum)
        #     if res is not None:
        #         self.nbbadcp += 1
        #         aentity = res
        #         self.log(f"WARNING Bad CP: {entity.cp} {entity.commune}=>{aentity.code_postal} {aentity.commune}")
        #         entity.scores[0] = 0.5
        #         entity.scores[1] = entity.scores[2] = entity.scores[3] = 0.99
        #     else:
        #         res = self.very_last_chance(int(entity.cp), self.normalize_street(adresse3), originalnum)
        #         if res is not None:
        #             self.nbbadcommune += 1
        #             aentity = res
        #             self.log(f"WARNING Bad Commune: {entity.cp} {entity.commune}=>{aentity.code_postal}"
        #                      f" {aentity.commune}")
        #             entity.scores[1] = 0.5
        #             entity.scores[0] = entity.scores[2] = entity.scores[3] = 0.98
        if entity.score < config.adresse_quality:
            self.nbscorelow += 1
            nba = len(self.adresses_db) if len(self.adresses_db) != 0 else 1
            self.log(f"LOW SCORE: {int(entity.score * 100)}% ({(self.nbscorelow / nba) * 100:.1f}%)"
                     f" {entity.adresse3} {entity.cp} {entity.commune} => {aentity.numero} {aentity.nom_afnor}"
                     f" {aentity.code_postal} {aentity.commune}")
        if aentity is None:
            aentity = entities.AdresseEntity(0)
            self.log(f"ERROR UNKNOWN {entity.adresse3} {entity.cp} {entity.commune}")
            self.nberror500 += 1
        return aentity

    def parse_ps(self, dept: int):
        """
        Fonction principale, charge PS et match un département
        :param dept: un département
        """
        self.rownum = 0
        for row in self.csv:
            self.i += 1
            self.rownum += 1
            cp = int(row[7])
            if ((dept * 1000) <= cp < (dept + 1) * 1000 and cp != 201 and cp != 202) or \
                    (dept == 201 and 20000 <= cp < 20200) or \
                    (dept == 202 and 20200 <= cp < 21000):
                self.nb += 1
                entity = entities.PSEntity()
                entity.rownum = self.rownum
                self.ps_repo.row2entity(entity, row)
                t = (entity.cp, entity.commune, entity.adresse3, entity.adresse2, entity.adresse4)
                if t in self.adresses_db:
                    aentity = self.db[self.adresses_db[t][0]]
                    self.update_entity(entity, aentity, self.adresses_db[t][1])
                    self.keys_db[entity.id] = (entity.adresseid, entity.score)
                    self.pss_db.append(entity)
                else:
                    cp, score = self.match_cp(cp)
                    entity.scores.append(score)
                    communes = self.cps_db[cp]
                    commune = self.normalize_commune(entity.commune)
                    adresse4 = self.normalize_street(entity.adresse4)
                    commune, score = self.match_commune(commune, adresse4, communes, cp)
                    entity.scores.append(score)
                    # if score < 0.8:
                    #     cp2, commune2, score2 = self.get_cp_by_commune(self.normalize_commune(entity.commune), cp)
                    #     if score2 > score:
                    #         self.log(f"[{self.rownum}] WARNING Bad CP {entity.cp} {entity.commune}=>{cp2} {commune2}")
                    #         self.nbbadcp += 1
                    #         cp = cp2
                    #         commune = commune2
                    #         entity.scores[1] = score2
                    #         entity.scores[0] = 0.5
                    adresse3 = self.normalize_street(entity.adresse3)
                    adresse2 = self.normalize_street(entity.adresse2)
                    num, adresse3 = self.split_num(adresse3)
                    if num == 0 and adresse2 != "":
                        num, adresse2 = self.split_num(adresse2)
                    originalnum = num
                    matchadresse, score = self.match_street(commune, adresse2, adresse3, cp)
                    entity.scores.append(score)
                    aentity, score = self.match_num(commune, matchadresse, num)
                    entity.scores.append(score)
                    aentity = self.check_low_score(entity, adresse3, originalnum, aentity)
                    self.update_entity(entity, aentity, entity.score)
                    self.pss_db.append(entity)
                    self.keys_db[entity.id] = (entity.adresseid, entity.score)
                    self.adresses_db[t] = (entity.adresseid, entity.score)

    def display(self):
        print(f"Nb PS: {self.nb}")
        print(f"Nb Matching PS: {len(self.pss_db)} {(len(self.pss_db) / self.nb) * 100 : .1f}%")
        print(f"Nb Unique PS: {len(self.keys_db)} ({len(self.keys_db) / self.nb:.1f} rows/PS)")
        print(f"Nb Unique Adresse: {len(self.adresses_db)} ({len(self.adresses_db) / self.nb:.1f} rows/PS)")
        print(f"Nb No num: {self.nonum} {(self.nonum / len(self.adresses_db)) * 100 : .1f}%")
        print(f"Nb Cedex BP: {self.nbcedexbp} {(self.nbcedexbp / len(self.adresses_db)) * 100 : .1f}%")
        print(f"Nb Bad CP: {self.nbbadcp} {(self.nbbadcp / len(self.adresses_db)) * 100 : .1f}%")
        print(f"Nb Bad commune: {self.nbbadcommune} {(self.nbbadcommune / len(self.adresses_db)) * 100 : .1f}%")
        print(f"Nb No Street: {self.nbnostreet} {(self.nbnostreet / len(self.adresses_db)) * 100 : .1f}%")
        print(f"Nb Error Unknown: {self.nberror500} {(self.nberror500 / len(self.adresses_db)) * 100 : .1f}%")
        print(f"Nb Bad INSEE: {self.nbbadinsee}")
        print(f"Nb Score low: {self.nbscorelow} {(self.nbscorelow / len(self.adresses_db)) * 100 : .1f}%")

    def load_by_depts(self, file: str, depts: Optional[List[int]] = None):
        """
        Prépare le chargement de PS en fonction d'une liste de département
        :param file: PS
        :param depts: la liste de département, None = all
        """
        self.log(f"Load {file}")
        self.csv = self.ps_repo.load_ps(file)
        self.total = len(self.csv)
        # self.log(f"Load {config.cedex_path}")
        # self.cedex_db = self.a_repo.load_cedex()
        if depts is None:
            depts = list(range(1, 20)) + list(range(21, 96)) + [201, 202]
        self.total *= len(depts)
        for dept in depts:
            self.log(f"Load dept {dept}")
            self.db, self.communes_db, self.cps_db, self.insees_db = self.a_repo.load_adresses(dept)
            self.parse_ps(dept)
        self.display()
        self.pss_db.sort(key=lambda e: e.rownum)
        file = file.replace(".csv", "-adresses.csv")
        self.ps_repo.save_entities(file, self.pss_db)
        self.log(f"Saved {self.nb} PS")


if __name__ == '__main__':
    art.tprint(config.name, "big")
    print("Adresses Matcher")
    print("================")
    print(f"V{config.version}")
    print(config.copyright)
    print()
    parser = argparse.ArgumentParser(description="Adresses Matcher")
    parser.add_argument("path", help="Path")
    parser.add_argument("-d", "--dept", help="Departments list in python format, eg [5,38,06]")
    args = parser.parse_args()
    am = AdresseMatcher()
    if args.dept is None:
        am.load_by_depts(args.path)
    else:
        am.load_by_depts(args.path, eval(args.dept))

    # 38
    # Nb PS: 48927
    # Nb Matching PS: 48927  100.0%
    # Nb Unique PS: 3178 (15.4 rows/PS)
    # Nb Unique Adresse: 2176 (0.7 rows/PS)
    # Nb No num: 308  14.2%
    # Nb Cedex BP: 101  4.6%
    # Nb Bad CP: 59  2.7%
    # Nb Bad commune: 0  0.0%
    # Nb No Street: 2  0.1%
    # Nb Error 500: 0  0.0%
    # Nb Score low: 4.3%
    # Save data/ps/ps-tarifs-21-03-adresses.csv
    # 102s 100.0% [2455164] Saved 48927 PS

    # 48
    # Nb PS: 1620
    # Nb Matching PS: 1620  100.0%
    # Nb Unique PS: 129 (0.1 rows/PS)
    # Nb Unique Adresse: 102 (0.1 rows/PS)
    # Nb No num: 66  64.7%
    # Nb Cedex BP: 0  0.0%
    # Nb Bad CP: 1  1.0%
    # Nb Bad commune: 0  0.0%
    # Nb No Street: 2  2.0%
    # Nb Error 500: 0  0.0%
    # Nb Bad INSEE: 0
    # Nb Score low: 14  13.7%
    # Save data/ps/ps-tarifs-21-03-adresses.csv
    # 14s 100.0% [2455164] Saved 1620 PS

    #
    # 0.87
    # Nb PS: 2401126
    # Nb Matching PS: 2401126  100.0%
    # Nb Unique PS: 151242 (0.1 rows/PS)
    # Nb Unique Adresse: 96114 (0.0 rows/PS)
    # Nb No num: 14589  15.2%
    # Nb Cedex BP: 5386  5.6%
    # Nb Bad CP: 4370  4.5%
    # Nb Bad commune: 0  0.0%
    # Nb No Street: 214  0.2%
    # Nb Error 500: 0  0.0%
    # Nb Bad INSEE: 0
    # Nb Score low: 5529  5.8%
    # Save data/ps/ps-tarifs-21-03-adresses.csv
    # 2h55m 100.0% [2455164] Saved 2401126 PS

