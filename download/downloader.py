import argparse
import datetime
import urllib.request
import urllib.parse
import urllib.error
import hashlib
import zipfile
import gzip
import abc
from sqlentities import File
from sqlalchemy import select


class BaseDownloader(metaclass=abc.ABCMeta):

    def __init__(self, context, echo=False, fake_download=False, no_commit=False, force_download=False, no_parsing=False):
        self.url = ""
        self.context = context
        self.echo = echo
        self.fake_download = fake_download
        self.no_commit = no_commit
        self.force_download = force_download
        self.no_parsing = no_parsing
        self.html = ""
        self.rows: list[str] = []
        self.nb_new_file = 0
        self.download_path = ""
        self.download_zip_path = ""
        self.category = ""
        self.frequency = "Y"
        self.download_mode = "AUTO"
        self.files: dict[str, File] = {}

    def make_cache(self):
        print("Making cache")

    def get_file(self, name: str) -> File:
        if name in self.files:
            return self.files[name]
        file = File(name, self.download_zip_path, self.category, self.frequency, self.download_mode)
        return file

    def test(self):
        print(f"Open {self.url}")
        try:
            with urllib.request.urlopen(self.url) as response:
                self.html = str(response.read())
                print("OK")
        except Exception as ex:
            print(self.url)
            print(f"WARNING URL Error: {ex}")
            quit(1)

    def get_file_by_id(self, id: int) -> File | None:
        return self.context.session.get(File, id)

    def get_last_file(self) -> File:
        return self.context.session.execute(
            select(File).where(File.dezip_date is not None).order_by(File.online_date.desc())).scalars().first()

    def daterange(self, start_date: datetime.date, end_date: datetime.date):
        days = int((end_date - start_date).days)
        for n in range(days):
            yield start_date + datetime.timedelta(n)

    def deptrange(self):
        for d in range(1, 97):
            dept = str(d)
            if len(dept) == 1:
                dept = "0" + dept
            elif d == 20:
                dept = "2A"
            elif d == 96:
                dept = "2B"
            yield dept

    def check_md5(self, path: str, md5: str) -> bool:
        with open(path, "rb") as f:
            content = f.read()
            hash = hashlib.md5(content).hexdigest()
            return hash == md5

    def dezip(self, path: str, file: str):
        print(f"Dezip {path+file} to {self.download_path}")
        if file.split(".")[-1] == "gz":
            with gzip.open(path+file, "rb") as f:
                with open(path+file.replace(".gz", ""), "wb") as out:
                    out.write(f.read())
        else:
            with zipfile.ZipFile(path+file, 'r') as zip:
                zip.extractall(self.download_path)

    def download(self, file: File):
        file.url = self.url + file.zip_name
        print(f"Downloading {file.url} to {self.download_zip_path}")
        if self.fake_download:
            file.download_date = datetime.datetime.now()
            file.date = datetime.date.today()
            if file.online_date is None:
                file.online_date = datetime.datetime.now()
        else:
            try:
                file.online_date = datetime.datetime.now()
                file.date = datetime.date.today()
                file.dezip_date = None
                file.import_end_date = None
                file.import_start_date = None
                with urllib.request.urlopen(file.url) as response:
                    content = response.read()
                    with open(file.full_name, "wb") as f:
                        f.write(content)
                    file.download_date = datetime.datetime.now()
                    self.nb_new_file += 1
            except Exception as ex:
                print(f"WARNING download Error: {ex}")
                file.log_date = datetime.datetime.now()
                file.log = f"Download error {ex}"

    def download_and_dezip(self, file: File, extension="zip"):
        self.download(file)
        if not self.no_commit:
            self.context.session.add(file)
            self.context.session.commit()
        try:
            self.dezip(self.download_zip_path, file.zip_name)
            file.name = file.zip_name.replace(f".{extension}", "")
            file.full_name = self.download_path + file.name
            file.dezip_date = datetime.datetime.now()
        except Exception as ex:
            print(f"WARNING dezip error: {ex}")
            file.log_date = datetime.datetime.now()
            file.log = f"Dezip error {ex}"
        if not self.no_commit:
            self.context.session.commit()

    def downloads(self):
        self.test()

    def load(self):
        print("Parsing")




