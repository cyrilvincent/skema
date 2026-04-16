import asyncio
from playwright.async_api import async_playwright, Browser, BrowserContext, Page, Playwright
from bs4 import BeautifulSoup
import json


class UrlDTO:

    def __init__(self, keyword: str, location: str, page=1, avaibilities=0, last_name=""):
        self.keyword = keyword
        self.location = location
        self.page = page
        self.avaibilities = avaibilities
        self.last_name = last_name


class PSDoctolibDTO:

    id: int
    pid: str
    name: str
    url: str
    nick: str
    speciality: str
    city: str
    type: str | None
    street: str | None
    cp: str | None
    locality: str | None

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

    async def goto_home(self, dto: UrlDTO):
        url = self.get_url_by_dto(dto)
        print(f"Load {url}")
        await self.page.goto(url)
        await self.page.wait_for_selector("footer")
        print("Loaded")
        await self.page.wait_for_timeout(100)

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


class DoctolibParser:

    def __init__(self, dir="out"):
        self.content = ""
        self.dir = dir
        self.name = ""
        self.dto: UrlDTO | None = None
        self.html: BeautifulSoup | None = None
        self.json = {}

    def load(self, name: str, dto: UrlDTO):
        self.name = name
        self.dto = dto
        path = f"{self.dir}/{name}_{dto.keyword}_{dto.location}_{dto.avaibilities}_{dto.page}.html"
        print(f"Loading {path}")
        with open(path, "r", encoding="utf-8") as f:
            self.content = f.read()
        self.html = BeautifulSoup(self.content, features="lxml")

    def find_json(self):
        node = self.html.find("script", attrs={"data-id": "removable-json-ld"})
        self.json = json.loads(node.text)
        self.save_json()

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
                    # node.parent.parent.parent.parent.parent.parent.parent.find("div", attrs={"data-test-id": "availabilities-container"}).findAll("span", attrs={"data-design-system-component":"Text", "data-design-system":"oxygen"})
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


async def test(dto):
    s = DoctolibScraper()
    # dto = UrlDTO("dermatologue", "alpes-maritimes", 1, 14, "KIRSTEN")
    async with async_playwright() as p:
        await s.launch(p)
        await s.goto_home(dto)
        await s.accept_cookies()
        await s.goto_end()
        await s.get_content()
        s.test_last_name(dto)
        s.save("out", "home", dto)

if __name__ == '__main__':
    dto = UrlDTO("dermatologue", "france", 1, 14, "Baratte")
    # asyncio.run(test(dto))
    p = DoctolibParser()
    p.load("home", dto)
    p.find_json()
    pss = p.find_h2_dr()
    for ps in pss:
        print(ps)
    # print(p.content)
    # Rechercher <script data-id="removable-json-ld"

