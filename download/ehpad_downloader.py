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
from download.downloader import BaseDownloader
from ehpad_parser import EhpadParser
from sqlentities import Context, File, BAN
from bs4 import BeautifulSoup
import re


class EphadDownloader(BaseDownloader):

    def __init__(self, context, echo=False, fake_download=False, no_commit=False, force_download=False, no_parsing=False):
        super().__init__(context, echo, fake_download, no_commit, force_download, no_parsing)
        self.url = "https://www.data.gouv.fr/fr/datasets/prix-hebergement-et-tarifs-dependance-des-ehpad-donnees-brutes/"
        self.api = "https://www.data.gouv.fr/fr/datasets/r/"
        self.download_path = "data/ehpad/"
        self.download_zip_path = self.download_path
        self.category = "Ehpad"
        self.frequency = "M"
        self.download_mode = "AUTO"
        self.make_cache()
        self.parser = EhpadParser()

    def make_cache(self):
        super().make_cache()
        l: list[File] = self.context.session.query(File).filter(File.category == "Ehpad").all()
        for e in l:
            self.files[e.name] = e

    def scrap_guid(self, name: str) -> str | None:
        node = self.soup.find("div", {'text': name})
        if node is None:
            return None
        anode = node.parent.parent.parent.parent.parent.next_sibling.find("a")
        aria = anode.attrs["aria-describedby"]
        guid = aria[aria.index("-") + 1:aria.rindex("-")]
        return guid

    def scrap_year_month(self, year_month: int):
        name = f"cnsa_export_prix_ehpad_20{year_month}_brute.csv"
        guid = self.scrap_guid(name)
        name = name.replace("_", "-")
        if guid is not None:
            file = self.get_file_by_name(name)
            if file.download_date is None:
                self.download(file, self.api + guid)
                if not self.no_commit:
                    if file.id is None:
                        self.context.session.add(file)
                    self.context.session.commit()

    def scrap(self):
        now = datetime.datetime.now()
        for year_month in self.monthrange(2407, (now.year - 2000) * 100 + now.month):
            self.scrap_year_month(year_month)

    def has_ehpad_by_datesource(self, year_month: int) -> bool:
        sql = f"select * from ehpad where datesource_id = {year_month}"
        engine = create_engine(config.connection_string, echo=False)
        conn = engine.raw_connection()
        cur = conn.cursor()
        cur.execute(sql)
        rows = cur.fetchall()
        return len(rows) > 0

    def load(self):
        super().load()
        for item in os.listdir(self.download_path):
            if item.endswith(".csv"):
                file = self.get_file_by_name(item)
                year = int(item[-16:-12]) if len(item) == 39 else int(item[-14:-10])
                month = int(item[-12:-10]) if len(item) == 39 else 0
                file.date = datetime.date(year, month if month != 0 else 12, 1)
                year_month = (year - 2000) * 100 + month
                if not self.has_ehpad_by_datesource(year_month):
                    file.import_start_date = datetime.datetime.now()
                    self.context.session.commit()
                    if not self.no_parsing:
                        print(f"Parse {file.name}")
                        self.parser.load(file.full_name)
                        self.nb_new_file += 1
                    file.import_end_date = datetime.datetime.now()
                    if file.id is None:
                        self.context.session.add(file)
                    if not self.no_commit:
                        self.context.session.commit()




if __name__ == '__main__':
    art.tprint(config.name, "big")
    print("Ehpad Downloader")
    print("================")
    print(f"V{config.version}")
    print(config.copyright)
    print()
    parser = argparse.ArgumentParser(description="Ehpad Downloader")
    parser.add_argument("-e", "--echo", help="Sql Alchemy echo", action="store_true")
    parser.add_argument("-f", "--fake_download", help="Faking the downloader and dezip", action="store_true")
    parser.add_argument("-d", "--force_download", help="Force the downloader and dezip", action="store_true")
    parser.add_argument("-n", "--no_commit", help="No commit", action="store_true")
    parser.add_argument("-p", "--no_parsing", help="No parsing", action="store_true")
    args = parser.parse_args()
    context = Context()
    context.create(echo=args.echo, expire_on_commit=False)
    d = EphadDownloader(context, args.echo, args.fake_download, args.no_commit, args.force_download, args.no_parsing)
    # d.get_html()
    # d.scrap()
    d.load()
    print(f"Nb new files: {d.nb_new_file}")
