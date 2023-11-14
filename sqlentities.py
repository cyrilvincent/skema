from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Integer, String, Float, CHAR, create_engine, Column, ForeignKey, Boolean, UniqueConstraint, \
    Table, Index, Date
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
#              -? profession
#              -? mode_exercice
#              -? famille_acte
#              -1 cabinet
# etab -1 adresse_raw
#      *-* date_source
# personne_activite *-* pa_adresse
#                   *-* code_profession *-* profession
#                   *-* diplome *-* profession
# /!\ FK != INDEX automatique, testé sur tarif


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
    is_lieu_dit = Column(Boolean, nullable=False)
    __table_args__ = (Index('BAN_cp_nom_commune_ix', 'code_postal', 'nom_commune'),
                      Index('BAN_cp_nom_commune_nom_voie_ix', 'nom_commune', 'nom_voie'),
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
    rue1 = Column(String(255))
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
    iris = Column(String(9))
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
                                 Column('date_source_id', ForeignKey('date_source.id'), primary_key=True, index=True)
                                 )

tarif_datesource = Table('tarif_date_source', Base.metadata,
                         Column('tarif_id', ForeignKey('tarif.id'), primary_key=True),
                         Column('date_source_id', ForeignKey('date_source.id'), primary_key=True, index=True)
                         )

personne_activite_pa_adresse = Table('personne_activite_pa_adresse', Base.metadata,
                                     Column('personne_activite_id', ForeignKey('personne_activite.id'),
                                            primary_key=True),
                                     Column('pa_adresse_id', ForeignKey('pa_adresse.id'), primary_key=True)
                                     )

personne_activite_code_profession = Table('personne_activite_code_profession', Base.metadata,
                                     Column('personne_activite_id', ForeignKey('personne_activite.id'),
                                            primary_key=True),
                                     Column('code_profession_id', ForeignKey('code_profession.id'), primary_key=True)
                                     )

personne_activite_diplome = Table('personne_activite_diplome', Base.metadata,
                                     Column('personne_activite_id', ForeignKey('personne_activite.id'),
                                            primary_key=True),
                                     Column('diplome_id', ForeignKey('diplome.id'), primary_key=True)
                                     )

profession_diplome = Table('profession_diplome', Base.metadata,
                                     Column('profession_id', ForeignKey('profession.id'),
                                            primary_key=True),
                                     Column('diplome_id', ForeignKey('diplome.id'), primary_key=True)
                                     )

profession_code_profession = Table('profession_code_profession', Base.metadata,
                                     Column('profession_id', ForeignKey('profession.id'),
                                            primary_key=True),
                                     Column('code_profession_id', ForeignKey('code_profession.id'), primary_key=True)
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
    nofinesset = Column(String(10), nullable=False, unique=True)
    nofinessej = Column(String(10), nullable=False)
    rs = Column(String(50), nullable=False)
    rslongue = Column(String(255), nullable=False)
    complrs = Column(String(255))
    mft = Column(String(10))
    categetab = Column(Integer)
    categretab = Column(Integer)
    sph = Column(Integer)
    telephone = Column(String(20))
    telecopie = Column(String(20))
    siret = Column(String(15))
    dateautor = Column(String(50))
    dateouvert = Column(String(50))
    datemaj = Column(String(50))
    codeape = Column(String(50))  # Pas dans tous
    cog = Column(String(5))
    adresse_raw: AdresseRaw = relationship("AdresseRaw")
    adresse_raw_id = Column(Integer, ForeignKey('adresse_raw.id'), nullable=False)
    date_sources: List[DateSource] = relationship("DateSource",
                                                  secondary=etablissement_datesource, backref="etablissements")

    def __repr__(self):
        return f"{self.id} {self.rs}"

    def equals(self, other):
        return self.nofinesset == other.nofinesset and self.nofinessej == other.nofinessej \
               and self.rs == other.rs and self.rslongue == other.rslongue \
               and self.complrs == other.complrs and self.mft == other.mft \
               and self.sph == other.sph and self.siret == other.siret \
               and self.telephone == other.telephone and self.datemaj == other.datemaj \
               and self.codeape == other.codeape
                # and self.categetab == other.categetab and self.categretab == other.categretab \
                # and self.cog == other.cog \


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
    genre = Column(CHAR(1))
    key = Column(String(255), nullable=False, unique=True)
    has_inpp = Column(Boolean, nullable=False)
    nom = Column(String(255), nullable=False)
    prenom = Column(String(255))
    rule_nb = Column(Integer)

    # ps_cabinet_date_sources by backref
    # tarifs by backref

    def __repr__(self):
        return f"{self.id} {self.key} {self.nom} {self.prenom}"

    def equals(self, other):
        return self.genre == other.genre


class PSCabinetDateSource(Base):
    __tablename__ = "ps_cabinet_date_source"
    id = Column(Integer, primary_key=True)
    ps: PS = relationship("PS", backref="ps_cabinet_date_sources")
    ps_id = Column(Integer, ForeignKey('ps.id'), nullable=False)
    cabinet: Cabinet = relationship("Cabinet")
    cabinet_id = Column(Integer, ForeignKey('cabinet.id'), nullable=False)
    date_source: DateSource = relationship("DateSource")
    date_source_id = Column(Integer, ForeignKey('date_source.id'), nullable=False, index=True)

    __table_args__ = (UniqueConstraint('ps_id', 'cabinet_id', 'date_source_id'),)

    @property
    def key(self):
        return self.ps_id, self.cabinet_id, self.date_source_id

    def __repr__(self):
        return f"{self.id} {self.ps_id} {self.cabinet_id} {self.date_source_id}"


class Convention(Base):
    __tablename__ = "convention"

    id = Column(Integer, primary_key=True)
    code = Column(CHAR(2), nullable=False, unique=True)
    libelle = Column(String(100), nullable=False)

    def __repr__(self):
        return f"{self.id} {self.code}"


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

    # backref: diplomes
    # backref: code_professions

    def __repr__(self):
        return f"{self.id} {self.libelle}"


class ModeExercice(Base):
    __tablename__ = "mode_exercice"

    id = Column(Integer, primary_key=True)
    libelle = Column(String(50), nullable=False)

    def __repr__(self):
        return f"{self.id} {self.libelle}"


class FamilleActe(Base):
    __tablename__ = "famille_acte"

    id = Column(Integer, primary_key=True)
    libelle = Column(String(255), nullable=False)

    def __repr__(self):
        return f"{self.id} {self.libelle}"


class Tarif(Base):
    __tablename__ = "tarif"

    id = Column(Integer, primary_key=True)
    profession: Profession = relationship("Profession")
    profession_id = Column(Integer, ForeignKey('profession.id'))
    mode_exercice: ModeExercice = relationship("ModeExercice")
    mode_exercice_id = Column(Integer, ForeignKey('mode_exercice.id'))
    nature: Nature = relationship("Nature")
    nature_id = Column(Integer, ForeignKey('nature.id'), nullable=False)
    convention: Convention = relationship("Convention")
    convention_id = Column(Integer, ForeignKey("convention.id"), nullable=False)
    option_contrat = Column(Boolean)
    vitale = Column(Boolean)
    code = Column(String(50), nullable=False)
    ps: PS = relationship("PS", backref="tarifs")
    ps_id = Column(Integer, ForeignKey('ps.id'), nullable=False, index=True)
    cabinet: Cabinet = relationship("Cabinet")
    cabinet_id = Column(Integer, ForeignKey('cabinet.id'), nullable=False)
    famille_acte: FamilleActe = relationship("FamilleActe")
    famille_acte_id = Column(Integer, ForeignKey('famille_acte.id'))
    date_sources = relationship("DateSource", secondary=tarif_datesource, backref="tarifs")
    montant = Column(Float)
    borne_inf = Column(Float)
    borne_sup = Column(Float)
    montant_2 = Column(Float)
    borne_inf_2 = Column(Float)
    borne_sup_2 = Column(Float)
    montant_imagerie = Column(Float)
    borne_inf_imagerie = Column(Float)
    borne_sup_imagerie = Column(Float)
    montant_anesthesie = Column(Float)
    borne_inf_anesthesie = Column(Float)
    borne_sup_anesthesie = Column(Float)
    montant_cec = Column(Float)
    borne_inf_cec = Column(Float)
    borne_sup_cec = Column(Float)

    @property
    def key(self):
        return (None if self.ps is None else self.ps.id,
                None if self.profession is None else self.profession.id,
                None if self.mode_exercice is None else self.mode_exercice.id,
                self.nature.id, self.convention.id, self.option_contrat, self.vitale, self.code,
                None if self.famille_acte is None else self.famille_acte.id, self.montant,
                self.borne_inf, self.borne_sup, self.montant_2, self.borne_inf_2, self.borne_sup_2,
                self.montant_imagerie, self.borne_inf_imagerie, self.borne_sup_imagerie, self.montant_anesthesie,
                self.borne_inf_anesthesie, self.borne_sup_anesthesie, self.montant_cec, self.borne_inf_cec,
                self.borne_sup_cec)

    def __repr__(self):
        return f"{self.id} {self.profession} {self.montant}"


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


class PersonneActivite(Base):
    __tablename__ = "personne_activite"

    id = Column(Integer, primary_key=True)
    inpp = Column(String(12), nullable=False, unique=True)
    nom = Column(String(255), nullable=False)
    prenom = Column(String(255))

    # backref pa_adresses
    # backref code_professions
    # backref diplomes

    def __repr__(self):
        return f"{self.id} {self.nom} {self.prenom}"


class PAAdresse(Base):
    __tablename__ = "pa_adresse"

    id = Column(Integer, primary_key=True)
    numero = Column(Integer)
    rue = Column(String(255))
    cp = Column(Integer, nullable=False)
    commune = Column(String(255), nullable=False)
    code_commune = Column(String(5))
    dept: Dept = relationship("Dept")
    dept_id = Column(Integer, ForeignKey('dept.id'), nullable=False, index=True)
    personne_activites: List[PersonneActivite] = relationship("PersonneActivite",
                                                              secondary=personne_activite_pa_adresse,
                                                              backref="pa_adresses")

    __table_args__ = (UniqueConstraint('numero', 'rue', 'cp', 'commune'),)

    @property
    def key(self):
        return self.numero, self.rue, self.cp, self.commune

    def __repr__(self):
        return f"{self.id} {self.numero} {self.rue} {self.cp} {self.commune}"


class Diplome(Base):
    __tablename__ = "diplome"

    id = Column(Integer, primary_key=True)
    code_type_diplome = Column(String(10), nullable=False)
    libelle_type_diplome = Column(String(255), nullable=False)
    code_diplome = Column(String(10), nullable=False, unique=True)
    libelle_diplome = Column(String(255), nullable=False)
    is_savoir_faire = Column(Boolean, nullable=False)

    personne_activites: List[PersonneActivite] = relationship("PersonneActivite",
                                                              secondary=personne_activite_diplome,
                                                              backref="diplomes")

    professions: List[Profession] = relationship("Profession",
                                                              secondary=profession_diplome,
                                                              backref="diplomes")

    @property
    def key(self):
        return self.code_diplome

    def __repr__(self):
        return f"{self.id} {self.code_diplome}"


class INPPDiplome(Base):
    __tablename__ = "inpp_diplome"

    id = Column(Integer, primary_key=True)
    inpp = Column(String(12), nullable=False)
    diplome_id = Column(Integer, ForeignKey('diplome.id'), nullable=False)
    diplome: Diplome = relationship("Diplome")

    __table_args__ = (UniqueConstraint('inpp', 'diplome_id'),)

    @property
    def key(self):
        return self.inpp, self.diplome.key

    def __repr__(self):
        return f"{self.id} {self.inpp} {self.diplome_id}"

class CodeProfession(Base):
    __tablename__ = "code_profession"

    id = Column(Integer, primary_key=True)
    libelle = Column(String(50), nullable=False)

    personne_activites: List[PersonneActivite] = relationship("PersonneActivite",
                                                              secondary=personne_activite_code_profession,
                                                              backref="code_professions")

    professions: List[Profession] = relationship("Profession",
                                                              secondary=profession_code_profession,
                                                              backref="code_professions")

    def __repr__(self):
        return f"{self.id} {self.libelle}"


class PSMerge(Base):
    __tablename__ = "ps_merge"

    id = Column(Integer, primary_key=True)
    key = Column(String(255), nullable=False, unique=True, index=True)
    inpp = Column(String(12), nullable=False)

    def __repr__(self):
        return f"{self.id} {self.key} {self.inpp}"

class OD(Base):
    __tablename__ = "od"

    id = Column(Integer, primary_key=True)
    com1 = Column(String(5), nullable=False)
    com2 = Column(String(5), nullable=False)
    km = Column(Float, nullable=False)
    hc = Column(Float, nullable=False)
    hp = Column(Float, nullable=False)

    __table_args__ = (UniqueConstraint('com1', 'com2'),)

    @property
    def key(self):
        return self.com1, self.com2

    def equals(self, other) -> bool:
        return self.com1 == other.com1 and self.com2 == other.com2 and self.km == other.km\
               and self.hc == other.hc and self.hp == other.hp

    def __repr__(self):
        return f"{self.id} {self.com1} {self.com2} {self.km}"

class CPInsee(Base):
    __tablename__ = "cp_insee"

    id = Column(Integer, primary_key=True)
    cp = Column(Integer, nullable=False, index=True)
    libelle = Column(String(255), nullable=False)
    insee = Column(String(5), nullable=False)
    is_cedex = Column(Boolean, nullable=False)
    commune = Column(String(255), nullable=False)
    departement = Column(String(255), nullable=False)
    epci = Column(String(255), nullable=False)
    region = Column(String(255), nullable=False)

    __table_args__ = (UniqueConstraint('cp', 'insee'),)

    @property
    def key(self):
        return self.cp, self.insee

    def __repr__(self):
        return f"{self.id} {self.cp} {self.insee}"

class Personne(Base):
    __tablename__ = "personne"

    id = Column(Integer, primary_key=True)
    inpp = Column(String(12), nullable=False, unique=True)
    nom = Column(String(255), nullable=False)
    prenom = Column(String(255))
    civilite = Column(String(3))
    nature = Column(String(2))
    code_nationalite = Column(String(5))
    date_acquisition_nationalite = Column(Date())
    date_effet = Column(Date())
    date_maj = Column(Date())

    # TODO backref pa_adresses
    # TODO backref code_professions
    # TODO backref diplomes

    def equals(self, other):
        return self.inpp == other.inpp and self.nom == other.nom and self.civilite == other.civilite \
            and self.nature == other.nature and self.code_nationalite == other.code_nationalite \
            and self.date_acquisition_nationalite == other.date_acquisition_nationalite \
            and self.date_effet == other.date_effet and self.date_maj == other.date_maj

    def __repr__(self):
        return f"{self.id} {self.nom} {self.prenom}"
