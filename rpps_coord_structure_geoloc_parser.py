import datetime
from typing import Dict, List
from sqlalchemy.orm import joinedload
from rpps_coord_corresp_parser import RPPSCoordPersonneParser
from sqlentities import Context, Dept, Coord, AdresseNorm, Structure, Source
from base_parser import time0
import argparse
import time
import art
import config


class RPPSCoordStructureGeolocParser(RPPSCoordPersonneParser):

    def __init__(self, context):
        super().__init__(context)
        self.structures: Dict[str, Structure] = {}
        self.sources: Dict[int, Source] = {}
        self.no_coord = 0
        self.nb_score_improvment = 0
        self.nb_rpps_score = 0


    def load_cache(self):
        print("Making cache")
        l: List[Coord] = self.context.session.query(Coord)\
            .options(joinedload(Coord.adresse_norm)).filter(Coord.structure_id_technique.isnot(None)).all()
        for e in l:
            self.entities[e.structure_id_technique] = e
            self.nb_ram += 1
        l: List[Structure] = self.context.session.query(Structure).all()
        for s in l:
            self.structures[s.key] = s
            self.nb_ram += 1
        l: List[Source] = self.context.session.query(Source).all()
        for s in l:
            self.sources[s.id] = s
            self.nb_ram += 1
        print(f"{self.nb_ram} objects in cache")

    def to_float(self, s: str):
        s = s.replace(",",".")
        if s.startswith("."):
            s = "0" + s
        return float(s)

    def mapper(self, row) -> Coord:
        e = Coord()
        try:
            e.structure_id_technique = row["Identifiant technique de la structure"]
            e.lat = float(row["Latitude (coordonnées GPS)"].strip())
            e.lon = float(row["Longitude (coordonnées GPS)"].strip())
            type = row["Type de précision (coordonnées GPS)"]
            e.type_precision = 4
            if type == "Street number":
                e.type_precision = 0
            elif type == "Street enhanced":
                e.type_precision = 1
            elif type == "Street":
                e.type_precision = 2
            elif type == "City":
                e.type_precision = 3
            e.precision = self.to_float(row["Précision (coordonnées GPS)"].strip())
        except Exception as ex:
            print(f"ERROR Coord row {self.row_num} {e}\n{ex}\n{row}")
            quit(1)
        return e

    def score(self, e: Coord):
        score = e.precision - 0.05 * e.type_precision
        if e.type_precision >= 3:
            score -= 0.15
        return score

    def update_norm(self, e: Coord):
        score = self.score(e)
        if e.adresse_norm.rpps_score is None or score > e.adresse_norm.rpps_score:
            e.adresse_norm.rpps_score = score
            self.nb_rpps_score += 1
        if e.adresse_norm.score is None or score > e.adresse_norm.score:
            if  e.adresse_norm.source_id is None or e.adresse_norm.source_id != 5:
                e.adresse_norm.lon = e.lon
                e.adresse_norm.lat = e.lat
                e.adresse_norm.score = score
                e.adresse_norm.source = self.sources[6]
                self.nb_score_improvment += 1
        elif (e.adresse_norm.source_id is None
              or (e.adresse_norm.source_id == 3 and score > config.source_rpps_win_etab)):
            e.adresse_norm.lon = e.lon
            e.adresse_norm.lat = e.lat
            e.adresse_norm.score = score
            e.adresse_norm.source = self.sources[6]
            self.nb_score_improvment += 1

    def parse_row(self, row):
        temp = self.mapper(row)
        if temp.structure_id_technique in self.entities:
            e = self.entities[temp.structure_id_technique]
            if e.lon is None:
                e.lon = temp.lon
                e.lat = temp.lat
                e.type_precision = temp.type_precision
                e.precision = temp.precision
                self.nb_new_entity += 1
                if e.adresse_norm is not None:
                    self.update_norm(e)
                self.context.session.commit()
        else:
            self.no_coord += 1


if __name__ == '__main__':
    art.tprint(config.name, "big")
    print("RPPS Coord Structure Parser")
    print("===========================")
    print(f"V{config.version}")
    print(config.copyright)
    print()
    parser = argparse.ArgumentParser(description="RPPS Coord Structure Parser")
    parser.add_argument("path", help="Path")
    parser.add_argument("-e", "--echo", help="Sql Alchemy echo", action="store_true")
    args = parser.parse_args()
    context = Context()
    context.create(echo=args.echo, expire_on_commit=False)
    db_size = context.db_size()
    print(f"Database {context.db_name}: {db_size:.0f} Mb")
    rpp = RPPSCoordStructureGeolocParser(context)
    rpp.load(args.path, delimiter=';', encoding="UTF-8", header=True)
    print(f"New geoloc: {rpp.nb_new_entity}")
    print(f"Nb geoloc without coord: {rpp.no_coord}")
    print(f"Nb new score for geoloc: {rpp.nb_rpps_score}")
    print(f"Nb score improvment: {rpp.nb_score_improvment}")
    new_db_size = context.db_size()
    print(f"Database {context.db_name}: {new_db_size:.0f} Mb")
    print(f"Database grows: {new_db_size - db_size:.0f} Mb ({((new_db_size - db_size) / db_size) * 100:.1f}%)")
    print(f"Parse {rpp.row_num} rows in {time.perf_counter() - time0:.0f} s")

    # data/rpps/CoordStructGeoloc_small.csv
    # data/rpps/CoordStructGeoloc_medium.csv
    # data/rpps/Extraction_RPPS_Profil4_CoordStructGeoloc_202310250948.csv

    # to reset
    # update public.coord set lon = null where lon is not null
    # update public.adresse_norm set score = null where lon is null and lat is null and score is not null and rpps_score is not null
    # update public.adresse_norm set rpps_score = null where rpps_score is not null
    # verify
    # SELECT * FROM public.coord
    # full join public.adresse_norm ON adresse_norm.id = coord.adresse_norm_id
    # where coord.lon is not null
    # ORDER BY coord.id DESC LIMIT 1000
    # remplacer full par inner pour eviter les vides


