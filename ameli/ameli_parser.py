import argparse
import art
import psycopg2
import config
import pandas as pd


class AmeliParser:

    def __init__(self, path: str):
        self.path = path
        self.specialites = {
            1: "TOTAL PSYCHIATRIE  (75, 33,17)",
            2: "02- Anesthésie-réanimation chirurgicale",
            3: "05- Dermato-vénéréologie",
            4: "08- Gastro-entérologie et hépatologie",
            5: "70- Gynécologie médicale",
            6: "15- Ophtalmologie",
            7: "12- Pédiatrie",
            8: "TOTAL RADIOLOGIE  (72, 74, 76, 06)",
            10: "01- Médecine générale",
            11: "03- Pathologie cardio-vasculaire",
            12: "04- Chirurgie générale",
            13: "42- Endocrinologie et métabolisme",
            14: "34-Gériatrie",
            15: "32- Neurologie",
            16: "11- Oto-rhino-laryngologie",
            17: "13- Pneumologie",
            18: "74- Oncologie radiothérapique",
            19: "14- Rhumatologie",
            20: "TOTAL STOMATOLOGIE  (69, 45, 18)",
            21: "24- Infirmiers",
            22: "21- Sages-femmes",
            23: "26- Masseurs-kinésithérapeutes-rééducateurs",
            24: "27- Pédicures",
            25: "28- Orthophonistes",
            27: "19- Chirurgiens-dentistes",
        }
        pd.options.display.width = None
        pd.options.display.max_colwidth = None

    def load_specialite(self, specialite: int, year: int, df: pd.DataFrame, first_col: str) -> dict[str, int]:
        select = df[df[first_col] == self.specialites[specialite]]
        metro = select[select["DEPARTEMENT"] == "TOTAL FRANCE METROPOLITAINE"]
        dom = select[select["DEPARTEMENT"] == "TOTAL OUTRE-MER"]
        return {"year": year,
                "specialite": specialite,
                "nb_metro": metro["TOTAL"].iloc[0],
                "nb_dom_tom": dom["TOTAL"].iloc[0]}

    def load_generaliste_mep(self, year: int, result: pd.DataFrame):
        sheet = "Généralistes et MEP"
        print(f"Loading {sheet}")
        df = pd.read_excel(self.path, sheet)
        result.loc[len(result)] = self.load_specialite(10, year, df, "Généralistes et compétence MEP")

    def load_dentiste(self, year: int, result: pd.DataFrame):
        sheet = "Dentistes et ODF"
        print(f"Loading {sheet}")
        df = pd.read_excel(self.path, sheet)
        result.loc[len(result)] = self.load_specialite(27, year, df, "Chirurgiens-dentistes et ODF")

    def load_specialistes(self, year: int, result: pd.DataFrame):
        sheet = "Spécialistes"
        print(f"Loading {sheet}")
        df = pd.read_excel(self.path, sheet)
        for i in list(range(1, 9)) + list(range(11, 21)):
            result.loc[len(result)] = self.load_specialite(i, year, df, sheet)

    def load_auxiliaires(self, year: int, result: pd.DataFrame):
        sheet = "Auxiliaires médicaux"
        print(f"Loading {sheet}")
        df = pd.read_excel(self.path, sheet)
        for i in [21, 23, 24, 25]:
            result.loc[len(result)] = self.load_specialite(i, year, df, sheet)

    def load_sage_femmes(self, year: int, result: pd.DataFrame):
        sheet = "Sages-femmes"
        print(f"Loading {sheet}")
        df = pd.read_excel(self.path, sheet)
        result.loc[len(result)] = self.load_specialite(22, year, df, "Sages-femmes")

    def load(self) -> pd.DataFrame:
        print(f"Loading {self.path}")
        i = self.path.rindex("20")
        year = int(self.path[i:i+4])
        result = pd.DataFrame({"year": pd.Series(dtype=int),
                               "specialite": pd.Series(dtype=int),
                               "nb_metro": pd.Series(dtype=int),
                               "nb_dom_tom": pd.Series(dtype=int)})
        self.load_generaliste_mep(year, result)
        self.load_specialistes(year, result)
        self.load_dentiste(year, result)
        self.load_sage_femmes(year, result)
        self.load_auxiliaires(year, result)
        result = result.sort_values(by=["year", "specialite"])
        return result

    def save(self, result: pd.DataFrame):
        self.delete(result)
        print("Saving")
        result.to_sql("ameli", config.connection_string, if_exists="append", index=False)

    def delete(self, result):
        print("Deleting old values")
        year = result["year"].iloc[0]
        conn = psycopg2.connect(config.connection_string)
        sql = f"delete from ameli where year={year}"
        try:
            with conn.cursor() as cur:
                cur.execute(sql)
            conn.commit()
            conn.close()
            print("Deleted")
        except:
            pass


if __name__ == '__main__':
    art.tprint(config.name, "big")
    print("Ameli Parser")
    print("============")
    print(f"V{config.version}")
    print(config.copyright)
    print()
    parser = argparse.ArgumentParser(description="Ameli Parser")
    parser.add_argument("path", help="Path")
    args = parser.parse_args()
    p = AmeliParser(args.path)
    df = p.load()
    p.save(df)


# data/ameli/2021_secteur-conventionnel-des-professionnels-de-sante-liberaux-par-departement_serie-annuelle.xls
