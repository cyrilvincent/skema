import unidecode
import re
import csv
import cyrilload
import difflib
import config
import entities
import time

class AdresseMatcher:

    def __init__(self):
        self.db = None
        self.communes_db = None
        self.cps_db = None
        self.nb = 0
        self.nberror = 0
        self.nbcperror = 0
        self.nbbadcp = 0
        self.nbnostreet = 0
        self.nberrorstreet = 0
        self.nbbp = 0
        self.nbscorelow = 0


    def match_adresse_string(self, adresse):
        s = unidecode.unidecode(adresse.upper()).replace("'", " ").replace("-", " ").replace(".","").replace("ST ", "SAINT ").strip()
        # if s == 'PHARMACIE ENTRE DEUX GUIERS ZA CHAMP PERROUD AVENUE MONTCELET 38380 ENTRE DEUX GUIERS':
        #     print("toto")
        if "BP" in s:
            self.nbbp += 1
        regex = r"(\d{4,5})" # Faire {4,5} pour 01
        match = re.findall(regex, s)
        if len(match) > 0:
            cp = match[-1]
            index = s.find(cp)
            commune = s[index + len(cp):].strip()
            cp = int(cp)
            s = s[:index]
            num = 0
            keys = ["RUE", "AVENUE", "AV ", "PLACE", "PL ", "CHEMIN", "CH ", "BD ", "BOULEVARD", "IMPASSE", "ZA ", "ZI ", "ROUTE", "ZAE "]
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

    def find_multiple(self, keys, s):
        for k in keys:
            if k in s:
                return s.find(k)
        return -1

    def gestalts(self, s, l):
        max = 0
        res = 0
        for item in l:
            if item.startswith(s):
                return item, 0.99
            if s.startswith(item):
                return item, 0.98
            sm = difflib.SequenceMatcher(None, s, item)
            if sm.ratio() > max:
                max = sm.ratio()
                res = item
        return res, max

    def load_adresses(self):
        print("Load adresses.pickle")
        indexdb = cyrilload.load(f"{config.adresse_path}/adresses.pickle")
        self.db = indexdb["db"]
        self.communes_db = indexdb["communes"]
        self.cps_db = indexdb["cps"]
        print(f"Load addresses.pickle in {int(time.perf_counter() - time0)}s")

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
        res = nums[0]
        difmin = 99999
        for n in nums:
            dif = abs(num - n)
            if dif % 2 == 0 and dif < difmin:
                res = n
                difmin = dif
        return res

    def match_cp(self, cp, commune):
        if cp in self.cps_db:
            return cp, 1
        else:
            self.nbbadcp += 1
            res = self.find_nearest_less_cp(cp)
            score = 0.95 if "CEDEX" in commune else 0.5
            #print(f"Warning CP {cp}=>{res} {int(score*100)}%")
            return res, score

    def match_commune(self, commune, communes):
        if "CEDEX" in commune:
            index = commune.find("CEDEX")
            commune = commune[:index].strip()
        if commune in communes:
            return commune, 1
        else:
            return self.gestalts(commune, communes)

    def match_street(self, commune, street):
        street = street.replace("CH ", "CHEMIN ").replace("AV ", "AVENUE ").replace("PL ", "PLACE ").replace("BD ", "BOULEVARD ")
        if street == "":
            self.nbnostreet += 1
            id = list(self.communes_db[commune])[0]
            return self.db[id].nom_afnor, 0
        else:
            ids = self.communes_db[commune]
            entities = [self.db[id] for id in ids]
            adresses = [e.nom_afnor for e in entities]
            streets = [a for a in adresses if a == street]
            if len(streets) > 0:
                return streets[0], 1
            else:
                return self.gestalts(street, adresses)

    def match_num(self, commune, adresse, num):
        ids = self.communes_db[commune]
        entities = [self.db[id] for id in ids]
        if num == 0:
            nums = [e.numero for e in entities if e.nom_afnor == adresse]
            return int(sum(nums) / len(nums)), 0.6
        else:
            founds = [e.numero for e in entities if e.nom_afnor == adresse and e.numero == num]
            if len(founds) > 0:
                return num, 1
            else:
                nums = [e.numero for e in entities if e.nom_afnor == adresse]
                res = self.find_nearest_num(num, nums)
                score = max(0.5, 1 - (abs(num - res) / max(nums)))
                return res, score

    def load_ameli(self):
        with open("data/ameli/ameli-all.csv") as f:
            reader = csv.DictReader(f)
            for row in reader:
                adresse = row["adresse"].replace("<br/>", " ")
                res = self.match_adresse_string(adresse)
                if res is None:
                    self.nbcperror += 1
                    #print(f"ERROR no CP {adresse}")
                else:
                    cp = res[0]
                    commune = res[1]
                    num = res[2]
                    street = res[3]
                    if 5000 <= cp < 6000: # Temporary
                        self.nb += 1
                        if self.nb % 100 == 0:
                            print(f"Parse {self.nb} addresses in {int(time.perf_counter() - time0)}s")
                        entity = entities.AdresseEntity(0)
                        entity.code_postal, score = self.match_cp(cp, commune)
                        entity.scores.append(score)
                        communes = self.cps_db[entity.code_postal]
                        entity.commune, score = self.match_commune(commune, communes)
                        entity.scores.append(score)
                        # if score < 0.8:
                        #     print(f"Warning commune {entity.code_postal} {commune}=>{entity.commune} @{int(score*100)}%")
                        entity.nom_afnor, score = self.match_street(entity.commune, street)
                        entity.scores.append(score)
                        if score < 0.5:
                            #print(f"Warning street {street}=>{entity.nom_afnor} @{int(score * 100)}% {entity.code_postal} {entity.commune} ")
                            # if street == "PHARMACIE ENTRE DEUX GUIERS ZA CHAMP PERROUD AVENUE MONTCELET":
                            #     print("toto")
                            self.nberrorstreet += 1
                        entity.num, score = self.match_num(entity.commune, entity.nom_afnor, num)
                        entity.scores.append(score)
                        if entity.score < 0.75:
                            self.nbscorelow += 1
                            print(f"Score: {int(entity.score * 100)}% ({(self.nbscorelow / self.nb) * 100:.1f}%) {entity.num} {entity.nom_afnor} {entity.code_postal} {entity.commune} vs {adresse}")





        print(self.nb, self.nbcperror, self.nbbadcp, self.nbnostreet, self.nbbp)

if __name__ == '__main__':
    time0 = time.perf_counter()
    l = AdresseMatcher()
    l.load_adresses()
    l.load_ameli()
    # No CP: 13
    # Bad CP: 165/9693 = 1.7%
    # NoStreet: 59/9693 = 0.6%
    # BP: 74/9693 = 1.0%
    # 38 : 2.1% accuracy @ 0.8
    # 05 : 7.5% accuracy @ 0.75
