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
        self.scores = []

    @property
    def score(self):
        return sum([s for s in self.scores]) / len(self.scores)