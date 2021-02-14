import unittest
import adressesmatcher


class SkemaIntegrationTests(unittest.TestCase):
    matcher = adressesmatcher.AdresseMatcher()
    matcher.load_adresses(59)

    def test_integration(self):
        s = "SONNEVILLE EMMANUEL ALLEE SAINT HUBERT 25/5 59910 BONDUES"
        cp, commune, num, street, rep = SkemaIntegrationTests.matcher.match_adresse_string(s)
        cp2, score = SkemaIntegrationTests.matcher.match_cp(cp, commune)
        communes = SkemaIntegrationTests.matcher.cps_db[cp2]
        commune2, score = SkemaIntegrationTests.matcher.match_commune(commune, communes, cp2)
        street2, score = SkemaIntegrationTests.matcher.match_street(commune2, street, cp2)
        num2, score = SkemaIntegrationTests.matcher.match_num(commune2, street2, num)


if __name__ == '__main__':
    unittest.main()
