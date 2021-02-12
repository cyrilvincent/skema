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
        self.db: Dict[str, entities.AdresseEntity] = {}
        self.i = 0
        self.communes: Dict[str, Set[str]] = {}
        self.cps: Dict[str, Set[str]] = {}
        self.indexdb = {"db": self.db, "cps": self.cps, "communes": self.communes}

    def scan(self):
        print(f"Scan {config.adresse_path}")
        for item in os.listdir(config.adresse_path):
            if item.endswith(".csv"):
                self.load(f"{config.adresse_path}/{item}")

    def load(self, path):
        print(f"Load {path}")
        with open(path, encoding="utf8") as f:
            self.i += 1
            reader = csv.DictReader(f, delimiter=';')
            for row in reader:
                e = entities.AdresseEntity(row["id"])
                e.numero = int(row["numero"])
                e.rep = row["rep"]
                e.nom_afnor = row["nom_afnor"]
                e.nom_voie = unidecode.unidecode(row["nom_voie"].upper()).replace("'", " ").replace("-", " ").replace("ST ","SAINT ")
                e.code_insee = int(row["code_insee"])
                e.commune = row["libelle_acheminement"].replace("'", " ").replace("-", " ").replace("ST ","SAINT ")
                if e.commune.endswith("(LE)"):
                    e.commune = "LE "+e.commune[:-4]
                if e.commune.endswith("(LA)"):
                    e.commune = "LA "+e.commune[:-4]
                e.lon = float(row["lon"])
                e.lat = float(row["lat"])
                if e.commune not in self.communes:
                    self.communes[e.commune] = set()
                self.communes[e.commune].add(e.id)
                e.commune_old = unidecode.unidecode(row["nom_ancienne_commune"].upper()).replace("'", " ").replace("-", " ").replace("ST ","SAINT ")
                if e.commune_old != "" and e.commune_old != e.commune:
                    if e.commune_old not in self.communes:
                        self.communes[e.commune_old] = set()
                    self.communes[e.commune_old].add(e.id)
                e.code_postal = int(row["code_postal"])
                if e.code_postal not in self.cps:
                    self.cps[e.code_postal] = set()
                if e.commune not in self.cps[e.code_postal]:
                    self.cps[e.code_postal].add(e.commune)
                if e.commune_old != "" and e.commune_old != e.commune:
                    if e.commune_old not in self.cps[e.code_postal]:
                        self.cps[e.code_postal].add(e.commune_old)
                self.db[e.id] = e
        self.log()

    def save(self):
        cyrilload.save(self.indexdb, f"{config.adresse_path}/adresses", method="pickle")


    def log(self):
        span = time.perf_counter() - time0 + 1e-5
        s = f"Found {self.i} files and {len(self.db)} adresses in {int(span)}s"
        print(s)


if __name__ == '__main__':
    print("Adresse2Pickle")
    print("==============")
    print(f"V{config.version}")
    print()
    time0 = time.perf_counter()
    p = AdresseParser()
    p.scan()
    p.save()
