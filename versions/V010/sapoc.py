import sqlalchemy.ext.declarative
import sqlalchemy.orm
import sqlalchemy
import csv

Base = sqlalchemy.ext.declarative.declarative_base()


class Adresse(Base):
    __tablename__ = "adresse"

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, )
    adresseid = sqlalchemy.Column(sqlalchemy.String(25), unique=True)
    numero = sqlalchemy.Column(sqlalchemy.Integer, nullable=False)
    rep = sqlalchemy.Column(sqlalchemy.String(10))
    nom_voie = sqlalchemy.Column(sqlalchemy.String(255), nullable=False)
    code_postal = sqlalchemy.Column(sqlalchemy.Integer, nullable=False)
    code_insee = sqlalchemy.Column(sqlalchemy.String(5), nullable=False)
    nom_commune = sqlalchemy.Column(sqlalchemy.String(255), nullable=False)
    nom_ancienne_commune = sqlalchemy.Column(sqlalchemy.String(255))
    x = sqlalchemy.Column(sqlalchemy.Float, nullable=False)
    y = sqlalchemy.Column(sqlalchemy.Float, nullable=False)
    lon = sqlalchemy.Column(sqlalchemy.Float, nullable=False)
    lat = sqlalchemy.Column(sqlalchemy.Float, nullable=False)
    libelle_acheminement = sqlalchemy.Column(sqlalchemy.String(255), nullable=False)
    nom_afnor = sqlalchemy.Column(sqlalchemy.String(255), nullable=False)

    def __repr__(self):
        return f"Adresse {self.id} {self.numero} {self.nom_afnor} {self.code_postal} {self.nom_commune}"


if __name__ == '__main__':
    print(sqlalchemy.__version__)

    uri = "postgresql://postgres:sa@localhost/postgres"
    engine = sqlalchemy.create_engine(uri, echo=True)
    Base.metadata.create_all(engine)

    Session = sqlalchemy.orm.sessionmaker(bind=engine, autocommit=False, autoflush=False)
    session = Session()

    # with open("data/adresse/adresses-38.csv", encoding="utf8") as f:
    #     reader = csv.DictReader(f, delimiter=';')
    #     for row in reader:
    #         a = Adresse()
    #         a.id = None
    #         a.adresseid = row["id"]
    #         a.numero = int(row["numero"])
    #         rep = row["rep"]
    #         if rep != "":
    #             a.rep = rep
    #         a.nom_voie = row["nom_voie"]
    #         a.code_postal = int(row["code_postal"])
    #         a.code_insee = row["code_insee"]
    #         a.nom_commune = row["nom_commune"]
    #         nac = row["nom_ancienne_commune"]
    #         if nac != "":
    #             a.nom_ancienne_commune = nac
    #         a.x = float(row["x"])
    #         a.y = float(row["y"])
    #         a.lon = float(row["lon"])
    #         a.lat = float(row["lat"])
    #         a.libelle_acheminement = row["libelle_acheminement"]
    #         a.nom_afnor = row["nom_afnor"]
    #         session.add(a)
    #         session.commit()

    # res = session.query(Adresse).filter(Adresse.code_postal == 38250)
    # for a in res:
    #     print(a)
    res = session.query(Adresse).filter(sqlalchemy.and_(Adresse.code_postal == 38250, Adresse.nom_commune.like("Villard%")))
    for a in res:
        print(a)



