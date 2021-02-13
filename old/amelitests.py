import unittest
import numpy as np
import config
from old import loaders
import requests
import parsers
import pickles2csv


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

    def test_pageentities(self):
        with requests.Session() as session:
            l = loaders.AmeliLoader(session)
            l.post("VINCENT")
            l = loaders.AmeliPageLoader(session)
            l.load()
            p = parsers.AmeliPageParser(l.html)
            p.soup_entities()
            self.assertEqual(20, len(p.entities))

    def test_pagesoup(self):
        with requests.Session() as session:
            l = loaders.AmeliLoader(session)
            l.post("VINCENT", "38")
            l = loaders.AmeliPageLoader(session)
            l.load()
            p = parsers.AmeliPageParser(l.html)
            p.soup_entities()
            e = p.entities["A7ozkjI3NjK2"]
            self.assertIsNotNone(e)
            self.assertEqual("Conventionné", e.convention)
            self.assertEqual("0625994386", e.phone)
            self.assertEqual("Masseur-kinésithérapeute", e.speciality)
            self.assertEqual("VINCENT", e.fname)
            self.assertTrue(e.vitale)
            self.assertEqual("KINE DU SPORT BERRIAT<br/>5 RUE PIERRE SEMARD<br/>38000 GRENOBLE", e.address)
            self.assertIsNone(e.honoraire)
            e = p.entities["A7o1kjoyNjaz"]
            self.assertEqual("Honoraires libres", e.honoraire)

    def test_honoraire(self):
        with requests.Session() as session:
            l = loaders.AmeliLoader(session)
            l.post("ACHARD ANTHEAUME", "21")
            l = loaders.AmeliPageLoader(session)
            l.load()
            p = parsers.AmeliPageParser(l.html)
            p.soup_entities()
            e = p.entities["ArMwkjI5Nje6"]
            self.assertEqual("Conventionné", e.honoraire)

    def test_dept(self):
        self.assertEqual("38", pickles2csv.get_dept_from_cp("38000"))
        self.assertEqual("971", pickles2csv.get_dept_from_cp("97100"))
        self.assertEqual("2A", pickles2csv.get_dept_from_cp("20100"))
        self.assertEqual("2B", pickles2csv.get_dept_from_cp("20200"))
        self.assertEqual("98", pickles2csv.get_dept_from_cp("98000"))


if __name__ == '__main__':
    unittest.main()
