import datetime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Integer, BigInteger, String, Float, CHAR, create_engine, Column, ForeignKey, Boolean, \
    UniqueConstraint, Table, Index, Date, DateTime, SmallInteger
from sqlalchemy.orm import sessionmaker, relationship, Session
from sqlalchemy.engine import Engine
import config

Base = declarative_base()


class Context:

    def __init__(self, connection_string=config.connection_string):
        self.engine: Engine | None = None
        self.session: Session | None = None
        self.connection_string = connection_string

    @property
    def db_name(self):
        index = self.connection_string.rindex("/")
        return self.connection_string[index + 1:]

    def create_engine(self, echo=False, create_all=True):
        self.engine = create_engine(self.connection_string, echo=echo)
        if create_all:
            Base.metadata.create_all(self.engine)

    def create_session(self, expire_on_commit=False):
        Session = sessionmaker(bind=self.engine, autocommit=False, autoflush=False, expire_on_commit=expire_on_commit)
        self.session = Session()

    def get_session(self, expire_on_commit=False):
        Session = sessionmaker(bind=self.engine, autocommit=False, autoflush=False, expire_on_commit=expire_on_commit)
        return Session()

    def create(self, echo=False, create_all=True, expire_on_commit=False):
        self.create_engine(echo, create_all)
        self.create_session(expire_on_commit)

    def db_size(self):
        with self.engine.connect() as conn:
            sql = f"select pg_database_size('{self.db_name}')"
            res = conn.execute(sql)
            row = res.fetchone()
            return row[0] / 2 ** 20

# MCD
# ps -* tarif


class UrlDTO(Base):
    __tablename__ = "url_dto"

    id = Column(Integer, primary_key=True)
    keyword = Column(String(255), nullable=False)
    location = Column(String(255), nullable=False)
    page = Column(Integer, nullable=False)
    avaibilities = Column(Integer)

    __table_args__ = ({"schema": "doctolib"},)

    def __init__(self, keyword: str, location: str, page=1, avaibilities=0, last_name=""):
        super().__init__()
        self.keyword = keyword
        self.location = location
        self.page = page
        self.avaibilities = avaibilities
        self.last_name = last_name


class PS(Base):
    __tablename__ = "ps"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    url = Column(String(255), nullable=False)
    pid = Column(String(255), nullable=False, unique=True)
    nick = Column(String(255), nullable=False, unique=True)
    speciality = Column(String(255), nullable=False)
    type = Column(String(50))
    street = Column(String(255))
    city = Column(String(255))
    cp = Column(String(5))
    locality = Column(String(255))
    rdv_text = Column(String(255))
    rdv_date = Column(Date)
    now = Column(Date)
    rdv_days = Column(Integer)
    rdv_type = Column(Integer)
    convention = Column(String(10))
    carte_vitale = Column(Boolean)
    address_name = Column(String(255))
    address = Column(String(255))
    rpps = Column(String(50))
    adeli = Column(String(50))
    siren = Column(String(50))
    url_dto: UrlDTO = relationship("UrlDTO", backref="pss")
    url_dto_id = Column(Integer, ForeignKey('doctolib.url_dto.id'), nullable=False, index=True)

    __table_args__ = ({"schema": "doctolib"},)

    def __init__(self, speciality):
        super().__init__()
        self.now = datetime.date.today()
        self.rdv_type = 0
        self.speciality = speciality

    def __repr__(self):
        return f"PS {self.pid} {self.type} {self.nick} {self.speciality} {self.city}"


class Tarif(Base):
    __tablename__ = "tarif"

    id = Column(Integer, primary_key=True, )
    label = Column(String(255), nullable=False)
    tarif = Column(Float)
    tarif_max = Column(Float)
    datesource_id = Column(Integer, nullable=False)
    ps: PS = relationship("PS", backref="tarifs")
    ps_id = Column(Integer, ForeignKey('doctolib.ps.id'), nullable=False, index=True)

    __table_args__ = ({"schema": "doctolib"},)

    def __repr__(self):
        return f"{self.label} {"None" if self.tarif is None else self.tarif}€"
