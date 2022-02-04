from typing import Optional, List, Tuple
from sqlalchemy.orm import joinedload
from base_parser import BaseParser
from sqlentities import Context, DateSource, Etablissement, EtablissementType, AdresseRaw, AdresseNorm
import argparse
import time
import art
import config

time0 = time.perf_counter()


class EtalabParser(BaseParser):

    def __init__(self, context):
        super().__init__(context)
        self.nb_new_lon_lat = 0
        self.etablissement_types = List[EtablissementType]

    def load_cache(self):
        super().load_cache()
        l = self.context.session.query(Etablissement).options(joinedload(Etablissement.adresse_raw)
                                                              .joinedload(AdresseRaw.adresse_norm)) \
            .options(joinedload(Etablissement.date_sources)).all()
        for e in l:
            self.entities[e.nofinesset] = e
        print(f"{self.nb_ram} objects in cache")

    def parse_date(self, path):
        try:
            yy = int(path[-10:-8])
            mm = int(path[-8:-6])
            self.date_source = DateSource(annee=yy, mois=mm)
        except IndexError:
            print("ERROR: file must have date like this: file_20211200.csv")

    def mapper(self, row) -> Etablissement:
        e = Etablissement()
        try:
            e.nofinesset = row["nofinesset"]
            e.nofinessej = row["nofinessej"]
            e.rs = row["rs"]
            e.rslongue = row["rslongue"]
            e.complrs = self.get_nullable(row["complrs"])
            e.mft = self.get_nullable(row["mft"])
            e.sph = self.get_nullable_int(row["sph"])
            e.categetab = self.get_nullable_int(row["categetab"])
            e.categretab = self.get_nullable_int(row["categretab"])
            e.telephone = self.get_nullable(row["telephone"])
            e.telecopie = self.get_nullable(row["telecopie"])
            e.siret = self.get_nullable(row["siret"])
            e.dateautor = self.get_nullable(row["dateautor"])
            e.dateouvert = self.get_nullable(row["dateouvert"])
            e.datemaj = self.get_nullable(row["datemaj"])
            e.cog = self.get_nullable(row["cog"]) if "cog" in row else None
            e.codeape = self.get_nullable(row["codeape"]) if "codeape" in row else None
        except Exception as ex:
            print(f"ERROR Etablissement row {self.row_num} {e}\n{ex}\n{row}")
            quit(1)
        return e

    def typevoie(self, s):
        s = s.strip()
        if s is None or s == "":
            return None
        dico = {"RTE": "ROUTE", "R": "RUE", "AV": "AVENUE", "CHE": "CHEMIN", "BD": "BOULEVARD", "PL": "PLACE"}
        if s in dico:
            return dico[s]
        return s

    def adresse_raw_mapper(self, row) -> AdresseRaw:
        a = AdresseRaw()
        try:
            num = self.get_nullable(row["numvoie"])
            type = self.typevoie(row["typvoie"])
            a.adresse3 = self.get_nullable(row["voie"])
            if a.adresse3 is not None and type is not None:
                a.adresse3 = f"{type} {a.adresse3}"
            if a.adresse3 is not None and num is not None:
                a.adresse3 = f"{num} {a.adresse3}"
            a.adresse4 = self.get_nullable(row["lieuditbp"])
            a.adresse2 = self.get_nullable(row["compvoie"])
            a.cp = int(row["codepostal"])
            a.dept = self.depts[row["departement"]]
            a.commune = row["libelle_routage"]
        except Exception as ex:
            print(f"ERROR row {self.row_num} {a}\n{ex}\n{row}")
            quit(1)
        return a

    def lon_lat_mapper(self, row) -> Tuple[Optional[float], Optional[float]]:
        try:
            if "coordx" in row and row["coordx"] != "" and row["coordy"] != "":
                x = float(row["coordx"].replace(",", ""))
                y = float(row["coordy"].replace(",", ""))
                if x == 0 or y == 0:
                    return None, None
                lon, lat = self.convert_lambert93_lon_lat(x, y)
                return lon, lat
            return None, None
        except Exception as ex:
            print(f"ERROR row {self.row_num} bad lon lat\n{ex}\n{row}")
            quit(1)

    def create_update_adresse_raw(self, e: Etablissement, row):
        a = self.adresse_raw_mapper(row)
        if a.key not in self.adresse_raws:
            self.adresse_raws[a.key] = a
            self.nb_new_adresse += 1
        else:
            a = self.adresse_raws[a.key]
        if e.adresse_raw is None or e.adresse_raw.id != a.id:
            e.adresse_raw = a

    def normalize(self, a: AdresseRaw) -> AdresseNorm:
        n = AdresseNorm()
        if a.adresse3 is not None:
            n.numero, n.rue1 = self.split_num(a.adresse3)
            n.rue1 = self.normalize_street(n.rue1)
        if a.adresse4 is not None:
            n.rue2 = self.normalize_street(a.adresse4)
        elif a.adresse2 is not None:
            n.rue2 = self.normalize_street(a.adresse2)
        n.cp = a.cp
        n.commune = self.normalize_commune(a.commune)
        n.dept = a.dept
        return n

    def create_update_norm(self, a: AdresseRaw):
        n = self.normalize(a)
        if n.key in self.adresse_norms:
            n = self.adresse_norms[n.key]
        else:
            self.adresse_norms[n.key] = n
            self.context.session.add(n)
            self.nb_new_norm += 1
        if a.adresse_norm is None:
            a.adresse_norm = n
        else:
            same = a.adresse_norm.equals(n)
            if not same:
                a.adresse_norm = n

    def create_update_lon_lat(self, row, n: AdresseNorm):
        if n.source_id is None or n.source_id != 3:
            lon, lat = self.lon_lat_mapper(row)
            if lon is not None and lat is not None:
                if 60 > lat > 35 and 20 > lon > -20:
                    n.lat = lat
                    n.lon = lon
                    n.source = self.sources[3]
                    n.score = 1
                    self.nb_new_lon_lat += 1

    def parse_row(self, row):
        dept = self.get_dept_from_cp(row["codepostal"])
        if dept in self.depts_int:
            e = self.mapper(row)
            if e.nofinesset in self.entities:
                same = e.equals(self.entities[e.nofinesset])
                if not same:
                    self.pseudo_clone(e, self.entities[e.nofinesset])
                    self.nb_update_entity += 1
                e = self.entities[e.nofinesset]
            else:
                self.entities[e.nofinesset] = e
                self.nb_new_entity += 1
                self.context.session.add(e)
            self.create_update_adresse_raw(e, row)
            self.create_update_norm(e.adresse_raw)
            self.create_update_lon_lat(row, e.adresse_raw.adresse_norm)
            if self.date_source.id not in [ds.id for ds in e.date_sources]:
                e.date_sources.append(self.date_source)
            self.context.session.commit()


if __name__ == '__main__':
    art.tprint(config.name, "big")
    print("Etalab Parser")
    print("=============")
    print(f"V{config.version}")
    print(config.copyright)
    print()
    parser = argparse.ArgumentParser(description="Etalab Parser")
    parser.add_argument("path", help="Path")
    parser.add_argument("-e", "--echo", help="Sql Alchemy echo", action="store_true")
    args = parser.parse_args()
    context = Context()
    context.create(echo=args.echo, expire_on_commit=False)
    db_size = context.db_size()
    print(f"Database {context.db_name}: {db_size:.0f} Mo")
    ep = EtalabParser(context)
    ep.load(args.path, header=True, encoding="ANSI")
    print(f"New etablissement: {ep.nb_new_entity}")
    print(f"Update etablissement: {ep.nb_update_entity}")
    print(f"New adresse: {ep.nb_new_adresse}")
    print(f"New adresse normalized: {ep.nb_new_norm}")
    print(f"New GPS: {ep.nb_new_lon_lat}")
    new_db_size = context.db_size()
    print(f"Database {context.db_name}: {new_db_size:.0f} Mo")
    print(f"Database grows: {new_db_size - db_size:.0f} Mo ({((new_db_size - db_size) / db_size) * 100:.1f}%)")
    print(f"Parse {ep.row_num} rows in {time.perf_counter() - time0:.0f} s")

    # data/etalab/etalab_small_20201231.csv -e
    # data/etalab/etalab_xsmall_20201231.csv -e
    # data/etalab/etalab_stock_et_20201231.csv
