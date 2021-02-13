def street(cp, street):
    if cp // 1000 == 5:
        if "CORONAT CLINIQUE DES ALPES DU SUD" in street:
            return "RUE ANTONIN CORONAT"
    if cp // 1000 == 69:
        if "SOUCELIER" in street:
            return "RUE M L ET ANNE MARIE SOUCELIER".upper()
    return street


def cp_cedex(cp):
    res = cp
    if cp == 38034:
        res = 38100
    if cp == 20184:
        res = 20090
    return res

def commune(cp, commune):
    if cp // 1000 == 20:
        if commune == "PORTO":
            return "OTA"
        if commune == "PORTICCIO":
            return "GROSSETO PRUGNA"
        if commune == "SAGONE":
            return "VICO"
    return commune