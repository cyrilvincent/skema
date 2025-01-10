from typing import Dict, Tuple
from sqlalchemy.orm import joinedload
from ps_parser import PSParser
from sqlentities import *
import argparse
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
        self.nb_warning = 0
        self.last_warning = ""

    def load_cache(self):
        print("Making cache")
        l: List[Cabinet] = self.context.session.query(Cabinet).all()
        for c in l:
            self.cabinets[c.key] = c
            self.nb_ram += 1
        l = self.context.session.query(Dept).all()
        for d in l:
            self.depts[d.num] = d
            self.depts_int[d.id] = d
            self.nb_ram += 2
        l: List[PS] = self.context.session.query(PS) \
            .options(joinedload(PS.ps_cabinet_date_sources).joinedload(PSCabinetDateSource.cabinet)) \
            .all()
            # .options(joinedload(PS.tarifs).joinedload(Tarif.date_sources.any(DateSource.id == self.date_source.id))) \
        for e in l:
            self.entities[e.key] = e
            self.nb_ram += 1
        l: List[Profession] = self.context.session.query(Profession).all()
        for p in l:
            self.professions[p.id] = p
            self.nb_ram += 1
        l: List[ModeExercice] = self.context.session.query(ModeExercice).all()
        for m in l:
            self.mode_exercices[m.id] = m
            self.nb_ram += 1
        l: List[Nature] = self.context.session.query(Nature).all()
        for n in l:
            self.natures[n.id] = n
            self.nb_ram += 1
        l: List[Convention] = self.context.session.query(Convention).all()
        for c in l:
            self.conventions[c.code] = c
            self.nb_ram += 1
        l: List[FamilleActe] = self.context.session.query(FamilleActe).all()
        for f in l:
            self.famille_actes[f.id] = f
            self.nb_ram += 1
        self.load_cache_inpp()
        print(f"{self.nb_ram:.0f} objects in cache")
        self.load_cache_tarif()
        print(f"{self.nb_ram:.0f} objects in cache")

    def load_cache_tarif(self):
        print("Making cache level 3, need a lot of RAM (>= 32Gb)")
        ds_back = self.datesource_back()
        l: List[Tarif] = self.context.session.query(Tarif) \
            .options(joinedload(Tarif.date_sources)) \
            .filter(Tarif.date_sources.any((DateSource.id >= ds_back) & (DateSource.id <= self.date_source.id)))
        print(f"{self.nb_ram + 1:.0f} objects in cache")
        for t in l:
            self.nb_ram += 1
            self.tarifs[t.key] = t
            if self.nb_ram % 100000 == 0:
                print(f"{self.nb_ram:.0f} objects in cache")
        if len(self.tarifs) == 0 and self.date_source.id > 1200 and self.date_source.id != 2009:
            print("Warning: No previous tarif found in db")
            input("CTRL+C to stop, enter to continue")

    def datesource_back(self) -> int:
        if self.date_source.annee < 20:
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
            ps.genre = self.get_nullable(row[0])
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
            t.nature = self.natures[int(row[12])] if row[12] != '' else self.natures[0]
            t.convention = self.conventions[row[13].upper()]
            t.option_contrat = self.get_nullable_boolean(row[14])
            t.vitale = self.get_nullable_boolean(row[15])
            t.code = row[16]
            if row[17] != '':
                t.famille_acte = self.famille_actes[int(row[17])]
            t.montant = self.get_nullable_float(row[18])
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

    def create_update_tarif(self, e: PS, c: Cabinet, row) -> Tarif:
        t = self.tarif_mapper(row)
        key = list(t.key)
        key[0] = e.id
        key[-1] = c.id
        key = tuple(key)
        if key in self.tarifs:
            t = self.tarifs[key]
            self.nb_existing_entity += 1
        else:
            self.nb_tarif += 1 # Si nb tarif augmente > mettre ce point d'arrêt
            t.cabinet = c
            e.tarifs.append(t)
            self.tarifs[key] = t # Bug line missing
        if self.date_source not in t.date_sources:
            t.date_sources.append(self.date_source)
        return t

    def parse_row(self, row):
        dept = self.get_dept_from_cp(row[7])
        if dept in self.depts_int:
            e = self.mapper(row)
            a = self.create_update_adresse_raw(row)
            n = self.create_update_norm(a)
            p = self.profession_mapper(row)
            inpp, _ = self.match_inpp(e, p, n)
            if inpp is not None:
                e.key = inpp
            try:
                e = self.entities[e.key]
                c = self.cabinet_mapper(row)
                c = self.cabinets[c.key]
                t = self.create_update_tarif(e, c, row)
            except KeyError:
                if e.key != self.last_warning:
                    self.last_warning = e.key
                    print(f"Warning {e.key}")
                    self.nb_warning += 1
            self.context.session.commit()
        else:
            self.nb_out_dept += 1


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
    print(f"Database {context.db_name}: {db_size:.0f} Mb")
    psp = PSTarifParser(context)
    psp.load(args.path, encoding=None)
    print(f"New tarif: {psp.nb_tarif}")
    print(f"Existing tarif: {psp.nb_existing_entity} ({psp.nb_tarif + psp.nb_existing_entity})")
    print(f"Dept >95 tarif: {psp.nb_out_dept} ({psp.nb_tarif + psp.nb_existing_entity + psp.nb_out_dept})")
    print(f"Nb warning: {psp.nb_warning}")
    new_db_size = context.db_size()
    print(f"Database {context.db_name}: {new_db_size:.0f} Mb")
    print(f"Database grows: {new_db_size - db_size:.0f} Mb ({((new_db_size - db_size) / db_size) * 100:.1f}%)")

    # data/ps/pediatres-small-00-00.csv -e
    # data/ps/ps-tarifs-small-00-00.csv -e
    # data/ps/ps-tarifs-21-03.csv
    # "data/UFC/ps-tarifs-UFC Santé, Pédiatres 2016 v1-3-12-00.csv"
    # data/SanteSpecialite/ps-tarifs-Santé_Spécialité_1_Gynécologues_201306_v0-97-13-00.csv

    # INPP 87%, 95% pour 2112

    # select count(*) from ps p
    # join tarif t on t.ps_id =p.id
    # join tarif_date_source tds on tds.tarif_id=t.id
    # and tds.date_source_id = 2106
    #
    #
    # select count(*) from ps p
    # join tarif t on t.ps_id =p.id
    # join tarif_date_source tds on tds.tarif_id=t.id
    # join cabinet c on c.id = t.cabinet_id
    # and tds.date_source_id = 2107
    #
    #
    # select *, c.* from ps p
    # join ps_cabinet_date_source pcds on pcds.ps_id = p.id
    # join cabinet c on c.id = pcds.cabinet_id
    # where pcds.date_source_id = 2107
    #
    # select count(*) from ps p
    # join ps_cabinet_date_source pcds on pcds.ps_id = p.id
    # join cabinet c on c.id = pcds.cabinet_id
    # join tarif t on t.cabinet_id = c.id
    # join tarif_date_source tds on tds.tarif_id = t.id
    # where pcds.date_source_id = 2106
    # and tds.date_source_id = 2106
    # and t.ps_id =p.id
    #
    # select count(*) from tarif t
    # join tarif_date_source tds on tds.tarif_id = t.id
    # join ps p on p.id = t.ps_id
    # where tds.date_source_id = 2106
    #
    # select count(*) from tarif t
    # join tarif_date_source tds on tds.tarif_id = t.id
    # join ps p on p.id = t.ps_id
    # join cabinet c on c.id = t.cabinet_id
    # where tds.date_source_id = 2106
