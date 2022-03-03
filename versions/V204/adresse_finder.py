import art
import config
from sqlentities import AdresseRaw
from ps_parser import PSParser
from BAN_matcher import BANMatcher
from OSM_matcher import OSMMatcher
from score_matcher import ScoreMatcher
from threading import Thread


class Cachethread(Thread):

    def __init__(self, dept, bm: BANMatcher):
        super().__init__()
        self.dept = dept
        self.bm = bm

    def run(self) -> None:
        self.bm.make_cache1(dept)


if __name__ == '__main__':
    art.tprint(config.name, "big")
    print("Adresses Finder")
    print("===============")
    print(f"V{config.version}")
    print(config.copyright)
    bm = BANMatcher([])
    bm.make_cache0()
    olddept = 0
    om = OSMMatcher()
    sm = ScoreMatcher()
    while True:
        try:
            ar = AdresseRaw()
            psp = PSParser(None)
            print()
            print("[Enter] to exit")
            cp = input("Code Postal: ")
            if cp == "":
                quit(0)
            ar.cp = int(cp)
            dept = psp.get_dept_from_cp(ar.cp)
            if dept != olddept:
                th = Cachethread(dept, bm)
                th.start()
                th.join()
                olddept = dept
            s = input("Rue: ")
            ar.adresse3 = s if s != "" else None
            ar.adresse2 = None
            ar.commune = input("Commune: ")
            norm = psp.normalize(ar)
            print(f"Adresse normalisée: {norm.numero} {norm.rue1} {norm.cp} {norm.commune}")
            osm, score = om.match_norm(norm)
            print(f"OSM: {osm.adresse[:100]} @{score * 100:.0f}% lon: {osm.lon:.4f}, lat: {osm.lat:.4f}")
            bm.match_norm(norm, False)
            print(f"BAN: {norm.ban} @{norm.ban_score * 100:.0f}% lon: {norm.ban.lon:.4f}, lat: {norm.ban.lat:.4f}")
            d = sm.calc_distance(norm.ban.lon, norm.ban.lat, osm.lon, osm.lat)
            print(f"Distance: {d}m")
        except Exception as ex:
            print(f"ERROR: {ex}, do again")
