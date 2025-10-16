import argparse
import art
import pandas as pd
import config
import numpy as np
import psycopg2
import json

class DepassementService:

    def __init__(self, study_id: int, acte: str, acte2s: list[str] | None, is_prix_moyen_correction=True, is_correct_bug_optam=True):
        self.df: pd.DataFrame = pd.DataFrame()
        self.mask_s2 = None
        self.study_id = study_id
        self.df_study: pd.DataFrame = pd.DataFrame()
        self.profession_type = ""
        self.datesource_min = 0
        self.datesource_max = 0
        self.tarif_s1 = 0
        self.acte = acte
        self.acte2s = acte2s
        self.actes = None
        self.is_prix_moyen_correction = is_prix_moyen_correction # A généraliser sauf dentiste
        self.is_correct_bug_optam = is_correct_bug_optam # A généraliser

    def depassement_study(self):
        print(f"Search study {self.study_id}")
        sql = f"select * from depassement_study where id={self.study_id}"
        self.df_study = pd.read_sql(sql, config.connection_string)
        self.profession_type = self.df_study.iloc[0]["profession_type"]
        self.datesource_min = self.df_study.iloc[0]["datesource_min"]
        self.datesource_max = self.df_study.iloc[0]["datesource_max"]
        self.tarif_s1 = self.df_study.iloc[0]["tarif_s1"]
        print(f"Found {self.profession_type} between {self.datesource_min}-{self.datesource_max} for tarif_s1 {self.tarif_s1}€")

    def get_or_add_depassement(self, profession_type: str, datesource_min: int, datesource_max: int, tarif_s1: float,
                               acte: str | None, acte2s: list | None, actes: list | None):
        self.profession_type = profession_type
        self.datesource_min = datesource_min
        self.datesource_max = datesource_max
        self.tarif_s1 = tarif_s1
        self.acte = acte
        self.acte2s = json.dumps(acte2s) if actes is not None else None
        self.actes = json.dumps(actes) if actes is not None else None
        sql = f"""select * from deplassement_study
        profession_type='{profession_type}' and date_source_min={datesource_min} and date_source_max={datesource_max},
        and tarif_s1={tarif_s1} and {"acte='"+str(self.acte)+"'" if self.acte is not None else "acte is null"}
        and {"acte2s='"+str(self.acte2s)+"'" if self.acte2s is not None else "acte2s is null"}
        and {"actes='"+str(self.actes)+"'" if self.actes is not None else "actes is null"}"""
        self.df_study = pd.read_sql(sql, config.connection_string)
        if len(self.df_study) == 0:
            print("No study found, create it")
            pass # add
        else:
            self.study_id = self.df_study.iloc[0]["study_id"]
            print(f"Found study with id={self.study_id}")



    def load(self, path: str = None):
        if path is not None:
            print(f"Loading {path}")
            self.df = pd.read_csv(path, low_memory=False)
            print(f"Nb rows: {len(self.df)}")
        else:
            print("Querying")
            sql = f"""select p.*, t.*, tds.date_source_id, b.id as adresse_id, an.cp as cp, ar.dept_id as dept_id, b.code_insee from ps p
            join tarif t on t.ps_id = p.id
            join tarif_date_source tds on tds.tarif_id = t.id
            join cabinet c on t.cabinet_id = c.id
            join adresse_raw ar on c.adresse_raw_id = ar.id
            join adresse_norm an on ar.adresse_norm_id = an.id
            join ban b on an.ban_id = b.id
            join profession_type pt on pt.profession = '{self.profession_type}' and t.profession_id = pt.profession_id
            where tds.date_source_id >= {self.datesource_min} and  tds.date_source_id <= {self.datesource_max}"""
            # todo ajouter acte like '{acte}%' pour tous sauf dentiste
            # todo virer join adresse_raw, adresse_norm et ban
            self.df = pd.read_sql(sql, config.connection_string)
            print(f"Found {len(self.df)} rows")

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

    def filter_acte2(self):
        print("Filter acte 2")
        if self.acte2s is not None:
            self.df = self.df[self.df['codeccamdelacte'].isin(self.acte2s)]

    def override_tarif_s1(self):
        print(f"Override tarif s1 by {self.tarif_s1}")
        self.df.loc[
            (self.df['convention'] == 1) & (self.df['optioncontratdaccèsauxsoins'] == False), 'mp'] = self.tarif_s1
        # /!\ is False ne fonctionne pas en Pandas

    def prix_moyen(self):
        if self.is_correct_bug_optam:
            self.df = self.df.sort_values(by=['b', "convention", "codeccamdelacte", "optioncontratdaccèsauxsoins", "date_source_id"], ascending=[True, True, True, False, True])
        self.df = self.df.drop_duplicates(subset=['b', 'convention', 'codeccamdelacte'])
        print(f"Prix moyen for {len(self.df)} rows")
        self.df['prixmoyen'] = self.df.groupby(['b', 'convention'])['mp'].transform('max')
        # print(f"prixmoyen", self.df['prixmoyen'].unique())
        self.df = self.df.drop_duplicates(subset=['b', 'convention'])
        print(f"group by: {self.df.groupby('convention')["ps_id"].nunique()}")
        # self.df = self.df.drop_duplicates(subset=['b']) # Inutile
        print(f"mp==0 {len(self.df[self.df["mp"] == 0])}")
        self.df['prixmoyen'] = self.df['prixmoyen'].replace(0, self.tarif_s1)
        print(f"After prix moyen: {len(self.df)} rows")
        print(f"ps_id unique after prix moyen: {self.df.groupby('convention')["ps_id"].nunique()}")

    def prix_moyen_correction(self):
        if self.is_prix_moyen_correction:
            print("Prix moyen correction")
            self.df.loc[self.df['prixmoyen'] < self.tarif_s1, 'prixmoyen'] = self.tarif_s1
            print(f"prixmoyen", self.df['prixmoyen'].unique())


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
        # A mettre en prod
        # self.df.to_csv(
        #     f"data/depassement/out/depassement_{self.profession_type}_{self.datesource_min}_{self.datesource_max}_{self.tarif_s1}_{self.study_id}.csv",
        #     index=False)

    def commit(self):
        conn = psycopg2.connect(config.connection_string)
        sql = f"delete from depassement where depassement_study_id={self.study_id}"
        with conn.cursor() as cur:
            cur.execute(sql)
        conn.commit()
        conn.close()
        self.df["depassement_study_id"] = self.study_id
        self.df.to_sql("depassement", config.connection_string, if_exists="append", index=False)
        print("Commited")

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
        self.commit()


class DepassementPsychiatre(DepassementService):

    def __init__(self, study_id: int, acte="CNP", acte2s=["CNP", "CNP+MPC+MCS"]):
        super().__init__(study_id, acte, acte2s)

    # def filter_acte2(self):
    #     self.df = self.df[(self.df['codeccamdelacte'] == "CNP") | (self.df['codeccamdelacte'] == "CNP+MPC+MCS")]

    # def override_tarif_s1(self):
    #     super().override_tarif_s1()
    #     self.df.loc[
    #         (self.df['convention'] == 1) & (self.df['optioncontratdaccèsauxsoins'] == False), 'mp'] = self.tarif_s1



class DepassementAnest(DepassementService):

    def __init__(self, study_id: int, acte="CS", acte2s=None):
        super().__init__(study_id, acte, acte2s)

    # def correction_nb(self):
    #     self.df.loc[(self.df['nom'] == "JERNITE") & (self.df['optioncontratdaccèsauxsoins'] == False), 'gender'] = "F"
    #     self.df.loc[(self.df['nom'] == "JERNITE") & (self.df['optioncontratdaccèsauxsoins'] == False), 'ps_id'] += 1000000
    #     self.df.loc[(self.df['nom'] == "JERNITE") & (self.df['optioncontratdaccèsauxsoins']), 'prénom'] = "MOHAMED"


    # def override_tarif_s1(self):
    #     super().override_tarif_s1()
    #     self.df.loc[(self.df['codeccamdelacte'] == "CS_+MEP+NFP") & (self.df['convention'] == 1) & (self.df['optioncontratdaccèsauxsoins'] == False), 'mp'] = self.tarif_s1

    # Bug pour le dep=85 j'ai cherché pendant 2h sans succès, j'ai un NB2=9 au lieu de 10 et je ne sais pas pourquoi
    # Le pire est que depassement_anest.py fonctionne !! J'ai vérifié ligne à ligne sans succès
    # Le pb se passe lors du drop_duplicates(subset=['b', 'convention', 'codeccamdelacte']) où j'ai une ligne en moins
    # 78	0	-1.0	0.0	0	0.0	0.4	-0.1	0	0.0	1.5	0.0	0.0	0.0	0.0
    # J'ai trouvé c'est à cause d'un tri => les tris sont importants lors des drop_duplicates

class DepassementCardiologue(DepassementService):

    def __init__(self, study_id: int, acte="CS", acte2s=["CSC", "CSC+MCC"]):
        super().__init__(study_id, acte, acte2s, is_prix_moyen_correction=True)

    # def filter_acte2(self):
    #     # self.df = self.df[(self.df['codeccamdelacte'] == "CSC") | (self.df['codeccamdelacte'] == "CSC+MCC")]


    # def override_tarif_s1(self):
    #     super().override_tarif_s1()
    #     self.df.loc[
    #         (self.df['convention'] == 1) & (self.df['optioncontratdaccèsauxsoins'] == False), 'mp'] = self.tarif_s1

    # def prix_moyen_correction(self):
    #     super().prix_moyen_correction()
    #     self.df.loc[self.df['prixmoyen'] < self.tarif_s1, 'prixmoyen'] = self.tarif_s1
    #     print(f"prixmoyen", self.df['prixmoyen'].unique())


class DepassementDermatologue(DepassementService):

    def __init__(self, study_id: int, acte="CS", acte2s=["CS_", "CS_+MPC", "CS_+MPC+MCS"]):
        super().__init__(study_id, acte, acte2s)

    # def filter_acte2(self):
    #     # self.df = self.df[(self.df['codeccamdelacte'] == "CS_") | (self.df['codeccamdelacte'] == "CS_+MPC") | (self.df['codeccamdelacte'] == "CS_+MPC+MCS")]
    #     self.df = self.df[self.df['codeccamdelacte'].isin(self.acte2s)]

    # def override_tarif_s1(self):
    #     super().override_tarif_s1()
    #     self.df.loc[
    #         (self.df['convention'] == 1) & (self.df['optioncontratdaccèsauxsoins'] == False), 'mp'] = self.tarif_s1


class DepassementGastro(DepassementService):

    def __init__(self, study_id: int, acte="CS", acte2s=["CS_", "CS_+MPC", "CS_+MPC+MCS"]):
        super().__init__(study_id, acte, acte2s, is_prix_moyen_correction=True)


class DepassementGyneco(DepassementService):

    def __init__(self, study_id: int, acte="CS", acte2s=["CS_", "CS_+MPC", "CS_+MPC+MCS", "CS_+MGM", "CS_+MGM+MCS"]):
        super().__init__(study_id, acte, acte2s, is_correct_bug_optam=True)


class DepassementOphtalmo(DepassementService):

    def __init__(self, study_id: int, acte="CS", acte2s=["CS_", "CS_+MPC", "CS_+MPC+MCS"]):
        super().__init__(study_id, acte, acte2s)


class DepassementPediatre(DepassementService):

    def __init__(self, study_id: int, acte="CS", acte2s=["CS_+MEP+NFP", "CS_+NFP"]):
        super().__init__(study_id, acte, acte2s)


class DepassementRadio(DepassementService):

    def __init__(self, study_id: int, acte="ZBQK0020", acte2s=None):
        super().__init__(study_id, acte, acte2s, is_prix_moyen_correction=True)


class DepassementDentiste(DepassementService):

    def __init__(self, study_id: int, actes=["HBLD4910", "HBLD6340", "HBLD7340"]):
        super().__init__(study_id, "", None,False,False)
        self.actes = actes
        self.numerotation: list[str] = []
        for i in range(len(self.actes)):
            if i == 0:
                self.numerotation.append("")
            else:
                self.numerotation.append(str(i+1))

    def manage_nb(self):
        print("Manage unique and NB")
        pd.options.mode.copy_on_write = True
        self.df['b'] = self.df['ps_id'].astype(str) + "_" + self.df['adresse_id'].astype(str)
        self.df = self.df.sort_values(by='ps_id')
        self.df['unique'] = self.df.groupby('ps_id')['adresse_id'].transform('nunique')
        self.df['un'] = self.df['unique']
        self.df['NB_total'] = self.df.groupby('dep')['ps_id'].transform('nunique')
        self.df = self.df.sort_values(by='dep')
        self.df['c'] = 1
        self.df['NB_Ftotal'] = self.df.groupby('c')['ps_id'].transform('nunique')
        self.df['weight'] = self.df['un'].map({1: 1, 2: 0.5, 3: 0.3333, 4: 0.25, 5: 0.2}).fillna(0) # Jamais utilisé
        self.df = self.df[self.df['codeccamdelacte'].isin(self.actes)]
        self.df = self.df[self.df["montantgénéralementconstaté"] != 0]
        self.df = self.df.sort_values(by=['b', "convention", "date_source_id"])
        for n, acte in zip(self.numerotation, self.actes):
            self.df[f"mp{n}"] = np.nan
            mask = self.df["codeccamdelacte"] == acte
            self.df.loc[mask, f"mp{n}"] = self.df[mask].groupby(["b", "convention"])["montantgénéralementconstaté"].transform("mean")
            self.df[f"mp{n}"] = self.df.groupby(['b', 'convention'])[f"mp{n}"].transform('max')
            self.df[f"NB{n}"] = np.nan
            mask = self.df["codeccamdelacte"] == acte
            self.df.loc[mask, f"NB{n}"] = self.df[mask].groupby(["dep", "convention"])["ps_id"].transform("nunique")
            self.df[f"NB{n}"] = self.df.groupby(['dep', "convention"])[f"NB{n}"].transform('mean')
            self.df[f"NB{n}_F"] = np.nan
            mask = self.df["codeccamdelacte"] == acte
            self.df.loc[mask,f"NB{n}_F"] = self.df[mask].groupby(["c"])["ps_id"].transform("nunique")
            self.df[f"NB{n}_F"] = self.df.groupby(["c"])[f"NB{n}_F"].transform('mean')
        self.df = self.df.sort_values(by=['dep', "convention"])

    def filter_acte(self):
        pass

    def prix_moyen(self):
        self.df = self.df.drop_duplicates(subset=['b', 'convention'])  # 20279 ok
        self.df = self.df.sort_values(by=['b', "convention"])
        for n in self.numerotation:
            self.df[f"prixmoyen{n}"] = self.df[f"mp{n}"]


    def departement(self):
        print("By departement")
        self.df = self.df.drop_duplicates(subset=['b'])  # 20279 ok
        for n in self.numerotation:
            self.df[f'exessr{n}'] = ((self.df[f'prixmoyen{n}'] - self.tarif_s1) / self.tarif_s1) * 100
            self.df[f'PF{n}'] = self.df[f'prixmoyen{n}'].mean()
            self.df[f'PrixMoyen{n}'] = self.df.groupby('dep')[f'prixmoyen{n}'].transform('mean')
            self.df[f'depmoyen{n}'] = ((self.df[f'PrixMoyen{n}'] - self.tarif_s1) / self.tarif_s1) * 100
            self.df[f"depmoyen_F{n}"] = ((self.df[f'PF{n}'] - self.tarif_s1) / self.tarif_s1) * 100
        # self.df['exessr'] = ((self.df['prixmoyen'] - self.tarif_s1) / self.tarif_s1) * 100
        # self.df['exessr2'] = ((self.df['prixmoyen2'] - self.tarif_s1) / self.tarif_s1) * 100
        # self.df['exessr3'] = ((self.df['prixmoyen3'] - self.tarif_s1) / self.tarif_s1) * 100
        # self.df['PF'] = self.df['prixmoyen'].mean()
        # self.df['PF2'] = self.df['prixmoyen2'].mean()
        # self.df['PF3'] = self.df['prixmoyen3'].mean()
        # self.df['PrixMoyen'] = self.df.groupby('dep')['prixmoyen'].transform('mean')
        # self.df['PrixMoyen2'] = self.df.groupby('dep')['prixmoyen2'].transform('mean')
        # self.df['PrixMoyen3'] = self.df.groupby('dep')['prixmoyen3'].transform('mean')
        # self.df['depmoyen'] = ((self.df['PrixMoyen'] - self.tarif_s1) / self.tarif_s1) * 100
        # self.df['depmoyen2'] = ((self.df['PrixMoyen2'] - self.tarif_s1) / self.tarif_s1) * 100
        # self.df['depmoyen3'] = ((self.df['PrixMoyen3'] - self.tarif_s1) / self.tarif_s1) * 100
        # self.df["depmoyen_F"] = ((self.df['PF'] - self.tarif_s1) / self.tarif_s1) * 100
        # self.df["depmoyen_F2"] = ((self.df['PF2'] - self.tarif_s1) / self.tarif_s1) * 100
        # self.df["depmoyen_F3"] = ((self.df['PF3'] - self.tarif_s1) / self.tarif_s1) * 100
        self.df = self.df.sort_values(by=['dep', 'depmoyen'], ascending=[True, False])
        self.df = self.df.drop_duplicates(subset=['dep'])
        self.df = self.df.drop(["gender", "nom", "prénom", "naturedexercice", "convention", "optioncontratdaccèsauxsoins",
                      "codeccamdelacte", "ps_id", "montantgénéralementconstaté", "borneinférieuredumontant",
                      "bornesupérieuredumontant", "date_source_id", "adresse_id", "matchcp", "codeinsee", "b", "unique",
                      "un", "weight"], axis=1)
        # self.df = self.df.drop(["gender", "nom", "prénom", "naturedexercice", "convention", "optioncontratdaccèsauxsoins",
        #               "codeccamdelacte", "ps_id", "montantgénéralementconstaté", "borneinférieuredumontant",
        #               "bornesupérieuredumontant", "date_source_id", "adresse_id", "matchcp", "codeinsee", "b", "unique",
        #               "un", "weight", "mp", "mp2", "mp3", "prixmoyen", "prixmoyen2", "prixmoyen3", "exessr", "exessr2",
        #               "exessr3"], axis=1)
        for n in self.numerotation:
            self.df = self.df.drop([f"mp{n}", f"prixmoyen{n}", f"exessr{n}"], axis=1)
        print(f"Nb dep: {len(self.df)}")


    def last_row(self):
        print("Last row")
        df_to_duplicate = self.df[self.df['dep'] == 75].copy()
        df_to_duplicate['dup'] = 1  # marquer les duplications
        self.df['dup'] = 0
        self.df = pd.concat([self.df, df_to_duplicate], ignore_index=True)
        self.df.loc[self.df["dup"] == 1, "dep"] = 0
        self.df.loc[self.df["dup"] == 1, "NB_total"] = self.df.loc[self.df["dup"] == 1]["NB_Ftotal"]
        for n in self.numerotation:
            self.df.loc[self.df["dup"] == 1, f"NB{n}"] = self.df.loc[self.df["dup"] == 1][f"NB{n}_F"]
            self.df.loc[self.df["dup"] == 1, f"PrixMoyen{n}"] = self.df.loc[self.df["dup"] == 1][f"PF{n}"]
            self.df.loc[self.df["dup"] == 1, f"depmoyen{n}"] = self.df.loc[self.df["dup"] == 1][f"depmoyen_F{n}"]
        # self.df.loc[self.df["dup"] == 1, "NB2"] = self.df.loc[self.df["dup"] == 1]["NB2_F"]
        # self.df.loc[self.df["dup"] == 1, "NB3"] = self.df.loc[self.df["dup"] == 1]["NB3_F"]
        # self.df.loc[self.df["dup"] == 1, "PrixMoyen"] = self.df.loc[self.df["dup"] == 1]["PF"]
        # self.df.loc[self.df["dup"] == 1, "PrixMoyen2"] = self.df.loc[self.df["dup"] == 1]["PF2"]
        # self.df.loc[self.df["dup"] == 1, "PrixMoyen3"] = self.df.loc[self.df["dup"] == 1]["PF3"]
        # self.df.loc[self.df["dup"] == 1, "depmoyen"] = self.df.loc[self.df["dup"] == 1]["depmoyen_F"]
        # self.df.loc[self.df["dup"] == 1, "depmoyen2"] = self.df.loc[self.df["dup"] == 1]["depmoyen_F2"]
        # self.df.loc[self.df["dup"] == 1, "depmoyen3"] = self.df.loc[self.df["dup"] == 1]["depmoyen_F3"]
        self.df = self.df.drop(["NB_Ftotal", "dup", "c"], axis=1)
        for n in self.numerotation:
            self.df = self.df.drop([f"NB{n}_F", f"PF{n}", f"depmoyen_F{n}"], axis=1)
        self.df = self.df.reset_index(drop=True)

    def commit(self):
        print("Commiting")
        try:
            conn = psycopg2.connect(config.connection_string)
            sql = f"delete from depassement_multiacte where depassement_study_id={self.study_id}"
            with conn.cursor() as cur:
                cur.execute(sql)
            conn.commit()
            conn.close()
        except:
            pass
        self.df["depassement_study_id"] = self.study_id
        self.df.to_sql("depassement_multiacte", config.connection_string, if_exists="append", index=False) # LA &ère fois sur le serveur mettre index=id
        print("Commited")


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
    ds = DepassementPsychiatre(1)
    ds.process("data/depassement/psychiatres.csv")
    da = DepassementAnest(2)
    da.process("data/depassement/anest.csv")
    dc = DepassementCardiologue(3)
    dc.process("data/depassement/cardiologues.csv")
    dd = DepassementDermatologue(4)
    dd.process("data/depassement/dermatologue.csv") # ok
    dg = DepassementGastro(5)
    dg.process("data/depassement/gastro.csv")
    dc = DepassementGyneco(6)
    dc.process("data/depassement/gyne.csv")
    do = DepassementOphtalmo(7)
    do.process("data/depassement/ophtal.csv")
    dp = DepassementPediatre(8)
    dp.process("data/depassement/pediatres.csv")
    dr = DepassementRadio(9)
    dr.process("data/depassement/radiologistes.csv")
    dd = DepassementDentiste(10)
    dd.process("data/depassement/d2.csv")
    # dd.process()
    # todo tester dentiste en sql (sur serveur uniquement car pas les data en local)
    # todo ajouter acte acte2s et actes dans la bd pour sauvegarder les data initiales
    # todo créer automatiquement la study via sqlalchemy ou pandas aujourd'hui elle est créée à la main









