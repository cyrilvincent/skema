import bs4
import re
from typing import List, Dict

class Entity:

    def __init__(self, id, name):
        self.id = id
        self.name = name
        self.fname = None
        self.phone = None
        self.convention = None
        self.dept = None
        self.speciality = None
        self.vitale = False
        self.address = None
        self.honoraire = None

class AmeliPageParser:

    def __init__(self, html):
        self.html = html
        self.soup = bs4.BeautifulSoup(html, "html.parser")
        self.nbpage = 1
        self.entities: Dict[str, Entity] = {}

    def soup_nbpage(self):
        tag = self.soup.find("img", attrs={"alt": " - Aller à la dernière page"})
        if tag is not None:
            href = tag.parent.attrs["href"]
            regex = r'/professionnels-de-sante/recherche/liste-resultats-page-([\d]+)-par_page-20-tri-nom_asc.html'
            match = re.match(regex, href)
            self.nbpage = int(match[1])

    def soup_entities(self):
        tags = self.soup.find_all("strong")
        for tag in tags:
            name = tag.contents[0]
            href = tag.parent.attrs["href"]
            fname = tag.nextSibling
            if fname is not None:
                fname = fname.strip()
            regex = r'/professionnels-de-sante/recherche/fiche-detaillee-([\d\w]+).html'
            match = re.match(regex, href)
            id = match[1]
            entity = Entity(id, name)
            root = tag.parent.parent.parent.parent
            entity.convention = self.soup_convention(root)
            entity.phone = self.soup_phone(root)
            entity.speciality = self.soup_speciality(root)
            entity.fname = fname
            entity.vitale = self.soup_vitale(root)
            entity.address = self.soup_address(root)
            self.entities[id] = entity

    def soup_convention(self, root):
        tag = root.find("div", attrs={"class": "convention"})
        if tag != None:
            a = tag.findChildren("a")
            if len(a) > 0:
                return a[0].contents[0]
        return None

    def soup_phone(self, root):
        tag = root.find("div", attrs={"class": "tel"})
        if tag is not None:
           return tag.contents[0].replace('\xa0', '')
        return None

    def soup_speciality(self, root):
        tag = root.find("div", attrs={"class": "specialite"})
        if tag is not None:
           return tag.contents[0]
        return None

    def soup_vitale(self, root):
        tag = root.find("img", attrs={"alt": "Ce professionnel de santé accepte la carte Vitale"})
        return tag is not None

    def soup_address(self, root):
        tag = root.find("div", attrs={"class": "adresse"})
        if tag is not None:
            s = ""
            for c in tag.contents:
                s += str(c)
            return s
        return None

    def soup_honoraire(self, root):
        tag = root.find("div", attrs={"class": "type_honoraires"})
        if tag is not None:
           return tag.contents[0]
        return None

    def soups(self):
        self.soup_nbpage()
        self.soup_entities()


# class AmeliDetailsParser:
#
#     def __init__(self, html):
#         self.html = html
#         self.soup = bs4.BeautifulSoup(html, "html.parser")
#         self.phone = None
#         self.convention = None
#
#     def soup_phone(self):
#         tag = self.soup.find("h2", attrs={"class": "tel"})
#         if tag is not None:
#             self.phone = tag.contents[0].replace('\xa0', '')
#
#     def soup_convention(self):
#         tag = self.soup.find("div", attrs={"class": "convention"})
#         if tag != None:
#             a = tag.findChildren("a")
#             if len(a) > 0:
#                 self.convention = a[0].contents[0]
#
#     def soups(self):
#         self.soup_phone()
#         self.soup_convention()
