import datetime
from typing import Dict, List
from sqlalchemy.orm import joinedload
from rpps_coord_corresp_parser import RPPSCoordPersonneParser
from sqlentities import Context, Dept, Coord, AdresseNorm, Activite
from base_parser import time0
import argparse
import time
import art
import config


class RPPSCoordActiviteParser(RPPSCoordPersonneParser):

    def __init__(self, context):
        super().__init__(context)
        self.activites: Dict[str, Activite] = {}


    def load_cache(self):
        print("Making cache")
        l: List[Coord] = self.context.session.query(Coord)\
            .options(joinedload(Coord.adresse_norm)).filter(Coord.activite_id.isnot(None))
        for e in l:
            self.entities[e.key] = e
            self.nb_ram += 1
        l: List[Activite] = self.context.session.query(Activite).all()
        for a in l:
            self.activites[a.key] = a
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
            e.identifiant_activite = row["Identifiant de l'activité"]
            e.complement_destinataire = self.get_nullable(row["Complément destinataire (coord. activité)"])
            e.complement_geo = self.get_nullable(row["Complément point géographique (coord. activité)"])
            e.numero = self.get_nullable(row["Numéro Voie (coord. activité)"])
            e.indice = self.get_nullable(row["Indice répétition voie (coord. activité)"])
            e.code_type_voie = self.get_nullable(row["Code type de voie (coord. activité)"])
            e.type_voie = self.get_nullable(row["Libellé type de voie (coord. activité)"])
            e.voie = self.get_nullable(row["Libellé Voie (coord. activité)"])
            e.mention = self.get_nullable(row["Mention distribution (coord. activité)"])
            e.cedex = self.get_nullable(row["Bureau cedex (coord. activité)"])
            e.cp = self.get_nullable(row["Code postal (coord. activité)"])
            e.code_commune = self.get_nullable(row["Code commune (coord. activité)"])
            e.commune = self.get_nullable(row["Libellé commune (coord. activité)"])
            if e.commune is None:
                if e.cedex is not None and len(e.cedex) > 7:
                    e.commune = e.cedex[6:]
            e.code_pays = self.get_nullable(row["Code pays (coord. activité)"])
            e.pays = None if e.code_pays == "99000" else self.get_nullable(row["Libellé pays (coord. activité)"])
            e.tel = self.get_nullable(row["Téléphone (coord. activité)"])
            e.tel2 = self.get_nullable(row["Téléphone 2 (coord. activité)"])
            e.fax = self.get_nullable(row["Télécopie (coord. activité)"])
            e.mail = self.get_nullable(row["Adresse e-mail (coord. activité)"])
            try:
                e.date_maj = self.get_nullable_date(row["Date de mise à jour (coord. activité)"])
                e.date_fin = self.get_nullable_date(row["Date de fin (coord. activité)"])
            except:
                try:
                    e.date_maj = self.get_nullable_date(row["Date de fin (coord. activité)"])
                except:
                    e.date_maj = datetime.date(1970,1,1)
                e.cp = self.get_nullable(row["Code commune (coord. activité)"])
                e.code_commune = self.get_nullable(row["Libellé commune (coord. activité)"])
                e.commune = self.get_nullable(row["Code pays (coord. activité)"])
                e.code_pays = self.get_nullable(row["Libellé pays (coord. activité)"])
        except Exception as ex:
            print(f"ERROR Coord row {self.row_num} {e}\n{ex}\n{row}")
            quit(1)
        return e

    def make_relations(self, e: Coord, row):
        try:
            if e.identifiant_activite in self.activites:
                e.activite = self.activites[e.identifiant_activite]
                n = self.norm_mapper(e)
                if n is not None:
                    if n.key in self.norms:
                        n = self.norms[n.key]
                    else:
                        self.nb_new_norm += 1
                    e.adresse_norm = n
        except Exception as ex:
            print(f"ERROR Coord unknow FK row {self.row_num} {e}\n{ex}")
            quit(2)


if __name__ == '__main__':
    art.tprint(config.name, "big")
    print("RPPS Coord Activite Parser")
    print("==========================")
    print(f"V{config.version}")
    print(config.copyright)
    print()
    parser = argparse.ArgumentParser(description="RPPS Coord Activite Parser")
    parser.add_argument("path", help="Path")
    parser.add_argument("-e", "--echo", help="Sql Alchemy echo", action="store_true")
    args = parser.parse_args()
    context = Context()
    context.create(echo=args.echo, expire_on_commit=False)
    db_size = context.db_size()
    print(f"Database {context.db_name}: {db_size:.0f} Mb")
    rpp = RPPSCoordActiviteParser(context)
    rpp.load(args.path, delimiter=';', encoding="UTF-8", header=True)
    print(f"New coord: {rpp.nb_new_entity}")
    print(f"Nb coord update: {rpp.nb_update_entity}")
    print(f"Nb bad coord: {rpp.nb_error}")
    print(f"Nb new adresse norm: {rpp.nb_new_norm}")
    new_db_size = context.db_size()
    print(f"Database {context.db_name}: {new_db_size:.0f} Mb")
    print(f"Database grows: {new_db_size - db_size:.0f} Mb ({((new_db_size - db_size) / db_size) * 100:.1f}%)")
    print(f"Parse {rpp.row_num} rows in {time.perf_counter() - time0:.0f} s")

    # data/rpps/CoordActivite_small.csv
    # data/rpps/Extraction_RPPS_Profil4_CoordAct_202310250948.csv
