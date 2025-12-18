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


def get_urgence_sae(year, urg="GEN"):
    sql = f"""
select d.fi, d.passu, p.perso is not null has_pdata, p.etpsal, p.efflib, p.etp, e.id etab_id, e.rs, an.dept_id, an.id adresse_norm_id, an.lon, an.lat, i.id iris 
from sae.urgence_detail d
left join sae.urgence_p p on p.fi=d.fi and p.an=d.an and p.perso='M9999'
join etablissement e on e.nofinesset=d.fi
join adresse_raw ar on e.adresse_raw_id=ar.id
join adresse_norm an on ar.adresse_norm_id=an.id
join iris.iris i on i.code=an.iris
where d.an={year}
and d.urg='{urg}'
"""
    print(f"Quering SAE urgence for year {year} and urg={urg}")
    # print(sql)
    return pd.read_sql(sql, config.connection_string)


def get_psy_sae(year):
    sql = f"""
select p.fi, p.cap_htp passu, true has_pdata, p.etpsal_pkt etpsal, p.efflib_pkt efflib, p.etp_pkt etp, e.id etab_id, e.rs, an.dept_id, an.id adresse_norm_id, an.lon, an.lat, i.id iris 
from sae.psy p
join etablissement e on e.nofinesset=p.fi
join adresse_raw ar on e.adresse_raw_id=ar.id
join adresse_norm an on ar.adresse_norm_id=an.id
join iris.iris i on i.code=an.iris
where p.an={year}
and p.dis='TOT'
"""
    print(f"Quering SAE psy for year {year}")
    # print(sql)
    return pd.read_sql(sql, config.connection_string)


def get_pharma(year):
    sql = f"""
select e.nofinesset fi, null as passu, false as has_pdata, null as etpsal, null as efflib, null as etp, e.id etab_id, e.rs, an.id an_id, an.dept_id, an.id adresse_norm_id, an.lon, an.lat, i.id iris
from etablissement e
join etablissement_date_source eds on eds.etablissement_id=e.id
join adresse_raw ar on ar.id=e.adresse_raw_id
join adresse_norm an on an.id=ar.adresse_norm_id
join iris.iris i on i.code=an.iris
join date_source ds on eds.date_source_id=ds.id
where e.categetab=620
and ds.annee={year-2000}
    """
    print(f"Quering etablissement pharma for year {year}")
    # print(sql)
    return pd.read_sql(sql, config.connection_string)


def get_ehpad(year):
    sql = f"""
select e.nofinesset fi, null as passu, false as has_pdata, null as etpsal, null as efflib, null as etp, e.id etab_id, e.rs, an.id an_id, an.dept_id, an.id adresse_norm_id, an.lon, an.lat, i.id iris
from etablissement e
join etablissement_date_source eds on eds.etablissement_id=e.id
join adresse_raw ar on ar.id=e.adresse_raw_id
join adresse_norm an on an.id=ar.adresse_norm_id
join iris.iris i on i.code=an.iris
join date_source ds on eds.date_source_id=ds.id
where e.categretab=4401
and ds.annee={year-2000}
    """
    # /!\ au r de categRetab
    print(f"Quering etablissement ehpad for year {year}")
    # print(sql)
    return pd.read_sql(sql, config.connection_string)


def get_sae_by_bor(year, bor):
    if bor == "urgence_gen":
        return get_urgence_sae(year, "GEN")
    elif bor == "urgence_ped":
        return get_urgence_sae(year, "PED")
    elif bor == "psy":
        return get_psy_sae(year)
    elif bor == "pharma":
        return get_pharma(year)
    elif bor == "ehpad":
        return get_ehpad(year)


def get_iriss():
    sql = f"""
select i.id "iris", i.nom "iris_label", c.code "code_commune", c.nom "commune_label"
from iris.iris i
join iris.commune c on c.id=i.commune_id
"""
    print(f"Quering iriss")
    return pd.read_sql(text(sql), config.connection_string)


def get_iris_matrix(time: int, time_type: str):
    sql = f"""
(select iris.id "iris1", iris.id "iris2", 0 "km", 0 "time_hc", 0 "time_hp" from iris.iris
union
select iris_id_from as "iris1", iris_id_to "iris2", route_km "km", route_min "time_hc", route_hp_min "time_hp" from iris.iris_matrix
where route_min <= {time}) order by "iris1", "iris2"
"""
    # print(sql)
    print(f"Quering iris matrix for {time}min {time_type}")
    m = pd.read_sql(sql, config.connection_string)
    m["time"] = m[f"time_{time_type.lower()}"].copy()
    return m


def get_pop_iris(year):
    yy = max(min(year - 2000, 21), 17)
    sql = f"""
select i.id iris, pi.iris iris_string, c.code code_commune, i.type type_iris, pi.pop, pi.pop0002, pi.pop0305, pi.pop0610, pi.pop1117, pi.pop1824, pi.pop2539, pi.pop4054, pi.pop5564, pi.pop6579, pi.pop80p
from iris.pop_iris pi
join iris.iris i on  pi.iris=i.code
join iris.commune c on i.commune_id=c.id
where year={yy}
"""
    # print(f"Get pop_iris for year {yy}")
    return pd.read_sql(text(sql), config.connection_string)

iriss = get_iriss()
for time in [60]:
    for time_type in ["HC"]:
        iris_matrix = get_iris_matrix(time, time_type)
        iris_matrix["iris"] = iris_matrix["iris2"].astype("int64")
        iris_matrix["time"] = iris_matrix[f"time_{time_type.lower()}"].copy()
        for year in range(2004, 2025):
            for bor in ["ehpad"]:  # ["urgence_gen", "urgence_ped", "psy", "pharma", "ehpad"]:
                if bor not in ["pharma", "ehpad"] and year < 2013:
                    continue
                pop_iris = get_pop_iris(year)
                print(f"Compute dist {bor} in {year} in {time}min {time_type}")
                ps_df = get_sae_by_bor(year, bor)
                ps_df["etpsal"] = ps_df["etpsal"].fillna(0)
                ps_df["efflib"] = ps_df["efflib"].fillna(0)
                ps_df["etp"] = ps_df["etp"].fillna(0)
                ps_df = ps_df.sort_values(by='iris')
                ps_df2 = ps_df.drop_duplicates(subset=['iris'])
                matrix_merge_df = iris_matrix.merge(ps_df2, on="iris", how="left", suffixes=('', ''))
                matrix_merge_df["etpsal"] = matrix_merge_df["etpsal"].fillna(0)
                matrix_merge_df["efflib"] = matrix_merge_df["efflib"].fillna(0)
                matrix_merge_df["etp"] = matrix_merge_df["etp"].fillna(0)
                matrix_merge_df["passu"] = matrix_merge_df["passu"].fillna(0)
                idx_ok = matrix_merge_df[matrix_merge_df['fi'].notna()].groupby('iris1')['time'].idxmin()
                idx_any = matrix_merge_df.groupby('iris1')['time'].idxmin()
                idx_final = idx_ok.combine_first(idx_any)
                result = matrix_merge_df.loc[idx_final].sort_index().reset_index(drop=True)
                dist_df = result[["iris1", "km", "time_hc", "time_hp", "fi", "passu", "has_pdata", "etpsal", "efflib", "etp", "rs", "lon", "lat"]]
                dist_df2 = dist_df.assign(time_hc=dist_df['time_hc'].where(dist_df['fi'].notna()))
                dist_df2 = dist_df2.assign(time_hp=dist_df['time_hp'].where(dist_df['fi'].notna()))
                dist_df2 = dist_df2.assign(km=dist_df['km'].where(dist_df['fi'].notna()))
                dist_df2["tension"] = dist_df2["passu"] / dist_df2["etp"]
                dist_df2["iris"] = dist_df2["iris1"]
                dist_df3 = dist_df2.merge(iriss, on="iris", how="left", suffixes=('', ''))
                dist_df3 = dist_df3.merge(pop_iris[["iris", "pop", "iris_string"]], on="iris", how="left", suffixes=('', ''))
                dist_df3["fake_time"] = dist_df3["time_hc"]
                dist_df3["fake_time"] = dist_df3["fake_time"].fillna(90)
                sum_pop = np.sum(dist_df3["pop"])
                dist_df3["meanw"] = dist_df3["fake_time"] * dist_df3["pop"] * len(dist_df3["fake_time"]) / sum_pop
                final = dist_df3.drop(["iris1", "fake_time"], axis=1)
                dico = {"year": year, "bor": bor, "time": time, "time_type": time_type}
                dico["meanw"] = np.mean(final["meanw"])
                dico["mean"] = np.mean(dist_df3["fake_time"])
                dico["std"] = np.std(dist_df3["fake_time"])
                dico["q10"], dico["q25"], dico["q50"], dico["q75"], dico["q90"] = np.quantile(dist_df3["fake_time"], [0.1, 0.25, 0.5, 0.75, 0.9])
                dico["min"] = np.min(dist_df3["fake_time"])
                dico["max"] = np.max(dist_df3["fake_time"])
                dico["passu_mean"] = np.mean(final[final["passu"] > 0]["passu"])
                dico["etpsal_mean"] = np.mean(final[final["has_pdata"] == True]["etpsal"])
                dico["efflib_mean"] = np.mean(final[final["has_pdata"] == True]["efflib"])
                dico["etp_mean"] = np.mean(final[final["has_pdata"] == True]["etp"])
                dico["tension_mean"] = np.mean(final[(final["has_pdata"] == True) & (final["tension"] != np.inf)]["tension"])
                dico["date"] = datetime.datetime.now()
                dico["key"] = random.randint(0, 1000000000000)
                study = pd.DataFrame(dico, index=[dico["key"]])
                final["year"] = year
                final["study_key"] = dico["key"]
                study.to_sql("dist_study", config.connection_string, schema="sae", if_exists="append", index=False)
                final.to_sql("dist", config.connection_string, schema="sae", if_exists="append", index=False)




