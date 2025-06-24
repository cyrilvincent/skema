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
from downloader.ps_downloader import PSDownloader
from personne_activite_parser import PersonneActiviteParser
from ps_parser import PSParser
from ps_tarif_parser import PSTarifParser
from sqlentities import Context, File, BAN
from bs4 import BeautifulSoup
import re


class PSDailyDownloader(PSDownloader):

    def __init__(self, context, echo=False, fake_download=False, no_commit=False, force_download=False, no_parsing=False):
        super().__init__(context, echo, fake_download, no_commit, force_download, no_parsing)
        self.url = "https://www.data.gouv.fr/fr/datasets/r/1911e468-3748-424b-8fb6-7738bbd8884f"
        self.download_path = "data/ps/daily/"
        self.now = datetime.date.today()

    def make_cache(self):
        pass

    def test(self):
        pass

    def downloads(self):
        name = f"ps-tarifs-{self.now.year - 2000}-{self.now.month:02d}-{self.now.day:02d}.csv"
        print(f"Download {self.url} to {self.download_path+name}")
        self.download_file(self.url, self.download_path+name)


if __name__ == '__main__':
    art.tprint(config.name, "big")
    print("PS Daily Downloader")
    print("===================")
    print(f"V{config.version}")
    print(config.copyright)
    print()
    parser = argparse.ArgumentParser(description="PS Daily Downloader")
    args = parser.parse_args()
    d = PSDailyDownloader(None)
    d.downloads()
