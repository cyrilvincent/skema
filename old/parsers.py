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
            regex = r'/professionnels-de-sante/recherche/liste-resultats-page-([\d]+)-par_page-20-tri-\w+_\w+.html'
            try:
                match = re.search(regex, href)
                self.nbpage = int(match[1])
            except Exception as ex:
                print(f"WARNING: soup_nbpage {ex}")

    def soup_entities(self):
        tags = self.soup.find_all("strong")
        for tag in tags:
            name = str(tag.contents[0]).replace(",", " ")
            href = tag.parent.attrs["href"]
            fname = str(tag.nextSibling)
            if fname is not None:
                fname = fname.strip().replace(",", " ")
            regex = r'/professionnels-de-sante/recherche/fiche-detaillee-([\d\w]+).html'
            match = re.search(regex, href)
            id = match[1]
            entity = Entity(id, name)
            root = tag.parent.parent.parent.parent
            entity.convention = self.soup_convention(root)
            entity.phone = self.soup_phone(root)
            entity.speciality = self.soup_speciality(root)
            entity.fname = fname
            entity.vitale = self.soup_vitale(root)
            entity.address = self.soup_address(root)
            entity.honoraire = self.soup_honoraire(root)
            self.entities[id] = entity

    def soup_convention(self, root):
        tag = root.find("div", attrs={"class": "convention"})
        if tag is not None:
            a = tag.findChildren("a")
            if len(a) > 0:
                return str(a[0].contents[0])
        return None

    def soup_phone(self, root):
        tag = root.find("div", attrs={"class": "tel"})
        if tag is not None:
            return str(tag.contents[0]).replace('\xa0', '')
        return None

    def soup_speciality(self, root):
        tag = root.find("div", attrs={"class": "specialite"})
        if tag is not None:
            return str(tag.contents[0])
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
            return s.replace(",", " ")
        return None

    def soup_honoraire(self, root):
        tag = root.find("div", attrs={"class": "type_honoraires"})
        if tag is not None:
            a = tag.find("a")
            if a is None:
                return str(tag.contents[0])
            else:
                return str(a.contents[0])
        return None

    def soups(self):
        self.soup_nbpage()
        self.soup_entities()


