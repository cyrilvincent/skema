from typing import Optional, Tuple
from sqlentities import Context, BAN, OSM, AdresseNorm
import argparse
import time
import art
import config
import numpy as np
import ssl
import urllib.request
import urllib.parse
import urllib.error
import json
import re

time0 = time.perf_counter()


class OSMMatcher:

    def __init__(self, force=False, ban_echo=False, sa_echo=False):
        self.context = Context()
        self.context.create_engine(echo=sa_echo)
        self.session = self.context.get_session(False)
        self.force = force
        self.echo = ban_echo
        self.uri = "https://nominatim.openstreetmap.org/search.php?format=jsonv2&country=France"
        self.row_num = 0
        self.total_nb_norm = 0
        self.total_scores = []
        self.filter_force = (AdresseNorm.ban_score < config.ban_mean - config.osm_nb_std * config.ban_std) & \
                            (AdresseNorm.source_id.is_(None) |
                             ((AdresseNorm.source_id != 3) & (AdresseNorm.source_id != 5)))
        self.filter_no_force = AdresseNorm.osm_score.is_(None) & AdresseNorm.score.is_(None)
        ssl._create_default_https_context = ssl._create_unverified_context

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

    def get_json_from_url(self, url, nbretry=0):
        if self.echo:
            print(url)
        try:
            with urllib.request.urlopen(url) as response:
                s = response.read()
                js = json.loads(s)
                return js
        except Exception as ex:
            print(url)
            print(f"ERROR URLError: {ex}")
            if nbretry == 5:
                raise ex
            else:
                print(f"RETRY {nbretry + 1}")
                time.sleep(nbretry * 30 + 1)
                return self.get_json_from_url(url, nbretry + 1)

    def get_osm_from_adresse(self, numero: Optional[int], rue: Optional[str],
                             commune: Optional[str], cp: Optional[int]) -> Optional[OSM]:
        url = self.uri
        osm = OSM()
        if rue is not None:
            if numero is None:
                url += f"&street={urllib.parse.quote(rue)}"
            else:
                url += f"&street={numero}%20{urllib.parse.quote(rue)}"
        if commune is not None:
            if commune.endswith("CEDE"):
                commune = commune[:-5]
            url += f"&city={urllib.parse.quote(commune)}"
        if cp is not None:
            url += f"&postalcode={cp}"
        js = self.get_json_from_url(url)
        if len(js) > 0:
            try:
                osm.lat = float(js[0]["lat"])
                osm.lon = float(js[0]["lon"])
                osm.adresse = js[0]["display_name"][:255]
                index = osm.adresse.rindex(",")
                cp: str = osm.adresse[index - 5: index].strip()
                if cp.isdigit():
                    osm.cp = int(cp)
            except ValueError:
                return None
            return osm
        return None

    def purge(self):
        print("Purge")
        osms = self.session.query(OSM).filter(~OSM.bans.any())
        for osm in osms:
            self.session.delete(osm)
        self.session.commit()

    def has_num(self, s: str) -> bool:
        regex = r"(\d+)"
        match = re.match(regex, s)
        return match is not None

    def match_norm(self, row: AdresseNorm) -> Tuple[Optional[OSM], float]:
        osm = self.get_osm_from_adresse(row.numero, row.rue1, row.commune, row.cp)
        if osm is not None:
            if self.has_num(osm.adresse):
                return osm, 1  # 1260
            if osm.adresse.count(",") >= 7:
                return osm, 0.85  # 2000
            return osm, 0.65  # 350
        if row.rue2 is not None:
            osm = self.get_osm_from_adresse(None, row.rue2, row.commune, row.cp)
            if osm is not None:
                if self.has_num(osm.adresse):
                    return osm, 1
                if osm.adresse.count(",") >= 7:
                    return osm, 0.97  # 490
                return osm, 0.77  # 20
        if row.numero is not None:
            osm = self.get_osm_from_adresse(None, row.rue1, None, row.cp)
            if osm is not None:
                if osm.adresse.count(",") >= 7:
                    return osm, 0.84  # 330
                return osm, 0.64  # 14
        osm = self.get_osm_from_adresse(None, None, row.commune, row.cp)
        if osm is not None:
            if osm.adresse.count(",") >= 6:
                return osm, 0.7  # 1500
            return osm, 0.5
        osm = self.get_osm_from_adresse(row.numero, row.rue1, row.commune, None)
        if osm is not None:
            if self.has_num(osm.adresse):
                return osm, 0.8  # 30
            if osm.adresse.count(",") >= 7:
                return osm, 0.6
            return osm, 0.5
        # osm = self.get_osm_from_adresse(None, None, row.commune, None)
        # if osm is not None:
        #     return osm, 0.5
        return None, 0

    def match(self):
        self.stats()
        rows = self.session.query(AdresseNorm).filter(self.filter_force).order_by(AdresseNorm.ban_score)
        if not self.force:
            rows = rows.filter(self.filter_no_force)
        for row in rows:
            self.row_num += 1
            osm, score = self.match_norm(row)
            self.total_scores.append(score)
            if osm is None:
                if self.echo:
                    print(f"{row.rue1} {row.cp} {row.commune} => No match")
            else:
                ban_score = 0 if row.ban_score is None else row.ban_score
                if self.echo:
                    print(f"{row.numero} {row.rue1} {row.cp} {row.commune} @{ban_score * 100:.0f}% "
                          f"=> {osm.adresse[:70]} {osm.cp} @{score * 100:.0f}%")
            row.osm_score = score
            if osm is not None:
                row.osm = osm
            self.session.commit()
            if self.row_num % 10 == 0:
                print(f"Found {self.row_num} adresses {(self.row_num / self.total_nb_norm) * 100:.1f}% "
                      f"in {int(time.perf_counter() - time0)}s")
        self.purge()

    def test_osm(self):
        print(f"Test OSM")
        url = f"{self.uri}&street=1571%20chemin%20des%20blancs&postalcode=38250&city=lans%20en%vercors"
        js = self.get_json_from_url(url)
        print(js)
        lat = int(float(js[0]["lat"]))
        if lat == 45:
            print("OSM is OK")
        else:
            print(f"Network problem {lat}")
            quit(1)


if __name__ == '__main__':
    art.tprint(config.name, "big")
    print("OSM Matcher")
    print("===========")
    print(f"V{config.version}")
    print(config.copyright)
    print()
    parser = argparse.ArgumentParser(description="OSM Matcher")
    parser.add_argument("-e", "--echo", help="Sql Alchemy echo", action="store_true")
    parser.add_argument("-f", "--force", help="Force matching", action="store_true")
    parser.add_argument("-l", "--log", help="Log (OSM echo)", action="store_true")
    args = parser.parse_args()
    om = OSMMatcher(args.force, args.log, args.echo)
    om.test_osm()
    print(f"Database {om.context.db_name}: {om.context.db_size():.0f} Mb")
    om.match()
    mean = np.mean(np.array(om.total_scores))
    std = np.std(np.array(om.total_scores))
    print(f"Score average {mean * 100:.1f}%")
    print(f"Score median {np.median(np.array(om.total_scores)) * 100:.1f}%")
    print(f"Score std {std * 100:.1f}%")
    print(f"Parse {om.row_num} adresses in {time.perf_counter() - time0:.0f} s")

    # -e -l -d [5]
