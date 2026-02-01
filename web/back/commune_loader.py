import warnings

import pandas as pd
import geopandas as gpd
import threading
import time
import pickle
import os


class CommuneLoader(threading.Thread):

    _instance = None
    lock = threading.RLock()

    def __init__(self):
        super().__init__()
        warnings.filterwarnings('ignore', category=UserWarning)
        self.time0 = time.perf_counter()
        self.gdfs: dict[str, pd.DataFrame] = {}
        self.file_name = "data/communes-{nb}m-2024.geojson"

    @staticmethod
    def factory():
        with CommuneLoader.lock:
            if CommuneLoader._instance is None:
                CommuneLoader._instance = CommuneLoader()
                CommuneLoader._instance.start()
        return CommuneLoader._instance

    def load_gdf(self, nb: int) -> pd.DataFrame:
        file = self.file_name.replace("{nb}", str(nb))
        print(f"Loading {file}")
        gdf = gpd.read_file(file)
        gdf = gdf[gdf["departement"].str.len() == 2]
        duration = time.perf_counter() - self.time0
        print(f"Found {len(gdf)} communes in {duration:.0f}s")
        return gdf

    def load_gdfs(self):
        self.gdfs["HD"] = self.load_gdf(50)
        self.gdfs["MD"] = self.load_gdf(100)
        self.gdfs["HD"] = self.load_gdf(1000)

    def run(self):
        self.load_gdfs()


if __name__ == '__main__':
    s = CommuneLoader()
    s.load_gdfs()
