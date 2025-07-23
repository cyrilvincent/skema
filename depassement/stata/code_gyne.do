///gyne////

import delimited "C:\Users\benjamin.montmartin\Desktop\Etude UFC 2023\Part III\gyne.csv", clear
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

unique ps_id, by(dep) gen(NB_total)
sort dep
by dep: egen NBBB=max(NB_total)
drop NB_total
rename NBBB NB_total
unique ps_id if convention ==2 | convention==1 & optioncontratdaccèsauxsoins=="true" |convention ==3, by(dep) gen(NB2_total)
by dep: egen NBB2=max(NB2_total)
drop NB2_total
rename NBB2 NB2_total
gen c=1
unique ps_id, by(c) gen(NB_Ftotal)
egen NBB_Ftotal=max(NB_Ftotal)
drop NB_Ftotal
rename NBB_Ftotal NB_Ftotal
unique ps_id if convention ==2 | convention==1 & optioncontratdaccèsauxsoins=="true" |convention ==3, by(c) gen(NB2_Ftotal)
egen NBB2_Ftotal=max(NB2_Ftotal)
drop NB2_Ftotal
rename NBB2_Ftotal NB2_Ftotal



////Algo pour corriger l'excès d'appareillage (à copier/coller pour APL?)////
///prenons les ind qui ont plusieurs type d'options///
gen cc=-1 if optioncontratdaccèsauxsoins=="false"
replace cc=1 if optioncontratdaccèsauxsoins=="true"
sort ps_id
by ps_id: egen ccc=mean(cc)

preserve
drop if ccc==-1 |ccc==1
sort ps_id date_source_id

unique ps_id

restore



gen weight=0
replace weight=1 if un==1
replace weight=0.5 if un==2
replace weight=0.33 if un==3
replace weight=0.25 if un==4
replace weight=0.2 if un==5

keep if strpos(codeccamdelacte, "CS")
tab codeccamdelacte

///Tarif S1: 30 euros (23 (CS) +2 (MPC) +5 (MCS)) 


distinct ps_id


sort convention
by convention:  distinct ps_id
tab codeccamdelacte
sort b convention codeccamdelacte date_source_id
by b convention  codeccamdelacte: egen mp=mean(montantgénéralementconstaté)

keep if codeccamdelacte=="CS_" |codeccamdelacte=="CS_+MPC"|codeccamdelacte=="CS_+MPC+MCS"|codeccamdelacte=="CS_+MGM"|codeccamdelacte=="CS_+MGM+MCS"

replace mp=30 if convention==1 & optioncontratdaccèsauxsoins=="false"

****on élimine les duplications ps-adresse convention acte puis on sélectionne le prix le plus élevé d'un acte de consultation (discard tarif opposable des secteurs 2)
***puis on élimine les duplications ps-adresse convention (car les actes ont le même prix maintenant pour chaque ps-adresse)
duplicates drop b convention  codeccamdelacte, force
sort b convention
by b convention: egen prixmoyen=max(mp)
duplicates drop b convention, force

distinct ps_id
distinct ps_id if convention==1
distinct ps_id if convention==2
distinct ps_id if convention==3

duplicates drop b, force
replace prixmoyen=30 if prixmoyen==0

////Prix OK ////


sort dep
unique ps_id, by(dep) gen(NB)
by dep: egen NB2=mean(NB)
replace NB2=0 if NB2==.
drop NB
rename NB2 NB
unique ps_id, by(c) gen(NB_F)
egen NBB_F=mean(NB_F)
drop NB_F
rename NBB_F NB_F
unique ps_id if convention ==2 | convention==1 & optioncontratdaccèsauxsoins=="true" |convention ==3, by(dep) gen(NB2) 
by dep: egen NB22=mean(NB2)
replace NB22=0 if NB22==.
drop NB2
rename NB22 NB2
unique ps_id if convention ==2 | convention==1 & optioncontratdaccèsauxsoins=="true" |convention ==3, by(c) gen(NB2_F) 
egen NBB2_F=mean(NB2_F)
drop NB2_F
rename NBB2_F NB2_F
by dep: gen ShareS2=NB2/NB
by dep: gen ShareS2_F=NB2_F/NB_F

gen exessr=((prixmoyen-30)/30)*100
by dep: egen nb10=count(exessr) if exessr>=10
by dep: egen c10=max(nb10)
replace c10=0 if c10==.
by dep: egen nb25=count(exessr) if exessr>=25
by dep: egen c25=max(nb25)
replace c25=0 if c25==.
by dep: egen nb50=count(exessr) if exessr>=50
by dep: egen c50=max(nb50)
replace c50=0 if c50==.
by dep: egen nb75=count(exessr) if exessr>=75
by dep: egen c75=max(nb75)
replace c75=0 if c75==.
by dep: egen nb100=count(exessr) if exessr>=100
by dep: egen c100=max(nb100)
replace c100=0 if c100==.



/////
egen c10_F=count(exessr) if exessr>=10
egen n10_F=max(c10_F)
drop c10_F
rename n10_F c10_F
egen c25_F=count(exessr) if exessr>=25
egen n25_F=max(c25_F)
drop c25_F
rename n25_F c25_F
egen c50_F=count(exessr) if exessr>=50
egen n50_F=max(c50_F)
drop c50_F
rename n50_F c50_F
egen c100_F=count(exessr) if exessr>=100
egen n100_F=max(c100_F)
drop c100_F
rename n100_F c100_F


***Proportion de dépassement / au nombre de médecin actifs sur le territoire
by dep: gen r10=(c10/NB)*100
by dep: gen r25=(c25/NB)*100
by dep: gen r50=(c50/NB)*100
by dep: gen r100=(c100/NB)*100



gen r10_F=(c10_F/NB_F)
gen r25_F=(c25_F/NB_F)
gen r50_F=(c50_F/NB_F)
gen r100_F=(c100_F/NB_F)

****dépassement moyen par département (uniquement les acteurs  faisant du dépassement)
egen PF=mean(prixmoyen)
egen PFS2=mean(prixmoyen) if convention==2 | convention==1 & optioncontratdaccèsauxsoins=="true" |convention ==3
egen PFFS2=mean(PFS2)
drop PFS2
rename PFFS2 PFS2
///dépassement moyen France

by dep: egen PrixMoyen =mean(prixmoyen)
by dep: egen PrixMoyenS2 = mean(prixmoyen) if convention==2 | convention==1 & optioncontratdaccèsauxsoins=="true" |convention ==3
///Dépassement moyen par département

by dep: egen Prix=mean(PrixMoyen)
by dep: gen depmoyen=[(PrixMoyen-30)/30]*100
drop PrixMoyen
rename Prix PrixMoyen
gen depmoyen_F=[(PF-30)/30]*100

gen double ty=round(depmoyen,.001)
drop depmoyen
rename ty depmoyen

by dep: egen PrixS2=mean(PrixMoyenS2)
by dep: gen depmoyenS2=[(PrixMoyenS2-30)/30]*100
by dep: egen dpS2=mean(depmoyenS2)
drop PrixMoyenS2
rename PrixS2 PrixMoyenS2
drop depmoyenS2
rename dpS2 depmoyenS2
gen depmoyen_FS2=[(PFS2-30)/30]*100

gen double ty=round(depmoyenS2,.001)
drop depmoyenS2
rename ty depmoyenS2




gsort dep -depmoyen
duplicates drop dep, force
replace depmoyen=0 if depmoyen==.


drop gender nom prénom naturedexercice convention optioncontratdaccèsauxsoins codeccamdelacte ps_id montantgénéralementconstaté borneinférieuredumontant bornesupérieuredumontant date_source_id adresse_id matchcp codeinsee b unique un cc ccc weight mp prixmoyen exessr nb10 c10 nb25 c25 nb50 c50 nb75 c75 nb100 c100 exess



expand 2 if dep==75, gen(dup)
replace dep=0 if dup==1
replace NB_total=NB_Ftotal if dup==1
replace NB2_total=NB2_Ftotal if dup==1
replace NB=NB_F if dup==1
replace NB2=NB2_F if dup==1
replace ShareS2 = ShareS2_F if dup==1
replace r10=r10_F if dup==1
replace r25=r25_F if dup==1
replace r50=r50_F if dup==1
replace r100=r100_F if dup==1
replace PrixMoyen = PF if dup==1
replace PrixMoyenS2 = PFS2 if dup==1
replace depmoyen = depmoyen_F if dup==1
replace depmoyenS2 = depmoyen_FS2 if dup==1

drop NB_Ftotal  NB2_Ftotal NB_F NB2_F ShareS2_F r10_F r25_F r50_F r100_F PF PFS2 depmoyen_F depmoyen_FS2 c10_F c25_F c50_F c100_F dup c

