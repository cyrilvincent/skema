import art
import psycopg2
import sqlalchemy
import dask.dataframe as dd
import pyarrow
import config
import pandas
import argparse
import numpy as np
from sqlentities import Context, DateSource


class DamirParser:

    def __init__(self, context):
        self.context = context
        self.date_source: DateSource | None = None
        # self.dtypes = {'FLX_ANN_MOI': np.dtype('uint32'), 'ORG_CLE_REG': np.dtype('int16'), 'AGE_BEN_SNDS': np.dtype('int16'), 'BEN_RES_REG': np.dtype('int16'), 'BEN_CMU_TOP': np.dtype('int16'), 'BEN_QLT_COD': np.dtype('int16'), 'BEN_SEX_COD': np.dtype('int16'), 'DDP_SPE_COD': np.dtype('int16'), 'ETE_CAT_SNDS': np.dtype('int16'), 'ETE_REG_COD': np.dtype('int16'), 'ETE_TYP_SNDS': np.dtype('int16'), 'ETP_REG_COD': np.dtype('int16'), 'ETP_CAT_SNDS': np.dtype('int16'), 'MDT_TYP_COD': np.dtype('int16'), 'MFT_COD': np.dtype('int16'), 'PRS_FJH_TYP': np.dtype('int16'), 'PRS_ACT_COG': np.dtype('float32'), 'PRS_ACT_NBR': np.dtype('int64'), 'PRS_ACT_QTE': np.dtype('int16'), 'PRS_DEP_MNT': np.dtype('int16'), 'PRS_PAI_MNT': np.dtype('float32'), 'PRS_REM_BSE': np.dtype('float32'), 'PRS_REM_MNT': np.dtype('float32'), 'FLT_ACT_COG': np.dtype('float32'), 'FLT_ACT_NBR': np.dtype('int16'), 'FLT_ACT_QTE': np.dtype('int16'), 'FLT_PAI_MNT': np.dtype('float32'), 'FLT_DEP_MNT': np.dtype('int16'), 'FLT_REM_MNT': np.dtype('float32'), 'SOI_ANN': np.dtype('int16'), 'SOI_MOI': np.dtype('int16'), 'ASU_NAT': np.dtype('int16'), 'ATT_NAT': np.dtype('int16'), 'CPL_COD': np.dtype('int16'), 'CPT_ENV_TYP': np.dtype('int16'), 'DRG_AFF_NAT': np.dtype('int16'), 'ETE_IND_TAA': np.dtype('int16'), 'EXO_MTF': np.dtype('int16'), 'MTM_NAT': np.dtype('int16'), 'PRS_NAT': np.dtype('int16'), 'PRS_PPU_SEC': np.dtype('int16'), 'PRS_REM_TAU': np.dtype('int16'), 'PRS_REM_TYP': np.dtype('int16'), 'PRS_PDS_QCP': np.dtype('int16'), 'EXE_INS_REG': np.dtype('int16'), 'PSE_ACT_SNDS': np.dtype('int16'), 'PSE_ACT_CAT': np.dtype('int16'), 'PSE_SPE_SNDS': np.dtype('int16'), 'PSE_STJ_SNDS': np.dtype('int16'), 'PRE_INS_REG': np.dtype('int16'), 'PSP_ACT_SNDS': np.dtype('int16'), 'PSP_ACT_CAT': np.dtype('int16'), 'PSP_SPE_SNDS': np.dtype('int16'), 'ETB_DCS_MCO': np.dtype('str'), 'Unnamed: 54': np.dtype('float32')}
        self.dataframe = None
    def parse_date(self, path):
        try:
            yy = int(path[-8:-6])
            mm = int(path[-6:-4])
            self.date_source = DateSource(annee=yy, mois=mm)
        except IndexError:
            print("ERROR: file must have date like this: AYYYYMM.csv")
            quit(1)

    def check_date(self, path):
        self.parse_date(path)
        db_date = self.context.session.query(DateSource).get(self.date_source.id)
        if db_date is None:
            print(f"Added date {self.date_source}")
            self.context.session.add(self.date_source)
            self.context.session.commit()
        else:
            self.date_source = db_date

    def read_csv(self, path: str):
        self.dataframe = dd.read_csv(path, sep=";", low_memory=False, assume_missing=True) # , dtype=self.dtypes)
        self.dataframe.columns = self.dataframe.columns.str.strip().str.lower()
        self.dataframe = self.dataframe.drop(self.dataframe.columns[-1], axis=1)

    def load(self, path: str):
        print(f"Load {path}")
        self.check_date(path)
        self.read_csv(path)
        self.dataframe["flx_ann_moi"] = (self.dataframe["flx_ann_moi"] - 200000).astype(np.uint16)
        # print(self.dataframe)
        # print(self.dataframe.dtypes.to_dict())

    def commit(self):
        print("Deleting old values")
        try:
            conn = psycopg2.connect(config.connection_string)
            sql = f"delete from damir where {("FLX_ANN_MOI".lower())}={self.date_source.id}"
            with conn.cursor() as cur:
                cur.execute(sql)
            conn.commit()
            conn.close()
        except:
            pass
        print("Committing")
        self.dataframe.to_sql("damir", config.connection_string, chunksize=100, if_exists="append", index=False, dtype={'etb_dcs_mco': sqlalchemy.types.CHAR(length=1)}) # index_label="id"
        print("Committed")
        # 7968MB pour 38758177 rows
        # 96Go par an


if __name__ == '__main__':
    art.tprint(config.name, "big")
    print("Open DAMIR Parser")
    print("=================")
    print(f"V{config.version}")
    print(config.copyright)
    print()
    parser = argparse.ArgumentParser(description="Open DAMIR Parser")
    parser.add_argument("path", help="Directory path")
    parser.add_argument("-e", "--echo", help="Sql Alchemy echo", action="store_true")
    args = parser.parse_args()
    context = Context()
    context.create(echo=args.echo)
    db_size = context.db_size()
    print(f"Database {context.db_name}: {db_size:.0f} MB")
    dp = DamirParser(context)
    dp.load(args.path)
    dp.commit()
    new_db_size = context.db_size()
    print(f"Database {context.db_name}: {new_db_size:.0f} MB")
    print(f"Database grows: {new_db_size - db_size:.0f} MB ({((new_db_size - db_size) / db_size) * 100:.1f}%)")

    # data/damir/A202401