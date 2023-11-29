import datetime
from typing import Dict, List, Tuple, Optional
from sqlalchemy.orm import joinedload
from rpps_exercice_pro_parser import RPPSExerciceProParser
from sqlentities import Context, Dept, Personne, Coord, AdresseNorm
from base_parser import time0
import argparse
import time
import art
import config


class RPPSCoordPersonneParser(RPPSExerciceProParser):

    def __init__(self, context):
        super().__init__(context)
        self.norms: Dict[Tuple[int, int, str, str, int, str], AdresseNorm] = {}
        self.nb_new_norm = 0

    def load_cache(self):
        print("Making cache")
        l: List[Coord] = self.context.session.query(Coord)\
            .options(joinedload(Coord.adresse_norm)).all()
        for e in l:
            if e.personne_id is not None:
                self.entities[e.key] = e
                self.nb_ram += 1
        l: List[Personne] = self.context.session.query(Personne).all()
        for p in l:
            self.personnes[p.inpp] = p
            self.nb_ram += 1
        print(f"{self.nb_ram} objects in cache")
        l: List[Dept] = self.context.session.query(Dept).all()
        for d in l:
            self.depts[d.num] = d
            self.nb_ram += 1
        l: List[AdresseNorm] = self.context.session.query(AdresseNorm).all()
        for n in l:
            self.norms[n.key] = n
            self.nb_ram += 1
        print(f"{self.nb_ram} objects in cache")

    def mapper(self, row) -> Coord:
        e = Coord()
        try:
            e.inpp = row["Identification nationale PP"]
            e.complement_destinataire = self.get_nullable(row["Complément destinataire (coord. correspondance)"])
            e.complement_geo = self.get_nullable(row["Complément point géographique (coord. correspondance)"])
            e.numero = self.get_nullable(row["Numéro Voie (coord. correspondance)"])
            e.indice = self.get_nullable(row["Indice répétition voie (coord. correspondance)"])
            e.code_type_voie = self.get_nullable(row["Code type de voie (coord. correspondance)"])
            e.type_voie = self.get_nullable(row["Libellé type de voie (coord. correspondance)"])
            e.voie = self.get_nullable(row["Libellé Voie (coord. correspondance)"])
            e.mention = self.get_nullable(row["Mention distribution (coord. correspondance)"])
            e.cedex = self.get_nullable(row["Bureau cedex (coord. correspondance)"])
            e.cp = self.get_nullable(row["Code postal (coord. correspondance)"])
            e.code_commune = self.get_nullable(row["Code commune (coord. correspondance)"])
            e.commune = self.get_nullable(row["Libellé commune (coord. correspondance)"])
            if e.commune is None:
                if e.cedex is not None and len(e.cedex) > 7:
                    e.commune = e.cedex[6:]
            e.code_pays = self.get_nullable(row["Code pays (coord. correspondance)"])
            e.pays = None if e.code_pays == "99000" else self.get_nullable(row["Libellé pays (coord. correspondance)"])
            e.tel = self.get_nullable(row["Téléphone (coord. correspondance)"])
            e.tel2 = self.get_nullable(row["Téléphone 2 (coord. correspondance)"])
            e.fax = self.get_nullable(row["Télécopie (coord. correspondance)"])
            e.mail = self.get_nullable(row["Adresse e-mail (coord. correspondance)"])
            try:
                e.date_maj = self.get_nullable_date(row["Date de mise à jour (coord. correspondance)"])
                if e.date_maj is None:
                    raise ValueError()
                e.date_fin = self.get_nullable_date(row["Date de fin (coord. correspondance)"])
            except:
                try:
                    e.date_maj = self.get_nullable_date(row["Date de fin (coord. correspondance)"])
                except:
                    e.date_maj = datetime.date(1970,1,1)
                e.cp = self.get_nullable(row["Code commune (coord. correspondance)"])
                e.code_commune = self.get_nullable(row["Libellé commune (coord. correspondance)"])
                e.commune = self.get_nullable(row["Code pays (coord. correspondance)"])
                e.code_pays = self.get_nullable(row["Libellé pays (coord. correspondance)"])
            if e.numero is not None and len(e.numero) > 10:
                e.numero = None
            if e.indice is not None and len(e.indice) > 10:
                e.indice = None
            if e.code_type_voie is not None and len(e.code_type_voie) > 10:
                e.code_type_voie = None
            if e.cp is not None and len(e.cp) > 10:
                e.cp = None
            if e.code_commune is not None and len(e.code_commune) > 10:
                e.code_commune = None
            if e.code_pays is not None and len(e.code_pays) > 5:
                e.code_pays = None
            if e.date_maj is None:
                e.date_maj = datetime.date(1970, 1, 1)
        except Exception as ex:
            print(f"ERROR CoordPersonne row {self.row_num} {e}\n{ex}\n{row}")
            quit(1)
        return e

    def norm_mapper(self, e: Coord) -> Optional[AdresseNorm]:
        if e.code_pays is not None and e.code_pays != "99000":
            return None
        n = AdresseNorm()
        try:
            n.cp = int(e.cp)
        except:
            return None
        if e.commune is None:
            return None
        n.commune = self.normalize_commune(e.commune)
        if e.code_commune is not None:
            dept = e.code_commune[:2]
        elif e.cp is not None:
            dept = e.cp[:2]
        else:
            return None
        if dept not in self.depts:
            return None
        n.dept = self.depts[dept]
        if e.numero is not None:
            try:
                n.numero = int(e.numero)
            except:
                pass
        elif e.voie is not None:
            n.numero, n.rue1 = self.split_num(e.voie)
        n.rue1 = e.voie
        if n.numero is not None and n.rue1 is None:
            n.rue1 = e.type_voie
        if n.numero is not None and n.rue1 is not None and n.rue1.startswith(str(n.numero)):
            n.rue1 = n.rue1.replace(str(n.numero), "")
        n.rue1 = self.normalize_street(n.rue1) if n.rue1 is not None else None
        n.rue2 = self.normalize_street(e.mention) if e.mention is not None else None
        if n.rue1 is None and n.rue2 is not None:
            n.rue1 = n.rue2
            n.rue2 = None
        if e.type_voie is not None and n.rue1 is not None and e.type_voie.upper() not in n.rue1:
            n.rue1 = e.type_voie.upper() + " " + n.rue1
        if n.rue1 == '':
            n.rue1 = None
        if n.rue1 is None and n.numero is not None:
            n.numero = None
        return n

    def make_relations(self, e: Coord, row):
        try:
            if e.inpp in self.personnes:
                e.personne = self.personnes[e.inpp]
                n = self.norm_mapper(e)
                if n is not None:
                    if n.key in self.norms:
                        n = self.norms[n.key]
                    else:
                        self.norms[n.key] = n
                        self.nb_new_norm += 1
                    e.adresse_norm = n
        except Exception as ex:
            print(f"ERROR CoordPersonne unknow FK row {self.row_num} {e}\n{ex}")
            quit(2)

    def update(self, e: Coord):
        self.entities[e.key].date_maj = e.date_maj
        if e.date_fin is not None:
            self.entities[e.key].date_fin = e.date_fin
        if e.tel is not None:
            self.entities[e.key].tel = e.tel
        if e.tel2 is not None:
            self.entities[e.key].tel2 = e.tel2
        if e.mail is not None:
            self.entities[e.key].mail = e.mail
        if e.mention is not None:
            self.entities[e.key].mention = e.mention
        if e.cedex is not None:
            self.entities[e.key].cedex = e.cedex
        self.nb_update_entity += 1

    def parse_row(self, row):
        e = self.mapper(row)
        if e.key in self.entities:
            same = e.equals(self.entities[e.key])
            if not same:
                self.update(e)
                self.nb_update_entity += 1
            e = self.entities[e.key]
            if e.adresse_norm is None and e.inpp is not None:
                n = self.norm_mapper(e)
                if n is not None:
                    if n.key in self.norms:
                        n = self.norms[n.key]
                    else:
                        self.norms[n.key] = n
                        self.nb_new_norm += 1
                    e.adresse_norm = n
                    self.nb_update_entity += 1
        else:
            self.nb_new_entity += 1
            self.entities[e.key] = e
            self.make_relations(e, row)
            self.context.session.add(e)
        self.context.session.commit()


if __name__ == '__main__':
    art.tprint(config.name, "big")
    print("RPPS Coord Corresp Parser")
    print("=========================")
    print(f"V{config.version}")
    print(config.copyright)
    print()
    parser = argparse.ArgumentParser(description="RPPS Coord Corresp Parser")
    parser.add_argument("path", help="Path")
    parser.add_argument("-e", "--echo", help="Sql Alchemy echo", action="store_true")
    args = parser.parse_args()
    context = Context()
    context.create(echo=args.echo, expire_on_commit=False)
    db_size = context.db_size()
    print(f"Database {context.db_name}: {db_size:.0f} Mb")
    rpp = RPPSCoordPersonneParser(context)
    rpp.load(args.path, delimiter=';', encoding="UTF-8", header=True)
    print(f"New coord: {rpp.nb_new_entity}")
    print(f"Nb coord update: {rpp.nb_update_entity}")
    print(f"Nb new adresse norm: {rpp.nb_new_norm}")
    new_db_size = context.db_size()
    print(f"Database {context.db_name}: {new_db_size:.0f} Mb")
    print(f"Database grows: {new_db_size - db_size:.0f} Mb ({((new_db_size - db_size) / db_size) * 100:.1f}%)")
    print(f"Parse {rpp.row_num} rows in {time.perf_counter() - time0:.0f} s")

    # data/rpps/CoordCorresp_small.csv
    # data/rpps/Extraction_RPPS_Profil4_CoordCorresp_202310250948.csv
