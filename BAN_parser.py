from sqlentities import Context, Dept, BAN
import csv
import config
import art
import unidecode
import time
import os

time0 = time.perf_counter()


class AdresseParser:

    def __init__(self):
        self.numrow = 0
        self.nbfile = 0
        self.nbadresse = 0
        self.set = set()
        self.set = set()

    def normalize(self, s: str):
        s = unidecode.unidecode(s.upper()).replace("'", " ").replace("-", " ").replace("/", " ").replace(".", "")
        s = s.replace("ARRONDISSEMENT", "")
        if s.endswith("(LE)"):
            s = "LE "+s[:-4]
        elif s.endswith("(LA)"):
            s = "LA "+s[:-4]
        elif s.endswith("(L)"):
            s = "L "+s[:-3]
        s = " " + s
        s = s.replace(" CH ", " CHEMIN ").replace(" AV ", " AVENUE ").replace(" PL ", " PLACE ")
        s = s.replace(" BD ", " BOULEVARD ").replace(" IMP ", " IMPASSE ").replace(" ST ", " SAINT ")
        s = s.replace(" ST ", " SAINT ").replace(" STE ", " SAINTE ").replace(" RT ", " ROUTE ")
        s = s.replace(" GAL ", " GENERAL ").replace(" R ", " RUE ").replace(" RTE ", " ROUTE ")
        return s.strip()

    def make_cache(self, dept, session):
        print("Making cache ...")
        self.set = set()
        bans = session.query(BAN).filter(BAN.dept_id == dept)
        for ban in bans:
            self.set.add(ban.adresse_id)

    def test_file(self, path):
        i = 0
        with open(path, encoding="utf8") as f:
            for _ in f:
                i += 1
        return i

    def load(self, path: str, dept_num: int):
        print(f"Load {path}")
        context = Context()
        context.create()
        self.make_cache(dept_num, context.session)
        dept = context.session.query(Dept).get(dept_num)
        self.numrow = 0
        nb = self.test_file(path)
        with open(path, encoding="utf8") as f:
            self.nbfile += 1
            reader = csv.DictReader(f, delimiter=';')
            for row in reader:
                self.nbadresse += 1
                self.numrow += 1
                e = BAN()
                e.adresse_id = row["id"][:50]
                if e.adresse_id not in self.set:
                    try:
                        e.numero = int(row["numero"])
                        e.rep = row["rep"][:50] if row["rep"] != "" else None
                        e.nom_voie = self.normalize(row["nom_voie"])
                        e.code_postal = int(row["code_postal"])
                        e.code_insee = row["code_insee"]
                        e.nom_commune = self.normalize(row["nom_commune"])
                        e.nom_ancienne_commune = self.normalize(row["nom_ancienne_commune"])
                        if e.nom_ancienne_commune == "":
                            e.nom_ancienne_commune = None
                        e.lon = float(row["lon"])
                        e.lat = float(row["lat"])
                        e.libelle_acheminement = self.normalize(row["libelle_acheminement"])
                        if e.libelle_acheminement == e.nom_commune or e.libelle_acheminement == e.nom_ancienne_commune \
                                or e.libelle_acheminement == "":
                            e.libelle_acheminement = None
                        e.nom_afnor = self.normalize(row["nom_afnor"])
                        if e.nom_afnor == e.nom_voie or e.nom_afnor == "":
                            e.nom_afnor = None
                        e.dept = dept
                        e.is_lieu_dit = False
                        context.session.add(e)
                        context.session.commit()
                        self.set.add(e.adresse_id)
                    except Exception as ex:
                        print(f"Error row {self.numrow}: {ex}")
                if self.numrow % 10000 == 0:
                    print(f"Found {self.nbadresse} adresses {(self.numrow/nb)*100:.1f}%")
        print(f"Found {self.nbfile} files and {self.nbadresse} adresses in {int(time.perf_counter() - time0)}s")

    def load_lieuxdits(self, path: str, dept_num: int):
        print(f"Load {path}")
        context = Context()
        context.create()
        self.nbfile += 1
        dept = context.session.query(Dept).get(dept_num)
        self.numrow = 0
        with open(path, encoding="utf8") as f:
            reader = csv.DictReader(f, delimiter=';')
            for row in reader:
                self.numrow += 1
                self.nbadresse += 1
                e = BAN()
                e.adresse_id = row["id"]
                if e.adresse_id not in self.set:
                    try:
                        e.nom_voie = self.normalize(row["nom_lieu_dit"])
                        e.code_postal = int(row["code_postal"])
                        e.code_insee = row["code_insee"]
                        e.nom_commune = self.normalize(row["nom_commune"])
                        e.nom_ancienne_commune = self.normalize(row["nom_ancienne_commune"])
                        if e.nom_ancienne_commune == "":
                            e.nom_ancienne_commune = None
                        try:
                            e.lon = float(row["lon"])
                            e.lat = float(row["lat"])
                        except ValueError:
                            e.lon = e.lat = 0
                        e.dept = dept
                        e.is_lieu_dit = True
                        context.session.add(e)
                        context.session.commit()
                        self.set.add(e.adresse_id)
                    except Exception as ex:
                        print(f"Error row {self.numrow}: {ex}")
        print(f"Found {self.nbfile} files and {self.nbadresse} addresses in {int(time.perf_counter() - time0)}s")

    def scan(self):
        print(f"Scan {config.adresse_path}")
        for item in os.listdir(config.adresse_path):
            if item.endswith(".csv") and item.startswith("adresses-"):
                dept = item[9:11].replace("A", "01").replace("B", "02")
                dept = int(dept)
                if 1 <= dept <= 95 or dept == 201 or dept == 202:
                    path = f"{config.adresse_path}/{item}"
                    self.load(path, dept)
                    path = path.replace('adresses-', 'lieux-dits-').replace('.csv', '-beta.csv')
                    self.load_lieuxdits(path, dept)
                else:
                    print(f"Skipping {dept}")


if __name__ == '__main__':
    art.tprint(config.name, "big")
    print("Sql BAN")
    print("=======")
    print(f"V{config.version}")
    print(config.copyright)
    print()
    time0 = time.perf_counter()
    parser = AdresseParser()
    parser.scan()
