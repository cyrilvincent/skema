import math

import pandas as pd
import art
import argparse
from shapely.geometry import Point
import psycopg2
from sqlalchemy import text

import config
import pickle

from sqlentities import Context

print(config.version)
print(config.connection_string)
pd.set_option('display.max_columns', None)
pd.options.mode.copy_on_write = True


class GeoIris:

    def __init__(self):
        self.gdf = pd.DataFrame()
        self.gdf_dept: dict[str, pd.DataFrame] = {}
        self.connection = psycopg2.connect(config.connection_string)

    def __del__(self):
        self.connection.close()

    def load(self):
        with open("data/iris/gdf.pickle", "rb") as f:
            self.gdf = pickle.load(f)

    def get_gdf_by_dept(self, dept: str) -> pd.DataFrame:
        if dept not in self.gdf_dept:
            df = self.gdf[self.gdf["code_iris"].str.startswith(dept)]
            self.gdf_dept[dept] = df
        return self.gdf_dept[dept]

    def calc_distance(self, lon1, lat1, lon2, lat2):
        r = 6373.0
        lat1 = math.radians(lat1)
        lon1 = math.radians(lon1)
        lat2 = math.radians(lat2)
        lon2 = math.radians(lon2)
        dlon = lon2 - lon1
        dlat = lat2 - lat1
        a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        distance = r * c
        return int(distance * 1000)  # in meter

    def find_iris(self, dept: str, lon: float, lat: float) -> str | None:
        df = self.get_gdf_by_dept(dept)
        p = Point(lon, lat)
        inside = df.geometry.apply(lambda poly: p.within(poly))
        result = df[inside]
        if len(result) == 0:
            return None
        return result["code_iris"].iloc[0]

    def find_nearest_iris(self, dept: str, lon: float, lat: float) -> str | None:
        df = self.get_gdf_by_dept(dept)
        best_distance = 99999
        best_iris = None
        for index, row in df.iterrows():
            d = self.calc_distance(lon, lat, row["lon"], row["lat"])
            if d < best_distance:
                best_distance = d
                best_iris = row["code_iris"]
        if best_distance > 1000:
            return None
        return best_iris

    def get_adresse_norms(self):
        print("Querying adresse_norm")
        sql = "select * from adresse_norm an where an.geo_iris is null and an.lon is not null"
        return pd.read_sql(text(sql), config.connection_string)

    def update_iris(self, id: int, iris: str):
        sql = f"update adresse_norm set geo_iris='{iris}' where id={id}"
        with self.connection.cursor() as cur:
            cur.execute(sql)
        self.connection.commit()

    def check_adresse_norms(self):
        adresse_norms = self.get_adresse_norms()
        print(f"Found {len(adresse_norms)} adresses to geo_irised")
        nb = 0
        diff = 0
        not_found = 0
        nearest_found = 0
        for index, row in adresse_norms.iterrows():
            id = row["id"]
            iris = row["iris"]
            lon = row["lon"]
            lat = row["lat"]
            if not math.isnan(lon):
                nb += 1
                dept_id = row["dept_id"]
                dept = str(dept_id)
                if dept_id == 201:
                    dept = "2A"
                elif dept_id == 202:
                    dept = "2B"
                elif len(dept) == 1:
                    dept = "0" + dept
                result = self.find_iris(dept, lon, lat)
                if result is None:
                    not_found += 1
                    result = self.find_nearest_iris(dept, lon, lat)
                    if result is not None:
                        nearest_found += 1
                if result is not None and result != iris:
                    diff += 1
                    print(f"Found {iris}!={result} {diff}/{nb} {nearest_found}/{not_found}")
                    self.update_iris(id, result)


if __name__ == '__main__':
    art.tprint(config.name, "big")
    print("GeoIris")
    print("=======")
    print(f"V{config.version}")
    print(config.copyright)
    print()
    gi = GeoIris()
    gi.load()
    iris = gi.find_iris("38", 5.580595, 45.098510)
    print(iris)
    iris = gi.find_iris("06", 7.251, 43.704)
    print(iris)
    print(gi.calc_distance(0.689, 47.39, 1.26, 45.83))  # 178km
    gi.check_adresse_norms()

    # Pharma en erreur bien corrigée par le prg
    # select * from etablissement e
    # join adresse_raw ar on ar.id=e.adresse_raw_id
    # join adresse_norm an on an.id=ar.adresse_norm_id
    # join iris.iris i on i.code=an.iris
    # where e.nofinesset='060016326'
