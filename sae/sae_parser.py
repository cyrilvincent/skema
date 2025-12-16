import art
import psycopg2
import config
import argparse
import pandas as pd
import os
from sqlentities import Context


class SAEBaseParser:

    def __init__(self, context):
        self.context = context
        self.df: pd.DataFrame | None = None
        self.finess_col = "FI"
        self.finessj_col = "FI_EJ"
        self.base = "FAKE"
        self.postfix = "r"
        self.suffix = ""
        self.suffixes = ["", "2", "_P"]
        pd.set_option('display.max_columns', None)
        pd.set_option('display.width', None)

    def read_csv(self, path: str, finess_col: str) -> pd.DataFrame:
        dtype = {finess_col: str, "AN": int}
        try:
            df = pd.read_csv(path, sep=";", dtype=dtype, low_memory=False)
        except UnicodeDecodeError:
            df = pd.read_csv(path, sep=";", dtype=dtype, encoding="latin_1", low_memory=False)
        return df

    def load(self, path) -> pd.DataFrame:
        print(f"Load {path}")
        df = self.read_csv(path, self.finess_col)
        df.columns = df.columns.str.strip().str.lower()
        if "bor" in df.columns:
            df = df.drop("bor", axis=1)
        if self.suffix != "":
            df = df.drop(self.finessj_col.lower(), axis=1)
            if "rs" in df.columns:
                df = df.drop("rs", axis=1)
        print(f"Found {len(df)} rows and {len(df.columns)} columns")
        return df

    def manage_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        return df

    def loads_by_year(self, path, suffix, postfix, year) -> pd.DataFrame | None:
        print(f"Loads {self.base}{suffix} in {year} from {path}")
        self.suffix = suffix
        file_path = f"{path}{year}/{self.base}{suffix}_{year}{postfix}.csv"
        if os.path.exists(file_path):
            df = self.load(file_path)
            df = self.manage_columns(df)
            print(df)
            return df
        return None

    def loads(self, path, suffix):
        print(f"Loads all {self.base}{suffix} from {path}")
        for year in range(2024, 2019, -1):
            postfix = self.postfix if year != 2020 else ""
            self.df = self.loads_by_year(path, suffix, postfix, year)
            if self.df is not None:
                self.commit(year)

    def load3(self, path):
        for suffix in self.suffixes:
            self.loads(path, suffix)

    def commit(self, year):
        print("Deleting old values")
        table = f"{self.base[:-1] if self.base.endswith("S") else self.base}{self.suffix.replace("2", "_detail")}".lower()
        try:
            conn = psycopg2.connect(config.connection_string)
            sql = f"delete from sae.{table} where an={year}"
            with conn.cursor() as cur:
                cur.execute(sql)
            conn.commit()
            conn.close()
            print("Deleted")
        except Exception as ex:
            print(f"No table {table}")
        print(f"Committing into {table}")
        self.df.to_sql(table, config.connection_string, schema="sae", chunksize=10000, if_exists="append", index=False)
        print("Committed")


class SAEUrgencesParser(SAEBaseParser):

    def __init__(self, context):
        super().__init__(context)
        self.base = "URGENCES"

    def manage_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        if self.suffix == "2":
            if "hmed" not in df.columns:
                df["hmed"] = None
            if "hide" not in df.columns:
                df["hide"] = None
            if "gde" in df.columns:
                df = df.drop("gde", axis=1)
        elif self.suffix == "_P":
            if "effpl" not in df.columns:
                df["effpl"] = None
            if "effpa" not in df.columns:
                df["effpa"] = None
            if "etp" not in df.columns:
                df["etp"] = df["etpsal"] + df["efflib"].fillna(0)
            else:
                df["etpsal"] = None
                df["efflib"] = None
        return df

# select * from sae.urgence_detail ud
# join etablissement e on e.nofinesset=ud.fi
# join adresse_raw ar on e.adresse_raw_id=ar.id
# join adresse_norm an on ar.adresse_norm_id=an.id
# where ud.an=2024
# and ud.urg='GEN'

class SAEPsyParser(SAEBaseParser):

    def __init__(self, context):
        super().__init__(context)
        self.base = "PSY"

    def manage_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        if self.suffix == "":
            if "etp_pkt" not in df.columns:
                df["etp_pkt"] = df["etpsal_pkt"].fillna(0) + df["efflib_pkt"].fillna(0)
            if "cap_had" not in df.columns:
                df["cap_had"] = None
                df["jou_had"] = None
            if "jou_st" not in df.columns:
                df["jou_st"] = None
            if "nb_cmp_seul_pa" in df.columns:
                df["nb_cmp_seul"] = df["nb_cmp_seul_pa"].fillna(0) + df["nb_cmp_seul_pl"]
                df = df.drop(["nb_cmp_seul_pa", "nb_cmp_seul_pl"], axis=1)
            if "hplefflib_pkt" not in df.columns:
                df["hplefflib_pkt"] = None
                df["hpletpsal_pkt"] = None
                df["hplefflib_med"] = None
                df["hpletpsal_med"] = None
                df["hplefflib_pnm"] = None
                df["hpletpsal_pnm"] = None
                df["hpletp_inf"] = None
                df["hpletp_aid"] = None
                df["hpletp_psy"] = None
                df["hpletp_ree"] = None
                df["hpletp_edu"] = None
            if "fil_tpl" not in df.columns:
                df["fil_tpl"] = None
                df["fil_pla"] = None
            if "effpl_pkt" not in df.columns:
                df["effpl_pkt"] = None
                df["effpa_pkt"] = None
                df["effpl_med"] = None
                df["effpa_med"] = None
                df["etp_med"] = None
                df["etp_pnm"] = None
                df["effpl_pnm"] = None
                df["effpa_pnm"] = None
                df["hpleffpl_pkt"] = None
                df["hpleffpa_pkt"] = None
                df["hpletp_pkt"] = None
                df["hpleffpl_med"] = None
                df["hpleffpa_med"] = None
                df["hpletp_med"] = None
                df["hpleffpl_pnm"] = None
                df["hpleffpa_pnm"] = None
                df["hpletp_pnm"] = None
        elif self.suffix == "2":
            for l in ["a", "b", "c", "d"]:
                for i in range(20, 50):
                    col = f"psy_{l}{i}"
                    if col not in df.columns:
                        df[col] = None
        return df


class SAEQ20Parser(SAEBaseParser):

    def __init__(self, context):
        super().__init__(context)
        self.base = "Q20"

    def manage_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        if "cf_at" in df.columns:
            df = df.drop(["cf_at", "cf_au"], axis=1)
        if "etp_at" not in df.columns:
            df["etp_at"] = 0
            df["etp_au"] = 0
        return df


class SAEQ21Parser(SAEBaseParser):

    def __init__(self, context):
        super().__init__(context)
        self.base = "Q21"


class SAEQ22Parser(SAEBaseParser):

    def __init__(self, context):
        super().__init__(context)
        self.base = "Q22"

    def manage_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        if "inttot" not in df.columns:
            df["inttot"] = 0
        return df


class SAEQ23Parser(SAEBaseParser):

    def __init__(self, context):
        super().__init__(context)
        self.base = "Q23"


class SAEQ24Parser(SAEBaseParser):

    def __init__(self, context):
        super().__init__(context)
        self.base = "Q24"

    def manage_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        if "dirsi" not in df.columns:
            df["dirsi"] = 0
            df["drsni"] = 0
            df["pnmhsf"] = 0
        return df


class SAESygenParser(SAEBaseParser):

    def __init__(self, context):
        super().__init__(context)
        self.base = "SYGEN"

    def manage_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        if "cap_complet_gen" not in df:
            df["cap_complet_gen"] = 0
            df["cap_complet_inf"] = 0
            df["cap_complet_pen"] = 0
            df["cap_complet_tot"] = 0
            df["nb_cattp_pen"] = 0
            df["act_cattp_pen"] = 0
            df["nb_cmp_gen"] = 0
            df["nb_cmp_inf"] = 0
            df["nb_cmp_tot"] = 0
            df["act_cmp_gen"] = 0
            df["act_cmp_inf"] = 0
            df["act_cmp_tot"] = 0
            df["sej_reanim"] = 0
            df["etpint"] = 0
            df["eff_sag"] = 0
            df["eff_cad"] = 0
            df["eff_infavecspe"] = 0
            df["eff_infsansspe"] = 0
            df["eff_aid"] = 0
            df["eff_ash"] = 0
            df["eff_psycho"] = 0
            df["eff_reedu"] = 0
            df["eff_sag"] = 0
            df["eff_soins"] = 0
            df["eff_dir"] = 0
            df["eff_tec"] = 0
            df["eff_tot_hors_soins"] = 0
            df["eff_tot_pnm"] = 0
            df["eff_dirsoi"] = 0
            df["eff_autadm"] = 0
            df["eff_edu"] = 0
            df["eff_dtsoc"] = 0
            df["eff_perspharma"] = 0
            df["eff_perslabo"] = 0
            df["eff_persradio"] = 0
            df["eff_autmedtec"] = 0
            df["eff_tec"] = 0
            df["eff_tot_hors_soins"] = 0
            df["eff_tot_pnm"] = 0
            df["etp_sag"] = 0
            df["etp_cad"] = 0
            df["etp_infavecspe"] = 0
            df["etp_infsansspe"] = 0
            df["etp_aid"] = 0
            df["etp_ash"] = 0
            df["etp_psycho"] = 0
            df["etp_reedu"] = 0
            df["etp_soins"] = 0
            df["etp_dir"] = 0
            df["etp_dirsoi"] = 0
            df["etp_autadm"] = 0
            df["etp_edu"] = 0
            df["etp_dtsoc"] = 0
            df["etp_perspharma"] = 0
            df["etp_perslabo"] = 0
            df["etp_persradio"] = 0
            df["etp_autmedtec"] = 0
            df["etp_tec"] = 0
            df["etp_tot_hors_soins"] = 0
            df["etp_tot_pnm"] = 0
        if "consult_ext" not in df.columns:
            df["consult_ext"] = 0
            df["fil_tpl_gen"] = 0
            df["fil_tpl_inf"] = 0
            df["fil_tpl_pen"] = 0
            df["fil_tpl_tot"] = 0
            df["inttot"] = 0
            df["eff_dirinf"] = 0
            df["etp_dirinf"] = 0
            df["pharma_a19"] = 0
        return df


if __name__ == '__main__':
    art.tprint(config.name, "big")
    print("SAE Parser")
    print("==========")
    print(f"V{config.version}")
    print(config.copyright)
    print()
    parser = argparse.ArgumentParser(description="SAE Parser")
    parser.add_argument("path", help="Directory path")
    parser.add_argument("-e", "--echo", help="Sql Alchemy echo", action="store_true")
    args = parser.parse_args()
    context = Context()
    context.create(echo=args.echo)
    db_size = context.db_size()
    print(f"Database {context.db_name}: {db_size:.0f} MB")
    # p = SAEUrgencesParser(context)
    # p.loads(args.path, "2")
    # p.loads(args.path, "_P")
    p = SAEPsyParser(context)
    p.loads(args.path, "")
    # p.load3(args.path)
    # p = SAEQ20Parser(context)
    # p.loads(args.path, "")
    # p = SAEQ21Parser(context)
    # p.loads(args.path, "")
    # p = SAEQ22Parser(context)
    # p.loads(args.path, "")
    # p = SAEQ23Parser(context)
    # p.loads(args.path, "")
    # p = SAEQ24Parser(context)
    # p.loads(args.path, "")
    # p = SAESygenParser(context)
    # p.loads(args.path, "")
    new_db_size = context.db_size()
    print(f"Database {context.db_name}: {new_db_size:.0f} MB")
    print(f"Database grows: {new_db_size - db_size:.0f} MB ({((new_db_size - db_size) / db_size) * 100:.1f}%)")

    # data\sae\
