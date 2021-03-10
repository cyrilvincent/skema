import unidecode
import re
import csv
import cyrilload
import difflib
import config
import entities
import time
import argparse
#import special

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
        self.numrow = 0
        self.nberror500 = 0
        self.nonum = 0
        self.nbbadcommune = 0
        self.psentities = []

    def split_num(self, s):
        regex = r"(\d+)"
        match = re.match(regex, s)
        if match is None:
            self.nonum += 1
            return 0, s
        num = match[1]
        index = s.index(match[1])
        return int(num), s[index + len(num):].strip()

    # def match_adresse_string(self, adresse):
    #     s = unidecode.unidecode(adresse.upper()).replace("'", " ").replace("-", " ").replace(".", "")
    #     s = s.replace("ST ", "SAINT ").replace("/", " ").strip()
    #     if "BP" in s:
    #         self.nbbp += 1
    #     regex = r"(\d{5})"
    #     match = re.findall(regex, s)
    #     if len(match) > 0:
    #         cp = match[-1]
    #         index = s.find(cp)
    #         commune = s[index + len(cp):].strip()
    #         cp = int(cp)
    #         s = s[:index]
    #         num = 0
    #         keys = ["RUE", "AVENUE", "AV ", "PLACE", "PL ", "CHEMIN", "CH ", "BD ", "BOULEVARD", "IMPASSE", "ZA ",
    #                 "ZI ", "ROUTE", "ZAE "]
    #         index = self.find_multiple(keys, s)
    #         street = s.strip()
    #         ss = s if index == -1 else s[:index]
    #         if index != -1:
    #             street = s[index:].strip()
    #         regex = r"(\d+)"
    #         match = re.findall(regex, ss)
    #         if len(match) > 0:
    #             num = match[-1].strip()
    #             index = s.find(num) + len(num)
    #             street = s[index:].strip()
    #             num = int(num)
    #         rep = ""
    #         if len(street) > 1 and street[1] == " ":
    #             rep = street[0]
    #             street = street[1:].strip()
    #         if street.startswith("BIS") or street.startswith("TER"):
    #             rep = street[:3]
    #             street = street[3:].strip()
    #         return cp, commune, num, street, rep
    #     else:
    #         return None

    def find_multiple(self, keys, s):
        for k in keys:
            if k in s:
                return s.find(k)
        return -1

    def load_adresses(self, dept):
        s = f"{dept:02d}"
        if dept == 201:
            s = "2A"
        if dept == 202:
            s = "2B"
        if dept > 970:
            s = str(dept)
        indexdb = cyrilload.load(f"{config.adresse_path}/adresses-{s}.pickle")
        self.db = indexdb["db"]
        self.communes_db = indexdb["communes"]
        self.cps_db = indexdb["cps"]
        print(f"Load adresses-{s}.pickle in {int(time.perf_counter() - time0)}s")

    def match_cp(self, cp, commune):
        # cp = special.cp_cedex(cp)
        if cp in self.cps_db:
            return cp, 1
        # elif 75100 <= cp < 75200:
        #     self.nbbadcp += 1
        #     cp, score = self.match_cp(cp - 100, commune)
        #     return cp, 0.9
        else:
            self.nbbadcp += 1
            print(f"WARNING BAD CP row {self.numrow}: {cp}")
            return 0, 0
            # res = self.find_nearest_less_cp(cp)
            # score = 0.8 if "CEDEX" in commune else 0.5
            # # print(f"Warning CP {cp}=>{res} {int(score*100)}%")
            # return res, score

    def match_commune(self, commune, communes, cp):
        # commune = special.commune(cp, commune)
        if commune in communes:
            return commune, 1
        else:
            print(f"WARNING BAD COMMUNE row {self.numrow}: {commune}")
            self.nbbadcommune += 1
            return 0, 0
            #return self.gestalts(commune, communes)

    def normalize_street(self, street):
        street = street.replace("CH ", "CHEMIN ").replace("AV ", "AVENUE ").replace("PL ", "PLACE ")
        street = street.replace("BD ", "BOULEVARD ")
        return street

    def normalize_commune(self, commune):
        commune = commune.replace("'", " ").replace("-", " ").replace(".", "")
        commune = commune.replace("ST ", "SAINT ").replace("/", " ").replace("CEDEX", "").strip()
        return commune

    def match_street(self, commune, adresse3, adresse4, cp):
        street = adresse3
        if adresse4 != "":
            street += " " + adresse4
        # street = special.street(cp, street)
        ids = self.communes_db[commune]
        entities = [self.db[id] for id in ids]
        adresses = [e.nom_afnor for e in entities if e.code_postal == cp]
        adresses_voie = [e.nom_voie for e in entities if e.code_postal == cp]
        if street == "":
            self.nbnostreet += 1
            street = "PLACE MAIRIE EGLISE"
        if street in adresses:
            return street, 1
        if street in adresses_voie:
            index = adresses_voie.index(street)
            return adresses[index], 1
        # street_res, score = self.gestalts(street, adresses)
        # if score > 0.9:
        #     return street_res, score
        # street2_res, score2 = self.gestalts(street, adresses_voie)
        # if score + 0.1 > score2:
        #     return street_res, score
        # index = adresses_voie.index(street2_res)
        # return adresses[index], score2
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
                    return 0, 1
                else:
                    return num, 0.8
            else:
                return 0, 0
        else:
            founds = [e.numero for e in entities if e.nom_afnor == adresse and e.numero == num]
            if len(founds) > 0:
                return num, 1
            else:
                nums = [e.numero for e in entities if e.nom_afnor == adresse]
                # res = self.find_nearest_num(num, nums)
                # if res == 0:
                #     return 0, 1
                # else:
                #     return res, 0.5
                return 0, 1

    def get_cp_by_commune(self, commune, oldcp):
        if commune in self.communes_db:
            ids = self.communes_db[commune]
            dept = str(oldcp)[:2] if oldcp >= 10000 else "0" + str(oldcp)[:1]
            for id in ids:
                e = self.db[id]
                if e.commune == commune and str(e.code_postal)[:2] == dept:
                    return e.code_postal, 1
                if (e.commune.startswith(commune) or e.commune.endswith(commune)) and str(e.code_postal)[:2] == dept:
                    return e.code_postal, 0.9
        return oldcp, 0

    def row2entity(self, entity, row):
        entity.tel = row[9]
        entity.genre = row[0]
        entity.prenom = row[2]
        entity.nom = row[1]
        for i in range(33):
            entity.values.append(row[i])

    def load_ps(self, dept):
        self.cps_db[0] = [] #TO REMOVE
        file = "data/ps/ps-tarifs-small.csv"
        file = "data/ps/ps-tarifs-21-03.csv"
        self.psentities = []
        with open(file) as f:
            reader = csv.reader(f, delimiter=";")
            self.numrow = 1
            for row in reader:
                self.numrow += 1
                cp = int(row[7])
                if cp < 1000 or cp > 99999:
                    print(f"ERROR CP row {self.numrow}: {cp}")
                if ((dept * 1000) <= cp < (dept + 1) * 1000 and cp != 201 and cp != 202) or \
                        (dept == 201 and 20000 <= cp < 20200) or \
                        (dept == 202 and 20200 <= cp < 21000):
                    self.nb += 1
                    entity = entities.PSEntity()
                    if self.nb % 100 == 0:
                        print(f"Parse {self.nb} PS in {int(time.perf_counter() - time0)}s")
                    commune = self.normalize_commune(row[8])
                    entity.cp, score = self.match_cp(cp, commune)
                    entity.scores.append(score)
                    communes = self.cps_db[entity.cp]
                    entity.commune, score = self.match_commune(commune, communes, entity.cp)
                    entity.scores.append(score)
                    if entity.commune != 0: #TO REMOVE
                        adresse3 = self.normalize_street(row[5])
                        num, entity.adresse3 = self.split_num(adresse3)
                        entity.adresse1 = row[3]
                        entity.adresse2 = row[4]
                        entity.adresse4 = row[6]
                        self.row2entity(entity, row)
                        # cp, commune, street = special.cp_commune_adresse(cp, commune, street)
                        # if score < 0.75:
                        #     cp, score = self.get_cp_by_commune(commune, entity.code_postal)
                        #     if cp != entity.code_postal:
                        #         print(f"[{self.numrow}] Warning Bad CP {entity.code_postal}=>{cp} {commune}")
                        #         entity.code_postal = cp
                        #         entity.commune = commune
                        #         entity.scores[-1] = score
                        #         entity.scores[-2] = 0.5
                        #     else:
                        #         print(
                        #             f"[{self.numrow}] Warning commune {entity.code_postal} {commune}=>{entity.commune} @{int(score * 100)}%")
                        entity.matchstreet, score = self.match_street(entity.commune, entity.adresse3, entity.adresse4, entity.cp)
                        entity.scores.append(score)
                        if score < 0.5:
                            self.nbscorelow += 1
                            # print(f"Warning street {street}=>{entity.nom_afnor} @{int(score * 100)}% {entity.code_postal} {entity.commune} ")
                        else: # TO REMOVE
                            entity.num, score = self.match_num(entity.commune, entity.matchstreet, num)
                            entity.scores.append(score)
                            if entity.score < 0.8:
                                self.nbscorelow += 1
                                #print(f"[{self.numrow}] Score: {int(entity.score * 100)}% ({(self.nbscorelow / self.nb) * 100:.1f}%) {entity.num} {entity.commune} {entity.cp} {entity.matchstreet} vs {entity.adresse3}")
                            ids = self.communes_db[entity.commune]
                            found = [self.db[id].id for id in ids if self.db[id].numero == entity.num and self.db[id].nom_afnor == entity.matchstreet]
                            if len(found) > 0:
                                entity.adresseid = found[0]
                                entity.lon = self.db[entity.adresseid].lon
                                entity.lat = self.db[entity.adresseid].lat
                                print(f"Lon: {entity.lon} Lat: {entity.lat}")
                                entity.x = self.db[entity.adresseid].x
                                entity.y = self.db[entity.adresseid].y
                                entity.code_insee = self.db[entity.adresseid].code_insee
                                entity.matchadresse = f"{self.db[entity.adresseid].numero} "
                                entity.matchadresse += f"{self.db[entity.adresseid].nom_afnor} "
                                entity.matchadresse += f"{self.db[entity.adresseid].code_postal} "
                                entity.matchadresse += self.db[entity.adresseid].commune
                                self.psentities.append(entity)
                            else:
                                print(f"[{self.numrow}] ERROR UNKNOWN {entity.adresse3}")
                                # input("Press Enter")
                                self.nberror500 += 1

        print(f"Nb PS: {self.nb}")
        print(f"Nb No num: {self.nonum} {(self.nonum / self.nb) * 100 : .1f}%")
        print(f"Nb Bad CP: {self.nbbadcp} {(self.nbbadcp / self.nb) * 100 : .1f}%")
        print(f"Nb Commune not found: {self.nbbadcommune} {(self.nbbadcommune / self.nb) * 100 : .1f}%")
        print(f"Nb No Street: {self.nbnostreet} {(self.nbnostreet / self.nb) * 100 : .1f}%")
        print(f"Nb Bad Street: {self.nbbadstreet} {(self.nbbadstreet / self.nb) * 100 : .1f}%")
        print(f"Nb Bad Num: {self.nbscorelow} {(self.nbscorelow / self.nb) * 100 : .1f}%")

    def load_by_depts(self, depts=None):
        if depts is None:
            depts = list(range(1, 21)) + list(range(21, 96)) + [201, 202]
        for dept in depts:
            print(f"Load dept {dept}")
            l.load_adresses(dept)
            l.load_ps(dept)

    def save_entities(self):
        with open("data/res.csv","w") as f:
            for e in self.psentities:
                # f.write(f"{e.genre};{e.nom};{e.prenom};")
                # f.write(f"{e.adresse1};{e.adresse2};{e.adresse3};{e.adresse4}")
                # f.write(f"{e.cp};{e.commune};")
                for i in range(31):
                    f.write(f"{e.values[i]};")
                f.write(f"{e.adresseid};{e.matchadresse};{e.code_insee};{e.lon};{e.lat};{e.x};{e.y}\n")


if __name__ == '__main__':
    print("Adresses Matcher")
    print(f"V{config.version}")
    print()
    parser = argparse.ArgumentParser(description="Adresses Matcher")
    parser.add_argument("-d", "--dept", help="Departments list in python format, eg [5,38,06]")
    args = parser.parse_args()
    l = AdresseMatcher()
    if args.dept is None:
        l.load_by_depts([1])
    else:
        l.load_by_depts(eval(args.dept))
    l.save_entities()

    # 01 100s
    # Nb PS: 19766
    # Nb No num: 3568  18.1%
    # Nb Bad CP: 601  3.0%
    # Nb Commune not found: 718  3.6%
    # Nb No Street: 13  0.1%
    # Nb Bad Street: 8518  43.1%
    # Nb Bad Num: 8518  43.1%

    # 38
    # Nb PS: 48927
    # Nb No num: 3491  7.1%
    # Nb Bad CP: 2181  4.5%
    # Nb Commune not found: 2649  5.4%
    # Nb No Street: 11  0.0%
    # Nb Bad Street: 15776  32.2%
    # Nb Bad Num: 15776  32.2%

# Pb et solutions
# Pas d'entête de colonne => en rajouter : 0.1j
# Rapidité => Indexation par pickle (cp, commune, rue) : 0.5j
# Pb de RAM : Gérer le fichier adresse-france en indexation nécessite > 16Go de RAM => Gestion par département : 0.5j
# Matching Commune => Pattern matching + score fiabilité : 0.5j
# Matching Rue => Pattern matching uniquement sur les adresses du CP, prendre la + proche + score fiabilité : 0.5j
# 2A 2B : 0.1j
# Gestion des anciens noms de communes => 1 commune peut avoir 3 valeurs: nom_commune, nom_ancienne_commune, libelle_acheminement : 0.1j
# Gestion des anciennes adresses => 1 adresse peut avoir 2 valeurs: nom_voie, nom_afnor, (lieux-dits?) : 0.1j
# Rue uniquement adresse3 tenir compte de adresse2 et 4 : 0.25j
# CEDEX => Gestion du CP le plus proche en dessous sauf 75 : 0.1j
# Si mauvais CP + Mauvaise commune chercher d'abord la commune puis déduire le CP : 0.25j
# Si mauvais num chercher le + proche : 0.1j
# Département ruraux : pas de numéro, gestion des lieux dits : 1j
# Mise en prod : 0.25j
# Réunions : 2*0.25j
