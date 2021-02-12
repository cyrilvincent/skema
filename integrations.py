import unittest
import adressesmatcher


class SkemaIntegrationTests(unittest.TestCase):
    matcher = adressesmatcher.AdresseMatcher()
    matcher.load_adresses()

    def test_integration(self):
        s = "VIENNE EN VUE ZI ESTRESSIN CHEMIN DES LONES 38200 VIENNE"
        cp, commune, num, street, rep = SkemaIntegrationTests.matcher.match_adresse_string(s)
        cp2, score = SkemaIntegrationTests.matcher.match_cp(cp, commune)
        self.assertEqual(cp, cp2)
        communes = SkemaIntegrationTests.matcher.cps_db[cp2]
        commune2, score = SkemaIntegrationTests.matcher.match_commune(commune, communes)
        self.assertEqual(commune, commune2)
        street2, score = SkemaIntegrationTests.matcher.match_street(commune2, street)
        self.assertEqual(street, street2)
        num2, score = SkemaIntegrationTests.matcher.match_num(commune2, street2, num)
        self.assertEqual(num, num2)

if __name__ == '__main__':
    unittest.main()
