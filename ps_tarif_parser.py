from typing import Dict, List, Tuple, Optional

from sqlalchemy.orm import joinedload

from ps_parser import PSParser
from sqlentities import Context, Cabinet, PS, AdresseRaw, AdresseNorm, PSCabinetDateSource, Tarif, DateSource, \
    Profession, ModeExercice, Nature, Convention, FamilleActe, Dept
from etab_parser import BaseParser, time0
import argparse
import time
import art
import config


class PSTarifParser(PSParser):

    def __init__(self, context):
        super().__init__(context)
        self.nb_tarif = 0
        self.tarifs: Dict[Tuple, Tarif] = {}
        self.professions: Dict[int, Profession] = {}
        self.mode_exercices: Dict[int, ModeExercice] = {}
        self.natures: Dict[int, Nature] = {}
        self.conventions: Dict[str, Convention] = {}
        self.famille_actes: Dict[int, FamilleActe] = {}

    def load_cache(self):
        print("Making cache")
        l: List[Cabinet] = self.context.session.query(Cabinet).all()
        for c in l:
            self.cabinets[c.key] = c
        l = self.context.session.query(Dept).all()
        for d in l:
            self.depts[d.num] = d
            self.depts_int[d.id] = d
        l: List[PS] = self.context.session.query(PS) \
            .options(joinedload(PS.ps_cabinet_date_sources).joinedload(PSCabinetDateSource.cabinet)).all()
        for e in l:
            self.entities[e.key] = e
        l: List[Profession] = self.context.session.query(Profession).all()
        for p in l:
            self.professions[p.id] = p
        l: List[ModeExercice] = self.context.session.query(ModeExercice).all()
        for m in l:
            self.mode_exercices[m.id] = m
        l: List[Nature] = self.context.session.query(Nature).all()
        for n in l:
            self.natures[n.id] = n
        l: List[Convention] = self.context.session.query(Convention).all()
        for c in l:
            self.conventions[c.code] = c
        l: List[FamilleActe] = self.context.session.query(FamilleActe).all()
        for f in l:
            self.famille_actes[f.id] = f
        self.load_cache_inpp()
        self.load_cache_tarif()

    def load_cache_tarif(self):
        print("Making cache level 3, need a lot of RAM")
        ds_back = self.datesource_back()
        l: List[Tarif] = self.context.session.query(Tarif) \
            .options(joinedload(Tarif.date_sources)) \
            .filter(Tarif.date_sources.any((DateSource.id >= ds_back) & (DateSource.id <= self.date_source.id)))  # TODO non testé
        for t in l:
            self.tarifs[t.key] = t

    def datesource_back(self) -> int:
        if self.date_source.year < 20:
            year = month = 0
        else:
            year, month = self.date_source.annee, self.date_source.mois - config.tarif_datesource_back
            if month <= 0:
                month += 12
                year -= 1
        return year * 100 + month

    def get_boolean(self, s: str) -> bool:
        if s == "O":
            return True
        if s == "N":
            return False
        print(f"ERROR Boolean row {self.row_num} {s}")
        quit(6)

    def get_nullable_boolean(self, s: str) -> Optional[bool]:
        return None if s == "" else self.get_boolean(s)

    def get_nullable_float(self, s: str) -> Optional[float]:
        return None if s == "" else float(s)

    def mapper(self, row) -> PS:
        ps = PS()
        try:
            ps.genre = row[0]
            ps.nom = row[1]
            ps.prenom = row[2]
            ps.key = f"{ps.nom}_{ps.prenom}_{row[7]}".replace(" ", "_")[:255]
        except Exception as ex:
            print(f"ERROR PS row {self.row_num} {ps}\n{ex}")
            quit(1)
        return ps

    def tarif_mapper(self, row) -> Tarif:
        t = Tarif()
        try:
            if row[10] != '':
                t.profession = self.professions[int(row[10])]
            if row[11] != '':
                t.mode_exercice = self.mode_exercices[int(row[11])]
            t.nature = self.natures[int(row[12])]
            t.convention = self.conventions[row[13].upper()]
            t.option_contrat = self.get_nullable_boolean(row[14])
            t.vitale = self.get_nullable_boolean(row[15])
            t.code = row[16]
            if row[17] != '':
                t.famille_acte = self.famille_actes[int(row[17])]
            t.montant = float(row[18])
            t.borne_inf = self.get_nullable_float(row[19])
            t.borne_sup = self.get_nullable_float(row[20])
            t.montant2 = self.get_nullable_float(row[21])
            t.borne_inf2 = self.get_nullable_float(row[22])
            t.borne_sup2 = self.get_nullable_float(row[23])
            t.montant_imagerie = self.get_nullable_float(row[24])
            t.borne_inf_imagerie = self.get_nullable_float(row[25])
            t.borne_sup_imagerie = self.get_nullable_float(row[26])
            t.montant_anesthesie = self.get_nullable_float(row[27])
            t.borne_inf_anesthesie = self.get_nullable_float(row[28])
            t.borne_sup_anesthesie = self.get_nullable_float(row[29])
            t.montant_cec = self.get_nullable_float(row[30])
            t.borne_inf_cec = self.get_nullable_float(row[31])
            t.borne_sup_cec = self.get_nullable_float(row[32])
        except Exception as ex:
            print(f"ERROR tarif row {self.row_num} {t}\n{ex}\n{row}")
            quit(3)
        return t

    def create_update_tarif(self, e: PS, c: Cabinet, row):
        t = self.tarif_mapper(row)
        key = list(t.key)
        key[0] = e.id
        key = tuple(key)
        if key in self.tarifs:
            t = self.tarifs[key]
        else:
            self.nb_tarif += 1
            # self.tarifs[key] = t # inutile dans ce cas précis
            t.cabinet = c
            e.tarifs.append(t)
        if self.date_source not in t.date_sources:
            t.date_sources.append(self.date_source)

    def parse_row(self, row):
        dept = self.get_dept_from_cp(row[7])
        if dept in self.depts_int:
            e = self.mapper(row)
            a = self.create_update_adresse_raw(row)
            n = self.create_update_norm(a)
            inpp = self.match_inpp(e, n)
            if inpp is not None:
                e.key = inpp
            e = self.entities[e.key]
            c = self.cabinet_mapper(row)
            c = self.cabinets[c.key]
            if c is None:
                print(f"ERROR cabinet row {self.row_num} {row}")
                quit(3)
            self.create_update_tarif(e, c, row)
            self.context.session.commit()


if __name__ == '__main__':
    art.tprint(config.name, "big")
    print("PS Tarif Parser")
    print("===============")
    print(f"V{config.version}")
    print(config.copyright)
    print()
    parser = argparse.ArgumentParser(description="PS Tarif Parser")
    parser.add_argument("path", help="Path")
    parser.add_argument("-e", "--echo", help="Sql Alchemy echo", action="store_true")
    args = parser.parse_args()
    context = Context()
    context.create(echo=args.echo, expire_on_commit=False)
    db_size = context.db_size()
    print(f"Database {context.db_name}: {db_size:.0f} Mo")
    psp = PSTarifParser(context)
    psp.load(args.path, encoding=None)
    print(f"New tarif: {psp.nb_tarif}")
    new_db_size = context.db_size()
    print(f"Database {context.db_name}: {new_db_size:.0f} Mo")
    print(f"Database grows: {new_db_size - db_size:.0f} Mo ({((new_db_size - db_size) / db_size) * 100:.1f}%)")
    print(f"Parse {psp.row_num} rows in {time.perf_counter() - time0:.0f} s")

    # data/ps/ps-tarifs-small-00-00.csv -e
    # data/ps/ps-tarifs-21-03.csv
    # "data/UFC/ps-tarifs-UFC Santé, Pédiatres 2016 v1-3-16-00.csv"
    # data/SanteSpecialite/ps-tarifs-Santé_Spécialité_1_Gynécologues_201306_v0-97-13-00.csv
