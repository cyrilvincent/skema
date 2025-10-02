import datetime
from typing import Dict, Optional, Tuple
from sqlalchemy.orm import joinedload
import unidecode
import pyproj
from sqlentities import DateSource, AdresseRaw, Dept, AdresseNorm, Source
from abc import ABCMeta, abstractmethod
import csv
import time
import re

time0 = time.perf_counter()


class BaseParser(metaclass=ABCMeta):

    def __init__(self, context):
        self.path = None
        self.context = context
        self.row_num = 0
        self.nb_row = 0
        self.entities = {}
        self.nb_new_adresse = 0
        self.nb_new_entity = 0
        self.nb_update_entity = 0
        self.nb_new_norm = 0
        self.nb_ram = 0
        self.date_source: Optional[DateSource] = None
        self.depts: Dict[str, Dept] = {}
        self.depts_int: Dict[int, Dept] = {}
        self.sources: Dict[int, Source] = {}
        self.adresse_raws: Dict[Tuple[str, str, str, str, str], AdresseRaw] = {}
        self.adresse_norms: Dict[Tuple[int, str, str, str, str], AdresseNorm] = {}
        self.adresse_norms_id: Dict[int, AdresseNorm] = {}

    def load_cache(self):
        print("Making cache")
        l = self.context.session.query(Dept).all()
        for d in l:
            self.depts[d.num] = d
            self.depts_int[d.id] = d
            self.nb_ram += 2
        l = self.context.session.query(Source).all()
        for s in l:
            self.sources[s.id] = s
            self.nb_ram += 1
        l = self.context.session.query(AdresseRaw).options(joinedload(AdresseRaw.adresse_norm)).all()
        # Erreur courante, quand le key ne matche pas c'est que le cp est en str
        for a in l:
            self.adresse_raws[a.key] = a
            self.nb_ram += 1
        l = self.context.session.query(AdresseNorm).all()
        for a in l:
            self.adresse_norms[a.key] = a
            self.adresse_norms_id[int(a.id)] = a
            self.nb_ram += 2
        print(f"{self.nb_ram} objects in cache")

    def test_file(self, path, encoding="utf8"):
        with open(path, encoding=encoding) as f:
            for _ in f:
                self.nb_row += 1
        print(f"Found {self.nb_row} rows")

    def parse_date(self, path):
        try:
            yy = int(path[-9:-7])
            mm = int(path[-6:-4])
            self.date_source = DateSource(annee=yy, mois=mm)
        except IndexError:
            print("ERROR: file must have date like this: file_YY-MM.csv")
            quit(1)

    def get_dept_from_cp(self, cp) -> int | None:
        cp = str(cp)
        if len(cp) == 4:
            cp = "0" + cp
        dept = cp[:2]
        if dept == "20":
            dept = cp[:3]
            if dept == "200":
                dept = "201"
        if dept.isnumeric():
            return int(dept)
        return None

    def check_date(self, path):
        self.parse_date(path)
        db_date = self.context.session.query(DateSource).get(self.date_source.id)
        if db_date is None:
            print(f"Added date {self.date_source}")
            self.context.session.add(self.date_source)
            self.context.session.commit()
        else:
            self.date_source = db_date

    def get_nullable(self, v, size=65536):
        return None if v == "" else v[:size]

    def get_nullable_int(self, v):
        return None if v == "" else int(v)

    def get_date(self, s: str) -> datetime.date:
        return datetime.datetime.strptime(s, "%d/%m/%Y").date()

    def get_nullable_date(self, s: str) -> datetime.date:
        return None if s == "" else self.get_date(s)

    def strip_quotes(self, s: str) -> str:
        if len(s) > 0 and ((s[0] == '"' and s[-1] == '"') or (s[0] == "'" and s[-1] == "'")):
            return s[1:-1]
        return s

    def pseudo_clone(self, from_obj: object, to_obj):
        for a in from_obj.__dict__:
            if type(from_obj.__getattribute__(a)) in [str, int, float] and a not in ['id'] and not a.startswith('_'):
                to_obj.__setattr__(a, from_obj.__getattribute__(a))

    def split_num(self, s: str) -> Tuple[Optional[int], str]:
        regex = r"(\d+)"
        match = re.match(regex, s)
        if match is None:
            return None, s
        num = match[1]
        index = s.index(match[1])
        return int(num), s[index + len(num):].strip()

    def replace_all(self, s, dico: Dict[str, str]) -> str:
        for key in dico:
            s = s.replace(key, dico[key])
        return s

    def normalize_street(self, street: str) -> str:
        street = unidecode.unidecode(street)
        street = " " + street.upper()
        dico = {"'": " ", "-": " ", ".": "", "/": " ", '"': "",
                " BP": "", " CH ": " CHEMIN ", " AV ": " AVENUE ", " PL ": " PLACE ", " BD ": " BOULEVARD ",
                " IMP ": " IMPASSE ", " ST ": " SAINT ", " RT ": " ROUTE ", " RTE ": " ROUTE ", " GAL ": " GENERAL ",
                " BIS ": "", " TER ": "", " BAT ": ""}
        street = self.replace_all(street, dico).strip()
        if len(street) > 2 and street[1] == " ":
            street = street[2:]
        return street.strip()

    def normalize_commune(self, commune: str) -> str:
        commune = unidecode.unidecode(commune)
        commune = " " + commune.upper()
        if "CEDEX" in commune:
            index = commune.index("CEDEX")
            commune = commune[:index]
        dico = {"'": " ", "-": " ", ".": "", "/": " ", '"': "",
                " ST ": " SAINT ", " STE ": " SAINTE "}
        commune = self.replace_all(commune, dico)
        return commune.strip()

    def normalize_string(self, s: str) -> str:
        s = s.strip().upper()
        s = unidecode.unidecode(s).replace("'", " ").replace("-", " ").replace("/", " ").replace(".", "")
        return s

    def convert_lambert93_lon_lat(self, x: float, y: float) -> Tuple[float, float]:
        transformer = pyproj.Transformer.from_crs(2154, 4326, always_xy=True)
        lon, lat = transformer.transform(x, y)
        return lon, lat

    def load(self, path: str, delimiter=';', encoding="utf8", header=False, quotechar="\""):
        print(f"Loading {path}")
        self.path = path
        self.check_date(path)
        self.test_file(path, encoding)
        self.load_cache()
        duration_cache = time.perf_counter() - time0
        with open(path, encoding=encoding) as f:
            if header:
                reader = csv.DictReader(f, delimiter=delimiter, quotechar=quotechar)
            else:
                reader = csv.reader(f, delimiter=delimiter)
            for row in reader:
                self.row_num += 1
                self.parse_row(row)
                if self.row_num % 10000 == 0 or self.row_num == 10 or self.row_num == 100 \
                        or self.row_num == 1000 or self.row_num == self.nb_row:
                    duration = time.perf_counter() - time0 - duration_cache + 1e-6
                    print(f"Parse {self.row_num} rows {(self.row_num / self.nb_row) * 100:.1f}% "
                          f"in {(duration + duration_cache):.0f}s "
                          f"@{self.row_num / duration:.0f}row/s "
                          f"{((self.nb_row / self.row_num) * duration) - duration + 1:.0f}s remaining ")

    def escape_dot_comma(self, s):
        regex = r"([\d\w\t ']);([\d\w\t '])?"
        if re.search(regex, s) is not None:
            s = re.sub(regex, r"\1.\2", s)
        # regex = r";([\d\w\t '])" # Never happened
        # if re.search(regex, s) is not None:
        #     s = re.sub(regex, r".\1", s)
        return s

    def strip_double_quotes_writer(self, path: str, out_path: str, encoding="utf8"):
        print(f"Loading {path}")
        with open(path, encoding=encoding) as f:
            print(f"Creating {out_path}")
            with open(out_path, "w", encoding=encoding) as out:
                for row in f:
                    row = self.escape_dot_comma(row)
                    # row = row.replace("matriçage ; métallurgie", "matriçage, métallurgie")
                    # row = row.replace("Créole haïtien; haïtien", "haïtien")
                    # row = row.replace("BAT I ;", "BAT I, ")
                    # row = row.replace("BÂTIMENT H ; LOT 409 ;", "BÂTIMENT H, LOT 409,")
                    row = row.replace('"', "")
                    out.write(row)


    @abstractmethod
    def parse_row(self, row): ...

    @abstractmethod
    def mapper(self, row): ...


