clear all
cd "C:\Users\benjamin.montmartin\Desktop\DONNEES IRIS 06\IRIS-GE_2-0__SHP_LAMB93_D006_2021-01-01\IRIS-GE\1_DONNEES_LIVRAISON_2021-06-00052\IRIS-GE_2-0_SHP_LAMB93_D006-2021"
spshape2dta IRIS_GE.SHP
use IRIS_GE, clear
describe
import delimited "C:\Users\benjamin.montmartin\Desktop\Etude 06\Rendus\APL_IRIS_06.csv", clear
gen str9 CODE_IRIS = string(iris1,"%09.0f")
merge 1:1 CODE_IRIS using IRIS_GE

spmap apl using IRIS_GE_shp, id(_ID) fcolor(Rainbow) cln(8) title("Alpes-Maritimes")

spmap apl using IRIS_GE_shp if libcom=="Nice", id(_ID) fcolor(Rainbow) clmethod(custom) clb(0 20 63 88 108 119 136 156 232) title("Nice")

spmap apl using IRIS_GE_shp if libcom=="Cannes", id(_ID) fcolor(Rainbow) clmethod(custom) clb(0 20 63 88 108 119 136 156 232) title("Cannes") 

spmap apl using IRIS_GE_shp if libcom=="Antibes", id(_ID) fcolor(Rainbow) clmethod(custom) clb(0 20 63 88 108 119 136 156 232) title("Antibes")   





cd "C:\Users\benjamin.montmartin\Desktop\DONNEES GEO DEPARTEMENTS"
spshape2dta departements-20180101.shp
use departements-20180101, clear
drop if code_insee=="972" |code_insee=="974"|code_insee=="971"|code_insee=="973"|code_insee=="976"
replace code_insee="69" if code_insee=="69D"|code_insee=="69M"
replace code_insee="201" if code_insee=="2A"
replace code_insee="202" if code_insee=="2B"
destring code_insee, gen(dep) force
sort dep
save dep
import delimited "C:\Users\benjamin.montmartin\Desktop\Etude UFC 2023\Part III\dep_dentistes.csv", clear 
sort dep
merge dep using dep

spmap deppratiqué3 using departements-20180101_shp, id(_ID) fcolor(Rainbow) cln(8) title("Dépassements honoraires couronne dentaire")

clear all
cd "C:\Users\benjamin.montmartin\Desktop\DONNEES GEO DEPARTEMENTS"
use dep
import delimited "C:\Users\benjamin.montmartin\Desktop\Etude UFC 2023\Part III\dep_radiologue.csv", clear 
sort dep
merge dep using dep

spmap deppratiquã using departements-20180101_shp, id(_ID) fcolor(Rainbow) cln(8) title("Dépassements honoraires consultation radio")

clear all
cd "C:\Users\benjamin.montmartin\Desktop\DONNEES GEO DEPARTEMENTS"
use dep
import delimited "C:\Users\benjamin.montmartin\Desktop\Etude UFC 2023\Part III\dep_psy.csv", clear 
sort dep
merge dep using dep

spmap deppratiqué using departements-20180101_shp, id(_ID) fcolor(Rainbow) cln(8) title("Dépassements honoraires psychiatres")

clear all
cd "C:\Users\benjamin.montmartin\Desktop\DONNEES GEO DEPARTEMENTS"
use dep
import delimited "C:\Users\benjamin.montmartin\Desktop\Etude UFC 2023\Part III\dep_ophtal.csv", clear 
sort dep
merge dep using dep

spmap deppratiqué using departements-20180101_shp, id(_ID) fcolor(Rainbow) cln(8) title("Dépassements honoraires ophtalmologistes")
