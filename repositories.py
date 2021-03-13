import entities
import config
import cyrilload
import time


class PSRepository:

    def save_entities(self, path, pss):
        print(f"Save {path}")
        with open(path, "w") as f:
            for e in pss:
                for i in range(entities.PSEntity.nb):
                    f.write(f"{e.v[i]};")
                f.write("\n")

    def row2entity(self, entity, row):
        for i in range(entities.PSEntity.originalnb):
            entity.v[i] = row[i]
        entity.updateid()

    def test_file(self, path):
        i = 0
        with open(path) as f:
            for _ in f:
                i += 1
        return i


class AdresseRepository:

    def load_adresses(self, dept, time0):
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
    file = "data/ps/ps-tarifs-small.csv"
    print(f"Parse {file}")
    repo = PSRepository()
    nb = repo.test_file(file)
    print(f"Found {nb} rows")
