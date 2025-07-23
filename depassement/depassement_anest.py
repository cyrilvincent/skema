#!/usr/bin/env python
# coding: utf-8

# In[1]:


import config
import pandas as pd
import psycopg2
import numpy as np


# - Anesthésie-réanimation (code 3) : La consultation pré-anesthésique
# - Code acte de consultation : CS_+MPC+MCS
# - Base de 25 ou 30 euros (à voir)
# 

# In[2]:


study_id = 2
sql = f"select * from depassement_study where id={study_id}"
df_study = pd.read_sql(sql, config.connection_string)
df_study


# In[3]:


profession_type = df_study.iloc[0]["profession_type"]
datesource_min = df_study.iloc[0]["datesource_min"]
datesource_max = df_study.iloc[0]["datesource_max"]
tarif_s1 = df_study.iloc[0]["tarif_s1"]
profession_type, datesource_min, datesource_max, tarif_s1


# In[4]:


sql = f"""
select p.*, t.*, tds.date_source_id, b.id as adresse_id, an.cp as cp, ar.dept_id as dept_id, b.code_insee from ps p
join tarif t on t.ps_id = p.id
join tarif_date_source tds on tds.tarif_id = t.id
join cabinet c on t.cabinet_id = c.id
join adresse_raw ar on c.adresse_raw_id = ar.id
join adresse_norm an on ar.adresse_norm_id = an.id
join ban b on an.ban_id = b.id
--join ps_cabinet_date_source pcd on pcd.ps_id = p.id and pcd.cabinet_id = c.id and pcd.date_source_id = tds.date_source_id
join profession_type pt on pt.profession = '{profession_type}' and t.profession_id = pt.profession_id
where tds.date_source_id >= {datesource_min} and  tds.date_source_id <= {datesource_max}
"""

pd.set_option('display.max_columns', None)
pd.set_option('display.width', None)
pd.set_option('display.expand_frame_repr', False)

df = pd.read_csv("../data/depassement/anest.csv", low_memory=False)
# df = pd.read_sql(sql, config.connection_string)
df  #1235287 





# In[5]:


# Renommer les colonnes
df.rename(columns={
    'genre': 'gender',
    'prenom': 'prénom',
    'code': 'codeccamdelacte',
    'nature_id': 'naturedexercice',
    'convention_id': 'convention',
    'code_insee': 'codeinsee',
    'cp': 'matchcp',
    'montant': 'montantgénéralementconstaté',
    'borne_inf': 'borneinférieuredumontant',
    'borne_sup': 'bornesupérieuredumontant',
    'option_contrat': 'optioncontratdaccèsauxsoins',
    'dept_id': 'dep',
}, inplace=True)

# Colonnes à conserver
df = df[['ps_id', 'gender', 'nom', 'prénom', 'codeccamdelacte', 'naturedexercice', 'convention',
         'codeinsee', 'montantgénéralementconstaté', 'borneinférieuredumontant', 'bornesupérieuredumontant',
         'adresse_id', 'date_source_id', 'optioncontratdaccèsauxsoins', 'matchcp', 'dep']]
df


# In[6]:


# Clé combinée
pd.options.mode.copy_on_write = True
df['b'] = df['ps_id'].astype(str) + "_" + df['adresse_id'].astype(str)
df


# In[7]:


nb_ps_id = df["ps_id"].nunique()
nb_ps_id  #3384 


# In[8]:


nb_b = df["b"].nunique()
nb_b  #4017


# In[9]:


df = df.sort_values(by='ps_id')
df['unique'] = df.groupby('ps_id')['adresse_id'].transform('nunique')
df['un'] = df['unique']
pd.set_option('display.max_rows', 200)
df.head(10)


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
df["NB_Ftotal"].unique() # 3384


# In[13]:


df['NB2_Ftotal'] = df[mask_s2].groupby('c')['ps_id'].transform('nunique')
df['NB2_Ftotal'] = df['NB2_Ftotal'].max() 
df["NB2_Ftotal"].unique() # 2333


# In[14]:


# ////Algo pour corriger l'excès d'appareillage (à copier/coller pour APL?)////
# ///prenons les ind qui ont plusieurs type d'options///
df['cc'] = np.where(df['optioncontratdaccèsauxsoins'] == False, -1, np.where(df['optioncontratdaccèsauxsoins'], 1, np.nan))
df["cc"].unique()


# In[15]:


df['ccc'] = df.groupby('ps_id')['cc'].transform('mean')
df["ccc"].unique()


# In[16]:


# . drop if ccc==-1 |ccc==1 (1,218,938 observations deleted) Reste 16349
# Unique = 57
nb_ccc_1 = len(df[(df["ccc"] == 1) | (df["ccc"] == -1)]) #1218938
nb_not_1 = len(df) - nb_ccc_1 # 16349
nb = len(df[(df["ccc"] != 1) & (df["ccc"] != -1)]["ps_id"].unique()) # 57
nb_ccc_1, nb_not_1, nb

# ***SINDIHEBURA ONESIME (pas de prb poste en clinique ou OPTAM=non)
# **EL KINANI	SALIMA (pas de prb changement de contrat au cours du temps)
# **SOUBIE	FLORENCE (pas de prb poste en clinique ou OPTAM=non)
# ***DE PONTBRIAND	ULRIKA (pas de prb changement de contrat au cours du temps)
# ***JOMAA STEPHANE (pas de prb poste en clinique ou OPTAM=non)
# ***ASSATHIANY	REMY (pas de prb changement de contrat au cours du temps)
# ***NOUJAIM LABBE	PAULINE (pas de prb changement de contrat au cours du temps+ changement adresse)
# ***FRANCOIS	PATRICK (pas de prb changement de contrat au cours du temps)
# ***CARLIER	LAURE (pas de prb poste en clinique ou OPTAM=oui)
# ***FUCHS	MICHAEL (pas de prb changement de contrat au cours du temps+ changement adresse)
# ***BAZIN	JEANNE  (pas de prb erreur de saisie)
# ***JERNITE ASSIA (gros prb car il existe Mohamed ASSIA à la même adresse)
# replace gender="F" if nom=="JERNITE" & optioncontratdaccèsauxsoins=="false"
# replace ps_id=ps_id+1000000 if nom=="JERNITE" & optioncontratdaccèsauxsoins=="false"
# replace prénom="MOHAMED" if nom=="JERNITE" & optioncontratdaccèsauxsoins=="true"
# ***NATHAN	NOEMIE (pas de prb changement de contrat au cours du temps)
# ***SIDI DANIEL (pas de prb mais double affiliation inexplicable- optam à privilégier)
# ***MOULA MAMOUDJY	NAFISSA (pas de prb changement de contrat au cours du temps)
# ***BASSEL ALI (pas de prb changement de statut au cours du temps)
# ***YVON CORALIE ( pas de prb poste en clinique ou OPTAM=non)
# ***SISSAOUI	SAMIRA (pas de prb changement de statut au cours du temps)
# In[17]:


# Correction spécifique pour JERNITE
df.loc[(df['nom'] == "JERNITE") & (df['optioncontratdaccèsauxsoins'] == False), 'gender'] = "F"
df.loc[(df['nom'] == "JERNITE") & (df['optioncontratdaccèsauxsoins'] == False), 'ps_id'] += 1000000
df.loc[(df['nom'] == "JERNITE") & (df['optioncontratdaccèsauxsoins']), 'prénom'] = "MOHAMED"
df[df['nom'] == "JERNITE"]


# In[18]:


# Pondération
df['weight'] = df['un'].map({1: 1, 2: 0.5, 3: 0.33, 4: 0.25, 5: 0.2}).fillna(0)


# In[19]:


# Tous les praticiens font des consultations
nb_ps_id, df["ps_id"].nunique()


# In[20]:


# Filtrage sur les actes de consultation
# On se concentre sur la consultation la plus standard: enfant de moins de 2 ans///
# Tarif S1 ou S2 OPTAM: 37 euros (23 (CS) +4 (MEP) +10 (NFP)) donc hors OPTAM/S1 on est à 33 euros
# code retenu: "CS_+MEP+NFP" et "CS_+NFP"
df = df[df['codeccamdelacte'].str.contains("CS", na=False)]
# 24911
df


# In[21]:


df["codeccamdelacte"].value_counts(normalize=True) # 29 9 60


# In[22]:


df["ps_id"].nunique() #2691


# In[23]:


df = df.sort_values(by='convention')
df.groupby('convention')["ps_id"].nunique() #1023 1669


# In[24]:


# Moyenne par groupe
df = df.sort_values(by=['b',"convention", "codeccamdelacte", "date_source_id"])
df['mp'] = df.groupby(['b', 'convention', 'codeccamdelacte'])['montantgénéralementconstaté'].transform('mean')
df["mp"].unique()



# In[25]:


# 0
len(df[(df['codeccamdelacte'] == "CS_+MEP+NFP") & (df['convention'] == 1) & (df['optioncontratdaccèsauxsoins'] == False)])


# In[26]:


df.loc[(df['codeccamdelacte'] == "CS_+MEP+NFP") & (df['convention'] == 1) & (df['optioncontratdaccèsauxsoins'] == False), 'mp'] = tarif_s1


# ****on élimine les duplications ps-adresse convention acte puis on sélectionne le prix le plus élevé d'un acte de consultation (discard tarif opposable des secteurs 2)
# ***puis on élimine les duplications ps-adresse convention (car les actes ont le même prix maintenant pour chaque ps-adresse)

# In[27]:


# Efface 21669
# Reste 3242
df = df.drop_duplicates(subset=['b', 'convention', 'codeccamdelacte'])
df


# In[28]:


df['prixmoyen'] = df.groupby(['b', 'convention'])['mp'].transform('max')
pd.set_option('display.max_rows', 100)
df.head(20)


# In[29]:


# Reste 2810
df = df.drop_duplicates(subset=['b', 'convention'])
df



# In[30]:


df.groupby('convention')["ps_id"].nunique() #1023 1669


# In[31]:


# df = df_backup.copy()
df = df.drop_duplicates(subset=['b']) # inutile
print(len(df[df["mp"] == 0])) #874
df['prixmoyen'] = df["prixmoyen"].replace(0, tarif_s1) # /!\ BUG ne pas faire df["mp"].replace(0, tarif_s1)
# # ////Prix OK ////
# # df
df[(df["dep"]==3) & (df["nom"]=="NOUNOU")].head(100)


# In[32]:


# Calculs départementaux
df = df.sort_values(by="dep")
df['NB'] = df.groupby('dep')['ps_id'].transform('nunique')
df["NB"].unique()


# In[33]:


df['NB_F'] = df.groupby('c')['ps_id'].transform('nunique')
df["NB_F"].unique() # 2691


# In[34]:


mask_s2 = (df['convention'].isin([2, 3])) | ((df['convention'] == 1) & (df['optioncontratdaccèsauxsoins']))
df['NB2'] = df[mask_s2].groupby('dep')['ps_id'].transform('nunique')
df['NB2'] = df.groupby("dep")["NB2"].transform("mean")
df["NB2"] = df["NB2"].fillna(0)
df["NB2"].unique()


# In[35]:


df['NB2_F'] = df[mask_s2].groupby('c')['ps_id'].transform('nunique')
df['NB2_F'] = df['NB2_F'].mean()
df["NB2_F"].unique()  # 1831


# In[36]:


df['ShareS2'] = df['NB2'] / df['NB']
# df[df["dep"]==1]['NB'].unique(), df[df["dep"]==1]['NB2'].unique(), df[df["dep"]==1]['ShareS2'].unique()
df['ShareS2'].unique()


# In[37]:


df['ShareS2_F'] = df['NB2_F'] / df['NB_F']
df['ShareS2_F'].unique() #0.68


# In[38]:


# Dépassement
df['exessr'] = ((df['prixmoyen'] - tarif_s1) / tarif_s1) * 100
df['exessr'].unique()


# In[39]:


for seuil in [10, 25, 50, 75, 100]:
    df[f'c{seuil}'] = df.groupby('dep')['exessr'].transform(lambda x: (x >= seuil).sum())
    df[f'c{seuil}_F'] = (df['exessr'] >= seuil).sum()
    df[f'r{seuil}'] = (df[f'c{seuil}'] / df['NB']) * 100
    df[f'r{seuil}_F'] = df[f'c{seuil}_F'] / df['NB_F']
print("c100", df["c100"].unique())
print("c10", df["c10"].unique())
print("c25", df["c25"].unique())
print("c50", df["c50"].unique())
print("cX0_F", df["c10_F"].unique(), df["c25_F"].unique(), df["c50_F"].unique(), df["c100_F"].unique()) # 1465	1448	1164	333
print("rX0_F", df["r10_F"].unique(), df["r25_F"].unique(), df["r50_F"].unique(), df["r100_F"].unique())


# ****dépassement moyen par département (uniquement les acteurs  faisant du dépassement)

# In[40]:


# Moyennes nationales
df['PF'] = df['prixmoyen'].mean() # 40.87
df["PF"].unique()


# In[41]:


df['PFS2'] = df[mask_s2]['prixmoyen'].mean()
df['PFS2'].unique()  # 45.77


# In[42]:


# Moyennes départementales
df['PrixMoyen'] = df.groupby('dep')['prixmoyen'].transform('mean')
df['PrixMoyen'].unique()


# In[43]:


df['PrixMoyenS2'] = df[mask_s2].groupby('dep')['prixmoyen'].transform('mean')
df['PrixMoyenS2'].unique()


# In[44]:


# df['Prix'] = df.groupby('dep')['PrixMoyen'].transform('mean')
df['depmoyen'] = ((df['PrixMoyen'] - tarif_s1) / tarif_s1) * 100  # * 100.roound(5)
df["depmoyen"].unique()


# In[45]:


df["depmoyen_F"] =((df['PF'] - tarif_s1) / tarif_s1) * 100
df["depmoyen_F"] = df["depmoyen_F"] #.round(3)
df["depmoyen_F"].unique() # 36.23


# In[46]:


df["PrixMoyenS2"] = df.groupby('dep')['PrixMoyenS2'].transform('mean')
df['depmoyenS2'] = ((df['PrixMoyenS2'] - tarif_s1) / tarif_s1) * 100
df['depmoyenS2'] = df['depmoyenS2'] #.round(3)
df['depmoyenS2'].unique()


# In[47]:


df['depmoyen_FS2'] = ((df['PFS2'] - tarif_s1) / tarif_s1) * 100
df['depmoyen_FS2'].unique() # 52.57


# In[48]:


df = df.sort_values(by=['dep', 'depmoyen'], ascending=[True, False])
df = df.drop_duplicates(subset=['dep'])
df['depmoyen'] = df['depmoyen'].fillna(0)
pd.set_option('display.max_rows', 20)
df


# In[49]:


# gender nom prénom naturedexercice convention optioncontratdaccèsauxsoins codeccamdelacte ps_id montantgénéralementconstaté borneinférieuredumontant bornesupérieuredumontant date_source_id adresse_id matchcp codeinsee b unique un weight mp prixmoyen exessr nb10 c10 nb25 c25 nb50 c50 nb75 c75 nb100 c100 exess
df = df.drop(["gender","nom","prénom","naturedexercice","convention","optioncontratdaccèsauxsoins","codeccamdelacte","ps_id","montantgénéralementconstaté","borneinférieuredumontant","bornesupérieuredumontant","date_source_id","adresse_id","matchcp","codeinsee","b","unique","un","weight","mp","prixmoyen","exessr","c10","c25","c50","c75","c100"], axis=1)
df


# In[50]:


# Séparer les lignes à dupliquer
df_to_duplicate = df[df['dep'] == 75].copy()
df_to_duplicate['dup'] = 1  # marquer les duplications
# Marquer les lignes originales
df['dup'] = 0
# Fusionner les deux
df = pd.concat([df, df_to_duplicate], ignore_index=True)
df



# In[51]:


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


# In[52]:


# NB_Ftotal  NB2_Ftotal NB_F NB2_F ShareS2_F r10_F r25_F r50_F r100_F PF PFS2 depmoyen_F depmoyen_FS2 c10_F c25_F c50_F c100_F dup c
df = df.drop(["NB_Ftotal","NB2_Ftotal","NB_F","NB2_F","ShareS2_F","r10_F","r25_F","r50_F","r100_F","PF","PFS2","depmoyen_F","depmoyen_FS2","c10_F","c25_F","c50_F","c75_F","r75_F", "r75","c100_F","dup","c","cc","ccc"], axis=1)
df


# In[53]:


# df[df["dep"] == 38]
df = df.reset_index(drop=True)
df.head(10)


# In[54]:


df2 = pd.read_csv("../data/depassement/Rendus_PartIII/dépassement_anest.csv")
df2.head(10)


# In[55]:


df1 = df.fillna(9999).round(2)
df2 = df2.fillna(9999).round(2)
diff = df1 - df2
pd.set_option('display.max_rows', 100)
diff.head(96)


# In[56]:


diff = df1["NB"].equals(df2["NB"])
diff = df1[df1["NB2"] != df2["NB2"]]
diff = df1[df1["NB2_total"] != df2["NB2_total"]]
diff = df1[df1["NB_total"] != df2["NB_total"]]
diff = df1[df1["PrixMoyen"] != df2["PrixMoyen"]]
diff = df2[df1["PrixMoyenS2"] != df2["PrixMoyenS2"]] # Aucune différence avec STATA, petite différence avec le fichier, + grosse différence avec SQL
diff


# In[57]:


df.to_csv(f"../data/depassement/out/depassement_{profession_type}_{datesource_min}_{datesource_max}_{tarif_s1}_{study_id}.csv", index=False)


# In[58]:


# conn = psycopg2.connect(config.connection_string)
# sql = f"delete from depassement where depassement_study_id={study_id}" # Ne marche pas la 1ère fois
# with conn.cursor() as cur:
#     cur.execute(sql)
# conn.commit()
# conn.close()
# df["depassement_study_id"] = study_id
# df.to_sql("depassement", config.connection_string, if_exists="append", index_label="id")


# In[ ]:




