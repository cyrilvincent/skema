import unittest
import adressesmatcher
import config
import AdresseParser


class SkemaTests(unittest.TestCase):

    def test_config(self):
        print(f"V{config.version}")

    def test_adresse_matcher(self):
        m = adressesmatcher.AdresseMatcher()
        cp, commune, num, street, rep = m.match_adresse_string("1571 chemin des blancs 38250 Lans en Vercors")
        self.assertEqual(38250, cp)
        self.assertEqual(commune, "LANS EN VERCORS")
        self.assertEqual(1571, num)
        self.assertEqual("CHEMIN DES BLANCS", street)

    def test_adresse_matcher_robust(self):
        m = adressesmatcher.AdresseMatcher()
        cp, commune, num, street, rep = m.match_adresse_string("12345 chemin des blancs 38250 Lans en Vercors")
        self.assertEqual(38250, cp)
        self.assertEqual("CHEMIN DES BLANCS", street)
        cp, commune, num, street, rep = m.match_adresse_string("12 place du 14 juillet 38250 Lans en Vercors")
        self.assertEqual(12, num)
        cp, commune, num, street, rep = m.match_adresse_string("chemin des blancs 38250 Lans en Vercors")
        self.assertEqual("CHEMIN DES BLANCS", street)
        cp, commune, num, street, rep = m.match_adresse_string("2b chemin des blancs 38250 Lans en Vercors")
        self.assertEqual(2, num)
        self.assertEqual("B", rep)
        cp, commune, num, street, rep = m.match_adresse_string("2ter chemin des blancs 38250 Lans en Vercors")
        self.assertEqual(2, num)
        self.assertEqual("TER", rep)

    # Bad
    # def test_adresse_parser(self):
    #     p = AdresseParser.AdresseParser()
    #     res = p.parse("12345 chemin des blancs 38250 Lans en Vercors")
    #     print(res) #bad
    #     res = p.parse("12 place du 14 juillet 38250 Lans en Vercors")
    #     print(res) # manque 14
    #     res = p.parse("chemin des blancs 38250 Lans en Vercors")
    #     print(res) # OK
    #     res = p.parse("2b chemin des blancs 38250 Lans en Vercors")
    #     print(res)  # NOK
    #     # self.assertEqual(2, num)
    #     # self.assertEqual("B", rep)
    #     # cp, commune, num, street, rep = m.match_adresse_string("2ter chemin des blancs 38250 Lans en Vercors")
    #     # self.assertEqual(2, num)
    #     # self.assertEqual("TER", rep)


if __name__ == '__main__':
    unittest.main()
