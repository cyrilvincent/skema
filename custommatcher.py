import config
import time
import entities
import csv
from adressesmatcher import AdresseMatcherBase
from typing import List, Optional

time0 = time.perf_counter()


class CustomRepository:

    def save_entities(self, path, entities):
        print(f"Save {path}")
        with open(path, "w") as f:
            for e in entities:
                for i in range(len(e.v)):
                    if i != 0:
                        f.write(";")
                    f.write(f"{e.v[i]}")
                f.write("\n")

    def row2entity(self, entity, row: str):
        for i in range(len(row)):
            entity.v[i] = row[i]

    def load(self, file: str):
        with open(file) as f:
            reader = csv.reader(f, delimiter=";")
            return list(reader)


class CustomMatcherBase(AdresseMatcherBase):

    def __init__(self):
        super().__init__()
        self.custom_db = []
        self.custom_repo = CustomRepository()

    def update_entity(self, entity, aentity: entities.AdresseEntity, score: float):
        entity.adresseid = aentity.id
        entity.adressescore = score
        entity.lon = aentity.lon
        entity.lat = aentity.lat
        entity.x = aentity.x
        entity.y = aentity.y
        entity.codeinsee = aentity.code_insee
        if aentity.numero != 0:
            entity.matchadresse = f"{aentity.numero} "
        entity.matchadresse += f"{aentity.nom_afnor} {aentity.code_postal} {aentity.commune}"
        entity.matchcp = aentity.code_postal

    def update_entity_by_adressesdb(self, entity, aentity: entities.AdresseEntity,
                                    values: entities.AdresseDbEntity):
        entity.adresseid = aentity.id
        entity.adressescore = values.score
        entity.lon = values.lon
        entity.lat = values.lat
        entity.codeinsee = aentity.code_insee
        entity.matchcp = values.matchcp
        entity.matchadresse = f"{entity.adresse3} {entity.matchcp} {entity.commune}"
        entity.source = values.source

    def check_low_score(self, entity,
                        adresse3: str, originalnum: int, aentity: entities.AdresseEntity) -> entities.AdresseEntity:
        if entity.score < config.adresse_quality:
            res = self.last_chance(self.normalize_commune(entity.commune), self.normalize_street(adresse3), originalnum)
            if res is not None:
                aentity = res
                if aentity.code_postal != entity.cp:
                    self.nbbadcp += 1
                    self.log(f"WARNING CORRECTING CP: {entity.cp} {entity.commune}=>{aentity.code_postal}"
                             f" {aentity.commune}")
                entity.scores[0] = 0.5 if aentity.code_postal != entity.cp else 0.9
                entity.scores[1] = entity.scores[2] = entity.scores[3] = 0.99
            else:
                res = self.very_last_chance(int(entity.cp), self.normalize_street(adresse3), originalnum)
                if res is not None:
                    aentity = res
                    if aentity.commune != entity.commune:
                        self.nbbadcommune += 1
                        self.log(f"WARNING CORRECTING COMMUNE: {entity.cp} {entity.commune}=>{aentity.code_postal}"
                                 f" {aentity.commune}")
                    entity.scores[1] = 0.5 if aentity.commune != entity.commune else 0.9
                    entity.scores[0] = entity.scores[2] = entity.scores[3] = 0.98
        if entity.score < config.adresse_quality:
            self.nbscorelow += 1
            self.log(f"LOW SCORE: {int(entity.score * 100)}% ({(self.nbscorelow / (self.nb + 1)) * 100:.1f}%)"
                     f" {entity.adresse3} {entity.cp} {entity.commune} => {aentity.numero} {aentity.nom_afnor}"
                     f" {aentity.code_postal} {aentity.commune}")
        if aentity is None:
            aentity = entities.AdresseEntity(0)
            self.log(f"ERROR UNKNOWN {entity.adresse3} {entity.cp} {entity.commune}")
            self.nberror500 += 1
        return aentity

    def manage_adresse_db(self, entity, t):
        values = self.adresses_db[t]
        aentity = self.db[values.adresseid]
        if "OSM" in values.source:
            self.update_entity_by_adressesdb(entity, aentity, values)
        else:
            self.update_entity(entity, aentity, values.score)
        self.custom_db.append(entity)
        if entity.adressescore < config.adresse_quality:
            self.nbscorelow += 1

    def display(self):
        print(f"Nb Custom: {self.nb}")
        print(f"Nb Matching PS: {len(self.custom_db)} {(len(self.custom_db) / self.nb) * 100 : .1f}%")
        print(f"Nb Score low: {self.nbscorelow} {(self.nbscorelow / self.nb) * 100 : .1f}%")

    def parse_entity(self, entity):
        cp = int(entity.cp)
        t = (entity.cp, entity.commune, entity.adresse3, entity.adresse2)
        if t in self.adresses_db:
            self.manage_adresse_db(entity, t)
        else:
            self.matches(entity, cp, t)

    def matches(self, entity, cp, t):
        cp, score = self.match_cp(cp)
        entity.scores.append(score)
        communes = self.cps_db[cp]
        commune = self.normalize_commune(entity.commune)
        commune, score = self.match_commune(commune, communes, cp)
        entity.scores.append(score)
        if score < 0.8:
            cp2, commune2, score2 = self.get_cp_by_commune(self.normalize_commune(entity.commune), cp)
            if score2 > score and cp2 != entity.cp:
                self.log(f"WARNING BAD CP {entity.cp} {entity.commune}=>{cp2} {commune2}")
                self.nbbadcp += 1
                cp = cp2
                commune = commune2
                entity.scores[1] = score2
                entity.scores[0] = 0.5
        adresse3 = self.normalize_street(entity.adresse3)
        adresse2 = self.normalize_street(entity.adresse2)
        num, adresse3 = self.split_num(adresse3)
        if num == 0 and adresse2 != "":
            num, adresse2 = self.split_num(adresse2)
        matchadresse, score = self.match_street(commune, adresse2, adresse3, cp)
        entity.scores.append(score)
        aentity, score = self.match_num(commune, matchadresse, num)
        entity.scores.append(score)
        aentity = self.check_low_score(entity, adresse3, num, aentity)
        self.update_entity(entity, aentity, entity.score)
        self.custom_db.append(entity)
        v = entities.AdresseDbEntity(t[0], t[1], t[2], t[3], entity.adresseid, entity.score, "BAN",
                                     entity.lon, entity.lat, entity.matchcp)
        self.adresses_db[v.key] = v
        self.nbnewadresse += 1

