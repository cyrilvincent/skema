import argparse
import datetime
import os
import time

import art
import config
from downloader.base_downloader import BaseDownloader
from sqlentities import Context, File, BAN
from BAN_parser import AdresseParser


class BANDownloader(BaseDownloader):

    def __init__(self, context, echo=False, fake_download=False, no_commit=False, force_download=False, no_parsing=False):
        super().__init__(context, echo, fake_download, no_commit, force_download, no_parsing)
        self.url = "https://adresse.data.gouv.fr/data/ban/adresses/latest/csv/"
        self.download_path = "data/adresse/"
        self.download_zip_path = self.download_path
        self.category = "BAN"
        self.frequency = "M"
        self.download_mode = "AUTO"
        self.make_cache()
        self.parser = AdresseParser()

    def make_cache(self):
        print("Make cache")
        l: list[File] = self.context.session.query(File).filter(File.category == "BAN").all()
        for e in l:
            self.files[e.zip_name] = e

    def downloads(self):
        super().downloads()
        for dept in self.deptrange():
            file = self.get_file_by_name(f"adresses-{dept}.csv.gz")
            self.download_and_dezip(file, "gz")
            file = self.get_file_by_name(f"lieux-dits-{dept}-beta.csv.gz")
            self.download_and_dezip(file, "gz")

    def load(self):
        super().load()
        for item in os.listdir(config.adresse_path):
            if item.endswith(".csv") and item.startswith("adresses-"):
                dept = item[9:11].replace("A", "01").replace("B", "02")
                dept = int(dept)
                if 1 <= dept <= 95 or dept == 201 or dept == 202:
                    path = f"{config.adresse_path}/{item}"
                    file = self.files[f"{path.split("/")[-1]}.gz"]
                    file.import_start_date = datetime.datetime.now()
                    self.context.session.commit()
                    if not self.no_parsing:
                        self.parser = AdresseParser()
                        self.parser.load(path, dept)
                    file.import_end_date = datetime.datetime.now()
                    self.context.session.commit()
                    path = path.replace('adresses-', 'lieux-dits-').replace('.csv', '-beta.csv')
                    file = self.files[f"{path.split("/")[-1]}.gz"]
                    file.import_start_date = datetime.datetime.now()
                    self.context.session.commit()
                    if not self.no_parsing:
                        self.parser.load_lieuxdits(path, dept)
                    file.import_end_date = datetime.datetime.now()
                    self.context.session.commit()
                else:
                    print(f"Skipping {dept}")


if __name__ == '__main__':
    art.tprint(config.name, "big")
    print("BAN Downloader")
    print("==============")
    print(f"V{config.version}")
    print(config.copyright)
    print()
    parser = argparse.ArgumentParser(description="BAN Downloader")
    parser.add_argument("-e", "--echo", help="Sql Alchemy echo", action="store_true")
    parser.add_argument("-f", "--fake_download", help="Faking the downloader and dezip", action="store_true")
    parser.add_argument("-d", "--force_download", help="Force the downloader and dezip", action="store_true")
    parser.add_argument("-n", "--no_commit", help="No commit", action="store_true")
    parser.add_argument("-p", "--no_parsing", help="No parsing", action="store_true")
    args = parser.parse_args()
    context = Context()
    context.create(echo=args.echo, expire_on_commit=False)
    d = BANDownloader(context, args.echo, args.fake_download, args.no_commit, args.force_download, args.no_parsing)
    d.downloads()
    d.load()
    print(f"Nb new files: {d.nb_new_file}")
