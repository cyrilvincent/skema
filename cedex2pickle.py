import config
import time
import csv
import cyrilload
import entities
import argparse
from typing import Dict


class CedexParser:

    def __init__(self):
        self.db: Dict[int, entities.CedexEntity] = {}
        self.nb = 0

    def normalize_commune(self, commune: str) -> str:
        """
        Normalise la commune
        :param commune: commune
        :return: la commune normalisée
        """
        if "CEDEX" in commune:
            index = commune.index("CEDEX")
            commune = commune[:index]
        commune = commune.replace("'", " ").replace("-", " ")
        commune = " " + commune
        commune = commune.replace(" ST ", " SAINT ").replace(" STE ", " SAINTE ")
        return commune.strip()

    def load(self, path: str):
        """
        Charge le fichier csv, créer les indexs, sauvegarde le pickle
        :param path: le chemin
        """
        print(f"Load {path}")
        with open(path, encoding="utf8") as f:
            reader = csv.DictReader(f, delimiter=';')
            for row in reader:
                self.nb += 1
                cp = int(row["cedex"])
                e = entities.CedexEntity(cp)
                e.commune = self.normalize_commune(row["libelle"])
                e.code_insee = row["insee"]
                self.db[cp] = e
        cyrilload.save(self.db, path.replace(".csv", ""), method="pickle")


if __name__ == '__main__':
    print("Cedex 2 Pickle")
    print("==============")
    print(f"V{config.version}")
    print(config.copyright)
    print()
    time0 = time.perf_counter()
    parser = argparse.ArgumentParser(description="Cedex 2 Pickle")
    parser.add_argument("path", help="Path")
    args = parser.parse_args()
    p = CedexParser()
    p.load(args.path)
    print(f"Save {p.nb} cedex adresses in pickle in {int(time.perf_counter() - time0)}s")
