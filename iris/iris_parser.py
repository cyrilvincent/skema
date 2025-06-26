import csv

from sqlentities import Context, Cabinet, PS, AdresseRaw, PSCabinetDateSource, Profession, Dept, Commune
from base_parser import BaseParser
import argparse
import art
import config
import sys



class IrisParser(BaseParser):

    def __init__(self, context):
        super().__init__(context)
        csv.field_size_limit(1000000)
        self.depts: dict[str, Dept] = {}
        self.communes: dict[str, Commune] = {}
        self.nb_new_commune = 0
        # todo add dept field to server & schema iris


    def load_cache(self):
        l = self.context.session.query(Dept).all()
        for d in l:
            self.depts[d.num] = d
            self.nb_ram += 1
        l = self.context.session.query(Commune).all()
        for c in l:
            self.communes[c.code] = c
            self.nb_ram += 1
        print(f"{self.nb_ram} objects in cache")

    def check_date(self, path):
        pass

    def dept_mapper(self, row) -> Dept | None:
        e = Dept()
        try:
            e.num = row["Code Officiel Département"]
            e.name = row["Nom Officiel Département"]
            e.region_id = self.get_nullable_int(row["Code Officiel Région"])
            e.region_name = row["Nom Officiel Région"]
        except Exception as ex:
            print(f"ERROR dept row {self.row_num} {e}\n{ex}")
            quit(1)
        return e

    def commune_mapper(self, row) -> Commune | None:
        e = Commune()
        try:
            e.code = row["Code Officiel Commune"]
            code: str = e.code
            if e.code == "2A024":
                pass
            if code.startswith("2A"):
                code = code.replace("2A", "201")
            elif code.startswith("2B"):
                code = code.replace("2B", "202")
            e.id = int(code)
            e.nom = row["Nom Officiel Commune"]
            e.nom_norm = self.normalize_string(e.nom).upper()
            e.epci_id = self.get_nullable_int(row["Code Officiel EPCI"])
            e.epci_nom = self.get_nullable(row["Nom Officiel EPCI"])
            e.bassin_vie_id = row["Code Officiel Bassin vie 2022"]
            e.bassin_vie_nom = row["Nom Officiel Bassin vie 2022"]
            e.zone_emploi_id = self.get_nullable_int(row["Code Officiel Zone emploi 2020"])
            e.zone_emploi_nom = self.get_nullable(row["Nom Officiel Zone emploi 2020"])
            e.arr_dept_id = row["Code Officiel Arrondissement départemental"]
            e.arr_dept_nom = row["Nom Officiel Arrondissement départemental"]
        except Exception as ex:
            print(f"ERROR commune row {self.row_num} {e}\n{ex}")
            quit(1)
        return e

    def mapper(self, row) -> Cabinet:
        c = Cabinet()
        try:
            c.nom = f"{row[1]} {row[2]}" if row[3] == '' else row[3]
            c.telephone = self.get_nullable(row[9])
            c.key = f"{c.nom}_{row[7]}_{row[5]}".replace(" ", "_")[:255]
        except Exception as ex:
            print(f"ERROR cabinet row {self.row_num} {c}\n{ex}")
            quit(2)
        return c

    # def create_update_cabinet(self, e: PS, row) -> Cabinet:
    #     c = self.cabinet_mapper(row)
    #     if c.key in self.cabinets:
    #         c = self.cabinets[c.key]
    #     else:
    #         self.nb_cabinet += 1
    #         self.cabinets[c.key] = c
    #     keys = [pcds.key for pcds in e.ps_cabinet_date_sources]
    #     if (e.id, c.id, self.date_source.id) not in keys:
    #         pcds = PSCabinetDateSource()
    #         pcds.date_source = self.date_source
    #         pcds.cabinet = c
    #         e.ps_cabinet_date_sources.append(pcds)
    #     return c

    def parse_row(self, row):
        dept_temp = self.dept_mapper(row)
        if dept_temp.num in self.depts:
            dept = self.depts[dept_temp.num]
            if dept.name is None:
                dept.name = dept_temp.name
                dept.region_id = dept_temp.region_id
                dept.region_name = dept_temp.region_name
                self.context.session.commit()
            commune = self.commune_mapper(row)
            if commune.code not in self.communes:
                self.communes[commune.code] = commune
                commune.dept = dept
                self.context.session.add(commune)
                self.context.session.commit()
                self.nb_new_commune += 1


        #     # if args.trace:
        #     #     out_file.write(",".join([str(x.strip()) for x in row]))
        #     e = self.mapper(row)
        #     a = self.create_update_adresse_raw(row)
        #     n = self.create_update_norm(a)
        #     p = self.profession_mapper(row)
        #     inpp, rule_nb = self.match_inpp(e, p, n)
        #     # if args.trace:
        #     #     out_file.write(f",{inpp},{rule_nb}\n")
        #     if inpp is not None:
        #         e.key = inpp
        #         e.has_inpp = True
        #         if rule_nb > 0:
        #             self.rules[rule_nb - 1] += 1
        #     if e.key in self.entities:
        #         if 0 < rule_nb < self.entities[e.key].rule_nb:
        #             self.entities[e.key].rule_nb = rule_nb
        #         e = self.entities[e.key]
        #         self.nb_existing_entity += 1
        #     else:
        #         if rule_nb > 0:
        #             e.rule_nb = rule_nb
        #         self.entities[e.key] = e
        #         self.nb_new_entity += 1
        #         self.context.session.add(e)
        #     c = self.create_update_cabinet(e, row)
        #     c.adresse_raw = a
        #     # if not args.nosave:
        #     #     self.context.session.commit()
        # else:
        #     self.nb_out_dept += 1


if __name__ == '__main__':
    art.tprint(config.name, "big")
    print("IRIS Parser")
    print("=========")
    print(f"V{config.version}")
    print(config.copyright)
    print()
    parser = argparse.ArgumentParser(description="IRIS Parser")
    parser.add_argument("path", help="Path")
    parser.add_argument("-e", "--echo", help="Sql Alchemy echo", action="store_true")
    args = parser.parse_args()
    context = Context()
    context.create(echo=args.echo, expire_on_commit=False)
    db_size = context.db_size()
    print(f"Database {context.db_name}: {db_size:.0f} Mb")
    ip = IrisParser(context)
    ip.load(args.path, encoding="utf8", header=True)
    print(f"New PS: {ip.nb_new_entity}")
    print(f"New commune: {ip.nb_new_commune}")
    # # print(f"Update PS: {psp.nb_update_entity}")
    # print(f"Existing PS: {psp.nb_existing_entity} ({psp.nb_new_entity + psp.nb_existing_entity})")
    # print(f"Dept >95 PS: {psp.nb_out_dept} ({psp.nb_new_entity + psp.nb_existing_entity + psp.nb_out_dept})")
    # print(f"New cabinet: {psp.nb_cabinet}")
    # print(f"New adresse: {psp.nb_new_adresse}")
    # print(f"New adresse normalized: {psp.nb_new_norm}")
    # print(f"Matching INPP: {psp.nb_inpps}/{psp.nb_unique_ps}: {(psp.nb_inpps / psp.nb_unique_ps) * 100:.0f}%")
    # print(f"Matched rules: {psp.rules}")
    new_db_size = context.db_size()
    print(f"Database {context.db_name}: {new_db_size:.0f} MB")
    print(f"Database grows: {new_db_size - db_size:.0f} Mb ({((new_db_size - db_size) / db_size) * 100:.1f}%)")

    # data/iris/georef-france-iris.csv
