import pandas as pd
import geopandas as gpd
import threading
import time
import pickle
import os


class IrisLoader(threading.Thread):

    _instance = None
    lock = threading.RLock()

    def __init__(self):
        super().__init__()
        self.time0 = time.perf_counter()
        self.gdf = pd.DataFrame()
        self.geojson = None
        self.file = f"data/contours-iris.gpkg"

    @staticmethod
    def factory():
        with IrisLoader.lock:
            if IrisLoader._instance is None:
                IrisLoader._instance = IrisLoader()
                IrisLoader._instance.start()
        return IrisLoader._instance

    def load_gpkg(self):
        print(f"Loading {self.file}")
        self.gdf = gpd.read_file(self.file)
        self.gdf = self.gdf.to_crs(epsg=4326)
        self.gdf["fid"] = self.gdf.index
        self.gdf["lon"] = self.gdf.geometry.centroid.x
        self.gdf["lon"] = self.gdf.geometry.centroid.x
        self.gdf["lat"] = self.gdf.geometry.centroid.y
        self.gdf = self.gdf.sort_values(by="code_iris")
        duration = time.perf_counter() - self.time0
        print(f"Found {len(self.gdf)} iris in {duration:.0f}s")

    def save(self):
        file = self.file.replace("gpkg", "pickle")
        with open(file, "wb") as f:
            print(f"Saving {file}")
            pickle.dump(self.gdf, f)

    def load(self):
        file = self.file.replace("gpkg", "pickle")
        if os.path.exists(file):
            with open(file, "rb") as f:
                print(f"Loading {file}")
                self.gdf = pickle.load(f)
        else:
            self.load_gpkg()
        print(f"Found {len(self.gdf)} iris")
        # self.geojson = self.gdf.__geo_interface__
        # print(f"Found {len(self.geojson['features'])} geojson")


    def run(self):
        self.load()


if __name__ == '__main__':
    s = IrisLoader()
    s.load()
