#!/usr/bin/env python
# coding: utf-8

# In[51]:


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


# In[3]:


def get_ps(year, specialite):
    sql=f"""
select ps.id, ps.nom, ps.prenom, an.dept_id, an.id adresse_norm_id, i.id iris, an.lon, an.lat, 'L' code_mode_exercice 
from ps
join tarif t on t.ps_id = ps.id
join tarif_date_source tds on tds.tarif_id=t.id
join cabinet c on t.cabinet_id=c.id
join adresse_raw ar on c.adresse_raw_id=ar.id
join adresse_norm an on ar.adresse_norm_id=an.id
join specialite_profession sp on sp.profession_id=t.profession_id
join specialite s on s.id=sp.specialite_id
join iris.iris i on i.code=an.iris
where sp.specialite_id={specialite}
and tds.date_source_id >= {year}00 and  tds.date_source_id < {year+1}00
group by ps.id, c.id, an.id, i.id
"""
    # print(f"Quering PS for year {year} and specialite {specialite}")
    return pd.read_sql(sql, config.connection_string)


# In[4]:


def get_pa(year, specialite):
    sql = f"""
select pa.id, pa.nom, pa.prenom, an.dept_id, an.id adresse_norm_id, i.id iris, an.lon, an.lat, ps.code_mode_exercice 
from apl.ps_libreacces ps
join personne_activite pa on pa.inpp=ps.inpp
join pa_adresse_norm_date_source pands on pands.personne_activite_id=pa.id and pands.date_source_id=ps.date_source_id
join personne_activite_diplome pad on pad.personne_activite_id=pa.id
join diplome d on d.code_diplome=ps.code_diplome
join profession_diplome pd on pd.diplome_id=d.id
join profession p on p.id=pd.profession_id
join specialite_profession sp on sp.profession_id=p.id
join adresse_norm an on an.id=pands.adresse_norm_id
join date_source ds on ds.id=pands.date_source_id
join iris.iris i on i.code=an.iris
where sp.specialite_id={specialite}
--and ps.code_mode_exercice='L'
and ds.annee={year}
and pands.adresse_norm_id is not null
group by pa.id, an.id, i.id, ps.code_mode_exercice
"""
    # print(f"Quering PA for year {year} and specialite {specialite}")
    # print(sql)
    return pd.read_sql(sql, config.connection_string)


# In[5]:


def get_by_source(year, specialite, source):
    if source=="PS":
        return get_ps(year, specialite)
    elif source=="PA":
        return get_pa(year, specialite)
    else:
        raise ValueError(f"Bad source: {source}")



# In[81]:


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


# In[85]:


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


def get_iriss():
    sql = f"""
select i.id "iris", i.code "iris_string", i.nom "iris_label", c.dept_id "dept", c.code "code_commune", c.nom "commune_label", 20{year} "year", {specialite} "specialite" from iris.iris i
join iris.commune c on c.id=i.commune_id
"""
    # print(sql)
    return pd.read_sql(text(sql), config.connection_string)

# In[2]:


specialite=10
year=21
source="PA"
time=30
time_type="HC"
# accessibilite_exp=-0.12 #0.08 pour 45

iriss = get_iriss()
for time in [60]: #[30, 45, 60]:
    iris_matrix = get_iris_matrix(time, time_type)
    for time_type in ["HC"]: #["HC", "HP"]:
        iris_matrix["iris"] = iris_matrix["iris2"].astype("int64")
        iris_matrix["time"] = iris_matrix[f"time_{time_type.lower()}"].copy()
        for source in ["PA"]: #["PA", "PS"]:
            for year in range(20, 26):
                pop_iris = get_pop_iris(year)
                for specialite in [10]: #range(1, 21):
                    for accessibilite_exp in [-0.12, -0.10, -0.08, -0.06, -0.04]:
                        if ((time > 30 and accessibilite_exp < -0.08) or
                                (time == 30 and accessibilite_exp > -0.06) or
                                (time > 45 and accessibilite_exp < -0.06)):
                            continue

                        # accessibilite_exp = -(75 - time) * 4 / 1500
                        print(f"Compute APL for 20{year}, specialite {specialite} from {source} in {time}min {time_type}, e={accessibilite_exp}")

                        # In[82]:


                        # pop_iris = get_pop_iris(year)
                        # pop_iris


                        # In[7]:


                        ps_df = get_by_source(year, specialite, source)
                        ps_df


                        # In[9]:


                        nb_ps = ps_df["id"].nunique()
                        nb_cabinet_ps = ps_df.groupby(["id", "lon", "lat"])
                        # print(f"Nb unique PS {nb_ps}")
                        # print(f"Nb cabinet {len(nb_cabinet_ps)}")


                        # In[10]:


                        ps_df["key"] = ps_df["id"].astype(str) + "_" + ps_df["code_mode_exercice"] + "_" + ps_df["lat"].astype(str) + "_" + ps_df["lon"].astype(str)
                        ps_df["nb_cabinet"] = ps_df.groupby("id")["key"].transform("nunique")
                        # ps_df["nb_cabinet"].value_counts(normalize=True)


                        # In[11]:

                        ps_df = ps_df[ps_df["code_mode_exercice"] == "L"]
                        ps_df["weight"] = (1 / ps_df["nb_cabinet"]).replace(np.inf, 0)
                        ps_df["nb"] = ps_df.groupby("iris")["weight"].transform("sum")
                        ps_df.head(10)


                        # In[12]:


                        ps_df = ps_df.sort_values(by='iris')
                        ps_df2 = ps_df.drop_duplicates(subset=['iris', 'nb'])
                        ps_df2


                        # In[15]:


                        iris_matrix_pop_df = iris_matrix.merge(pop_iris, on="iris", how="left", suffixes=('', ''))
                        iris_matrix_pop_df


                        # In[17]:


                        accessibilite_fn = lambda x: np.exp(accessibilite_exp * x)
                        iris_matrix_pop_df["accessibilite_weight"] = accessibilite_fn(iris_matrix_pop_df["time"])
                        iris_matrix_pop_df.head(10)


                        # In[18]:


                        cols = [col for col in iris_matrix_pop_df.columns if "pop" in col and col != "pop"]
                        cols


                        # In[78]:


                        yy=min(year, 24)
                        sql = f"""
                        select o.* from apl.overrepresentation o
                        join specialite s on s.psp_spe_snds=o.psp_spe_snds
                        where o.year={yy}
                        and s.id={specialite}
                        """
                        over = pd.read_sql(sql, config.connection_string)
                        over


                        # In[79]:


                        if len(over) > 0:
                            weights = over.values[0,2:]
                        else:
                            weights = np.ones(len(over.columns) - 2)
                        weights


                        # In[21]:


                        iris_matrix_pop_df["pop_gp"] = sum(w * iris_matrix_pop_df[c] for w, c in zip(weights, cols))
                        iris_matrix_pop_df=iris_matrix_pop_df.sort_values(by='iris2')
                        # iris_matrix_pop_df.head(5)
                        test_pop = iris_matrix_pop_df.drop_duplicates(subset=['iris2'])
                        ratio = test_pop["pop_gp"] / (test_pop["pop"] + 1)
                        ratio_mean = np.mean(ratio)
                        # print(ratio_mean)
                        iris_matrix_pop_df["pop_gp"] = iris_matrix_pop_df["pop_gp"] / ratio_mean
                        if specialite == 5:
                            iris_matrix_pop_df["pop_gp"] /= 2


                        # In[22]:


                        matrix_df = iris_matrix_pop_df[["iris1","iris2","km","time","accessibilite_weight","pop_gp","pop","type_iris"]]
                        matrix_df.head(5)


                        # In[24]:


                        matrix_df["iris"] = matrix_df["iris1"].copy()
                        matrix_df = matrix_df.sort_values(by='iris2')
                        matrix_merge_df = matrix_df.merge(ps_df2, on="iris", how="left", suffixes=('', ''))
                        matrix_merge_df


                        # In[25]:


                        matrix_merge_df["nb"] = matrix_merge_df["nb"].fillna(0)
                        matrix_merge_df = matrix_merge_df.sort_values(by=['iris1', "iris2"])
                        matrix_merge_df["nb"].nunique()


                        # In[28]:


                        # matrix_merge_df = matrix_merge_df.sort_values(by='iris1')
                        matrix_merge_df["wpop"] = matrix_merge_df["accessibilite_weight"] * matrix_merge_df["pop_gp"]
                        matrix_merge_df["swpop"] = matrix_merge_df.groupby("iris1")["wpop"].transform("sum")
                        matrix_merge_df["R"] = (matrix_merge_df["nb"] / (matrix_merge_df["swpop"] / 100000)).replace(np.inf, 0)
                        matrix_merge_df.head(5)
                        # apl["R"].unique()


                        # In[29]:


                        rgp = matrix_merge_df[matrix_merge_df["iris1"] == matrix_merge_df["iris2"]]
                        rgp = rgp[["iris1", "iris2", "type_iris", "pop_gp", "nb", "R", "swpop", "wpop", "pop_gp", "pop"]].copy()
                        rgp


                        # In[30]:


                        apl = matrix_merge_df.merge(rgp, on="iris2", suffixes=("", "_dest"))
                        apl


                        # In[31]:


                        apl = apl.sort_values(by=['iris1', "iris2"])
                        apl["ap"] = apl["accessibilite_weight"] * apl["R_dest"]
                        apl.head(5)


                        # In[32]:


                        apl["apl"] = apl.groupby("iris1")["ap"].transform("sum")
                        apl


                        # In[33]:


                        apl2 = apl[apl["iris1"] == apl["iris2"]]
                        apl2


                        # In[34]:


                        # print(year, specialite, source)
                        apl2["apl"].describe()
                        # 21-10-PA:66-57


                        # In[ ]:


                        # 21 10 PA
                        # count    48569.000000
                        # mean        66.239008
                        # std         36.200523
                        # min          0.000000
                        # 25%         40.432111
                        # 50%         56.872725
                        # 75%         85.083597
                        # max        681.212229
                        # Name: apl, dtype: float64


                        # In[56]:


                        dico = {"year":year, "specialite_id":specialite, "source":source, "time":time, "time_type":time_type, "exp":accessibilite_exp}
                        dico["mean"] = np.mean(apl2["apl"])
                        dico["std"] = np.std(apl2["apl"])
                        dico["q10"], dico["q25"], dico["q50"], dico["q75"], dico["q90"] = np.quantile(apl2["apl"], [0.1, 0.25, 0.5, 0.75, 0.9])
                        dico["min"] = np.min(apl2["apl"])
                        dico["max"] = np.max(apl2["apl"])
                        dico["date"] = datetime.datetime.now()
                        dico["key"] = random.randint(0, 1000000000000)
                        dico


                        # In[62]:


                        study = pd.DataFrame(dico, index=[dico["key"]])
                        study


                        # In[35]:


                        apl2[apl2["apl"]>400]


                        # In[36]:


                        apl3 = apl2[["iris1", "type_iris", "nb", "apl", "ap", "accessibilite_weight", "wpop", "swpop", "R", "pop_gp","pop"]]
                        apl3 = apl3.rename(columns={'iris1': 'iris'})
                        apl3.head(5)


                        # In[37]:


                        # iriss = get_iriss()
                        # iriss


                        # In[38]:


                        apl_final = apl3.merge(iriss, on="iris", how="left", suffixes=("", "_dest"))
                        apl_final = apl_final[["year", "specialite", "iris", "iris_string", "type_iris", "nb", "apl", "ap", "accessibilite_weight", "R", "wpop", "swpop", "pop_gp","pop", "iris_label", "dept", "code_commune", "commune_label"]]
                        apl_final


                        # In[39]:


                        # d6=apl_final[apl_final["dept"]==6]
                        # d6
                        #
                        #
                        # # In[40]:
                        #
                        #
                        # d6["apl"].describe()
                        # # Ca change à cause des cabinets multi-dept
                        #
                        #
                        # # In[41]:
                        #
                        #
                        # apl_final.to_csv("apl_france.csv", index=False)


                        # In[65]:

                        apl_final["year"]=year
                        apl_final["study_key"]=dico["key"]
                        study.to_sql("apl_study", config.connection_string, schema="apl", if_exists="append", index=False)
                        apl_final.to_sql("apl", config.connection_string, schema="apl", if_exists="append", index=False)



