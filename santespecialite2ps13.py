import art
import config
import argparse
import repositories
import pandas
import entities
import numpy as np
from typing import List, Tuple, Optional


class SanteSpecialiteParser:

    def __init__(self, path):
        self.repo = repositories.SSRepository()
        self.ps_repo = repositories.PSRepository()
        self.path = path
        self.dataframe: Optional[pandas.DataFrame] = None
        self.entities: List[entities.PSEntity] = []

    def load(self):
        print(f"Load {self.path}")
        self.dataframe = self.repo.load_ss(self.path)

    def split_nom(self, s: str) -> Tuple[str, str]:
        nom = s
        prenom = ""
        if " " in s:
            index = s.rindex(" ")
            nom = s[:index]
            prenom = s[index+1:]
        return nom, prenom

    def parse(self):
        print("Parse")
        for index, row in self.dataframe.iterrows():
            e = entities.PSEntity()
            e.rownum = index + 1
            e.v[7] = row["CP"]
            e.v[8] = row["Ville"].strip().replace("_x000D_", "")
            e.v[1], e.v[2] = self.split_nom(row["Nom"].strip())
            e.v[10] = self.get_profession(row["Specialite"].strip())
            e.v[13] = self.get_secteur(row["Secteur"])
            e.v[18] = int(np.round(row[15])) if str(row[15]) != "nan" else ""
            e.v[19] = int(np.round(row[13])) if str(row[13]) != "nan" else ""
            e.v[20] = int(np.round(row[14])) if str(row[14]) != "nan" else ""
            self.entities.append(e)

    def save(self):
        file = self.path
        if "\\" in self.path:
            index = self.path.rindex("\\")
            file = self.path[:index + 1]
            source = self.path[index + 1:]
            index = source.rindex(".")
            source = source[:index]
        file += f"ps-tarifs-13-00-{source}.csv"
        self.ps_repo.save_entities(file, self.entities, entities.PSEntity.originalnb)

    def get_profession(self, s: str) -> int:
        s = s.strip()
        if s == "Pédiatre":
            return 60
        if s == "Gynécologue":
            return 37
        if s == "Ophtalmologue":
            return 56
        print(f"ERROR bad profession {s}")
        return 0

    def get_secteur(self, s) -> str:
        s = str(s).strip()
        if s == "NC":
            return "nc"
        return "c" + s


if __name__ == '__main__':
    art.tprint(config.name, "big")
    print("Sante Specialite 2 PS")
    print("=====================")
    print(f"V{config.version}")
    print(config.copyright)
    print()
    parser = argparse.ArgumentParser(description="Sante Specialite 2 PS")
    parser.add_argument("path", help="Path")
    args = parser.parse_args()
    p = SanteSpecialiteParser(args.path)
    p.load()
    p.parse()
    p.save()
