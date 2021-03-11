import entities
import config

class PSRepository:

    def save_entities(self, path, pss):
        with open("data/res.csv","w") as f:
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
        with open("data/ps/ps-tarifs-small.csv") as f:
            for _ in f:
                i+=1
        return i


if __name__ == '__main__':
    print("Test PS file")
    print("============")
    print(f"V{config.version}")
    print("Parse data/ps/ps-tarifs-small.csv")
    repo = PSRepository()
    nb = repo.test_file("")
    print(f"Found {nb} rows")
