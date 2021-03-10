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

class PSEntity:

    def __init__(self):
        self.id = ""
        self.genre = ""
        self.prenom = ""
        self.nom = ""
        self.adresse1 = ""
        self.adresse2 = ""
        self.adresse3 = ""
        self.adresse4 = ""
        self.cp = 0
        self.commune = ""
        self.tel = ""
        self.matchstreet = ""
        self.num = 0
        self.scores = []
        self.adresseid = None
        self.values = []
        self.v10 = ""
        self.v11 = ""
        self.v12 = ""
        self.v13 = ""
        self.v14 = ""
        self.v15 = ""
        self.v16 = ""
        self.v17 = ""
        self.v18 = ""
        self.v19 = ""
        self.v20 = ""
        self.v21 = ""
        self.v22 = ""
        self.v23 = ""
        self.v24 = ""
        self.v25 = ""
        self.v26 = ""
        self.v27 = ""
        self.v28 = ""
        self.v29 = ""
        self.v30 = ""
        self.v31 = ""
        self.lon = 0
        self.lat = 0


    @property
    def score(self):
        return sum([s for s in self.scores]) / len(self.scores)