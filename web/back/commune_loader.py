import os
import warnings
import pandas as pd
import geopandas as gpd
import threading
import time
import pickle


class CommuneLoader(threading.Thread):

    _instance = None
    lock = threading.RLock()

    def __init__(self):
        super().__init__()
        self.time0 = time.perf_counter()
        self.gdfs: dict[str, pd.DataFrame] = {}
        self.commune_file = "data/communes-{nb}m-2024.geojson"
        self.associee_file = "data/communes-associees-deleguees-{nb}m.geojson"
        self.pickle_file = "data/communes.pickle"
        self.with_associee = True
        warnings.filterwarnings('ignore', category=UserWarning)

    @staticmethod
    def factory():
        with CommuneLoader.lock:
            if CommuneLoader._instance is None:
                CommuneLoader._instance = CommuneLoader()
                CommuneLoader._instance.start()
        return CommuneLoader._instance

    def load_gdf(self, nb: int, associee: bool) -> pd.DataFrame:
        file = self.commune_file.replace("{nb}", str(nb))
        print(f"Loading {file}")
        gdf = gpd.read_file(file)
        gdf["associee"] = False
        if associee:
            file = self.associee_file.replace("{nb}", str(nb))
            print(f"Loading {file}")
            gdfa = gpd.read_file(file)
            gdfa["associee"] = True
            gdf = pd.concat([gdf, gdfa], ignore_index=True)
        gdf = gdf[gdf["departement"].str.len() == 2]
        gdf = gdf.drop("plm", axis=1)
        gdf["lon"] = gdf["geometry"].centroid.y
        gdf["lat"] = gdf["geometry"].centroid.x
        duration = time.perf_counter() - self.time0
        print(f"Found {len(gdf)} communes in {duration:.0f}s")
        return gdf

    def load_gdfs(self):
        self.gdfs["HD"] = self.load_gdf(50, self.with_associee)
        self.gdfs["MD"] = self.load_gdf(100, self.with_associee)
        self.gdfs["LD"] = self.load_gdf(1000, self.with_associee)
        self.save()

    def run(self):
        self.load_pickle_or_gdfs()

    def save(self):
        with open(self.pickle_file, "wb") as f:
            print(f"Saving {self.pickle_file}")
            pickle.dump(self.gdfs, f)

    def load_pickle_or_gdfs(self):
        if os.path.exists(self.pickle_file):
            with open(self.pickle_file, "rb") as f:
                print(f"Loading {self.pickle_file}")
                self.gdfs = pickle.load(f)
        else:
            self.load_gdfs()
        print(f"Found {len(self.gdfs["HD"])} communes")


if __name__ == '__main__':
    s = CommuneLoader()
    s.run()
    # s.load_gdf(1000, False)
