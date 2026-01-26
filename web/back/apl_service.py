import json
import threading
import time
import warnings
from sqlalchemy import text
from iris_loader import IrisLoader
from service_error import ServiceError
import re
import pandas as pd
import config


class APLService:

    _instance = None
    lock = threading.RLock()

    def __init__(self):
        self.iris_loader: IrisLoader = IrisLoader.factory()
        self.first_year = 20
        self.years = list(range(self.first_year, 26))
        self.regex = re.compile(r"^C[CDRAEFP]-\d[\dAB]\d*$")  #TODO CP faire la table cp_insee
        warnings.filterwarnings('ignore', category=UserWarning)
        # todo remonter régions ici

    @staticmethod
    def factory():
        with APLService.lock:
            if APLService._instance is None:
                APLService._instance = APLService()
        return APLService._instance

    def check_time_type(self, time_type: str):
        if time_type not in ["HC", "HP"]:
            raise ServiceError(f"Bad time_type {time_type}")

    def check_code(self, code: str) -> tuple[str, str]:
        if re.match(self.regex, code):
            return code[:2], code[3:]
        raise ServiceError(f"Bad code {code}")

    def get_iriss_cc(self, id: str) -> list[str]:
        sql = f"""
        select i.code from iris.commune c
        join iris.iris i on i.commune_id=c.id
        where c.code='{id}'
        order by i.id
        """
        # print(sql)
        iris_df = pd.read_sql(sql, config.connection_string)
        iriss = iris_df["code"].to_list()
        return iriss

    def get_depts_cr(self, id: str) -> list[str]:
        sql = f"select num from dept where region_id={id}"
        iris_df = pd.read_sql(sql, config.connection_string)
        depts = iris_df["num"].to_list()
        return depts

    def get_iriss_ce(self, id: str) -> list[str]:
        sql = f"""
        select i.code from iris.commune c
        join iris.iris i on i.commune_id=c.id
        where c.epci_id='{id}'
        order by i.id
        """
        iris_df = pd.read_sql(sql, config.connection_string)
        iriss = iris_df["code"].to_list()
        return iriss

    def get_iriss_ca(self, id: str) -> list[str]:
        sql = f"""
        select i.code from iris.commune c
        join iris.iris i on i.commune_id=c.id
        where c.arr_dept_id='{id}'
        order by i.id
        """
        iris_df = pd.read_sql(sql, config.connection_string)
        iriss = iris_df["code"].to_list()
        return iriss

    def get_iriss_cp(self, id: str) -> list[str]:
        sql = f"""
        select i.code from iris.cp_insee ci
        join iris.commune c on c.code=ci.code_insee
        join iris.iris i on i.commune_id=c.id
        where ci.code_postal={id}
        """
        iris_df = pd.read_sql(sql, config.connection_string)
        iriss = iris_df["code"].to_list()
        return iriss

    def get_gdf_by_cc(self, id: str) -> pd.DataFrame:
        iriss = self.get_iriss_cc(id)
        if len(iriss) > 0:
            gdf = self.iris_loader.gdf[self.iris_loader.gdf["code_iris"].isin(iriss)]
        else:
            gdf = self.iris_loader.gdf[self.iris_loader.gdf["code_insee"] == id]
        return gdf

    def get_gdf_by_cd(self, id: str) -> pd.DataFrame:
        gdf = self.iris_loader.gdf[self.iris_loader.gdf["code_iris"].str.startswith(id)]
        return gdf

    def get_gdf_by_cr(self, id: str) -> pd.DataFrame:
        depts = self.get_depts_cr(id)
        gdf = self.iris_loader.gdf[self.iris_loader.gdf["code_iris"].str.startswith(tuple(depts))]
        return gdf

    def get_gdf_by_ce(self, id: str) -> pd.DataFrame:
        iriss = self.get_iriss_ce(id)
        gdf = self.iris_loader.gdf[self.iris_loader.gdf["code_iris"].isin(iriss)]
        return gdf

    def get_gdf_by_ca(self, id: str) -> pd.DataFrame:
        iriss = self.get_iriss_ca(id)
        gdf = self.iris_loader.gdf[self.iris_loader.gdf["code_iris"].isin(iriss)]
        return gdf

    def get_gdf_by_cp(self, id: str) -> pd.DataFrame:
        iriss = self.get_iriss_cp(id)
        gdf = self.iris_loader.gdf[self.iris_loader.gdf["code_iris"].isin(iriss)]
        return gdf

    def get_gdf_by_type_code_id(self, type_code: str, id: str) -> pd.DataFrame:
        if type_code == "CC":
            return self.get_gdf_by_cc(id)
        elif type_code == "CD":
            return self.get_gdf_by_cd(id)
        elif type_code == "CR":
            return self.get_gdf_by_cr(id)
        elif type_code == "CE":
            return self.get_gdf_by_ce(id)
        elif type_code == "CA":
            return self.get_gdf_by_ca(id)
        elif type_code == "CP":
            return self.get_gdf_by_cp(id)
        elif type_code == "CF":
            return self.iris_loader.gdf
        else:
            raise ServiceError(f"Bad type code: {type_code}")

    def get_study_by_year(self, specialite: int, time: int, time_type: str, aexp: float, year: int) -> pd.DataFrame:
        sql = f"""
        select * from apl.apl_study s
        where s.specialite_id={specialite}
        and s.year={year}
        and s.source='PA'
        and s.time={time}
        and s.time_type='{time_type}'
        and s.exp={aexp}
        order by date desc
        limit 1
        """
        return pd.read_sql(sql, config.connection_string)

    def get_studies_by_years(self, specialite: int,
                             time: int,
                             time_type: str,
                             aexp: float,
                             years: list[int]) -> pd.DataFrame:
        df = None
        for year in years:
            if df is None:
                df = self.get_study_by_year(specialite, time, time_type, aexp, year)
            else:
                df = pd.concat([df, self.get_study_by_year(specialite, time, time_type, aexp, year)], ignore_index=True)
        return df

    def get_apl_by_keys(self, keys: list[int], code: str, id: str):
        sql = f"select * from apl.apl a  where a.study_key in {tuple(keys)} "
        sql0 = sql
        if code == "CC":
            sql += f"and code_commune='{id}'"
        elif code == "CD":
            sql += f"and a.iris_string like '{id}%'"
        elif code == "CR":
            depts = self.get_depts_cr(id)
            sql += f"and a.iris_string like any (array{[c+'%' for c in depts]})"
        elif code in ["CA", "CP"]:
            sql += f"and a.iris_string like '{id[:2]}%'"
        apl = pd.read_sql(text(sql), config.connection_string)
        if len(apl) == 0:
            apl = pd.read_sql(text(sql0), config.connection_string)
        return apl

    def corrections(self, apl: pd.DataFrame):
        if len(apl[apl["iris_string"] == "140110000"]) > 0:
            apl.loc[apl["iris_string"] == "140110000", "iris_string"] = "145810000"

    def merge_gdf_apl(self, gdf: pd.DataFrame, apl: pd.DataFrame) -> pd.DataFrame:
        apl["code_iris"] = apl["iris_string"]
        gdf_merged = gdf.merge(apl, on="code_iris", how="left", suffixes=('', '_dest'))
        return gdf_merged

    def gdf_merge_add_columns(self, gdf_merged: pd.DataFrame) -> pd.DataFrame:
        gdf_merged["pretty"] = gdf_merged["apl"].fillna(0).apply(lambda x: round(x, 0)).astype(int)
        gdf_merged["pop_ajustee"] = gdf_merged['pop_gp']
        apl20 = gdf_merged.loc[gdf_merged['year'] == 20, ['iris_dest', 'apl']].set_index('iris_dest')['apl']
        gdf_merged["year20"] = gdf_merged['iris_dest'].map(apl20).fillna(0)
        gdf_merged["diff20"] = gdf_merged["apl"] - gdf_merged["year20"]
        gdf_merged["delta20"] = gdf_merged["diff20"] / (gdf_merged["year20"] + 0.1)
        return gdf_merged

    def get_export(self, code: str, studies_df: pd.DataFrame, gdf_merged: pd.DataFrame) -> tuple[dict, any]:
        center_lat = gdf_merged.geometry.centroid.y.mean()  # 45.1209 5.5901
        center_lon = gdf_merged.geometry.centroid.x.mean()
        dico = {"center_lat": center_lat, "center_lon": center_lon, "q": code, "meanws": [], "years": {}}  #TODO enlever le superflu
        export = gdf_merged[['code_insee', 'nom_commune', 'code_iris', 'nom_iris', 'lon', 'lat', 'fid', 'year', 'nb', 'apl', 'R', 'swpop', 'pop', 'pop_ajustee']]
        for year in self.years:
            meanw = studies_df[studies_df["year"] == year]["meanw"].iloc[0]
            dico["meanws"].append(meanw)
            export_year = export[export["year"] == year]
            dico_year = {}
            for col in export.columns:
                dico_year[col] = export_year[col].values.tolist()
            dico["years"][year + 2000] = dico_year
        geojson = gdf_merged.__geo_interface__
        print(f"Found {len(geojson["features"]) / len(self.years):.0f} geojsons by years ")  # TODO Optimisation enlever tous les geojson de même fid x6
        return dico, geojson

    def compute(self, code: str, specialite: int, time: int, time_type: str, aexp: float) -> tuple[dict, any]:
        print(f"Compute APL for {code} {specialite} {time} {time_type} {aexp}")
        self.check_time_type(time_type)
        type_code, id = self.check_code(code)
        gdf = self.get_gdf_by_type_code_id(type_code, id)
        # geojson = gdf.__geo_interface__
        print(f"Found {len(gdf)} gdfs")
        studies_df = self.get_studies_by_years(specialite, time, time_type, aexp, self.years)
        print(f"Found {len(studies_df)} studies for {len(self.years)} years")
        keys = studies_df["key"].to_list()
        apl = self.get_apl_by_keys(keys, type_code, id)
        print(f"Found {len(apl) / len(self.years):.0f} apls by year")
        self.corrections(apl)
        gdf_merged = self.merge_gdf_apl(gdf, apl)
        print(f"Merged {len(gdf_merged) / len(self.years):.0f} gdf-apls by year")
        gdf_merged = self.gdf_merge_add_columns(gdf_merged)
        export = self.get_export(code, studies_df, gdf_merged)
        return export
        # TODO exporter les vrais data
        # TODO gérer si vide par exemple cp 75001


if __name__ == '__main__':
    s = APLService()
    time.sleep(1)
    export = s.compute("CP-75001", 10, 30, "HC", -0.12)  #CC-38185 CC-38205 CC-06088 CC-75101 CD-38 CD-06 CR-84 CR-93 CE-200040715 CA-381 CF-00
    s = json.dumps(export)
    print(s[:5000])
