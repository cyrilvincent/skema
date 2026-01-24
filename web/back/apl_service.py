from collections import OrderedDict
import threading
import time
from iris_loader import IrisLoader
from service_error import ServiceError
import re
import pandas as pd
import config

class APLService:

    _instance = None
    lock = threading.RLock()

    def __init__(self):
        self.iris_loader = IrisLoader.factory()
        self.years = list(range(20, 26))
        self.regex = re.compile(r"^C[CDRAE]-\d[\dAB]\d*$")

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

    def get_cc(self, id: str) -> tuple[list[str], str | None]:
        sql = f"""
        select i.*, c.nom commune_nom from iris.commune c
        join iris.iris i on i.commune_id=c.id
        where c.code='{id}'
        order by i.id
        """
        print(sql)
        iris_df = pd.read_sql(sql, config.connection_string)
        iriss = iris_df["code"].to_list()
        commune_nom = iris_df["commune_nom"].iloc[0] if len(iris_df) > 0 else None
        return iriss, commune_nom

    def get_by_type_code(self, type_code: str, id: str) -> tuple[list[str], str | None]:
        if type_code == "CC":
            return self.get_cc(id)
        else:
            raise ServiceError(f"Bad type code: {type_code}")

    def compute(self, code: str, specialite: int, time: int, time_type: str, aexp: float):
        print(f"Compute APL for {code} {specialite} {time} {time_type} {aexp}")
        self.check_time_type(time_type)
        type_code, id = self.check_code(code)
        commune_nom: str | None = None
        iriss: list[str] = []





if __name__ == '__main__':
    s = APLService()
    time.sleep(1)
    s.compute("CC-38205", 10, 30, "HC", -0.12)
    print(s.get_cc("38205"))
