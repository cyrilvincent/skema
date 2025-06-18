import argparse
import art
import config
from download.downloader import BaseDownloader
from sqlentities import Context, File, BAN


class BANDownloader(BaseDownloader):

    def __init__(self, context, echo=False, fake_download=False, no_commit=False, force_download=False):
        super().__init__(context, echo, fake_download, no_commit, force_download)
        self.url = "https://adresse.data.gouv.fr/data/ban/adresses/latest/csv/"
        self.download_path = "data/adresse/"
        self.download_zip_path = self.download_path
        self.category = "BAN"
        self.files: dict[str, File] = {}
        self.make_cache()

    def make_cache(self):
        l: list[File] = self.context.session.query(File).filter(File.category == "BAN").all()
        for e in l:
            self.files[e.zip_name] = e

    def _get_file(self, zip_name: str) -> File:
        if zip_name in self.files:
            return self.files[zip_name]
        file = File(zip_name, self.download_zip_path, self.category)
        return file

    def downloads(self):
        super().downloads()
        for dept in self.deptrange():
            file = self._get_file(f"adresses-{dept}.csv.gz")
            self.download_and_dezip(file, "gz")
            file = self._get_file(f"lieux-dits-{dept}-beta.csv.gz")
            self.download_and_dezip(file, "gz")

    def parses(self):
        super().parses()
        files: list[File] = (self.context.session.query(File)
                             .filter((File.category == "BAN") & (File.dezip_date.isnot(None))))




if __name__ == '__main__':
    art.tprint(config.name, "big")
    print("BAN Downloader")
    print("==============")
    print(f"V{config.version}")
    print(config.copyright)
    print()
    parser = argparse.ArgumentParser(description="BAN Downloader")
    parser.add_argument("-e", "--echo", help="Sql Alchemy echo", action="store_true")
    parser.add_argument("-f", "--fake_download", help="Faking the download and dezip", action="store_true")
    parser.add_argument("-d", "--force_download", help="Force the download and dezip", action="store_true")
    parser.add_argument("-n", "--no_commit", help="No commit", action="store_true")
    args = parser.parse_args()
    context = Context()
    context.create(echo=args.echo)
    d = BANDownloader(context, args.echo, args.fake_download, args.no_commit, args.force_download)
    d.downloads()
    print(f"Nb new files: {d.nb_new_file}")
