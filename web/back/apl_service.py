import json
import threading
import time
import warnings

from pandas.errors import SettingWithCopyWarning
from sqlalchemy import text
from iris_loader import IrisLoader
from service_error import ServiceError
import re
import pandas as pd
import config
from web.back.commune_loader import CommuneLoader


class APLService:

    _instance = None
    lock = threading.RLock()

    def __init__(self):
        self.iris_loader: IrisLoader = IrisLoader.factory()
        self.commune_loader: CommuneLoader = CommuneLoader.factory()
        self.first_year = 20
        self.years = list(range(self.first_year, 26))
        self.regex = re.compile(r"^C[CDRAEFP]-\d[\dAB]\d*$")
        warnings.filterwarnings('ignore', category=UserWarning)
        warnings.filterwarnings('ignore', category=SettingWithCopyWarning)

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
            if code[:6] == "CP-750":
                return "CC", "751"+code[-2:]
            if code[:7] == "CP-6900":
                return "CC", "6938"+code[-1]
            if code[:6] == "CP-130":
                return "CC", "132"+code[-2:]
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

    def get_iris_gdf_by_cc(self, id: str) -> pd.DataFrame:
        iriss = self.get_iriss_cc(id)
        if len(iriss) > 0:
            gdf = self.iris_loader.gdf[self.iris_loader.gdf["code_iris"].isin(iriss)]
        else:
            gdf = self.iris_loader.gdf[self.iris_loader.gdf["code_insee"] == id]
        return gdf

    def get_commune_gdf_by_cc(self, id: str, resolution: str) -> pd.DataFrame:
        gdf = self.commune_loader.gdfs[resolution]
        # gdf = gdf[((gdf["code"] == id) | (gdf["commune"] == id)]
        gdf = gdf[(gdf["code"] == id) & (gdf["associee"] == False)]
        gdf["code"] = gdf["code"].where(gdf["commune"].isna(), gdf["commune"])  # Pour 75, 69, 13
        return gdf

    def get_iris_gdf_by_cd(self, id: str) -> pd.DataFrame:
        gdf = self.iris_loader.gdf[self.iris_loader.gdf["code_iris"].str.startswith(id)]
        return gdf

    def get_iris_gdf_by_cr(self, id: str) -> pd.DataFrame:
        depts = self.get_depts_cr(id)  # Inutile pour commune la region est dans le df
        gdf = self.iris_loader.gdf[self.iris_loader.gdf["code_iris"].str.startswith(tuple(depts))]
        return gdf

    def get_iris_gdf_by_ce(self, id: str) -> pd.DataFrame:
        iriss = self.get_iriss_ce(id)  # Inutile pour commune le epci est dans le df
        gdf = self.iris_loader.gdf[self.iris_loader.gdf["code_iris"].isin(iriss)]
        return gdf

    def get_iris_gdf_by_ca(self, id: str) -> pd.DataFrame:
        iriss = self.get_iriss_ca(id)
        gdf = self.iris_loader.gdf[self.iris_loader.gdf["code_iris"].isin(iriss)]
        return gdf

    def get_iris_gdf_by_cp(self, id: str) -> pd.DataFrame:
        iriss = self.get_iriss_cp(id)
        gdf = self.iris_loader.gdf[self.iris_loader.gdf["code_iris"].isin(iriss)]
        return gdf

    def get_iris_gdf_by_type_code_id(self, type_code: str, id: str) -> pd.DataFrame:
        if type_code == "CF":
            return self.iris_loader.gdf
        else:
            return self.__getattribute__(f"get_iris_gdf_by_{type_code.lower()}")(id)

    def get_commune_gdf_by_type_code_id(self, type_code: str, id: str, resolution: str) -> pd.DataFrame:
        if type_code == "CF":
            return self.iris_loader.gdf
        else:
            return self.__getattribute__(f"get_commune_gdf_by_{type_code.lower()}")(id, resolution)

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

    def merge_iris_gdf_apl(self, gdf: pd.DataFrame, apl: pd.DataFrame) -> pd.DataFrame:
        apl["code_iris"] = apl["iris_string"]
        gdf_merged = gdf.merge(apl, on="code_iris", how="left", suffixes=('', '_dest'))
        return gdf_merged

    def merge_commune_gdf_apl(self, gdf: pd.DataFrame, apl: pd.DataFrame) -> pd.DataFrame:
        gdf["code_commune"] = gdf["code"]
        gdf_merged = gdf.merge(apl, on="code_commune", how="left", suffixes=('', '_dest'))
        return gdf_merged

    def group_apl_by_commune(self, apl: pd.DataFrame) -> pd.DataFrame:
        apl = apl.sort_values(by=["year", "iris"])
        apl["pop_sum"] = apl['pop'].fillna(0).groupby([apl["code_commune"], apl["year"]]).transform('sum')
        apl["pop_gp_sum"] = apl['pop_gp'].fillna(0).groupby([apl["code_commune"], apl["year"]]).transform('sum')
        apl["nb_sum"] = apl['nb'].fillna(0).groupby([apl["code_commune"], apl["year"]]).transform('sum')
        apl[f"apl_meanw"] = ((apl["apl"].fillna(0) * apl["pop"])
                             .groupby([apl["code_commune"], apl["year"]]).transform('sum') / apl["pop_sum"])
        apl = apl.drop_duplicates(subset=['year', "code_commune"])
        return apl

    def gdf_merge_add_columns(self, gdf: pd.DataFrame) -> pd.DataFrame:
        if "apl_meanw" in gdf.columns:
            gdf["apl"] = gdf["apl_meanw"]
            gdf["pop_ajustee"] = gdf["pop_gp_sum"]
            gdf["nb"] = gdf["nb_sum"]
            gdf["pop"] = gdf["pop_sum"]
            gdf["code_insee"] = gdf["code"]
            gdf["nom_commune"] = gdf["nom"]
            gdf["fid"] = gdf["code"]
            gdf["code_iris"] = ""
            gdf["nom_iris"] = ""
        else:
            gdf["pop_ajustee"] = gdf['pop_gp'].fillna(0)
            gdf["pop"] = gdf["pop"].fillna(0)
        gdf["apl_max"] = gdf["apl"].max()
        return gdf

    def get_export(self, code: str, studies_df: pd.DataFrame, gdf: pd.DataFrame) -> tuple[dict, any]:
        center_lat = gdf.geometry.centroid.y.mean()  # 45.1209 5.5901
        center_lon = gdf.geometry.centroid.x.mean()
        dico = {"center_lat": center_lat, "center_lon": center_lon, "q": code, "meanws": [], "years": {}}
        cols = ['code_insee', 'nom_commune', 'lon', 'lat', 'fid', 'year', 'nb', 'apl', 'swpop', 'pop', 'pop_ajustee',
                'apl_max', 'code_iris', 'nom_iris', "geometry"]
        export = gdf[cols]
        for year in self.years:
            meanw = studies_df[studies_df["year"] == year]["meanw"].iloc[0]
            dico["meanws"].append(meanw)
            export_year = export[export["year"] == year]
            dico_year = {}
            for col in export.columns:
                if col != "geometry":
                    dico_year[col] = export_year[col].values.tolist()
            dico["years"][year + 2000] = dico_year
        gdf_first_year = gdf[gdf["year"] == self.first_year]
        geojson = gdf_first_year[["fid", "geometry"]].__geo_interface__
        print(f"Found {len(geojson["features"])} geojsons")
        return dico, geojson

    def simplify(self, gdf: pd.DataFrame, resolution: str) -> pd.DataFrame:
        if resolution == "MD":
            gdf["geometry"] = gdf["geometry"].simplify(0.001)  # 10km
        elif resolution == "LD":
            gdf["geometry"] = gdf["geometry"].simplify(0.01)   # 1km
        return gdf

    def get_apl(self, code: str, specialite: int, time: int, time_type: str, aexp: float)\
            -> tuple[pd.DataFrame, pd.DataFrame]:
        type_code, id = self.check_code(code)
        studies_df = self.get_studies_by_years(specialite, time, time_type, aexp, self.years)
        keys = studies_df["key"].to_list()
        apl = self.get_apl_by_keys(keys, type_code, id)
        print(f"Found {len(apl) / len(self.years):.0f} apls by year")
        self.corrections(apl)
        return apl, studies_df

    def compute_iris(self, code: str, specialite: int, time: int, time_type: str, aexp: float, resolution: str)\
            -> tuple[dict, any]:
        print(f"Compute IRIS APL for {code} {specialite} {time} {time_type} {aexp}")
        self.check_time_type(time_type)
        type_code, id = self.check_code(code)
        apl, studies_df = self.get_apl(code, specialite, time, time_type, aexp)
        gdf = self.get_iris_gdf_by_type_code_id(type_code, id)
        print(f"Found {len(gdf)} gdfs")
        gdf_merged = self.merge_iris_gdf_apl(gdf, apl)
        print(f"Merged {len(gdf_merged) / len(self.years):.0f} gdf-apls by year")
        gdf_merged = self.gdf_merge_add_columns(gdf_merged)
        gdf_merged = self.simplify(gdf_merged, resolution)  # Ne pas appeler pour commune
        export = self.get_export(code, studies_df, gdf_merged)
        return export

    def compute_iris_csv(self, code: str, specialite: int, time: int, time_type: str, aexp: float) -> pd.DataFrame:
        print(f"Compute IRIS APL CSV for {code} {specialite} {time} {time_type} {aexp}")
        apl, _ = self.get_apl(code, specialite, time, time_type, aexp)
        apl["year"] = apl["year"]+2000
        return apl[["specialite", "year", "iris_string", "iris_label", "apl", "code_commune", "commune_label"]]

    def compute_commune(self, code: str, specialite: int, time: int, time_type: str, aexp: float, resolution: str) \
            -> tuple[dict, any]:
        print(f"Compute Commune APL for {code} {specialite} {time} {time_type} {aexp} {resolution}")
        self.check_time_type(time_type)
        type_code, id = self.check_code(code)
        apl, studies_df = self.get_apl(code, specialite, time, time_type, aexp)
        gdf = self.get_commune_gdf_by_type_code_id(type_code, id, resolution)
        print(f"Found {len(gdf)} gdfs")
        gdf_merged = self.merge_commune_gdf_apl(gdf, apl)
        print(f"Merged {len(gdf_merged) / len(self.years):.0f} gdf-apls by year")
        gdf_commune = self.group_apl_by_commune(gdf_merged)
        gdf_commune = self.gdf_merge_add_columns(gdf_commune)
        export = self.get_export(code, studies_df, gdf_commune)
        return export


if __name__ == '__main__':
    pd.set_option('display.max_columns', None)
    pd.options.display.width = 0
    s = APLService()
    time.sleep(1)
    # export = s.compute_iris("CC-38225", 10, 30, "HC", -0.12, "HD")  #CC-38185 CC-38205 CC-38021 Autrans CC-38225 Autrans Meaudre CC-75101 CC-75056 CC-06088 CC-75101 CD-38 CD-06 CR-84 CR-93 CE-200040715 CA-381 CF-00
    # s = json.dumps(export)
    # print(s[:5000])
    export = s.compute_commune("CC-75056", 10, 30, "HC", -0.12, "HD")  # Ne fonctionne pas pour Autrans 38021
    s = json.dumps(export)
    print(s[:5000])


