import art
import config
import pandas
from sqlalchemy import create_engine


class BaseCCParser:

    def load(self):
        file17 = "data/insee_villes/base_cc_17.xls"
        file20 = "data/insee_villes/base_cc_20.xlsx"
        print(f"Load {file17}")
        df17_com = pandas.read_excel(file17, index_col="CODGEO")
        df17_com["is_com"] = True
        engine = create_engine(config.connection_string, echo=False)
        with engine.begin() as connection:
            df17_com.to_sql("basecc17", con=connection, if_exists="replace")
        df17_arm = pandas.read_excel(file17, 1, index_col="CODGEO")
        df17_arm["is_com"] = False
        engine = create_engine(config.connection_string, echo=False)
        with engine.begin() as connection:
            df17_arm.to_sql("basecc17", con=connection, if_exists="append")

        print(f"Load {file20}")
        df20_com = pandas.read_excel(file20, index_col="CODGEO")
        df20_com["is_com"] = True
        engine = create_engine(config.connection_string, echo=False)
        with engine.begin() as connection:
            df20_com.to_sql("basecc20", con=connection, if_exists="replace")
        df20_arm = pandas.read_excel(file20, 1, index_col="CODGEO")
        df20_arm["is_com"] = False
        engine = create_engine(config.connection_string, echo=False)
        with engine.begin() as connection:
            df20_arm.to_sql("basecc20", con=connection, if_exists="append")


if __name__ == '__main__':
    art.tprint(config.name, "big")
    print("BASE_CC Parser")
    print("==============")
    print(f"V{config.version}")
    print(config.copyright)
    print()
    p = BaseCCParser()
    p.load()
