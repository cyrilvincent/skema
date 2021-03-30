import unidecode
import re
import csv
import difflib
import config
import entities
import time
import argparse
import repositories
from typing import Dict, Set, List, Tuple, Optional

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
        self.nbbadstreet = 0
        self.nbscorelow = 0
        self.rownum = 0
        self.nberror500 = 0
        self.nbcedexbp = 0
        self.nonum = 0
        self.nbbadcommune = 0
        self.total = 1
        self.i = 0
        self.pss_db = []
        self.ps_repo = repositories.PSRepository()
        self.a_repo = repositories.AdresseRepository()
        self.keys_db = {}
        self.adresses_db = {}
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

    def match_adresse_string(self, adresse): #TO REMOVE
        s = unidecode.unidecode(adresse.upper()).replace("'", " ").replace("-", " ").replace(".", "")
        s = s.replace("ST ", "SAINT ").replace("/", " ").strip()
        if "BP" in s:
            self.nbbp += 1
        regex = r"(\d{5})"
        match = re.findall(regex, s)
        if len(match) > 0:
            cp = match[-1]
            index = s.find(cp)
            commune = s[index + len(cp):].strip()
            cp = int(cp)
            s = s[:index]
            num = 0
            keys = ["RUE", "AVENUE", "AV ", "PLACE", "PL ", "CHEMIN", "CH ", "BD ", "BOULEVARD", "IMPASSE", "ZA ",
                    "ZI ", "ROUTE", "ZAE "]
            index = self.find_multiple(keys, s)
            street = s.strip()
            ss = s if index == -1 else s[:index]
            if index != -1:
                street = s[index:].strip()
            regex = r"(\d+)"
            match = re.findall(regex, ss)
            if len(match) > 0:
                num = match[-1].strip()
                index = s.find(num) + len(num)
                street = s[index:].strip()
                num = int(num)
            rep = ""
            if len(street) > 1 and street[1] == " ":
                rep = street[0]
                street = street[1:].strip()
            if street.startswith("BIS") or street.startswith("TER"):
                rep = street[:3]
                street = street[3:].strip()
            return cp, commune, num, street, rep
        else:
            return None

    def find_multiple(self, keys, s): # TO REMOVE
        for k in keys:
            if k in s:
                return s.find(k)
        return -1

    def normalize_street(self, street: str) -> str:
        """
        Normalise la rue
        :param street: rue
        :return: rue normalisée
        """
        street = street.replace("'", " ").replace("-", " ").replace(".", "").replace("/", " ")
        street = " " + street
        if " BP" in street:
            self.nbcedexbp += 1
            street.replace(" BP", "")
        street = street.replace(" CH ", " CHEMIN ").replace(" AV ", " AVENUE ").replace(" PL ", " PLACE ")
        street = street.replace(" BD ", "BOULEVARD ").replace(" IMP ", " IMPASSE ").replace(" ST ", " SAINT ")
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
        commune = commune.replace("'", " ").replace("-", " ").replace(".", "").replace("/", " ")
        commune = " " + commune
        commune = commune.replace(" ST ", " SAINT ").replace(" STE ", " SAINTE ")
        return commune.strip()

    def match_cp(self, cp: int, commune: str) -> Tuple[int, float]:
        """
        Match le code postal
        :param cp: le code postal
        :param commune: la commune
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
            cp, score = self.match_cp(cp - 100, commune)
            return cp, score * 0.9
        else:
            self.nbbadcp += 1
            self.log(f"WARNING BAD CP: {cp}")
            return 0, 0.0
            # res = self.find_nearest_less_cp(cp)
            # score = 0.8  # if "CEDEX" in commune else 0.5
            # self.log(f"Warning CP {cp}=>{res} {int(score*100)}%")
            # return res, 0.8

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
            self.log(f"WARNING BAD COMMUNE: {cp} {commune}")
            self.nbbadcommune += 1
            return 0, 0.0
            # commune, score = self.gestalts(commune, communes)
            # if score < 0.8 and adresse4 != "":
            #     adresse4, score2 = self.gestalts(adresse4, communes)
            #     if score2 > score + 0.1:
            #         return adresse4, score2
            # return commune, score

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

        # res, score = self.gestalts(adresse3, adresses)
        # if score > 0.8:
        #     return res, score
        # res2, score2 = self.gestalts(adresse2, adresses)
        # if score2 > 0.8:
        #     return res2, score2
        # res3, score3 = self.gestalts(adresse3, adresses_voie)
        # if score + 0.1 > max(score2, score3):
        #     return res, score
        # if score2 > score3:
        #     return res2, score2 * 0.8
        # index = adresses_voie.index(res3)
        # return adresses[index], score3 * 0.9

        self.nbbadstreet += 1
        return "", 0

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
                    return adresses[0], 0.8
            else:
                return None, 0.0
        else:
            founds = [e for e in adresses if e.nom_afnor == adresse and e.numero == num]
            if len(founds) > 0:
                return founds[0], 1.0
            else:
                # nums = [e.numero for e in adresses if e.nom_afnor == adresse]
                # res = self.find_nearest_num(num, nums)
                # founds = [e for e in adresses if e.nom_afnor == adresse and e.numero == num]
                # if len(founds) > 0:
                #     if res == 0:
                #         return 0, 0.8
                #     else:
                #         return res, 0.5
                # return entities.AdresseEntity(), 0.0 # Normalement impossible mettre un point d'arrêt
                return None, 0.0

    def get_cp_by_commune(self, commune: str, oldcp: int) -> Tuple[int, float]:
        """
        TODO
        :param commune:
        :param oldcp:
        :return:
        """
        if commune in self.communes_db:
            ids = self.communes_db[commune]
            dept = str(oldcp)[:2] if oldcp >= 10000 else "0" + str(oldcp)[:1]
            for id in ids:
                e = self.db[id]
                if e.commune == commune and str(e.code_postal)[:2] == dept:
                    return e.code_postal, 0.99
                if (e.commune.startswith(commune) or e.commune.endswith(commune)) and str(e.code_postal)[:2] == dept:
                    return e.code_postal, 0.9
        return oldcp, 0

    def last_chance(self, commune: str, adresse3: str, num: int) -> Tuple[Optional[entities.AdresseEntity], float]:
        if commune in self.communes_db:
            ids = self.communes_db[commune]
            for id in ids:
                e = self.db[id]
                if e.commune == commune and (e.nom_afnor == adresse3 or e.nom_voie == adresse3) and e.numero == num:
                    return e, 0.95
        return None, 0

    def last_chance2(self, cp: int, adresse3: str, num: int) -> Tuple[Optional[entities.AdresseEntity], float]:
        communes = self.cps_db[cp]
        for commune in communes:
            ids = self.communes_db[commune]
            for id in ids:
                e = self.db[id]
                if e.code_postal == cp and (e.nom_afnor == adresse3 or e.nom_voie == adresse3) and e.numero == num:
                    return e, 0.95
        return None, 0

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

    def parse_ps(self, file: str, dept: int):
        """
        Fonction principale, charge PS et match un département
        :param file: le fichier PS
        :param dept: un département
        """
        self.cps_db[0] = []  # TO REMOVE
        self.log(f"Parse {file}")
        self.rownum = 0
        for row in self.csv:
            self.i += 1
            self.rownum += 1
            cp = int(row[7])
            if ((dept * 1000) <= cp < (dept + 1) * 1000 and cp != 201 and cp != 202) or \
                    (dept == 201 and 20000 <= cp < 20200) or \
                    (dept == 202 and 20200 <= cp < 21000):
                self.nb += 1
                if self.nb % 1000 == 0:
                    self.log(f"Parse {self.nb} PS in {dept}")
                entity = entities.PSEntity()
                entity.rownum = self.rownum
                self.ps_repo.row2entity(entity, row)
                t = (entity.cp, entity.commune, entity.adresse3, entity.adresse2, entity.adresse4)
                if t in self.adresses_db:
                    aentity = self.db[self.adresses_db[t][0]]
                    self.update_entity(entity, aentity, self.adresses_db[t][1])
                    self.keys_db[entity.id] = (entity.adresseid, entity.score)
                    self.pss_db.append(entity)
                # if entity.id in self.keys_db:
                #     self.update_entity(entity, self.keys_db[entity.id][0], self.keys_db[entity.id][1])
                #     self.pss_db.append(entity)
                else:
                    commune = self.normalize_commune(entity.commune)
                    cp, score = self.match_cp(cp, commune)
                    entity.scores.append(score)
                    communes = self.cps_db[cp]
                    adresse4 = self.normalize_street(entity.adresse4)
                    commune, score = self.match_commune(commune, adresse4, communes, cp)
                    entity.scores.append(score)
                    if commune != 0:  # TO REMOVE
                        adresse3 = self.normalize_street(entity.adresse3)
                        adresse2 = self.normalize_street(entity.adresse2)
                        num, adresse3 = self.split_num(adresse3)
                        if num == 0 and adresse2 != "":
                            num, adresse2 = self.split_num(adresse2)
                            if num != 0:
                                self.log(f"WARNING NUM in adresse2 {adresse2}")

                        # cp, commune, street = special.cp_commune_adresse(cp, commune, street)
                        # if score < 0.8:
                        #     cp2, score = self.get_cp_by_commune(commune, cp)
                        #     if cp2 != cp:
                        #         print(f"[{self.rownum}] Warning Bad CP {cp} {commune}=>{cp2} {commune}")
                        #         cp = cp2
                        #         entity.scores[-1] = score
                        #         entity.scores[-2] = 0.5
                        #     else:
                        #         self.log(f"Warning commune score {entity.cp} {entity.commune}=>{cp} {commune} @{int(score * 100)}%")
                        matchadresse, score = self.match_street(commune, adresse2, adresse3, cp)
                        entity.scores.append(score)
                        if score < 0.5:
                            self.nbscorelow += 1
                            # self.log(f"Warning street {entity.adresse3}=>{adresse3} @{int(score * 100)}% {entity.cp} {entity.commune} ")
                        else:  # TO REMOVE
                            aentity, score = self.match_num(commune, matchadresse, num)
                            entity.scores.append(score)
                            if entity.score < 0.8:
                                self.nbscorelow += 1
                                # lastchance
                                # self.log(f"Score: {int(entity.score * 100)}% ({(self.nbscorelow / self.nb) * 100:.1f}%) {entity.num} {entity.commune} {entity.cp} {entity.matchstreet} vs {entity.adresse3}")
                            #ids = self.communes_db[commune]
                            #found = [self.db[id].id for id in ids if self.db[id].numero == numero and self.db[id].nom_afnor == matchadresse]
                            #if len(found) > 0:
                            if aentity is None:
                                aentity = entities.AdresseEntity(0)
                                self.log(f"ERROR UNKNOWN {entity.adresse3} {entity.cp} {entity.commune}")
                                self.nberror500 += 1
                            else: # TO REMOVE
                                self.update_entity(entity, aentity, entity.score)
                                self.pss_db.append(entity)
                                self.keys_db[entity.id] = (entity.adresseid, entity.score)
                                self.adresses_db[t] = (entity.adresseid, entity.score)

        print(f"Nb PS: {self.nb}")
        print(f"Nb Matching PS: {len(self.pss_db)} {(len(self.pss_db) / self.nb) * 100 : .1f}%")
        print(f"Nb No num: {self.nonum} {(self.nonum / self.nb) * 100 : .1f}%")
        print(f"Nb Cedex BP: {self.nbcedexbp} {(self.nbcedexbp / self.nb) * 100 : .1f}%")
        print(f"Nb Bad CP: {self.nbbadcp} {(self.nbbadcp / self.nb) * 100 : .1f}%")
        print(f"Nb Commune not found: {self.nbbadcommune} {(self.nbbadcommune / self.nb) * 100 : .1f}%")
        print(f"Nb No Street: {self.nbnostreet} {(self.nbnostreet / self.nb) * 100 : .1f}%")
        print(f"Nb Bad Street: {self.nbbadstreet} {(self.nbbadstreet / self.nb) * 100 : .1f}%")
        print(f"Nb Bad Num: {self.nbscorelow} {(self.nbscorelow / self.nb) * 100 : .1f}%")
        print(f"Nb Error 500: {self.nberror500} {(self.nberror500 / self.nb) * 100 : .1f}%")
        print(f"Nb Unique PS: {len(self.keys_db)} ({len(self.pss_db) / len(self.keys_db):.1f} rows per PS)")
        print(f"Nb Unique Adresse: {len(self.adresses_db)}") #333 adresse3, 406 adresse234, 703 UniquePS

    def load_by_depts(self, file: str, depts: Optional[List[int]] = None):
        """
        Prépare le chargement de PS en fonction d'une liste de département
        :param file: PS
        :param depts: la liste de département, None = all
        """
        self.log(f"Load {file}")
        self.csv = self.ps_repo.load_ps(file)
        self.total = len(self.csv)
        if depts is None:
            depts = list(range(1, 20)) + list(range(21, 96)) + [201, 202]
        self.total *= len(depts)
        for dept in depts:
            self.log(f"Load dept {dept}")
            self.db, self.communes_db, self.cps_db = l.a_repo.load_adresses(dept, time0)
            self.parse_ps(file, dept)
        self.log(f"Match {self.nb} PS")
        file = file.replace(".csv", "-adresses.csv")
        self.pss_db.sort(key=lambda e: e.rownum)
        self.ps_repo.save_entities(file, l.pss_db)
        self.log(f"Saved {self.nb} PS")


if __name__ == '__main__':
    print("Adresses Matcher")
    print("================")
    print(f"V{config.version}")
    print(config.copyright)
    print()
    parser = argparse.ArgumentParser(description="Adresses Matcher")
    parser.add_argument("path", help="Path")
    parser.add_argument("-d", "--dept", help="Departments list in python format, eg [5,38,06]")
    args = parser.parse_args()
    l = AdresseMatcher()
    if args.dept is None:
        l.load_by_depts(args.path)
    else:
        l.load_by_depts(args.path, eval(args.dept))

    # 38
    # Nb PS: 48927
    # Nb No num: 3491  7.1%
    # Nb Bad CP: 2181  4.5%
    # Nb Commune not found: 2649  5.4% (+4.5%)
    # Nb No Street: 11  0.0%
    # Nb Bad Street: 15776  32.2% (+9.9%)

    # 01
    # Nb PS: 19766
    # Nb Matching PS: 12255  62.0%
    # Nb No num: 3327  16.8%
    # Nb Cedex BP: 295  1.5%
    # Nb Bad CP: 601  3.0%
    # Nb Commune not found: 718  3.6%
    # Nb No Street: 13  0.1%
    # Nb Bad Street: 6650  33.6%
    # Nb Bad Num: 6650  33.6%
    # Nb Error 500: 143  0.7%
    # Nb Unique PS: 703 (17.4 rows per PS)
    # Nb Unique Adresse: 406

    # All
    # Nb PS: 2401126
    # Nb Matching PS: 1597210  66.5%
    # Nb No num: 152354  6.3%
    # Nb Cedex BP: 125713  5.2%
    # Nb Bad CP: 118729  4.9%
    # Nb Commune not found: 154299  6.4%
    # Nb No Street: 2450  0.1%
    # Nb Bad Street: 608100  25.3%
    # Nb Bad Num: 649617  27.1%
    # Nb Error 500: 41517  1.7%
    # Nb Unique PS: 104125 (15.3 rows per PS)
    # Nb Unique Adresse: 61120

