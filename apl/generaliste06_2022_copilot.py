import pandas as pd
import numpy as np

# Chargement des fichiers .dta
gene = pd.read_stata("Gene06.dta")
od = pd.read_stata("ODFinale.dta")
pop_iris = pd.read_stata("popIRIS.dta")
nom_iris = pd.read_stata("NomIRIS.dta")

# Étape 1 : concaténation et comptage des localisations uniques
gene["b"] = gene["id"].astype(str) + gene["lat"].astype(str) + gene["lon"].astype(str)
gene["unique"] = gene.groupby("id")["b"].transform("nunique")
gene["un"] = gene["unique"]

# Pondération selon le nombre d'adresses
conditions = [
    gene["un"] == 1,
    gene["un"] == 2,
    gene["un"] == 3,
    gene["un"] == 4
]
weights = [1, 0.5, 0.33, 0.25]
gene["weight"] = np.select(conditions, weights, default=0)

# Nombre de médecins ETP par iris
nbgp = gene.groupby("iris", as_index=False)["weight"].sum().rename(columns={"weight": "NB"}).drop_duplicates()

# Étape 2 : Nettoyage de la base OD et jointure avec la population
od = od[od["TIME"] <= 30].copy()
od["iris"] = od["IRIS2"].astype("int64")
od = od.merge(pop_iris, on="iris", how="left")
od["WexpGP"] = np.exp(-0.12 * od["TIME"])

# Calcul de la population pondérée par âge
pop_cols = ["P19_POP0002", "P19_POP0305", "P19_POP0610", "P19_POP1117", "P19_POP1824", "P19_POP2539", "P19_POP4559", "P19_POP6074", "P19_POP75P"]
weights = [0.759201627]*4 + [0.784999993, 0.915, 1.05, 1.4, 1.3]
for col in pop_cols:
    od[col] = pd.to_numeric(od[col], errors="coerce")
od["POPGP"] = sum(w * od[c] for w, c in zip(weights, pop_cols))

# Étape 3 : Fusion avec le nombre de médecins par iris d’origine
od["iris"] = od["IRIS1"]
od = od.merge(nbgp, on="iris", how="left")
od["NB"] = od["NB"].fillna(0)

# Calcul de la demande adressable et du ratio R
od["wpop"] = od["WexpGP"] * od["POPGP"]
od["swpop"] = od.groupby("IRIS1")["wpop"].transform("sum")
od["R"] = od["NB"] / (od["swpop"] / 100000)

# Extraction des lignes où IRIS1 == IRIS2 pour calculer APL
rgp = od[od["IRIS1"] == od["IRIS2"]][["IRIS1", "TYP_IRIS", "POPGP", "NB", "R"]].copy()
rgp["IRIS2"] = rgp["IRIS1"]

# Étape 4 : Fusion avec RGP pour calculer APL
od = od.merge(rgp[["IRIS2", "R"]], on="IRIS2", suffixes=("", "_dest"))
od["Ap"] = od["WexpGP"] * od["R_dest"]
od["APL"] = od.groupby("IRIS1")["Ap"].transform("sum")

# Résultat final
apl_final = od[od["IRIS1"] == od["IRIS2"]][["IRIS1", "TYP_IRIS", "NB", "APL"]]

# Fusion avec les noms d’IRIS
apl_final = apl_final.merge(nom_iris, on="IRIS1", how="left")

# Sauvegarde finale
apl_final.to_stata("APL06_2022_Final.dta", write_index=False)