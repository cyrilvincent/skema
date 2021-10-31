import art
import config
import adressesmatcher
import entities
import osmrest
import selenium
import gmappoc

if __name__ == '__main__':
    art.tprint(config.name, "big")
    print("Adresses Finder")
    print("===============")
    print(f"V{config.version}")
    print(config.copyright)
    print()
    with selenium.webdriver.Chrome() as browser:
        gmap = gmappoc.GoogleLoader(browser)
        gmap.load()
        gmap.cookies()
        gmap = gmappoc.MapsLoader(browser)
        gmap.load()
        olddept = 0
        am = adressesmatcher.AdresseMatcher()
        nominatim = osmrest.NominatimRest()
        while True:
            entity = entities.PSEntity()
            try:
                dept = int(input("Departement (0 pour quitter): "))
                if dept == 0:
                    quit()
                if dept != olddept:
                    print(f"Load dept {dept}")
                    am.db, am.communes_db, am.cps_db, am.insees_db = am.a_repo.load_adresses(dept)
                    am.cedex_db = am.a_repo.load_cedex()
                olddept = dept
                entity.v[7] = int(input("Code postal: "))
                cp, score = am.match_cp(entity.cp)
                entity.scores.append(score)
                print(f"=>{cp} @{int(score*100)}%")
                communes = am.cps_db[cp]
                print(communes)
                entity.v[8] = input("Commune: ")
                commune = am.normalize_commune(entity.commune)
                commune, score = am.match_commune(commune, communes, cp)
                print(f"=>{commune} @{int(score*100)}%")
                entity.scores.append(score)
                if score < 0.8:
                    cp2, commune2, score2 = am.get_cp_by_commune(am.normalize_commune(entity.commune), cp)
                    if score2 > score:
                        print(f"WARNING BAD CP {entity.cp} {entity.commune}=>{cp2} {commune2}")
                        cp = cp2
                        commune = commune2
                        entity.scores[1] = score2
                        entity.scores[0] = 0.5
                streets = am.communes_db[commune]
                print(f"{len(streets)} adresses trouvées")
                entity.v[5] = input("Rue (sans numéro): ")
                adresse3 = am.normalize_street(entity.adresse3)
                adresse3, score = am.match_street(commune, "", adresse3, cp)
                print(f"=>{adresse3} @{int(score * 100)}%")
                entity.scores.append(score)
                num = int(input("Numéro (0 si aucun): "))
                aentity, score = am.match_num(commune, adresse3, num)
                print(f"=>{aentity.numero} @{int(score * 100)}%")
                entity.scores.append(score)
                aentity = am.check_low_score(entity, entity.adresse3, num, aentity)
                print(f"Résultat: {aentity} @{int(entity.score * 100)}%")
                print(f"Position depuis Adresse: {aentity.lon},{aentity.lat}")
                lon, lat, cp = nominatim.get_lon_lat_from_adresse(f"{num} {entity.v[5]}", entity.v[8], entity.v[7])
                dist = nominatim.calc_distance(aentity.lon, aentity.lat, lon, lat)
                print(f"Position depuis Nominatim: {lon},{lat} @{dist}m")
                lon, lat = gmap.get_lon_lat_from_adresse(f"{num} {entity.v[5]} {entity.v[7]} {entity.v[8]} FRANCE")
                dist = nominatim.calc_distance(aentity.lon, aentity.lat, lon, lat)
                print(f"Position depuis GoogleMap: {lon},{lat} @{dist}m")
                dist = nominatim.calc_distance(aentity.lon, aentity.lat, 5.5782497, 45.098384)
                print(f"Position depuis Cyril: {dist}m")
            except ValueError:
                print("Erreur de saisie, recommencer")
            except KeyError:
                print("Mauvaise valeur, recommencer")
