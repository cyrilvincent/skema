class AdresseEntity:

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


class PSEntity:

    nb = 42
    originalnb = 33

    def __init__(self):
        self.scores = []
        self.v = []
        for i in range(PSEntity.nb):
            self.v.append("")
        for i in range(38, 42):
            self.v[i] = 0
        self.v[7] = 0
        self.v[33] = self.updateid()
        self.v[34] = 0

    @property
    def nom(self):
        return self.v[1]

    @property
    def prenom(self):
        return self.v[2]

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
    def id(self):
        return f"{self.cp}_{self.nom}_{self.prenom}_{self.commune}_{self.adresse3}".replace(" ", "_")

    def updateid(self):
        self.v[33] = self.id

    @property
    def score(self):
        if len(self.scores) == 0:
            return 0
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

    def __repr__(self):
        return f"{self.id} [{self.rownum}]"


if __name__ == '__main__':
    e = PSEntity()
    print(e)