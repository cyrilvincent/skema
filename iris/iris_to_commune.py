import time

from sqlalchemy import any_
from sqlalchemy.dialects.postgresql import Any
from sqlalchemy.orm import joinedload

from iris.commune_matrix import CommuneMatrixService
from sqlentities import Context, Commune, Iris, IrisMatrix, CommuneMatrix
import argparse
import art
import config


time0 = time.perf_counter()


class IrisToCommuneTransferer:

    def __init__(self, context):
        self.context = context
        self.nb_entity = 0
        self.total = 0
        self.commune_matrix_service = CommuneMatrixService(context)
        self.effective_commit = 0
        self.commune_iriss: dict[int, int] = {}
        self.nb_ram = 0

    def load_cache(self):
        l: list[Iris] = self.context.session.query(Iris).filter(Iris.is_main == True)
        for e in l:
            self.commune_iriss[e.commune_id] = e.id
            self.nb_ram += 1
        print(f"{self.nb_ram} objects in cache")

    def get_commune_by_id(self, id: int) -> Commune:
        return self.context.session.get(Commune, id)

    def get_iris_matrix_by_ids(self, iris_id1: int, iris_id2: int) -> IrisMatrix | None:
        iris_matrix = (self.context.session.query(IrisMatrix)
                       .filter((IrisMatrix.iris_id_from == iris_id1) & (IrisMatrix.iris_id_to == iris_id2)).first())
        return iris_matrix

    def iris_matrix_to_commune_matrix(self, iris_matrix: IrisMatrix, commune_matrix: CommuneMatrix):
        commune_matrix.route_km = iris_matrix.route_km
        commune_matrix.route_min = iris_matrix.route_min
        commune_matrix.route_hp_min = iris_matrix.route_hp_min

    def get_nearset_iris(self, commune: Commune) -> Iris | None:
        dist_min = 999
        iris_min = None
        for iris in commune.iriss:
            d = self.commune_matrix_service.compute_distance(commune.lon, commune.lat, iris.lon, iris.lat)
            if d < 0.1:
                return iris
            if d < dist_min:
                dist_min = d
                iris_min = iris
        return iris_min

    def transfer(self):
        # update iris.commune_matrix
        # set route_km = null, route_min = null, route_hp_min = null
        # where route_km is not null
        print("Transfer")
        l: list[CommuneMatrix] = (self.context.session.query(CommuneMatrix)
                                  .filter((CommuneMatrix.route_km.is_(None)) &
                                          (CommuneMatrix.direct_km.isnot(None))).all())
        #todo il y a 7294 rows vide à cause des 9999 faire un delete from iris.commune_matrix where od_km is null and direct_km
        #todo comprendre pourquoi il y a 120M de pairs et seulement 50% ont matchées
        #todo la seule explication à priori ce sont des pairs d'iris non trouvées car > 200km, mais il y seulement 500K od_km > 190
        # select * from iris.commune_matrix cm
        # left outer join iris.commune c1 on c1.id = cm.code_id_low
        # left outer join iris.commune c2 on c2.id = cm.code_id_high
        # left outer join iris.iris i1 on i1.commune_id = cm.code_id_low
        # left outer join iris.iris i2 on i2.commune_id = cm.code_id_high and i2.is_main = true
        # left outer join iris.iris_matrix im on im.iris_id_from = i1.id and im.iris_id_to = i2.id
        # where cm.direct_km is not null
        # and cm.route_km is null
        # and c1.parent is null
        # and c2.parent is null
        # and c1.type is null
        # and c2.type is null
        # --and cm.id = 6087624 -- normalement cet id doit avoir un route_km not null
        # limit 1000
        self.total = len(l)
        print(f"Found {self.total} rows")
        for commune_matrix in l:
            self.nb_entity += 1

            # commune1 = self.get_commune_by_id(commune_matrix.code_id_low)
            # commune2 = self.get_commune_by_id(commune_matrix.code_id_high)
            # iriss1 = [iris for iris in commune1.iriss if iris.is_main]
            # iris1 = iris2 = None
            # if len(iriss1) > 0:
            #     iris1 = iriss1[0]
            # iriss2 = [iris for iris in commune2.iriss if iris.is_main]
            # if len(iriss2) > 0:
            #     iris2 = iriss2[0]

            # todo il y a 7294 rows vide à cause des 9999 faire un delete from iris.commune_matrix where od_km is null and direct_km
            # todo comprendre pourquoi il y a 120M de pairs et seulement 50% ont matchées (rectif il y a 23M de pairs manquantes à 56%)
            # todo la seule explication à priori ce sont des pairs d'iris non trouvées car > 200km, mais il y seulement 500K od_km > 190

            iris1 = iris2 = None
            if commune_matrix.code_id_low in self.commune_iriss:
                iris1 = self.commune_iriss[commune_matrix.code_id_low]
            if commune_matrix.code_id_high in self.commune_iriss:
                iris2 = self.commune_iriss[commune_matrix.code_id_high]

            if iris1 is not None and iris2 is not None:
                iris_matrix = self.get_iris_matrix_by_ids(iris1, iris2)
                if iris_matrix is not None and iris_matrix.route_km is not None:
                    self.iris_matrix_to_commune_matrix(iris_matrix, commune_matrix)
                    self.effective_commit += 1
                else:
                    pass # why for direct_km < 200 ?
            if self.nb_entity % 1000 == 0 or self.nb_entity == self.total:
                self.context.session.commit()
                duration = time.perf_counter() - time0
                print(f"Commited {self.effective_commit/self.nb_entity} rows ({(self.nb_entity / self.total) * 100:.2f}%) in {int(duration)}s")

    def compute_iris_mains(self):
        print("Compute Iris mains")
        l: list[Commune] = (self.context.session.query(Commune).options(joinedload(Commune.iriss))
                            .filter(Commune.iriss.any(Iris.is_main.is_(None)))).all()
        self.total = len(l)
        print(f"Found {self.total} rows")
        for commune in l:
            self.nb_entity += 1
            if len(commune.iriss) == 1:
                commune.iriss[0].is_main = True
            elif len(commune.iriss) > 1:
                for iris in commune.iriss:
                    iris.is_main = False
                iris = self.get_nearset_iris(commune)
                iris.is_main = True
            if self.nb_entity % 1000 == 0 or self.nb_entity == self.total:
                duration = time.perf_counter() - time0
                print(f"Commited {self.nb_entity} rows ({(self.nb_entity / self.total) * 100:.1f}%) in {int(duration)}s")
                self.context.session.commit()



if __name__ == '__main__':
    art.tprint(config.name, "big")
    print("IRIS to Commune Transfer")
    print("========================")
    print(f"V{config.version}")
    print(config.copyright)
    print()

    parser = argparse.ArgumentParser(description="IRIS to Commune Transfer")
    parser.add_argument("-e", "--echo", help="Sql Alchemy echo", action="store_true")
    args = parser.parse_args()
    context = Context()
    context.create(echo=args.echo, expire_on_commit=False)
    db_size = context.db_size()
    print(f"Database {context.db_name}: {db_size:.0f} MB")
    ict = IrisToCommuneTransferer(context)
    # ict.compute_iris_mains()
    ict.transfer()
