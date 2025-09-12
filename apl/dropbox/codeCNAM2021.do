cd "C:\Users\benjamin.montmartin\Desktop\CNAM\CNAM 2021"
import delimited "C:\Users\benjamin.montmartin\Desktop\CNAM\CNAM 2021\A202101.csv"
save "C:\Users\benjamin.montmartin\Desktop\CNAM\CNAM 2021\CNAM20211.dta"

clear all
cd "C:\Users\benjamin.montmartin\Desktop\CNAM\CNAM 2021"
import delimited "C:\Users\benjamin.montmartin\Desktop\CNAM\CNAM 2021\A202102.csv"
save "C:\Users\benjamin.montmartin\Desktop\CNAM\CNAM 2021\CNAM20212.dta"

clear all
cd "C:\Users\benjamin.montmartin\Desktop\CNAM\CNAM 2021"
import delimited "C:\Users\benjamin.montmartin\Desktop\CNAM\CNAM 2021\A202103.csv"
save "C:\Users\benjamin.montmartin\Desktop\CNAM\CNAM 2021\CNAM20213.dta"


clear all
cd "C:\Users\benjamin.montmartin\Desktop\CNAM\CNAM 2021"
import delimited "C:\Users\benjamin.montmartin\Desktop\CNAM\CNAM 2021\A202104.csv"
save "C:\Users\benjamin.montmartin\Desktop\CNAM\CNAM 2021\CNAM20214.dta"

clear all
cd "C:\Users\benjamin.montmartin\Desktop\CNAM\CNAM 2021"
import delimited "C:\Users\benjamin.montmartin\Desktop\CNAM\CNAM 2021\A202105.csv"
save "C:\Users\benjamin.montmartin\Desktop\CNAM\CNAM 2021\CNAM20215.dta"

clear all
cd "C:\Users\benjamin.montmartin\Desktop\CNAM\CNAM 2021"
import delimited "C:\Users\benjamin.montmartin\Desktop\CNAM\CNAM 2021\A202106.csv"
save "C:\Users\benjamin.montmartin\Desktop\CNAM\CNAM 2021\CNAM20216.dta"

clear all
cd "C:\Users\benjamin.montmartin\Desktop\CNAM\CNAM 2021"
import delimited "C:\Users\benjamin.montmartin\Desktop\CNAM\CNAM 2021\A202107.csv"
save "C:\Users\benjamin.montmartin\Desktop\CNAM\CNAM 2021\CNAM20217.dta"

clear all
cd "C:\Users\benjamin.montmartin\Desktop\CNAM\CNAM 2021"
import delimited "C:\Users\benjamin.montmartin\Desktop\CNAM\CNAM 2021\A202108.csv"
save "C:\Users\benjamin.montmartin\Desktop\CNAM\CNAM 2021\CNAM20218.dta"


clear all
cd "C:\Users\benjamin.montmartin\Desktop\CNAM\CNAM 2021"
import delimited "C:\Users\benjamin.montmartin\Desktop\CNAM\CNAM 2021\A202109.csv"
save "C:\Users\benjamin.montmartin\Desktop\CNAM\CNAM 2021\CNAM20219.dta"



clear all
cd "C:\Users\benjamin.montmartin\Desktop\CNAM\CNAM 2021"
import delimited "C:\Users\benjamin.montmartin\Desktop\CNAM\CNAM 2021\A202110.csv"
save "C:\Users\benjamin.montmartin\Desktop\CNAM\CNAM 2021\CNAM202110.dta"

clear all
cd "C:\Users\benjamin.montmartin\Desktop\CNAM\CNAM 2021"
import delimited "C:\Users\benjamin.montmartin\Desktop\CNAM\CNAM 2021\A202111.csv"
save "C:\Users\benjamin.montmartin\Desktop\CNAM\CNAM 2021\CNAM202111.dta"


clear all
cd "C:\Users\benjamin.montmartin\Desktop\CNAM\CNAM 2021"
import delimited "C:\Users\benjamin.montmartin\Desktop\CNAM\CNAM 2021\A202112.csv"
save "C:\Users\benjamin.montmartin\Desktop\CNAM\CNAM 2021\CNAM202112.dta"


use CNAM20211.dta, clear
forvalues i = 2/12 {
	append using CNAM2021`i'
}
save "C:\Users\benjamin.montmartin\Desktop\CNAM\CNAM 2021\CNAM2021.dta"



use CNAM2021.dta, replace
keep pse_spe_snds age_ben_snds ben_qlt_cod psp_spe_snds flt_act_qte flt_act_nbr prs_rem_typ prs_nat cpl_cod
keep if pse_spe_snds==1
save "C:\Users\benjamin.montmartin\Desktop\CNAM\CNAM 2021\CNAMgénéraliste.dta", replace

use CNAM2021.dta, replace
keep pse_spe_snds age_ben_snds ben_qlt_cod psp_spe_snds flt_act_qte flt_act_nbr prs_rem_typ prs_nat cpl_cod
keep if pse_spe_snds==15
save "C:\Users\benjamin.montmartin\Desktop\CNAM\CNAM 2021\CNAMophtal.dta", replace

use CNAM2021.dta, replace
keep pse_spe_snds age_ben_snds ben_qlt_cod psp_spe_snds flt_act_qte flt_act_nbr prs_rem_typ prs_nat cpl_cod
keep if pse_spe_snds==7
save "C:\Users\benjamin.montmartin\Desktop\CNAM\CNAM 2021\CNAMgyne.dta", replace


use CNAM2021.dta, replace
keep pse_spe_snds age_ben_snds ben_qlt_cod psp_spe_snds flt_act_qte flt_act_nbr prs_rem_typ prs_nat cpl_cod
keep if pse_spe_snds==12
save "C:\Users\benjamin.montmartin\Desktop\CNAM\CNAM 2021\CNAMpedia.dta", replace



tab ben_qlt_cod
tab age_ben_snds
drop if age_ben_snds==99


use CNAMgénéraliste.dta, replace
tab ben_qlt_cod
keep if prs_rem_typ==0
drop if age_ben_snds==99
keep if cpl_cod==0
keep if prs_nat==1111 | prs_nat==1112 | prs_nat==1113 | prs_nat==1114 | prs_nat==1115  | prs_nat==1117 | prs_nat==1118 | prs_nat==1140| prs_nat==1168 | prs_nat==1098 |prs_nat==1099 |prs_nat==1104 |prs_nat==1105 |prs_nat==1109 |prs_nat==1110|prs_nat==1107| prs_nat==1096 | prs_nat==1164| prs_nat==1157
sort age_ben_snds
by age_ben_snds: egen count1=sum(flt_act_qte)
by age_ben_snds: egen count2=sum(flt_act_nbr)
tabulate age_ben_snds, summarize(count1)
tabulate age_ben_snds, summarize(count2)





use CNAMophtal.dta, replace
tab ben_qlt_cod
keep if prs_rem_typ==0
drop if age_ben_snds==99
keep if cpl_cod==0
keep if prs_nat==1111 | prs_nat==1112 | prs_nat==1113 | prs_nat==1114 | prs_nat==1115  | prs_nat==1117 | prs_nat==1118 | prs_nat==1140| prs_nat==1168 | prs_nat==1098 |prs_nat==1099 |prs_nat==1104 |prs_nat==1105 |prs_nat==1109 |prs_nat==1110|prs_nat==1107| prs_nat==1096 | prs_nat==1164| prs_nat==1157 
sort age_ben_snds
by age_ben_snds: egen count1=sum(flt_act_qte)
by age_ben_snds: egen count2=sum(flt_act_nbr)
tabulate age_ben_snds, summarize(count1)
tabulate age_ben_snds, summarize(count2)




use CNAMgyne.dta, replace
tab ben_qlt_cod
keep if prs_rem_typ==0
drop if age_ben_snds==99
keep if cpl_cod==0
keep if prs_nat==1111 | prs_nat==1112 | prs_nat==1113 | prs_nat==1114 | prs_nat==1115  | prs_nat==1117 | prs_nat==1118 | prs_nat==1140| prs_nat==1168 | prs_nat==1098 |prs_nat==1099 |prs_nat==1104 |prs_nat==1105 |prs_nat==1109 |prs_nat==1110|prs_nat==1107| prs_nat==1096 | prs_nat==1164| prs_nat==1157
sort age_ben_snds
by age_ben_snds: egen count1=sum(flt_act_qte)
by age_ben_snds: egen count2=sum(flt_act_nbr)
tabulate age_ben_snds, summarize(count1)
tabulate age_ben_snds, summarize(count2)



use CNAMpedia.dta, replace
tab ben_qlt_cod
keep if prs_rem_typ==0
drop if age_ben_snds==99
keep if cpl_cod==0
//keep if prs_nat==1111 | prs_nat==1112 | prs_nat==1113 | prs_nat==1114 | prs_nat==1115 | prs_nat==1116 | prs_nat==1117 | prs_nat==1118 | prs_nat==1120 | prs_nat==1125 | prs_nat==1126 | prs_nat==1127 | prs_nat==1129 | prs_nat==1131 | prs_nat==1132 | prs_nat==1133 | prs_nat==1134 | prs_nat==1135 | prs_nat==1136 | prs_nat==1140 | prs_nat==1141 | prs_nat==1152 | prs_nat==1153 | prs_nat==1154 | prs_nat==1914 | prs_nat==1918 | prs_nat==1931 | prs_nat==1932 | prs_nat==1933 | prs_nat==1934 | prs_nat==1935 | prs_nat==1941 
keep if prs_nat==1111 | prs_nat==1112 | prs_nat==1113 | prs_nat==1114 | prs_nat==1115  | prs_nat==1117 | prs_nat==1118 | prs_nat==1140| prs_nat==1168 | prs_nat==1098 |prs_nat==1099 |prs_nat==1104 |prs_nat==1105 |prs_nat==1109 |prs_nat==1110|prs_nat==1107| prs_nat==1096 | prs_nat==1164| prs_nat==1157
sort age_ben_snds
by age_ben_snds: egen count1=sum(flt_act_qte)
by age_ben_snds: egen count2=sum(flt_act_nbr)
tabulate age_ben_snds, summarize(count1)
tabulate age_ben_snds, summarize(count2)






