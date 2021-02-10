import unittest
import numpy as np
import config
import loaders
import requests
import parsers
import urllib.parse
import selenium.webdriver


class SkemaTests(unittest.TestCase):

    browser = selenium.webdriver.Chrome()

    def test_config(self):
        print(f"V{config.version}")
        print(f"NP: {np.__version__}")

    def test_selenium(self):
        SkemaTests.browser.get("http://www.cyrilvincent.com")
        html = SkemaTests.browser.page_source
        self.assertIsNotNone(html)

    def test_maps(self):
        l = loaders.MapsLoader(SkemaTests.browser)
        l.load()
        # browser.add_cookie({'domain': '.google.com', 'expiry': 2146723198, 'httpOnly': False, 'name': 'CONSENT', 'path': '/', 'sameSite': 'None', 'secure': True, 'value': 'YES+FR.fr+V10+BX'})
        # browser.add_cookie({'domain': 'www.google.com', 'expiry': 1613003483, 'httpOnly': False, 'name': 'UULE', 'path': '/', 'secure': True, 'value': 'a+cm9sZTogMQpwcm9kdWNlcjogMTIKdGltZXN0YW1wOiAxNjEyOTgxODgyODA3MDAwCmxhdGxuZyB7CiAgbGF0aXR1ZGVfZTc6IDQ1MDk4NTA5NwogIGxvbmdpdHVkZV9lNzogNTU4MDU4ODIKfQpyYWRpdXM6IDIwMDAwCnByb3ZlbmFuY2U6IDYK'})
        # browser.add_cookie({'domain': '.google.com', 'expiry': 1628793080, 'httpOnly': True, 'name': 'NID', 'path': '/', 'sameSite': 'None', 'secure': True, 'value': '209=PKy9a4qj0N-6NoIM6EpYj5YXO3Ou5BqaR99At-pmiEI6Vxo2yzWiJxufnCfPUmpeXGEA_jPyrlSvgWVR2VAs38dubXqtXX6zVIH71ExZlxeacD5MUXkTfj9lnDfeOcaByatRW6obhzZ3TwU2d3T-6ZHM7fDPH7qD-RwvXJtpr6A'})
        self.assertTrue(l.response.ok)

    def test_maps_get(self):
        l = loaders.MapsLoader(SkemaTests.browser)
        s = "Cyril Vincent Conseil 970 avenue Leopold Fabre"
        q = urllib.parse.quote_plus(s)
        self.assertEqual("Cyril+Vincent+Conseil+970+avenue+Leopold+Fabre", q)
        l.get(q)
        self.assertTrue(l.response.ok)

    def test_parser(self):
        l = loaders.MapsLoader(SkemaTests.browser)
        s = "Pavaday Christelle, 51 Place Pierre Chabert, 38250 Villard-de-Lans"
        l.get(urllib.parse.quote_plus(s))
        p = parsers.MapsParser(l.html)
        p.soup_pane()
        self.assertIsNotNone(p.pane)
        self.assertEqual("PAVADAY CHRISTELLE", p.soup_name())



if __name__ == '__main__':
    unittest.main()
