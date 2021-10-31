from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Integer, String, Float, CHAR, create_engine, Column, ForeignKey, Boolean, UniqueConstraint, \
    Table, Index
from sqlalchemy.orm import sessionmaker, relationship, Session
from sqlalchemy.engine import Engine
from typing import Optional, List
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

    def create_session(self, expire_on_commit=True):
        Session = sessionmaker(bind=self.engine, autocommit=False, autoflush=False, expire_on_commit=expire_on_commit)
        self.session = Session()

    def get_session(self, expire_on_commit=True):
        Session = sessionmaker(bind=self.engine, autocommit=False, autoflush=False, expire_on_commit=expire_on_commit)
        return Session()

    def create(self, echo=False, create_all=True, expire_on_commit=True):
        self.create_engine(echo, create_all)
        self.create_session(expire_on_commit)

    def db_size(self):
        with self.engine.connect() as conn:
            sql = f"select pg_database_size('{self.db_name}')"
            res = conn.execute(sql)
            row = res.fetchone()
            return row[0] / 2 ** 20

# ps -* ps_cabinet_date_source -1 cabinet -1 adresse_raw -1 adresse_norm -? osm -1 dept
#                                                                        -? ban -1 dept
#                                                                        -1 dept
#                                                                        -? source
#                                                        -1 dept
#                              -1 date_source
#    1-* tarif *-* date_source
#              -1 profession -* tarif_stats *-* date_source
#                                           -? dept (si None = France)
# etab -1 adresse_raw
#      *-* date_source


class Dept(Base):
    __tablename__ = "dept"

    id = Column(Integer, primary_key=True, )
    num = Column(CHAR(2), nullable=False, unique=True)

    # backref: bans

    def __repr__(self):
        return f"{self.id}"


class BAN(Base):
    __tablename__ = "ban"

    id = Column(Integer, primary_key=True, )
    adresse_id = Column(String(50), unique=True)
    numero = Column(Integer)
    rep = Column(String(50))
    nom_voie = Column(String(255), nullable=False)
    code_postal = Column(Integer, nullable=False, index=True)
    code_insee = Column(String(5), nullable=False, index=True)
    nom_commune = Column(String(255), nullable=False, index=True)
    nom_ancienne_commune = Column(String(255))
    lon = Column(Float, nullable=False)
    lat = Column(Float, nullable=False)
    libelle_acheminement = Column(String(255))
    nom_afnor = Column(String(255))
    dept: Dept = relationship("Dept", backref="bans")
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
    adresse = Column(String(255), nullable=False)
    cp = Column(Integer)

    # backref bans

    def __repr__(self):
        return f"{self.id} {self.adresse}"


class Source(Base):
    __tablename__ = "source"

    id = Column(Integer, primary_key=True)
    name = Column(String(10), nullable=False, unique=True)

    def __repr__(self):
        return f"{self.id} {self.name}"


class AdresseNorm(Base):
    __tablename__ = "adresse_norm"

    id = Column(Integer, primary_key=True)
    numero = Column(Integer)
    rue1 = Column(String(255))  # enlever le not null
    rue2 = Column(String(255))
    cp = Column(Integer, nullable=False)
    commune = Column(String(255), nullable=False)
    osm: OSM = relationship("OSM", backref="bans")
    osm_id = Column(Integer, ForeignKey('osm.id'))
    osm_score = Column(Float)
    ban: BAN = relationship("BAN")
    ban_id = Column(Integer, ForeignKey('ban.id'))
    ban_score = Column(Float)
    source: Source = relationship("Source")
    source_id = Column(Integer, ForeignKey('source.id'))
    lon = Column(Float)
    lat = Column(Float)
    score = Column(Float)
    dept: Dept = relationship("Dept")
    dept_id = Column(Integer, ForeignKey('dept.id'), nullable=False, index=True)
    __table_args__ = (UniqueConstraint('numero', 'rue1', 'rue2', 'cp', 'commune'),)

    def __repr__(self):
        return f"{self.id} {self.numero} {self.rue1} {self.rue2} {self.cp} {self.commune}"

    @property
    def key(self):
        return self.numero, self.rue1, self.rue2, self.cp, self.commune

    def equals(self, other):
        return self.key == other.key


class AdresseRaw(Base):
    __tablename__ = "adresse_raw"

    id = Column(Integer, primary_key=True)
    adresse2 = Column(String(255))
    adresse3 = Column(String(255))  # Main
    adresse4 = Column(String(255))
    cp = Column(Integer, nullable=False, index=True)
    commune = Column(String(255), nullable=False, index=True)
    adresse_norm: AdresseNorm = relationship("AdresseNorm")
    adresse_norm_id = Column(Integer, ForeignKey('adresse_norm.id'))
    dept: Dept = relationship("Dept")
    dept_id = Column(Integer, ForeignKey('dept.id'), nullable=False, index=True)
    __table_args__ = (UniqueConstraint('adresse2', 'adresse3', 'adresse4', 'cp', 'commune'),
                      Index('adresse_raw_cp_commune_ix', 'cp', 'commune'),
                      Index('adresse_raw_adresse3_cp_commune_ix', 'adresse3', 'cp', 'commune'),
                      )

    @property
    def key(self):
        return self.adresse2, self.adresse3, self.adresse4, self.cp, self.commune

    def __repr__(self):
        return f"{self.id} {self.adresse2} {self.adresse3} {self.adresse4} {self.cp} {self.commune}"

    def equals(self, other):
        return self.key == other.key


etablissement_datesource = Table('etablissement_date_source', Base.metadata,
                                 Column('etablissement_id', ForeignKey('etablissement.id'), primary_key=True),
                                 Column('date_source_id', ForeignKey('date_source.id'), primary_key=True)
                                 )

tarif_datesource = Table('tarif_date_source', Base.metadata,
                         Column('tarif_id', ForeignKey('tarif.id'), primary_key=True),
                         Column('date_source_id', ForeignKey('date_source.id'), primary_key=True)
                         )


class DateSource(Base):
    __tablename__ = "date_source"
    id = Column(Integer, primary_key=True)
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
    numero = Column(String(50), nullable=False, unique=True)
    type: EtablissementType = relationship("EtablissementType")
    type_id = Column(Integer, ForeignKey('etablissement_type.id'), nullable=False)
    telephone = Column(String(20))
    mail = Column(String(50))
    nom2 = Column(String(255), nullable=False)
    url = Column(String(255))
    adresse_raw: AdresseRaw = relationship("AdresseRaw")
    adresse_raw_id = Column(Integer, ForeignKey('adresse_raw.id'), nullable=False)
    date_sources: List[DateSource] = relationship("DateSource",
                                                  secondary=etablissement_datesource, backref="etablissements")

    def __repr__(self):
        return f"{self.id} {self.nom}"

    def equals(self, other):
        return self.nom == other.nom and self.numero == other.numero and self.telephone == other.telephone \
               and self.mail == other.mail and self.url == other.url


class Cabinet(Base):
    __tablename__ = "cabinet"

    id = Column(Integer, primary_key=True)
    nom = Column(String(255), nullable=False)
    key = Column(String(255), nullable=False, index=True, unique=True)
    telephone = Column(String(15))
    adresse_raw: AdresseRaw = relationship("AdresseRaw")
    adresse_raw_id = Column(Integer, ForeignKey('adresse_raw.id'), nullable=False)

    def __repr__(self):
        return f"{self.id} {self.key}"


class PS(Base):
    __tablename__ = "ps"

    id = Column(Integer, primary_key=True)
    genre = Column(CHAR(1), nullable=False)
    key = Column(String(255), nullable=False, unique=True, index=True)
    nom = Column(String(255), nullable=False)
    prenom = Column(String(255))

    # ps_cabinet_date_sources by backref
    # tarifs by backref

    def __repr__(self):
        return f"{self.id} {self.key} {self.nom} {self.prenom}"


class PSCabinetDateSource(Base):
    __tablename__ = "ps_cabinet_date_source"
    id = Column(Integer, primary_key=True)
    ps: PS = relationship("PS", backref="ps_cabinet_date_sources")
    ps_id = Column(Integer, ForeignKey('ps.id'), nullable=False)
    cabinet: Cabinet = relationship("Cabinet")
    cabinet_id = Column(Integer, ForeignKey('cabinet.id'), nullable=False)
    date_source: DateSource = relationship("DateSource")
    date_source_id = Column(Integer, ForeignKey('date_source.id'), nullable=False)

    __table_args__ = (UniqueConstraint('ps_id', 'cabinet_id', 'date_source_id'),)

    @property
    def key(self):
        return self.ps_id, self.cabinet_id, self.date_source_id

    def __repr__(self):
        return f"{self.id} {self.ps_id} {self.cabinet_id} {self.date_source_id}"


class Convention(Base):
    __tablename__ = "convention"

    id = Column(Integer, primary_key=True)
    code = Column(CHAR(2), nullable=False)
    libelle = Column(String(100), nullable=False)

    def __repr__(self):
        return f"{self.id} {self.libelle}"


class Nature(Base):
    __tablename__ = "nature"

    id = Column(Integer, primary_key=True)
    libelle = Column(String(50), nullable=False)

    def __repr__(self):
        return f"{self.id} {self.libelle}"


class Profession(Base):
    __tablename__ = "profession"

    id = Column(Integer, primary_key=True)
    libelle = Column(String(50), nullable=False)
    annexe = Column(Boolean, nullable=False)

    def __repr__(self):
        return f"{self.id} {self.libelle}"


class TarifStats(Base):
    __tablename__ = "tarif_stats"

    id = Column(Integer, primary_key=True)
    moy = Column(Float, nullable=False)
    min = Column(Float)
    max = Column(Float)
    dept: Dept = relationship("Dept")
    dept_id = Column(Integer, ForeignKey('dept.id'), index=True)
    profession: Profession = relationship("Profession", backref="tarif_statss")
    profession_id = Column(Integer, ForeignKey('profession.id'))

    # TODO *-* DateSource

    # __table_args__ = (UniqueConstraint('profession_id', 'dept_id', "date_source_id"),)

    def __repr__(self):
        return f"{self.id} {self.moyenne}"


class Tarif(Base):
    __tablename__ = "tarif"

    id = Column(Integer, primary_key=True)
    profession: Profession = relationship("Profession")
    profession_id = Column(Integer, ForeignKey('profession.id'))
    nature: Nature = relationship("Nature")
    nature_id = Column(Integer, ForeignKey('nature.id'), nullable=False)
    convention: Convention = relationship("Convention")
    convention_id = Column(Integer, ForeignKey("convention.id"), nullable=False)
    option_contrat = Column(Boolean)
    vitale = Column(Boolean)
    code = Column(String(50), nullable=False)
    famille = Column(String(50))
    ps: PS = relationship("PS", backref="tarifs")
    ps_id = Column(Integer, ForeignKey('ps.id'), nullable=False)
    date_sources: List[DateSource] = relationship("DateSource",
                                                  secondary=tarif_datesource,
                                                  backref="tarifs")

    def __repr__(self):
        return f"{self.id} {self.profession}"


class Cedex(Base):
    __tablename__ = "cedex"

    id = Column(Integer, primary_key=True)
    cedex = Column(Integer, nullable=False, index=True)
    libelle = Column(String(255), nullable=False)
    insee = Column(CHAR(5), nullable=False)
    cp = Column(Integer)

    __table_args__ = (UniqueConstraint('cedex', 'insee'),)

    def __repr__(self):
        return f"{self.id} {self.cedex} => {self.cp}"
