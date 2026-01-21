import pandas as pd
import unidecode
import config
import threading
import time
import pickle
import datetime
import os
from collections import OrderedDict


class Indexer(threading.Thread):

    def __init__(self, nb_limit=99, commune_length_limit=255, join_type="C"):
        super().__init__()
        self.time0 = time.perf_counter()
        self.nb_limit = nb_limit
        self.q_limit = commune_length_limit
        self.join_type = join_type  # TODO C pour commune I pour Iris (cf ligne 38)
                                    # Mettre les communes associées deleguées
        self.df = pd.DataFrame()
        self.ban = pd.DataFrame()
        self.db: dict[str, dict[str, str]] = {}
        self.limit_year = 2020
        self.file = f"data/index_{datetime.datetime.now().year}{datetime.datetime.now().month:02d}.pickle"

    def load_commune(self):
        sql = f"""select c.code, c.nom, c.nom_norm, c.epci_id, c.epci_nom, c.bassin_vie_id, c.bassin_vie_nom, c.old_nom,
        c.old_nom_norm , c.arr_dept_id, c.arr_dept_nom, d.num dept, d.name dept_name, d.region_id, d.region_name
        from iris.commune c
        join dept d on c.dept_id=d.id
        where (c.date_fin is null or c.date_fin >= '{self.limit_year}-01-01')
        """
        print("Querying commune")
        self.df = pd.read_sql(sql, config.connection_string)
        duration = time.perf_counter() - self.time0
        print(self.df.columns)
        print(f"Found {len(self.df)} communes in {duration:.0f}s")
        # TODO Join sur iris ou commune en fonction de la cible, par exemple 75101 est présent en iris mais pas en commune

    def load_ban(self):
        sql = "select distinct(code_postal, code_insee) from ban"
        print("Querying BAN")
        self.ban = pd.read_sql(sql, config.connection_string)
        duration = time.perf_counter() - self.time0
        self.ban["cp"] = self.ban["row"].apply(lambda x: f"{int(x[1:-1].split(",")[0]):05d}")
        self.ban["code"] = self.ban["row"].apply(lambda x: x[1:-1].split(",")[1])
        print(f"Found {len(self.ban)} CP in {duration:.0f}s")

    def merge_ban(self):
        self.ban["communes"] = ""
        cps = self.ban["cp"].drop_duplicates()
        for cp in cps:
            communes = []
            bans = self.ban[self.ban["cp"] == cp]
            for _, ban in bans.iterrows():
                df = self.df[self.df["code"] == ban["code"]]
                for __, commune in df.iterrows():
                    communes.append(commune["nom"])
            if len(communes) > 3:
                communes[3] = "..."
                communes = communes[:4]
            self.ban.loc[self.ban["cp"] == cp, "communes"] = ", ".join(communes)
        self.ban = self.ban.drop_duplicates(["cp"])
        self.ban = self.ban[self.ban["communes"] != ""]

    def normalize_string(self, s: str) -> str:
        s = s.strip().upper()
        s = unidecode.unidecode(s).replace("'", " ").replace("-", " ").replace("/", " ").replace(".", "")
        return s

    def split(self, s: str) -> list[str]:
        if s is None:
            return []
        s = s.strip()
        res = [s]
        for i in range(0, len(s)):
            if s[i] == " ":
                sub = s[i + 1:]
                if len(sub) > 3:
                    res.append(sub)
        return res

    def index(self, strings: list[str], serie: pd.Series, code: str, code_col: str, value_col: str):
        for s in strings:
            if s is not None:
                for i in range(1, min(len(s) + 1, self.q_limit)):
                    key = s[:i]
                    if key[-1] != " ":
                        if key not in self.db:
                            self.db[key] = OrderedDict()
                        item = self.db[key]
                        if len(item) < self.nb_limit or len(serie[value_col]) == i:
                            fk = f"{code}-{serie[code_col]}"
                            if fk not in item:
                                item[fk] = serie[value_col]

    def index_code_communes(self):
        nb = len(self.db)
        for _, serie in self.df.iterrows():
            self.index([serie["code"]], serie, "CC", "code", "nom")
        duration = time.perf_counter() - self.time0
        print(f"Index {len(self.db) - nb} CC in {duration:.0f}s")

    def index_commune_noms(self):
        nb = len(self.db)
        for _, serie in self.df.iterrows():
            self.index(self.split(serie["nom_norm"]), serie, "CC", "code", "nom")  # Faire multi mots
            # self.index(self.split(serie["old_nom_norm"]), serie, "CC", "code", "nom")
        duration = time.perf_counter() - self.time0
        print(f"Index {len(self.db) - nb} CC in {duration:.0f}s")

    def index_regions(self):
        df: pd.DataFrame = self.df[["region_id", "region_name"]].drop_duplicates()
        df["region_name_norm"] = df["region_name"].apply(lambda x: self.normalize_string(x))
        print(f"Found {len(df)} regions")
        nb = len(self.db)
        for _, serie in df.iterrows():
            self.index(self.split(serie["region_name_norm"]), serie, "CR", "region_id", "region_name")
        duration = time.perf_counter() - self.time0
        print(f"Index {len(self.db) - nb} CR in {duration:.0f}s")

    def index_depts(self):
        df: pd.DataFrame = self.df[["dept", "dept_name"]].drop_duplicates()
        df["dept_name_norm"] = df["dept_name"].apply(lambda x: self.normalize_string(x))
        print(f"Found {len(df)} departments")
        nb = len(self.db)
        for _, serie in df.iterrows():
            self.index(self.split(serie["dept_name_norm"]), serie, "CD", "dept", "dept_name")
            self.index(self.split(serie["dept"]), serie, "CD", "dept", "dept_name")
        duration = time.perf_counter() - self.time0
        print(f"Index {len(self.db) - nb} CD in {duration:.0f}s")

    def index_epcis(self):
        df: pd.DataFrame = self.df[["epci_id", "epci_nom"]].drop_duplicates()
        df = df.dropna()
        df["epci_nom_norm"] = df["epci_nom"].apply(lambda x: self.normalize_string(x))
        df["epci_id"] = df["epci_id"].astype(int).astype(str)
        print(f"Found {len(df)} epcis")
        nb = len(self.db)
        for _, serie in df.iterrows():
            self.index(self.split(serie["epci_nom_norm"]), serie, "CE", "epci_id", "epci_nom")
        duration = time.perf_counter() - self.time0
        print(f"Index {len(self.db) - nb} CE in {duration:.0f}s")

    def index_arrondissements(self):
        df: pd.DataFrame = self.df[["arr_dept_id", "arr_dept_nom"]].drop_duplicates()
        df = df.dropna()
        df["arr_dept_nom_norm"] = df["arr_dept_nom"].apply(lambda x: self.normalize_string(x))
        print(f"Found {len(df)} arrondissements")
        nb = len(self.db)
        for _, serie in df.iterrows():
            self.index(self.split(serie["arr_dept_nom_norm"]), serie, "CA", "arr_dept_id", "arr_dept_nom")
        duration = time.perf_counter() - self.time0
        print(f"Index {len(self.db) - nb} CA in {duration:.0f}s")

    def index_cps(self):
        print(f"Found {len(self.ban)} cps")
        nb = len(self.db)
        for _, serie in self.ban.iterrows():
            self.index(self.split(serie["cp"]), serie, "CP", "cp", "communes")
        duration = time.perf_counter() - self.time0
        print(f"Index {len(self.db) - nb} CP in {duration:.0f}s")

    def save(self):
        with open(self.file, "wb") as f:
            print(f"Saving {self.file}")
            pickle.dump(self.db, f)

    def load_or_index(self):
        if os.path.exists(self.file):
            with open(self.file, "rb") as f:
                print(f"Loading {self.file}")
                self.db = pickle.load(f)
        else:
            self.indexer()
        print(f"Found {len(self.db)} indexes")

    def indexer(self):
        print("Starting indexer")
        self.load_commune()
        self.index_depts()
        self.index_regions()
        self.index_code_communes()
        self.index_commune_noms()
        self.index_epcis()
        self.index_arrondissements()
        self.load_ban()
        self.merge_ban()
        self.index_cps()
        self.save()

    def run(self):
        self.load_or_index()


if __name__ == '__main__':
    s = Indexer()
    # s.indexer()
    s.load_or_index()

    # s.start()
    # print(f"Thread 0s:{len(s.db)}")
    # time.sleep(1)
    # print(f"Thread 1s:{len(s.db)}")
    # time.sleep(1)
    # print(f"Thread 2s:{len(s.db)}")
    # s.join()
    # print(f"Thread end:{len(s.db)}")

