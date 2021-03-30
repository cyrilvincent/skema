import art
import config
import adressesmatcher

art.tprint(config.name, "big")
print("Adresses Finder")
print("===============")
print(f"V{config.version}")
print(config.copyright)
print()
olddept = 0
am = adressesmatcher.AdresseMatcher()
while True:
    scores = []
    try:
        dept = int(input("Departement (0 pour quitter): "))
        if dept == 0:
            quit()
        if dept != olddept:
            print(f"Load dept {dept}")
            am.db, am.communes_db, am.cps_db, am.insees_db = am.a_repo.load_adresses(dept)
        olddept = dept
        cp = int(input("Code postal: "))
        cp, score = am.match_cp(cp)
        scores.append(score)
        print(f"=>{cp} @{int(score*100)}%")
        communes = am.cps_db[cp]
        print(communes)
        commune = input("Commune: ")
        commune = am.normalize_commune(commune)
        commune, score = am.match_commune(commune, "", communes, cp)
        print(f"=>{commune} @{int(score*100)}%")
        scores.append(score)
        streets = am.communes_db[commune]
        print(f"{len(streets)} adresses trouvées")
        adresse3 = input("Rue (sans numéro): ")
        adresse3 = am.normalize_street(adresse3)
        adresse3, score = am.match_street(commune, "", adresse3, cp)
        print(f"=>{adresse3} @{int(score * 100)}%")
        scores.append(score)
        num = int(input("Numéro (0 si aucun): "))
        aentity, score = am.match_num(commune, adresse3, num)
        print(f"=>{aentity.numero} @{int(score * 100)}%")
        scores.append(score)
        print(f"Résultat: {aentity} @{int((sum(scores) / 4) * 100)}%")
    except ValueError:
        print("Erreur de saisie, recommencer")
