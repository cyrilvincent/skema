class AdresseEntity:
    """
    Entité adresse
    """

    def __init__(self, id):
        self.id = id
        self.numero = 0
        self.rep = ""
        self.nom_afnor = ""
        self.nom_voie = ""
        self.code_postal = 0
        self.commune = ""
        self.commune_old = ""
        self.lon = 0
        self.lat = 0
        self.code_insee = ""
        self.x = 0
        self.y = 0

    def __repr__(self):
        return f"Adresse ({self.id}) {self.numero} {self.nom_afnor} {self.code_postal} {self.commune}"


class CedexEntity:
    """
    Entité cedex
    """

    def __init__(self, cp):
        self.cp = cp
        self.commune = ""
        self.code_insee = ""

    def __repr__(self):
        return f"Cedex {self.cp} {self.commune} {self.code_insee}"


class AdresseDbEntity:

    def __init__(self, cp, commune, adresse3, adresse2, adresseid, score, source, lon, lat, matchcp):
        self._cp = 0
        self.cp = cp
        self.commune = commune
        self.adresse3 = adresse3
        self.adresse2 = adresse2
        self.adresseid = adresseid
        self.score = score
        self.source = source
        self.lon = lon
        self.lat = lat
        self.matchcp = matchcp

    @property
    def key(self):
        return self.cp, self.commune, self.adresse3, self.adresse2

    @property
    def cp(self):
        return self._cp

    @cp.setter
    def cp(self, value):
        self._cp = value
        if len(value) == 4:
            self._cp = "0" + self._cp

    def __repr__(self):
        return f"AdresseDb {self.key}"


class PSEntity:
    """
    Entité PS
    """

    nb = 45
    originalnb = 33

    def __init__(self):
        self.scores = []
        self.v = []
        for i in range(PSEntity.nb):
            self.v.append("")
        for i in range(38, 43):
            self.v[i] = 0.0
        self.v[7] = 0
        self.v[44] = "BAN"
        self.updateid()
        self.rownum = 0

    @property
    def nom(self):
        return self.v[1]

    @property
    def prenom(self):
        return self.v[2]

    @property
    def adresse2(self):
        return self.v[4]

    @property
    def adresse3(self):
        return self.v[5]

    @property
    def adresse4(self):
        return self.v[6]

    @property
    def cp(self):
        return self.v[7]

    @property
    def commune(self):
        return self.v[8]

    @property
    def profession(self):
        return self.v[10]

    @property
    def id(self):
        s = f"{self.cp}{self.nom}{self.prenom}{self.profession}".replace(" ", "")
        return s.replace("'", "").replace("-", "").replace("/", "").replace(" ", "").strip()

    def updateid(self):
        """
        MAJ de l'id
        """
        self.v[33] = self.id

    @property
    def score(self):
        if len(self.scores) == 0:
            return 0.0
        return sum([s for s in self.scores]) / len(self.scores)

    @property
    def rownum(self):
        return self.v[34]

    @rownum.setter
    def rownum(self, value):
        self.v[34] = value

    @property
    def adresseid(self):
        return self.v[35]

    @adresseid.setter
    def adresseid(self, value):
        self.v[35] = value

    @property
    def matchadresse(self):
        return self.v[36]

    @matchadresse.setter
    def matchadresse(self, value):
        self.v[36] = value

    @property
    def codeinsee(self):
        return self.v[37]

    @codeinsee.setter
    def codeinsee(self, value):
        self.v[37] = value

    @property
    def lon(self):
        return self.v[38]

    @lon.setter
    def lon(self, value):
        self.v[38] = value

    @property
    def lat(self):
        return self.v[39]

    @lat.setter
    def lat(self, value):
        self.v[39] = value

    @property
    def x(self):
        return self.v[40]

    @x.setter
    def x(self, value):
        self.v[40] = value

    @property
    def y(self):
        return self.v[41]

    @y.setter
    def y(self, value):
        self.v[41] = value

    @property
    def adressescore(self):
        return self.v[42]

    @adressescore.setter
    def adressescore(self, value):
        self.v[42] = value

    @property
    def matchcp(self):
        return self.v[43]

    @matchcp.setter
    def matchcp(self, value):
        self.v[43] = value

    def __repr__(self):
        return f"[{self.rownum}] PS: {self.id}"


if __name__ == '__main__':
    e = PSEntity()
    print(e)
