import pandas as pd
import numpy as np
import config
from sqlalchemy import text
import datetime
import random
print(config.version)
print(config.connection_string)
pd.set_option('display.max_columns', None)
pd.options.mode.copy_on_write = True


def get_sae(year, bor):
    sql = f"select * from sae.bor where id={bor}"
    df = pd.read_sql(sql, config.connection_string)
    table = df["table"].iloc[0]
    column = df["column"].iloc[0]
    condition = df["condition"].iloc[0]
    sql = f"""
select e.id, ud.{column} score, e.nofinesset, e.rs, e.rslongue, an.dept_id, an.id adresse_norm_id, i.id iris, an.lon, an.lat
from sae.{table} ud
join etablissement e on e.nofinesset=ud.fi
join adresse_raw ar on e.adresse_raw_id=ar.id
join adresse_norm an on ar.adresse_norm_id=an.id
join iris.iris i on i.code=an.iris
where ud.an={year}
and {condition}
"""
    # TODO tester cette requete en ajoutant les jointures petit à petit sur serveur
    print(f"Quering SAE for year {year} and bor {bor}")
    print(sql)
    return pd.read_sql(sql, config.connection_string)


def get_pop_iris(year):
    yy=min(21, year)
    sql = f"""
select i.id iris, pi.iris iris_string, c.code code_commune, i.type type_iris, pi.pop, pi.pop0002, pi.pop0305, pi.pop0610, pi.pop1117, pi.pop1824, pi.pop2539, pi.pop4054, pi.pop5564, pi.pop6579, pi.pop80p
from iris.pop_iris pi
join iris.iris i on  pi.iris=i.code
join iris.commune c on i.commune_id=c.id
where year={yy}
"""
    print(f"Get pop_iris for year {yy}")
    return pd.read_sql(text(sql), config.connection_string)


def get_iris_matrix(time: int, time_type: str):
    sql = f"""
(select iris.id "iris1", iris.id "iris2", 0 "km", 0 "time_hc", 0 "time_hp" from iris.iris
union
select iris_id_from as "iris1", iris_id_to "iris2", route_km "km", route_min "time_hc", route_hp_min "time_hp" from iris.iris_matrix
where route_min <= {time}) order by "iris1", "iris2"
"""
    print(f"Get iris_matrix for time {time} {time_type}")
    m = pd.read_sql(sql, config.connection_string)
    m["time"] = m[f"time_{time_type.lower()}"].copy()
    return m


def get_iriss(year, bor):
    sql = f"""
select i.id "iris", i.code "iris_string", i.nom "iris_label", c.dept_id "dept", c.code "code_commune", c.nom "commune_label", {year} "year", {bor} "bor" from iris.iris i
join iris.commune c on c.id=i.commune_id
"""
    # print(sql)
    return pd.read_sql(text(sql), config.connection_string)

#TEST ONLY to remove
ps_df = get_sae(2024, 1)

for time in [30]:
    for time_type in ["HP"]:
        iris_matrix = get_iris_matrix(time, time_type)
        iris_matrix["iris"] = iris_matrix["iris2"].astype("int64")
        iris_matrix["time"] = iris_matrix[f"time_{time_type.lower()}"].copy()
        for year in range(2013, 2025):
            pop_iris = get_pop_iris(year)
            for bor in [1]:
                iriss = get_iriss(year, bor)
                for accessibilite_exp in [-0.12]:
                    if ((time > 30 and accessibilite_exp < -0.08) or
                            (time == 30 and accessibilite_exp > -0.06) or
                            (time > 45 and accessibilite_exp < -0.06)):
                        continue

                    print(f"Compute APL bor {bor} in {year} in {time}min {time_type}, e={accessibilite_exp}")
                    ps_df = get_sae(year, bor)
                    ps_df["score"] = ps_df["score"].fillna(0)
                    ps_df = ps_df.sort_values(by='iris')
                    ps_df2 = ps_df.drop_duplicates(subset=['iris'])

                    iris_matrix_pop_df = iris_matrix.merge(pop_iris, on="iris", how="left", suffixes=('', ''))

                    accessibilite_fn = lambda x: np.exp(accessibilite_exp * x)
                    iris_matrix_pop_df["accessibilite_weight"] = accessibilite_fn(iris_matrix_pop_df["time"])
                    iris_matrix_pop_df.head(10)

                    cols = [col for col in iris_matrix_pop_df.columns if "pop" in col and col != "pop"]
                    weights = [1.0] * len(cols)

                    iris_matrix_pop_df["pop_gp"] = sum(w * iris_matrix_pop_df[c] for w, c in zip(weights, cols))
                    iris_matrix_pop_df=iris_matrix_pop_df.sort_values(by='iris2')

                    matrix_df = iris_matrix_pop_df[["iris1","iris2","km","time","accessibilite_weight","pop_gp","pop","type_iris"]]

                    matrix_df["iris"] = matrix_df["iris1"].copy()
                    matrix_df = matrix_df.sort_values(by='iris2')
                    matrix_merge_df = matrix_df.merge(ps_df2, on="iris", how="left", suffixes=('', ''))
                    matrix_merge_df["nb"] = matrix_merge_df["nb"].fillna(0)
                    matrix_merge_df = matrix_merge_df.sort_values(by=['iris1', "iris2"])

                    matrix_merge_df["wpop"] = matrix_merge_df["accessibilite_weight"] * matrix_merge_df["pop_gp"]
                    matrix_merge_df["swpop"] = matrix_merge_df.groupby("iris1")["wpop"].transform("sum")
                    matrix_merge_df["R"] = (matrix_merge_df["nb"] / (matrix_merge_df["swpop"] / 100000)).replace(np.inf, 0)

                    rgp = matrix_merge_df[matrix_merge_df["iris1"] == matrix_merge_df["iris2"]]
                    rgp = rgp[["iris1", "iris2", "type_iris", "pop_gp", "nb", "R", "swpop", "wpop", "pop_gp", "pop"]].copy()

                    apl = matrix_merge_df.merge(rgp, on="iris2", suffixes=("", "_dest"))
                    apl = apl.sort_values(by=['iris1', "iris2"])
                    apl["ap"] = apl["accessibilite_weight"] * apl["R_dest"]

                    apl["apl"] = apl.groupby("iris1")["ap"].transform("sum")

                    apl2 = apl[apl["iris1"] == apl["iris2"]]

                    dico = {"year":year, "bor_id":bor, "time":time, "time_type":time_type, "exp":accessibilite_exp}
                    dico["mean"] = np.mean(apl2["apl"])
                    dico["std"] = np.std(apl2["apl"])
                    dico["q10"], dico["q25"], dico["q50"], dico["q75"], dico["q90"] = np.quantile(apl2["apl"], [0.1, 0.25, 0.5, 0.75, 0.9])
                    dico["min"] = np.min(apl2["apl"])
                    dico["max"] = np.max(apl2["apl"])
                    dico["date"] = datetime.datetime.now()
                    dico["key"] = random.randint(0, 1000000000000)

                    study = pd.DataFrame(dico, index=[dico["key"]])

                    apl3 = apl2[["iris1", "type_iris", "nb", "apl", "ap", "accessibilite_weight", "wpop", "swpop", "R", "pop_gp","pop"]]
                    apl3 = apl3.rename(columns={'iris1': 'iris'})

                    apl_final = apl3.merge(iriss, on="iris", how="left", suffixes=("", "_dest"))
                    apl_final = apl_final[["year", "specialite", "iris", "iris_string", "type_iris", "nb", "apl", "ap", "accessibilite_weight", "R", "wpop", "swpop", "pop_gp","pop", "iris_label", "dept", "code_commune", "commune_label"]]

                    sum_pop = np.sum(apl_final["pop_gp"])
                    apl_final["meanw"] = apl_final["apl"] * apl_final["pop_gp"] * len(apl_final) / sum_pop
                    study["meanw"] = np.mean(apl_final["meanw"])

                    apl_final["year"]=year
                    apl_final["study_key"]=dico["key"]
                    study.to_sql("apl_study", config.connection_string, schema="sae", if_exists="append", index=False)
                    apl_final.to_sql("apl", config.connection_string, schema="sae", if_exists="append", index=False)



