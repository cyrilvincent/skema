import argparse
import datetime
import os
import time
import urllib.request
import urllib.parse
import urllib.error
import art
from sqlalchemy import create_engine
import config
from diplome_parser import DiplomeParser
from downloader.base_downloader import BaseDownloader
from personne_activite_parser import PersonneActiviteParser
from sqlentities import Context, File, BAN
from bs4 import BeautifulSoup
import re


class PersonneActiviteDownloader(BaseDownloader):

    def __init__(self, context, echo=False, fake_download=False, no_commit=False, force_download=False, no_parsing=False):
        super().__init__(context, echo, fake_download, no_commit, force_download, no_parsing)
        self.url = "https://annuaire.sante.fr/web/site-pro/extractions-publiques/"
        self.download_path = "data/ps_libreacces/"
        self.download_zip_path = self.download_path
        self.category = "PsLibreAcces"
        self.frequency = "M"
        self.download_mode = "AUTO"
        self.files2: dict[int, File] = {}
        self.make_cache()

    def make_cache(self):
        print("Making cache")
        l: list[File] = (self.context.session.query(File)
                         .filter((File.category == self.category) & (File.name.endswith(".zip"))).all())
        for e in l:
            self.files2[e.date.year * 100 + e.date.month] = e
        l: list[File] = (self.context.session.query(File)
                         .filter(File.category == self.category).all())
        for e in l:
            self.files[e.name] = e

    def get_file2_by_name(self, name: str) -> File:
        yearmonth = int(name[-16:-10])
        if yearmonth in self.files2:
            return self.files2[yearmonth]
        file = File(name, self.download_zip_path, self.category, self.frequency, self.download_mode)
        file.date = datetime.date(yearmonth // 100, yearmonth % 100, 1)
        return file

    def scrap_url(self) -> str | None:
        node = self.soup.find("td", {"class": "col_4a"})
        if node is None:
            return None
        url = node.find("a").attrs["href"]
        return url

    def scrap(self):
        url = self.scrap_url()
        if url is not None:
            name = url.split("nomFichier=")[-1]
            file = self.get_file2_by_name(name) # /!\ 1 fichier en genere 3 créer 4 file en tout le masterfile et les 3 files
            file.url = url
            if file.download_date is None:
                if not self.fake_download:
                    self.download(file, file.url)
                file.download_date = datetime.datetime.now()
                if not self.no_commit:
                    if file.id is None:
                        self.context.session.add(file)
                    self.context.session.commit()

    def dezips(self):
        files = [f for f in self.files.values() if f.dezip_date is None and f.name.endswith(".zip")]
        if len(files) > 0:
            file = files[0]
            try:
                if not self.fake_download:
                    self.dezip(self.download_path, file.name)
                file.dezip_date = datetime.datetime.now()
                if not self.no_commit:
                    self.context.session.commit()
            except Exception as ex:
                print(f"PSLibreAcces error {ex}")
                if not self.no_commit:
                    file.log_date = datetime.datetime.now()
                    file.log = str(ex)
                    self.context.session.commit()

    def load_file_from_type(self, zip_file: File, file: File, type: str):
        if file.import_end_date is None:
            file.dezip_date = zip_file.dezip_date
            file.date = zip_file.date
            file.zip_name = zip_file.zip_name
            file.url = zip_file.url
            file.import_start_date = datetime.datetime.now()
            zip_file.import_start_date = file.import_start_date
            if not self.no_commit:
                self.context.session.add(file)
                self.context.session.commit()
            if not self.no_parsing:
                print(f"Parse {file.name}")
                context = Context()
                context.create(echo=args.echo, expire_on_commit=False)
                if type == "Personne_activite":
                    self.parser = PersonneActiviteParser(context)
                elif type == "Dipl_AutExerc":
                    self.parser = DiplomeParser(context)
                else:
                    self.parser = DiplomeParser(context, savoir=True)
                self.parser.load(file.full_name)
                self.nb_new_file += 1
            file.import_end_date = datetime.datetime.now()
            if not self.no_commit:
                self.context.session.commit()

    def load(self):
        super().load()
        types = ["Dipl_AutExerc", "SavoirFaire", "Personne_activite"]
        file: File | None = None
        for zip_file in self.files2.values():
            all_ok = True
            if zip_file.import_end_date is None:
                for type in types:
                    for item in os.listdir(self.download_path):
                        yearmonth = zip_file.date.year * 100 + zip_file.date.month
                        if item.endswith(".txt") and item.startswith(f"PS_LibreAcces_{type}_{yearmonth}"):  # Ne fonctionne pas pour un zip du 1er du mois
                            try:
                                file = self.get_file_by_name(item)
                                self.load_file_from_type(zip_file, file, type)
                            except Exception as ex:
                                print(f"Error for parsing {type}")
                                all_ok = False
                                file.log_date = datetime.datetime.now()
                                file.log(str(ex))
                                if not self.no_commit:
                                    if file.id is not None:
                                        self.context.session.add(file)
                                    self.context.session.commit()
                if all_ok:
                    zip_file.import_end_date = file.import_end_date
                if file is not None and not self.no_commit:
                    if file.id is not None:
                        self.context.session.add(file)
                    self.context.session.commit()




if __name__ == '__main__':
    art.tprint(config.name, "big")
    print("PS Libre Acces Downloader")
    print("=========================")
    print(f"V{config.version}")
    print(config.copyright)
    print()
    parser = argparse.ArgumentParser(description="PS Libre Acces Downloader")
    parser.add_argument("-e", "--echo", help="Sql Alchemy echo", action="store_true")
    parser.add_argument("-f", "--fake_download", help="Faking the downloader and dezip", action="store_true")
    parser.add_argument("-d", "--force_download", help="Force the downloader and dezip", action="store_true")
    parser.add_argument("-n", "--no_commit", help="No commit", action="store_true")
    parser.add_argument("-p", "--no_parsing", help="No parsing", action="store_true")
    args = parser.parse_args()
    context = Context()
    context.create(echo=args.echo, expire_on_commit=False)
    d = PersonneActiviteDownloader(context, args.echo, args.fake_download, args.no_commit, args.force_download, args.no_parsing)
    # d.get_html()
    # d.scrap()
    # d.dezips()
    d.load()
    print(f"Nb new files: {d.nb_new_file}")
