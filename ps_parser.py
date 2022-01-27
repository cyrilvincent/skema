import difflib
from typing import Dict, List, Tuple, Optional, Set
from sqlalchemy.orm import joinedload
from sqlentities import Context, Cabinet, PS, AdresseRaw, AdresseNorm, PSCabinetDateSource, PAAdresse, PSMerge
from base_parser import BaseParser
import argparse
import art
import config


class PSParser(BaseParser):

    def __init__(self, context):
        super().__init__(context)
        self.nb_cabinet = 0
        self.nb_inpps = 0
        self.nb_ps_to_match = 0
        self.cabinets: Dict[str, Cabinet] = {}
        self.inpps: Dict[Tuple[str, str, int], Dict[Tuple[int, str, int, str], str]] = {}
        self.inpps_france: Dict[Tuple[str, str], Set[str]] = {}
        self.inpps_temp: Dict[Tuple[str, str, int, str, int, str], Optional[str]] = {}
        self.ps_merges: Dict[str, str] = {}

    def load_cache(self):
        super().load_cache()
        l: List[PS] = self.context.session.query(PS) \
            .options(joinedload(PS.ps_cabinet_date_sources).joinedload(PSCabinetDateSource.cabinet)).all()
        for e in l:
            self.entities[e.key] = e
            self.nb_ram += 1
        l: List[Cabinet] = self.context.session.query(Cabinet).all()
        for c in l:
            self.cabinets[c.key] = c
            self.nb_ram += 1
        l: List[PSMerge] = self.context.session.query(PSMerge).all()
        for p in l:
            self.ps_merges[p.key] = p.inpp
            self.nb_ram += 1
        self.load_cache_inpp()
        print(f"{self.nb_ram} objects in cache")

    def load_cache_inpp(self):
        print("Making cache level 2")
        session = self.context.get_session()
        pa_adresses = session.query(PAAdresse).options(joinedload(PAAdresse.personne_activites)).all()
        for a in pa_adresses:
            for pa in a.personne_activites:
                key1 = pa.nom, pa.prenom, self.get_dept_from_cp(a.cp)
                key2 = a.numero, a.rue, a.cp, a.commune
                key0 = pa.nom, pa.prenom
                if key1 not in self.inpps:
                    self.inpps[key1] = {key2: pa.inpp}
                else:
                    self.inpps[key1][key2] = pa.inpp
                if key0 not in self.inpps_france:
                    self.inpps_france[key0] = {pa.inpp}
                else:
                    self.inpps_france[key0].add(pa.inpp)
                self.nb_ram += 1
            session.expunge(a)

    def mapper(self, row) -> PS:
        ps = PS()
        try:
            ps.genre = self.get_nullable(row[0])
            ps.nom = row[1]
            ps.prenom = row[2]
            ps.key = f"{ps.nom}_{ps.prenom}_{row[7]}".replace(" ", "_")[:255]
            ps.has_inpp = False
        except Exception as ex:
            print(f"ERROR PS row {self.row_num} {ps}\n{ex}")
            quit(1)
        return ps

    def cabinet_mapper(self, row) -> Cabinet:
        c = Cabinet()
        try:
            c.nom = f"{row[1]} {row[2]}" if row[3] == '' else row[3]
            c.telephone = self.get_nullable(row[9])
            c.key = f"{c.nom}_{row[7]}_{row[5]}".replace(" ", "_")[:255]
        except Exception as ex:
            print(f"ERROR cabinet row {self.row_num} {c}\n{ex}")
            quit(2)
        return c

    def create_update_cabinet(self, e: PS, row) -> Cabinet:
        c = self.cabinet_mapper(row)
        if c.key in self.cabinets:
            c = self.cabinets[c.key]
        else:
            self.nb_cabinet += 1
            self.cabinets[c.key] = c
        keys = [pcds.key for pcds in e.ps_cabinet_date_sources]
        if (e.id, c.id, self.date_source.id) not in keys:
            pcds = PSCabinetDateSource()
            pcds.date_source = self.date_source
            pcds.cabinet = c
            e.ps_cabinet_date_sources.append(pcds)
        return c

    def adresse_raw_mapper(self, row) -> AdresseRaw:
        a = AdresseRaw()
        try:
            a.adresse2 = self.get_nullable(row[4])
            a.adresse3 = self.get_nullable(row[5])
            a.adresse4 = self.get_nullable(row[6])
            a.cp = int(row[7])
            a.commune = row[8]
            a.dept = self.depts_int[self.get_dept_from_cp(a.cp)]
        except Exception as ex:
            print(f"ERROR raw row {self.row_num} {a}\n{ex}")
            quit(4)
        return a

    def create_update_adresse_raw(self, row) -> AdresseRaw:
        a = self.adresse_raw_mapper(row)
        if a.key in self.adresse_raws:
            a = self.adresse_raws[a.key]
        else:
            self.nb_new_adresse += 1
            self.adresse_raws[a.key] = a
        # c.adresse_raw = a
        return a

    def choose_best_rue(self, a: AdresseRaw) -> int:
        if a.adresse2 is None:
            return 3
        l = ["CHEMIN", "AVENUE", "PLACE", "BOULEVARD", "IMPASSE", "ROUTE", "RUE"]
        if a.adresse3 is not None:
            num, rue = self.split_num(a.adresse3)
            if num is not None:
                return 3
            rue = self.normalize_street(rue)
            for w in l:
                if w in rue:
                    return 3
        if a.adresse2 is not None:
            num, rue = self.split_num(a.adresse2)
            if num is not None:
                return 2
            rue = self.normalize_street(rue)
            for w in l:
                if w in rue:
                    return 2
        return 3

    def normalize(self, a: AdresseRaw) -> AdresseNorm:
        n = AdresseNorm()
        n.cp = a.cp
        n.commune = self.normalize_commune(a.commune)
        n.dept = a.dept
        best = self.choose_best_rue(a)
        if best == 3 and a.adresse3 is not None:
            n.numero, n.rue1 = self.split_num(a.adresse3)
            n.rue1 = self.normalize_street(n.rue1)
            n.rue2 = self.normalize_street(a.adresse2) if a.adresse2 is not None else None
        elif best == 2 and a.adresse2 is not None:
            n.numero, n.rue1 = self.split_num(a.adresse2)
            n.rue1 = self.normalize_street(n.rue1)
            n.rue2 = self.normalize_street(a.adresse3) if a.adresse3 is not None else None
        return n

    def convert_key_to_rue_string(self, key: Tuple[Optional[int], Optional[str], int, str]) -> str:
        s = f"{key[2]} {key[3]}"
        if key[1] is not None:
            s = f"{key[1]} {s}"
        if key[0] is not None:
            s = f"{key[0]} {s}"
        return s

    def gestalt(self, s1: str, s2: str):
        sm = difflib.SequenceMatcher(None, s1, s2)
        return sm.ratio()

    def match_inpp_gestalt(self, key: Tuple[int, str, int, str],
                           dico: Dict[Tuple[int, str, int, str], str]) -> Optional[str]:
        s = self.convert_key_to_rue_string(key)
        max = 0
        inpp = None
        for k in dico.keys():
            s2 = self.convert_key_to_rue_string(k)
            score = self.gestalt(s, s2)
            if score > max:
                max = score
                inpp = dico[k]
        if max > 0.75:  # je confirme que ca ne doit pas être dans config
            return inpp
        if len(set(dico.values())) == 1:  # and max > (config.inpp_quality * 0.9):
            return inpp
        return None

    def match_rue(self, rue1: Optional[str], rue2: Optional[str]):
        if self.date_source.id == 1206 or self.date_source.id == 1306:  # SanteSpecialite
            return False
        if rue1 is None or rue2 is None:
            return True
        if rue1 == rue2:
            return True
        if rue1 is not None and rue2 is not None:
            if rue1.startswith(rue2) or rue2.startswith(rue1):
                return True
        return False

    def match_inpp(self, ps: PS, a: AdresseNorm) -> Optional[str]:
        if ps.key in self.ps_merges:
            return self.ps_merges[ps.key]
        key3 = ps.nom, ps.prenom, a.numero, a.rue1, a.cp, a.commune
        if key3 in self.inpps_temp:
            return self.inpps_temp[key3]
        self.nb_ps_to_match += 1
        # Recherche 1 nom, prenom sur toute la france avec len == 1
        key0 = ps.nom, ps.prenom
        if key0 not in self.inpps_france:
            self.inpps_temp[key3] = None
            return None
        else:
            if len(list(self.inpps_france[key0])) == 1:
                self.nb_inpps += 1
                self.inpps_temp[key3] = list(self.inpps_france[key0])[0]
                return self.inpps_temp[key3]
        key1 = ps.nom, ps.prenom, self.get_dept_from_cp(a.cp)
        if key1 not in self.inpps:
            self.inpps_temp[key3] = None
            return None
        dico = self.inpps[key1]
        key2 = a.numero, a.rue1, a.cp, a.commune
        if key2 in dico:
            self.nb_inpps += 1
            self.inpps_temp[key3] = dico[key2]
            return dico[key2]
        l = [dico[k] for k in dico.keys() if (k[2] == a.cp or k[3] == a.commune) and self.match_rue(k[1], a.rue1)]
        l = list(set(l))
        if len(l) == 1:
            self.nb_inpps += 1
            self.inpps_temp[key3] = l[0]
            return l[0]
        inpp = self.match_inpp_gestalt(key2, dico)
        if inpp is not None:
            self.nb_inpps += 1
        # else:
        #     print("No match", (self.nb_inpps / self.nb_ps_to_match) * 100, key3)
        self.inpps_temp[key3] = inpp
        return inpp

    def create_update_norm(self, a: AdresseRaw) -> AdresseNorm:
        n = self.normalize(a)
        if n.key in self.adresse_norms:
            n = self.adresse_norms[n.key]
        else:
            self.adresse_norms[n.key] = n
            self.nb_new_norm += 1
        if a.adresse_norm is None:
            a.adresse_norm = n
        else:
            same = a.adresse_norm.equals(n)
            if not same:
                a.adresse_norm = n
        return n

    def parse_row(self, row):
        dept = self.get_dept_from_cp(row[7])
        if dept in self.depts_int:
            e = self.mapper(row)
            a = self.create_update_adresse_raw(row)
            n = self.create_update_norm(a)
            inpp = self.match_inpp(e, n)
            if inpp is not None:
                e.key = inpp
                e.has_inpp = True
            if e.key in self.entities:
                same = e.equals(self.entities[e.key])
                if not same:
                    if e.genre is not None:
                        self.entities[e.key].genre = e.genre
                        self.nb_update_entity += 1
                e = self.entities[e.key]
            else:
                self.entities[e.key] = e
                self.nb_new_entity += 1
                self.context.session.add(e)
            c = self.create_update_cabinet(e, row)
            c.adresse_raw = a
            self.context.session.commit()


if __name__ == '__main__':
    art.tprint(config.name, "big")
    print("PS Parser")
    print("=========")
    print(f"V{config.version}")
    print(config.copyright)
    print()
    parser = argparse.ArgumentParser(description="PS Parser")
    parser.add_argument("path", help="Path")
    parser.add_argument("-e", "--echo", help="Sql Alchemy echo", action="store_true")
    args = parser.parse_args()
    context = Context()
    context.create(echo=args.echo, expire_on_commit=False)
    db_size = context.db_size()
    print(f"Database {context.db_name}: {db_size:.0f} Mo")
    psp = PSParser(context)
    psp.load(args.path, encoding=None)
    print(f"New PS: {psp.nb_new_entity}")
    print(f"Update PS: {psp.nb_update_entity}")
    print(f"New cabinet: {psp.nb_cabinet}")
    print(f"New adresse: {psp.nb_new_adresse}")
    print(f"New adresse normalized: {psp.nb_new_norm}")
    print(f"Matching INPP: {psp.nb_inpps}/{psp.nb_ps_to_match}: {(psp.nb_inpps / psp.nb_ps_to_match) * 100:.0f}%")
    new_db_size = context.db_size()
    print(f"Database {context.db_name}: {new_db_size:.0f} Mo")
    print(f"Database grows: {new_db_size - db_size:.0f} Mo ({((new_db_size - db_size) / db_size) * 100:.1f}%)")

    # Avant de refaire tourner valider vider la table ps_merge

    # data/ps/ps-tarifs-small-00-00.csv -e
    # data/ps/ps-tarifs-21-03.csv 88% 584s 89% 701s
    # "data/UFC/ps-tarifs-UFC Santé, Pédiatres 2016 v1-3-16-00.csv" /!\ Enlever le update genre
    # data/SanteSpecialite/ps-tarifs-Santé_Spécialité_1_Gynécologues_201306_v0-97-13-00.csv

    # select cast(data1.count1 as float)/ cast(data2.count2 as float)
    # from
    # (select count(*) as count1 from ps where has_inpp is true) data1,
    # (select count(*) as count2 from ps) data2

    # select cast(data1.count1 as float)/ cast(data2.count2 as float)
    # from
    # (select count(*) as count1 from ps, ps_cabinet_date_source
    #  	where ps_cabinet_date_source.ps_id = ps.id
    #  	and ps_cabinet_date_source.date_source_id = 2112
    #  	and has_inpp is true) data1,
    # (select count(*) as count2 from ps, ps_cabinet_date_source
    # 	where ps_cabinet_date_source.ps_id = ps.id
    #  	and ps_cabinet_date_source.date_source_id = 2112
    # ) data2
