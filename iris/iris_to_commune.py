import time
from sqlalchemy.orm import joinedload

from iris.commune_matrix import CommuneMatrixService
from sqlentities import Context, Commune, Iris, IrisMatrix, CommuneMatrix
import argparse
import art
import config


time0 = time.perf_counter()


class IrisToCommuneTransferer:

    def __init__(self, context, distance_max=100):
        self.context = context
        self.distance_max = distance_max
        self.nb_entity = 0
        self.total = 0
        self.commune_matrix_service = CommuneMatrixService(context, False)

    def get_commune_by_id(self, id: int) -> Commune:
        return self.context.session.get(Commune, id)

    def get_iris_matrix_by_ids(self, iris_id1: int, iris_id2: int) -> IrisMatrix:
        iris_matrix = (self.context.session.query(IrisMatrix)
                       .filter((IrisMatrix.iris_id_from == iris_id1) & (IrisMatrix.iris_id_to == iris_id2)).one())
        return iris_matrix

    def iris_matrix_to_commune_matrix(self, iris_matrix: IrisMatrix, commune_matrix: CommuneMatrix):
        commune_matrix.route_km = iris_matrix.route_km
        commune_matrix.route_min = iris_matrix.route_min
        commune_matrix.route_hp_min = iris_matrix.route_hp_min

    def iris_to_commune(self, iris: Iris, commune: Commune):
        delta = abs(commune.lon - iris.lon) + abs(commune.lat - iris.lat)
        if delta > 0.001:
            commune.lon = iris.lon
            commune.lat = iris.lat

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
        if dist_min < 0.75:
            return iris_min

    def find_mairie(self, commune: Commune) -> Iris | None:
        for iris in commune.iriss:
            if "MAIRIE" in iris.nom_norm or "HOTEL DE VILLE" in iris.nom_norm:
                return iris
        return None

    def transfer_not_irised(self, commune1: Commune, commune2: Commune, commune_matrix: CommuneMatrix):
        iris1 = commune1.iriss[0]
        iris2 = commune2.iriss[0]
        iris_matrix = self.get_iris_matrix_by_ids(iris1.id, iris2.id)
        if iris_matrix.route_km is not None:
            self.iris_matrix_to_commune_matrix(iris_matrix, commune_matrix)
            self.context.session.commit()

    def transfer_irised(self, commune1: Commune, commune2: Commune, commune_matrix: CommuneMatrix):
        iris1 = commune1.iriss[0]
        if len(commune1.iriss) > 1:
            iris1 = self.find_mairie(commune1)
            if iris1 is not None:
                self.iris_to_commune(iris1, commune1)
            else:
                iris1 = self.get_nearset_iris(commune1)
        iris2 = commune2.iriss[0]
        if len(commune2.iriss) > 1:
            iris2 = self.find_mairie(commune2)
            if iris2 is not None:
                self.iris_to_commune(iris2, commune2)
            else:
                iris2 = self.get_nearset_iris(commune2)
        if iris1 is not None and iris2 is not None:
            iris_matrix = self.get_iris_matrix_by_ids(iris1.id, iris2.id)
            if iris_matrix.route_km is not None:
                self.iris_matrix_to_commune_matrix(iris_matrix, commune_matrix)
                self.context.session.commit()

    def transfer(self):
        print("Transfer")
        l: list[CommuneMatrix] = (self.context.session.query(CommuneMatrix)
                                  .filter((CommuneMatrix.route_km.is_(None)) &
                                          (CommuneMatrix.direct_km.isnot(None)) &
                                          (CommuneMatrix.direct_km < self.distance_max)).all())
        self.total = len(l)
        print(f"Found {self.total} rows")
        for commune_matrix in l:
            self.nb_entity += 1
            commune1 = self.get_commune_by_id(commune_matrix.code_id_low)
            commune2 = self.get_commune_by_id(commune_matrix.code_id_high)
            if len(commune1.iriss) == 0 or len(commune2.iriss) == 0:
                continue
            elif len(commune1.iriss) == 1 and len(commune2.iriss) == 1:
                self.transfer_not_irised(commune1, commune2, commune_matrix)
            else:
                self.transfer_irised(commune1, commune2, commune_matrix)
            if self.nb_entity % 10000:
                duration = time.perf_counter() - time0
                print(f"Commited {self.nb_entity} ({(self.nb_entity / self.total) * 100:.2f} rows in {duration}s")


if __name__ == '__main__':
    art.tprint(config.name, "big")
    print("IRIS to Commune Transfer")
    print("========================")
    print(f"V{config.version}")
    print(config.copyright)
    print()
    parser = argparse.ArgumentParser(description="IRIS to Commune Transfer")
    parser.add_argument("-e", "--echo", help="Sql Alchemy echo", action="store_true")
    parser.add_argument("-d", "--distance_max", help="Distance max", type=int, default=100)
    args = parser.parse_args()
    context = Context()
    context.create(echo=args.echo, expire_on_commit=False)
    db_size = context.db_size()
    print(f"Database {context.db_name}: {db_size:.0f} MB")
    ict = IrisToCommuneTransferer(context, args.distance_max)
    ict.transfer()
