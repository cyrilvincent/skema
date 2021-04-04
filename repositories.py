import entities
import config
import cyrilload
import art
import csv
import pandas
import argparse
import shutil
from typing import List


class PSRepository:
    """
    Repository PS
    """

    def save_entities(self, path, pss: List[entities.PSEntity]):
        """
        Sauvegarde une liste de PS dans un CSV
        :param path: le CSV
        :param pss: la liste de PS
        """
        print(f"Save {path}")
        with open(path, "w") as f:
            for e in pss:
                for i in range(len(e.v)):
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

    def load_ps(self, file):
        with open(file) as f:
            reader = csv.reader(f, delimiter=";")
            return list(reader)

    def get_dataframe(self, path):
        dataframe = pandas.read_csv(path, delimiter=";", header=None, encoding="cp1252",
                                    dtype={14: str, 37: str, 43: int})
        return dataframe

    def save_csv_from_dataframe(self, dataframe, path):
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

    def load_cedex(self):
        return cyrilload.load(config.cedex_path)

    def save_adresses_db(self, db):
        print(f"Save {config.adresse_db_path}")
        with open(config.adresse_db_path, "w") as f:
            f.write("cp;commune;adresse2;adresse3;adresseid;score\n")
            for k in db.keys():
                f.write(f"{k[0]};{k[1]};{k[3]};{k[2]};")
                v = db[k]
                f.write(f"{v[0]};{v[1]}\n")

    def load_adresses_db(self):
        db = {}
        try:
            with open(config.adresse_db_path) as f:
                reader = csv.DictReader(f, delimiter=";")
                for row in reader:
                    k = row["cp"], row["commune"], row["adresse3"], row["adresse2"]
                    v = row["adresseid"], float(row["score"])
                    db[k] = v
        except FileNotFoundError:
            print(f"{config.adresse_db_path} does not exist")
        return db


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
