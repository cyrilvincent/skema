
import pandas as pd
import numpy as np

# Charger les données
df = pd.read_csv("anest.csv")

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

# Garder les colonnes nécessaires
df = df[['ps_id', 'gender', 'nom', 'prénom', 'codeccamdelacte', 'naturedexercice', 'convention',
         'codeinsee', 'montantgénéralementconstaté', 'borneinférieuredumontant', 'bornesupérieuredumontant',
         'adresse_id', 'date_source_id', 'optioncontratdaccèsauxsoins', 'matchcp', 'dep']]

# Créer une clé combinée
df['b'] = df['ps_id'].astype(str) + df['adresse_id'].astype(str)

# Identifier les adresses uniques par ps_id
df['unique'] = df.groupby('ps_id')['adresse_id'].transform('nunique')
df['un'] = df['unique']

# Comptage par département
df['NB_total'] = df.groupby('dep')['ps_id'].transform('nunique')
df['NB2_total'] = df[df['convention'].isin([2, 3]) | ((df['convention'] == 1) & (df['optioncontratdaccèsauxsoins'] == "true"))].groupby('dep')['ps_id'].transform('nunique')
df['NB_Ftotal'] = df['ps_id'].nunique()
df['NB2_Ftotal'] = df[df['convention'].isin([2, 3]) | ((df['convention'] == 1) & (df['optioncontratdaccèsauxsoins'] == "true"))]['ps_id'].nunique()

# Correction des doublons d'option
df['cc'] = np.where(df['optioncontratdaccèsauxsoins'] == "false", -1, np.where(df['optioncontratdaccèsauxsoins'] == "true", 1, np.nan))
df['ccc'] = df.groupby('ps_id')['cc'].transform('mean')

# Correction spécifique pour JERNITE
df.loc[(df['nom'] == "JERNITE") & (df['optioncontratdaccèsauxsoins'] == "false"), 'gender'] = "F"
df.loc[(df['nom'] == "JERNITE") & (df['optioncontratdaccèsauxsoins'] == "false"), 'ps_id'] += 1000000
df.loc[(df['nom'] == "JERNITE") & (df['optioncontratdaccèsauxsoins'] == "true"), 'prénom'] = "MOHAMED"

# Pondération
df['weight'] = df['un'].map({1: 1, 2: 0.5, 3: 0.33, 4: 0.25, 5: 0.2}).fillna(0)

# Filtrer les actes de consultation
df = df[df['codeccamdelacte'].str.contains("CS", na=False)]

# Moyenne des montants par acte
df['mp'] = df.groupby(['b', 'convention', 'codeccamdelacte'])['montantgénéralementconstaté'].transform('mean')
df.loc[(df['codeccamdelacte'] == "CS_+MEP+NFP") & (df['convention'] == 1) & (df['optioncontratdaccèsauxsoins'] == False), 'mp'] = 30

# Supprimer les doublons
df = df.drop_duplicates(subset=['b', 'convention', 'codeccamdelacte'])
df['prixmoyen'] = df.groupby(['b', 'convention'])['mp'].transform('max')
df = df.drop_duplicates(subset=['b', 'convention'])

# Remplacer les prix manquants
df['prixmoyen'] = df['prixmoyen'].replace(0, 30)

# Calculs par département
df['NB'] = df.groupby('dep')['ps_id'].transform('nunique')
df['NB2'] = df[df['convention'].isin([2, 3]) | ((df['convention'] == 1) & (df['optioncontratdaccèsauxsoins'] == "true"))].groupby('dep')['ps_id'].transform('nunique')
df['NB_F'] = df['ps_id'].nunique()
df['NB2_F'] = df[df['convention'].isin([2, 3]) | ((df['convention'] == 1) & (df['optioncontratdaccèsauxsoins'] == "true"))]['ps_id'].nunique()

# Part de S2
df['ShareS2'] = df['NB2'] / df['NB']
df['ShareS2_F'] = df['NB2_F'] / df['NB_F']

# Dépassement
df['exessr'] = ((df['prixmoyen'] - 30) / 30) * 100

# Comptage des dépassements
for seuil in [10, 25, 50, 75, 100]:
    df[f'c{seuil}'] = df.groupby('dep')['exessr'].transform(lambda x: (x >= seuil).sum())
    df[f'c{seuil}_F'] = (df['exessr'] >= seuil).sum()

# Proportions
for seuil in [10, 25, 50, 100]:
    df[f'r{seuil}'] = (df[f'c{seuil}'] / df['NB']) * 100
    df[f'r{seuil}_F'] = df[f'c{seuil}_F'] / df['NB_F']

# Moyennes
df['PF'] = df['prixmoyen'].mean()
df['PFS2'] = df[df['convention'].isin([2, 3]) | ((df['convention'] == 1) & (df['optioncontratdaccèsauxsoins'] == "true"))]['prixmoyen'].mean()

df['PrixMoyen'] = df.groupby('dep')['prixmoyen'].transform('mean')
df['PrixMoyenS2'] = df[df['convention'].isin([2, 3]) | ((df['convention'] == 1) & (df['optioncontratdaccèsauxsoins'] == "true"))].groupby('dep')['prixmoyen'].transform('mean')

df['depmoyen'] = round(((df['PrixMoyen'] - 30) / 30) * 100, 3)
df['depmoyenS2'] = round(((df['PrixMoyenS2'] - 30) / 30) * 100, 3)
df['depmoyen_F'] = ((df['PF'] - 30) / 30) * 100
df['depmoyen_FS2'] = ((df['PFS2'] - 30) / 30) * 100

# Nettoyage final
df = df.drop_duplicates(subset='dep')
df['depmoyen'] = df['depmoyen'].fillna(0)

# Export final
df.to_csv("resultats_analyse.csv", index=False)
