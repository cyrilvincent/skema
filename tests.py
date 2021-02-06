import unittest
import numpy as np
import config
import loaders
import requests
import parsers


class SkemaTests(unittest.TestCase):

    def test_config(self):
        print(f"V{config.version}")
        print(f"NP: {np.__version__}")

    def test_google(self):
        with requests.Session() as session:
            l = loaders.GoogleLoader(session)
            l.load()
            self.assertTrue(l.response.ok)

    def test_ameli(self):
        with requests.Session() as session:
            l = loaders.AmeliLoader(session)
            l.load()
            self.assertTrue(l.response.ok)

    def test_post(self):
        with requests.Session() as session:
            l = loaders.AmeliLoader(session)
            res = l.post("VINCENT", "38")
            self.assertTrue(l.ok)
            self.assertTrue(res)

    def test_post_404(self):
        with requests.Session() as session:
            l = loaders.AmeliLoader(session)
            res = l.post("XYZ", "38")
            self.assertFalse(res)

    def test_amelipageloader(self):
        with requests.Session() as session:
            l = loaders.AmeliLoader(session)
            l.post("VINCENT", "38")
            l = loaders.AmeliPageLoader(session)
            l.load()
            self.assertTrue(l.response.ok)

    def test_amelipageparser(self):
        with requests.Session() as session:
            l = loaders.AmeliLoader(session)
            l.post("VINCENT", "38")
            l = loaders.AmeliPageLoader(session)
            l.load()
            p = parsers.AmeliPageParser(l.html)
            self.assertIsNotNone(p.soup)

    def test_nbpage(self):
        with requests.Session() as session:
            l = loaders.AmeliLoader(session)
            l.post("VI")
            l = loaders.AmeliPageLoader(session)
            l.load()
            p = parsers.AmeliPageParser(l.html)
            p.soup_nbpage()
            self.assertEqual(50, p.nbpage)

    def test_pageitems(self):
        with requests.Session() as session:
            l = loaders.AmeliLoader(session)
            l.post("VINCENT")
            l = loaders.AmeliPageLoader(session)
            l.load()
            p = parsers.AmeliPageParser(l.html)
            p.soup_items()
            self.assertEqual(20, len(p.items))

    def test_details(self):
        with requests.Session() as session:
            l = loaders.AmeliLoader(session)
            l.post("VINCENT", "38")
            l = loaders.AmeliPageLoader(session)
            l.load()
            p = parsers.AmeliPageParser(l.html)
            p.soup_items()
            id = list(p.items.keys())[0]
            l = loaders.AmeliDetailLoader(session, id)
            l.load()
            p = parsers.AmeliDetailsParser(l.html)
            p.soup_phone()
            self.assertEqual("0625994386", p.phone)
            p.soup_convention()
            self.assertEqual("Conventionné", p.convention)


if __name__ == '__main__':
    unittest.main()
