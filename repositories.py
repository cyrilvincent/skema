import entities

class PSRepository:

    def save_entities(self, pss):
        with open("data/res.csv","w") as f:
            for e in pss:
                for i in range(entities.PSEntity.nb):
                    f.write(f"{e.v[i]};")
                f.write("\n")

    def row2entity(self, entity, row):
        for i in range(entities.PSEntity.originalnb):
            entity.v[i] = row[i]
        entity.updateid()