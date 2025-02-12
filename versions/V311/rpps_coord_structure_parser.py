import datetime
from typing import Dict, List
from sqlalchemy.orm import joinedload
from rpps_coord_corresp_parser import RPPSCoordPersonneParser
from sqlentities import Context, Dept, Coord, AdresseNorm, Structure
from base_parser import time0
import argparse
import time
import art
import config


class RPPSCoordStructureParser(RPPSCoordPersonneParser):

    def __init__(self, context):
        super().__init__(context)
        self.structures: Dict[str, Structure] = {}


    def load_cache(self):
        print("Making cache")
        l: List[Coord] = self.context.session.query(Coord)\
            .options(joinedload(Coord.adresse_norm)).filter(Coord.structure_id_technique.isnot(None)).all()
        for e in l:
            self.entities[e.structure_id_technique] = e
            self.nb_ram += 1
        l: List[Structure] = self.context.session.query(Structure).all()
        for s in l:
            self.structures[s.key] = s
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
            e.structure_id_technique = row["Identifiant technique de la structure"]
            e.complement_destinataire = self.get_nullable(row["Complément destinataire (coord. structure)"])
            e.complement_geo = self.get_nullable(row["Complément point géographique (coord. structure)"])
            e.numero = self.get_nullable(row["Numéro Voie (coord. structure)"])
            e.indice = self.get_nullable(row["Indice répétition voie (coord. structure)"])
            e.code_type_voie = self.get_nullable(row["Code type de voie (coord. structure)"])
            e.type_voie = self.get_nullable(row["Libellé type de voie (coord. structure)"])
            e.voie = self.get_nullable(row["Libellé Voie (coord. structure)"])
            e.mention = self.get_nullable(row["Mention distribution (coord. structure)"])
            e.cedex = self.get_nullable(row["Bureau cedex (coord. structure)"])
            e.cp = self.get_nullable(row["Code postal (coord. structure)"])
            e.code_commune = self.get_nullable(row["Code commune (coord. structure)"])
            e.commune = self.get_nullable(row["Libellé commune (coord. structure)"])
            if e.commune is None:
                if e.cedex is not None and len(e.cedex) > 7:
                    e.commune = e.cedex[6:]
            e.code_pays = self.get_nullable(row["Code pays (coord. structure)"])
            e.pays = None if e.code_pays == "99000" else self.get_nullable(row["Libellé pays (coord. structure)"])
            e.tel = self.get_nullable(row["Téléphone (coord. structure)"])
            e.tel2 = self.get_nullable(row["Téléphone 2 (coord. structure)"])
            e.fax = self.get_nullable(row["Télécopie (coord. structure)"])
            e.mail = self.get_nullable(row["Adresse e-mail (coord. structure)"])
            try:
                e.date_maj = self.get_nullable_date(row["Date de mise à jour (coord. structure)"])
                if e.date_maj is None:
                    raise ValueError()
                e.date_fin = self.get_nullable_date(row["Date de fin (coord. structure)"])
            except:
                try:
                    e.date_maj = self.get_nullable_date(row["Date de fin (coord. structure)"])
                except:
                    e.date_maj = datetime.date(1970,1,1)
                e.cp = self.get_nullable(row["Code commune (coord. structure)"])
                e.code_commune = self.get_nullable(row["Libellé commune (coord. structure)"])
                e.commune = self.get_nullable(row["Code pays (coord. structure)"])
                e.code_pays = self.get_nullable(row["Libellé pays (coord. structure)"])
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
            print(f"ERROR Coord row {self.row_num} {e}\n{ex}\n{row}")
            quit(1)
        return e

    def make_relations(self, e: Coord, row):
        try:
            if e.structure_id_technique in self.structures:
                e.structure = self.structures[e.structure_id_technique]
                n = self.norm_mapper(e)
                if n is not None:
                    if n.key in self.norms:
                        n = self.norms[n.key]
                    else:
                        self.norms[n.key] = n
                        self.nb_new_norm += 1
                    e.adresse_norm = n
        except Exception as ex:
            print(f"ERROR Coord unknow FK row {self.row_num} {e}\n{ex}")
            quit(2)

    def update(self, e: Coord):
        key = e.structure_id_technique
        self.entities[key].date_maj = e.date_maj
        if e.date_fin is not None:
            self.entities[key].date_fin = e.date_fin
        if e.tel is not None:
            self.entities[key].tel = e.tel
        if e.tel2 is not None:
            self.entities[key].tel2 = e.tel2
        if e.mail is not None:
            self.entities[key].mail = e.mail
        if e.mention is not None:
            self.entities[key].mention = e.mention
        if e.cedex is not None:
            self.entities[key].cedex = e.cedex
        self.nb_update_entity += 1

    def parse_row(self, row):
        e = self.mapper(row)
        if e.structure_id_technique in self.entities:
            same = e.equals(self.entities[e.structure_id_technique])
            if not same:
                self.update(e)
                self.nb_update_entity += 1
            e = self.entities[e.structure_id_technique]
            if e.adresse_norm is None and e.structure_id_technique is not None:
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
            self.entities[e.structure_id_technique] = e
            self.make_relations(e, row)
            self.context.session.add(e)
        self.context.session.commit()


if __name__ == '__main__':
    art.tprint(config.name, "big")
    print("RPPS Coord Structure Parser")
    print("===========================")
    print(f"V{config.version}")
    print(config.copyright)
    print()
    parser = argparse.ArgumentParser(description="RPPS Coord Structure Parser")
    parser.add_argument("path", help="Path")
    parser.add_argument("-e", "--echo", help="Sql Alchemy echo", action="store_true")
    args = parser.parse_args()
    context = Context()
    context.create(echo=args.echo, expire_on_commit=False)
    db_size = context.db_size()
    print(f"Database {context.db_name}: {db_size:.0f} Mb")
    rpp = RPPSCoordStructureParser(context)
    rpp.load(args.path, delimiter=';', encoding="UTF-8", header=True)
    print(f"New coord: {rpp.nb_new_entity}")
    print(f"Nb coord update: {rpp.nb_update_entity}")
    print(f"Nb new adresse norm: {rpp.nb_new_norm}")
    new_db_size = context.db_size()
    print(f"Database {context.db_name}: {new_db_size:.0f} Mb")
    print(f"Database grows: {new_db_size - db_size:.0f} Mb ({((new_db_size - db_size) / db_size) * 100:.1f}%)")
    print(f"Parse {rpp.row_num} rows in {time.perf_counter() - time0:.0f} s")

    # data/rpps/CoordStruct_small.csv
    # data/rpps/Extraction_RPPS_Profil4_CoordStruct_202310250948.csv
    # adresse_nomr limit 287554
