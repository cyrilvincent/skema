import datetime

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Integer, String, Float, CHAR, create_engine, Column, ForeignKey, Boolean, UniqueConstraint, \
    Table, Index, Date, DateTime
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
# personne 1-* exercice_pro *-1 code_profession *-* profession
#                           1-*(1) reference_ae
#                           1-*(1) savoir_faire_obtenu *-1 diplome
#                           *-1 categorie_pro
#          1-* activite *-1 structure
#                       *-1 code_profession *-* profession
#                       1-* coord
#          1-* diplome_obtenu *-1 diplome *-* profession (vue direct profession)
#          ?-*(1) etat_civil
#          1-* personne_langue *-1 langue
#          1-* personne_autorisation *-1 autorisation
#                                    *-1 code_profession
#          1-+ personne_attribution *-1 attribution
#          1-* coord *-1 adresse_norm
#                    *-1 activite *-1 code_profession *-* profession
# structure 1-* activite *-1 code_profession *-* profession
#                        1-* coord
#           1-* coord


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
    rpps_score = Column(Float)
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
                self.borne_sup_cec,
                self.cabinet_id) # Bug 3.1.2, must be -1

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
    code_diplome = Column(String(10), nullable=False, unique=True) #Warning: d'après la doc clé fonctionnelle est code_type_diplome + code_diplome
    libelle_diplome = Column(String(255), nullable=False)
    is_savoir_faire = Column(Boolean, nullable=False)
    personne_activites: List[PersonneActivite] = relationship("PersonneActivite",
                                                              secondary=personne_activite_diplome,
                                                              backref="diplomes")
    professions: List[Profession] = relationship("Profession",
                                                              secondary=profession_diplome,
                                                              backref="diplomes")

    # backref diplome_obtenus
    # backref savoir_faire_obtenus

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

    # backref exercice_pros
    # backref activites
    # backref personne_autorisations

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

    # backref exercice_pros
    # backref activites
    # backref diplome_obtenus
    # backref personne_attributions
    # backref coord_personnes

    def equals(self, other):
        return (self.inpp == other.inpp and self.nom == other.nom and self.prenom == other.prenom \
            and self.civilite == other.civilite \
            and self.nature == other.nature and self.code_nationalite == other.code_nationalite \
            and self.date_acquisition_nationalite == other.date_acquisition_nationalite \
            and self.date_effet == other.date_effet and self.date_maj == other.date_maj)

    def __repr__(self):
        return f"{self.id} {self.nom} {self.prenom}"

class CategorieJuridique(Base):
    __tablename__ = "categorie_juridique"

    id = Column(Integer, primary_key=True)
    libelle = Column(String(255), nullable=False)

    def __repr__(self):
        return f"{self.id} {self.libelle}"

class SecteurActivite(Base):
    __tablename__ = "secteur_activite"

    id = Column(Integer, primary_key=True)
    code = Column(String(4), nullable=False, unique=True)
    libelle = Column(String(255), nullable=False)

    # backref exercice_pros

    def __repr__(self):
        return f"{self.id} {self.code}"

class Structure(Base):
    __tablename__ = "structure"

    id = Column(Integer, primary_key=True)
    type = Column(String(2), nullable=False)
    id_technique = Column(String(25), nullable=False, unique=True)
    id_national = Column(String(15), nullable=False)
    siret = Column(String(14))
    siren = Column(String(9))
    finess = Column(String(9))
    finessj = Column(String(9))
    rpps = Column(String(14))
    adeli = Column(String(14))
    licence = Column(String(10))
    date_ouverture = Column(Date())
    date_fermeture = Column(Date())
    date_maj = Column(Date())
    ape = Column(String(10))
    categorie_juridique: CategorieJuridique = relationship("CategorieJuridique", backref="structures")
    categorie_juridique_id = Column(Integer, ForeignKey('categorie_juridique.id'), index=True)
    code_secteur_activite = Column(String(4))
    secteur_activite: SecteurActivite = relationship("SecteurActivite", backref="structures")
    secteur_activite_id = Column(Integer, ForeignKey('secteur_activite.id'), index=True)
    raison_sociale = Column(String(255))
    enseigne = Column(String(255))

    # backref activites

    @property
    def key(self):
        return self.id_technique

    def equals(self, other):
        return self.type == other.type and self.id_technique == other.id_technique \
            and self.id_national == other.id_national and self.siret == other.siret \
            and self.siren == other.siren and self.licence == other.licence \
            and self.date_fermeture == other.date_fermeture and self.date_maj == other.date_maj \
            and self.raison_sociale == other.raison_sociale and self.enseigne == other.enseigne

    def __repr__(self):
        return f"{self.id} {self.id_technique} {self.raison_sociale}"

class CategoriePro(Base):
    __tablename__ = "categorie_pro"

    id = Column(Integer, primary_key=True)
    code = Column(String(7), nullable=False, unique=True)
    libelle = Column(String(255), nullable=False)

    # backref exercice_pros

    def __repr__(self):
        return f"{self.id} {self.code}"

class ExercicePro(Base):
    __tablename__ = "exercice_pro"

    id = Column(Integer, primary_key=True)
    inpp = Column(String(12), nullable=False)
    personne: Personne = relationship("Personne", backref="exercice_pros")
    personne_id = Column(Integer, ForeignKey('personne.id'), nullable=False, index=True)
    nom = Column(String(255), nullable=False)
    prenom = Column(String(255))
    civilite = Column(String(3))
    code_profession: CodeProfession = relationship("CodeProfession", backref="exercice_pros")
    code_profession_id = Column(Integer, ForeignKey('code_profession.id'), nullable=False, index=True)
    code_categorie_pro = Column(String(5), nullable=False)
    categorie_pro: CategoriePro = relationship("CategoriePro", backref="exercice_pros")
    categorie_pro_id = Column(Integer, ForeignKey('categorie_pro.id'), nullable=False, index=True)
    date_fin = Column(Date())
    date_maj = Column(Date())
    date_effet = Column(Date())
    ae = Column(String(5))
    date_debut_inscription = Column(Date())
    departement_inscription = Column(String(3))
    __table_args__ = (UniqueConstraint('inpp', 'code_categorie_pro', 'code_profession_id'),)

    # backref reference_aes
    # backref savoir_faire_obtenus

    @property
    def key(self):
        return self.inpp, self.code_categorie_pro, self.code_profession_id

    def equals(self, other):
        return self.key == other.key and self.date_fin == other.date_fin and self.date_maj == other.date_maj

    def __repr__(self):
        return f"{self.id} {self.inpp} {self.categorie_pro} {self.code_profession_id}"

class Fonction(Base):
    __tablename__ = "fonction"

    id = Column(Integer, primary_key=True)
    code = Column(String(10), nullable=False, unique=True)
    libelle = Column(String(255), nullable=False)

    # backref activites

    def __repr__(self):
        return f"{self.id} {self.code}"

class Activite(Base):
    __tablename__ = "activite"

    id = Column(Integer, primary_key=True)
    activite_id = Column(String(15), nullable=False, unique=True)
    inpp = Column(String(12), nullable=False)
    personne: Personne = relationship("Personne", backref="activites")
    personne_id = Column(Integer, ForeignKey('personne.id'), nullable=False, index=True)
    id_technique_structure = Column(String(25))
    structure: Structure = relationship("Structure", backref="activites")
    structure_id = Column(Integer, ForeignKey('structure.id'), index=True)
    code_fonction = Column(String(10), nullable=False)
    fonction: Fonction = relationship("Fonction", backref="activites")
    fonction_id = Column(Integer, ForeignKey('fonction.id'), index=True, nullable=False)
    mode_exercice = Column(String(1), nullable=False)
    date_debut = Column(Date())
    date_fin = Column(Date())
    date_maj = Column(Date())
    region = Column(String(3))
    genre = Column(String(6), nullable=False)
    motif_fin = Column(String(10))
    section_tableau_pharmaciens = Column(String(10))
    sous_section_tableau_pharmaciens = Column(String(10))
    type_activite_liberale = Column(String(10))
    statut_ps_ssa = Column(String(10))
    statut_hospitalier = Column(String(10))
    code_profession: CodeProfession = relationship("CodeProfession", backref="activites")
    code_profession_id = Column(Integer, ForeignKey('code_profession.id'), nullable=False, index=True)
    categorie_pro = Column(String(5), nullable=False)

    # Backref coord_activites
    @property
    def key(self):
        return self.activite_id

    def equals(self, other):
        return self.key == other.key and self.date_fin == other.date_fin and self.date_maj == other.date_maj

    def __repr__(self):
        return f"{self.id} {self.activite_id}"


class DiplomeObtenu(Base):
    __tablename__ = "diplome_obtenu"

    id = Column(Integer, primary_key=True)
    inpp = Column(String(12), nullable=False)
    personne: Personne = relationship("Personne", backref="diplome_obtenus")
    personne_id = Column(Integer, ForeignKey('personne.id'), nullable=False, index=True)
    type_diplome = Column(String(10), nullable=False)
    code_diplome = Column(String(10), nullable=False)
    diplome: Diplome = relationship("Diplome", backref="diplome_obtenus")
    diplome_id = Column(Integer, ForeignKey('diplome.id'), nullable=False, index=True)
    date_obtention = Column(Date(), nullable=False)
    date_maj = Column(Date(), nullable=False)
    lieu_obtention = Column(String(10), nullable=False)
    numero = Column(String(50))
    __table_args__ = (UniqueConstraint('inpp', 'type_diplome', 'code_diplome', 'lieu_obtention'),)

    @property
    def key(self):
        return self.inpp, self.type_diplome, self.code_diplome, self.lieu_obtention

    def equals(self, other):
        return self.key == other.key and self.date_maj == other.date_maj and self.numero == other.numero

    def __repr__(self):
        return f"{self.id} {self.inpp} {self.code_diplome} {self.lieu_obtention}"

class EtatCivil(Base):
    __tablename__ = "etat_civil"

    id = Column(Integer, primary_key=True)
    inpp = Column(String(12), nullable=False, unique=True)
    personne: Personne = relationship("Personne", backref="etat_civils")
    personne_id = Column(Integer, ForeignKey('personne.id'), nullable=False, index=True)
    statut = Column(String(3), nullable=False)
    sexe = Column(String(1), nullable=False)
    nom = Column(String(255), nullable=False)
    nom_norm = Column(String(255), nullable=False)
    prenoms = Column(String(255), nullable=False)
    prenom_norm = Column(String(255), nullable=False)
    date_naissance = Column(Date(), nullable=False)
    lieu_naissance = Column(String(255))
    date_deces = Column(Date())
    date_effet = Column(Date(), nullable=False)
    code_commune = Column(String(5))
    commune = Column(String(255))
    code_pays = Column(String(5))
    pays = Column(String(2555))
    date_maj = Column(Date(), nullable=False)

    @property
    def key(self):
        return self.inpp

    def equals(self, other):
        return self.key == other.key and self.statut == other.statut and self.date_deces == other.date_deces \
            and self.date_effet == other.date_effet and self.date_maj == other.date_maj

    def __repr__(self):
        return f"{self.id} {self.inpp} {self.nom} {self.prenoms}"



class ReferenceAE(Base):
    __tablename__ = "reference_ae"

    id = Column(Integer, primary_key=True)
    inpp = Column(String(12), nullable=False)
    ae = Column(String(5), nullable=False)
    date_debut = Column(Date(), nullable=False)
    date_fin = Column(Date())
    date_maj = Column(Date(), nullable=False)
    statut = Column(String(1), nullable=False)
    departement = Column(String(3))
    departement_acceuil = Column(String(3))
    code_profession = Column(Integer, nullable=False, index=True)
    exercice_pro: ExercicePro = relationship("ExercicePro", backref="reference_aes")
    exercice_pro_id = Column(Integer, ForeignKey('exercice_pro.id'), nullable=False, index=True)
    categorie_pro = Column(String(5), nullable=False)
    __table_args__ = (UniqueConstraint('inpp', 'categorie_pro', 'code_profession', 'ae', 'date_debut'),)


    @property
    def key(self):
        return self.inpp, self.categorie_pro, self.code_profession, self.ae, self.date_debut

    def equals(self, other):
        return self.key == other.key and self.date_fin == other.date_fin and self.date_maj == other.date_maj

    def __repr__(self):
        return f"{self.id} {self.categorie_pro} {self.code_profession} {self.ae} {self.date_debut}"

class SavoirFaireObtenu(Base):
    __tablename__ = "savoir_faire_obtenu"

    id = Column(Integer, primary_key=True)
    inpp = Column(String(12), nullable=False)
    type_sf = Column(String(10), nullable=False)
    code_sf = Column(String(10), nullable=False)
    diplome: Diplome = relationship("Diplome", backref="savoir_faire_obtenus")
    diplome_id = Column(Integer, ForeignKey('diplome.id'), nullable=False, index=True)
    code_profession = Column(Integer, nullable=False)
    categorie_pro = Column(String(5), nullable=False)
    exercice_pro: ExercicePro = relationship("ExercicePro", backref="savoir_faire_obtenus")
    exercice_pro_id = Column(Integer, ForeignKey('exercice_pro.id'), nullable=False, index=True)
    date_reconnaissance = Column(Date(), nullable=False)
    date_maj = Column(Date(), nullable=False)
    date_abandon = Column(Date())
    __table_args__ = (UniqueConstraint('inpp', 'categorie_pro', 'code_profession', 'code_sf',
                                       'type_sf', 'date_reconnaissance'),)

    @property
    def key(self):
        return self.inpp, self.categorie_pro, self.code_profession, self.code_sf, self.type_sf, self.date_reconnaissance

    def equals(self, other):
        return self.key == other.key and self.date_maj == other.date_maj and self.date_abandon == other.date_abandon

    def __repr__(self):
        return f"{self.id} {self.categorie_pro} {self.code_profession} {self.code_sf} {self.date_reconnaissance}"


class Langue(Base):
    __tablename__ = "langue"

    id = Column(Integer, primary_key=True)
    code = Column(String(2), nullable=False, unique=True)
    libelle = Column(String(255), nullable=False)

    def __repr__(self):
        return f"{self.id} {self.code}"


class PersonneLangue(Base):
    __tablename__ = "personne_langue"

    id = Column(Integer, primary_key=True)
    inpp = Column(String(12), nullable=False)
    code = Column(String(2), nullable=False)
    langue: Langue = relationship("Langue", backref="personne_langues")
    langue_id = Column(Integer, ForeignKey('langue.id'), nullable=False, index=True)
    date_maj = Column(Date(), nullable=False)

    @property
    def key(self):
        return self.inpp, self.code

    def equals(self, other):
        return self.key == other.key and self.date_maj == other.date_maj

    def __repr__(self):
        return f"{self.id} {self.inpp} {self.code}"


class Autorisation(Base):
    __tablename__ = "autorisation"

    id = Column(Integer, primary_key=True)
    code = Column(String(4), nullable=False, unique=True)
    libelle = Column(String(255), nullable=False)

    def __repr__(self):
        return f"{self.id} {self.code}"


class PersonneAutorisation(Base):
    __tablename__ = "personne_autorisation"

    id = Column(Integer, primary_key=True)
    inpp = Column(String(12), nullable=False)
    code = Column(String(4), nullable=False)
    autorisation: Autorisation = relationship("Autorisation", backref="personne_autorisations")
    autorisation_id = Column(Integer, ForeignKey('autorisation.id'), nullable=False, index=True)
    date_effet = Column(Date(), nullable=False)
    date_fin = Column(Date())
    date_maj = Column(Date(), nullable=False)
    discipline = Column(String(10))
    code_profession: CodeProfession = relationship("CodeProfession", backref="personne_autorisations")
    code_profession_id = Column(Integer, ForeignKey('code_profession.id'), nullable=False, index=True)


    @property
    def key(self):
        return self.inpp, self.code, self.code_profession_id

    def equals(self, other):
        return self.key == other.key and self.date_maj == other.date_maj and self.date_fin == other.date_fin

    def __repr__(self):
        return f"{self.id} {self.code} {self.code_profession_id}"


class Attribution(Base):
    __tablename__ = "attribution"

    id = Column(Integer, primary_key=True)
    code = Column(String(7), nullable=False, unique=True)
    libelle = Column(String(255), nullable=False)

    def __repr__(self):
        return f"{self.id} {self.code}"


class PersonneAttribution(Base):
    __tablename__ = "personne_attribution"

    id = Column(Integer, primary_key=True)
    inpp = Column(String(12), nullable=False)
    code = Column(String(7), nullable=False)
    attribution: Attribution = relationship("Attribution", backref="personne_attributions")
    attribution_id = Column(Integer, ForeignKey('attribution.id'), nullable=False, index=True)
    date_reconnaissance = Column(Date(), nullable=False)
    date_abandon = Column(Date())
    date_maj = Column(Date(), nullable=False)
    code_profession: CodeProfession = relationship("CodeProfession", backref="personne_attributions")
    code_profession_id = Column(Integer, ForeignKey('code_profession.id'), nullable=False, index=True)
    categorie_pro = Column(String(5), nullable=False)


    @property
    def key(self):
        return self.inpp, self.code, self.code_profession_id, self.categorie_pro, self.date_reconnaissance

    def equals(self, other):
        return self.key == other.key and self.date_maj == other.date_maj and self.date_abandon == other.date_abandon

    def __repr__(self):
        return f"{self.id} {self.inpp} {self.code} {self.code_profession_id} {self.categorie_pro}"

class Coord(Base):
    __tablename__ = "coord"

    id = Column(Integer, primary_key=True)
    inpp = Column(String(12))
    personne: Personne = relationship("Personne", backref="coord_personnes")
    personne_id = Column(Integer, ForeignKey('personne.id'), index=True)
    activite: Activite = relationship("Activite", backref="coord_activites")
    activite_id = Column(Integer, ForeignKey('activite.id'), index=True)
    identifiant_activite = Column(String(15))
    structure: Structure = relationship("Structure", backref="coord_structures")
    structure_id = Column(Integer, ForeignKey('structure.id'), index=True)
    structure_id_technique = Column(String(25))
    complement_destinataire = Column(String(255))
    complement_geo = Column(String(255))
    numero = Column(String(10))
    indice = Column(String(10))
    code_type_voie = Column(String(10))
    type_voie = Column(String(50))
    voie = Column(String(255))
    mention = Column(String(255))
    cedex = Column(String(255))
    cp = Column(String(10))
    code_commune = Column(String(10))
    commune = Column(String(255))
    code_pays = Column(String(5))
    pays = Column(String(255))
    tel = Column(String(50))
    tel2 = Column(String(50))
    fax = Column(String(50))
    mail = Column(String(255))
    date_maj = Column(Date(), nullable=False)
    date_fin = Column(Date())
    adresse_norm: AdresseNorm = relationship("AdresseNorm", backref="coord_personnes")
    adresse_norm_id = Column(Integer, ForeignKey('adresse_norm.id'), index=True)
    lon = Column(Float)
    lat = Column(Float)
    type_precision = Column(Integer)
    precision = Column(Float)


    @property
    def key(self):
        return self.inpp

    def equals(self, other):
        return self.key == other.key and self.identifiant_activite == other.identifiant_activite \
            and self.structure_id_technique == other.structure_id_technique \
            and self.date_maj == other.date_maj and self.date_fin == other.date_fin \
            and self.tel == other.tel and self.tel2 == other.tel2 and self.mail == other.mail \
            and self.mention == other.mention and self.cedex == other.cedex \
            and self.complement_geo == other.complement_geo \
            and self.complement_destinataire == other.complement_destinataire \
            and self.numero == other.numero and self.code_type_voie == other.code_type_voie and self.cp == other.cp


    def __repr__(self):
        return f"{self.inpp} {self.numero} {self.voie} {self.cp} {self.commune}"


class SAE(Base):
    __tablename__ = "sae"

    id = Column(Integer, primary_key=True)
    an = Column(Integer, nullable=False)
    nofinesset = Column(String(10), nullable=False, index=True)
    nofinessej = Column(String(10), nullable=False)
    structure: Structure = relationship("Structure")
    structure_id = Column(Integer, ForeignKey('structure.id'), index=True)
    etablissement: Etablissement = relationship("Etablissement")
    etablissement_id = Column(Integer, ForeignKey('etablissement.id'), index=True)

    __table_args__ = (UniqueConstraint('nofinesset', 'an'), {"schema": "sae2"},)

    @property
    def key(self):
        return self.nofinesset, self.an

    def equals(self, other):
        return self.key == other.key

    def __repr__(self):
        return f"{self.nofinesset} {self.an}"


class Lieu(Base):
    __tablename__ = "lieu"

    id = Column(Integer, primary_key=True)
    lieu = Column(String(10), nullable=False, unique=True)
    libelle = Column(String(255), nullable=False)

    @property
    def key(self):
        return self.lieu

    def __repr__(self):
        return f"{self.id} {self.lieu}"

    def equals(self, other):
        return self.lieu == other.lieu


class File(Base):
    __tablename__ = "file"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False, unique=True)
    zip_name = Column(String(255), nullable=False, unique=True)
    category = Column(String(50), nullable=False)
    url = Column(String(1024), nullable=False)
    path = Column(String(50), nullable=False)
    full_name = Column(String(255), nullable=False, unique=True)
    date = Column(Date, nullable=False)
    frequency = Column(String(1), nullable=False)
    download_mode = Column(String(10), nullable=False)
    online_date = Column(DateTime)
    download_date = Column(DateTime)
    md5 = Column(String(50))
    dezip_date = Column(DateTime)
    import_start_date = Column(DateTime)
    import_end_date = Column(DateTime)
    log_date = Column(DateTime)
    log = Column(String(1024))

    __table_args__ = ({"schema": "downloader"},)

    def __init__(self, name, path, category, frequency, mode):
        super().__init__()
        self.zip_name = self.name = name
        self.path = path
        self.full_name = self.path + name
        self.category = category
        self.frequency = frequency
        self.download_mode = mode
        self.online_date = datetime.datetime.now()

    def __repr__(self):
        return f"{self.id} {self.name}"
