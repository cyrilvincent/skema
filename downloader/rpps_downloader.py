import argparse
import datetime
import os
import art
import config
from downloader.base_downloader import BaseDownloader
from rpps_activite_parser import RPPSActiviteParser
from rpps_attribution_parser import RPPSAttributionParser
from rpps_autre_diplome_parser import RPPSAutreDiplomeParser
from rpps_coord_activite_parser import RPPSCoordActiviteParser
from rpps_coord_corresp_parser import RPPSCoordPersonneParser
from rpps_coord_structure_geoloc_parser import RPPSCoordStructureGeolocParser
from rpps_coord_structure_parser import RPPSCoordStructureParser
from rpps_diplome_obtenu_parser import RPPSDiplomeObtenuParser
from rpps_etat_civil_parser import RPPSEtatCivilParser
from rpps_exercice_pro_parser import RPPSExerciceProParser
from rpps_langue_parser import RPPSLangueParser
from rpps_personne_parser import RPPSPersonneParser
from rpps_reference_ae_parser import RPPSReferenceAEParser
from rpps_savoir_faire_parser import RPPSSavoirFaireParser
from rpps_structure_parser import RPPSStructureParser
from sqlentities import Context, File


class RPPSDownloader(BaseDownloader):

    def __init__(self, context, echo=False, fake_download=False, no_commit=False, force_download=False, no_parsing=False):
        super().__init__(context, echo, fake_download, no_commit, force_download, no_parsing)
        self.url = "https://annuaire.sante.fr/"
        self.download_path = "data/rpps/"
        self.download_zip_path = self.download_path
        self.category = "RPPS"
        self.frequency = "M"
        self.download_mode = "MAN_DEZIP"
        self.types = ["Personne", "Structure", "ExercPro", "Activite", "DiplObt", "AutreDiplObt", "SavoirFaire", "EtatCiv", "ReferAe", "Langue", "AttribPart", "CoordCorresp", "CoordAct", "CoordStruct", "CoordStructGeoloc"]
        self.yearmonth_files: dict[int, File] = {}
        self.make_cache()

    def make_cache(self):
        print("Making cache")
        l: list[File] = (self.context.session.query(File)
                         .filter(File.category == self.category).all())
        for e in l:
            self.files[e.name] = e
            self.yearmonth_files[e.date.year * 100 + e.date.month] = e

    def get_yearmonth_file_by_name(self, name: str) -> File:
        yearmonth = int(name[-16:-10])
        if yearmonth in self.yearmonth_files:
            return self.yearmonth_files[yearmonth]
        file = File(name, self.download_zip_path, self.category, self.frequency, self.download_mode)
        file.date = datetime.date(yearmonth // 100, yearmonth % 100, 1)
        return file

    def load_file_from_type(self, file: File, type: str):
        print(f"Scan {file.name}")
        if file.import_end_date is None:
            file.import_start_date = datetime.datetime.now()
            if not self.no_commit:
                self.context.session.add(file)
                self.context.session.commit()
            if not self.no_parsing:
                print(f"Parse {file.name}")
                context = Context()
                context.create(echo=args.echo, expire_on_commit=False)
                if type == "Personne":
                    self.parser = RPPSPersonneParser(context)  # Si trop lent à la fin mettre self.context
                elif type == "Structure":
                    self.parser = RPPSStructureParser(context)
                elif type == "ExercPro":
                    self.parser = RPPSExerciceProParser(context)
                elif type == "Activite":
                    self.parser = RPPSActiviteParser(context)
                elif type == "DiplObt":
                    self.parser = RPPSDiplomeObtenuParser(context)
                elif type == "AutreDiplObt":
                    self.parser = RPPSAutreDiplomeParser(context)
                elif type == "SavoirFaire":
                    self.parser = RPPSSavoirFaireParser(context)
                elif type == "EtatCiv":
                    self.parser = RPPSEtatCivilParser(context)
                elif type == "ReferAe":
                    self.parser = RPPSReferenceAEParser(context)
                elif type == "Langue":
                    self.parser = RPPSLangueParser(context)
                elif type == "AttribPart":
                    self.parser = RPPSAttributionParser(context)
                elif type == "CoordCorresp":
                    self.parser = RPPSCoordPersonneParser(context)
                elif type == "CoordAct":
                    self.parser = RPPSCoordActiviteParser(context)
                elif type == "CoordStruct":
                    self.parser = RPPSCoordStructureParser(context)
                elif type == "CoordStructGeoloc":
                    self.parser = RPPSCoordStructureGeolocParser(context)
                else:
                    raise ValueError(f"Bad RPPS type {type}")
                self.parser.load(file.full_name, delimiter=';', encoding="UTF-8", header=True)
                self.nb_new_file += 1
            file.import_end_date = datetime.datetime.now()
            if not self.no_commit:
                self.context.session.commit()

    def load(self):
        super().load()
        file: File | None = None
        for type in self.types:
            for item in os.listdir(self.download_path):
                yearmonth = item[-16:-10]
                if yearmonth.isnumeric():
                    yearmonth = int(yearmonth)
                    if item.endswith(".csv") and item.startswith(f"Extraction_RPPS_Profil4_{type}_{yearmonth}"):
                        if yearmonth > 202502:
                            try:
                                file = self.get_file_by_name(item)
                                file.date = datetime.date(yearmonth // 100, yearmonth % 100, 1)
                                self.load_file_from_type(file, type)
                                if not self.no_commit:
                                    if file.id is not None:
                                        self.context.session.add(file)
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
    print("RPPS Downloader")
    print("===============")
    print(f"V{config.version}")
    print(config.copyright)
    print()
    parser = argparse.ArgumentParser(description="RPPS Downloader")
    parser.add_argument("-e", "--echo", help="Sql Alchemy echo", action="store_true")
    parser.add_argument("-n", "--no_commit", help="No commit", action="store_true")
    parser.add_argument("-p", "--no_parsing", help="No parsing", action="store_true")
    args = parser.parse_args()
    context = Context()
    context.create(echo=args.echo, expire_on_commit=False)
    d = RPPSDownloader(context, args.echo, True, args.no_commit, True, args.no_parsing)
    d.load()
    print(f"Nb new files: {d.nb_new_file}")
