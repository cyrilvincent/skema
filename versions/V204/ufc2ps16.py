import art
import config
import argparse
import repositories
import pandas
import entities
import numpy as np
from typing import List, Tuple, Optional


class UFCParser:

    def __init__(self, path):
        self.repo = repositories.UFCRepository()
        self.ps_repo = repositories.PSRepository()
        self.path = path
        self.dataframe: Optional[pandas.DataFrame] = None
        self.address_df: Optional[pandas.DataFrame] = None
        self.entities: List[entities.PSEntity] = []

    def load(self):
        print(f"Load {self.path}")
        self.dataframe, self.address_df, _ = self.repo.load_ufc(self.path)

    def parse(self):
        print("Parsing")
        for index, row in self.dataframe.iterrows():
            e = entities.PSEntity()
            e.rownum = index + 1
            e.v[7] = row["CP"]
            e.v[8] = row["VILLE"]
            e.v[1] = row["NOM"]
            e.v[2] = row["PRENOM"]
            e.v[3], e.v[4], e.v[5] = self.get_adresse123_by_id2016(row["ID2016"])
            e.v[10] = self.get_profession(row["specialité"])
            e.v[12] = self.get_nature(row["Type d'activité"])
            e.v[13], e.v[14] = self.get_convention(row["SECTEUR"])
            v = row["PRIXFrequent"]
            e.v[18] = int(np.round(v)) if str(v) != "nan" else ""
            e.v[19] = int(np.round(row["PRIXBas"])) if str(row["PRIXBas"]) != "nan" else ""
            e.v[20] = int(np.round(row["PRIXHaut"])) if str(row["PRIXHaut"]) != "nan" else ""
            self.entities.append(e)

    def save(self):
        self.path = "./" + self.path
        index = self.path.rindex("/")
        file = self.path[:index + 1]
        source = self.path[index + 1:]
        index = source.rindex(".")
        source = source[:index]
        file += f"ps-tarifs-{source}-16-00.csv"
        self.ps_repo.save_entities(file, self.entities, entities.PSEntity.originalnb)

    def get_adresse123_by_id2016(self, id: str) -> Tuple[str, str, str]:
        df = self.address_df[self.address_df.ID2016 == id]
        l = df.values.tolist()
        if len(l) == 0:
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
        s = s.strip()
        if s == "Pédiatre":
            return 60
        if s == "Gynécologue Obstétricien":
            return 37
        if s == "Ophtalmologiste":
            return 56
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
        s = str(s).strip().replace("\r\n", "")
        res1, res2 = "nc", "N"
        if "secteur 1" in s:
            res1 = "c1"
        elif "secteur 2" in s:
            res1 = "c2"
        if "soins" in s:
            res2 = "O"
        return res1, res2


if __name__ == '__main__':
    art.tprint(config.name, "big")
    print("UFC 2 PS 2016")
    print("=============")
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

    # "data/UFC/UFC Santé_ Gynécologues 2016 v1-3.xlsx"
    # "data/UFC/UFC Santé, Pédiatres 2016 v1-3.xlsx"
    # "data/UFC/UFC Santé_ Ophtalmologistes 2016 v1-3.xlsx"
