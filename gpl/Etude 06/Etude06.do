import delimited "C:\Users\benjamin.montmartin\Desktop\Etude 06\logements-en-2015-maille-iris.csv", clear
keep if codeinseecommune>"05999" & codeinseecommune<"07000"
duplicates drop codeiris, force
save "C:\Users\benjamin.montmartin\Desktop\Etude 06\ciris06.dta", replace
gen CIRIS=codeiris
save "C:\Users\benjamin.montmartin\Desktop\Etude 06\ciris06.dta", replace


use "C:\Users\benjamin.montmartin\Desktop\Etude 06\iris06.dta"
mmerge CIRIS using ciris06.dta
drop  logementsen2015princ résidencesprincipalesen2015princ réssecondairesetlogtsoccasionnel logementsvacantsen2015princ maisonsen2015princ appartementsen2015princ résprinc1pièceen2015princ résprinc2piècesen2015princ résprinc3piècesen2015princ résprinc4piècesen2015princ résprinc5piècesouplusen2015princ piècesrésprincen2015princ résprinctypemaisonen2015princ piècesrésprinctypemaisonen2015pr résprinctypeappartementen2015pri piècesrésprinctypeappartementen2 résprincdemoinsde30m2en2015princ résprincde30àmoinsde40m2en2015pr résprincde40àmoinsde60m2en2015pr résprincde60àmoinsde80m2en2015pr résprincde80àmoinsde100m2en2015p résprincde100àmoinsde120m2en2015 résprincde120m2ouplusen2015princ résprincavt2013en2015princ résprincavt1919en2015princ résprinc1919à1945en2015princ résprinc1946à1970en2015princ résprinc1971à1990en2015princ résprinc1991à2005en2015princ résprinc2006à2012en2015princ résprinctypemaisonavt2013en2015p résprinctypemaisonavt1919en2015p résprinctypemaison1919à1945en201 résprinctypemaison1946à1970en201 résprinctypemaison1971à1990en201 résprinctypemaison1991à2005en201 résprinctypemaison2006à2012en201 résprinctypeappartavt2013en2015p résprinctypeappartavt1919en2015p résprinctypeappart1919à1945en201 résprinctypeappart1946à1970en201 résprinctypeappart1971à1990en201 résprinctypeappart1991à2005en201 résprinctypeappart2006à2012en201 ménagesen2015princ ménagesemménagésmoins2ansen2015p ménagesemménagésentre24ansen2015 ménagesemménagésentre59ansen2015 ménagesemménagésdepuis10ansouplu popménagesen2015princ popménemménagésmoins2ansen2015pr popménemménagésentre24ansen2015p popménemménagésentre59ansen2015p popménemménagésdepuis10ansouplus piècesrésprincménemménagésmoins2 piècesrésprincménemménagésentre2 piècesrésprincménemménagésentre5 piècesrésprincménemménagésdepuis résprincoccupéespropriétairesen2 résprincoccupéeslocatairesen2015 résprinchlmlouéevideen2015princ résprinclogégratuiten2015princ personnesrésprincen2015princ persrésprincoccupéespropriétaire persrésprincoccupéeslocatairesen persrésprinchlmlouéesvidesen2015 persrésprincoccupéesgratuiten201 anctotemméngtrésprincannéesen201 anctotemméngtrésprincoccparpropr anctotemméngtrésprincoccparlocat anctotemméngtrésprinchlmlouéesvi anctotemméngtrésprincoccgratuita résprincsdbbaignoiredouchemeten2 résprincchauffagecentralcollecti résprincchauffagecentralindividu résprincchauffageindividuelelect résprincavecélectricitédomen2015 résprincaveceauchaudedomen2015pr résprincavecbaindouchewcdomen201 résprincavecchauffeeausolairedom résprincavecpièceclimatiséedomen résprincavectoutàlégoutdomen2015 ménagesaumoinsunparkingen2015pri ménagesaumoinsunevoitureen2015pr ménagesunevoitureen2015princ ménagesdeuxvoituresouplusen2015p habitationsdefortunedomen2015pri casestraditionnellesdomen2015pri maisonsouimmeublesenboisdomen201 maisonsouimmeublesendurdomen2015
save "C:\Users\benjamin.montmartin\Desktop\Etude 06\iris06WC.dta"

import excel "C:\Users\benjamin.montmartin\Desktop\Etude 06\irisWC.xls", sheet("Sheet1") firstrow clear
gen ID=_n
save "C:\Users\benjamin.montmartin\Desktop\Etude 06\iris06WCWL.dta"

forvalues i = 1/500 {
	use "C:\Users\benjamin.montmartin\Desktop\Etude 06\iris06WCWL.dta", replace
	drop  CodeIRIS LibelléIRIS TypeIRIS GrandQuartier Codedépartementcommune Libellédecommune Unitéurbaine2020 Région Département CIRIS codeiris région département unitéurbaine codeinseecommune libellécommuneouarm grandquartier libellédeliris nomdelepci 	 nomdudépartement nomdelarégion geoshape lat lon 
	gen NUM=ID if ID==`i'
	replace NUM=`i' if NUM==.
	gen double X1=X if ID==`i'
	fillmissing X1, with(any)
	gen double Y1=Y if ID==`i'
	fillmissing Y1, with(any)
	rename X X2
	rename Y Y2
	drop ID
	order NUM X1 Y1 X2 Y2
	drop NUM
	save "C:\Users\benjamin.montmartin\Desktop\Etude 06\File_distance\DIS`i'.dta", replace
	}
	

	use DIS1, clear
forvalues i = 2/500 {
	append using DIS`i'
}
save "C:\Users\benjamin.montmartin\Desktop\Etude 06\File_distance\ODcomp.dta"
use ODcomp.dta, clear


////Extraire en dbf et faire test sous METRIC///
///Importer base avec outcome METRIC et identifier les iris problématiques ie 9999
import dbase using "C:\Users\benjamin.montmartin\Desktop\Metric\Metric\sorties\couples_infra_ODcomp_HP.dbf", clear
sort X1
keep if HP==9999
tab X1
by X1: egen c=count(X1)
keep if c==500
duplicates drop X1 Y1
duplicates drop X1 Y1, force
///EXPORT DE CETTE LISTE SOUS FICHIER EXCEL DE BASE ET IDENTIFICATION DES IRIS PRBLEMATIQUE
///REIMPORT DU NOUVEAU FICHIER SOUS STATA


///STRAT 1: on voit si un round sur X et Y gère le souci
import excel "C:\Users\benjamin.montmartin\Desktop\Etude 06\irisWC_C.xls", sheet("Sheet1") firstrow clear
save "C:\Users\benjamin.montmartin\Desktop\Etude 06\iris06WC_C.dta"
gen ID=_n
save "C:\Users\benjamin.montmartin\Desktop\Etude 06\iris06WCWL_C.dta", replace
use  "C:\Users\benjamin.montmartin\Desktop\Etude 06\iris06WCWL_C.dta", clear


forvalues i = 1/500 {
	use "C:\Users\benjamin.montmartin\Desktop\Etude 06\iris06WCWL_C.dta", replace
	drop  CodeIRIS LibelléIRIS TypeIRIS GrandQuartier Codedépartementcommune Libellédecommune Unitéurbaine2020 Région Département CIRIS codeiris région département unitéurbaine codeinseecommune libellécommuneouarm grandquartier libellédeliris nomdelepci 	 nomdudépartement nomdelarégion geoshape lat lon X Y BADCENTROID
	gen NUM=ID if ID==`i'
	replace NUM=`i' if NUM==.
	gen double X1=XX if ID==`i'
	fillmissing X1, with(any)
	gen double Y1=YY if ID==`i'
	fillmissing Y1, with(any)
	rename XX X2
	rename YY Y2
	drop ID
	order NUM X1 Y1 X2 Y2
	drop NUM
	save "C:\Users\benjamin.montmartin\Desktop\Etude 06\File_distance\DIS_C`i'.dta", replace
	}
	
	use DIS_C1, clear
forvalues i = 2/500 {
	append using DIS_C`i'
}
save "C:\Users\benjamin.montmartin\Desktop\Etude 06\File_distance\ODcomp_C.dta"
use ODcomp_C.dta, clear
////STRAT 1 inefficace

////Nécessité de changer directement les coordonnées X et Y 
///retour fichier excel et recherche des nouvelles coordonnées (chef - lieu sur annuaire-mairie.fr)

import excel "C:\Users\benjamin.montmartin\Desktop\Etude 06\irisWC_C.xls", sheet("Sheet1") firstrow clear
save "C:\Users\benjamin.montmartin\Desktop\Etude 06\iris06WC_C.dta", replace
gen ID=_n
save "C:\Users\benjamin.montmartin\Desktop\Etude 06\iris06WCWL_C.dta", replace
use  "C:\Users\benjamin.montmartin\Desktop\Etude 06\iris06WCWL_C.dta", clear


forvalues i = 1/500 {
	use "C:\Users\benjamin.montmartin\Desktop\Etude 06\iris06WCWL_C.dta", replace
	drop  CodeIRIS LibelléIRIS TypeIRIS GrandQuartier Codedépartementcommune Libellédecommune Unitéurbaine2020 Région Département CIRIS codeiris région département unitéurbaine codeinseecommune libellécommuneouarm grandquartier libellédeliris nomdelepci 	 nomdudépartement nomdelarégion geoshape lat lon X Y BADCENTROID XX_ville YY_ville
	gen NUM=ID if ID==`i'
	replace NUM=`i' if NUM==.
	gen double X1=XX if ID==`i'
	fillmissing X1, with(any)
	gen double Y1=YY if ID==`i'
	fillmissing Y1, with(any)
	rename XX X2
	rename YY Y2
	drop ID
	order NUM X1 Y1 X2 Y2
	drop NUM
	save "C:\Users\benjamin.montmartin\Desktop\Etude 06\File_distance\DIS_C`i'.dta", replace
	}

		use DIS_C1, clear
forvalues i = 2/500 {
	append using DIS_C`i'
}

save "C:\Users\benjamin.montmartin\Desktop\Etude 06\File_distance\ODcomp_C.dta", replace
use ODcomp_C.dta, clear


///On obtient toutes les données avec METRIC MAIS CELLES SUR LES IRIS PRBS NE SONT PAS BONNES POUR HP ET HC**
///Nécessité de corriger les données de temps de trajet pour ces iris06
///Probablement nécessité de combiner avec données HP / HC communes
///nécessité de combiner HP, HC et KM meme pour l'infra

/////Utilisation de Google Maps pour le calcul des distances + temps de trajet...cf python code Google Maps.
////Pour que l'utilisation de Google Maps soit efficace, il faut utiliser les lat/lon des mairies pour les territoires non IRISés
///Les coordonnées sont disponibles pour les mairies en utilisant le site opendatsoft "Annuaire de l'administration - Base de données locales"



