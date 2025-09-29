import argparse
import datetime
import os

import requests
import art
from bs4 import BeautifulSoup
import config
from damir_parser import DamirParser
from downloader.base_downloader import BaseDownloader
from sqlentities import Context, File


class DamirDownloader(BaseDownloader):

    def __init__(self, context, echo=False, fake_download=False, no_commit=False, force_download=False, no_parsing=False):
        super().__init__(context, echo, fake_download, no_commit, force_download, no_parsing)
        # https://www.assurance-maladie.ameli.fr/etudes-et-donnees/open-damir-depenses-sante-interregimes
        self.url = "https://open-data-assurance-maladie.ameli.fr/depenses/download.php?Dir_Rep=Open_DAMIR&Annee="
        self.download_url = "https://open-data-assurance-maladie.ameli.fr/depenses/"
        self.download_path = self.download_zip_path = "data/damir/"
        self.category = "Damir"
        self.frequency = "M"
        self.download_mode = "AUTO"
        self.parser = DamirParser(context)
        self.make_cache()

    def make_cache(self):
        print("Making cache")
        l: list[File] = self.context.session.query(File).filter((File.category == self.category)).all()
        for e in l:
            self.files[e.name] = e

    def scrap_urls(self) -> dict[int, str]:
        nodes = self.soup.find_all("a")
        urls: dict[int, str] = {}
        for node in nodes:
            url = node.attrs["href"]
            name = url.split("/")[-1]
            yearmonth = int(name[-11:-7])
            urls[yearmonth] = self.download_url + url[2:]
        return urls

    def get_html_by_year(self, year: int):
        self.soup = None
        url = f"{self.url}{year}"
        print(f"Reading {url}")
        try:
            self.html = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}).text
            self.soup = BeautifulSoup(self.html, features="html.parser")
        except Exception as ex:
            print(f"Error with {url}: {ex}")

    def scrap_by_url(self, yearmonth: int, url: str):
        name = f"A20{yearmonth}.csv.gz"
        if name not in self.files:
            print(f"Scraping {url}")
            file = File(name, self.download_path, self.category, self.frequency, self.download_mode)
            file.date = datetime.date((yearmonth // 100) + 2000, yearmonth % 100, 1)
            self.files[name] = file
        file = self.files[name]
        file.url = f"{self.url}20{yearmonth // 100}"
        if file.download_date is None:
            if not self.fake_download:
                self.download(file, url)
            file.download_date = datetime.datetime.now()
            if not self.no_commit:
                if file.id is None:
                    self.context.session.add(file)
                self.context.session.commit()

    def scrap(self, start_year=2020, end_year=datetime.date.today().year - 1):
        for year in range(start_year, end_year + 1):
            self.get_html_by_year(year)
            if self.soup is not None:
                urls = self.scrap_urls()
                for yearmonth in urls.keys():
                    self.scrap_by_url(yearmonth, urls[yearmonth])

    def dezip_and_load(self, file: File):
        try:
            if file.dezip_date is None:
                self.dezip(self.download_path, file.name)
                file.dezip_date = datetime.datetime.now()
                if not self.no_commit:
                    self.context.session.commit()
            db_size = self.context.db_size()
            file.import_start_date = datetime.datetime.now()
            if not self.no_parsing:
                self.parser.load(file.full_name[:-3])
                if not self.no_commit:
                    self.parser.commit()
            new_db_size = context.db_size()
            print(f"Database {context.db_name}: {new_db_size:.0f} MB")
            print(f"Database grows: {new_db_size - db_size:.0f} MB ({((new_db_size - db_size) / db_size) * 100:.1f}%)")
            self.nb_new_file += 1
            file.import_end_date = datetime.datetime.now()
            if not self.no_commit:
                self.context.session.commit()
            try:
                os.remove(file.full_name[:-3])
            except:
                pass
        except Exception as ex:
            print(f"Damir error {ex}")
            if not self.no_commit:
                file.log_date = datetime.datetime.now()
                file.log = str(ex)
                self.context.session.commit()

    def load(self):
        super().load()
        files: list[File] = (self.context.session.query(File)
                             .filter((File.category == self.category) & (File.import_end_date.is_(None)))
                             .order_by(File.date).all())
        for file in files:
            self.dezip_and_load(file)


if __name__ == '__main__':
    art.tprint(config.name, "big")
    print("Damir Downloader")
    print("================")
    print(f"V{config.version}")
    print(config.copyright)
    print()
    parser = argparse.ArgumentParser(description="Damir Downloader")
    parser.add_argument("-e", "--echo", help="Sql Alchemy echo", action="store_true")
    parser.add_argument("-f", "--fake_download", help="Faking the downloader and dezip", action="store_true")
    parser.add_argument("-d", "--force_download", help="Force the downloader and dezip", action="store_true")
    parser.add_argument("-n", "--no_commit", help="No commit", action="store_true")
    parser.add_argument("-p", "--no_parsing", help="No parsing", action="store_true")
    args = parser.parse_args()
    context = Context()
    context.create(echo=args.echo, expire_on_commit=False)
    d = DamirDownloader(context, args.echo, args.fake_download, args.no_commit, args.force_download, args.no_parsing)
    # d.scrap()
    # d.scrap(start_year=datetime.date.today().year - 1)
    d.load()
    print(f"Nb new files: {d.nb_new_file}")
