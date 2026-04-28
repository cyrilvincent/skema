import asyncio
import os
import time
from playwright.async_api import async_playwright, Browser, BrowserContext, Page, Playwright
from bs4 import BeautifulSoup, PageElement
import json
import datetime
import re

class UrlDTO:

    def __init__(self, keyword: str, location: str, page=1, avaibilities=0, last_name=""):
        self.keyword = keyword
        self.location = location
        self.page = page
        self.avaibilities = avaibilities
        self.last_name = last_name


class TarifDoctolibDTO:

    label: str
    tarif_string: str
    tarif: float | None = None
    tarif_max: float | None = None

    def __repr__(self):
        return f"Tarif {self.label} {"None" if self.tarif is None else self.tarif}€"


class PSDoctolibDTO:

    id: int
    pid: str
    name: str
    url: str
    nick: str
    speciality: str
    city: str
    type: str | None = None
    street: str | None = None
    cp: str | None = None
    locality: str | None = None
    rdv_text: str | None = None
    rdv_date: datetime.date | None = None
    now = datetime.date.today()
    rdv_days: int | None = None
    rdv_type = 0
    convention: str | None = None
    carte_vitale: bool | None = None
    address_name: str | None = None
    address: str | None = None
    tarifs: list[TarifDoctolibDTO] = []


    def __init__(self, speciality):
        self.speciality = speciality

    def __repr__(self):
        return f"PS {self.pid} {self.type} {self.nick} {self.speciality} {self.city}"


class DoctolibScraper:

    def __init__(self, headless=False, width=800, height=900):
        self.headless = headless
        self.width = width
        self.height = height
        self.browser: Browser | None = None
        self.context: BrowserContext | None = None
        self.page: Page | None = None
        self.home_url = "https://www.doctolib.fr/search?keyword={keyword}&location={location}&page={page}"
        self.url = "https://www.doctolib.fr"
        self.content = ""

    async def launch(self, manager: Playwright):
        self.browser = await manager.chromium.launch(headless=False)
        self.context = await self.browser.new_context(viewport={"width": self.width, "height": self.height})
        self.page = await self.context.new_page()

    def get_url_by_dto(self, dto: UrlDTO) -> str:
        url = self.home_url.replace("{keyword}", dto.keyword)
        url = url.replace("{location}", dto.location)
        url = url.replace("{page}", str(dto.page))
        if dto.avaibilities > 0:
            url += f"&availabilitiesBefore={dto.avaibilities}"
        return url

    async def goto(self, url: str):
        print(f"Load {url}")
        await self.page.goto(url)
        await self.page.wait_for_selector("footer")
        print("Loaded")
        await self.page.wait_for_timeout(100)

    async def goto_home(self, dto: UrlDTO):
        url = self.get_url_by_dto(dto)
        await self.goto(url)

    async def goto_ps(self, dto: PSDoctolibDTO):
        await self.goto(self.url + dto.url)

    async def accept_cookies(self):
        print("Accept Cookies")
        for _ in range(5):
            print("Tab")
            await self.page.keyboard.press("Tab")
            await self.page.wait_for_timeout(100)
        print("Enter")
        await self.page.keyboard.press("Enter")
        await self.page.wait_for_timeout(100)

    async def goto_end(self):
        print("End")
        await self.page.keyboard.press("End")
        await self.page.wait_for_timeout(3000)

    async def get_content(self):
        self.content = await self.page.content()

    def test_last_name(self, dto: UrlDTO) -> bool:
        if dto.last_name.upper() in self.content.upper():
            print(f"OK for {dto.last_name}")
            return True
        print(f"Not OK for {dto.last_name}")
        return False

    def save(self, dir: str, name: str, dto: UrlDTO):
        path = f"{dir}/{name}_{dto.keyword}_{dto.location}_{dto.avaibilities}_{dto.page}.html"
        print(f"Saving {path}")
        with open(path, "w", encoding="utf-8") as f:
            f.write(self.content)

    def save_ps(self, dir: str, dto: PSDoctolibDTO):
        path = f"{dir}/ps_{dto.nick}_{dto.speciality}.html"
        print(f"Saving {path}")
        with open(path, "w", encoding="utf-8") as f:
            f.write(self.content)


class DoctolibParser:

    def __init__(self, dir="out"):
        self.content = ""
        self.dir = dir
        self.name = ""
        self.dto: UrlDTO | None = None
        self.html: BeautifulSoup | None = None
        self.json = {}
        self.months = {"janvier": 1, "février": 2, "mars": 3, "avril": 4, "mai": 5, "juin": 6,
                       "juillet": 7, "août": 8, "septembre": 9, "octobre": 10, "novembre": 11, "décembre": 12}

    def _load(self, path: str) -> bool:
        if os.path.isfile(path):
            print(f"Loading {path}")
            with open(path, "r", encoding="utf-8") as f:
                self.content = f.read()
            self.html = BeautifulSoup(self.content, features="lxml")
            return True
        return False

    def load(self, name: str, dto: UrlDTO) -> bool:
        self.name = name
        self.dto = dto
        path = f"{self.dir}/{name}_{dto.keyword}_{dto.location}_{dto.avaibilities}_{dto.page}.html"
        return self._load(path)

    def find_json(self):
        node = self.html.find("script", attrs={"data-id": "removable-json-ld"})
        self.json = json.loads(node.text)
        # self.save_json()

    def find_h2_dr(self) -> list[PSDoctolibDTO]:
        pss: list[PSDoctolibDTO] = []
        nodes = self.html.find_all("h2")
        for node in nodes:
            ps = PSDoctolibDTO(dto.keyword)
            ps.name = node.text
            if "href" in node.parent.attrs.keys():
                ps.url = node.parent.attrs["href"]
                pid = self.get_pid_from_url(ps.url)
                if pid is not None:
                    ps.pid = pid
                    ps.id = int(pid[pid.rindex("-") + 1:])
                    ps.nick = self.get_nick_from_url(ps.url)
                    ps.city = self.get_city_from_url(ps.url)
                    self.join_ps_json(ps)
                    self.get_rdv(node, ps)
                    pss.append(ps)
        return pss

    def join_ps_json(self, ps: PSDoctolibDTO):
        item = self.get_item_json_by_pid(ps.pid)
        if item is not None:
            ps.type = item["@type"]
            ps.street = item["address"]["streetAddress"]
            ps.cp = item["address"]["postalCode"]
            ps.locality = item["address"]["addressLocality"]

    def get_pid_from_url(self, url: str) -> str | None:
        if "pid=" in url:
            pid = url[url.index("pid=") + 4:]
            if "&" in pid:
                pid = pid[:pid.index("&")]
            return pid
        return None

    def get_nick_from_url(self, url: str) -> str:
        nick = url[:url.index("?")]
        nick = nick[nick.rindex("/") + 1:]
        return nick

    def get_city_from_url(self, url: str) -> str:
        city = url[1:]
        city = city[city.index("/") + 1:]
        city = city[:city.index("/")]
        return city

    def save_json(self):
        path = (f"{self.dir}/{self.name}_{self.dto.keyword}_{self.dto.location}_{self.dto.avaibilities}_{self.dto.page}"
                f".json")
        print(f"Saving {path}")
        with open(path, "w", encoding="UTF-8") as f:
            json.dump(self.json, f, indent=2)

    def get_item_json_by_pid(self, pid: str) -> dict | None:
        items = self.json["mainEntity"]["itemListElement"]
        for item in items:
            if pid in item["item"]["url"]:
                return item["item"]
        return None

    def get_rdv(self, node: PageElement, ps: PSDoctolibDTO):
        ancestor = node.parent.parent.parent.parent.parent.parent.parent
        div = ancestor.find("div", attrs={"data-test-id": "availabilities-container"})
        if div is not None:
            if "Ce soignant réserve" in div.get_text():
                ps.rdv_type = 1
            elif "Aucune disponibilité" in div.get_text():
                ps.rdv_type = 2
            else:
                ps.rdv_type = 3
                spans = div.find_all("span", attrs={"data-design-system-component": "Text", "data-design-system": "oxygen"})
                if len(spans) > 0:
                    ps.rdv_text = spans[0].text
                    if ps.rdv_text is not None:
                        text = ps.rdv_text
                        text = text.replace("Matin", "").replace("Après-midi", "")
                        ps.rdv_date = self.get_date_from_text(text)
                        if ps.rdv_date is not None:
                            ps.rdv_days = (ps.rdv_date - ps.now).days

    def get_date_from_text(self, text: str) -> datetime.date | None:
        short_regex = r"^\w{3}\. (\d?\d$)"
        groups = re.match(short_regex, text)
        today = datetime.date.today()
        if groups is not None:
            day = int(groups[1])
            month = today.month
            year = today.year
            if day < today.day:
                month += 1
                if month > 12:
                    month = 1
                    year += 1
            return datetime.date(year, month, day)
        long_regex = r"^\w+\s(\d?\d)\s(\w+)$"
        groups = re.match(long_regex, text)
        if groups is not None:
            day = int(groups[1])
            month = int(self.months[groups[2]])
            year = today.year if month >= today.month else today.year + 1
            return datetime.date(year, month, day)
        return None

    def has_next_page(self) -> bool:
        node = self.html.find("a", href=lambda h: h and f"page={dto.page + 1}" in h)
        print(node)
        return node is not None


class DoctolibPSParser(DoctolibParser):

    def __init__(self, dir="out"):
        super().__init__(dir)
        self.name = "ps"
        self.dto: PSDoctolibDTO | None = None

    def load(self, dto: PSDoctolibDTO) -> bool:
        self.dto = dto
        path = f"{self.dir}/ps_{dto.nick}_{dto.speciality}.html"
        return self._load(path)

    def find_infos(self):
        node = self.html.find(string=lambda t: t and "Tarifs et remboursement" in t)
        if node is not None:
            parent = node.parent
            print(parent)
            p = parent.find("p")
            if p is not None:
                if "dépassement" in p.text:
                    self.dto.convention = "C2"
                elif "secteur 1" in p.text:
                    self.dto.convention = "C1"
                elif "secteur 2" in p.text:
                    self.dto.convention = "C3"
                elif "non" in p.text:
                    self.dto.convention = "NC"
            if parent.parent.find(string="Carte Vitale acceptée"):
                self.dto.carte_vitale = True
            elif parent.parent.finf(string="Carte Vitale non acceptée"):
                self.dto.carte = False
        node = self.html.find(string="Carte et informations d'accès")
        if node is not None:
            parent = node.parent.parent
            h2 = parent.find("h2", class_="dl-profile-practice-name")
            if h2 is not None:
                self.dto.address_name = h2.text
            div = parent.find("div", id=True)
            if div is not None:
                self.dto.address = div.text
        self.find_tarifs()

    def find_tarifs(self):
        nodes = self.html.find_all("div", class_="dl-profile-fee")
        for node in nodes:
            name = node.find("span", class_="dl-profile-fee-name")
            if name is not None:
                tarif = TarifDoctolibDTO()
                tarif.label = name.text
                tag = node.find("span", class_="dl-profile-fee-tag")
                tarif.tarif_string = tag.text
                regex = r"\d+"
                groups = re.findall(regex, tarif.tarif_string)
                if len(groups) > 0:
                    tarif.tarif = float(groups[0])
                    if len(groups) > 1:
                        tarif.tarif_max = float(groups[1])
                self.dto.tarifs.append(tarif)
                print(tarif)







class DoctolibEngine:

    def __init__(self, player: Playwright):
        self.player = player
        self.scraper = DoctolibScraper()

    async def scrap_home_light(self, dto: UrlDTO):
        await self.scraper.launch(self.player)
        await self.scraper.goto_home(dto)
        await self.scraper.accept_cookies()

    async def scrap_home(self, dto: UrlDTO):
        await self.scrap_home_light(dto)
        await self.scraper.goto_end()
        await self.scraper.get_content()
        self.scraper.test_last_name(dto)
        self.scraper.save("out", "home", dto)

    async def scrap_page(self, dto: UrlDTO):
        await self.scraper.goto_home(dto)
        await self.scraper.goto_end()
        await self.scraper.get_content()
        self.scraper.save("out", "home", dto)

    async def scrap_ps(self, dto: PSDoctolibDTO):
        await self.scraper.goto_ps(dto)
        await self.scraper.get_content()
        self.scraper.save_ps("out", dto)


class DoctolibWorkflow:

    def __init__(self):
        self.parser = DoctolibParser()

    async def go(self, dto: UrlDTO):
        async with async_playwright() as p:
            e = DoctolibEngine(p)
            await e.scrap_home(dto)
            while True:
                self.parser.load("home", dto)
                if self.parser.has_next_page():
                    time.sleep(4)
                    dto.page += 1
                    await e.scrap_page(dto)
                else:
                    break

    def parse_all(self, dto: UrlDTO):
        dto.page = 1
        while True:
            ok = self.parser.load("home", dto)
            if not ok:
                break
            w.parser.find_json()
            pss = w.parser.find_h2_dr()
            for ps in pss:
                print(ps)
                print(ps.rdv_type, ps.rdv_text, ps.rdv_date, ps.rdv_days)
            dto.page += 1

    async def scrap_pss(self, dto: UrlDTO):
        async with async_playwright() as p:
            e = DoctolibEngine(p)
            await e.scrap_home_light(dto)
            dto.page = 1
            while True:
                ok = self.parser.load("home", dto)
                if not ok:
                    break
                self.parser.find_json()
                pss = self.parser.find_h2_dr()
                for ps in pss:
                    time.sleep(3.5)
                    await e.scrap_ps(ps)
                dto.page += 1



if __name__ == '__main__':
    # dto = UrlDTO("dermatologue", "alpes-maritimes", 1, 14, "KIRSTEN")
    # dto = UrlDTO("dermatologue", "france", 1, 14, "Baratte")
    dto = UrlDTO("dermatologue", "alpes-maritimes", 1, 0, "")
    w = DoctolibWorkflow()
    # asyncio.run(w.go(dto))
    # w.parse_all(dto)
    # asyncio.run(w.scrap_pss(dto))

    pps = DoctolibPSParser()
    ps_dto = PSDoctolibDTO("dermatologue")
    ps_dto.nick = "buhas-buhas"
    pps.load(ps_dto)
    pps.find_infos()


    # dto.page = 3
    # w.parser.load("home", dto)
    # w.parser.find_json()
    # pss = w.parser.find_h2_dr()
    # for ps in pss:
    #     print(ps)
    #     print(ps.rdv_type, ps.rdv_text, ps.rdv_date, ps.rdv_days)
    # print(w.parser.has_next_page())
