import argparse
import datetime
import os
import art
import config
from apl.ps_libreacces_raw_parser import PSLibreAccesRawParser
from diplome_parser import DiplomeParser
from downloader.base_downloader import BaseDownloader
from personne_activite_parser import PersonneActiviteParser
from sqlentities import Context, File


class PersonneActiviteDownloader(BaseDownloader):

    def __init__(self, context, echo=False, fake_download=False, no_commit=False, force_download=False, no_parsing=False):
        super().__init__(context, echo, fake_download, no_commit, force_download, no_parsing)
        self.url = "https://www.data.gouv.fr/datasets/annuaire-sante-extractions-des-donnees-en-libre-acces-des-professionnels-intervenant-dans-le-systeme-de-sante/"
        self.download_path = self.download_zip_path = "data/ps_libreacces/"
        self.category = "PsLibreAcces"
        self.frequency = "M"
        self.download_mode = "AUTO"

    def make_cache(self):
        print("Making cache")
        l: list[File] = self.context.session.query(File).filter(File.category == self.category).all()
        for e in l:
            self.files[e.name] = e


    def get_yearmonth_file_by_name(self, name: str) -> File:
        yearmonth = datetime.datetime.now().year * 100 + datetime.datetime.now().month
        if "personne" in name:
            name = f"PS_LibreAcces_Personne_activite_{yearmonth}000000.txt"
        elif "dipl" in name:
            name = f"PS_LibreAcces_Dipl_AutExerc_{yearmonth}000000.txt"
        elif "savoir" in name:
            name = f"PS_LibreAcces_SavoirFaire_{yearmonth}000000.txt"
        if name in self.files:
            return self.files[name]
        file = File(name, self.download_path, self.category, self.frequency, self.download_mode)
        file.date = datetime.date(yearmonth // 100, yearmonth % 100, 1)
        return file

    def scrap_url(self, file_name: str) -> str | None:
        node = self.soup.find("div", attrs={"text": file_name})
        if node is None:
            return None
        header = node.find_parent("header")
        url = header.find("a").attrs["href"]
        return url

    def scrap(self, file_name: str):
        url = self.scrap_url(file_name)
        if url is not None:
            file = self.get_yearmonth_file_by_name(file_name)
            file.url = url
            if file.download_date is None:
                if not self.fake_download:
                    self.download(file, file.url)
                else:
                    file.download_date = datetime.datetime.now()
                if not self.no_commit:
                    if file.id is None:
                        self.context.session.add(file)
                    self.context.session.commit()

    def scraps(self):
        files = ["ps-libreacces-dipl-autexerc.txt",
                 "ps-libreacces-savoirfaire.txt",
                 "ps-libreacces-personne-activite.txt"]
        for f in files:
            self.scrap(f)

    def load_file(self, file: File):
        file.import_start_date = datetime.datetime.now()
        if not self.no_parsing:
            print(f"Parse {file.name}")
            context = Context()
            context.create(echo=args.echo, expire_on_commit=False)
            if "Persone" in file.name:
                self.parser = PersonneActiviteParser(context)
            elif "Dipl" in file.name:
                self.parser = DiplomeParser(context)
            else:
                self.parser = DiplomeParser(context, savoir=True)
            self.parser.load(file.full_name)
            if "Persone" in file.name:
                self.parser = PSLibreAccesRawParser(context)
                self.parser.load(file.full_name)
                self.parser.commit()
            self.nb_new_file += 1
        file.import_end_date = datetime.datetime.now()
        if not self.no_commit:
            self.context.session.commit()

    def load(self):
        self.make_cache()
        files = sorted(self.files.values(), key=lambda f: len(f.name))
        for file in files:
            if file.import_end_date is None:
                self.load_file(file)


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
    d.make_cache()
    d.get_html()
    d.scraps()
    d.load()
    print(f"Nb new files: {d.nb_new_file}")
