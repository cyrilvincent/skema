import art
import config
import argparse
import repositories
import pandas
import entities
import numpy as np
from typing import List, Tuple


class UFCParser:

    def __init__(self, path):
        self.repo = repositories.UFCRepository()
        self.ps_repo = repositories.PSRepository()
        self.path = path
        self.dataframe: pandas.DataFrame | None = None
        self.address_df: pandas.DataFrame | None = None
        self.entities: List[entities.PSEntity] = []

    def load(self):
        print(f"Load {self.path}")
        self.dataframe, self.address_df = self.repo.load_ufc(self.path)

    def parse(self):
        print("Parse")
        for index, row in self.dataframe.iterrows():
            e = entities.PSEntity()
            e.rownum = index + 1
            e.v[7] = row["CP"]
            e.v[8] = row["VILLE"]
            e.v[1] = row["NOM"]
            e.v[2] = row["PRENOM"]
            e.v[3], e.v[4], e.v[5] = self.get_adresse123_by_nom_prenom_cp(row["NOM"], row["PRENOM"], row["CP"])
            e.v[10] = self.get_profession(row["specialité"])
            e.v[12] = self.get_nature(row["Type d'activité"])
            e.v[13], e.v[14] = self.get_convention(row["SECTEUR"])
            v = row["Moyenne Départementale"]
            e.v[18] = int(np.round(v)) if str(v) != "nan" else ""
            e.v[19] = int(np.round(row["PRIXBas"])) if str(row["PRIXBas"]) != "nan" else ""
            e.v[20] = int(np.round(row["PRIXHaut"])) if str(row["PRIXHaut"]) != "nan" else ""
            self.entities.append(e)

    def save(self):
        file = self.path
        if "/" in self.path:
            index = self.path.rindex("/")
            file = self.path[:index + 1]
        file += "ps-tarifs-00-00-from-ufc.csv"
        self.ps_repo.save_entities(file, self.entities, entities.PSEntity.originalnb)

    def get_adresse123_by_nom_prenom_cp(self, nom: str, prenom: str, cp: str) -> Tuple[str, str, str]:
        df = self.address_df[(self.address_df.NOM == nom) &
                             (self.address_df.PRENOM == prenom) &
                             (self.address_df.CP == cp)]
        l = df.values.tolist()
        if len(l) == 0:
            print(f"ERROR no address for ID2016 {id}")
            return "", "", ""
        l = l[0]
        a1 = str(l[3])
        a2 = str(l[4])
        a3 = str(l[5])
        if a3 == "nan" or a3 == "":
            a3 = str(l[4])
            a2 = ""
            if a3 == "nan" or a3 == "":
                a3 = str(l[3])
                a1 = ""
                if a3 == "nan":
                    a3 = ""
        return a1, a2, a3

    def get_profession(self, s: str) -> int:
        if s == "Pédiatre":
            return 60
        print(f"ERROR bad profession {s}")
        return 0

    def get_nature(self, s: str) -> int:
        s = str(s).strip()
        if s == "Libéral intégral":
            return 3
        if s == "Temps partagé entre activité libérale et activité salariée (hors hôpital)":
            return 2
        if s == "Temps partagé entre activité libérale et activité hospitalière":
            return 4
        if s == "Hospitalier avec activité libérale au sein de l'hôpital":
            return 7
        if s == "Ce professionnel n'exerce pas actuellement":
            return 1
        if s == "nan":
            return 0
        print(f"ERROR bad nature {s}")
        return 0

    def get_convention(self, s) -> Tuple[str, str]:
        s = str(s).strip()
        if s == "Conventionné secteur 1":
            return "c1", "N"
        if s == "Conventionné secteur 1 avec contrat d'accès aux soins":
            return "c1", "O"
        if s == "Conventionné secteur 1 avec droit à dépassement permanent et contrat d'accès aux soins":
            return "c1", "O"
        if s == "Conventionné secteur 1 avec droit permanent à dépassement":
            return "c1", "N"
        if s == "Conventionné secteur 2":
            return "c2", "N"
        if s == "Conventionné secteur 2 avec contrat d'accès aux soins":
            return "c2", "O"
        if s == "nan":
            return "nc", "N"
        print(f"ERROR bad nature {s}")
        return "", ""




if __name__ == '__main__':
    art.tprint(config.name, "big")
    print("UFC 2 Rest")
    print("==========")
    print(f"V{config.version}")
    print(config.copyright)
    print()
    parser = argparse.ArgumentParser(description="UFC 2 PS")
    parser.add_argument("path", help="Path")
    args = parser.parse_args()
    p = UFCParser(args.path)
    p.load()
    p.parse()
    p.save()