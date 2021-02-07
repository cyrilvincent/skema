import requests
import config
import abc
import time


class AbstractLoader(metaclass=abc.ABCMeta):

    def __init__(self, session: requests.Session):
        self.url: str = None
        self.session = session
        self.response: requests.Response = None
        self.ok = False

    @property
    def html(self) -> bool:
        return self.response.content

    def load(self, nbtry=config.nbtry):
        i = 0
        while i < nbtry:
            try:
                self.response = self.session.get(self.url, timeout=config.timeout)
                self.ok = self.response.ok
                i = nbtry
                time.sleep(config.sleep)
            except Exception:
                self.ok = False
                i += 1


class GoogleLoader(AbstractLoader):

    def __init__(self, session: requests.Session):
        super().__init__(session)
        self.url = "http://www.google.com/"


class AmeliLoader(AbstractLoader):

    def __init__(self, session: requests.Session):
        super().__init__(session)
        self.url = "http://annuairesante.ameli.fr/"
        self.post_url = "http://annuairesante.ameli.fr/recherche.html"

    def post(self, s: str, loc="", nbtry=config.nbtry * 2):
        i = 0
        while i < nbtry:
            try:
                data = {"ps_nom": s, "type": "ps", "ps_localisation": loc, "ps_proximite": False}
                self.response = self.session.post(self.post_url, data=data, allow_redirects=True, timeout=config.timeout * 2)
                self.ok = self.response.ok
                return self.response.history[0].headers["Location"] != "/modifier_votre_recherche.html"
            except:
                self.ok = False
                i += 1



class AmeliPageLoader(AbstractLoader):

    # 2 lettres + dept

    def __init__(self, session: requests.Session, page=1):
        super().__init__(session)
        self.page = page
        self.url = f"http://annuairesante.ameli.fr/professionnels-de-sante/recherche/liste-resultats-page-{self.page}-par_page-20-tri-nom_asc.html"


class AmeliDetailsLoader(AbstractLoader):

    def __init__(self, session: requests.Session, id):
        super().__init__(session)
        self.id = id
        self.url = f"http://annuairesante.ameli.fr//professionnels-de-sante/recherche/fiche-detaillee-{self.id}.html"


if __name__ == '__main__':
    gl = GoogleLoader()
    gl.load()