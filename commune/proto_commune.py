
import os
import json
import random
import numpy as np
import geopandas as gpd
import plotly.graph_objects as go

# ---------------------------------
# Paramètres
# ---------------------------------
LOCAL_GEOJSON_PATH = "communes_fr.geojson"   # fichier local après téléchargement
ENABLE_SIMPLIFY = True                       # simplifier pour accélérer l'affichage
SIMPLIFY_TOLERANCE_M = 50                    # ~50 m en EPSG:3857 (ajuste si besoin)

# URLs publiques candidates (essayées dans l'ordre)
CANDIDATE_URLS = [
    "https://france-geojson.gregoiredavid.fr/repo/communes.geojson", # Vieux2018
    "https://raw.githubusercontent.com/gregoiredavid/france-geojson/master/communes.geojson", #Vieux2018
    "https://etalab.github.io/cerema-geojson/communes.geojson", #Ne fonctionne pas
]

# ---------------------------------
# Utilitaires
# ---------------------------------
def try_download(urls, out_path):
    """Télécharge un GeoJSON depuis la première URL valide et le sauvegarde en local."""
    import urllib.request
    for url in urls:
        try:
            print(f"→ Téléchargement : {url}")
            with urllib.request.urlopen(url, timeout=60) as resp:
                data = resp.read()
                text = data.decode("utf-8")
                obj = json.loads(text)
                if obj.get("type") == "FeatureCollection":
                    with open(out_path, "w", encoding="utf-8") as f:
                        f.write(text)
                    print(f"✔ Enregistré dans {out_path}")
                    return out_path
                else:
                    print("⚠ Contenu non FeatureCollection.")
        except Exception as e:
            print(f"⚠ Échec : {e}")
    return None

def pick_first_present(gdf, candidates, default=None):
    """Retourne la première colonne de gdf présente parmi candidates."""
    for c in candidates:
        if c in gdf.columns:
            return c
    return default

def ensure_epsg4326(gdf):
    """Assure un CRS WGS84 (EPSG:4326) pour compatibilité avec Plotly."""
    try:
        if gdf.crs is not None and gdf.crs.to_epsg() != 4326:
            return gdf.to_crs(epsg=4326)
    except Exception:
        pass
    return gdf

def simplify_geometries(gdf, tolerance_m=50):
    """Simplifie en EPSG:3857 puis revient en EPSG:4326 (gain de performance)."""
    try:
        gdf_3857 = gdf.to_crs(epsg=3857)
        gdf_3857["geometry"] = gdf_3857.geometry.simplify(
            tolerance=tolerance_m, preserve_topology=True
        )
        return gdf_3857.to_crs(epsg=4326)
    except Exception as e:
        print(f"⚠ Simplification impossible : {e}")
        return gdf

# ---------------------------------
# 1) Télécharger le GeoJSON si absent
# ---------------------------------
if not os.path.exists(LOCAL_GEOJSON_PATH):
    if try_download(CANDIDATE_URLS, LOCAL_GEOJSON_PATH) is None:
        raise RuntimeError(
            "Impossible de télécharger un GeoJSON des communes. "
            "Fournissez un chemin local valide."
        )

# ---------------------------------
# 2) Charger le GeoJSON
# ---------------------------------
print("→ Chargement du GeoJSON…")
gdf = gpd.read_file(LOCAL_GEOJSON_PATH)

# ---------------------------------
# 3) Colonnes clés (INSEE et NOM)
# ---------------------------------
candidate_insee = ["code", "insee", "code_insee", "INSEE_COM", "INSEE"]
candidate_name  = ["nom", "name", "NOM_COM", "NOM", "libelle", "LIBELLE"]

insee_col = pick_first_present(gdf, candidate_insee)
name_col  = pick_first_present(gdf, candidate_name)

# Si absentes, créer des colonnes par défaut
if insee_col is None:
    insee_col = "insee_auto"
    gdf[insee_col] = np.arange(len(gdf)).astype(str)
if name_col is None:
    name_col = "nom_auto"
    gdf[name_col] = "Commune_" + gdf[insee_col].astype(str)

print(f"→ INSEE : {insee_col}")
print(f"→ NOM   : {name_col}")

# ---------------------------------
# 4) Harmoniser CRS + (option) simplifier
# ---------------------------------
gdf = ensure_epsg4326(gdf)
if ENABLE_SIMPLIFY:
    print(f"→ Simplification géométrique (≈ {SIMPLIFY_TOLERANCE_M} m)…")
    gdf = simplify_geometries(gdf, SIMPLIFY_TOLERANCE_M)

# ---------------------------------
# 5) Couleur/valeur aléatoire pour la choropleth
#    (Plotly CHOROPLETH utilise une palette continue basée sur z)
# ---------------------------------
gdf["random_value"] = np.random.rand(len(gdf))

# ---------------------------------
# 6) Construire la trace go.Choropleth (sans express)
# ---------------------------------
geojson_dict = gdf.__geo_interface__
featureidkey = f"properties.{insee_col}"

choropleth = go.Choropleth(
    geojson=geojson_dict,
    featureidkey=featureidkey,
    locations=gdf[insee_col],       # correspond à featureidkey
    z=gdf["random_value"],          # valeur numérique aléatoire par commune
    colorscale="Viridis",
    marker_line_color="black",
    marker_line_width=0.05,
    colorbar_title="Aléatoire",
    hovertext=gdf[name_col],
    hovertemplate="%{hovertext}<br>Valeur: %{z:.3f}<extra></extra>",
)

fig = go.Figure(choropleth)

# Adapter la vue à la France et cacher axes
fig.update_geos(
    projection_type="mercator",
    fitbounds="locations",
    visible=False
)

fig.update_layout(
    title="Communes de France — couleurs aléatoires (Plotly Graph Objects • Choropleth)",
    margin=dict(r=0, t=40, l=0, b=0),
    height=800,
    template="plotly_white",
)

print("→ Affichage Plotly…")
fig.show()
print("✔ Terminé.")

