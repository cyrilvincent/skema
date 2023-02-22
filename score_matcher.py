from typing import Dict, List
from sqlalchemy.orm import joinedload
from sqlentities import Context, BAN, AdresseNorm, Source
import argparse
import time
import art
import config
import numpy as np
import math


time0 = time.perf_counter()


class ScoreMatcher:

    def __init__(self, force=False, ban_echo=False, sa_echo=False):
        self.context = Context()
        self.context.create_engine(echo=sa_echo)
        self.session = self.context.get_session(False)
        self.force = force
        self.echo = ban_echo
        self.row_num = 0
        self.total_nb_norm = 0
        self.total_scores = []
        self.filter_no_force = AdresseNorm.score.is_(None)
        self.sources: Dict[int, Source] = {}

    def load_cache(self):
        l: List[Source] = self.session.query(Source).all()
        for s in l:
            self.sources[s.id] = s

    def stats(self):
        ban = self.session.query(BAN).count()
        print(f"Found {ban} BAN")
        norm = self.session.query(AdresseNorm).count()
        print(f"Found {norm} adresses")
        query = self.session.query(AdresseNorm)
        if self.force:
            self.total_nb_norm = query.count()
        else:
            self.total_nb_norm = query.filter(self.filter_no_force).count()
        print(f"Found {self.total_nb_norm} adresses to match")
        if self.total_nb_norm == 0:
            print("Everything is up to date")
            quit(0)

    def calc_distance(self, lon1, lat1, lon2, lat2):
        r = 6373.0
        lat1 = math.radians(lat1)
        lon1 = math.radians(lon1)
        lat2 = math.radians(lat2)
        lon2 = math.radians(lon2)
        dlon = lon2 - lon1
        dlat = lat2 - lat1
        a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        distance = r * c
        return int(distance * 1000)

    def match_row(self, row: AdresseNorm):
        self.row_num += 1
        if (row.source is None or (row.source_id != 3 and row.source_id != 5)) and row.ban is not None:
            if (row.osm is None and row.ban_score >= config.ban_mean - config.osm_nb_std * config.ban_std)\
                    or row.osm_score == 0:
                row.source = self.sources[2]
                row.lon, row.lat = row.ban.lon, row.ban.lat
                row.score = row.ban_score
            elif row.osm is not None:
                d = self.calc_distance(row.ban.lon, row.ban.lat, row.osm.lon, row.osm.lat)
                if d < 100:
                    row.source = self.sources[4]
                    row.lon, row.lat = row.ban.lon, row.ban.lat
                    row.score = 1
                if d < 250:
                    row.source = self.sources[4]
                    row.lon, row.lat = row.ban.lon, row.ban.lat
                    row.score = min(1, max(row.ban_score, row.osm_score) + 0.1)
                elif d < 500:
                    row.source = self.sources[4]
                    if row.ban_score > row.osm_score:
                        row.lon, row.lat = row.ban.lon, row.ban.lat
                        row.score = row.ban_score
                    else:
                        row.lon, row.lat = row.osm.lon, row.osm.lat
                        row.score = row.osm_score
                elif d > 100000 and row.osm_score < 0.9:
                    row.source = self.sources[2]
                    row.lon, row.lat = row.ban.lon, row.ban.lat
                    row.score = row.ban_score
                else:
                    if row.ban_score > row.osm_score:
                        row.source = self.sources[2]
                        row.lon, row.lat = row.ban.lon, row.ban.lat
                        row.score = row.ban_score
                    else:
                        row.source = self.sources[1]
                        row.lon, row.lat = row.osm.lon, row.osm.lat
                        row.score = row.osm_score
                    if d > 5000 and row.score < config.ban_mean - config.ban_std:
                        row.score -= 0.1
                    elif d > 10000 and row.score < config.ban_mean - 3 * config.ban_std:
                        row.score /= 2
                if row.rue1 is None and row.source_id == 1:
                    row.score = (1 + row.score) / 2
                if self.echo:
                    print(f"{d}m {row.rue1} {row.cp} {row.commune} <=> "
                          f"{row.ban.nom_voie} {row.ban.code_postal} {row.ban.nom_commune} "
                          f"@{row.ban_score * 100:.0f}% <=> {row.osm.adresse[:40]} @{row.osm_score * 100:.0f}% "
                          f"=> {row.source} @{row.score * 100:.0f}%")
            if row.score is not None:
                self.total_scores.append(row.score)
                self.session.commit()

    def match(self):
        self.stats()
        self.load_cache()
        rows = self.session.query(AdresseNorm).options(joinedload(AdresseNorm.source)) \
            .options(joinedload(AdresseNorm.ban)).options(joinedload(AdresseNorm.osm))
        if self.force:
            rows = rows.all()
        else:
            rows = rows.filter(self.filter_no_force)
        print("Parsing...")
        for row in rows:
            self.match_row(row)
            if self.row_num % 1000 == 0 or self.row_num == 10 or self.row_num == 100:
                print(f"Found {self.row_num} adresses {(self.row_num / self.total_nb_norm) * 100:.1f}% "
                      f"in {int(time.perf_counter() - time0)}s")


if __name__ == '__main__':
    art.tprint(config.name, "big")
    print("Score Matcher")
    print("============")
    print(f"V{config.version}")
    print(config.copyright)
    print()
    parser = argparse.ArgumentParser(description="BAN Matcher")
    parser.add_argument("-e", "--echo", help="Sql Alchemy echo", action="store_true")
    parser.add_argument("-f", "--force", help="Force matching", action="store_true")
    parser.add_argument("-l", "--log", help="Log (debug echo)", action="store_true")
    args = parser.parse_args()
    sm = ScoreMatcher(args.force, args.log, args.echo)
    print(f"Database {sm.context.db_name}: {sm.context.db_size():.0f} Mb")
    sm.match()
    if len(sm.total_scores) > 0:
        mean = np.mean(np.array(sm.total_scores))
        std = np.std(np.array(sm.total_scores))
        print(f"Score average {mean * 100:.1f}%")
        print(f"Score median {np.median(np.array(sm.total_scores)) * 100:.1f}%")
        print(f"Score min {np.min(np.array(sm.total_scores)) * 100:.1f}%")
        print(f"Score std {std * 100:.1f}%")
    print(f"Parse {sm.row_num} adresses in {time.perf_counter() - time0:.0f} s")
    # -e -l -d [5]
    # select percentile_cont(0.5)WITHIN GROUP (ORDER BY score) as median, stddev(score) as std, avg(score)
    # from adresse_norm where score is not NULL limit 100
