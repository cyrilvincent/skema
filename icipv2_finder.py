import art
import config
from sqlentities import AdresseRaw
from icipv2_ps import PSParser
from icipv2_BAN_matcher import BANMatcher
from icipv2_OSM_matcher import OSMMatcher
from icipv2_score import ScoreMatcher

if __name__ == '__main__':
    art.tprint(config.name, "big")
    print("Adresses Finder")
    print("===============")
    print(f"V{config.version}")
    print(config.copyright)
    print()
    bm = BANMatcher([])
    bm.make_cache0()
    olddept = 0
    om = OSMMatcher()
    sm = ScoreMatcher()
    while True:
        ar = AdresseRaw
        psp = PSParser(None)
        s = input("Rue: ")
        ar.adresse3 = s if s != "" else None
        ar.adresse2 = None
        ar.cp = int(input("Code Postal: "))
        dept = psp.get_dept_from_cp(ar.cp)
        ar.commune = input("Commune: ")
        norm = psp.normalize(ar)
        if dept != olddept:
            bm.make_cache1(dept)
            olddept = dept
        bm.match_norm(norm, False)
        print(f"Adresse normalisée: {norm.numero} {norm.rue1} {norm.cp} {norm.commune}")
        print(f"BAN: {norm.ban} @{norm.ban_score * 100:.0f}% lon: {norm.ban.lon:.4f}, lat: {norm.ban.lat:.4f}")
        osm, score = om.match_norm(norm)
        print(f"OSM: {osm.adresse[:100]} @{score * 100:.0f}% lon: {osm.lon:.4f}, lat: {osm.lat:.4f}")
        d = sm.calc_distance(norm.ban.lon, norm.ban.lat, osm.lon, osm.lat)
        print(f"Distance: {d}m")




