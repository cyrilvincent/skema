import pandas as pd
import psycopg2

import config
from sqlentities import Context

# Code acte consultation : « CNP »
# Base tarif : 42,5 (Secteur 2 non OPTAM)
# MPC : majoration du médecin spécialiste : 2,7 euros
# Donc S1 et S2 OPTAM = 45,2
# keep if strpos(v17,"CNP")
# MCS: MCS : majoration de coordination pour les psychiatres : 5 euros
# BaseTarif + MPC + MCS = 50.2
base_tarif = 42.5
mpc = 2.7
mcs = 5
tarif = base_tarif + mpc + mcs


print("Hello")
sql = """
select * from ps p
join tarif t on t.ps_id =p.id
join tarif_date_source tds on tds.tarif_id =t.id 
join cabinet c on t.cabinet_id = c.id
join adresse_raw ar on c.adresse_raw_id = ar.id
join adresse_norm an on ar.adresse_norm_id = an.id
join ban b on an.ban_id  = b.id
where (t.profession_id =65 or t.profession_id =66)
and tds.date_source_id >= 2201 and  tds.date_source_id <= 2308
"""
# Charger le fichier CSV
# df = pd.read_csv("C:/Users/conta/git-CVC/Skema/Part III/pediatres.csv", low_memory=False)
pd.set_option('display.max_columns', None)
pd.set_option('display.width', None)
pd.set_option('display.expand_frame_repr', False)

df = pd.read_sql(sql, config.connection_string)
import pandas as pd
import numpy as np

# Charger les données
df = pd.read_csv("psychiatres.csv")

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

# Clé combinée
df['b'] = df['ps_id'].astype(str) + df['adresse_id'].astype(str)

# Nombre d'adresses uniques par praticien
df['unique'] = df.groupby('ps_id')['adresse_id'].transform('nunique')
df['un'] = df['unique']

# Comptages globaux
df['NB_total'] = df.groupby('dep')['ps_id'].transform('nunique')
mask_s2 = (df['convention'].isin([2, 3])) | ((df['convention'] == 1) & (df['optioncontratdaccèsauxsoins']))
df['NB2_total'] = df[mask_s2].groupby('dep')['ps_id'].transform('nunique')
df['c'] = 1
df['NB_Ftotal'] = df.groupby('c')['ps_id'].transform('nunique')
df['NB2_Ftotal'] = df[mask_s2].groupby('c')['ps_id'].transform('nunique')

# Pondération
df['weight'] = df['un'].map({1: 1, 2: 0.5, 3: 0.33, 4: 0.25, 5: 0.2}).fillna(0)

# Filtrage sur les actes de consultation
df = df[df['codeccamdelacte'].str.contains("CNP", na=False)]

# Moyenne par groupe
df['mp'] = df.groupby(['b', 'convention', 'codeccamdelacte'])['montantgénéralementconstaté'].transform('mean')
df.loc[(df['convention'] == 1) & (df['optioncontratdaccèsauxsoins'] is False), 'mp'] = 50.2

# Nettoyage des doublons
df = df.drop_duplicates(subset=['b', 'convention', 'codeccamdelacte'])
df['prixmoyen'] = df.groupby(['b', 'convention'])['mp'].transform('max')
df = df.drop_duplicates(subset=['b', 'convention'])
df['prixmoyen'] = df['prixmoyen'].replace(0, 50.2)

# Calculs départementaux
df['NB'] = df.groupby('dep')['ps_id'].transform('nunique')
df['NB_F'] = df.groupby('c')['ps_id'].transform('nunique')
df['NB2'] = df[mask_s2].groupby('dep')['ps_id'].transform('nunique')
df['NB2_F'] = df[mask_s2].groupby('c')['ps_id'].transform('nunique')
df['ShareS2'] = df['NB2'] / df['NB']
df['ShareS2_F'] = df['NB2_F'] / df['NB_F']

# Dépassement
df['exessr'] = ((df['prixmoyen'] - 50.2) / 50.2) * 100
for seuil in [10, 25, 50, 75, 100]:
    df[f'c{seuil}'] = df.groupby('dep')['exessr'].transform(lambda x: (x >= seuil).sum())
    df[f'c{seuil}_F'] = (df['exessr'] >= seuil).sum()
    df[f'r{seuil}'] = (df[f'c{seuil}'] / df['NB']) * 100
    df[f'r{seuil}_F'] = df[f'c{seuil}_F'] / df['NB_F']

# Moyennes nationales et départementales
df['PF'] = df['prixmoyen'].mean()
df['PFS2'] = df[mask_s2]['prixmoyen'].mean()
df['PrixMoyen'] = df.groupby('dep')['prixmoyen'].transform('mean')
df['PrixMoyenS2'] = df[mask_s2].groupby('dep')['prixmoyen'].transform('mean')
df['depmoyen'] = ((df['PrixMoyen'] - 50.2) / 50.2).round(3) * 100
df['depmoyenS2'] = ((df['PrixMoyenS2'] - 50.2) / 50.2).round(3) * 100

# Nettoyage final
df = df.drop_duplicates(subset=['dep'])
df['depmoyen'] = df['depmoyen'].fillna(0)

# Export possible
# df.to_csv("résultat_analyse_psy.csv", index=False)
