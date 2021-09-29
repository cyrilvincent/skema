from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Integer, String, Float, CHAR, create_engine, Column, ForeignKey, Boolean
from sqlalchemy.orm import sessionmaker, relationship
import config

Base = declarative_base()


class Context:

    def __init__(self):
        self.engine = None
        self.session: sessionmaker = None

    def create_engine(self, echo=False, create_all=True):
        self.engine = create_engine(config.connection_string, echo=echo)
        if create_all:
            Base.metadata.create_all(self.engine)

    def create_session(self):
        Session = sessionmaker(bind=self.engine, autocommit=False, autoflush=False)
        self.session = Session()

    def create(self, echo=False, create_all=True):
        self.create_engine(echo, create_all)
        self.create_session()

# ps 1-* ps_row *-1 ps_adresse -? osm -1 dept
#                              -? ban -1 dept
#               -? source
# etab *-1 ps_adresse
# etab -? source
# Voir dbeaver


class Dept(Base):
    __tablename__ = "dept"

    id = Column(Integer, primary_key=True, )
    num = Column(CHAR(2), nullable=False)

    def __repr__(self):
        return f"Dept {self.id} {self.num}"


class BAN(Base):
    __tablename__ = "ban"

    id = Column(Integer, primary_key=True, )
    adresse_id = Column(String(50), unique=True)
    numero = Column(Integer)
    rep = Column(String(50))
    nom_voie = Column(String(255))
    code_postal = Column(Integer, nullable=False)
    code_insee = Column(String(5), nullable=False)
    nom_commune = Column(String(255), nullable=False)
    nom_ancienne_commune = Column(String(255))
    lon = Column(Float, nullable=False)
    lat = Column(Float, nullable=False)
    libelle_acheminement = Column(String(255))
    nom_afnor = Column(String(255))
    dept: Dept = relationship("Dept")
    dept_id = Column(Integer, ForeignKey('dept.id'), nullable=False)
    is_lieu_dit = Column(Boolean)

    def __repr__(self):
        return f"Adresse {self.id} {self.numero} {self.nom_voie} {self.code_postal} {self.nom_commune}"


class OSM(Base):
    __tablename__ = "osm"

    id = Column(Integer, primary_key=True)
    lon = Column(Float, nullable=False)
    lat = Column(Float, nullable=False)
    display_name = Column(String(255), nullable=False)
    score = Column(Float, nullable=False)


    def __repr__(self):
        return f"OSM {self.id} {self.id} {self.display_name} {self.lon} {self.lat}"


class Source(Base):
    __tablename__ = "source"

    id = Column(Integer, primary_key=True)
    name = Column(String(10), nullable=False) #BAN OSM Etab Manually


class PSAdresse(Base):
    __tablename__ = "ps_adresse"

    id = Column(Integer, primary_key=True)
    adresse1 = Column(String(255))
    adresse2 = Column(String(255))
    adresse3 = Column(String(255), nullable=False)
    adresse4 = Column(String(255))
    cp = Column(String(5), nullable=False)
    commune = Column(String(255), nullable=False)
    osm: OSM = relationship("OSM")
    osm_id = Column(Integer, ForeignKey('osm.id'))
    ban: BAN = relationship("BAN")
    ban_id = Column(Integer, ForeignKey('ban.id'))
    source: Source = relationship("Source")
    source_id = Column(Integer, ForeignKey('source.id'))
    lon = Column(Float)
    lat = Column(Float)
    score = Column(Float)
    dept: Dept = relationship("Dept")
    dept_id = Column(Integer, ForeignKey('dept.id'), nullable=False)

    def __repr__(self):
        return f"PSAdresse {self.id} {self.adresse3} {self.cp} {self.commune} {self.source} {self.lon} {self.lat}"