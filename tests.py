from unittest import TestCase
from icipv2_etab import EtabParser
from sqlentities import *


class ICIPTests(TestCase):

    def test_orm(self):
        context = Context()
        context.create(echo=True)

    def test_parse_date(self):
        ep = EtabParser(None)
        path = "toto_21-10.csv"
        ep.parse_date(path)
        self.assertEqual(2110, ep.date_source.id)

    def test_check_data(self):
        context = Context()
        context.create(echo=True)
        ep = EtabParser(context)
        path = "toto_00-00.csv"
        ep.check_date(path)

    def test_etab_cache(self):
        context = Context()
        context.create(echo=True)
        ep = EtabParser(context)
        ep.load_cache()

    def test_etab_mapper(self):
        context = Context()
        context.create(echo=True)
        ep = EtabParser(context)
        s = "123456789;Cyril Vincent;;010003978;18;Privé non lucratif;;FALSE;FALSE;FALSE;FALSE;TRUE;FALSE;FALSE;TRUE;FALSE;TRUE;FALSE;TRUE;FALSE;FALSE;FALSE;FALSE;FALSE;FALSE;;;;;;;;1570 chemin des blancs;38250;38;ISERE;LANS EN VERCORS;0622538762;contact@cyrilvincent.com;Cyril Vincent Conseil;www.cyrilvincent.com;45.930657;4.814821;;;;;;;;;;;;;;;;;;;;;;;;;;;"
        row = s.split(";")
        ep.load_cache()
        e = ep.mapper(row)
        self.assertEqual(123456789, e.id)
        self.assertEqual("Cyril Vincent", e.nom)
        self.assertEqual("Privé non lucratif", e.type.type)
        self.assertEqual("0622538762", e.telephone)
        self.assertEqual("contact@cyrilvincent.com", e.mail)
        self.assertEqual("Cyril Vincent Conseil", e.nom2)
        self.assertEqual("www.cyrilvincent.com", e.url)

    def test_pseudo_equal(self):
        ep = EtabParser(None)
        e1 = Etablissement(id=1, nom="Cyril Vincent", telephone="0622538762")
        e2 = Etablissement(nom="Cyril Vincent", telephone="0622538762")
        self.assertTrue(ep.pseudo_equal(e1, e2))

    def test_pseudo_clone(self):
        ep = EtabParser(None)
        e1 = Etablissement(id=1, nom="Cyril Vincent", telephone="0622538762")
        e2 = Etablissement(id=2)
        ep.pseudo_clone(e1, e2)
        self.assertEqual(2, e2.id)
        self.assertEqual("Cyril Vincent", e2.nom)
        self.assertEqual("0622538762", e2.telephone)

    def test_adresseraw_mapper(self):
        context = Context()
        context.create(echo=True)
        ep = EtabParser(context)
        s = "123456789;Cyril Vincent;;010003978;18;Privé non lucratif;;FALSE;FALSE;FALSE;FALSE;TRUE;FALSE;FALSE;TRUE;FALSE;TRUE;FALSE;TRUE;FALSE;FALSE;FALSE;FALSE;FALSE;FALSE;;;;;;;;1571 chemin des blancs;38250;38;ISERE;LANS EN VERCORS;0622538762;contact@cyrilvincent.com;Cyril Vincent Conseil;www.cyrilvincent.com;45.930657;4.814821;;;;;;;;;;;;;;;;;;;;;;;;;;;"
        row = s.split(";")
        ep.load_cache()
        a = ep.adresse_raw_mapper(row)
        self.assertEqual("1571 chemin des blancs", a.adresse3)
        self.assertEqual("38250", a.cp)
        self.assertEqual("LANS EN VERCORS", a.commune)

    def test_create_update_adresse(self):
        context = Context()
        context.create(echo=True)
        ep = EtabParser(context)
        s = "123456789;Cyril Vincent;;010003978;18;Privé non lucratif;;FALSE;FALSE;FALSE;FALSE;TRUE;FALSE;FALSE;TRUE;FALSE;TRUE;FALSE;TRUE;FALSE;FALSE;FALSE;FALSE;FALSE;FALSE;;;;;;;;1571 chemin des blancs;38250;38;ISERE;LANS EN VERCORS;0622538762;contact@cyrilvincent.com;Cyril Vincent Conseil;www.cyrilvincent.com;45.930657;4.814821;;;;;;;;;;;;;;;;;;;;;;;;;;;"
        row = s.split(";")
        ep.load_cache()
        e = ep.mapper(row)
        a = ep.adresse_raw_mapper(row)
        ep.create_update_adresse(e, a)
        self.assertIsNone(e.adresse_raw.id)
        self.assertEqual("1571 chemin des blancs", e.adresse_raw.adresse3)
        s = "123456789;Cyril Vincent;;010003978;18;Privé non lucratif;;FALSE;FALSE;FALSE;FALSE;TRUE;FALSE;FALSE;TRUE;FALSE;TRUE;FALSE;TRUE;FALSE;FALSE;FALSE;FALSE;FALSE;FALSE;;;;;;;;Rue du Collège;01600;01;AIN;REYRIEUX;0622538762;contact@cyrilvincent.com;Cyril Vincent Conseil;www.cyrilvincent.com;45.930657;4.814821;;;;;;;;;;;;;;;;;;;;;;;;;;;"
        row = s.split(";")
        a = ep.adresse_raw_mapper(row)
        ep.create_update_adresse(e, a)
        self.assertIsNotNone(e.adresse_raw.id)
        self.assertEqual("REYRIEUX", e.adresse_raw.commune)

    def test_parse_row_new_etab_new_adresse(self):
        context = Context()
        context.create(echo=True)
        ep = EtabParser(context)
        path = "toto_00-01.csv"
        ep.check_date(path)
        # New etab new adresse
        s = "123456789;Cyril Vincent;;123456789;18;Privé non lucratif;;FALSE;FALSE;FALSE;FALSE;TRUE;FALSE;FALSE;TRUE;FALSE;TRUE;FALSE;TRUE;FALSE;FALSE;FALSE;FALSE;FALSE;FALSE;;;;;;;;1571 chemin des blancs;38250;38;ISERE;LANS EN VERCORS;0622538762;contact@cyrilvincent.com;Cyril Vincent Conseil;www.cyrilvincent.com;45.930657;4.814821;;;;;;;;;;;;;;;;;;;;;;;;;;;"
        row = s.split(";")
        ep.load_cache()
        ep.parse_row(row)
        self.assertEqual(1, ep.nb_new_entity)
        self.assertEqual(1, ep.nb_new_adresse)

    def test_parse_row_new_etab_known_adresse(self):
        context = Context()
        context.create(echo=True)
        ep = EtabParser(context)
        path = "toto_00-01.csv"
        ep.check_date(path)
        s = "123456788;Cyril Vincent 2;;123456788;18;Privé non lucratif;;FALSE;FALSE;FALSE;FALSE;TRUE;FALSE;FALSE;TRUE;FALSE;TRUE;FALSE;TRUE;FALSE;FALSE;FALSE;FALSE;FALSE;FALSE;;;;;;;;1571 chemin des blancs;38250;38;ISERE;LANS EN VERCORS;0622538762;contact@cyrilvincent.com;Cyril Vincent Conseil;www.cyrilvincent.com;45.930657;4.814821;;;;;;;;;;;;;;;;;;;;;;;;;;;"
        row = s.split(";")
        ep.load_cache()
        ep.parse_row(row)
        self.assertEqual(1, ep.nb_new_entity)
        self.assertEqual(0, ep.nb_new_adresse)

    def test_etab_load(self):
        context = Context()
        context.create(echo=True)
        ep = EtabParser(context)
        path = "data/etab_00-00.csv"
        ep.load(path)

    def test_parse_row_known_etab_known_adresse(self):
        context = Context()
        context.create(echo=True)
        ep = EtabParser(context)
        path = "toto_00-01.csv"
        ep.check_date(path)
        s = "123456789;Cyril Vincent;;123456789;18;Privé non lucratif;;FALSE;FALSE;FALSE;FALSE;TRUE;FALSE;FALSE;TRUE;FALSE;TRUE;FALSE;TRUE;FALSE;FALSE;FALSE;FALSE;FALSE;FALSE;;;;;;;;1571 chemin des blancs;38250;38;ISERE;LANS EN VERCORS;0622538762;contact@cyrilvincent.com;Cyril Vincent Conseil;www.cyrilvincent.com;45.930657;4.814821;;;;;;;;;;;;;;;;;;;;;;;;;;;"
        row = s.split(";")
        ep.load_cache()
        ep.parse_row(row)
        self.assertEqual(0, ep.nb_new_entity)
        self.assertEqual(0, ep.nb_new_adresse)

    def test_parse_row_known_etab_new_adresse(self):
        context = Context()
        context.create(echo=True)
        ep = EtabParser(context)
        path = "toto_00-01.csv"
        ep.check_date(path)
        s = "123456789;Cyril Vincent;;123456789;18;Privé non lucratif;;FALSE;FALSE;FALSE;FALSE;TRUE;FALSE;FALSE;TRUE;FALSE;TRUE;FALSE;TRUE;FALSE;FALSE;FALSE;FALSE;FALSE;FALSE;;;;;;;;1572 chemin des blancs;38250;38;ISERE;LANS EN VERCORS;0622538762;contact@cyrilvincent.com;Cyril Vincent Conseil;www.cyrilvincent.com;45.930657;4.814821;;;;;;;;;;;;;;;;;;;;;;;;;;;"
        row = s.split(";")
        ep.load_cache()
        ep.parse_row(row)
        self.assertEqual(0, ep.nb_new_entity)
        self.assertEqual(1, ep.nb_new_adresse)

    def test_parse_row_known_etab_other_adresse(self):
        context = Context()
        context.create(echo=True)
        ep = EtabParser(context)
        path = "toto_00-01.csv"
        ep.check_date(path)
        s = "123456789;Cyril Vincent;;123456789;18;Privé non lucratif;;FALSE;FALSE;FALSE;FALSE;TRUE;FALSE;FALSE;TRUE;FALSE;TRUE;FALSE;TRUE;FALSE;FALSE;FALSE;FALSE;FALSE;FALSE;;;;;;;;1571 chemin des blancs;38250;38;ISERE;LANS EN VERCORS;0622538762;contact@cyrilvincent.com;Cyril Vincent Conseil;www.cyrilvincent.com;45.930657;4.814821;;;;;;;;;;;;;;;;;;;;;;;;;;;"
        row = s.split(";")
        ep.load_cache()
        ep.parse_row(row)
        self.assertEqual(0, ep.nb_new_entity)
        self.assertEqual(0, ep.nb_new_adresse)

    def test_parse_row_update_etab(self):
        context = Context()
        context.create(echo=True)
        ep = EtabParser(context)
        path = "toto_00-01.csv"
        ep.check_date(path)
        s = "123456789;Cyril Vincent;;123456789;18;Privé non lucratif;;FALSE;FALSE;FALSE;FALSE;TRUE;FALSE;FALSE;TRUE;FALSE;TRUE;FALSE;TRUE;FALSE;FALSE;FALSE;FALSE;FALSE;FALSE;;;;;;;;1571 chemin des blancs;38250;38;ISERE;LANS EN VERCORS;0622538762;contact@cyrilvincent.com;Cyril Vincent Conseil;www.cyrilvincent.com;45.930657;4.814821;;;;;;;;;;;;;;;;;;;;;;;;;;;"
        row = s.split(";")
        ep.load_cache()
        ep.parse_row(row)
        self.assertEqual(0, ep.nb_new_entity)
        self.assertEqual(0, ep.nb_new_adresse)
        self.assertEqual(1, ep.nb_update_entity)

    def test_parse_multi_date(self):
        context = Context()
        context.create(echo=True)
        ep = EtabParser(context)
        path = "toto_00-02.csv"
        ep.check_date(path)
        s = "123456789;Cyril Vincent;;123456789;18;Privé non lucratif;;FALSE;FALSE;FALSE;FALSE;TRUE;FALSE;FALSE;TRUE;FALSE;TRUE;FALSE;TRUE;FALSE;FALSE;FALSE;FALSE;FALSE;FALSE;;;;;;;;1571 chemin des blancs;38250;38;ISERE;LANS EN VERCORS;0622538762;contact@cyrilvincent.com;Cyril Vincent Conseil;www.cyrilvincent.com;45.930657;4.814821;;;;;;;;;;;;;;;;;;;;;;;;;;;"
        row = s.split(";")
        ep.load_cache()
        ep.parse_row(row)

    def test_split_num(self):
        ep = EtabParser(None)
        num, s = ep.split_num("1571 ch des blancs")
        self.assertEqual(1571, num)
        self.assertEqual("ch des blancs", s)

    def test_replace_all(self):
        ep = EtabParser(None)
        s = ep.replace_all("CYRIL VINCENT", {"CY": "MA", "RIL": "TIS"})
        self.assertEqual("MATIS VINCENT", s)

    def test_normalize_street(self):
        ep = EtabParser(None)
        s = ep.normalize_street("ch. des-blancs")
        self.assertEqual("CHEMIN DES BLANCS", s)

    def test_normalize_commune(self):
        ep = EtabParser(None)
        s = ep.normalize_street("st. donat")
        self.assertEqual("SAINT DONAT", s)

    def test_normalize(self):
        ep = EtabParser(None)
        a = AdresseRaw()
        a.adresse3 = "1571 ch. des blancs"
        a.cp = "38250"
        a.commune = "Lans en Vercors"
        n = ep.normalize(a)
        self.assertEqual(1571, n.numero)
        self.assertEqual("CHEMIN DES BLANCS", n.rue1)
        self.assertEqual("38250", n.cp)
        self.assertEqual("LANS EN VERCORS", n.commune)

    def test_create_update_norm(self):
        context = Context()
        context.create(echo=True)
        ep = EtabParser(context)
        s = "123456789;Cyril Vincent;;010003978;18;Privé non lucratif;;FALSE;FALSE;FALSE;FALSE;TRUE;FALSE;FALSE;TRUE;FALSE;TRUE;FALSE;TRUE;FALSE;FALSE;FALSE;FALSE;FALSE;FALSE;;;;;;;;1571 chemin des blancs;38250;38;ISERE;LANS EN VERCORS;0622538762;contact@cyrilvincent.com;Cyril Vincent Conseil;www.cyrilvincent.com;45.930657;4.814821;;;;;;;;;;;;;;;;;;;;;;;;;;;"
        row = s.split(";")
        ep.load_cache()
        e = ep.mapper(row)
        a = ep.adresse_raw_mapper(row)
        ep.create_update_adresse(e, a)
        ep.create_update_norm(a)
        self.assertEqual(1571, a.adresse_norm.numero)
        self.assertEqual(ep.nb_new_norm, 1)
        ep.create_update_norm(a)
        self.assertEqual(ep.nb_new_norm, 1)
        a.adresse3 = a.adresse3.replace("1571", "970")
        ep.create_update_norm(a)
        self.assertEqual(ep.nb_new_norm, 2)

    def test_parse_row_new_norm(self):
        context = Context()
        context.create(echo=True)
        ep = EtabParser(context)
        path = "toto_00-01.csv"
        ep.check_date(path)
        s = "123456789;Cyril Vincent;;123456789;18;Privé non lucratif;;FALSE;FALSE;FALSE;FALSE;TRUE;FALSE;FALSE;TRUE;FALSE;TRUE;FALSE;TRUE;FALSE;FALSE;FALSE;FALSE;FALSE;FALSE;;;;;;;;1571 chemin des blancs;38250;38;ISERE;LANS EN VERCORS;0622538762;contact@cyrilvincent.com;Cyril Vincent Conseil;www.cyrilvincent.com;45.930657;4.814821;;;;;;;;;;;;;;;;;;;;;;;;;;;"
        row = s.split(";")
        ep.load_cache()
        ep.parse_row(row)
        self.assertEqual(1, ep.nb_new_norm)

    def test_parse_row_known_norm(self):
        context = Context()
        context.create(echo=True)
        ep = EtabParser(context)
        path = "toto_00-01.csv"
        ep.check_date(path)
        s = "123456789;Cyril Vincent;;123456789;18;Privé non lucratif;;FALSE;FALSE;FALSE;FALSE;TRUE;FALSE;FALSE;TRUE;FALSE;TRUE;FALSE;TRUE;FALSE;FALSE;FALSE;FALSE;FALSE;FALSE;;;;;;;;1571 chemin des blancs;38250;38;ISERE;LANS EN VERCORS;0622538762;contact@cyrilvincent.com;Cyril Vincent Conseil;www.cyrilvincent.com;45.930657;4.814821;;;;;;;;;;;;;;;;;;;;;;;;;;;"
        row = s.split(";")
        ep.load_cache()
        ep.parse_row(row)
        self.assertEqual(0, ep.nb_new_norm)