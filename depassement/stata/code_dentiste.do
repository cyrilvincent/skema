///dentiste////

import delimited "C:\Users\conta\git-CVC\Skema\git-skema\data\depassement\dentistes.csv", clear

import delimited "C:\Users\conta\git-CVC\Skema\git-skema\data\depassement\d2.csv", clear
rename genre gender
rename prenom prénom
rename code codeccamdelacte
rename nature_id naturedexercice
rename convention_id convention
rename code_insee codeinsee
rename code_postal matchcp
rename montant  montantgénéralementconstaté 
rename borne_inf borneinférieuredumontant
rename borne_sup bornesupérieuredumontant
rename option_contrat optioncontratdaccèsauxsoins
rename dept_id dep


keep ps_id gender nom prénom codeccamdelacte naturedexercice convention codeinsee  montantgénéralementconstaté borneinférieuredumontant bornesupérieuredumontant adresse_id date_source_id optioncontratdaccèsauxsoins matchcp dep
egen b =concat(ps_id adresse_id)
distinct ps_id
distinct b

sort ps_id
unique adresse_id, by(ps_id) gen(unique)
by ps_id: egen un=mean(unique)

////Algo pour corriger l'excès d'appareillage (à copier/coller pour APL?)////
///prenons les ind qui ont plusieurs type d'options///


unique ps_id, by(dep) gen(NB_total)
sort dep
by dep: egen NBBB=max(NB_total)
drop NB_total
rename NBBB NB_total
gen c=1
unique ps_id, by(c) gen(NB_Ftotal)
egen NBB_Ftotal=max(NB_Ftotal)
drop NB_Ftotal
rename NBB_Ftotal NB_Ftotal


gen weight=0
replace weight=1 if un==1
replace weight=0.5 if un==2
replace weight=0.33 if un==3
replace weight=0.25 if un==4
replace weight=0.2 if un==5

keep if codeccamdelacte=="HBLD4910" | codeccamdelacte== "HBLD6340"|  codeccamdelacte== "HBLD7340"
tab codeccamdelacte

///Tarif base sécu: 120




distinct ps_id

drop if montantgénéralementconstaté==0

distinct ps_id


sort convention
by convention:  distinct ps_id
tab codeccamdelacte
sort b convention date_source_id
by b convention: egen mp=mean(montantgénéralementconstaté) if codeccamdelacte=="HBLD4910"
by b convention: egen mp2=mean(montantgénéralementconstaté) if codeccamdelacte=="HBLD6340"
by b convention: egen mp3=mean(montantgénéralementconstaté) if codeccamdelacte=="HBLD7340"

/// Correction Cyril // Save dentiste_debug
by b convention: egen temp=max(mp)
drop mp
rename temp mp
by b convention: egen temp=max(mp2)
drop mp2
rename temp mp2
by b convention: egen temp=max(mp3)
drop mp3
rename temp mp3

// Correction Cyril 2
unique ps_id if codeccamdelacte=="HBLD4910", by(dep convention) gen(NB)
sort dep convention
by dep convention: egen temp=mean(NB)
drop NB
rename temp NB
unique ps_id if codeccamdelacte=="HBLD6340", by(dep convention) gen(NB2)
by dep convention: egen temp=mean(NB2)
drop NB2
rename temp NB2
unique ps_id if codeccamdelacte=="HBLD7340", by(dep convention) gen(NB3)
by dep convention: egen temp=mean(NB3)
drop NB3
rename temp NB3
unique ps_id if codeccamdelacte=="HBLD4910", by(c) gen(NB_F)
egen temp=mean(NB_F)
drop NB_F
rename temp NB_F
unique ps_id if codeccamdelacte=="HBLD6340", by(c) gen(NB2_F)
egen temp=mean(NB2_F)
drop NB2_F
rename temp NB2_F
unique ps_id if codeccamdelacte=="HBLD7340", by(c) gen(NB3_F)
egen temp=mean(NB3_F)
drop NB3_F
rename temp NB3_F

duplicates drop b convention, force
sort b convention
by b convention: egen prixmoyen=max(mp)
by b convention: egen prixmoyen2=max(mp2)
by b convention: egen prixmoyen3=max(mp3)
duplicates drop b convention, force

distinct ps_id
distinct ps_id if convention==1
distinct ps_id if convention==2
distinct ps_id if convention==3

duplicates drop b, force

////Prix OK //// Cyril : sauvegardé dans dentiste_prix_ok

// Mis en commentaire par Cyril
//sort dep
//unique ps_id if codeccamdelacte=="HBLD4910", by(dep) gen(NB)
//by dep: egen NB2=mean(NB)
//replace NB2=0 if NB2==.
//drop NB
//rename NB2 NB
//unique ps_id if codeccamdelacte=="HBLD4910", by(c) gen(NB_F)
//egen NBB_F=mean(NB_F)
//drop NB_F
//rename NBB_F NB_F
//unique ps_id if codeccamdelacte=="HBLD6340", by(dep) gen(NB2)
//by dep: egen NB22=mean(NB2)
//replace NB22=0 if NB22==.
//drop NB2
//rename NB22 NB2
//unique ps_id if codeccamdelacte=="HBLD6340", by(c) gen(NB2_F)
//egen NBB2_F=mean(NB2_F)
//drop NB2_F
//rename NBB2_F NB2_F
//unique ps_id if codeccamdelacte=="HBLD7340", by(dep) gen(NB3)
//by dep: egen NB32=mean(NB3)
//replace NB32=0 if NB32==.
//drop NB3
//rename NB32 NB3
//unique ps_id if codeccamdelacte=="HBLD7340", by(c) gen(NB3_F)
//egen NBB3_F=mean(NB3_F)
//drop NB3_F
//rename NBB3_F NB3_F

// Save dentiste_prix_ok

gen exessr=((prixmoyen-120)/120)*100
gen exessr2=((prixmoyen2-120)/120)*100
gen exessr3=((prixmoyen3-120)/120)*100



****dépassement moyen par département (uniquement les acteurs  faisant du dépassement)
egen PF=mean(prixmoyen)
egen PF2=mean(prixmoyen2)
egen PF3=mean(prixmoyen3)

by dep: egen PrixMoyen =mean(prixmoyen)
by dep: egen PrixMoyen2 =mean(prixmoyen2)
by dep: egen PrixMoyen3 =mean(prixmoyen3)

by dep: gen depmoyen=[(PrixMoyen-120)/120]*100
by dep: gen depmoyen2=[(PrixMoyen2-120)/120]*100
by dep: gen depmoyen3=[(PrixMoyen3-120)/120]*100

gen depmoyen_F=[(PF-120)/120]*100
gen depmoyen_F2= [(PF2-120)/120]*100
gen depmoyen_F3= [(PF3-120)/120]*100

//gen exess=exessr
//gen exess2=exessr2
//gen exess3=exessr3

//by dep: egen deppratiqué=mean(exess)
//by dep: egen deppratiqué2=mean(exess2)
//by dep: egen deppratiqué3=mean(exess3)


//by dep: egen deppratiqué_F=mean(exess)
//by dep: egen deppratiqué2_F=mean(exess2)
//by dep: egen deppratiqué3_F=mean(exess3)



gsort dep -depmoyen 
duplicates drop dep, force

drop gender nom prénom naturedexercice convention optioncontratdaccèsauxsoins codeccamdelacte ps_id montantgénéralementconstaté borneinférieuredumontant bornesupérieuredumontant date_source_id adresse_id matchcp codeinsee b unique un weight mp mp2 mp3 exessr exessr2 exessr3  prixmoyen prixmoyen2 prixmoyen3 


expand 2 if dep==75, gen(dup)
replace dep=0 if dup==1
replace NB_total=NB_Ftotal if dup==1
replace NB=NB_F if dup==1
replace NB2=NB2_F if dup==1
replace NB3=NB3_F if dup==1
replace PrixMoyen = PF if dup==1
replace PrixMoyen2 = PF2 if dup==1
replace PrixMoyen3 = PF3 if dup==1
replace depmoyen = depmoyen_F if dup==1
replace depmoyen2 = depmoyen_F2 if dup==1
replace depmoyen3 = depmoyen_F3 if dup==1
//replace deppratiqué = deppratiqué_F if dup==1
//replace deppratiqué2 = deppratiqué2_F if dup==1
//replace deppratiqué3 = deppratiqué3_F if dup==1

drop NB_Ftotal NB_F NB2_F NB3_F PF PF2 PF3 depmoyen_F  depmoyen_F2 depmoyen_F3   dup c
export delimited using "C:\Users\benjamin.montmartin\Desktop\Etude UFC 2023\Part III\dépassement_dentistes.csv", replace