import argparse
import art
import pandas as pd
import config
import numpy as np

class DepassementService:

    def __init__(self, study_id: int):
        self.df: pd.DataFrame = pd.DataFrame()
        self.mask_s2 = None
        self.study_id = study_id
        self.df_study: pd.DataFrame = pd.DataFrame()
        self.profession_type = ""
        self.datesource_min = 0
        self.datesource_max = 0
        self.tarif_s1 = 0
        self.acte = ""

    def depassement_study(self):
        print(f"Search study {self.study_id}")
        sql = f"select * from depassement_study where id={self.study_id}"
        df_study = pd.read_sql(sql, config.connection_string)
        self.profession_type = df_study.iloc[0]["profession_type"]
        self.datesource_min = df_study.iloc[0]["datesource_min"]
        self.datesource_max = df_study.iloc[0]["datesource_max"]
        self.tarif_s1 = df_study.iloc[0]["tarif_s1"]
        print(f"Found {self.profession_type} between {self.datesource_min}-{self.datesource_max} for tarif_s1 {self.tarif_s1}€")

    def load(self, path: str = None):
        if path is not None:
            print(f"Loading {path}")
            self.df = pd.read_csv(path, low_memory=False)
            print(f"Nb rows: {len(self.df)}")
        else:
            #sql
            pass

    def rename(self):
        self.df.rename(columns={
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
        self.df = self.df[['ps_id', 'gender', 'nom', 'prénom', 'codeccamdelacte', 'naturedexercice', 'convention',
                     'codeinsee', 'montantgénéralementconstaté', 'borneinférieuredumontant', 'bornesupérieuredumontant',
                     'adresse_id', 'date_source_id', 'optioncontratdaccèsauxsoins', 'matchcp', 'dep']]

    def manage_nb(self):
        print("Manage unique and NB")
        pd.options.mode.copy_on_write = True
        self.df['b'] = self.df['ps_id'].astype(str) + self.df['adresse_id'].astype(str)
        print(f"Nb unique ps_id {self.df["ps_id"].nunique()}")
        print(f"Nb unique b {self.df["b"].nunique()}")
        self.df = self.df.sort_values(by='ps_id')
        self.df['unique'] = self.df.groupby('ps_id')['adresse_id'].transform('nunique')
        self.df['un'] = self.df['unique']
        self.df['NB_total'] = self.df.groupby('dep')['ps_id'].transform('nunique')
        self.df = self.df.sort_values(by='dep')
        print(f"Nb total by dept: {self.df["NB_total"].unique()}")
        self.mask_s2 = (self.df['convention'].isin([2, 3])) | ((self.df['convention'] == 1) & (self.df['optioncontratdaccèsauxsoins']))
        self.df['NB2_total'] = self.df[self.mask_s2].groupby('dep')['ps_id'].transform('nunique')
        self.df['NB2_total'] = self.df.groupby('dep')['NB2_total'].transform('max')
        self.df["NB2_total"] = self.df["NB2_total"].fillna(0)
        print(f"Nb2 total by dept: {self.df["NB2_total"].unique()}")
        self.df['c'] = 1
        self.df['NB_Ftotal'] = self.df.groupby('c')['ps_id'].transform('nunique')
        print(f"Nb Ftotal by dept: {self.df["NB_Ftotal"].unique()}")
        self.df['NB2_Ftotal'] = self.df[self.mask_s2].groupby('c')['ps_id'].transform('nunique')
        self.df['NB2_Ftotal'] = self.df['NB2_Ftotal'].max()
        print(f"Nb2 Ftotal by dept: {self.df["NB2_Ftotal"].unique()}")
        self.df['cc'] = np.where(self.df['optioncontratdaccèsauxsoins'] == False, -1, np.where(self.df['optioncontratdaccèsauxsoins'], 1, np.nan))
        self.df['ccc'] = self.df.groupby('ps_id')['cc'].transform('mean')

    def correction_nb(self):
        print("Correction nb")

    def filter_acte(self):
        print(f"Filter by {self.acte}")
        self.df = self.df[self.df['codeccamdelacte'].str.contains(self.acte)]
        self.mask_s2 = (self.df['convention'].isin([2, 3])) | ((self.df['convention'] == 1) & (self.df['optioncontratdaccèsauxsoins']))
        print(f"Nb {self.acte}: {len(self.df)}")
        print(f"Tab {self.acte}")
        print(self.df["codeccamdelacte"].value_counts(normalize=True))
        self.df = self.df.sort_values(by='convention')
        self.df.groupby('convention')["ps_id"].nunique()
        self.df = self.df.sort_values(by=['b', "convention", "codeccamdelacte", "date_source_id"])
        self.df['mp'] = self.df.groupby(['b', 'convention', 'codeccamdelacte'])['montantgénéralementconstaté'].transform('mean')
        print(f"Convention unique ps_id {self.df["ps_id"].nunique()}")
        # self.df = self.df.sort_values(by='convention') # A causé un bug de fou les tris sont importants pour les drop_duplicates

    def filter_acte2(self):
        print("Filter acte 2")

    def override_tarif_s1(self):
        print(f"Override tarif s1 by {self.tarif_s1}")

    def prix_moyen(self):
        # Bug stata il faudrait refaire ce tri à chaque fois
        # J'en ai parlé à Benjamin le 24/7
        # Pour moi il faut l'activer mais ca change certains résultats
        # self.df = self.df.sort_values(by=['b', "convention", "codeccamdelacte", "optioncontratdaccèsauxsoins", "date_source_id"], ascending=[True, True, True, False, True])
        self.df = self.df.drop_duplicates(subset=['b', 'convention', 'codeccamdelacte'])
        print(f"Prix moyen for {len(self.df)} rows")
        self.df['prixmoyen'] = self.df.groupby(['b', 'convention'])['mp'].transform('max')
        # print(f"prixmoyen", self.df['prixmoyen'].unique())
        self.df = self.df.drop_duplicates(subset=['b', 'convention'])
        print(f"group by: {self.df.groupby('convention')["ps_id"].nunique()}")
        # self.df = self.df.drop_duplicates(subset=['b']) # Semble inutile revérifier pour psy
        print(f"mp==0 {len(self.df[self.df["mp"] == 0])}")
        self.df['prixmoyen'] = self.df['prixmoyen'].replace(0, self.tarif_s1)
        print(f"After prix moyen: {len(self.df)} rows")
        print(f"ps_id unique after prix moyen: {self.df.groupby('convention')["ps_id"].nunique()}")

    def prix_moyen_correction(self):
        print("Prix moyen correction")

    def departement(self):
        print("By departement")
        self.df = self.df.sort_values(by="dep")
        self.df['NB'] = self.df.groupby('dep')['ps_id'].transform('nunique')
        print(f"NB by dep {self.df["NB"].unique()}")
        self.df['NB_F'] = self.df.groupby('c')['ps_id'].transform('nunique')
        print(f"NB_F by dep {self.df["NB_F"].unique()}")
        self.mask_s2 = (self.df['convention'].isin([2, 3])) | ((self.df['convention'] == 1) & (self.df['optioncontratdaccèsauxsoins']))
        self.df['NB2'] = self.df[self.mask_s2].groupby('dep')['ps_id'].transform('nunique')
        self.df['NB2'] = self.df.groupby("dep")["NB2"].transform("mean")
        self.df["NB2"] = self.df["NB2"].fillna(0)
        print(f"NB2 by dep {self.df["NB2"].unique()}")
        self.df['NB2_F'] = self.df[self.mask_s2].groupby('c')['ps_id'].transform('nunique')
        self.df['NB2_F'] = self.df['NB2_F'].mean()
        print(f"NB2_F by dep {self.df["NB_F"].unique()}")
        self.df['ShareS2'] = self.df['NB2'] / self.df['NB']
        self.df['ShareS2_F'] = self.df['NB2_F'] / self.df['NB_F']
        self.df['exessr'] = ((self.df['prixmoyen'] - self.tarif_s1) / self.tarif_s1) * 100
        for seuil in [10, 25, 50, 75, 100]:
            self.df[f'c{seuil}'] =self. df.groupby('dep')['exessr'].transform(lambda x: (x >= seuil).sum())
            self.df[f'c{seuil}_F'] = (self.df['exessr'] >= seuil).sum()
            self.df[f'r{seuil}'] = (self.df[f'c{seuil}'] / self.df['NB']) * 100
            self.df[f'r{seuil}_F'] = self.df[f'c{seuil}_F'] / self.df['NB_F']
        print("c10", self.df["c10"].unique())
        print("c25", self.df["c25"].unique())
        print("c50", self.df["c50"].unique())
        print("c100", self.df["c100"].unique())
        print("cX0_F", self.df["c10_F"].unique(), self.df["c25_F"].unique(), self.df["c50_F"].unique(),
              self.df["c100_F"].unique())  # 1465	1448	1164	333
        print("rX0_F", self.df["r10_F"].unique(), self.df["r25_F"].unique(), self.df["r50_F"].unique(), self.df["r100_F"].unique())
        self.df['PF'] = self.df['prixmoyen'].mean()  # 63.86
        print(f"PF: {self.df["PF"].unique()}")
        self.df['PFS2'] = self.df[self.mask_s2]['prixmoyen'].mean()
        print(f"PFS2: {self.df["PFS2"].unique()}")
        self.df['PrixMoyen'] = self.df.groupby('dep')['prixmoyen'].transform('mean')
        print(f"PrixMoyen: {self.df["PrixMoyen"].unique()}")
        self.df['PrixMoyenS2'] = self.df[self.mask_s2].groupby('dep')['prixmoyen'].transform('mean')
        self.df['depmoyen'] = ((self.df['PrixMoyen'] - self.tarif_s1) / self.tarif_s1) * 100
        self.df["depmoyen_F"] = ((self.df['PF'] - self.tarif_s1) / self.tarif_s1) * 100
        print(f"depmoyen_F: {self.df["depmoyen_F"].unique()}")
        self.df["PrixMoyenS2"] = self.df.groupby('dep')['PrixMoyenS2'].transform('mean')
        self.df['depmoyenS2'] = ((self.df['PrixMoyenS2'] - self.tarif_s1) / self.tarif_s1) * 100  # .round(5) * 100
        self.df['depmoyen_FS2'] = ((self.df['PFS2'] - self.tarif_s1) / self.tarif_s1) * 100
        print(f"depmoyen_FS2: {self.df["depmoyen_FS2"].unique()}")
        self.df = self.df.sort_values(by=['dep', 'depmoyen'], ascending=[True, False])
        self.df = self.df.drop_duplicates(subset=['dep'])
        self.df['depmoyen'] = self.df['depmoyen'].fillna(0)
        self.df = self.df.drop(["gender", "nom", "prénom", "naturedexercice", "convention", "optioncontratdaccèsauxsoins",
                      "codeccamdelacte", "ps_id", "montantgénéralementconstaté", "borneinférieuredumontant",
                      "bornesupérieuredumontant", "date_source_id", "adresse_id", "matchcp", "codeinsee", "b", "unique",
                      "un", "mp", "prixmoyen", "exessr", "c10", "c25", "c50", "c75", "c100"], axis=1)
        print(f"Nb dep: {len(self.df)}")

    def last_row(self):
        print("Last row")
        df_to_duplicate = self.df[self.df['dep'] == 75].copy()
        df_to_duplicate['dup'] = 1  # marquer les duplications
        self.df['dup'] = 0
        self.df = pd.concat([self.df, df_to_duplicate], ignore_index=True)
        self.df.loc[self.df["dup"] == 1, "dep"] = 0
        self.df.loc[self.df["dup"] == 1, "NB_total"] = self.df.loc[self.df["dup"] == 1]["NB_Ftotal"]
        self.df.loc[self.df["dup"] == 1, "NB2_total"] = self.df.loc[self.df["dup"] == 1]["NB2_Ftotal"]
        self.df.loc[self.df["dup"] == 1, "NB"] = self.df.loc[self.df["dup"] == 1]["NB_F"]
        self.df.loc[self.df["dup"] == 1, "NB2"] = self.df.loc[self.df["dup"] == 1]["NB2_F"]
        self.df.loc[self.df["dup"] == 1, "ShareS2"] = self.df.loc[self.df["dup"] == 1]["ShareS2_F"]
        self.df.loc[self.df["dup"] == 1, "r10"] = self.df.loc[self.df["dup"] == 1]["r10_F"]
        self.df.loc[self.df["dup"] == 1, "r25"] = self.df.loc[self.df["dup"] == 1]["r25_F"]
        self.df.loc[self.df["dup"] == 1, "r50"] = self.df.loc[self.df["dup"] == 1]["r50_F"]
        self.df.loc[self.df["dup"] == 1, "r100"] = self.df.loc[self.df["dup"] == 1]["r100_F"]
        self.df.loc[self.df["dup"] == 1, "PrixMoyen"] = self.df.loc[self.df["dup"] == 1]["PF"]
        self.df.loc[self.df["dup"] == 1, "PrixMoyenS2"] = self.df.loc[self.df["dup"] == 1]["PFS2"]
        self.df.loc[self.df["dup"] == 1, "depmoyen"] = self.df.loc[self.df["dup"] == 1]["depmoyen_F"]
        self.df.loc[self.df["dup"] == 1, "depmoyenS2"] = self.df.loc[self.df["dup"] == 1]["depmoyen_FS2"]
        self.df = self.df.drop(
            ["NB_Ftotal", "NB2_Ftotal", "NB_F", "NB2_F", "ShareS2_F", "r10_F", "r25_F", "r50_F", "r100_F", "PF", "PFS2",
             "depmoyen_F", "depmoyen_FS2", "c10_F", "c25_F", "c50_F", "c75_F", "r75_F", "r75", "c100_F", "dup", "c", "cc", "ccc"],
            axis=1)
        self.df = self.df.reset_index(drop=True)

    def save(self):
        self.df.to_csv(f"data/depassement/out/out_{self.profession_type}.csv", index=False)

    def process(self, path=None):
        self.depassement_study()
        self.load(path)
        self.rename()
        self.manage_nb()
        self.correction_nb()
        self.filter_acte()
        self.filter_acte2()
        self.override_tarif_s1()
        self.prix_moyen()
        self.prix_moyen_correction()
        self.departement()
        self.last_row()
        self.save()


class DepassementPsychiatre(DepassementService):

    def __init__(self, study_id: int):
        super().__init__(study_id)
        self.acte = "CNP"

    def filter_acte2(self):
        self.df = self.df[(self.df['codeccamdelacte'] == "CNP") | (self.df['codeccamdelacte'] == "CNP+MPC+MCS")]

    def override_tarif_s1(self):
        super().override_tarif_s1()
        self.df.loc[
            (self.df['convention'] == 1) & (self.df['optioncontratdaccèsauxsoins'] == False), 'mp'] = self.tarif_s1
        # /!\ is False ne fonctionne pas en Pandas


class DepassementAnest(DepassementService):

    def __init__(self, study_id: int):
        super().__init__(study_id)
        self.acte = "CS"

    def correction_nb(self):
        self.df.loc[(self.df['nom'] == "JERNITE") & (self.df['optioncontratdaccèsauxsoins'] == False), 'gender'] = "F"
        self.df.loc[(self.df['nom'] == "JERNITE") & (self.df['optioncontratdaccèsauxsoins'] == False), 'ps_id'] += 1000000
        self.df.loc[(self.df['nom'] == "JERNITE") & (self.df['optioncontratdaccèsauxsoins']), 'prénom'] = "MOHAMED"


    def override_tarif_s1(self):
        super().override_tarif_s1()
        self.df.loc[(self.df['codeccamdelacte'] == "CS_+MEP+NFP") & (self.df['convention'] == 1) & (self.df['optioncontratdaccèsauxsoins'] == False), 'mp'] = self.tarif_s1

    # Bug pour le dep=85 j'ai cherché pendant 2h sans succès, j'ai un NB2=9 au lieu de 10 et je ne sais pas pourquoi
    # Le pire est que depassement_anest.py fonctionne !! J'ai vérifié ligne à ligne sans succès
    # Le pb se passe lors du drop_duplicates(subset=['b', 'convention', 'codeccamdelacte']) où j'ai une ligne en moins
    # 78	0	-1.0	0.0	0	0.0	0.4	-0.1	0	0.0	1.5	0.0	0.0	0.0	0.0
    # J'ai trouvé c'est à cause d'un tri => les tris sont importants lors des drop_duplicates

class DepassementCardiologue(DepassementService):

    def __init__(self, study_id: int):
        super().__init__(study_id)
        self.acte = "CS"

    def filter_acte2(self):
        self.df = self.df[(self.df['codeccamdelacte'] == "CSC") | (self.df['codeccamdelacte'] == "CSC+MCC")]

    def override_tarif_s1(self):
        super().override_tarif_s1()
        self.df.loc[
            (self.df['convention'] == 1) & (self.df['optioncontratdaccèsauxsoins'] == False), 'mp'] = self.tarif_s1

    def prix_moyen_correction(self):
        super().prix_moyen_correction()
        self.df.loc[self.df['prixmoyen'] < self.tarif_s1, 'prixmoyen'] = self.tarif_s1
        print(f"prixmoyen", self.df['prixmoyen'].unique())


class DepassementDermatologue(DepassementService):

    def __init__(self, study_id: int):
        super().__init__(study_id)
        self.acte = "CS"

    def filter_acte2(self):
        self.df = self.df[(self.df['codeccamdelacte'] == "CS_") | (self.df['codeccamdelacte'] == "CS_+MPC") | (self.df['codeccamdelacte'] == "CS_+MPC+MCS")]

    def override_tarif_s1(self):
        super().override_tarif_s1()
        self.df.loc[
            (self.df['convention'] == 1) & (self.df['optioncontratdaccèsauxsoins'] == False), 'mp'] = self.tarif_s1


if __name__ == '__main__':
    art.tprint(config.name, "big")
    print("Depassement Service")
    print("===================")
    print(f"V{config.version}")
    print(config.copyright)
    print()
    parser = argparse.ArgumentParser(description="Depassement Service")
    parser.add_argument("-p", "--path", help="CSV Path if not SQL")
    args = parser.parse_args()
    # ds = DepassementPsychiatre(1)
    # ds.process("data/depassement/psychiatres.csv")
    # da = DepassementAnest(2)
    # da.process("data/depassement/anest.csv")
    # dc = DepassementCardiologue(3)
    # dc.process("data/depassement/cardiologues.csv")
    dd = DepassementDermatologue(4)
    dd.process("data/depassement/dermatologue.csv") # ok



