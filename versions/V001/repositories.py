import entities
import config
import cyrilload
import time
import csv
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
                for i in range(entities.PSEntity.nb):
                    f.write(f"{e.v[i]};")
                f.write("\n")

    def row2entity(self, entity: entities.PSEntity, row: str):
        """
        Convertis une ligne CSV en une entité PS
        :param entity: PS
        :param row: ligne CSV
        """
        for i in range(entities.PSEntity.originalnb):
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


class AdresseRepository:
    """
    Adresse Repository
    """

    def load_adresses(self, dept: int, time0):
        """
        Charge le pickle adresse
        :param dept: département pickle à charger
        :param time0: le temps 0
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
        print(f"Load adresses-{s}.pickle in {int(time.perf_counter() - time0)}s")
        return indexdb["db"], indexdb["communes"], indexdb["cps"]


if __name__ == '__main__':
    print("Test PS file")
    print("============")
    print(f"V{config.version}")
    print(config.copyright)
    file = "data/ps/ps-tarifs-small-00-00.csv"
    print(f"Parse {file}")
    repo = PSRepository()
    nb = repo.test_file(file)
    print(f"Found {nb} rows")
