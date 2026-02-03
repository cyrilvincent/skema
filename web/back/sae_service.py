import json
import threading
import time
import warnings
from typing import Iterable

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
        self.last_year = 25
        self.years = None

    @staticmethod
    def factory():
        with SAEService.lock:
            if SAEService._instance is None:
                SAEService._instance = SAEService()
        return SAEService._instance

    def get_first_year(self, bor: str):
        return 13 if bor not in ["pharma", "ehpad"] else 4

    def years_generator(self, bor: str):
        for y in range(self.get_first_year(bor), self.last_year + 1):
            yield y

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


if __name__ == '__main__':
    pd.set_option('display.max_columns', None)
    pd.options.display.width = 0
    s = SAEService()
    time.sleep(1)
    bor = "urgence_gen"
    years = list(s.years_generator(bor))
    df = s.get_sae_studies_by_years(bor, 60, "HC", years)
    print(df)




