from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Integer, String, Float, CHAR, create_engine, Column, ForeignKey, Boolean, UniqueConstraint
from sqlalchemy.orm import sessionmaker, relationship, Session
from sqlalchemy.engine import Engine
from typing import Optional
import config


Base = declarative_base()


class Context:

    def __init__(self):
        self.engine: Optional[Engine] = None
        self.session: Optional[Session] = None

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

# ps 1-* ps_row -1 adresse_raw -1 adresse_norm -? osm -1 dept NB:adresse_row contient adresse1234 avant normalisation
#                                              -? ban -1 dept
#                                              -1 dept
#                                              -? source
#                              -1 dept
#               *-* date_source
# etab -1 adresse_raw
#      *-* date_source
# Voir dbeaver


class Dept(Base):
    __tablename__ = "dept"

    id = Column(Integer, primary_key=True, )
    num = Column(CHAR(2), nullable=False, unique=True)

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

    # Indexes : code_postal
    #           code_insee
    #           nom_commune
    #           code_postale nomcommune
    #           nomcommune nom_voie
    #           dept_id


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
    name = Column(String(10), nullable=False, unique=True)  # BAN OSM Etab Manually

    def __repr__(self):
        return f"Source {self.id} {self.name}"


class DateSource(Base):
    __tablename__ = "date_source"
    id = Column(Integer, primary_key=True)
    mois = Column(Integer)
    annee = Column(Integer, nullable=False)
    __table_args__ = (UniqueConstraint('mois', 'annee'),)

    def __repr__(self):
        return f"DateSource {self.id} {self.mois} {self.annee}"

    # Indexes : annee
    #           mois annee


class AdresseNorm(Base):
    __tablename__ = "adresse_norm"

    id = Column(Integer, primary_key=True)
    adresse = Column(String(255), nullable=False) # Contient le num
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
    __table_args__ = (UniqueConstraint('adresse', 'cp', 'commune'),)

    def __repr__(self):
        return f"AdresseNorm {self.id} {self.adresse} {self.cp} {self.commune} {self.source} {self.lon} {self.lat}"


class AdresseRaw(Base):
    __tablename__ = "adresse_raw"

    id = Column(Integer, primary_key=True)
    numero = Column(Integer)
    adresse2 = Column(String(255))
    adresse3 = Column(String(255), nullable=False)
    adresse4 = Column(String(255))
    cp = Column(String(5), nullable=False)
    commune = Column(String(255), nullable=False)
    adresse_norm: AdresseNorm = relationship("AdresseNorm")
    adresse_norm_id = Column(Integer, ForeignKey('adresse_norm.id'))
    dept: Dept = relationship("Dept")
    dept_id = Column(Integer, ForeignKey('dept.id'), nullable=False)
    __table_args__ = (UniqueConstraint('adresse2', 'adresse3', 'adresse4', 'cp', 'commune'),)

    def __repr__(self):
        return f"AdresseRaw {self.id} {self.adresse2} {self.adresse3} {self.adresse4} {self.cp} {self.commune}"

    # Index : cp
    #         commune
