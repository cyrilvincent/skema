import argparse
import datetime
import os
import time

import art
import config
from downloader.base_downloader import BaseDownloader
from etalab_parser import EtalabParser
from sqlentities import Context, File, BAN
from BAN_parser import AdresseParser
import shutil

# Le lien change chaque année
# Impossible d'automatiser le zip
# Le fichier de l'année en cours est corrompu

class EtalabDownloader(BaseDownloader):

    def __init__(self, context, echo=False, fake_download=False, no_commit=False, force_download=False, no_parsing=False):
        super().__init__(context, echo, fake_download, no_commit, force_download, no_parsing)
        self.url = "https://www.data.gouv.fr/fr/datasets/finess-extraction-du-fichier-des-etablissements/"
        self.download_path = "data/etalab/"
        self.download_zip_path = self.download_path
        self.category = "Etalab"
        self.frequency = "M"
        self.download_mode = "MANUALLY"
        self.make_cache()
        self.parser = EtalabParser(context)

    def dezips(self):
        year = datetime.date.year
        if len(self.files) == 0:
            year = 2024
        for item in os.listdir(self.download_path):
            if item.endswith(f"-{year}.zip"):
                # name = f"etalab_stock_et_{year}1231.csv"
                if item not in self.files:
                    file = File(item, self.download_path, self.category, self.frequency, self.download_mode)
                    file.online_date = file.download_date = datetime.datetime.now()
                    file.date = datetime.date(year, 1, 1)
                    file.zip_name = item
                    file.url = self.url
                    try:
                        if file.dezip_date is None:
                            self.dezip(self.download_path, item)
                            shutil.copytree(self.download_path+item[:item.rindex(".")], self.download_path, dirs_exist_ok=True)
                            file.dezip_date = datetime.datetime.now()
                            if not self.no_commit:
                                self.context.session.add(file)
                                self.context.session.commit()
                    except Exception as ex:
                        print(f"Etalab error {ex}")
                        if not self.no_commit:
                            file.log_date = datetime.datetime.now()
                            file.log = str(ex)
                            self.context.session.commit()

    def load(self):
        super().load()
        for item in os.listdir(self.download_path):
            if item.endswith(".csv") and item.startswith("etalab_stock_et_"):
                file = self.get_file_by_name(item)
                file.url = self.url
                file.date = datetime.date(int(item[-12:-8]), 12, 31)
                if file.online_date is None:
                    file.online_date = datetime.datetime.now()
                    file.download_date = datetime.datetime.now()
                if file.import_end_date is None:
                    file.import_start_date = datetime.datetime.now()
                    self.context.session.commit()
                    if not self.no_parsing:
                        self.parser = EtalabParser(self.context)
                        self.parser.load(file.full_name, header=True, encoding="ANSI", delimiter=";")
                        print(f"New etablissement: {self.parser.nb_new_entity}")
                        print(f"Update etablissement: {self.parser.nb_update_entity}")
                        print(f"New adresse: {self.parser.nb_new_adresse}")
                        print(f"New adresse normalized: {self.parser.nb_new_norm}")
                    file.import_end_date = datetime.datetime.now()
                    if file.id is None:
                        self.context.session.add(file)
                    if not self.no_commit:
                        self.context.session.commit()





if __name__ == '__main__':
    art.tprint(config.name, "big")
    print("Etalab Downloader")
    print("=================")
    print(f"V{config.version}")
    print(config.copyright)
    print()
    parser = argparse.ArgumentParser(description="Etalab Downloader")
    parser.add_argument("-e", "--echo", help="Sql Alchemy echo", action="store_true")
    parser.add_argument("-n", "--no_commit", help="No commit", action="store_true")
    parser.add_argument("-p", "--no_parsing", help="No parsing", action="store_true")
    args = parser.parse_args()
    context = Context()
    context.create(echo=args.echo, expire_on_commit=False)
    d = EtalabDownloader(context, args.echo, True, args.no_commit, True, args.no_parsing)
    d.dezips()
    d.load()
    print(f"Nb new files: {d.nb_new_file}")
