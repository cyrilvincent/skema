import json
import threading
import time
import warnings
from typing import Iterable

import numpy as np
from pandas.errors import SettingWithCopyWarning
from sqlalchemy import text
from iris_loader import IrisLoader
from commune_loader import CommuneLoader
from service_error import ServiceError
import re
import pandas as pd
import config
from apl_service import APLService


class SAEService(APLService):

    _instance = None
    lock = threading.RLock()

    def __init__(self):
        super().__init__()
        self.first_year = None
        self.last_year = 24
        self.years = None
        self.bors = ["urgence_gen", "urgence_ped", "psy", "pharma", "ehpad"]

    @staticmethod
    def factory():
        with SAEService.lock:
            if SAEService._instance is None:
                SAEService._instance = SAEService()
        return SAEService._instance

    def get_first_year(self, bor: str):
        return 13 if bor not in ["pharma", "ehpad"] else 4

    def years_list(self, bor: str):
        years = []
        for y in range(self.get_first_year(bor), self.last_year + 1):
            years.append(y)
        return years

    def get_sae_study_by_year(self, bor: str, time: int, time_type: str, year: int) -> pd.DataFrame:
        sql = f"""
        select * from sae.dist_study s
        where s.bor='{bor}'
        and s.year=20{year:02d}
        and s.time={time}
        and s.time_type='{time_type}'
        order by date desc
        limit 1
        """
        return pd.read_sql(sql, config.connection_string)

    def get_sae_studies_by_years(self, bor: str, time: int, time_type: str, years: Iterable[int]) -> pd.DataFrame:
        df = None
        for year in years:
            if df is None:
                df = self.get_sae_study_by_year(bor, time, time_type, year)
            else:
                df = pd.concat([df, self.get_sae_study_by_year(bor, time, time_type, year)], ignore_index=True)
        return df

    def get_sae_by_keys(self, keys: list[int], code: str, id: str):
        sql = f"select * from sae.dist d where d.study_key in {tuple(keys)} "
        sql0 = sql
        if code == "CC":
            sql += f"and d.code_commune='{id}'"
        elif code == "CD":
            sql += f"and d.iris_string like '{id}%'"
        elif code == "CR":
            depts = self.get_depts_cr(id)
            sql += f"and d.iris_string like any (array{[c+'%' for c in depts]})"
        elif code in ["CA", "CP"]:
            sql += f"and d.iris_string like '{id[:2]}%'"
        apl = pd.read_sql(text(sql), config.connection_string)
        if len(apl) == 0:
            apl = pd.read_sql(text(sql0), config.connection_string)
        return apl

    def get_sae(self, type_code: str, id: str, bor: str, time: int, time_type: str)\
            -> tuple[pd.DataFrame, pd.DataFrame]:
        years = self.years_list(bor)
        studies_df = self.get_sae_studies_by_years(bor, time, time_type, years)
        keys = studies_df["key"].to_list()
        sae = self.get_sae_by_keys(keys, type_code, id)
        print(f"Found {len(sae) / len(years):.0f} sae by year")
        self.corrections(sae)
        return sae, studies_df

    def get_tuple(self, l):
        if len(l) > 1:
            return tuple(l)
        elif len(l) == 1:
            return f"('{l[0]}')"
        else:
            return "()"

    def get_urgence_sae(self, iris_list: list[str], urg: str) -> pd.DataFrame:
        sql = f"""
            select d.an as year, d.fi, d.passu, p.perso is not null has_pdata, p.etpsal, p.efflib, p.etp, e.id etab_id,
                e.rs, an.dept_id, an.id adresse_norm_id, an.lon, an.lat, i.id iris 
            from sae.urgence_detail d
            left join sae.urgence_p p on p.fi=d.fi and p.an=d.an and p.perso='M9999'
            join etablissement e on e.nofinesset=d.fi
            join adresse_raw ar on e.adresse_raw_id=ar.id
            join adresse_norm an on ar.adresse_norm_id=an.id
            join iris.iris i on i.code=an.iris
            where d.urg='{urg}'
            and an.iris in {self.get_tuple(iris_list)}
            order by d.an, d.fi
            """
        return pd.read_sql(sql, config.connection_string)

    def get_urgence_commune_sae(self, iris_list: list[str], urg: str) -> pd.DataFrame:
        sql = f"""
            select d.an as year, d.fi, d.passu, p.perso is not null has_pdata, p.etpsal, p.efflib, p.etp, e.id etab_id,
                e.rs, an.dept_id, an.id adresse_norm_id, an.lon, an.lat, i.id iris 
            from sae.urgence_detail d
            left join sae.urgence_p p on p.fi=d.fi and p.an=d.an and p.perso='M9999'
            join etablissement e on e.nofinesset=d.fi
            join adresse_raw ar on e.adresse_raw_id=ar.id
            join adresse_norm an on ar.adresse_norm_id=an.id
            join iris.iris i on i.code=an.iris
            where d.urg='{urg}'
            and an.iris in {self.get_tuple(iris_list)}
            order by d.an, d.fi
            """
        return pd.read_sql(sql, config.connection_string)

    def get_psy_sae(self, iris_list: list[str]) -> pd.DataFrame:
        sql = f"""
            select p.an as year, p.fi, p.cap_htp passu, true has_pdata, p.etpsal_pkt etpsal, p.efflib_pkt efflib,
                p.etp_pkt etp, e.id etab_id, e.rs, an.dept_id, an.id adresse_norm_id, an.lon, an.lat, i.id iris 
            from sae.psy p
            join etablissement e on e.nofinesset=p.fi
            join adresse_raw ar on e.adresse_raw_id=ar.id
            join adresse_norm an on ar.adresse_norm_id=an.id
            join iris.iris i on i.code=an.iris
            where p.dis='TOT'
            and an.iris in {self.get_tuple(iris_list)}
            order by p.an, p.fi
            """
        return pd.read_sql(sql, config.connection_string)

    def get_pharma_sae(self, iris_list: list[str]) -> pd.DataFrame:
        sql = f"""
            select ds.annee+2000 as year, e.nofinesset fi, null as passu, false as has_pdata, null as etpsal,
                null as efflib, null as etp, e.id etab_id, e.rs, an.id an_id, an.dept_id, an.id adresse_norm_id,
                an.lon, an.lat, i.id iris
            from etablissement e
            join etablissement_date_source eds on eds.etablissement_id=e.id
            join adresse_raw ar on ar.id=e.adresse_raw_id
            join adresse_norm an on an.id=ar.adresse_norm_id
            join iris.iris i on i.code=an.iris
            join date_source ds on eds.date_source_id=ds.id
            where e.categetab=620
            and an.iris in {self.get_tuple(iris_list)}
            order by ds.annee, e.nofinesset
        """
        return pd.read_sql(sql, config.connection_string)

    def get_ehpad_sae(self, iris_list: list[str]) -> pd.DataFrame:
        sql = f"""
            select ds.annee+2000 as year, e.nofinesset fi, null as passu, false as has_pdata, null as etpsal,
                null as efflib, null as etp, e.id etab_id, e.rs, an.id an_id, an.dept_id, an.id adresse_norm_id,
                an.lon, an.lat, i.id iris
            from etablissement e
            join etablissement_date_source eds on eds.etablissement_id=e.id
            join adresse_raw ar on ar.id=e.adresse_raw_id
            join adresse_norm an on an.id=ar.adresse_norm_id
            join iris.iris i on i.code=an.iris
            join date_source ds on eds.date_source_id=ds.id
            where e.categretab=4401
            and an.iris in {self.get_tuple(iris_list)}
            order by ds.annee, e.nofinesset
        """
        return pd.read_sql(sql, config.connection_string)

    def get_sae_by_bor(self, bor: str, gdf: pd.DataFrame) -> pd.DataFrame:
        iris_list = list(gdf["code_iris"].unique())
        if bor == "urgence_gen":
            return self.get_urgence_commune_sae(iris_list, "GEN")
        elif bor == "urgence_ped":
            return self.get_urgence_commune_sae(iris_list, "PED")
        else:
            return self.__getattribute__(f"get_{bor}_sae")(iris_list)

    def get_sae_commune_by_bor(self, bor: str, gdf: pd.DataFrame) -> pd.DataFrame:
        commune_list = list(gdf["code"].unique())
        if bor == "urgence_gen":
            return self.get_urgence_sae(commune_list, "GEN")
        elif bor == "urgence_ped":
            return self.get_urgence_sae(commune_list, "PED")
        # else:
        #     return self.__getattribute__(f"get_{bor}_sae")(iris_list)

    def etab_tension(self, etab_df: pd.DataFrame) -> pd.DataFrame:
        etab_df = etab_df.drop_duplicates(subset=['year', "lon", "lat"])
        etab_df["tension"] = etab_df["passu"] / etab_df["etp"]
        etab_df["has_pdata"] = etab_df["tension"].notna()
        return etab_df

    def etab_corrections(self, bor: str, etab: pd.DataFrame) -> pd.DataFrame:
        if bor in ["pharma", "ehpad"]:
            etab = etab[etab['year'] != 2018]
            rows_2017 = etab[etab['year'] == 2017].copy()
            rows_2018 = rows_2017.assign(year=2018)
            etab = pd.concat([etab, rows_2018], ignore_index=True)
        return etab

    def gdf_corrections(self, bor: str, gdf: pd.DataFrame) -> pd.DataFrame:
        if bor in ["pharma", "ehpad"]:
            gdf = gdf[gdf['year'] != 2018]
            rows_2017 = gdf[gdf['year'] == 2017].copy()
            rows_2018 = rows_2017.assign(year=2018)
            gdf = pd.concat([gdf, rows_2018], ignore_index=True)
        return gdf

    def get_sae_export(self, code: str,
                       studies_df: pd.DataFrame,
                       gdf: pd.DataFrame,
                       etab_df: pd.DataFrame,
                       years: list[int]) -> tuple[dict, any]:
        center_lat = gdf.geometry.centroid.y.mean()  # 45.1209 5.5901
        center_lon = gdf.geometry.centroid.x.mean()
        gdf["km"] = gdf["km"].fillna(60)
        gdf["time_hc"] = gdf["time_hc"].fillna(60)
        gdf["time_hp"] = gdf["time_hp"].fillna(60)
        gdf["pop"] = gdf["pop"].fillna(0)
        dico = {"center_lat": center_lat, "center_lon": center_lon, "q": code, "meanws": [], "years": {}}
        cols = ['code_insee', 'nom_commune', 'lon', 'lat', 'fid', 'year', 'code_iris', 'nom_iris', "geometry",
                "km", "time_hc", "time_hp", "rs", "fi", "pop"]
        export = gdf[cols]
        etab_df["etpsal"] = etab_df["etpsal"].fillna(-1)
        etab_df["efflib"] = etab_df["efflib"].fillna(-1)
        etab_df["etp"] = etab_df["etp"].fillna(-1)
        etab_df["tension"] = etab_df["tension"].fillna(-1).replace([np.inf, -np.inf], -1)
        etab_df["passu"] = etab_df["passu"].fillna(-1)
        etab_df["has_pdata"] = etab_df["has_pdata"].fillna(False)
        cols = ["year", "fi", "passu", "has_pdata", "etp", "efflib", "etpsal", "rs", "lon", "lat", "tension"]
        export_etab = etab_df[cols]
        for year in years:
            meanw = studies_df[studies_df["year"] == year + 2000]["meanw"].iloc[0]
            if meanw is None:
                meanw = 1
            dico["meanws"].append(meanw)
            export_year = export[export["year"] == year + 2000]
            export_etab_year = export_etab[export_etab["year"] == year + 2000]
            dico_year = {}
            etab_year = {}
            for col in export.columns:
                if col != "geometry":
                    dico_year[col] = export_year[col].values.tolist()
            for col in export_etab.columns:
                etab_year[col] = export_etab_year[col].values.tolist()
            if len(etab_year["rs"]) > 500:  # 576 urgence_gen in france
                for col in export_etab.columns:
                    etab_year[col] = []
            dico_year["etab"] = etab_year
            dico["years"][year + 2000] = dico_year
        first_year = years[0]
        if len(gdf) > 0:
            gdf = gdf.sort_values(by="year")
            first_year = gdf["year"].unique()[0]
        gdf_first_year = gdf[gdf["year"] == first_year]
        geojson = gdf_first_year[["fid", "geometry"]].__geo_interface__
        print(f"Found {len(geojson["features"])} geojsons")
        return dico, geojson

    def compute_sae_iris(self, code: str, specialite: int, time: int, time_type: str, resolution: str)\
            -> tuple[dict, any]:
        bor = self.bors[specialite - 1]
        years = self.years_list(bor)
        print(f"Compute IRIS SAE for {code} {bor}")
        self.check_time_type(time_type)
        type_code, id = self.check_code(code)
        sae, studies_df = self.get_sae(type_code, id, bor, time, time_type)
        gdf = self.get_iris_gdf_by_type_code_id(type_code, id)
        print(f"Found {len(gdf)} gdfs")
        etab_df = self.get_sae_by_bor(bor, gdf)
        etab_df = self.etab_tension(etab_df)
        etab_df = self.etab_corrections(bor, etab_df)
        print(f"Found {len(etab_df) / len(years):.0f} etab by year")
        gdf_merged = self.merge_iris_gdf_apl(gdf, sae)
        gdf_merged = self.gdf_corrections(bor, gdf_merged)
        gdf_merged = self.simplify(gdf_merged, resolution)
        print(f"Merged {len(gdf_merged) / len(years):.0f} gdf-saes by year")
        export = self.get_sae_export(code, studies_df, gdf_merged, etab_df, years)
        return export

    def compute_sae_iris_csv(self, code: str, specialite: int, time: int, time_type: str) -> pd.DataFrame:
        bor = self.bors[specialite - 1]
        years = self.years_list(bor)
        print(f"Compute IRIS SAE CSV for {code} {specialite}")
        self.check_time_type(time_type)
        type_code, id = self.check_code(code)
        sae, _ = self.get_sae(type_code, id, bor, time, time_type)
        return sae[["km", "time_hc", "time_hp", "fi", "rs", "lon", "lat", "passu", "etpsal", "efflib", "etp",
                    "tension", "iris_string", "iris_label", "code_commune", "commune_label", "pop", "meanw", "year"]]

    def compute_sae_commune(self, code: str, specialite: int, time: int, time_type: str, resolution: str) \
            -> tuple[dict, any]:
        bor = self.bors[specialite - 1]
        years = self.years_list(bor)
        print(f"Compute Commune SAE for {code} {bor}")
        self.check_time_type(time_type)
        type_code, id = self.check_code(code)
        sae, studies_df = self.get_sae(type_code, id, bor, time, time_type)
        gdf = self.get_commune_gdf_by_type_code_id(type_code, id, resolution)
        print(f"Found {len(gdf)} gdfs")
        # TODO migrate an.iris => geo_iris (ok pour apl)
        etab_df = self.get_sae_by_bor(bor, gdf) # TODO Refaire toutes les fonctions SQL au niveau commune gdf["code"]
        # etab_df = self.etab_tension(etab_df)
        # etab_df = self.etab_corrections(bor, etab_df)
        # print(f"Found {len(etab_df) / len(years):.0f} etab by year")
        # gdf_merged = self.merge_commune_gdf_apl(gdf, apl)
        # print(f"Merged {len(gdf_merged) / len(self.years):.0f} gdf-apls by year")
        # gdf_commune = self.group_apl_by_commune(gdf_merged)
        # gdf_commune = self.gdf_merge_add_columns(gdf_commune)
        # export = self.get_export(code, studies_df, gdf_commune)
        # return export



if __name__ == '__main__':
    pd.set_option('display.max_columns', None)
    pd.options.display.width = 0
    s = SAEService()
    time.sleep(1)
    # export = s.compute_sae_iris("CC-69072", 1, 60, "HC", "HD")
    # s = json.dumps(export)
    # print(s[:5000])
    # df = s.compute_sae_iris_csv("CC-38185",1,60,"HC")
    export = s.compute_sae_commune("CC-38205", 1, 60, "HC", "HD")





