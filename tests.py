import datetime
import re
from unittest import TestCase
from sqlalchemy.orm import joinedload

import base_parser
import rpps_etat_civil_parser
from etalab_parser import EtalabParser
from ps_change_key import PSChangeKey
from ps_parser import PSParser
from ps_parser_v2 import PSParserV2
from BAN_matcher import BANMatcher
from OSM_matcher import OSMMatcher
from iris_matcher import IrisMatcher
from ps_tarif_parser import PSTarifParser
from score_matcher import ScoreMatcher
from personne_activite_parser import PersonneActiviteParser
from pa_correspondance_parser import PACorrespondanceParser
from rpps_personne_parser import RPPSPersonneParser
from rpps_structure_parser import RPPSStructureParser
from rpps_exercice_pro_parser import RPPSExerciceProParser
from rpps_activite_parser import RPPSActiviteParser
from rpps_diplome_obtenu_parser import RPPSDiplomeObtenuParser
from rpps_etat_civil_parser import RPPSEtatCivilParser
from rpps_reference_ae_parser import RPPSReferenceAEParser
from rpps_savoir_faire_parser import RPPSSavoirFaireParser
from rpps_coord_corresp_parser import RPPSCoordPersonneParser
from rpps_coord_activite_parser import RPPSCoordActiviteParser
from rpps_coord_structure_parser import RPPSCoordStructureParser
from rpps_coord_structure_geoloc_parser import RPPSCoordStructureGeolocParser
from sqlentities import *


class ICIPTests(TestCase):

    def test_orm(self):
        context = Context()
        context.create(echo=True)

    def test_parse_date(self):
        ep = EtalabParser(None)
        path = "toto_21-10.csv"
        ep.parse_date(path)
        self.assertEqual(2110, ep.date_source.id)

    def test_check_data(self):
        context = Context()
        context.create(echo=True)
        ep = EtalabParser(context)
        path = "toto_00-00.csv"
        ep.check_date(path)

    def test_pseudo_clone(self):
        ep = EtalabParser(None)
        e1 = Etablissement(id=1, rs="Cyril Vincent", telephone="0622538762")
        e2 = Etablissement(id=2)
        ep.pseudo_clone(e1, e2)
        self.assertEqual(2, e2.id)
        self.assertEqual("Cyril Vincent", e2.rs)
        self.assertEqual("0622538762", e2.telephone)
        self.assertIsNone(e2.codeape)
        e1.codeape = "abc"
        ep.pseudo_clone(e1, e2)
        self.assertEqual("abc", e2.codeape)

    def test_adresseraw_mapper(self):
        context = Context()
        context.create(echo=True)
        ep = EtalabParser(context)
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
        ep = EtalabParser(context)
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
        ep = EtalabParser(context)
        path = "toto_00-01.csv"
        ep.check_date(path)
        # New etab new adresse
        s = "123456789;Cyril Vincent;;123456789;18;Privé non lucratif;;FALSE;FALSE;FALSE;FALSE;TRUE;FALSE;FALSE;TRUE;FALSE;TRUE;FALSE;TRUE;FALSE;FALSE;FALSE;FALSE;FALSE;FALSE;;;;;;;;1571 chemin des blancs;38250;38;ISERE;LANS EN VERCORS;0622538762;contact@cyrilvincent.com;Cyril Vincent Conseil;www.cyrilvincent.com;45.930657;4.814821;;;;;;;;;;;;;;;;;;;;;;;;;;;"
        row = s.split(";")
        ep.load_cache()
        ep.parse_row(row)
        self.assertEqual(1, ep.nb_new_entity)
        self.assertEqual(1, ep.nb_new_adresse)

    def test_split_num(self):
        ep = EtalabParser(None)
        num, s = ep.split_num("1571 ch des blancs")
        self.assertEqual(1571, num)
        self.assertEqual("ch des blancs", s)

    def test_replace_all(self):
        ep = EtalabParser(None)
        s = ep.replace_all("CYRIL VINCENT", {"CY": "MA", "RIL": "TIS"})
        self.assertEqual("MATIS VINCENT", s)

    def test_normalize_street(self):
        ep = EtalabParser(None)
        s = ep.normalize_street("ch. des-blancs")
        self.assertEqual("CHEMIN DES BLANCS", s)

    def test_normalize_commune(self):
        ep = EtalabParser(None)
        s = ep.normalize_street("st. donat")
        self.assertEqual("SAINT DONAT", s)

    def test_normalize(self):
        ep = EtalabParser(None)
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
        ep = EtalabParser(context)
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
        ep = EtalabParser(context)
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
        ep = EtalabParser(context)
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
            .filter(Tarif.date_sources.any(DateSource.annee >= 20))
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
        for k in p.inpps_dept:
            l = len(set(p.inpps_dept[k].values()))
            if l > max:
                max = l
                max_key = k
        print(len(p.inpps_dept))
        self.assertEqual(8, max)
        self.assertEqual(('LEFEBVRE', 'SOPHIE', 62), max_key)
        self.assertEqual({(141, 'RUE DE QUIERY', 62490, 'VITRY EN ARTOIS'): '810104335319', (1601, 'BOULEVARD DES JUSTES', 62107, 'CALAIS'): '0629400748', (55, 'RUE DE ROSEMONT', 62130, 'SAINT POL SUR TERNOISE'): '810005814339', (28, 'PLACE DU GENERAL LECLERC', 62130, 'SAINT POL SUR TERNOISE'): '810100224947', (None, 'RUE DE BLENDECQUES', 62570, 'HELFAUT'): '810104257190', (39, 'RUE LESAGE', 62940, 'HAILLICOURT'): '810100124576', (1, 'RUE PRINCIPALE', 62120, 'CAMPAGNE LÈS WARDRECQUES'): '810005810808', (55, 'IMPASSE DU STADE', 62145, 'ESTRÉE BLANCHE'): '810005814339', (30, 'AVENUE DU PRESIDENT WILSON', 62100, 'CALAIS'): '810100356202', (2, 'RUE DES BRUYERES', 62120, 'RACQUINGHEM'): '810005810808'}, p.inpps_dept[max_key])
        print(p.inpps_dept[('MARTIN', 'ISABELLE', 75)])
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
        p = EtalabParser(None)
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
        # h = "nofinesset;nofinessej;rs;rslongue;complrs;compldistrib;numvoie;typvoie;voie;compvoie;lieuditbp;region;departement;libdepartement;ligneacheminement;telephone;telecopie;categetab;libcategetab;categretab;libcategretab;siret;codeape;mft;libmft;sph;libsph;dateouvert;dateautor;datemaj;nofinesset;coordx;coordy;sourcegeocod;dategeocod"
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

    def test_ps_change_key(self):
        context = Context()
        context.create(echo=True)
        psm = PSChangeKey(context)
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

    def test_code_profession_mapper(self):
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
        c = p.code_profession_mapper(dico)
        self.assertEqual(26, c.id)
        self.assertEqual("Audioprothésiste", c.libelle)

    def test_code_profession_mapper(self):
        context = Context()
        context.create(echo=True)
        p = PersonneActiviteParser(context)
        p.load_cache()
        s = "Type d'identifiant PP|Identifiant PP|Identification nationale PP|Code civilité d'exercice|Libellé civilité d'exercice|Code civilité|Libellé civilité|Nom d'exercice|Prénom d'exercice|Code profession|Libellé profession|Code catégorie professionnelle|Libellé catégorie professionnelle|Code type savoir-faire|Libellé type savoir-faire|Code savoir-faire|Libellé savoir-faire|Code mode exercice|Libellé mode exercice|Numéro SIRET site|Numéro SIREN site|Numéro FINESS site|Numéro FINESS établissement juridique|Identifiant technique de la structure|Raison sociale site|Enseigne commerciale site|Complément destinataire (coord. structure)|Complément point géographique (coord. structure)|Numéro Voie (coord. structure)|Indice répétition voie (coord. structure)|Code type de voie (coord. structure)|Libellé type de voie (coord. structure)|Libellé Voie (coord. structure)|Mention distribution (coord. structure)|Bureau cedex (coord. structure)|Code postal (coord. structure)|Code commune (coord. structure)|Libellé commune (coord. structure)|Code pays (coord. structure)|Libellé pays (coord. structure)|Téléphone (coord. structure)|Téléphone 2 (coord. structure)|Télécopie (coord. structure)|Adresse e-mail (coord. structure)|Code Département (structure)|Libellé Département (structure)|Ancien identifiant de la structure|Autorité d'enregistrement|Code secteur d'activité|Libellé secteur d'activité|Code section tableau pharmaciens|Libellé section tableau pharmaciens|"
        headers = s.split("|")
        s = "8|10106476764|810106476764|DR|Docteur|M|Monsieur|BENHOUCHAME|Zakaria|10|Médecin|C|Civil|S|Spécialité ordinale|SM20|Gynécologie-obstétrique|S|Salarié|||||||||||||||||||||||||||||CNOM//|||||"
        row = s.split("|")
        dico = {}
        for h, r in zip(headers, row):
            dico[h] = r
        d = p.savoir_faire_mapper(dico)
        self.assertEqual("SM20", d.code_diplome)

    def test_pa_correspondance_mapper(self):
        context = Context()
        context.create(echo=True)
        p = PACorrespondanceParser(context)
        p.load_cache()
        s = "\ufeffprofession,mode d’exercice particulier,codeprofession,Code savoir-faire,code profession,libelléprofession"
        headers = s.split(",")
        s = "35,,Gynécologie médicale et obstétrique (CEX),CEX22,10,Médecin"
        row = s.split(",")
        dico = {}
        for h, r in zip(headers, row):
            dico[h] = r
        id, code, cp = p.mapper(dico)
        self.assertEqual(35, id)
        self.assertEqual("CEX22", code)
        self.assertEqual(10, cp)

    def test_match_specialite(self):
        context = Context()
        context.create(echo=True)
        p = PSParser(context)
        p.date_source = DateSource(21, 12)
        s = "F;BRIARD;EMILIE;;;PLACE DE LA FENIERE;;13640;LA ROQUE D ANTHERON;;60;;3;c1;N;O;BLQP0100;114;0;0;0;0;0;0;0;0;0;0;0;0;0;0;0"
        row = s.split(";")
        ps = p.mapper(row)
        l = p.context.session.query(Profession).all()
        for prof in l:
            p.professions[prof.id] = prof
        profession = p.profession_mapper(row)
        self.assertEqual(60, profession.id)
        profession = p.professions[profession.id]
        pa = p.context.session.query(PersonneActivite).first()
        res = p.match_profession_code_profession_pa(profession, pa)
        self.assertFalse(res)
        cp = p.context.session.query(CodeProfession).filter(CodeProfession.id == 10).first()
        pa.code_professions.append(cp)
        res = p.match_profession_code_profession_pa(profession, pa)
        self.assertTrue(res)
        res = p.match_specialite_pa(profession, pa)
        self.assertTrue(res)
        res = p.match_profession_savoir_faire_pa(profession, pa)
        self.assertTrue(res)
        d = p.context.session.query(Diplome).filter(Diplome.code_diplome == "SM40").first()
        pa.diplomes.append(d)
        res = p.match_profession_savoir_faire_pa(profession, pa)
        self.assertTrue(res)
        res = p.match_specialite_pa(profession, pa)
        self.assertTrue(res)
        d2 = p.context.session.query(Diplome).filter(Diplome.code_diplome == "SM01").first()
        pa.diplomes.append(d2)
        res = p.match_profession_savoir_faire_pa(profession, pa)
        self.assertTrue(res)
        res = p.match_specialite_pa(profession, pa)
        self.assertTrue(res)
        profession = p.professions[2]
        res = p.match_profession_savoir_faire_pa(profession, pa)
        self.assertTrue(res)
        profession = p.professions[3]
        res = p.match_profession_savoir_faire_pa(profession, pa)
        self.assertFalse(res)
        res = p.match_specialite_pa(profession, pa)
        self.assertFalse(res)

    def test_match_specialite_v2(self):
        context = Context()
        context.create(echo=True)
        parser = PSParserV2(context)
        parser.date_source = DateSource(21, 12)
        s = "F;BRIARD;EMILIE;;;PLACE DE LA FENIERE;;13640;LA ROQUE D ANTHERON;;60;;3;c1;N;O;BLQP0100;114;0;0;0;0;0;0;0;0;0;0;0;0;0;0;0"
        row = s.split(";")
        ps = parser.mapper(row)
        l = parser.context.session.query(Profession).all()
        for prof in l:
            parser.professions[prof.id] = prof
        profession = parser.profession_mapper(row)
        self.assertEqual(60, profession.id)
        profession = parser.professions[profession.id]
        p = parser.context.session.query(Personne).filter((Personne.nom == "JOLY") & (Personne.prenom == "ODILON")).first()
        res = parser.match_profession_code_profession_pa(profession, p)
        self.assertFalse(res)
        a = parser.context.session.query(Activite).filter(Activite.code_profession_id == 10).first()
        p.activites.append(a)
        res = parser.match_profession_code_profession_pa(profession, p)
        self.assertTrue(res)
        res = parser.match_profession_savoir_faire_pa(profession, p)
        self.assertFalse(res)
        res = parser.match_specialite_pa(profession, p)
        self.assertFalse(res)
        do = parser.context.session.query(DiplomeObtenu).join(Diplome).filter(Diplome.code_diplome == "SM40").first()
        p.diplome_obtenus.append(do)
        res = parser.match_profession_savoir_faire_pa(profession, p)
        self.assertTrue(res)
        res = parser.match_specialite_pa(profession, p)
        self.assertTrue(res)
        d2 = parser.context.session.query(Diplome).filter(Diplome.code_diplome == "SM01").first()
        p.diplomes.append(d2)
        res = parser.match_profession_savoir_faire_pa(profession, p)
        self.assertTrue(res)
        res = parser.match_specialite_pa(profession, p)
        self.assertTrue(res)
        profession = parser.professions[2]
        res = parser.match_profession_savoir_faire_pa(profession, p)
        self.assertTrue(res)
        profession = parser.professions[3]
        res = parser.match_profession_savoir_faire_pa(profession, p)
        self.assertFalse(res)
        res = parser.match_specialite_pa(profession, p)
        self.assertFalse(res)


    def test_create_ps_with_split_names(self):
        p = PSParser(None)
        ps = PS
        ps.nom = "VINCENT"
        ps.prenom = "CYRIL"
        res = p.create_ps_with_split_names(ps)
        self.assertIsNone(res)
        ps.nom = "VINCENT BELRHALI"
        res = p.create_ps_with_split_names(ps)
        self.assertEqual("VINCENT", res.nom)
        self.assertEqual("CYRIL", res.prenom)
        ps.prenom = "CYRIL MATIS"
        res = p.create_ps_with_split_names(ps)
        self.assertEqual("VINCENT", res.nom)
        self.assertEqual("CYRIL", res.prenom)
        ps.nom = "VINCENT"
        res = p.create_ps_with_split_names(ps)
        self.assertEqual("VINCENT", res.nom)

    def test_iris(self):
        time0 = datetime.datetime.now()
        m = IrisMatcher(None, True)
        iris = m.get_iris_from_lon_lat(5.5783773, 45.0984914)
        self.assertEqual("382050000", iris)
        iris = m.get_iris_from_lon_lat(2.2769951, 48.8588336)
        self.assertEqual("751166216", iris)
        iris = m.get_iris_from_lon_lat(2.2769951, 0)
        self.assertIsNone(iris)
        iris = m.get_iris_from_address(1571, "CHEMIN DES BLANCS", 38250, "LANS EN VERCORS")
        self.assertEqual("382050000", iris)
        iris = m.get_iris_from_concatenate_address("1571 CHEMIN DES BLANCS 38250 LANS EN VERCORS")
        self.assertEqual("382050000", iris)
        print(datetime.datetime.now() - time0)

    def test_get_date(self):
        p = RPPSPersonneParser(None)
        d = p.get_date("15/11/1972")
        self.assertEqual(datetime.date(1972, 11, 15), d)

    def test_remove_double_quotes(self):
        p = RPPSPersonneParser(None)
        res = p.strip_quotes('""')
        self.assertEqual("", res)
        res = p.strip_quotes('"A"')
        self.assertEqual("A", res)

    def test_personne_mapper(self):
        p = RPPSPersonneParser(None)
        keys = """"Type d'identifiant PP";"Identifiant PP";"Identification nationale PP";"Code civilité";"Libellé civilité";"Nom d'usage";"Prénom d'usage";"Nature";"Code nationalité";"Libellé nationalité";"Date d'acquisition de la nationalité française";"Date d'effet";"Date de mise à jour e";"""
        values = """"8";"10100669562";"810100669562";"M";"Monsieur";"PREVOST";"Nicolas";"";"";"";"";"29/10/2014";"30/10/2014";"""
        keys = keys.replace('"', "").split(";")
        values = values.replace('"', "").split(";")
        row = {}
        for key, value in zip(keys, values):
            row[key] = value
        e = p.mapper(row)
        self.assertEqual("810100669562", e.inpp)
        self.assertEqual("M", e.civilite)
        self.assertEqual("PREVOST", e.nom)
        self.assertEqual("NICOLAS", e.prenom)
        self.assertIsNone(e.nature)
        self.assertIsNone(e.code_nationalite)
        self.assertIsNone(e.date_acquisition_nationalite)
        self.assertEqual(datetime.date(2014,10,29), e.date_effet)
        self.assertEqual(datetime.date(2014, 10, 30), e.date_maj)
        
    def test_structure_mapper(self):
        p = RPPSStructureParser(None)
        keys = """"Type de structure";"Identifiant technique de la structure";"Identification nationale de la structure";"Numéro SIRET";"Numéro SIREN";"Numéro FINESS Etablissement";"Numéro FINESS EJ";"RPPS rang";"ADELI rang";"Numéro licence officine";"Date d'ouverture structure";"Date de fermeture structure";"Date de mise à jour structure";"Code APE";"Libellé APE";"Code catégorie juridique";"Libellé catégorie juridique";"Code secteur d'activité";"Libellé secteur d'activité";"Raison sociale";"Enseigne commerciale";"""
        values = """"EG";"R10000000586941";"410000464692001";"";"";"";"";"10000464692001";"";"";"17/01/1994";"";"30/12/2015";"";"";"70";"Personne Physique";"SA07";"Cabinet individuel";"CABINET DU DR DOMINIQUE SAVELLI";"CABINET DU DR DOMINIQUE SAVELLI";"""
        keys = keys.replace('"', "").split(";")
        values = values.replace('"', "").split(";")
        row = {}
        for key, value in zip(keys, values):
            row[key] = value
        e = p.mapper(row)
        self.assertEqual("EG", e.type)
        self.assertEqual("R10000000586941", e.id_technique)
        self.assertEqual("410000464692001", e.id_national)
        self.assertEqual("10000464692001", e.rpps)
        self.assertIsNone(e.siret)
        self.assertEqual(datetime.date(1994,1,17), e.date_ouverture)
        self.assertEqual(datetime.date(2015, 12, 30), e.date_maj)
        self.assertEqual("70", e.categorie_juridique_id)
        self.assertEqual("SA07", e.code_secteur_activite)
        self.assertEqual("CABINET DU DR DOMINIQUE SAVELLI", e.enseigne)
        self.assertEqual("CABINET DU DR DOMINIQUE SAVELLI", e.raison_sociale)

    def test_exercice_pro_mapper(self):
        p = RPPSExerciceProParser(None)
        keys = """"Type d'identifiant PP";"Identifiant PP";"Identification nationale PP";"Code civilité d'exercice";"Libellé civilité d'exercice";"Nom d'exercice";"Prénom d'exercice";"Code profession";"Libellé profession";"Code catégorie professionnelle";"Libellé catégorie professionnelle";"Date de fin exercice";"Date de mise à jour exercice";"Date effet exercice";"Code AE 1e inscription";"Libellé AE 1e inscription";"Date début 1e inscription";"Département 1e inscription";"Libellé département 1e inscription";"""
        values = """"8";"10100669273";"810100669273";"DR";"Docteur";"MONTOUT";"Anne-Lise";"10";"Médecin";"C";"Civil";"";"13/07/2022";"27/10/2014";"CNOM";"Ordre des Médecins";"27/10/2014";"75";"Paris";"""
        keys = keys.replace('"', "").split(";")
        values = values.replace('"', "").split(";")
        row = {}
        for key, value in zip(keys, values):
            row[key] = value
        e = p.mapper(row)
        self.assertEqual("810100669273", e.inpp)
        self.assertEqual("DR", e.civilite)
        self.assertEqual("MONTOUT", e.nom)
        self.assertEqual("Anne-Lise", e.prenom)
        self.assertEqual("C", e.code_categorie_pro)
        self.assertEqual(datetime.date(2022,7,13), e.date_maj)
        self.assertEqual(datetime.date(2014, 10, 27), e.date_effet)
        self.assertEqual("CNOM", e.ae)
        self.assertEqual(datetime.date(2014, 10, 27), e.date_debut_inscription)
        self.assertEqual("75", e.departement_inscription)

    def test_activite_mapper(self):
        p = RPPSActiviteParser(None)
        keys = """"Type d'identifiant PP";"Identifiant PP";"Identifiant de l'activité";"Identification nationale PP";"Identifiant technique de la structure";"Code fonction";"Libellé fonction";"Code mode exercice";"Libellé mode exercice";"Date de début activité";"Date de fin activité";"Date de mise à jour activité";"Code région exercice";"Libellé région exercice";"Code genre activité";"Libellé genre activité";"Code motif de fin d'activité";"Libellé motif de fin d'activité";"Code section tableau pharmaciens";"Libellé section tableau pharmaciens";"Code sous-section tableau pharmaciens";"Libellé sous-section tableau pharmaciens";"Code type activité libérale";"Libellé type activité libérale";"Code statut des PS du SSA";"Libellé statut des PS du SSA";"Code statut hospitalier";"Libellé statut hospitalier";"Code profession";"Libellé profession";"Code catégorie professionnelle";"Libellé catégorie professionnelle";"""
        values = """"8";"10100669182";"1012552948";"810100669182";"R10100000515498";"FON-01";"Titulaire de cabinet";"L";"Lib,indép,artis,com";"01/09/2021";"";"30/09/2021";"";"";"GENR01";"Activité standard de soin ou de pharmacien";"";"";"";"";"";"";"ACT-LIB-06";"Cabinet";"";"";"";"";"10";"Médecin";"C";"Civil";"""
        keys = keys.replace('"', "").split(";")
        values = values.replace('"', "").split(";")
        row = {}
        for key, value in zip(keys, values):
            row[key] = value
        e = p.mapper(row)
        self.assertEqual("810100669182", e.inpp)
        self.assertEqual("R10100000515498", e.id_technique_structure)
        self.assertEqual("FON-01", e.fonction)
        self.assertEqual("L", e.mode_exercice)
        self.assertEqual("C", e.categorie_pro)
        self.assertEqual(datetime.date(2021,9,1), e.date_debut)
        self.assertEqual(datetime.date(2021, 9, 30), e.date_maj)
        self.assertIsNone(e.date_fin)
        self.assertEqual("GENR01", e.genre)
        self.assertEqual("ACT-LIB-06", e.type_activite_liberale)
        self.assertEqual(10, e.code_profession_id)
        self.assertEqual("C", e.categorie_pro)

    def test_diplome_obtenu_mapper(self):
        p = RPPSDiplomeObtenuParser(None)
        keys = """"Type d'identifiant PP";"Identifiant PP";"Identification nationale PP";"Code type diplôme obtenu";"Libellé type diplôme obtenu";"Code diplôme obtenu";"Libellé diplôme obtenu";"Date de mise à jour diplôme obtenu";"Code lieu obtention";"Libellé lieu obtention";"Date d'obtention diplôme";"Numéro diplôme";"""
        values = """"8";"10100670032";"810100670032";"DES";"Diplôme d'Etudes Spécialisées";"DSM41";"DES Psychiatrie";"30/10/2014";"U51";"Université de Reims (Université de Champagne-Arden";"06/10/2014";"";"""
        keys = keys.replace('"', "").split(";")
        values = values.replace('"', "").split(";")
        row = {}
        for key, value in zip(keys, values):
            row[key] = value
        e = p.mapper(row)
        self.assertEqual("810100670032", e.inpp)
        self.assertEqual("DES", e.type_diplome)
        self.assertEqual("DSM41", e.code_diplome)
        self.assertEqual(datetime.date(2014,10,30), e.date_maj)
        self.assertEqual(datetime.date(2014, 10, 6), e.date_obtention)
        self.assertEqual("U51", e.lieu_obtention)

    def test_etat_civil_mapper(self):
        p = RPPSEtatCivilParser(None)
        keys = """"Type d'identifiant PP";"Identifiant PP";"Identification nationale PP";"Code statut état-civil";"Libellé statut état-civil";"Code sexe";"Libellé sexe";"Nom de famille";"Prénoms";"Date de naissance";"Lieu de naissance";"Date de décès";"Date d'effet de l'état-civil";"Code commune de naissance";"Libellé commune de naissance";"Code pays de naissance";"Libellé pays de naissance";"Date de mise à jour état-civil";"""
        values = """"8";"10004973441";"810004973441";"NCI";"Non certifié INSEE, Immatriculation en cours";"M";"Masculin";"YANG-CROSSON";"SONG'TO'";"25/08/1962";"VIENTIANE";"";"21/10/2014";"38250";"LANS";"99241";"Laos";"28/10/2014";"""
        keys = keys.replace('"', "").split(";")
        values = values.replace('"', "").split(";")
        row = {}
        for key, value in zip(keys, values):
            row[key] = value
        e = p.mapper(row)
        self.assertEqual("810004973441", e.inpp)
        self.assertEqual("NCI", e.statut)
        self.assertEqual("M", e.sexe)
        self.assertEqual("YANG-CROSSON", e.nom)
        self.assertEqual("YANG CROSSON", e.nom_norm)
        self.assertEqual("SONG'TO'", e.prenoms)
        self.assertEqual("SONG", e.prenom_norm)
        self.assertEqual(datetime.date(1962,8,25), e.date_naissance)
        self.assertEqual("VIENTIANE", e.lieu_naissance)
        self.assertEqual(datetime.date(2014, 10, 21), e.date_effet)
        self.assertEqual("38250", e.code_commune)
        self.assertEqual("LANS", e.commune)
        self.assertEqual("99241", e.code_pays)
        self.assertEqual("LAOS", e.pays)
        self.assertEqual(datetime.date(2014, 10, 28), e.date_maj)

    def test_reference_ae_mapper(self):
        p = RPPSReferenceAEParser(None)
        keys = """"Type d'identifiant PP";"Identifiant PP";"Identification nationale PP";"Code AE";"Libellé AE";"Date début inscription";"Date fin inscription";"Date de mise à jour inscription";"Code statut inscription";"Libellé statut inscription";"Code département inscription";"Libellé département inscription";"Code département accueil";"Libellé département accueil";"Code profession";"Libellé profession";"Code catégorie professionnelle";"Libellé catégorie professionnelle";"""
        values = """"8";"10000037662";"810000037662";"CNOSF";"Ordre des Sages Femmes";"22/01/1988";"";"30/04/2009";"D";"Définitif";"34";"Hérault";"";"";"50";"Sage-Femme";"C";"Civil";"""
        keys = keys.replace('"', "").split(";")
        values = values.replace('"', "").split(";")
        row = {}
        for key, value in zip(keys, values):
            row[key] = value
        e = p.mapper(row)
        self.assertEqual("810000037662", e.inpp)
        self.assertEqual("CNOSF", e.ae)
        self.assertEqual(datetime.date(1988, 1, 22), e.date_debut)
        self.assertEqual(datetime.date(2009, 4, 30), e.date_maj)
        self.assertEqual("D", e.statut)
        self.assertEqual("34", e.departement)
        self.assertEqual(50, e.code_profession)
        self.assertEqual("C", e.categorie_pro)

    def test_savoir_faire_obtenu_mapper(self):
        p = RPPSSavoirFaireParser(None)
        keys = """"Type d'identifiant PP";"Identifiant PP";"Identification nationale PP";"Code savoir-faire";"Libellé savoir-faire";"Code type savoir-faire";"Libellé type savoir-faire";"Code profession";"Libellé profession";"Code catégorie professionnelle";"Libellé catégorie professionnelle";"Date reconnaissance savoir-faire";"Date de mise à jour savoir-faire";"Date abandon savoir-faire";"""
        values = """"8";"10100669372";"810100669372";"SM53";"Spécialiste en Médecine Générale";"S";"Spécialité ordinale";"10";"Médecin";"C";"Civil";"28/10/2014";"29/10/2014";"";"""
        keys = keys.replace('"', "").split(";")
        values = values.replace('"', "").split(";")
        row = {}
        for key, value in zip(keys, values):
            row[key] = value
        e = p.mapper(row)
        self.assertEqual("810100669372", e.inpp)
        self.assertEqual("SM53", e.code_sf)
        self.assertEqual("S", e.type_sf)
        self.assertEqual(10, e.code_profession)
        self.assertEqual("C", e.categorie_pro)
        self.assertEqual("C", e.categorie_pro)
        self.assertEqual(datetime.date(2014, 10, 28), e.date_reconnaissance)
        self.assertEqual(datetime.date(2014, 10, 29), e.date_maj)

    def test_coord_corresp_mapper(self):
        p = RPPSCoordPersonneParser(None)
        keys = """"Type d'identifiant PP";"Identifiant PP";"Identification nationale PP";"Complément destinataire (coord. correspondance)";"Complément point géographique (coord. correspondance)";"Numéro Voie (coord. correspondance)";"Indice répétition voie (coord. correspondance)";"Code type de voie (coord. correspondance)";"Libellé type de voie (coord. correspondance)";"Libellé Voie (coord. correspondance)";"Mention distribution (coord. correspondance)";"Bureau cedex (coord. correspondance)";"Code postal (coord. correspondance)";"Code commune (coord. correspondance)";"Libellé commune (coord. correspondance)";"Code pays (coord. correspondance)";"Libellé pays (coord. correspondance)";"Téléphone (coord. correspondance)";"Téléphone 2 (coord. correspondance)";"Télécopie (coord. correspondance)";"Adresse e-mail (coord. correspondance)";"Date de mise à jour (coord. correspondance)";"Date de fin (coord. correspondance)";"""
        values = """"8";"10000026632";"810000026632";"";"RESIDENCE FLEURS DE PARADIS";"";"";"";"";"RUE DU GENERAL DE GAULLE";"";"97118 ST FRANCOIS";"97118";"97125";"Saint-François";"99000";"France";"0590884193";"";"";"";"17/02/2022";"";"""
        keys = keys.replace('"', "").split(";")
        values = values.replace('"', "").split(";")
        row = {}
        for key, value in zip(keys, values):
            row[key] = value
        e = p.mapper(row)
        self.assertEqual("810000026632", e.inpp)
        self.assertEqual("RESIDENCE FLEURS DE PARADIS", e.complement_geo)
        self.assertEqual("RUE DU GENERAL DE GAULLE", e.voie)
        self.assertEqual("97118 ST FRANCOIS", e.cedex)
        self.assertEqual("97118", e.cp)
        self.assertEqual("97125", e.code_commune)
        self.assertEqual("Saint-François", e.commune)
        self.assertEqual("99000", e.code_pays)
        self.assertEqual("0590884193", e.tel)
        self.assertEqual(datetime.date(2022, 2, 17), e.date_maj)

    def test_coord_corresp_norm_mapper(self):
        p = RPPSCoordPersonneParser(None)
        keys = """"Type d'identifiant PP";"Identifiant PP";"Identification nationale PP";"Complément destinataire (coord. correspondance)";"Complément point géographique (coord. correspondance)";"Numéro Voie (coord. correspondance)";"Indice répétition voie (coord. correspondance)";"Code type de voie (coord. correspondance)";"Libellé type de voie (coord. correspondance)";"Libellé Voie (coord. correspondance)";"Mention distribution (coord. correspondance)";"Bureau cedex (coord. correspondance)";"Code postal (coord. correspondance)";"Code commune (coord. correspondance)";"Libellé commune (coord. correspondance)";"Code pays (coord. correspondance)";"Libellé pays (coord. correspondance)";"Téléphone (coord. correspondance)";"Téléphone 2 (coord. correspondance)";"Télécopie (coord. correspondance)";"Adresse e-mail (coord. correspondance)";"Date de mise à jour (coord. correspondance)";"Date de fin (coord. correspondance)";"""
        values = """107133661";"810107133661";"BATIMENT C ; APPARTEMENT 16";"";"";"";"";"";"183 AVENUE DES MARRONNIERS";"";"59113 SECLIN";"59113";"59560";"Seclin";"99000";"France";"";"";"";"";"31/05/2023";"";"""
        keys = keys.replace('"', "").split(";")
        values = values.replace('"', "").split(";")
        row = {}
        for key, value in zip(keys, values):
            row[key] = value
        e = p.mapper(row)
        context = Context()
        context.create(echo=True)
        l = context.session.query(Dept).all()
        for d in l:
            p.depts[d.num] = d
        n = p.norm_mapper(e)
        self.assertEqual("59113", n.cp)
        self.assertEqual("SECLIN", n.commune)
        self.assertEqual(97, n.dept_id)
        self.assertEqual("97125", n.iris)
        self.assertEqual("183", n.numero)
        self.assertEqual("AVENUE DES MARRONNIERS", n.rue1)

    def test_coord_activite_mapper(self):
        p = RPPSCoordActiviteParser(None)
        keys = """"Type d'identifiant PP";"Identifiant PP";"Identifiant de l'activité";"Identification nationale PP";"Identifiant technique de la structure";"Code profession";"Libellé profession";"Code catégorie professionnelle";"Libellé catégorie professionnelle";"Complément destinataire (coord. activité)";"Complément point géographique (coord. activité)";"Numéro Voie (coord. activité)";"Indice répétition voie (coord. activité)";"Code type de voie (coord. activité)";"Libellé type de voie (coord. activité)";"Libellé Voie (coord. activité)";"Mention distribution (coord. activité)";"Bureau cedex (coord. activité)";"Code postal (coord. activité)";"Code commune (coord. activité)";"Libellé commune (coord. activité)";"Code pays (coord. activité)";"Libellé pays (coord. activité)";"Téléphone (coord. activité)";"Téléphone 2 (coord. activité)";"Télécopie (coord. activité)";"Adresse e-mail (coord. activité)";"Date de mise à jour (coord. activité)";"Date de fin (coord. activité)";"""
        values = """"8";"10004973441";"1010656965";810004973441;"R10100000026103";"10";"Médecin";"C";"Civil";"DRSMG";"ESPACE TURENNE RADAMONTHE";"";"";"";"";"RTE DE RABAN";"BP 167";"97307 CAYENNE CEDEX";"97307";"97302";"Cayenne";"99000";"France";"0594396140";"0694490698";"0594396148";"songyangcrosson@yahoo.fr";"23/04/2015";"";"""
        keys = keys.replace('"', "").split(";")
        values = values.replace('"', "").split(";")
        row = {}
        for key, value in zip(keys, values):
            row[key] = value
        e = p.mapper(row)
        self.assertEqual("1010656965", e.identifiant_activite)
        self.assertEqual("DRSMG", e.complement_destinataire)
        self.assertEqual("ESPACE TURENNE RADAMONTHE", e.complement_geo)
        self.assertEqual("RTE DE RABAN", e.voie)
        self.assertEqual("BP 167", e.mention)
        self.assertEqual("97307 CAYENNE CEDEX", e.cedex)
        self.assertEqual("97307", e.cp)
        self.assertEqual("97302", e.code_commune)
        self.assertEqual("Cayenne", e.commune)
        self.assertEqual("99000", e.code_pays)
        self.assertEqual("0594396140", e.tel)
        self.assertEqual("0694490698", e.tel2)
        self.assertEqual("songyangcrosson@yahoo.fr", e.mail)
        self.assertEqual(datetime.date(2015, 4, 23), e.date_maj)


    def test_coord_structure_mapper(self):
        p = RPPSCoordStructureParser(None)
        keys = """"Identifiant technique de la structure";"Complément destinataire (coord. structure)";"Complément point géographique (coord. structure)";"Numéro Voie (coord. structure)";"Indice répétition voie (coord. structure)";"Code type de voie (coord. structure)";"Libellé type de voie (coord. structure)";"Libellé Voie (coord. structure)";"Mention distribution (coord. structure)";"Bureau cedex (coord. structure)";"Code postal (coord. structure)";"Code commune (coord. structure)";"Libellé commune (coord. structure)";"Code pays (coord. structure)";"Libellé pays (coord. structure)";"Téléphone (coord. structure)";"Téléphone 2 (coord. structure)";"Télécopie (coord. structure)";"Adresse e-mail (coord. structure)";"Date de mise à jour (coord. structure)";"Date de fin (coord. structure)";"""
        values = """"F97010871811041988";"";"";"55";"";"LOT";"Lotissement";"DE BELCOURT";"";"97122 BAIE-MAHAULT";"97122";"97103";"Baie-Mahault";"99000";"France";"0590262224";"";"0059026222";"";"07/09/2009";"";"""
        keys = keys.replace('"', "").split(";")
        values = values.replace('"', "").split(";")
        row = {}
        for key, value in zip(keys, values):
            row[key] = value
        e = p.mapper(row)
        self.assertEqual("F97010871811041988", e.structure_id_technique)
        self.assertEqual("55", e.numero)
        self.assertEqual("LOT", e.code_type_voie)
        self.assertEqual("Lotissement", e.type_voie)
        self.assertEqual("DE BELCOURT", e.voie)
        self.assertEqual("97122 BAIE-MAHAULT", e.cedex)
        self.assertEqual("97122", e.cp)
        self.assertEqual("97103", e.code_commune)
        self.assertEqual("Baie-Mahault", e.commune)
        self.assertEqual("99000", e.code_pays)
        self.assertEqual("0590262224", e.tel)
        self.assertEqual(datetime.date(2009, 9, 7), e.date_maj)

    def test_coord_structure_geoloc_mapper(self):
        p = RPPSCoordStructureGeolocParser(None)
        keys = """"Identifiant technique de la structure";Latitude (coordonnées GPS);Longitude (coordonnées GPS);Type de précision (coordonnées GPS);"Précision (coordonnées GPS)";"""
        values = """"F92002048422031994";"48.774916";" 2.313346";Street number;",93";"""
        keys = keys.replace('"', "").split(";")
        values = values.replace('"', "").split(";")
        row = {}
        for key, value in zip(keys, values):
            row[key] = value
        e = p.mapper(row)
        self.assertEqual("F92002048422031994", e.structure_id_technique)
        self.assertEqual(48.774916, e.lat)
        self.assertEqual(2.313346, e.lon)
        self.assertEqual(0, e.type_precision)
        self.assertEqual(0.93, e.precision)

    def test_re_quote(self):
        p = rpps_etat_civil_parser.RPPSEtatCivilParser(None)
        row = '"toto";"titi";"1;x";"A;x";"A ;x";"A; x";"A;";";A";"END";\n"A";"B";'
        row = p.escape_dot_comma(row)
        self.assertEqual('"toto";"titi";"1,x";"A,x";"A ,x";"A, x";"A,";"A";"END";\n"A";"B";', row)
