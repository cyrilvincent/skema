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
        self.cps: Dict[int, Set[str]] = {}
        self.indexdb = None
        self.nb = 0
        self.numrow = 0

    def scan(self):
        """
        Scan directory config.adresse_path
        """
        print(f"Scan {config.adresse_path}")
        for item in os.listdir(config.adresse_path):
            if item.endswith(".csv") and item.startswith("adresses-"):
                self.load(f"{config.adresse_path}/{item}")

    def normalize(self, s: str):
        """
        Normalise la commune
        :param s: la commune
        :return:
        """
        s = unidecode.unidecode(s.upper()).replace("'", " ").replace("-", " ").replace("/", " ")
        if s.endswith("(LE)"):
            s = "LE "+s[:-4]
        elif s.endswith("(LA)"):
            s = "LA "+s[:-4]
        return s.strip()

    def load(self, path: str):
        """
        Charge le fichier
        :param path: le chemin
        """
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
                if e.commune_old == "":
                    e.commune_old = self.normalize(row["libelle_acheminement"])
                e.lon = float(row["lon"])
                e.lat = float(row["lat"])
                e.code_insee = row["code_insee"]
                e.x = float(row["x"])
                e.y = float(row["y"])
                self.make_index(e)
        print(f"Found {self.nbfile} files and {len(self.db)} adresses in {int(time.perf_counter() - time0)}s")
        cyrilload.save(self.indexdb, path.replace(".csv", ""), method="pickle")

    def make_index(self, e: entities.AdresseEntity):
        """
        Crée l'index cp => commune => AdresseEntity
        :param e: l'entité
        """
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
    print("Adresses 2 Pickles")
    print("==================")
    print(f"V{config.version}")
    print()
    time0 = time.perf_counter()
    p = AdresseParser()
    p.scan()
    print(f"Create {p.nbfile // 1} pickles in {int(time.perf_counter() - time0)}s")
