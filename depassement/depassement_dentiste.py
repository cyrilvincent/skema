import config
import pandas as pd
import numpy as np

study_id = 10
sql = f"select * from depassement_study where id={study_id}"
df_study = pd.read_sql(sql, config.connection_string)

profession_type = df_study.iloc[0]["profession_type"]
datesource_min = df_study.iloc[0]["datesource_min"]
datesource_max = df_study.iloc[0]["datesource_max"]
tarif_s1 = df_study.iloc[0]["tarif_s1"]

df = pd.read_csv("../data/depassement/d2.csv", low_memory=False)

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

df = df[['ps_id', 'gender', 'nom', 'prénom', 'codeccamdelacte', 'naturedexercice', 'convention',
         'codeinsee', 'montantgénéralementconstaté', 'borneinférieuredumontant', 'bornesupérieuredumontant',
         'adresse_id', 'date_source_id', 'optioncontratdaccèsauxsoins', 'matchcp', 'dep']]
pd.options.mode.copy_on_write = True
df['b'] = df['ps_id'].astype(str) + "_" + df['adresse_id'].astype(str)

df = df.sort_values(by='ps_id')
df['unique'] = df.groupby('ps_id')['adresse_id'].transform('nunique')
df['un'] = df['unique']

df['NB_total'] = df.groupby('dep')['ps_id'].transform('nunique')
df = df.sort_values(by='dep')

df['c'] = 1
df['NB_Ftotal'] = df.groupby('c')['ps_id'].transform('nunique')

df['weight'] = df['un'].map({1: 1, 2: 0.5, 3: 0.33, 4: 0.25, 5: 0.2}).fillna(0)

df = df[df['codeccamdelacte'].isin(["HBLD4910","HBLD6340","HBLD7340"])]

# /!\ Différent des autres codes
df = df[df["montantgénéralementconstaté"] != 0]

df = df.sort_values(by=['b',"convention", "date_source_id"])

df["mp"] = np.nan
mask = df["codeccamdelacte"] == "HBLD4910"
df.loc[mask, "mp"] = df[mask].groupby(["b", "convention"])["montantgénéralementconstaté"].transform("mean")
df["mp2"] = np.nan
mask = df["codeccamdelacte"] == "HBLD6340"
df.loc[mask, "mp2"] = df[mask].groupby(["b", "convention"])["montantgénéralementconstaté"].transform("mean")
df["mp2"].unique()
df["mp3"] = np.nan
mask = df["codeccamdelacte"] == "HBLD7340"
df.loc[mask, "mp3"] = df[mask].groupby(["b", "convention"])["montantgénéralementconstaté"].transform("mean")

df['mp'] = df.groupby(['b', 'convention'])['mp'].transform('max')
df['mp2'] = df.groupby(['b', 'convention'])['mp2'].transform('max')
df['mp3'] = df.groupby(['b', 'convention'])['mp3'].transform('max')

df = df.sort_values(by=['dep',"convention"])
df["NB"] = np.nan
mask = df["codeccamdelacte"] == "HBLD4910"
df.loc[mask, "NB"] = df[mask].groupby(["dep", "convention"])["ps_id"].transform("nunique")
df['NB'] = df.groupby(['dep', "convention"])['NB'].transform('mean')
df["NB2"] = np.nan
mask = df["codeccamdelacte"] == "HBLD6340"
df.loc[mask, "NB2"] = df[mask].groupby(["dep", "convention"])["ps_id"].transform("nunique")
df['NB2'] = df.groupby(['dep', "convention"])['NB2'].transform('mean')
df["NB3"] = np.nan
mask = df["codeccamdelacte"] == "HBLD7340"
df.loc[mask, "NB3"] = df[mask].groupby(["dep", "convention"])["ps_id"].transform("nunique")
df['NB3'] = df.groupby(['dep', "convention"])['NB3'].transform('mean')

df["NB_F"] = np.nan
mask = df["codeccamdelacte"] == "HBLD4910"
df.loc[mask, "NB_F"] = df[mask].groupby(["c"])["ps_id"].transform("nunique")
df['NB_F'] = df.groupby(["c"])['NB_F'].transform('mean')
df["NB2_F"] = np.nan
mask = df["codeccamdelacte"] == "HBLD6340"
df.loc[mask, "NB2_F"] = df[mask].groupby(["c"])["ps_id"].transform("nunique")
df['NB2_F'] = df.groupby(["c"])['NB2_F'].transform('mean')
df["NB3_F"] = np.nan
mask = df["codeccamdelacte"] == "HBLD7340"
df.loc[mask, "NB3_F"] = df[mask].groupby(["c"])["ps_id"].transform("nunique")
df['NB3_F'] = df.groupby(["c"])['NB3_F'].transform('mean')

df = df.drop_duplicates(subset=['b', 'convention']) # 20279 ok

df = df.sort_values(by=['b',"convention"])
df["prixmoyen"]=df["mp"]
df["prixmoyen2"]=df["mp2"]
df["prixmoyen3"]=df["mp3"]

df = df.drop_duplicates(subset=['b']) # 20279 ok

df['exessr'] = ((df['prixmoyen'] - tarif_s1) / tarif_s1) * 100
df['exessr2'] = ((df['prixmoyen2'] - tarif_s1) / tarif_s1) * 100
df['exessr3'] = ((df['prixmoyen3'] - tarif_s1) / tarif_s1) * 100

df['PF'] = df['prixmoyen'].mean()
df['PF2'] = df['prixmoyen2'].mean()
df['PF3'] = df['prixmoyen3'].mean()

df['PrixMoyen'] = df.groupby('dep')['prixmoyen'].transform('mean')
df['PrixMoyen2'] = df.groupby('dep')['prixmoyen2'].transform('mean')
df['PrixMoyen3'] = df.groupby('dep')['prixmoyen3'].transform('mean')

df['depmoyen'] = ((df['PrixMoyen'] - tarif_s1) / tarif_s1) * 100
df['depmoyen2'] = ((df['PrixMoyen2'] - tarif_s1) / tarif_s1) * 100
df['depmoyen3'] = ((df['PrixMoyen3'] - tarif_s1) / tarif_s1) * 100

df["depmoyen_F"] =((df['PF'] - tarif_s1) / tarif_s1) * 100
df["depmoyen_F2"] =((df['PF2'] - tarif_s1) / tarif_s1) * 100
df["depmoyen_F3"] =((df['PF3'] - tarif_s1) / tarif_s1) * 100

df = df.sort_values(by=['dep', 'depmoyen'], ascending=[True, False])
df = df.drop_duplicates(subset=['dep'])

df = df.drop(["gender","nom","prénom","naturedexercice","convention","optioncontratdaccèsauxsoins","codeccamdelacte","ps_id","montantgénéralementconstaté","borneinférieuredumontant","bornesupérieuredumontant","date_source_id","adresse_id","matchcp","codeinsee","b","unique","un","weight","mp", "mp2", "mp3","prixmoyen","prixmoyen2","prixmoyen3","exessr","exessr2","exessr3"], axis=1)

df_to_duplicate = df[df['dep'] == 75].copy()
df_to_duplicate['dup'] = 1
df['dup'] = 0
df = pd.concat([df, df_to_duplicate], ignore_index=True)
df.loc[df["dup"] == 1, "dep"] = 0
df.loc[df["dup"] == 1, "NB_total"] = df.loc[df["dup"] == 1]["NB_Ftotal"]
df.loc[df["dup"] == 1, "NB"] = df.loc[df["dup"] == 1]["NB_F"]
df.loc[df["dup"] == 1, "NB2"] = df.loc[df["dup"] == 1]["NB2_F"]
df.loc[df["dup"] == 1, "NB3"] = df.loc[df["dup"] == 1]["NB3_F"]
df.loc[df["dup"] == 1, "PrixMoyen"] = df.loc[df["dup"] == 1]["PF"]
df.loc[df["dup"] == 1, "PrixMoyen2"] = df.loc[df["dup"] == 1]["PF2"]
df.loc[df["dup"] == 1, "PrixMoyen3"] = df.loc[df["dup"] == 1]["PF3"]
df.loc[df["dup"] == 1, "depmoyen"] = df.loc[df["dup"] == 1]["depmoyen_F"]
df.loc[df["dup"] == 1, "depmoyen2"] = df.loc[df["dup"] == 1]["depmoyen_F2"]
df.loc[df["dup"] == 1, "depmoyen3"] = df.loc[df["dup"] == 1]["depmoyen_F3"]

df = df.drop(["NB_Ftotal","NB_F","NB2_F","NB3_F","PF","PF2","PF3","depmoyen_F","depmoyen_F2","depmoyen_F3","dup","c"], axis=1)
df = df.reset_index(drop=True)

df.to_csv(f"../data/depassement/out/depassement_{profession_type}_{datesource_min}_{datesource_max}_{tarif_s1}_{study_id}.csv", index=False)
