#!/usr/bin/env python
# coding: utf-8

# In[1]:


import config
import pandas as pd
import psycopg2
import numpy as np


# Code acte consultation : « CNP »
# Base tarif : 42,5 (Secteur 2 non OPTAM)
# MPC : majoration du médecin spécialiste : 2,7 euros
# Donc S1 et S2 OPTAM = 45,2
# keep if strpos(v17,"CNP")
# MCS: MCS : majoration de coordination pour les psychiatres : 5 euros

# In[2]:


datesource_min = 2301
datesource_max = 2308
cs = 42.5
mpc = 2.7
mcs = 5
tarif_s1 = cs + mpc + mcs
tarif_s1


# In[3]:


sql = f"""
select * from ps p
join tarif t on t.ps_id =p.id
join tarif_date_source tds on tds.tarif_id =t.id 
join cabinet c on t.cabinet_id = c.id
join adresse_raw ar on c.adresse_raw_id = ar.id
join adresse_norm an on ar.adresse_norm_id = an.id
join ban b on an.ban_id  = b.id
where (t.profession_id =65 or t.profession_id =66)  # Faire mune jointure avec les diplomes vs profession j'ai l'info psy = 65 or 66 qqpart
and tds.date_source_id >= {datesource_min} and  tds.date_source_id <= {datesource_max}
"""

pd.set_option('display.max_columns', None)
pd.set_option('display.width', None)
pd.set_option('display.expand_frame_repr', False)

# df = pd.read_sql(sql, config.connection_string)
df = pd.read_csv("C:/Users/conta/git-CVC/Skema/Part III/psychiatres.csv", low_memory=False)
df.describe()


# In[4]:


# Renommer les colonnes
df.rename(columns={
    'genre': 'gender',
    'prenom': 'prénom',
    'code': 'codeccamdelacte',
    'nature_id': 'naturedexercice',
    'convention_id': 'convention',
    'code_insee': 'codeinsee',
    'code_postal': 'matchcp',
    'montant': 'montantgénéralementconstaté',
    'borne_inf': 'borneinférieuredumontant',
    'borne_sup': 'bornesupérieuredumontant',
    'option_contrat': 'optioncontratdaccèsauxsoins',
    'dept_id': 'dep'
}, inplace=True)

# Colonnes à conserver
df = df[['ps_id', 'gender', 'nom', 'prénom', 'codeccamdelacte', 'naturedexercice', 'convention',
         'codeinsee', 'montantgénéralementconstaté', 'borneinférieuredumontant', 'bornesupérieuredumontant',
         'adresse_id', 'date_source_id', 'optioncontratdaccèsauxsoins', 'matchcp', 'dep']]
df


# In[5]:


# Clé combinée
df['b'] = df['ps_id'].astype(str) + df['adresse_id'].astype(str)
df


# In[6]:


nb_ps_id = df["ps_id"].nunique()
nb_ps_id  # 5439


# In[7]:


nb_b = df["b"].nunique()
nb_b  # 5674


# In[8]:


df = df.sort_values(by='ps_id')
df


# In[9]:


df['unique'] = df.groupby('ps_id')['adresse_id'].transform('nunique')
df['un'] = df['unique']
pd.set_option('display.max_rows', 200)
df.head(100)


# In[10]:


# Comptages globaux
df['NB_total'] = df.groupby('dep')['ps_id'].transform('nunique')
df = df.sort_values(by='dep')
df["NB_total"].unique()


# In[11]:


mask_s2 = (df['convention'].isin([2, 3])) | ((df['convention'] == 1) & (df['optioncontratdaccèsauxsoins']))
df['NB2_total'] = df[mask_s2].groupby('dep')['ps_id'].transform('nunique')
df['NB2_total'] = df.groupby('dep')['NB2_total'].transform('max')
df["NB2_total"] = df["NB2_total"].fillna(0)
df["NB2_total"].unique()



# In[12]:


df['c'] = 1
df['NB_Ftotal'] = df.groupby('c')['ps_id'].transform('nunique')
df["NB_Ftotal"].unique()


# In[13]:


df['NB2_Ftotal'] = df[mask_s2].groupby('c')['ps_id'].transform('nunique')
df['NB2_Ftotal'] = df['NB2_Ftotal'].max()  # Car ne diot pas avoir de nan
df["NB2_Ftotal"].unique()


# In[14]:


# Pondération
df['weight'] = df['un'].map({1: 1, 2: 0.5, 3: 0.33, 4: 0.25, 5: 0.2}).fillna(0)
df


# In[15]:


# Tous les praticiens ne font pas de consultation
nb_ps_id, df["ps_id"].nunique()


# In[16]:


# Filtrage sur les actes de consultation
df = df[df['codeccamdelacte'].str.contains("CNP")]
# 45586
df


# In[17]:


df["codeccamdelacte"].value_counts(normalize=True)


# In[18]:


df = df.sort_values(by='convention')
df.groupby('convention')["ps_id"].nunique()


# In[19]:


df = df.sort_values(by=['b',"convention", "codeccamdelacte", "date_source_id"])
df.head(20)


# In[20]:


# Moyenne par groupe
df['mp'] = df.groupby(['b', 'convention', 'codeccamdelacte'])['montantgénéralementconstaté'].transform('mean')
df.head(30)


# In[21]:


# 45339
df = df[(df['codeccamdelacte'] == "CNP") | (df['codeccamdelacte'] == "CNP+MPC+MCS")]
df


# In[22]:


tarif_s1


# In[23]:


# 23421
print(len(df[(df['convention'] == 1) & (df['optioncontratdaccèsauxsoins'] == False)]))
df.loc[(df['convention'] == 1) & (df['optioncontratdaccèsauxsoins'] == False), 'mp'] = tarif_s1
df


# ****on élimine les duplications ps-adresse convention acte puis on sélectionne le prix le plus élevé d'un acte de consultation (discard tarif opposable des secteurs 2)
# ***puis on élimine les duplications ps-adresse convention (car les actes ont le même prix maintenant pour chaque ps-adresse)

# In[24]:


# Efface 39500
# Reste 5839
df = df.drop_duplicates(subset=['b', 'convention', 'codeccamdelacte'])
df


# In[25]:


df = df.sort_values(by=['b',"convention"])
df.head(10)


# In[26]:


df['prixmoyen'] = df.groupby(['b', 'convention'])['mp'].transform('max')
df.head(30)


# In[27]:


# Reste 5522
df = df.drop_duplicates(subset=['b', 'convention'])
df


# In[28]:


df.groupby('convention')["ps_id"].nunique()


# In[29]:


# df = df.drop_duplicates(subset=['b']) inutile
print(len(df[df["prixmoyen"] == 0])) #2
df['prixmoyen'] = df['prixmoyen'].replace(0, tarif_s1)
# ////Prix OK ////


# In[30]:


# Calculs départementaux
df = df.sort_values(by="dep")
df['NB'] = df.groupby('dep')['ps_id'].transform('nunique')
df["NB"].unique() # Jamais == nan


# In[31]:


df['NB_F'] = df.groupby('c')['ps_id'].transform('nunique')
df["NB_F"].unique() # 5410


# In[32]:


mask_s2 = (df['convention'].isin([2, 3])) | ((df['convention'] == 1) & (df['optioncontratdaccèsauxsoins']))
df['NB2'] = df[mask_s2].groupby('dep')['ps_id'].transform('nunique')
df['NB2'] = df.groupby("dep")["NB2"].transform("mean")
df["NB2"] = df["NB2"].fillna(0)
df["NB2"].unique()
df[df["NB2"] == 0]["dep"].unique()


# In[33]:


df['NB2_F'] = df[mask_s2].groupby('c')['ps_id'].transform('nunique')
df['NB2_F'] = df['NB2_F'].mean()
df["NB2_F"].unique()  # 2418


# In[34]:


df['ShareS2'] = df['NB2'] / df['NB']
df['ShareS2_F'] = df['NB2_F'] / df['NB_F']
df.head(20)


# In[35]:


# Dépassement
df['exessr'] = ((df['prixmoyen'] - tarif_s1) / tarif_s1) * 100
df.head(10)


# In[36]:


for seuil in [10, 25, 50, 75, 100]:
    df[f'c{seuil}'] = df.groupby('dep')['exessr'].transform(lambda x: (x >= seuil).sum())
    df[f'c{seuil}_F'] = (df['exessr'] >= seuil).sum()
    df[f'r{seuil}'] = (df[f'c{seuil}'] / df['NB']) * 100
    df[f'r{seuil}_F'] = df[f'c{seuil}_F'] / df['NB_F']
print("c100", df["c100"].unique())
print("cX0_F", df["c10_F"].unique(), df["c25_F"].unique(), df["c50_F"].unique(), df["c100_F"].unique())
print("rX0_F", df["r10_F"].unique(), df["r25_F"].unique(), df["r50_F"].unique(), df["r100_F"].unique())
df.head(20)


# ****dépassement moyen par département (uniquement les acteurs  faisant du dépassement)

# In[37]:


# Moyennes nationales
df['PF'] = df['prixmoyen'].mean() # 63.86
df["PF"].unique()


# In[38]:


df['PFS2'] = df[mask_s2]['prixmoyen'].mean()
df['PFS2'].unique()  # 80.45


# In[39]:


# Moyennes départementales
df['PrixMoyen'] = df.groupby('dep')['prixmoyen'].transform('mean')
df['PrixMoyen'].unique()


# In[40]:


df['PrixMoyenS2'] = df[mask_s2].groupby('dep')['prixmoyen'].transform('mean')
df.head(20)


# In[41]:


# df['Prix'] = df.groupby('dep')['PrixMoyen'].transform('mean')
df['depmoyen'] = ((df['PrixMoyen'] - tarif_s1) / tarif_s1) * 100  # * 100.roound(5)
df["depmoyen"].unique()


# In[42]:


#27.22
df["depmoyen_F"] =((df['PF'] - tarif_s1) / tarif_s1) * 100 # .round(5) * 100
df["depmoyen_F"].unique()


# In[43]:


df["PrixMoyenS2"] = df.groupby('dep')['PrixMoyenS2'].transform('mean')
df['depmoyenS2'] = ((df['PrixMoyenS2'] - tarif_s1) / tarif_s1) * 100 #.round(5) * 100
df['depmoyenS2'].unique()


# In[44]:


df['depmoyen_FS2'] = ((df['PFS2'] - tarif_s1) / tarif_s1) * 100
df['depmoyen_FS2'].unique() # 60.26


# In[45]:


df = df.sort_values(by=['dep', 'depmoyen'], ascending=[True, False])
df


# In[46]:


df = df.drop_duplicates(subset=['dep'])
df['depmoyen'] = df['depmoyen'].fillna(0)
pd.set_option('display.max_rows', 20)
df


# In[47]:


# gender nom prénom naturedexercice convention optioncontratdaccèsauxsoins codeccamdelacte ps_id montantgénéralementconstaté borneinférieuredumontant bornesupérieuredumontant date_source_id adresse_id matchcp codeinsee b unique un weight mp prixmoyen exessr nb10 c10 nb25 c25 nb50 c50 nb75 c75 nb100 c100 exess
df = df.drop(["gender","nom","prénom","naturedexercice","convention","optioncontratdaccèsauxsoins","codeccamdelacte","ps_id","montantgénéralementconstaté","borneinférieuredumontant","bornesupérieuredumontant","date_source_id","adresse_id","matchcp","codeinsee","b","unique","un","weight","mp","prixmoyen","exessr","c10","c25","c50","c75","c100"], axis=1)
df


# In[48]:


# Séparer les lignes à dupliquer
df_to_duplicate = df[df['dep'] == 75].copy()
df_to_duplicate['dup'] = 1  # marquer les duplications
# Marquer les lignes originales
df['dup'] = 0
# Fusionner les deux
df = pd.concat([df, df_to_duplicate], ignore_index=True)
df



# In[49]:


df.loc[df["dup"] == 1, "dep"] = 0
df.loc[df["dup"] == 1, "NB_total"] = df.loc[df["dup"] == 1]["NB_Ftotal"]
df.loc[df["dup"] == 1, "NB2_total"] = df.loc[df["dup"] == 1]["NB2_Ftotal"]
df.loc[df["dup"] == 1, "NB"] = df.loc[df["dup"] == 1]["NB_F"]
df.loc[df["dup"] == 1, "NB2"] = df.loc[df["dup"] == 1]["NB2_F"]
df.loc[df["dup"] == 1, "ShareS2"] = df.loc[df["dup"] == 1]["ShareS2_F"]
df.loc[df["dup"] == 1, "r10"] = df.loc[df["dup"] == 1]["r10_F"]
df.loc[df["dup"] == 1, "r25"] = df.loc[df["dup"] == 1]["r25_F"]
df.loc[df["dup"] == 1, "r50"] = df.loc[df["dup"] == 1]["r50_F"]
df.loc[df["dup"] == 1, "r100"] = df.loc[df["dup"] == 1]["r100_F"]
df.loc[df["dup"] == 1, "PrixMoyen"] = df.loc[df["dup"] == 1]["PF"]
df.loc[df["dup"] == 1, "PrixMoyenS2"] = df.loc[df["dup"] == 1]["PFS2"]
df.loc[df["dup"] == 1, "depmoyen"] = df.loc[df["dup"] == 1]["depmoyen_F"]
df.loc[df["dup"] == 1, "depmoyenS2"] = df.loc[df["dup"] == 1]["depmoyen_FS2"]
df


# In[50]:


# NB_Ftotal  NB2_Ftotal NB_F NB2_F ShareS2_F r10_F r25_F r50_F r100_F PF PFS2 depmoyen_F depmoyen_FS2 c10_F c25_F c50_F c100_F dup c
df = df.drop(["NB_Ftotal","NB2_Ftotal","NB_F","NB2_F","ShareS2_F","r10_F","r25_F","r50_F","r100_F","PF","PFS2","depmoyen_F","depmoyen_FS2","c10_F","c25_F","c50_F","c75_F","r75_F", "r75","c100_F","dup","c"], axis=1)
df


# In[51]:


# df[df["dep"] == 38]
df = df.reset_index(drop=True)
df.head(10)


# In[52]:


df2 = pd.read_csv("Rendus_PartIII/dépassement_psychiatres.csv")
df2.head(10)


# In[53]:


diff = (df - df2).round(3)
pd.set_option('display.max_rows', 100)
diff.head(96)


# In[54]:


df2 = df2.round(2)
df2 = df2.fillna(9999)
df1 = df.round(2)
df1 = df1.fillna(9999)
diff = df1.equals(df2)
# diff = df1["NB"].equals(df2["NB"])
# diff = df1[df1["NB2"] != df2["NB2"]]
# diff = df1[df1["NB2_total"] != df2["NB2_total"]]
# diff = df1[df1["NB_total"] != df2["NB_total"]]
diff = df1[df1["PrixMoyen"] != df2["PrixMoyen"]]
diff = df2[df1["PrixMoyenS2"] != df2["PrixMoyenS2"]]
diff


# In[ ]:




