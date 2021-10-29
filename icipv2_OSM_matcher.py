from typing import Dict, Optional, List, Tuple, Set, Iterable
from sqlalchemy.orm import joinedload
from sqlentities import Context, Cedex, BAN, OSM, AdresseRaw, Dept, AdresseNorm, Source
import argparse
import time
import art
import config
import difflib
import numpy as np

time0 = time.perf_counter()


class OSMMatcher:

    def __init__(self, force=False, ban_echo=False, sa_echo=False):
        self.context = Context()
        self.context.create_engine(echo=sa_echo)
        self.session = self.context.get_session(False)
        self.force = force
        self.echo = ban_echo
        self.row_num = 0
        self.total_nb_norm = 0
        self.score = 0.0
        self.total_scores = []
        self.filter_force = (AdresseNorm.ban_score < 0.9) | AdresseNorm.source_id.is_(None) \
                            | ((AdresseNorm.source_id != 3) & (AdresseNorm.source_id != 5))
        self.filter_no_force = AdresseNorm.osm_id.is_(None) & AdresseNorm.score.is_(None)
        print(f"Database {self.context.db_name}: {self.context.db_size():.0f} Mo")

    def stats(self):
        ban = self.session.query(BAN).count()
        print(f"Found {ban} BAN")
        norm = self.session.query(AdresseNorm).count()
        print(f"Found {norm} adresses")
        query = self.session.query(AdresseNorm).filter(self.filter_force)
        if self.force:
            self.total_nb_norm = query.count()
        else:
            self.total_nb_norm = query.filter(self.filter_no_force).count()
        print(f"Found {self.total_nb_norm} adresses to match")
        if self.total_nb_norm == 0:
            print("Everything is up to date")
            quit(0)

    def purge(self):
        print("Purge")
        osms = self.session.query(OSM).filter(~OSM.bans.any())
        for osm in osms:
            self.session.delete(osm)
        self.session.commit()

    def match_norm(self, row: AdresseNorm):
        pass

    def match(self):
        self.stats()
        rows = self.session.query(AdresseNorm).filter(self.filter_force)
        if not self.force:
            rows = rows.filter(self.filter_no_force)
        for row in rows:
            self.row_num += 1
            self.match_norm(row)
            self.total_scores.append(self.score)


if __name__ == '__main__':
    art.tprint(config.name, "big")
    print("OSM Matcher")
    print("===========")
    print(f"V{config.version}")
    print(config.copyright)
    print()
    parser = argparse.ArgumentParser(description="BAN Matcher")
    parser.add_argument("-e", "--echo", help="Sql Alchemy echo", action="store_true")
    parser.add_argument("-f", "--force", help="Force matching", action="store_true")
    parser.add_argument("-l", "--log", help="Log (OSM echo)", action="store_true")
    args = parser.parse_args()
    om = OSMMatcher(args.force, args.log, args.echo)
    om.match()
    mean = np.mean(np.array(om.total_scores))
    std = np.std(np.array(om.total_scores))
    print(f"Score average {mean * 100:.1f}%")
    print(f"Score median {np.median(np.array(om.total_scores)) * 100:.1f}%")
    print(f"Score min {np.min(np.array(om.total_scores)) * 100:.1f}%")
    print(f"Score std {std * 100:.1f}%")
    print(f"Score average-std {(mean - std) * 100:.1f}%")
    print(f"Score average-3std {(mean - 3 * std) * 100:.1f}%")
    print(f"Parse {om.row_num} adresses in {time.perf_counter() - time0:.0f} s")

    # -e -l -d [5]
