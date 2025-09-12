import argparse
import datetime
import os
import art
import config
from downloader.base_downloader import BaseDownloader
from ps_parser import PSParser
from ps_tarif_parser import PSTarifParser
from sqlentities import Context, File, BAN


class PSDownloader(BaseDownloader):

    def __init__(self, context, echo=False, fake_download=False, no_commit=False, force_download=False, no_parsing=False):
        super().__init__(context, echo, fake_download, no_commit, force_download, no_parsing)
        self.url = "https://www.data.gouv.fr/fr/datasets/r/1911e468-3748-424b-8fb6-7738bbd8884f"
        self.download_path = "data/ps/"
        self.download_zip_path = self.download_path
        self.category = "PS"
        self.frequency = "M"
        self.download_mode = "AUTO"
        self.make_cache()
        self.now = datetime.date.today()

    def test(self):
        pass

    def downloads(self):
        super().downloads()
        file = self.get_file_by_name(f"ps-tarifs-{self.now.year - 2000}-{self.now.month:02d}.csv")
        if file.download_date is None:
            self.download(file, self.url)
            if not self.no_commit:
                self.context.session.add(file)
                self.context.session.commit()

    def load(self):
        super().load()
        file: File | None = None
        for item in os.listdir(self.download_path):
            if item.endswith(".csv") and item.startswith(f"ps-tarifs-"):
                try:
                    yearmonth = int(item[-9:-7]) * 100 + int(item[-6:-4])
                    if yearmonth > 2505:
                        file = self.get_file_by_name(item)
                        if file.import_end_date is None:
                            print(f"Parse {file.name}")
                            file.date = datetime.date(self.now.year, self.now.month, 1)
                            file.import_start_date = datetime.datetime.now()
                            if not self.no_commit:
                                self.context.session.commit()
                            context = Context()
                            context.create(echo=self.echo, expire_on_commit=False)
                            db_size = context.db_size()
                            print(f"Database {context.db_name}: {db_size:.0f} Mb")
                            self.parser = PSParser(context)
                            if not self.no_parsing:
                                self.parser.load(file.full_name, encoding=None)
                                print(f"New PS: {self.parser.nb_new_entity}")
                                print(f"Existing PS: {self.parser.nb_existing_entity} ({self.parser.nb_new_entity + self.parser.nb_existing_entity})")
                                print(f"Dept >95 PS: {self.parser.nb_out_dept} ({self.parser.nb_new_entity + self.parser.nb_existing_entity + self.parser.nb_out_dept})")
                                print(f"New cabinet: {self.parser.nb_cabinet}")
                                print(f"New adresse: {self.parser.nb_new_adresse}")
                                print(f"New adresse normalized: {self.parser.nb_new_norm}")
                                print(f"Matching INPP: {self.parser.nb_inpps}/{self.parser.nb_unique_ps}: {(self.parser.nb_inpps / self.parser.nb_unique_ps) * 100:.0f}%")
                                print(f"Matched rules: {self.parser.rules}")
                                context = Context()
                                context.create(echo=self.echo, expire_on_commit=False)
                                self.parser = PSTarifParser(context)
                                self.parser.load(file.full_name, encoding=None)
                                print(f"New tarif: {self.parser.nb_tarif}")
                                print(f"Existing tarif: {self.parser.nb_existing_entity} ({self.parser.nb_tarif + self.parser.nb_existing_entity})")
                                print(f"Nb warning: {self.parser.nb_warning}")
                                new_db_size = context.db_size()
                                print(f"Database {context.db_name}: {new_db_size:.0f} MB")
                                print(f"Database grows: {new_db_size - db_size:.0f} MB ({((new_db_size - db_size) / db_size) * 100:.1f}%)")
                            file.import_end_date = datetime.datetime.now()
                            if not self.no_commit:
                                self.context.session.commit()
                except Exception as ex:
                    print(f"Error for parsing {type}")
                    file.log_date = datetime.datetime.now()
                    file.log(str(ex))
                    if not self.no_commit:
                        self.context.session.add(file)
                        self.context.session.commit()


if __name__ == '__main__':
    art.tprint(config.name, "big")
    print("PS Downloader")
    print("=============")
    print(f"V{config.version}")
    print(config.copyright)
    print()
    parser = argparse.ArgumentParser(description="PS Downloader")
    parser.add_argument("-e", "--echo", help="Sql Alchemy echo", action="store_true")
    parser.add_argument("-f", "--fake_download", help="Faking the downloader and dezip", action="store_true")
    parser.add_argument("-d", "--force_download", help="Force the downloader and dezip", action="store_true")
    parser.add_argument("-n", "--no_commit", help="No commit", action="store_true")
    parser.add_argument("-p", "--no_parsing", help="No parsing", action="store_true")
    args = parser.parse_args()
    context = Context()
    context.create(echo=args.echo, expire_on_commit=False)
    d = PSDownloader(context, args.echo, args.fake_download, args.no_commit, args.force_download, args.no_parsing)
    d.downloads()
    d.load()
    print(f"Nb new files: {d.nb_new_file}")
