import bs4
import re

class AmeliPageParser:

    def __init__(self, html):
        self.html = html
        self.soup = bs4.BeautifulSoup(html, "html.parser")
        self.nbpage = 1
        self.items = {}

    def soup_nbpage(self):
        tag = self.soup.find("img", attrs={"alt": " - Aller à la dernière page"})
        if tag is not None:
            href = tag.parent.attrs["href"]
            regex = r'/professionnels-de-sante/recherche/liste-resultats-page-([\d]+)-par_page-20-tri-nom_asc.html'
            match = re.match(regex, href)
            self.nbpage = int(match[1])

    def soup_items(self):
        tags = self.soup.find_all("strong")
        for tag in tags:
            name = tag.contents[0]
            href = tag.parent.attrs["href"]
            regex = r'/professionnels-de-sante/recherche/fiche-detaillee-([\d\w]+).html'
            match = re.match(regex, href)
            id = match[1]
            self.items[id] = name

    def soups(self):
        self.soup_nbpage()
        self.soup_items()


class AmeliDetailsParser:

    def __init__(self, html):
        self.html = html
        self.soup = bs4.BeautifulSoup(html, "html.parser")
        self.phone = None
        self.convention = None

    def soup_phone(self):
        tag = self.soup.find("h2", attrs={"class": "tel"})
        if tag is not None:
            self.phone = tag.contents[0].replace('\xa0', '')

    def soup_convention(self):
        tag = self.soup.find("div", attrs={"class": "convention"})
        if tag != None:
            a = tag.findChildren("a")
            if len(a) > 0:
                self.convention = a[0].contents[0]

    def soups(self):
        self.soup_phone()
        self.soup_convention()
