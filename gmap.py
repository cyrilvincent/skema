import requests
import config
import abc
import selenium.webdriver
import time


class SeleniumLoader(metaclass=abc.ABCMeta):

    def __init__(self, browser):
        self.url: str = ""
        self.browser: selenium.webdriver.Chrome = browser
        self.ok = False

    @property
    def html(self):
        return self.browser.page_source

    def load(self, url=None):
        if url is None:
            url = self.url
        print(f"Load {url}")
        self.browser.get(url)
        time.sleep(config.sleep)
        self.ok = len(self.html) > 1000


class GoogleLoader(SeleniumLoader):

    def __init__(self, session: requests.Session):
        super().__init__(session)
        self.url = "http://www.google.fr"

    def cookies(self):
        self.browser.add_cookie({'domain': '.google.com', 'expiry': 2146723198, 'httpOnly': False, 'name': 'CONSENT', 'path': '/', 'sameSite': 'None', 'secure': True, 'value': 'YES+FR.fr+V10+BX'})
        self.browser.add_cookie({'domain': 'www.google.com', 'expiry': 1613003483, 'httpOnly': False, 'name': 'UULE', 'path': '/', 'secure': True, 'value': 'a+cm9sZTogMQpwcm9kdWNlcjogMTIKdGltZXN0YW1wOiAxNjEyOTgxODgyODA3MDAwCmxhdGxuZyB7CiAgbGF0aXR1ZGVfZTc6IDQ1MDk4NTA5NwogIGxvbmdpdHVkZV9lNzogNTU4MDU4ODIKfQpyYWRpdXM6IDIwMDAwCnByb3ZlbmFuY2U6IDYK'})
        self.browser.add_cookie({'domain': '.google.com', 'expiry': 1628793080, 'httpOnly': True, 'name': 'NID', 'path': '/', 'sameSite': 'None', 'secure': True, 'value': '209=PKy9a4qj0N-6NoIM6EpYj5YXO3Ou5BqaR99At-pmiEI6Vxo2yzWiJxufnCfPUmpeXGEA_jPyrlSvgWVR2VAs38dubXqtXX6zVIH71ExZlxeacD5MUXkTfj9lnDfeOcaByatRW6obhzZ3TwU2d3T-6ZHM7fDPH7qD-RwvXJtpr6A'})


class MapsLoader(SeleniumLoader):

    def __init__(self, session: requests.Session):
        super().__init__(session)
        self.url = "http://www.google.com/maps?hl=fr"

    def post(self, q):
        print(f"Post {q}")
        tag = self.browser.find_element_by_id("searchboxinput")
        tag.clear()
        tag.send_keys(q)
        btn = self.browser.find_element_by_id("searchbox-searchbutton")
        btn.click()
        time.sleep(config.sleep)
        self.ok = len(self.html) > 1000

    def get_url(self):
        return self.browser.current_url

    def get_lon_lat(self, url):
        index = url.index("@")
        s = url[index + 1:]
        index = s.index(",")
        lat = s[:index]
        s = s[index + 1:]
        index = s.index(",")
        lon = s[:index]
        return float(lon), float(lat)


if __name__ == '__main__':
    with selenium.webdriver.Chrome() as browser:
        l = GoogleLoader(browser)
        l.load()
        l.cookies()
        l = MapsLoader(browser)
        l.load()
        s = "1571 chemin des blancs 38250 Lans en Vercors"
        l.post(s)
        url = l.get_url()
        print(url)
        lon, lat = l.get_lon_lat(url)
        print(lon, lat) # 45.098384 5.5782497 vs 45.098642 5.580492
        s = "970 avenue leopold fabre 38250 Lans en Vercors"
        l.post(s)
        url = l.get_url()
        print(url)
        lon, lat = l.get_lon_lat(url)
        print(lon, lat)
        # p = parsers.MapsParser(l.html)
        # p.soup_pane()
        # print(p.soup_name())
        # print(p.soup_note())
        # print(p.soup_nbreview())
        # s = "stade de neige lans en vercors"
        # l.post(s)
        # p = parsers.MapsParser(l.html)
        # p.soup_pane()
        # print(p.soup_name())
        # print(p.soup_note())
        # print(p.soup_nbreview())