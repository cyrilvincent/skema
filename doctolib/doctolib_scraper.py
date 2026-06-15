import argparse
import asyncio
import os
import time
import art
from playwright.async_api import async_playwright, Browser, BrowserContext, Page, Playwright
from playwright._impl._errors import TimeoutError
from bs4 import BeautifulSoup, PageElement
import json
import datetime
import re
from sqlalchemy.orm import joinedload
import config
from sqlentities import PS, Tarif, Context


class UrlDTO:

    def __init__(self, keyword: str, location: str, page=1, avaibilities=0, last_name=""):
        super().__init__()
        self.keyword = keyword
        self.location = location
        self.page = page
        self.avaibilities = avaibilities
        self.last_name = last_name


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

    async def goto_ps(self, dto: PS):
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

    def save_ps(self, dir: str, dto: PS):
        path = f"{dir}/ps_{dto.nick}_{dto.speciality}.html"
        print(f"Saving {path}")
        with open(path, "w", encoding="utf-8") as f:
            f.write(self.content)

    def ps_exist(self, dir: str, dto: PS):
        path = f"{dir}/ps_{dto.nick}_{dto.speciality}.html"
        return os.path.isfile(path)


class DoctolibParser:

    def __init__(self, dir="out", now: datetime.date | None=None):
        self.content = ""
        self.dir = dir
        self.name = ""
        self.now = now
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

    def check_date(self, name: str, dto: UrlDTO):
        path = f"{self.dir}/{name}_{dto.keyword}_{dto.location}_{dto.avaibilities}_{dto.page}.html"
        ctime = os.path.getctime(path)
        self.now = datetime.datetime.fromtimestamp(ctime).date()
        print(f"Setting date to {self.now}")

    def home_exist(self, dir: str, dto: UrlDTO):
        path = f"{dir}/home_{dto.keyword}_{dto.location}_{dto.avaibilities}_{dto.page}.html"
        return os.path.isfile(path)

    def find_json(self):
        node = self.html.find("script", attrs={"data-id": "removable-json-ld"})
        self.json = json.loads(node.text)
        # self.save_json()

    def find_h2_dr(self) -> list[PS]:
        pss: list[PS] = []
        nodes = self.html.find_all("h2")
        for node in nodes:
            ps = PS(dto.keyword, self.now)
            ps.name = node.text
            ps.video = "vidéo" in ps.name
            if "," in ps.name:
                ps.name = ps.name[:ps.name.index(",")]
            if "href" in node.parent.attrs.keys():
                ps.url = node.parent.attrs["href"]
                ps.short_url = f"https://www.doctolib.fr{ps.url[:ps.url.index("?")]}"
                pid = self.get_pid_from_url(ps.url)
                if pid is not None:
                    ps.pid = pid
                    ps.nick = self.get_nick_from_url(ps.url)
                    ps.city = self.get_city_from_url(ps.url)
                    self.join_ps_json(ps)
                    self.get_rdv(node, ps)
                    pss.append(ps)
        return pss

    def join_ps_json(self, ps: PS):
        item = self.get_item_json_by_pid(ps.pid)
        if item is not None:
            ps.medical_speciality = item["medicalSpecialty"]
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

    def get_rdv(self, node: PageElement, ps: PS):
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
        if groups is not None:
            day = int(groups[1])
            month = self.now.month
            year = self.now.year
            if day < self.now.day:
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
            year = self.now.year if month >= self.now.month else self.now.year + 1
            return datetime.date(year, month, day)
        return None

    def has_next_page(self) -> bool:
        node = self.html.find("a", href=lambda h: h and f"page={dto.page + 1}" in h)
        print(node)
        return node is not None


class DoctolibPSParser(DoctolibParser):

    def __init__(self, datesource_id: int, dir="out"):
        super().__init__(dir)
        self.datesource_id = datesource_id
        self.name = "ps"
        self.dto: PS | None = None

    def load(self, dto: PS) -> bool:
        self.dto = dto
        path = f"{self.dir}/ps_{dto.nick}_{dto.speciality}.html"
        return self._load(path)

    def find_infos(self):
        if self.html:
            node = self.html.find(string=lambda t: t and "Tarifs et remboursement" in t)
            if node is not None:
                p = node.parent.parent.parent.parent.parent
                if p is not None:
                    if "dépassement" in p.text:
                        self.dto.convention = "C2"
                    elif "secteur 1" in p.text:
                        self.dto.convention = "C1"
                    elif "secteur 2" in p.text:
                        self.dto.convention = "C3"
                    elif "non" in p.text:
                        self.dto.convention = "NC"
                    if p.find(string="Carte Vitale acceptée"):
                        self.dto.carte_vitale = True
                    elif p.find(string="Carte Vitale non acceptée"):
                        self.dto.carte = False
            nodes = self.html.find_all(string="Adresses")
            if len(nodes) > 0:
                node = nodes[-1]
                p = node.parent.parent.parent.parent
                span = p.find("span", class_="break-all")
                if span is not None:
                    self.dto.address = span.text
            self.dto.new_patient = self.html.find("p", string=lambda t: t and "Ce soignant réserve la prise" in t) is None
            if self.dto.new_patient:
                self.dto.new_patient = self.html.find("p", string=lambda t: t and "pas de nouveau patient" in t) is None
            self.find_tarifs()
            self.find_legals()
        else:
            print("No HTML")

    def find_tarifs(self):
        node = self.html.find("h2", string="Tarifs et remboursement")
        if node is not None:
            p = node.parent.parent.parent.parent
            ul = p.find("ul")
            if ul is not None:
                lis = ul.find_all("li")
                for li in lis:
                    div = li.find("div", attrs={"data-test": "profiles-details-fees-name"})
                    if div is not None:
                        tarif = Tarif()
                        tarif.label = div.text
                        tarif.datesource_id = self.datesource_id
                        tag = li.find("div", attrs={"data-test": "profiles-details-fees-price"})
                        tarif.tarif_string = tag.text
                        regex = r'\d{1,3}(?:\s\d{3})*(?:,\d+)?'  # r"\d+(?:,\d+)?"
                        groups = re.findall(regex, tarif.tarif_string)
                        if len(groups) > 0:
                            tarif.tarif = float(groups[0].replace(",", ".").replace(" ", ""))
                            if len(groups) > 1:
                                tarif.tarif_max = float(groups[1].replace(",", ".").replace(" ", ""))
                        self.dto.tarifs.append(tarif)
                        print(tarif)

    def find_legals(self):
        node = self.html.find(string="Informations légales")
        if node is not None:
            node = node.parent.parent.parent
            rpps = node.find(string="Numéro RPPS : ")
            if rpps is not None:
                self.dto.rpps = rpps.parent.parent.find_all("span")[-1].text
            adeli = node.find(string="Numéro ADELI : ")
            if adeli is not None:
                self.dto.adeli = adeli.parent.parent.find_all("span")[-1].text
            siren = node.find(string="SIREN")
            if siren is not None:
                self.dto.siren = siren.parent.parent.find_all("span")[-1].text


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

    async def scrap_ps(self, dto: PS) -> bool:
        exist = self.scraper.ps_exist("out", dto)
        if not exist:
            try:
                await self.scraper.goto_ps(dto)
            except TimeoutError as ex:
                print(ex)
                time.sleep(30)
                await self.scraper.goto_ps(dto)
            time.sleep(3)
            await self.scraper.get_content()
            self.scraper.save_ps("out", dto)
        return exist


class DoctolibWorkflow:

    def __init__(self, context, datesource_id: int):
        self.parser = DoctolibParser("out")
        self.context = context
        self.datesource_id = datesource_id
        self.pss: dict[str, PS] = {}
        self.tarifs: dict[tuple[int, str], Tarif] = {}  # ps_id, label
        self.nb_ram = 0
        self.ps_results: list[PS] = []

    def make_cache(self):
        print("Making cache")
        l: list[PS] = (self.context.session.query(PS).options(joinedload(PS.tarifs)).all())
        for e in l:
            self.pss[e.nick] = e
            self.nb_ram += 1
        l: list[Tarif] = self.context.session.query(Tarif).filter(Tarif.datesource_id == self.datesource_id).all()
        for e in l:
            self.tarifs[e.key] = e
            self.nb_ram += 1

    async def go(self, dto: UrlDTO):
        async with async_playwright() as p:
            e = DoctolibEngine(p)
            await e.scrap_home(dto)
            while True:
                self.parser.load("home", dto)
                if self.parser.has_next_page():
                    # exist = self.parser.home_exist("out", dto)
                    dto.page += 1
                    # if not exist:
                    time.sleep(5)
                    await e.scrap_page(dto)
                else:
                    break

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
                sleep = 3
                for ps in pss:
                    time.sleep(sleep)
                    exist = await e.scrap_ps(ps)
                    sleep = 0 if exist else 3
                dto.page += 1
                time.sleep(sleep)

    def parse_all(self, dto: UrlDTO):
        dto.page = 1
        self.ps_results = []
        while True:
            ok = self.parser.load("home", dto)
            if not ok:
                break
            self.parser.check_date("home", dto)
            w.parser.find_json()
            pss = w.parser.find_h2_dr()
            for ps in pss:
                print(ps)
                if ps.rdv_text is None and ps.rdv_days is not None:
                    input()
                if ps.rdv_text is not None:
                    print(ps.rdv_type, ps.rdv_text, ps.rdv_date, ps.now, ps.rdv_days)
                    print()
                self.parse_ps(ps)
                self.ps_results.append(ps)
            dto.page += 1

    def parse_ps(self, dto: PS):
        pps = DoctolibPSParser(self.datesource_id)
        pps.load(dto)
        pps.find_infos()

    def commit(self):
        print(f"Commit {len(self.ps_results)} PS in {self.datesource_id}")
        for ps in self.ps_results:
            if ps.nick not in self.pss.keys():
                self.pss[ps.nick] = ps
                self.context.session.add(ps)
        self.context.session.commit()


if __name__ == '__main__':
    art.tprint(config.name, "big")
    print("Doctolib Scraper")
    print("================")
    print(f"V{config.version}")
    print(config.copyright)
    print()
    parser = argparse.ArgumentParser(description="PS Parser")
    parser.add_argument("-e", "--echo", help="Sql Alchemy echo", action="store_true")
    args = parser.parse_args()
    context = Context()
    context.create(echo=args.echo)

    dto = UrlDTO("dermatologue", "alpes-maritimes", 1, 0, "") # /!\ ps avec l'ancien parser
    dto = UrlDTO("pediatre", "alpes-maritimes", 1, 0, "")
    dto = UrlDTO("medecin-generaliste", "alpes-maritimes", 1, 0, "")
    dto = UrlDTO("psychiatre", "alpes-maritimes", 1, 0, "")
    dto = UrlDTO("gastro-enterologue", "alpes-maritimes", 1, 0, "")
    dto = UrlDTO("gynecologue", "alpes-maritimes", 1, 0, "")
    dto = UrlDTO("ophtalmologue", "alpes-maritimes", 1, 0, "")
    dto = UrlDTO("cardiologue", "alpes-maritimes", 1, 0, "")
    dto = UrlDTO("neurologue", "alpes-maritimes", 1, 0, "")
    dto = UrlDTO("orl-oto-rhino-laryngologie", "alpes-maritimes", 1, 0, "")
    dto = UrlDTO("pneumologue", "alpes-maritimes", 1, 0, "")
    dto = UrlDTO("rhumatologue", "alpes-maritimes", 1, 0, "")
    dto = UrlDTO("stomatologue", "alpes-maritimes", 1, 0, "")
    dto = UrlDTO("infirmier", "alpes-maritimes", 1, 0, "")
    dto = UrlDTO("sage-femme", "alpes-maritimes", 1, 0, "")
    dto = UrlDTO("masseur-kinesitherapeute", "alpes-maritimes", 1, 0, "")
    dto = UrlDTO("psychologue", "alpes-maritimes", 1, 0, "")
    # dto = UrlDTO("dentiste", "alpes-maritimes", 1, 0, "")

    w = DoctolibWorkflow(context, 2606)
    #
    # asyncio.run(w.go(dto))  # Do the scrap & parse_all & commit the same time
    # time.sleep(5)  # Never test go + scrap_pss at the same time
    #
    # try:
    #     asyncio.run(w.scrap_pss(dto))
    # except:
    #     try:
    #         asyncio.run(w.scrap_pss(dto))
    #     except:
    #         asyncio.run(w.scrap_pss(dto))

    w.make_cache()  # Never test parse_all & go & scrap_pss at the same time
    w.parse_all(dto)
    input("Commit ?")
    w.commit()

    # Debug for one PS
    # ps_dto = PS("pediatre")
    # ps_dto.nick = "cathijean-suf"  # Ce soignant réserve la prise de rendez-vous en ligne aux patients déjà suivis.
    # pps = DoctolibPSParser(2606)
    # pps.load(ps_dto)
    # pps.find_infos()
    # w.parse_ps(ps_dto)

    # Debug for one home page
    # dto.page = 1
    # w.parser.load("home", dto)
    # w.parser.find_json()
    # pss = w.parser.find_h2_dr()
    # for ps in pss:
    #     print(ps)
    #     print(ps.rdv_type, ps.rdv_text, ps.rdv_date, ps.rdv_days)
    # print(w.parser.has_next_page())

