from unittest import TestCase

from sqlalchemy.orm import joinedload

from base_parser import EtabParser
from etalab_parser import EtalabParser
from ps_merge import PSMerger
from ps_parser import PSParser
from BAN_matcher import BANMatcher
from OSM_matcher import OSMMatcher
from ps_tarif_parser import PSTarifParser
from score_matcher import ScoreMatcher
from personne_activite_parser import PersonneActiviteParser
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

    def test_pseudo_clone(self):
        ep = EtabParser(None)
        e1 = Etablissement(id=1, rs="Cyril Vincent", telephone="0622538762")
        e2 = Etablissement(id=2)
        ep.pseudo_clone(e1, e2)
        self.assertEqual(2, e2.id)
        self.assertEqual("Cyril Vincent", e2.rs)
        self.assertEqual("0622538762", e2.telephone)
        e2.codeape = "xyz"
        e1.codeape = None
        self.assertIsNone(e1.codeape)
        ep.pseudo_clone(e1, e2)
        self.assertIsNone(e2.codeape)
        e1.codeape = "abc"
        ep.pseudo_clone(e1, e2)
        self.assertEqual("abc", e2.codeape)

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

    def test_get_dept_by_cp(self):
        pp = PSParser(None)
        d = pp.get_dept_from_cp(38250)
        self.assertEqual(38, d)
        d = pp.get_dept_from_cp(1000)
        self.assertEqual(1, d)
        d = pp.get_dept_from_cp(20100)
        self.assertEqual(201, d)

    def test_ban_matcher_make_cache(self):
        m = BANMatcher([])
        m.make_cache0()
        m.make_cache1(5)

    def test_ban_matcher_nearest_less_cp(self):
        m = BANMatcher([])
        m.make_cache0()
        m.make_cache1(38)
        cp = m.find_nearest_less_cp(38259)
        self.assertEqual(38250, cp)

    def test_ban_matcher_cp(self):
        m = BANMatcher([])
        m.make_cache0()
        m.make_cache1(38)
        cp, score = m.match_cp(38250)
        self.assertEqual(38250, cp)
        self.assertEqual(1, score)
        cp, score = m.match_cp(38058)
        self.assertEqual(38400, cp)
        self.assertEqual(0.95, score)
        cp, score = m.match_cp(38259)
        self.assertEqual(38250, cp)
        self.assertEqual(0.5, score)

    def test_gestlat(self):
        m = BANMatcher([])
        score = m.gestalt("LANS EN VERCORS", "LANS VERCROS")
        self.assertAlmostEqual(0.81, score, delta=0.01)
        score = m.gestalt("LANS EN VERCORS", "LANS")
        self.assertAlmostEqual(0.42, score, delta=0.01)

    def test_gestlats(self):
        m = BANMatcher([])
        res, _ = m.gestalts("LANS", ["LANS EN VERCORS", "VILLARD DE LANS"])
        self.assertEqual("LANS EN VERCORS", res)
        res, _ = m.gestalts("LANS VERCROS", ["LANS EN VERCORS", "VILLARD DE LANS"])
        self.assertEqual("LANS EN VERCORS", res)
        res, score = m.gestalts("SAINT LARENT", ["SAINT LAURENT DU PONT"])
        self.assertEqual("SAINT LAURENT DU PONT", res)

    def test_get_cp_by_commune(self):
        m = BANMatcher([38])
        m.make_cache1(38)
        cp, _, _ = m.get_cp_by_commune("LANS EN VERCORS")
        self.assertEqual(38250, cp)

    def test_match_rue(self):
        m = BANMatcher([38])
        m.make_cache1(38)
        rue, score = m.match_rue("LANS EN VERCORS", "CHEMIN DES BLANCS", None, 38250)
        self.assertEqual("CHEMIN DES BLANCS", rue)
        self.assertEqual(1, score)
        rue, _ = m.match_rue("LANS EN VERCORS", "CH DES BLANCS", None, 38250)
        self.assertEqual("CHEMIN DES BLANCS", rue)
        rue, _ = m.match_rue("LANS EN VERCORS", "BLANC", "CHEMIN DES BLANCS", 38250)
        self.assertEqual("CHEMIN DES BLANCS", rue)
        rue, _ = m.match_rue("LANS EN VERCORS", "BLANC", "CH DES BLANCS", 38250)
        self.assertEqual("CHEMIN DES BLANCS", rue)

    def test_match_num(self):
        m = BANMatcher([38])
        m.make_cache1(38)
        ban, score = m.match_numero(38250, "LANS EN VERCORS", "CHEMIN DES BLANCS", 1571)
        self.assertEqual(1571, ban.numero)
        ban, score = m.match_numero(38250, "LANS EN VERCORS", "CHEMIN DES BLANCS", 1573)
        self.assertEqual(1571, ban.numero)
        ban, score = m.match_numero(38250, "LANS EN VERCORS", "CHEMIN DES BLANCS", None)
        self.assertEqual(17, ban.numero)
        ban, score = m.match_numero(38250, "LANS EN VERCORS", "CHEMIN DES BLANCS", 5000)
        self.assertEqual(1600, ban.numero)

    def test_get_json_from_url(self):
        om = OSMMatcher(ban_echo=True)
        url = "https://nominatim.openstreetmap.org/search.php?format=jsonv2&country=France&city=lans+en+vercors"
        json = om.get_json_from_url(url)
        self.assertAlmostEqual(45, float(json[0]["lat"]), delta=1)
        print(json)

    def test_get_lon_lat_from_adresse(self):
        om = OSMMatcher(ban_echo=True)
        osm = om.get_osm_from_adresse(1571, "chemin des blancs", "lans en vercors", 38250)
        self.assertAlmostEqual(45, osm.lat, delta=1)
        self.assertEqual(38250, osm.cp)
        osm = om.get_osm_from_adresse(None, None, "lans en vercors", 38250)
        self.assertAlmostEqual(45, osm.lat, delta=1)
        osm = om.get_osm_from_adresse(None, None, None, 38250)
        self.assertAlmostEqual(45, osm.lat, delta=1)
        osm = om.get_osm_from_adresse(None, None, "lans en vercors", None)
        self.assertAlmostEqual(45, osm.lat, delta=1)
        osm = om.get_osm_from_adresse(None, None, "xxx", None)
        self.assertIsNone(osm)
        osm = om.get_osm_from_adresse(None, "chemin des blancs", None, 38250)
        self.assertAlmostEqual(45, osm.lat, delta=1)
        osm = om.get_osm_from_adresse(None, "xxx", None, 38250)
        self.assertIsNone(osm)
        osm = om.get_osm_from_adresse(None, None, "paris", None)
        self.assertIsNone(osm.cp)
        osm = om.get_osm_from_adresse(None, "maison de sante", "lans en vercors", 38250)
        print(osm)

    def test_osm_purge(self):
        om = OSMMatcher(ban_echo=True)
        om.purge()

    def test_calc_distance(self):
        om = OSMMatcher(ban_echo=True)
        osm1 = om.get_osm_from_adresse(1571, "chemin des blancs", "lans en vercors", 38250)
        osm2 = om.get_osm_from_adresse(970, "avenue leopold fabre", "lans en vercors", 75008)
        sm = ScoreMatcher(ban_echo=True)
        d = sm.calc_distance(osm1.lon, osm1.lat, osm2.lon, osm2.lat)
        self.assertEqual(3314, d)

    def test_tarif_by_year(self):
        context = Context()
        context.create(echo=True)
        l: List[Tarif] = context.session.query(Tarif).options(joinedload(Tarif.date_sources))\
            .filter(Tarif.date_sources.any(DateSource.annee >= 2020))
        print(l)

    def test_tarif_mapper(self):
        context = Context()
        context.create(echo=True)
        p = PSParser(context)
        p.date_source = DateSource(21, 12)
        p.load_cache()
        s = "H;JITTEN;PHILIPPE;CABINET MEDICAL ET OSTEOPATHIE;;5 ESPA CHARLES DE GAULLE;LA GRENETTE;01100;OYONNAX;0474776681;45;1;3;c1;N;O;G__;1;10;20;30;;;;;;;;;;;;"
        row = s.split(";")
        t = p.tarif_mapper(row)
        self.assertEqual(45, t.profession.id)
        self.assertEqual(1, t.mode_exercice.id)
        self.assertEqual(3, t.nature.id)
        self.assertEqual("C1", t.convention.code)
        self.assertFalse(t.option_contrat)
        self.assertTrue(t.vitale)
        self.assertEqual("G__", t.code)
        self.assertEqual(1, t.famille_acte.id)
        self.assertEqual(10, t.montant)
        self.assertEqual(20, t.borne_inf)
        self.assertEqual(30, t.borne_sup)

    def test_personne_activite_mapper(self):
        context = Context()
        context.create(echo=True)
        p = PersonneActiviteParser(context)
        s = "Type d'identifiant PP|Identifiant PP|Identification nationale PP|Code civilité d'exercice|Libellé civilité d'exercice|Code civilité|Libellé civilité|Nom d'exercice|Prénom d'exercice|Code profession|Libellé profession|Code catégorie professionnelle|Libellé catégorie professionnelle|Code type savoir-faire|Libellé type savoir-faire|Code savoir-faire|Libellé savoir-faire|Code mode exercice|Libellé mode exercice|Numéro SIRET site|Numéro SIREN site|Numéro FINESS site|Numéro FINESS établissement juridique|Identifiant technique de la structure|Raison sociale site|Enseigne commerciale site|Complément destinataire (coord. structure)|Complément point géographique (coord. structure)|Numéro Voie (coord. structure)|Indice répétition voie (coord. structure)|Code type de voie (coord. structure)|Libellé type de voie (coord. structure)|Libellé Voie (coord. structure)|Mention distribution (coord. structure)|Bureau cedex (coord. structure)|Code postal (coord. structure)|Code commune (coord. structure)|Libellé commune (coord. structure)|Code pays (coord. structure)|Libellé pays (coord. structure)|Téléphone (coord. structure)|Téléphone 2 (coord. structure)|Télécopie (coord. structure)|Adresse e-mail (coord. structure)|Code Département (structure)|Libellé Département (structure)|Ancien identifiant de la structure|Autorité d'enregistrement|Code secteur d'activité|Libellé secteur d'activité|Code section tableau pharmaciens|Libellé section tableau pharmaciens|"
        headers = s.split("|")
        s = "0|012600631|0012600631|||M|Monsieur|PETITGUYOT|ALEXANDRE|26|Audioprothésiste|C|Civil|||||S|Salarié|49940088500020||||C49940088500020|DOUBS OPTIC||DOUBS OPTIC||9||RTE|Route|DE BESANCON||25300 DOUBS|25300|||||||||||349940088500020|ARS/Variable/Variable|SA42|Appareillage médical|||"
        row = s.split("|")
        dico = {}
        for h, r in zip(headers, row):
            dico[h] = r
        pa = p.mapper(dico)
        self.assertEqual("0012600631", pa.inpp)
        self.assertEqual("PETITGUYOT", pa.nom)
        self.assertEqual("ALEXANDRE", pa.prenom)

    def test_datesource_back(self):
        p = PSTarifParser(None)
        p.date_source = DateSource(21, 12)
        res = p.datesource_back()
        self.assertEqual(2110, res)
        p.date_source = DateSource(22, 1)
        res = p.datesource_back()
        self.assertEqual(2111, res)
        p.date_source = DateSource(19, 0)
        res = p.datesource_back()
        self.assertEqual(0, res)

    def test_pa_adresse_mapper(self):
        context = Context()
        context.create(echo=True)
        p = PersonneActiviteParser(context)
        p.load_cache()
        s = "Type d'identifiant PP|Identifiant PP|Identification nationale PP|Code civilité d'exercice|Libellé civilité d'exercice|Code civilité|Libellé civilité|Nom d'exercice|Prénom d'exercice|Code profession|Libellé profession|Code catégorie professionnelle|Libellé catégorie professionnelle|Code type savoir-faire|Libellé type savoir-faire|Code savoir-faire|Libellé savoir-faire|Code mode exercice|Libellé mode exercice|Numéro SIRET site|Numéro SIREN site|Numéro FINESS site|Numéro FINESS établissement juridique|Identifiant technique de la structure|Raison sociale site|Enseigne commerciale site|Complément destinataire (coord. structure)|Complément point géographique (coord. structure)|Numéro Voie (coord. structure)|Indice répétition voie (coord. structure)|Code type de voie (coord. structure)|Libellé type de voie (coord. structure)|Libellé Voie (coord. structure)|Mention distribution (coord. structure)|Bureau cedex (coord. structure)|Code postal (coord. structure)|Code commune (coord. structure)|Libellé commune (coord. structure)|Code pays (coord. structure)|Libellé pays (coord. structure)|Téléphone (coord. structure)|Téléphone 2 (coord. structure)|Télécopie (coord. structure)|Adresse e-mail (coord. structure)|Code Département (structure)|Libellé Département (structure)|Ancien identifiant de la structure|Autorité d'enregistrement|Code secteur d'activité|Libellé secteur d'activité|Code section tableau pharmaciens|Libellé section tableau pharmaciens|"
        headers = s.split("|")
        s = "0|012600631|0012600631|||M|Monsieur|PETITGUYOT|ALEXANDRE|26|Audioprothésiste|C|Civil|||||S|Salarié|49940088500020||||C49940088500020|DOUBS OPTIC||DOUBS OPTIC||9||RTE|Route|DE BESANCON||25300 DOUBS|25300|||||||||||349940088500020|ARS/Variable/Variable|SA42|Appareillage médical|||"
        row = s.split("|")
        dico = {}
        for h, r in zip(headers, row):
            dico[h] = r
        a = p.pa_adresse_mapper(dico)
        self.assertEqual(9, a.numero)
        self.assertEqual("ROUTE DE BESANCON", a.rue)
        self.assertEqual(25300, a.cp)
        self.assertEqual("DOUBS", a.commune)
        self.assertEqual(25, a.dept.id)
        dico["Libellé commune (coord. structure)"] = "lans"
        a = p.pa_adresse_mapper(dico)
        self.assertEqual("LANS", a.commune)
        dico["Libellé commune (coord. structure)"] = ""
        dico["Bureau cedex (coord. structure)"] = ""
        a = p.pa_adresse_mapper(dico)
        self.assertIsNone(a)
        dico = {"Type d'identifiant PP": '0', 'Identifiant PP': '759124159', 'Identification nationale PP': '0759124159', "Code civilité d'exercice": '', "Libellé civilité d'exercice": '', 'Code civilité': 'MME', 'Libellé civilité': 'Madame', "Nom d'exercice": 'DE RUIJTER', "Prénom d'exercice": 'ISABELLE', 'Code profession': '91', 'Libellé profession': 'Orthophoniste', 'Code catégorie professionnelle': 'C', 'Libellé catégorie professionnelle': 'Civil', 'Code type savoir-faire': '', 'Libellé type savoir-faire': '', 'Code savoir-faire': '', 'Libellé savoir-faire': '', 'Code mode exercice': 'L', 'Libellé mode exercice': 'Libéral', 'Numéro SIRET site': '', 'Numéro SIREN site': '', 'Numéro FINESS site': '', 'Numéro FINESS établissement juridique': '', 'Identifiant technique de la structure': 'C75912415900', 'Raison sociale site': 'CABINET MME DE RUIJTER', 'Enseigne commerciale site': '', 'Complément destinataire (coord. structure)': 'CABINET MME DE RUIJTER', 'Complément point géographique (coord. structure)': '', 'Numéro Voie (coord. structure)': 'P', 'Indice répétition voie (coord. structure)': '', 'Code type de voie (coord. structure)': 'PL', 'Libellé type de voie (coord. structure)': 'Place', 'Libellé Voie (coord. structure)': 'VIOLET', 'Mention distribution (coord. structure)': 'CDS ANSELME PAYEN EPHPAD', 'Bureau cedex (coord. structure)': '75015 PARIS', 'Code postal (coord. structure)': '75015', 'Code commune (coord. structure)': '', 'Libellé commune (coord. structure)': '', 'Code pays (coord. structure)': '', 'Libellé pays (coord. structure)': '', 'Téléphone (coord. structure)': '0148237096', 'Téléphone 2 (coord. structure)': '', 'Télécopie (coord. structure)': '', 'Adresse e-mail (coord. structure)': '', 'Code Département (structure)': '', 'Libellé Département (structure)': '', 'Ancien identifiant de la structure': '075912415900', "Autorité d'enregistrement": 'ARS/CPAM/CPAM', "Code secteur d'activité": 'SA07', "Libellé secteur d'activité": 'Cabinet individuel', 'Code section tableau pharmaciens': '', 'Libellé section tableau pharmaciens': '', '': ''}
        a = p.pa_adresse_mapper(dico)
        dico = {"Type d'identifiant PP": '8', 'Identifiant PP': '10001045367', 'Identification nationale PP': '810001045367', "Code civilité d'exercice": 'DR', "Libellé civilité d'exercice": 'Docteur', 'Code civilité': 'M', 'Libellé civilité': 'Monsieur', "Nom d'exercice": 'GUIGNARD', "Prénom d'exercice": 'ERIC', 'Code profession': '10', 'Libellé profession': 'Médecin', 'Code catégorie professionnelle': 'C', 'Libellé catégorie professionnelle': 'Civil', 'Code type savoir-faire': 'S', 'Libellé type savoir-faire': 'Spécialité ordinale', 'Code savoir-faire': 'SM49', 'Libellé savoir-faire': 'Santé publique et médecine sociale', 'Code mode exercice': 'S', 'Libellé mode exercice': 'Salarié', 'Numéro SIRET site': '85131528300016', 'Numéro SIREN site': '', 'Numéro FINESS site': '', 'Numéro FINESS établissement juridique': '', 'Identifiant technique de la structure': 'R10100000328372', 'Raison sociale site': 'AIMMUNE THERAPEUTICS UK LIMITED', 'Enseigne commerciale site': 'AIMMUNE THERAPEUTICS', 'Complément destinataire (coord. structure)': 'AIMMUNE THERAPEUTICS UK LIMITED', 'Complément point géographique (coord. structure)': '', 'Numéro Voie (coord. structure)': '', 'Indice répétition voie (coord. structure)': '', 'Code type de voie (coord. structure)': '', 'Libellé type de voie (coord. structure)': '', 'Libellé Voie (coord. structure)': 'CARRICK HOUSE LYPIATT ROAD', 'Mention distribution (coord. structure)': '', 'Bureau cedex (coord. structure)': 'GL 5O 2QJ CHELTENHAM', 'Code postal (coord. structure)': 'GL', 'Code commune (coord. structure)': '', 'Libellé commune (coord. structure)': '', 'Code pays (coord. structure)': '99132', 'Libellé pays (coord. structure)': 'Royaume-uni', 'Téléphone (coord. structure)': '', 'Téléphone 2 (coord. structure)': '', 'Télécopie (coord. structure)': '', 'Adresse e-mail (coord. structure)': '', 'Code Département (structure)': '', 'Libellé Département (structure)': '', 'Ancien identifiant de la structure': '385131528300016', "Autorité d'enregistrement": 'CNOM/CNOM/CNOM', "Code secteur d'activité": 'SA32', "Libellé secteur d'activité": 'Fab. Exploit. Import. Méd. DM', 'Code section tableau pharmaciens': '', 'Libellé section tableau pharmaciens': '', '': ''}
        a = p.pa_adresse_mapper(dico)

    def test_cache_inpp(self):
        context = Context()
        context.create(echo=True)
        p = PSParser(context)
        p.load_cache_inpp()
        max = 0
        max_key = None
        for k in p.inpps:
            l = len(set(p.inpps[k].values()))
            if l > max:
                max = l
                max_key = k
        print(len(p.inpps))
        self.assertEqual(8, max)
        self.assertEqual(('LEFEBVRE', 'SOPHIE', 62), max_key)
        self.assertEqual({(141, 'RUE DE QUIERY', 62490, 'VITRY EN ARTOIS'): '810104335319', (1601, 'BOULEVARD DES JUSTES', 62107, 'CALAIS'): '0629400748', (55, 'RUE DE ROSEMONT', 62130, 'SAINT POL SUR TERNOISE'): '810005814339', (28, 'PLACE DU GENERAL LECLERC', 62130, 'SAINT POL SUR TERNOISE'): '810100224947', (None, 'RUE DE BLENDECQUES', 62570, 'HELFAUT'): '810104257190', (39, 'RUE LESAGE', 62940, 'HAILLICOURT'): '810100124576', (1, 'RUE PRINCIPALE', 62120, 'CAMPAGNE LÈS WARDRECQUES'): '810005810808', (55, 'IMPASSE DU STADE', 62145, 'ESTRÉE BLANCHE'): '810005814339', (30, 'AVENUE DU PRESIDENT WILSON', 62100, 'CALAIS'): '810100356202', (2, 'RUE DES BRUYERES', 62120, 'RACQUINGHEM'): '810005810808'}, p.inpps[max_key])
        print(p.inpps[('MARTIN', 'ISABELLE', 75)])
        # ('MARTIN', 'ISABELLE') 36 dans la france

    def test_convert_key_to_adresse_string(self):
        p = PSParser(None)
        key = (1571, "CHEMIN DES BLANCS", 38250, "LANS")
        s = p.convert_key_to_rue_string(key)
        self.assertEqual(s, "1571 CHEMIN DES BLANCS 38250 LANS")
        key = (None, "CHEMIN DES BLANCS", 38250, "LANS")
        s = p.convert_key_to_rue_string(key)
        self.assertEqual(s, "CHEMIN DES BLANCS 38250 LANS")
        key = (None, None, 38250, "LANS")
        s = p.convert_key_to_rue_string(key)
        self.assertEqual(s, "38250 LANS")

    def test_convert_lambert92_gps(self):
        p = EtabParser(None)
        x1, y1 = 882408.3, 6543019.6
        lon, lat = p.convert_lambert93_lon_lat(x1, y1)
        self.assertAlmostEqual(5.355651287573366, lon, delta=1e-5)
        self.assertAlmostEqual(45.96240165432614, lat, delta=1e-5)
        x1, y1 = 870215.7, 6571590.5
        lon, lat = p.convert_lambert93_lon_lat(x1, y1)
        print(lon, lat)

    def test_etalab_mapper(self):
        context = Context()
        context.create(echo=True)
        p = EtalabParser(context)
        h = "nofinesset;nofinessej;rs;rslongue;complrs;compldistrib;numvoie;typvoie;voie;compvoie;lieuditbp;region;libregion;departement;libdepartement;cog;codepostal;libelle_routage;ligneacheminement;telephone;telecopie;categetab;libcategetab;liblongcategetab;categretab;libcategretab;siret;codeape;libcodeape;mft;libmft;liblongmft;sph;libsph;numen;coordx;coordy;sourcegeocod;dategeocod;dateautor;dateouvert;datemaj"
        headers = h.split(";")
        s = "010000024;010780054;CH DE FLEYRIAT;CENTRE HOSPITALIER DE BOURG-EN-BRESSE FLEYRIAT;;;900;RTE;DE PARIS;;;84;AUVERGNE-RHONE-ALPES;01;AIN;01451;01440;VIRIAT;01440 VIRIAT;04 74 45 46 47;04 74 45 41 14;355;C.H.;Centre Hospitalier (C.H.);1102;Centres Hospitaliers;26010004500012;8610Z;Activit�s hospitali�res;03;ARS / DG EPS;ARS �tablissements Publics de sant� dotation globale;1;Etab.public de sant�;;870215.7;6571590.5;1,ATLASANTE,100,IGN,BD_ADRESSE,V2.2,LAMBERT_93;2021-01-04;1979-02-13;1979-02-13;2020-02-04"
        row = s.split(";")
        dico = {}
        for h, r in zip(headers, row):
            dico[h] = r
        t = p.mapper(dico)
        self.assertEqual("010000024", t.nofinesset)
        self.assertEqual("010780054", t.nofinessej)
        self.assertEqual("CH DE FLEYRIAT", t.rs)
        self.assertEqual("CENTRE HOSPITALIER DE BOURG-EN-BRESSE FLEYRIAT", t.rslongue)
        self.assertEqual("03", t.mft)
        self.assertEqual(1, t.sph)
        self.assertEqual(355, t.categetab)
        self.assertEqual(1102, t.categretab)
        self.assertEqual("04 74 45 46 47", t.telephone)
        self.assertEqual("04 74 45 41 14", t.telecopie)
        self.assertEqual("26010004500012", t.siret)
        self.assertEqual("8610Z", t.codeape)

    def test_ps_merger(self):
        context = Context()
        context.create(echo=True)
        psm = PSMerger(context)
        ps1 = psm.context.session.query(PS).options(joinedload(PS.ps_cabinet_date_sources)) \
            .options(joinedload(PS.tarifs)).filter(PS.key == "BENYOUB_DA_SILVA_KARIMA_01000").first()
        nb_cabinet1 = len(ps1.ps_cabinet_date_sources)
        nb_tarif1 = len(ps1.tarifs)
        ps2 = psm.context.session.query(PS).options(joinedload(PS.ps_cabinet_date_sources)) \
            .options(joinedload(PS.tarifs)).filter(PS.key == "810100779536").first()
        nb_cabinet2 = len(ps2.ps_cabinet_date_sources)
        nb_tarif2 = len(ps2.tarifs)
        psm.merge_ps(ps1, ps2)
        self.assertEqual(0, len(ps1.ps_cabinet_date_sources))
        self.assertEqual(0, len(ps1.tarifs))
        self.assertEqual(nb_cabinet1 + nb_cabinet2, len(ps2.ps_cabinet_date_sources))
        self.assertEqual(nb_tarif1 + nb_tarif2, len(ps2.tarifs))
        psm.context.session.commit()





