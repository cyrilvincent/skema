cd "C:\Users\benjamin.montmartin\Desktop\Etude 06"
use Gene06.dta, clear
///Base de données extraite de la plateforme à partir de la commande SQL Généralistes avec "duplicates drop id lat lon, force"
distinct id
//1189 généralistes dans le département pour 1288 couple ps-adresse

egen b =concat(id lat lon)
distinct b

///génère variable un qui compte le nombre de localisation/médecin
sort id
unique b, by(id) gen(unique)
by id: egen un=mean(unique)

tab un

///génère variable qui pondère l'activité d'un médecin en fonction de ses adresses
gen weight=0
replace weight=1 if un==1
replace weight=0.5 if un==2
replace weight=0.33 if un==3
replace weight=0.25 if un==4

////génère la variable qui NB qui donne le nombre de médecin ETP/iris
sort iris
by iris: egen NB=sum(weight)
duplicates drop iris NB, force
save nbgpiris2022.dta, replace
///nbgpiris2022 donne pour chaque iris le nombre de médecin ETP s'il existe au moins un médecin dans l'iris. 

////Utilisation de la sortie Google Maps, fichier Coordinates_distancematrix.csv puis nettoyage.
///Penser à tester les codes OSM pour obtenir le même fichier ou écrire code pour générer cette OD finale
use ODFinale.dta, replace
drop if TIME>30
gen iris=.
format iris %10.0g 
recast long iris
replace iris=IRIS2 if iris==.
distinct iris
mmerge iris using popIRIS.dta
gen WexpGP=exp(-0.12*TIME)
save popiris2022.dta, replace
///On merge la base de données recensement population par iris à la base OD finale par la colonne de destination.
///On élimine les destinations à plus de 30 minutes de distance
// Pour chaque destination, on calcule la valeur de la fonction exponentielle négative et on appelle cette base popiris2022.



sort IRIS2
destring P19_POP0002 P19_POP0305 P19_POP0610 P19_POP1117 P19_POP1824 P19_POP2539 P19_POP4559 P19_POP6074 P19_POP75P, replace
by IRIS2: gen POPGP=0.759201627*P19_POP0002+0.759201627*P19_POP0305+0.759201627*P19_POP0610+0.759201627*P19_POP1117+0.784999993*P19_POP1824+0.915*P19_POP2539+1.05*P19_POP4559+1.4*P19_POP6074+1.3*P19_POP75P
save popiris2022.dta, replace
///On organise par destination et on calcule pour chaque destination la population effective qui tient compte de la consommation de consultation / age. Fait à partir d'open DAMIR, procédure à optimiser
///On save
///Popiris2022 donne les données par DESTINATION


drop KM iris COM TYP_IRIS MODIF_IRIS LAB_IRIS P19_POP P19_POP0002 P19_POP0305 P19_POP0610 P19_POP1117 P19_POP1824 P19_POP2539 P19_POP4054 P19_POP5564 P19_POP6579 P19_POP80P P19_POP0014 P19_POP1529 P19_POP3044 P19_POP4559 P19_POP6074 P19_POP75P P19_POP0019 P19_POP2064 P19_POP65P P19_POPH P19_H0014 P19_H1529 P19_H3044 P19_H4559 P19_H6074 P19_H75P P19_H0019 P19_H2064 P19_H65P P19_POPF P19_F0014 P19_F1529 P19_F3044 P19_F4559 P19_F6074 P19_F75P P19_F0019 P19_F2064 P19_F65P _merge WexpGP POPGP
save ODgeneralistes06.dta, replace
//// On conserve une base OD avec temps de trajet uniquement appelé ODgeneralistes06


use popiris2022.dta, replace
sort IRIS1
drop iris
gen iris=.
format iris %10.0g 
recast long iris
replace iris=IRIS1 if iris==.
mmerge iris using nbgpiris2022.dta
replace NB=0 if NB==.
sort IRIS1 IRIS2
duplicates drop IRIS1 IRIS2, force
save IRIS2022.dta, replace
///On prend le fichier popiris2022, on sort par origine et on merge avec le fichier qui donne le nombre ETP de médecin par iris
///Dans le fichier IRIS2022, on a pour l'ensemble des couples IRIS à moins de 30mins organiser par ORIGINE: population effective de la destination (POPGP) et le nombre de médecin dans l'origine, 

sort IRIS1
by IRIS1: gen wpop=WexpGP*(POPGP)
by IRIS1: egen swpop=sum(wpop)
by IRIS1: gen R=NB/(swpop/100000)
keep if IRIS1==IRIS2
////on sorte par origine et on calcule WPOP qui représente le produit de la distance exponentielle et de la population effective de la destination 
///Par origine, on calcule la somme de ce produit (demande effective/adressable par iris donc pour un médecin localisé dans cet iris )
/// On calcule le ratio par iris offre interne/demande adressable (R)
/// On supprime les doublons en conservant ce R pour chaque IRIS

keep IRIS1 COM TYP_IRIS POPGP NB R
gen IRIS2=.
format IRIS2 %10.0g 
recast long IRIS2
replace IRIS2=IRIS1 if IRIS2==.
save RGP2022.dta, replace
///On conserve les infos critiques et on génère IRIS2=IRIS1 qu'on appelle RGP2022
use IRIS2022.dta, replace
mmerge IRIS2 using RGP2022.dta
///On utilise la base avec l'ensemble des couples origines destinations classé par ORIGINE que l'on merge avec ce R de la DESTINATION
sort IRIS1 IRIS2
by IRIS1: gen Ap=WexpGP*R
by IRIS1: egen APL=sum(Ap)
keep if IRIS1==IRIS2
///On calcule la somme pondéré du R par IRIS (mon R tient compte de la demande adjacente mais les autres R tiennent compte de ma demande)
///Je bénéficie pleinement de mon R et dans une moindre mesure du R des autres
///Calcul de l'APL
sum APL, detail

drop  IRIS2 KM TIME MODIF_IRIS LAB_IRIS P19_POP P19_POP0002 P19_POP0305 P19_POP0610 P19_POP1117 P19_POP1824 P19_POP2539 P19_POP4054 P19_POP5564 P19_POP6579 P19_POP80P P19_POP0014 P19_POP1529 P19_POP3044 P19_POP4559 P19_POP6074 P19_POP75P P19_POP0019 P19_POP2064 P19_POP65P P19_POPH P19_H0014 P19_H1529 P19_H3044 P19_H4559 P19_H6074 P19_H75P P19_H0019 P19_H2064 P19_H65P P19_POPF P19_F0014 P19_F1529 P19_F3044 P19_F4559 P19_F6074 P19_F75P P19_F0019 P19_F2064 P19_F65P WexpGP POPGP iris id genre key nom prenom profession_id dept_id numero rue1 rue2 cp commune lon lat ban_id code_insee b unique un weight R _merge Ap
keep IRIS1 TYP_IRIS NB APL 
save "C:\Users\benjamin.montmartin\Desktop\Etude 06\APL06_2022.dta", replace
mmerge IRIS1 using NomIRIS.dta
drop UU2020 REG DEP _merge GRD_QUART 
save "C:\Users\benjamin.montmartin\Desktop\Etude 06\APL06_2022_Final.dta", replace
