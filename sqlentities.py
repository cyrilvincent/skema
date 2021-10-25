from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Integer, String, Float, CHAR, create_engine, Column, ForeignKey, Boolean, UniqueConstraint, \
    Table, Index
from sqlalchemy.orm import sessionmaker, relationship, Session
from sqlalchemy.engine import Engine
from typing import Optional, List, Iterable
import config

Base = declarative_base()


class Context:

    def __init__(self, connection_string=config.connection_string):
        self.engine: Optional[Engine] = None
        self.session: Optional[Session] = None
        self.connection_string = connection_string

    @property
    def db_name(self):
        index = self.connection_string.rindex("/")
        return self.connection_string[index + 1:]

    def create_engine(self, echo=False, create_all=True):
        self.engine = create_engine(self.connection_string, echo=echo)
        if create_all:
            Base.metadata.create_all(self.engine)

    def create_session(self):
        Session = sessionmaker(bind=self.engine, autocommit=False, autoflush=False)
        self.session = Session()

    def get_session(self):
        return sessionmaker(bind=self.engine, autocommit=False, autoflush=False)

    def create(self, echo=False, create_all=True):
        self.create_engine(echo, create_all)
        self.create_session()

    def db_size(self):
        with self.engine.connect() as conn:
            sql = f"select pg_database_size('{self.db_name}')"
            res = conn.execute(sql)
            row = res.fetchone()
            return row[0] / 2 ** 20


# ps 1 -1 adresse_raw -1 adresse_norm -? osm -1 dept NB:adresse_raw contient adresse1234 avant normalisation
#                                     -? ban -1 dept
#                                     -1 dept
#                                     -? source
#                     -1 dept
#    1-* ps_row *-* date_source
# etab -1 adresse_raw
#      *-* date_source
# Voir dbeaver


class Dept(Base):
    __tablename__ = "dept"

    id = Column(Integer, primary_key=True, )
    num = Column(CHAR(2), nullable=False, unique=True)

    def __repr__(self):
        return f"{self.id}"


class BAN(Base):
    __tablename__ = "ban"

    id = Column(Integer, primary_key=True, )
    adresse_id = Column(String(50), unique=True)
    numero = Column(Integer)
    rep = Column(String(50))
    nom_voie = Column(String(255))
    code_postal = Column(Integer, nullable=False, index=True)
    code_insee = Column(String(5), nullable=False, index=True)
    nom_commune = Column(String(255), nullable=False, index=True)
    nom_ancienne_commune = Column(String(255))
    lon = Column(Float, nullable=False)
    lat = Column(Float, nullable=False)
    libelle_acheminement = Column(String(255))
    nom_afnor = Column(String(255))
    dept: Dept = relationship("Dept", lazy="joined")
    dept_id = Column(Integer, ForeignKey('dept.id'), nullable=False, index=True)
    is_lieu_dit = Column(Boolean)
    __table_args__ = (Index('BAN_cp_nom_commune_ix', 'code_postal', 'nom_commune'),
                      Index('BAN_cp_nom_commune_nom_voie', 'nom_commune', 'nom_voie'),
                      )

    def __repr__(self):
        return f"{self.id} {self.numero} {self.nom_voie} {self.code_postal} {self.nom_commune}"


class OSM(Base):
    __tablename__ = "osm"

    id = Column(Integer, primary_key=True)
    lon = Column(Float, nullable=False)
    lat = Column(Float, nullable=False)
    display_name = Column(String(255), nullable=False)
    score = Column(Float, nullable=False)

    def __repr__(self):
        return f"{self.id} {self.id} {self.display_name} {self.lon} {self.lat}"


class Source(Base):
    __tablename__ = "source"

    id = Column(Integer, primary_key=True)
    name = Column(String(10), nullable=False, unique=True)  # BAN OSM Etab Manually

    def __repr__(self):
        return f"{self.id} {self.name}"


class AdresseNorm(Base):
    __tablename__ = "adresse_norm"

    id = Column(Integer, primary_key=True)
    numero = Column(Integer)
    rue1 = Column(String(255)) # enlever le not null
    rue2 = Column(String(255))
    cp = Column(String(5), nullable=False)
    commune = Column(String(255), nullable=False)
    osm: OSM = relationship("OSM")
    osm_id = Column(Integer, ForeignKey('osm.id'))
    ban: BAN = relationship("BAN")
    ban_id = Column(Integer, ForeignKey('ban.id'))
    source: Source = relationship("Source", lazy="joined")
    source_id = Column(Integer, ForeignKey('source.id'))
    lon = Column(Float)
    lat = Column(Float)
    score = Column(Float)
    dept: Dept = relationship("Dept", lazy="joined")
    dept_id = Column(Integer, ForeignKey('dept.id'), nullable=False, index=True)
    __table_args__ = (UniqueConstraint('numero', 'rue1', 'rue2', 'cp', 'commune'),)

    def __repr__(self):
        return f"{self.id} {self.rue1} {self.rue2} {self.cp} {self.commune} {self.source} {self.lon} {self.lat}"

    @property
    def key(self):
        return self.numero, self.rue1, self.rue2, self.cp, self.commune

    def equals(self, other):
        return self.key == other.key


class AdresseRaw(Base):
    __tablename__ = "adresse_raw"

    id = Column(Integer, primary_key=True)
    adresse1 = Column(String(255))
    adresse2 = Column(String(255))
    adresse3 = Column(String(255)) # Main
    adresse4 = Column(String(255))
    cp = Column(String(5), nullable=False, index=True)
    commune = Column(String(255), nullable=False, index=True)
    adresse_norm: AdresseNorm = relationship("AdresseNorm", lazy="joined")
    adresse_norm_id = Column(Integer, ForeignKey('adresse_norm.id'))
    dept: Dept = relationship("Dept", lazy="joined")
    dept_id = Column(Integer, ForeignKey('dept.id'), nullable=False, index=True)
    __table_args__ = (UniqueConstraint('adresse1', 'adresse2', 'adresse3', 'adresse4', 'cp', 'commune'),
                      Index('adresse_raw_cp_commune_ix', 'cp', 'commune'),
                      Index('adresse_raw_adresse3_cp_commune_ix', 'adresse3', 'cp', 'commune'),
                      )

    @property
    def key(self):
        return self.adresse2, self.adresse3, self.adresse4, self.cp, self.commune

    def __repr__(self):
        return f"{self.id} {self.adresse2} {self.adresse3} {self.adresse4} {self.cp} {self.commune}"

    def equals(self, other):
        return self.key == other.key and self.adresse1 == other.adresse1


etablissement_datesource = Table('etablissement_date_source', Base.metadata,
                                 Column('etablissement_id', ForeignKey('etablissement.id'), primary_key=True),
                                 Column('date_source_id', ForeignKey('date_source.id'), primary_key=True)
                                 )

psrow_datesource = Table('ps_row_date_source', Base.metadata,
                         Column('ps_row_id', ForeignKey('ps_row.id'), primary_key=True),
                         Column('date_source_id', ForeignKey('date_source.id'), primary_key=True)
                         )


class DateSource(Base):
    __tablename__ = "date_source"
    id = Column(Integer, primary_key=True)  # format 2110
    mois = Column(Integer)
    annee = Column(Integer, nullable=False)
    __table_args__ = (UniqueConstraint('mois', 'annee'),)

    def __init__(self, annee, mois):
        self.annee = annee
        self.mois = mois
        self.id = annee * 100 + mois

    def __repr__(self):
        return f"{self.id}"


class EtablissementType(Base):
    __tablename__ = "etablissement_type"

    id = Column(Integer, primary_key=True)
    type = Column(String(50), nullable=False)

    def __repr__(self):
        return f"{self.id} {self.type}"


class Etablissement(Base):
    __tablename__ = "etablissement"

    id = Column(Integer, primary_key=True)
    nom = Column(String(255), nullable=False)
    numero = Column(String(50), nullable=False)
    type: EtablissementType = relationship("EtablissementType", lazy="joined")
    type_id = Column(Integer, ForeignKey('etablissement_type.id'), nullable=False)
    telephone = Column(String(20))
    mail = Column(String(50))
    nom2 = Column(String(255), nullable=False)
    url = Column(String(255))
    adresse_raw: AdresseRaw = relationship("AdresseRaw", lazy="joined")
    adresse_raw_id = Column(Integer, ForeignKey('adresse_raw.id'), nullable=False)
    date_sources: List[DateSource] = relationship("DateSource", lazy="joined",
                                                  secondary=etablissement_datesource,
                                                  backref="etablissements")
    __table_args__ = (UniqueConstraint('numero'),)

    def __repr__(self):
        return f"{self.id} {self.nom}"

    def equals(self, other):
        return self.nom == other.nom and self.numero == other.numero and self.telephone == other.telephone \
               and self.mail == other.mail and self.url == other.url


class PS(Base):
    __tablename__ = "ps"

    id = Column(Integer, primary_key=True)
    key = Column(String(255), nullable=False, unique=True)  # manque unique en base
    nom = Column(String(255), nullable=False)
    prenom = Column(String(255))
    telephone = Column(String(15))
    adresse_raw: AdresseRaw = relationship("AdresseRaw", lazy="joined")
    adresse_raw_id = Column(Integer, ForeignKey('adresse_raw.id'), nullable=False)  # Mettre le nullable=False en base

    def __repr__(self):
        return f"{self.id} {self.key} {self.nom} {self.prenom}"


class PSRow(Base):
    __tablename__ = "ps_row"

    id = Column(Integer, primary_key=True)
    profession = Column(String(255), nullable=False)
    ps: PS = relationship("PS", backref="psrows")
    ps_id = Column(Integer, ForeignKey('ps.id'), nullable=False)
    date_sources: List[DateSource] = relationship("DateSource", lazy="joined",
                                                  secondary=psrow_datesource,
                                                  backref="psrows")

    def __repr__(self):
        return f"{self.id} {self.profession}"

# backrefs vs backpopulate
# Le backref est plus simple à coder et génère automatiquement la propriété *s
# Par exemple ps.psrows est automatiquement généré
# Par contre pas d'intellisense sur les propriétés générées
