import entities
import config
import cyrilload
import art
import csv
import pandas
import argparse
from typing import List, Dict, Tuple


class PSRepository:
    """
    Repository PS
    """

    def save_entities(self, path, pss: List[entities.PSEntity], nbcolumn=0):
        """
        Sauvegarde une liste de PS dans un CSV
        :param path: le CSV
        :param pss: la liste de PS
        :param nbcolumn: nombre de colonne
        """
        print(f"Save {path}")
        with open(path, "w") as f:
            for e in pss:
                nbcolumn = len(e.v) if nbcolumn == 0 else nbcolumn
                for i in range(nbcolumn):
                    if i != 0:
                        f.write(";")
                    f.write(f"{e.v[i]}")
                f.write("\n")

    def row2entity(self, entity: entities.PSEntity, row: str):
        """
        Convertis une ligne CSV en une entité PS
        :param entity: PS
        :param row: ligne CSV
        """
        for i in range(len(row)):
            entity.v[i] = row[i]
        entity.updateid()

    def test_file(self, path):
        """
        Teste le fichier
        :param path: le fichier
        :return: le nombre de ligne
        """
        i = 0
        with open(path) as f:
            for _ in f:
                i += 1
        return i

    def load_ps(self, file: str):
        """
        Load PS file
        :param file: the path
        """
        with open(file) as f:
            reader = csv.reader(f, delimiter=";")
            return list(reader)

    def get_dataframe(self, path: str) -> pandas.DataFrame:
        """
        Load PS as dataframe
        :param path: path
        :return: dataframe
        """
        dataframe = pandas.read_csv(path, delimiter=";", header=None, encoding="cp1252",
                                    dtype={14: str, 37: str, 43: int})
        return dataframe

    def save_csv_from_dataframe(self, dataframe: pandas.DataFrame, path: str):
        """
        Save dataframe as CSV
        :param dataframe: dataframe
        :param path: path
        """
        dataframe.to_csv(path, header=False, index=False, sep=";")


class AdresseRepository:
    """
    Adresse Repository
    """

    def load_adresses(self, dept: int):
        """
        Charge le pickle adresse
        :param dept: département pickle à charger
        :return: Le tuple d'index db, communes, cps voir adresses2pickles
        """
        s = f"{dept:02d}"
        if dept == 201:
            s = "2A"
        if dept == 202:
            s = "2B"
        if dept > 970:
            s = str(dept)
        indexdb = cyrilload.load(f"{config.adresse_path}/adresses-{s}.pickle")
        return indexdb["db"], indexdb["communes"], indexdb["cps"], indexdb["insees"]

    def load_cedex(self) -> Dict:
        """
        Charge Cedex
        :return: le dictionnaire
        """
        return cyrilload.load(config.cedex_path)

    def save_adresses_db(self, db: Dict[Tuple[str, str, str, str], entities.AdresseDbEntity]):
        """
        Sauvegarde le dict d'adresse en CSV
        :param db: le dict
        """
        print(f"Save {config.adresse_db_path}")
        with open(config.adresse_db_path, "w") as f:
            f.write("cp;commune;adresse2;adresse3;adresseid;score;source;lon;lat;matchcp\n")
            l = list(db.values())
            l.sort(key=lambda a: a.score)
            for v in l:
                # f.write(f"{k[0]};{k[1]};{k[3]};{k[2]};")
                # v = db[k]
                # f.write(f"{v[0]};{v[1]};{v[2]};{v[3]};{v[4]};{v[5]}\n")
                f.write(f"{v.cp};{v.commune};{v.adresse2};{v.adresse3};{v.adresseid};{v.score};{v.source};")
                f.write(f"{v.lon};{v.lat};{v.matchcp}\n")

    def load_adresses_db(self) -> Dict[Tuple[str, str, str, str], entities.AdresseDbEntity]:
        """
        Charge l'adresse db depuis CSV
        :return: la DB
        """
        db = {}
        try:
            with open(config.adresse_db_path) as f:
                reader = csv.DictReader(f, delimiter=";")
                for row in reader:
                    v = entities.AdresseDbEntity(row["cp"], row["commune"], row["adresse3"], row["adresse2"],
                                                 row["adresseid"], float(row["score"]), row["source"],
                                                 float(row["lon"]), float(row["lat"]), row["matchcp"])
                    # cp = row["cp"]
                    # k = cp, row["commune"], row["adresse3"], row["adresse2"]
                    # score = float(row["score"])
                    # v = row["adresseid"], score, row["source"], float(row["lon"]), float(row["lat"]), row["matchcp"]
                    # db[k] = v
                    db[v.key] = v
        except FileNotFoundError:
            print(f"{config.adresse_db_path} does not exist")
        return db


class UFCRepository:

    def load_ufc(self, path: str) -> Tuple[pandas.DataFrame, pandas.DataFrame]:
        dataframe = pandas.read_excel(path)
        adataframe = pandas.read_excel(path, 4)
        return (dataframe, adataframe)

class SSRepository:

    def load_ss(self, path: str) -> pandas.DataFrame:
        dataframe = pandas.read_excel(path)
        return dataframe


if __name__ == '__main__':
    art.tprint(config.name, "big")
    print("Test PS file")
    print("============")
    print(f"V{config.version}")
    print(config.copyright)
    parser = argparse.ArgumentParser(description="Test PS file")
    parser.add_argument("path", help="Path")
    args = parser.parse_args()
    print(f"Parse {args.path}")
    repo = PSRepository()
    df = repo.get_dataframe(args.path)
    print(df)
