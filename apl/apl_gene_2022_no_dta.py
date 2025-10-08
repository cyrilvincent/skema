#!/usr/bin/env python
# coding: utf-8

# In[1]:


import pandas as pd
import numpy as np
import config
print(config.version)
print(config.connection_string)
pd.set_option('display.max_columns', None)


# In[2]:


specialite=10
year=21
method="PS"

sql = f"""
select ps.id, ps.nom, ps.prenom, an.dept_id, an.id adresse_norm_id, i.id iris, an.lon, an.lat from ps
join tarif t on t.ps_id = ps.id
join tarif_date_source tds on tds.tarif_id=t.id 
join cabinet c on t.cabinet_id=c.id
join adresse_raw ar on c.adresse_raw_id=ar.id
join adresse_norm an on ar.adresse_norm_id=an.id
join specialite_profession sp on sp.profession_id=t.profession_id
join iris.iris i on i.code=an.iris
where sp.specialite_id=10
and tds.date_source_id >= 2100 and  tds.date_source_id < 2200
and ar.dept_id=6
group by ps.id, c.id, an.id, i.id
"""

if method=="PA":
    sql = f"""
    select pa.id, pa.nom, pa.prenom, an.dept_id, an.id adresse_norm_id, i.id iris, an.lon, an.lat from personne_activite pa
    join personne_activite_diplome pad on pad.personne_activite_id=pa.id
    join diplome d on pad.diplome_id=d.id
    join profession_diplome pd on pd.diplome_id=d.id
    join profession p on pd.profession_id=p.id
    join specialite_profession sp on sp.profession_id=p.id
    join pa_adresse_norm_date_source pands ON pands.personne_activite_id = pa.id
    join adresse_norm an on pands.adresse_norm_id=an.id
    join iris.iris i on i.code=an.iris
    where sp.specialite_id=10
    and pands.date_source_id/100=21
    and an.dept_id=6
    group by pa.id, an.id, i.id
    """
elif method=="RPPS":
    sql = f"""
    select personne.id, personne.nom, personne.prenom, an.dept_id, an.id adresse_norm_id, i.id iris, an.lon, an.lat from personne
    join diplome_obtenu dio on dio.personne_id = personne.id
    join diplome d on d.id=dio.diplome_id
    join profession_diplome pd on pd.diplome_id=d.id
    join profession p on pd.profession_id=p.id
    join specialite_profession sp on sp.profession_id=p.id
    join coord c on c.personne_id=personne.id
    join adresse_norm an on c.adresse_norm_id=an.id
    join iris.iris i on i.code=an.iris
    where sp.specialite_id=10
    and personne.date_maj > '2022-01-01' and date_effet < '2022-01-01'
    and an.dept_id=6
    group by personne.id, an.id, i.id
    """

print(sql)
gene = pd.read_sql(sql, config.connection_string)
# 1286
# 50488 gene en 2023
# 47058 en 2024
gene.style.set_table_attributes('style="font-size: 10px;height:10px;"')
# gene = pd.read_stata("Etude 06/Gene06.dta")
gene #1289


# In[3]:


gene["id"].nunique() # 1189 sql 1203


# In[4]:


gene["b"] = gene["id"].astype(str) + "_" + gene["lat"].astype(str) + "_" + gene["lon"].astype(str)
gene["b"].nunique() #1289 #sql 1274


# In[5]:


gene = gene.sort_values(by='id')
gene["un"] = gene.groupby("id")["b"].transform("nunique")
gene["un"].value_counts(normalize=True) # 85 12 1


# In[6]:


gene['weight'] = 1 / gene['un']
gene.head(10)


# In[7]:


gene = gene.sort_values(by='iris')
gene["NB"] = gene.groupby("iris")["weight"].transform("sum")
gene


# In[8]:


gene = gene.drop_duplicates(subset=['iris', 'NB'])
# gene.to_csv("nbgpiris2022.csv", index=False)
gene


# In[9]:


min=30
dept=6
sql = f"""
(select iris.id "IRIS1", iris.id "IRIS2", 0 "KM", 0 "TIME" from iris.iris
where id / 10000000 = {dept}

union

select iris_id_from as "IRIS1", iris_id_to "IRIS2", route_km "KM", route_min "TIME" from iris.iris_matrix
where (iris_id_from/10000000={dept} or iris_id_to/10000000={dept})
and route_min <= {min}) order by "IRIS1", "IRIS2"
"""

# od06sql = pd.read_sql(sql, config.connection_string)
# od06sql.to_csv("od_06_sql.csv")
# od = od06sql
# od06sql

# od = pd.read_stata("Etude 06/ODFinale.dta")
# od = od[od["TIME"] <= 30]
# od #80712
# od

od = pd.read_csv("od_06_sql.csv")
od.style.set_table_attributes('style="font-size: 10px;height:10px;"')
od


# In[10]:


pd.options.mode.copy_on_write = True
od["iris"] = od["IRIS2"].astype("int64")
od["iris"].nunique() # 500


# In[11]:


from sqlalchemy import text
sql = f"""
select pi.iris, c.code "COM", i.type "TYP_IRIS", pi.p20_pop0002, pi.p20_pop0305, pi.p20_pop0610, pi.p20_pop1117, pi.p20_pop1824, pi.p20_pop2539, pi.p20_pop4559, pi.p20_pop6074, pi.p20_pop75p
from iris.pop_iris pi
join iris.iris i on  pi.iris=i.code
join iris.commune c on i.commune_id=c.id
where com like '{dept:02}%'"""
print(sql)
pop_iris = pd.read_sql(text(sql), config.connection_string)
# pop_iris = pd.read_stata("Etude 06/popIRIS.dta")
pop_iris


# In[12]:


pop_iris["iris"] = pd.to_numeric(pop_iris["iris"], errors="coerce")
od = od.merge(pop_iris, on="iris", how="left", suffixes=('', ''))
od.head(10)


# In[13]:


od["WexpGP"] = np.exp(-0.12 * od["TIME"])
# od.to_csv("popiris2022.csv", index=False)
od.head(10)



# In[14]:


od = od.sort_values(by='IRIS2')
# P19_POP0002 P19_POP0305 P19_POP0610 P19_POP1117 P19_POP1824 P19_POP2539 P19_POP4559 P19_POP6074 P19_POP75P
pop_cols = ["p20_pop0002", "p20_pop0305", "p20_pop0610", "p20_pop1117", "p20_pop1824", "p20_pop2539", "p20_pop4559", "p20_pop6074", "p20_pop75p"]
weights = [0.759201627]*4 + [0.784999993, 0.915, 1.05, 1.4, 1.3]
for col in pop_cols:
    od[col] = pd.to_numeric(od[col], errors="coerce")
od["POPGP"] = sum(w * od[c] for w, c in zip(weights, pop_cols))
# od.to_csv("popiris2022.csv", index=False)
od.head(10)


# In[15]:


# KM iris COM TYP_IRIS MODIF_IRIS LAB_IRIS P19_POP P19_POP0002 P19_POP0305 P19_POP0610 P19_POP1117 P19_POP1824 P19_POP2539 P19_POP4054 P19_POP5564 P19_POP6579 P19_POP80P P19_POP0014 P19_POP1529 P19_POP3044 P19_POP4559 P19_POP6074 P19_POP75P P19_POP0019 P19_POP2064 P19_POP65P P19_POPH P19_H0014 P19_H1529 P19_H3044 P19_H4559 P19_H6074 P19_H75P P19_H0019 P19_H2064 P19_H65P P19_POPF P19_F0014 P19_F1529 P19_F3044 P19_F4559 P19_F6074 P19_F75P P19_F0019 P19_F2064 P19_F65P _merge WexpGP POPGP
od = od.drop(["KM","iris","COM"], axis=1)
for col in od.columns:
    if col.startswith("P20"):
        od = od.drop(col, axis=1)
od2 = od.drop(["WexpGP","POPGP", "TYP_IRIS"], axis=1)
# od2.to_csv("ODgeneralistes06.csv", index=False)
od2


# In[16]:


od["iris"] = od["IRIS1"]
od = od.sort_values(by='IRIS1')
nbgp = gene
od = od.merge(nbgp, on="iris", how="left", suffixes=('', ''))
od["NB"].unique()


# In[17]:


od["NB"] = od["NB"].fillna(0)
od = od.sort_values(by=['IRIS1', "IRIS2"])
# od.to_csv("IRIS2022.csv", index=False)


# In[18]:


od = od.sort_values(by='IRIS1')
od["wpop"] = od["WexpGP"] * od["POPGP"]
od["swpop"] = od.groupby("IRIS1")["wpop"].transform("sum")
od["R"] = od["NB"] / (od["swpop"] / 100000)
od.head(10)


# In[19]:


rgp = od[od["IRIS1"] == od["IRIS2"]]
rgp = rgp[["IRIS1", "TYP_IRIS", "POPGP", "NB", "R"]].copy()
rgp.head(10)


# In[20]:


rgp["IRIS2"] = rgp["IRIS1"]
# rgp.to_csv("RGP2022.csv", index=False)
od = od.merge(rgp, on="IRIS2", suffixes=("", "_dest"))
od.head(10)


# In[21]:


od = od.sort_values(by=['IRIS1', "IRIS2"]).copy()
od["Ap"] = od["WexpGP"] * od["R_dest"]
od["APL"] = od.groupby("IRIS1")["Ap"].transform("sum")
od


# In[22]:


apl_final = od[od["IRIS1"] == od["IRIS2"]]
apl_final.head(10)


# In[23]:


apl_final["APL"].describe() #mean=98 median=108 du 2205 au 2305, median=110 en 21, pour pa median=62


# In[24]:


apl_final = apl_final[["IRIS1", "TYP_IRIS", "NB", "APL"]]
apl_final.head(10)


# In[25]:


sql = f"""
select i.id "IRIS1", i.code "IRIS", i.nom "LIB_IRIS", c.dept_id "DEP", c.code "DEPCOM", c.nom "LIBCOM", 20{year} "YEAR", {specialite} "SPECIALITE" from iris.iris i
join iris.commune c on c.id=i.commune_id
where i.code like '{dept:02d}%'"""
print(sql)
nom_iris = pd.read_sql(text(sql), config.connection_string)
# nom_iris = pd.read_stata("Etude 06/NomIRIS.dta")
nom_iris


# In[26]:


apl_final = apl_final.merge(nom_iris, on="IRIS1", how="left", suffixes=("", "_dest"))
apl_final = apl_final[["IRIS", "TYP_IRIS", "NB", "APL", "LIB_IRIS", "DEP", "DEPCOM", "LIBCOM", "YEAR", "SPECIALITE"]]
apl_final


# In[27]:


# apl_final.to_csv("APL06_2022_Final.csv", index=False)


# In[28]:


# TODO trouver les ratio DAMIR
# TODO remplacer ps par personne_activite : prévoir les 2

