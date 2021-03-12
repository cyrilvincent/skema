import unidecode
import re
import csv
import cyrilload
import difflib
import config
import entities
import time
import argparse
import repositories

time0 = time.perf_counter()


class AdresseMatcher:

    def __init__(self):
        self.db = None
        self.communes_db = None
        self.cps_db = None
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
        self.pss_db = []
        self.ps_repo = repositories.PSRepository()
        self.a_repo = repositories.AdresseRepository()
        self.keys_db = {}

    def split_num(self, s):
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

    def find_nearest_less_cp(self, cp):
        min = 99999
        res = 0
        for k in self.cps_db.keys():
            dif = cp - k
            if 0 <= dif < min:
                min = dif
                res = k
        return res

    def find_nearest_num(self, num, nums):
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

    def find_multiple(self, keys, s): # TO REMOVE
        for k in keys:
            if k in s:
                return s.find(k)
        return -1

    def normalize_street(self, street):
        street = self.normalize_commune(street)
        street = " " + street
        if " BP" in street:
            self.nbcedexbp += 1
        street = street.replace(" CH ", " CHEMIN ").replace(" AV ", " AVENUE ").replace(" PL ", " PLACE ")
        street = street.replace(" BD ", "BOULEVARD ").replace(" IMP ", " IMPASSE ")
        return street.strip()

    def normalize_commune(self, commune):
        if "CEDEX" in commune:
            self.nbcedexbp += 1
            commune = commune.replace("CEDEX", "")
        commune = commune.replace("'", " ").replace("-", " ").replace(".", "").replace("/", " ")
        commune = " " + commune
        commune = commune.replace(" ST ", " SAINT ")
        return commune.strip()

    def match_cp(self, cp, commune):
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
            print(f"[{self.rownum}] WARNING BAD CP: {cp}")
            return 0, 0.0
            # res = self.find_nearest_less_cp(cp)
            # score = 0.8  # if "CEDEX" in commune else 0.5
            # print(f"[{self.rownum}] Warning CP {cp}=>{res} {int(score*100)}%")
            # return res, 0.8

    def match_commune(self, commune, adresse4, communes, cp):
        # commune = special.commune(cp, commune)
        if commune in communes:
            return commune, 1.0
        elif adresse4 != "" and adresse4 in communes:
            return adresse4, 0.9
        else:
            print(f"[{self.rownum}] WARNING BAD COMMUNE: {commune}")
            self.nbbadcommune += 1
            return 0, 0.0
            # commune, score = self.gestalts(commune, communes)
            # if score < 0.8 and adresse4 != "":
            #     adresse4, score2 = self.gestalts(adresse4, communes)
            #     if score2 > score + 0.1:
            #         return adresse4, score2
            # return commune, score

    def match_street(self, commune, adresse2, adresse3, cp):
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
        # if score > 0.9:
        #     return res, score
        # res2, score2 = self.gestalts(adresse2, adresses)
        # if score2 > 0.9:
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

    def match_num(self, commune, adresse, num):
        ids = self.communes_db[commune]
        entities = [self.db[id] for id in ids]
        if num == 0:
            nums = [e.numero for e in entities if e.nom_afnor == adresse]
            if len(nums) > 0:
                num = nums[0]
                if num == 0:
                    return 0, 1.0
                else:
                    return num, 0.8
            else:
                return 0, 0.0
        else:
            founds = [e.numero for e in entities if e.nom_afnor == adresse and e.numero == num]
            if len(founds) > 0:
                return num, 1.0
            else:
                # nums = [e.numero for e in entities if e.nom_afnor == adresse]
                # res = self.find_nearest_num(num, nums)
                # if res == 0:
                #     return 0, 0.8
                # else:
                #     return res, 0.5
                return 0, 1.0

    def get_cp_by_commune(self, commune, oldcp):
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

    def update_entity(self, entity, adresseid, score):
        entity.adresseid = adresseid
        entity.adressescore = score
        a = self.db[entity.adresseid]
        entity.lon = a.lon
        entity.lat = a.lat
        entity.x = a.x
        entity.y = a.y
        entity.codeinsee = a.code_insee
        entity.matchadresse = f"{a.numero} {a.nom_afnor} {a.code_postal} {a.commune}"

    def load_ps(self, file, dept):
        self.cps_db[0] = []  # TO REMOVE
        self.pss_db = []
        print(f"Parse {file}")
        with open(file) as f:
            reader = csv.reader(f, delimiter=";")
            self.rownum = 0
            for row in reader:
                self.rownum += 1
                cp = int(row[7])
                if ((dept * 1000) <= cp < (dept + 1) * 1000 and cp != 201 and cp != 202) or \
                        (dept == 201 and 20000 <= cp < 20200) or \
                        (dept == 202 and 20200 <= cp < 21000):
                    self.nb += 1
                    if self.nb % 100 == 0:
                        print(f"Parse {self.nb} PS in {int(time.perf_counter() - time0)}s")
                    entity = entities.PSEntity()
                    entity.rownum = self.rownum
                    self.ps_repo.row2entity(entity, row)
                    if entity.id in self.keys_db:
                        self.update_entity(entity, self.keys_db[entity.id][0], self.keys_db[entity.id][1])
                        self.pss_db.append(entity)
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
                                    print(f"[{self.rownum}] WARNING NUM in adresse2 {adresse2}")

                            # cp, commune, street = special.cp_commune_adresse(cp, commune, street)
                            # if score < 0.75:
                            #     cp2, score = self.get_cp_by_commune(commune, cp)
                            #     if cp2 != cp:
                            #         print(f"[{self.rownum}] Warning Bad CP {cp} {commune}=>{cp2} {commune}")
                            #         cp = cp2
                            #         entity.scores[-1] = score
                            #         entity.scores[-2] = 0.5
                            #     else:
                            #         print(
                            #             f"[{self.rownum}] Warning commune score {entity.cp} {entity.commune}=>{cp} {commune} @{int(score * 100)}%")
                            matchadresse, score = self.match_street(commune, adresse2, adresse3, cp)
                            entity.scores.append(score)
                            if score < 0.5:
                                self.nbscorelow += 1
                                # print(f"[{self.rownum}] Warning street {entity.adresse3}=>{adresse3} @{int(score * 100)}% {entity.cp} {entity.commune} ")
                            else:  # TO REMOVE
                                numero, score = self.match_num(commune, matchadresse, num)
                                entity.scores.append(score)
                                if entity.score < 0.8:
                                    self.nbscorelow += 1
                                    # print(f"[{self.rownum}] Score: {int(entity.score * 100)}% ({(self.nbscorelow / self.nb) * 100:.1f}%) {entity.num} {entity.commune} {entity.cp} {entity.matchstreet} vs {entity.adresse3}")
                                ids = self.communes_db[commune]
                                found = [self.db[id].id for id in ids if self.db[id].numero == numero and self.db[id].nom_afnor == matchadresse]
                                if len(found) > 0:
                                    self.update_entity(entity, found[0], entity.score)
                                    self.pss_db.append(entity)
                                    self.keys_db[entity.id] = (entity.adresseid, entity.score)
                                else:
                                    print(f"[{self.rownum}] ERROR UNKNOWN {entity.adresse3}")
                                    self.nberror500 += 1

        print(f"Nb PS: {self.nb}")
        print(f"Nb Matching PS: {len(self.pss_db)} {(len(self.pss_db) / self.nb) * 100 : .1f}%")
        print(f"Nb Unique PS: {len(self.keys_db)} ({len(self.pss_db) / len(self.keys_db):.1f} rows per PS)")
        print(f"Nb No num: {self.nonum} {(self.nonum / self.nb) * 100 : .1f}%")
        print(f"Nb Cedex BP: {self.nbcedexbp} {(self.nbcedexbp / self.nb) * 100 : .1f}%")
        print(f"Nb Bad CP: {self.nbbadcp} {(self.nbbadcp / self.nb) * 100 : .1f}%")
        print(f"Nb Commune not found: {self.nbbadcommune} {(self.nbbadcommune / self.nb) * 100 : .1f}%")
        print(f"Nb No Street: {self.nbnostreet} {(self.nbnostreet / self.nb) * 100 : .1f}%")
        print(f"Nb Bad Street: {self.nbbadstreet} {(self.nbbadstreet / self.nb) * 100 : .1f}%")
        print(f"Nb Bad Num: {self.nbscorelow} {(self.nbscorelow / self.nb) * 100 : .1f}%")
        print(f"Nb Error 500: {self.nberror500} {(self.nberror500 / self.nb) * 100 : .1f}%")

    def load_by_depts(self, file, depts=None):
        if depts is None:
            depts = list(range(1, 21)) + list(range(21, 96)) + [201, 202]
        for dept in depts:
            print(f"Load dept {dept}")
            self.db, self.communes_db, self.cps_db = l.a_repo.load_adresses(dept, time0)
            l.load_ps(file, dept)
        print(f"Match {self.nb} PS in {int(time.perf_counter() - time0)}s")
        file = file.replace(".csv", "-adresses.csv")
        self.ps_repo.save_entities(file, l.pss_db)
        print(f"Saved {self.nb} PS in {int(time.perf_counter() - time0)}s")


if __name__ == '__main__':
    print("Adresses Matcher")
    print("================")
    print(f"V{config.version}")
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
    # Nb No num: 3568  18.1%
    # Nb Bad CP: 601  3.0%
    # Nb Commune not found: 718  3.6% (+3.0%)
    # Nb No Street: 13  0.1%
    # Nb Bad Street: 8518  43.1% (+6.7%)

