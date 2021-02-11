import unittest
import numpy as np
import config
import loaders
import requests
import parsers
import urllib.parse


class SkemaTests(unittest.TestCase):

    def test_config(self):
        print(f"V{config.version}")
        print(f"NP: {np.__version__}")

    def test_maps(self):
        with requests.Session() as session:
            l = loaders.MapsLoader(session)
            l.load()
            self.assertTrue(l.response.ok)

    def test_maps_get(self):
        with requests.Session() as session:
            l = loaders.MapsLoader(session)
            s = "Cyril Vincent Conseil 970 avenue Leopold Fabre"
            q = urllib.parse.quote_plus(s)
            self.assertEqual("Cyril+Vincent+Conseil+970+avenue+Leopold+Fabre", q)
            l.get(q)
            self.assertTrue(l.response.ok)


if __name__ == '__main__':
    unittest.main()
