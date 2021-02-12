import unidecode
import re
import csv
import cyrilload
import difflib

class AdresseMatcher:

    def match_adresse_string(self, adresse):
        s = unidecode.unidecode(adresse.upper()).replace("'", " ").replace("-", " ").replace(".","").replace("ST ", "SAINT ")
        regex = r"(\d{5})"
        match = re.findall(regex, s)
        if len(match) > 0:
            cp = match[-1]
            index = s.find(cp)
            commune = s[index  + len(cp):].strip()
            cp = int(cp)
            s = s[:index]
            num = 0
            keys = ["RUE", "AVENUE", "AV ", "PLACE", "PL ", "CHEMIN", "CH ", "BD ", "BOULEVARD ", "IMPASSE"]
            index = self.find_multiple(keys, s)
            ss = s if index == -1 else s[:index]
            regex = r"(\d+)"
            match = re.findall(regex, ss)
            if len(match) > 0:
                num = match[-1].strip()
                index = s.find(num) + len(num)
                street = s[index:].strip()
                num = int(num)
            else:
                street = s.strip()
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


class AmeliLoader:

    def load(self):
        print("Load adresses.pickle")
        indexdb = cyrilload.load("data/adresse/adresses.pickle")
        db = indexdb["db"]
        communes_db = indexdb["communes"]
        cps_db = indexdb["cps"]
        nb = 0
        nberror = 0
        print(f"Load Ameli")
        m = AdresseMatcher()
        with open("data/ameli/ameli-all.csv") as f:
            reader = csv.DictReader(f)
            for row in reader:
                id = row["id"]
                adresse = row["adresse"].replace("<br/>", " ")
                res = m.match_adresse_string(adresse)
                if res is not None and res[0] >= 38000 and res[0] < 39000:
                    cp = res[0]
                    commune = res[1]
                    nb += 1
                    communes = []
                    if cp in cps_db:
                        communes = cps_db[cp]
                    else:
                        if "CEDEX" in commune:
                            cp = int(str(cp)[:-2]+"00")
                            # Au lieu de celà prendre le cp le plus proche en dessous
                            # si la la diff  entre les 2 cp < 100 avec un cedex score = 0.99 sinon 0.5
                            if cp in cps_db:
                                communes = cps_db[cp]
                    if len(communes) == 0:
                        print(f"ERROR1 {cp} {adresse}")
                        # prendre le cp immédiatement inférieur
                        nberror += 1
                    else:
                        if "CEDEX" in commune:
                            index = commune.find("CEDEX")
                            commune = commune[:index].strip()
                        if commune in communes:
                            ids = communes_db[commune]
                        else:

                            commune2, score = m.gestalts(commune, communes)
                            if score < 0.8:
                                print(f"WARNING {commune}=>{commune2} @{int(score*100)}%")
                            commune = commune2
                            ids = communes_db[commune]
                        entities = [db[id] for id in ids]
                        adresses = [e.nom_afnor for e in entities]
                        # D'abord essayer avec ==
                        street = res[3].replace("CH ", "CHEMIN ").replace("AV ", "AVENUE ").replace("PL ", "PLACE ").replace("BD ", "BOULEVARD ")
                        if street != "":
                            streets = [a for a in adresses if a == street]
                            if len(streets) > 0:
                                adresse = streets[0]
                                score = 1
                            else:
                                adresse, score = m.gestalts(street, adresses)
                                if score < 0.66:
                                    print(f"WARNING2 {street}=>{adresse} @{int(score*100)}%")
                        num = res[2]
                        if num != 0:
                            founds = [e for e in entities if e.nom_afnor == adresse and e.numero == num]
                            if len(founds)> 0:
                                pass
                                #print("OK")
                            else:
                                # prendre le + près
                                print(f"WARNING3 {num} {adresse} not found")




        print(nb, nberror, nberror / nb)


if __name__ == '__main__':
    l = AmeliLoader()
    l.load()

