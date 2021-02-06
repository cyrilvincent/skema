import requests
import bs4
import abc



class AbstractLoader(metaclass=abc.ABCMeta):

    def __init__(self, session: requests.Session):
        self.url: str = None
        self.session = session
        self.response: requests.Response = None

    @property
    def ok(self) -> bool:
        return self.response.ok

    @property
    def html(self) -> bool:
        return self.response.content

    def load(self):
        self.response = self.session.get(self.url)

class GoogleLoader(AbstractLoader):

    def __init__(self, session: requests.Session):
        super().__init__(session)
        self.url = "http://www.google.com/"


class AmeliLoader(AbstractLoader):

    def __init__(self, session: requests.Session):
        super().__init__(session)
        self.url = "http://annuairesante.ameli.fr/"
        self.post_url = "http://annuairesante.ameli.fr/recherche.html"

    def post(self, s: str, loc=""):
        data = {"ps_nom": s, "type": "ps", "ps_localisation": loc, "ps_proximite": False}
        self.response = self.session.post(self.post_url, data=data, allow_redirects=True)
        return self.response.history[0].headers["Location"] != "/modifier_votre_recherche.html"


class AmeliPageLoader(AbstractLoader):

    # 2 lettres + dept

    def __init__(self, session: requests.Session, page=1):
        super().__init__(session)
        self.page = page
        self.url = f"http://annuairesante.ameli.fr/professionnels-de-sante/recherche/liste-resultats-page-{self.page}-par_page-20-tri-nom_asc.html"


class AmeliDetailLoader(AbstractLoader):

    def __init__(self, session: requests.Session, id):
        super().__init__(session)
        self.id = id
        self.url = f"http://annuairesante.ameli.fr//professionnels-de-sante/recherche/fiche-detaillee-{self.id}.html"


if __name__ == '__main__':
    gl = GoogleLoader()
    gl.load()