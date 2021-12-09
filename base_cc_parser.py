import art
import config
import pandas
from sqlalchemy import create_engine

from sqlentities import Context


class BaseCCParser:

    def __init__(self):
        pass

    def load(self):
        file17 = "data/insee_villes/base_cc_17.xls"
        file20 = "data/insee_villes/base_cc_20.xlsx"
        print(f"Load {file17}")
        df17_com = pandas.read_excel(file17, index_col="CODGEO")
        engine = create_engine(config.connection_string, echo=False)
        with engine.begin() as connection:
            df17_com.to_sql("basecc17_com", con=connection)
        df17_arm = pandas.read_excel(file17, 1, index_col="CODGEO")
        engine = create_engine(config.connection_string, echo=False)
        with engine.begin() as connection:
            df17_arm.to_sql("basecc17_arm", con=connection)
        print(f"Load {file20}")
        df20_com = pandas.read_excel(file20, index_col="CODGEO")
        engine = create_engine(config.connection_string, echo=False)
        with engine.begin() as connection:
            df20_com.to_sql("basecc20_com", con=connection)
        df20_arm = pandas.read_excel(file20, 1, index_col="CODGEO")
        engine = create_engine(config.connection_string, echo=False)
        with engine.begin() as connection:
            df20_arm.to_sql("basecc20_arm", con=connection)


if __name__ == '__main__':
    art.tprint(config.name, "big")
    print("BASE_CC Parser")
    print("==============")
    print(f"V{config.version}")
    print(config.copyright)
    print()
    p = BaseCCParser()
    p.load()

