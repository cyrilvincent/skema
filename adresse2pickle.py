import config
import os
import time
import csv
import cyrilload
import unidecode
import entities
from typing import Dict, Set


class AdresseParser:

    def __init__(self):
        self.nbfile = 0
        self.db: Dict[str, entities.AdresseEntity] = {}
        self.communes: Dict[str, Set[str]] = {}
        self.cps: Dict[str, Set[str]] = {}
        self.indexdb = None
        self.nb = 0
        self.numrow = 0

    def scan(self):
        print(f"Scan {config.adresse_path}")
        for item in os.listdir(config.adresse_path):
            if item.endswith(".csv") and item.startswith("adresses-"):
                self.load(f"{config.adresse_path}/{item}")

    def normalize(self, s):
        return unidecode.unidecode(s.upper()).replace("'", " ").replace("-", " ").replace("ST ", "SAINT ")

    def load(self, path):
        print(f"Load {path}")
        self.db = {}
        self.communes = {}
        self.cps = {}
        self.indexdb = {"db": self.db, "cps": self.cps, "communes": self.communes}
        self.numrow = 1
        with open(path, encoding="utf8") as f:
            self.nbfile += 1
            reader = csv.DictReader(f, delimiter=';')
            for row in reader:
                self.numrow += 1
                e = entities.AdresseEntity(row["id"])
                e.numero = int(row["numero"])
                e.rep = row["rep"]
                e.nom_afnor = row["nom_afnor"]
                e.nom_voie = self.normalize(row["nom_voie"])
                if e.nom_voie == e.nom_afnor:
                    e.nom_voie = ""
                e.commune = self.normalize(row["nom_commune"])
                e.code_postal = int(row["code_postal"])
                e.commune_old = self.normalize(row["nom_ancienne_commune"])
                e.lon = float(row["lon"])
                e.lat = float(row["lat"])
                e.code_insee = row["code_insee"]
                self.make_index(e)
        print(f"Found {self.nbfile} files and {len(self.db)} adresses in {int(time.perf_counter() - time0)}s")
        ldpath = path.replace('adresses-', 'lieux-dits-').replace('.csv', '-beta.csv')
        self.load_lieuxdits(ldpath)
        cyrilload.save(self.indexdb, path.replace(".csv", ""), method="pickle")

    def load_lieuxdits(self, path):
        self.nbfile += 1
        print(f"Load {path}")
        self.numrow = 1
        with open(path, encoding="utf8") as f:
            reader = csv.DictReader(f, delimiter=';')
            for row in reader:
                self.numrow += 1
                e = entities.AdresseEntity(row["id"])
                e.nom_afnor = self.normalize(row["nom_lieu_dit"])
                e.commune = self.normalize(row["nom_commune"])
                e.code_postal = int(row["code_postal"])
                e.commune_old = self.normalize(row["nom_ancienne_commune"])
                e.code_insee = row["code_insee"]
                try:
                    e.lon = float(row["lon"])
                    e.lat = float(row["lat"])
                except:
                    continue
                self.make_index(e)
        print(f"Found {self.nbfile} files and {len(self.db)} adresses in {int(time.perf_counter() - time0)}s")

    def make_index(self, e):
        if e.commune not in self.communes:
            self.communes[e.commune] = set()
        self.communes[e.commune].add(e.id)
        if e.commune_old != "" and e.commune_old != e.commune:
            if e.commune_old not in self.communes:
                self.communes[e.commune_old] = set()
            self.communes[e.commune_old].add(e.id)
        if e.code_postal not in self.cps:
            self.cps[e.code_postal] = set()
        if e.commune not in self.cps[e.code_postal]:
            self.cps[e.code_postal].add(e.commune)
        if e.commune_old != "" and e.commune_old != e.commune:
            if e.commune_old not in self.cps[e.code_postal]:
                self.cps[e.code_postal].add(e.commune_old)
        self.nb += 1
        self.db[e.id] = e

if __name__ == '__main__':
    print("Adresse2Pickle")
    print("==============")
    print(f"V{config.version}")
    print()
    time0 = time.perf_counter()
    p = AdresseParser()
    p.scan()
    print(f"Create {p.nb // 2} pickles in {int(time.perf_counter() - time0)}s")
