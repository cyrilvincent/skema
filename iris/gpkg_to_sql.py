import pandas as pd
import numpy as np
import config
import datetime
from sqlalchemy import text, create_engine
import plotly
import plotly.express as px
import ipywidgets
from urllib.request import urlopen
import json
import plotly.graph_objects as go
import geopandas as gpd
import warnings
import pyproj
import plotly.io as pio
print(config.version)
print(config.connection_string)

gdf = gpd.read_file("contours-iris.gpkg")
gdf = gdf[gdf["nom_commune"] == "Grenoble"].to_crs(epsg=4326)
gdf_l93 = gdf.to_crs(2154)
pts_l93 = gdf_l93.geometry.representative_point()
pts = pts_l93.to_crs(4326)
gdf["fid"] = gdf.index
gdf["lon"] = gdf.geometry.centroid.x
gdf["lat"] = gdf.geometry.centroid.y
gdf=gdf.sort_values(by="code_iris")
gdf["year"] = 25
geojson=gdf.__geo_interface__
print(geojson)

# engine = create_engine(config.connection_string)
# gdf.to_postgis("gdf", engine, schema="iris", if_exists="replace")

# gdf = gpd.read_postgis("select * from iris.gdf g", config.connection_string, geom_col="geometry")
# print(gdf)
# geojson = gdf.__geo_interface__
# print(geojson)