create or replace view ps_tarif as
select ps.*, tarif.id as tarif_id, profession_id, mode_exercice_id, nature_id, convention_id, option_contrat, vitale, code, cabinet_id, famille_acte_id, montant, borne_inf, borne_sup, montant_2, borne_inf_2, borne_sup_2, montant_imagerie, borne_inf_imagerie, borne_sup_imagerie, montant_anesthesie, borne_inf_anesthesie, borne_sup_anesthesie, montant_cec, borne_inf_cec, borne_sup_cec, date_source_id
from ps
full join tarif on tarif.ps_id = ps.id
full join tarif_date_source tds on tds.tarif_id = tarif.id

select * from ps_tarif where date_source_id = 2101

create or replace view ps_adresse as
select ps.*, pcds.id as pcds_id, pcds.date_source_id as date_source_id, c.id as cabinet_id, raw.id as raw_id, norm.id as norm_id, norm.dept_id as dept_id, norm.numero as numero, rue1, rue2, norm.cp as cp, norm.commune as commune, norm.lon as lon, norm.lat as lat, iris, ban_id, code_insee
from ps
full join ps_cabinet_date_source as pcds on pcds.ps_id = ps.id
full join cabinet as c on pcds.cabinet_id = c.id
full join adresse_raw as raw on c.adresse_raw_id = raw.id
full join adresse_norm as norm on raw.adresse_norm_id = norm.id
full join ban on norm.ban_id = ban.id

select * from ps_adresse where date_source_id = 2101

--Ancienne vue en erreur
--create or replace view ps_tarif_adresse as
--select ps.*, tarif.id as tarif_id, profession_id, mode_exercice_id, nature_id, convention_id, option_contrat, vitale, code, famille_acte_id, montant, borne_inf, borne_sup, montant_2, borne_inf_2, borne_sup_2, montant_imagerie, borne_inf_imagerie, borne_sup_imagerie, montant_anesthesie, borne_inf_anesthesie, borne_sup_anesthesie, montant_cec, borne_inf_cec, borne_sup_cec,
--    pcds.id as pcds_id, pcds.date_source_id as date_source_id, c.id as cabinet_id, raw.id as raw_id, norm.id as norm_id, norm.dept_id as dept_id, norm.numero as numero, rue1, rue2, norm.cp as cp, norm.commune as commune, norm.lon as lon, norm.lat as lat, iris, ban_id, code_insee
--from ps
--full join ps_cabinet_date_source as pcds on pcds.ps_id = ps.id
--full join cabinet as c on pcds.cabinet_id = c.id
--full join adresse_raw as raw on c.adresse_raw_id = raw.id
--full join adresse_norm as norm on raw.adresse_norm_id = norm.id
--full join tarif on tarif.ps_id = ps.id
--full join tarif_date_source as tds on tds.tarif_id = tarif.id
--full join ban on norm.ban_id = ban.id
--where tds.date_source_id = pcds.date_source_id
--and tarif.cabinet_id = c.id
--
--select * from ps_tarif_adresse where date_source_id = 2101

drop view ps_tarif_adresse;
create or replace view ps_tarif_adresse as
select ps.*, tarif.id as tarif_id, profession_id, mode_exercice_id, nature_id, convention_id, option_contrat, vitale, code, famille_acte_id, montant, borne_inf, borne_sup, montant_2, borne_inf_2, borne_sup_2, montant_imagerie, borne_inf_imagerie, borne_sup_imagerie, montant_anesthesie, borne_inf_anesthesie, borne_sup_anesthesie, montant_cec, borne_inf_cec, borne_sup_cec,
    tds.date_source_id as date_source_id, c.id as cabinet_id, raw.id as raw_id, norm.id as norm_id, norm.dept_id as dept_id, norm.numero as numero, rue1, rue2, norm.cp as cp, norm.commune as commune, norm.lon as lon, norm.lat as lat, iris, ban_id, code_insee
from ps
full join tarif on tarif.ps_id = ps.id
full join tarif_date_source as tds on tds.tarif_id = tarif.id
full join cabinet as c on tarif.cabinet_id = c.id
full join adresse_raw as raw on c.adresse_raw_id = raw.id
full join adresse_norm as norm on raw.adresse_norm_id = norm.id
full join ban on norm.ban_id = ban.id

select * from ps_tarif_adresse where date_source_id = 2101

create or replace view etablissement_view as
select etablissement.*, eds.date_source_id as date_source_id
from etablissement
full join etablissement_date_source as eds on eds.etablissement_id = etablissement.id

select * from etablissement_view where date_source_id = 2012

create or replace view etablissement_adresse as
select etablissement.*, eds.date_source_id as date_source_id, raw.id as raw_id, norm.id as norm_id, norm.dept_id as dept_id, norm.numero as numero, rue1, rue2, norm.cp as cp, norm.commune as commune, norm.lon as lon, norm.lat as lat, iris, ban_id, code_insee
from etablissement
full join etablissement_date_source as eds on eds.etablissement_id = etablissement.id
full join adresse_raw as raw on raw.id = etablissement.adresse_raw_id
full join adresse_norm as norm on norm.id = raw.adresse_norm_id
full join ban on norm.ban_id = ban.id

select * from etablissement_adresse where date_source_id = 2012

create or replace view etablissement_codecc as
select e.*, b20.*, "P14_POP", "P09_POP", b17."SUPERF" as B17_SUPERF, "NAIS0914", "DECE0914", "P14_MEN", "NAISD16", "DECESD16", "P14_LOG", "P14_RP", "P14_RSECOCC", "P14_LOGVAC", "P14_RP_PROP", "NBMENFISC14", "PIMP14", "MED14", "TP6014", "P14_EMPLT", "P14_EMPLT_SAL", "P09_EMPLT", "P14_POP1564", "P14_CHOM1564", "P14_ACT1564", b17.is_com as b17_is_com
from etablissement e
full join basecc20 as b20 on b20."CODGEO" = e.cog
full join basecc17 as b17 on b17."CODGEO" = e.cog

create or replace view etablissement_adresse_codecc as
select etablissement.*, eds.date_source_id as date_source_id, raw.id as raw_id, norm.id as norm_id, norm.dept_id as dept_id, norm.numero as numero, rue1, rue2, norm.cp as cp, norm.commune as commune, norm.lon as lon, norm.lat as lat, iris, ban_id, code_insee,
    b20.*, "P14_POP", "P09_POP", b17."SUPERF" as B17_SUPERF, "NAIS0914", "DECE0914", "P14_MEN", "NAISD16", "DECESD16", "P14_LOG", "P14_RP", "P14_RSECOCC", "P14_LOGVAC", "P14_RP_PROP", "NBMENFISC14", "PIMP14", "MED14", "TP6014", "P14_EMPLT", "P14_EMPLT_SAL", "P09_EMPLT", "P14_POP1564", "P14_CHOM1564", "P14_ACT1564", b17.is_com as b17_is_com
from etablissement
full join etablissement_date_source as eds on eds.etablissement_id = etablissement.id
full join adresse_raw as raw on raw.id = etablissement.adresse_raw_id
full join adresse_norm as norm on norm.id = raw.adresse_norm_id
full join ban on norm.ban_id = ban.id
full join basecc20 as b20 on b20."CODGEO" = etablissement.cog
full join basecc17 as b17 on b17."CODGEO" = etablissement.cog

-- lent
drop view ps_tarif_adresse_bcc;
create or replace view ps_tarif_adresse_bcc as
select ps.*, tarif.id as tarif_id, profession_id, mode_exercice_id, nature_id, convention_id, option_contrat, vitale, code, famille_acte_id, montant, borne_inf, borne_sup, montant_2, borne_inf_2, borne_sup_2, montant_imagerie, borne_inf_imagerie, borne_sup_imagerie, montant_anesthesie, borne_inf_anesthesie, borne_sup_anesthesie, montant_cec, borne_inf_cec, borne_sup_cec,
    tds.date_source_id as date_source_id, c.id as cabinet_id, raw.id as raw_id, norm.id as norm_id, norm.dept_id as dept_id, norm.numero as numero, rue1, rue2, norm.cp as cp, norm.commune as commune, norm.lon as lon, norm.lat as lat, iris, ban_id, code_insee,
    b20.*, "P14_POP", "P09_POP", b17."SUPERF" as B17_SUPERF, "NAIS0914", "DECE0914", "P14_MEN", "NAISD16", "DECESD16", "P14_LOG", "P14_RP", "P14_RSECOCC", "P14_LOGVAC", "P14_RP_PROP", "NBMENFISC14", "PIMP14", "MED14", "TP6014", "P14_EMPLT", "P14_EMPLT_SAL", "P09_EMPLT", "P14_POP1564", "P14_CHOM1564", "P14_ACT1564", b17.is_com as b17_is_com
from ps
full join tarif on tarif.ps_id = ps.id
full join tarif_date_source as tds on tds.tarif_id = tarif.id
full join cabinet as c on tarif.cabinet_id = c.id
full join adresse_raw as raw on c.adresse_raw_id = raw.id
full join adresse_norm as norm on raw.adresse_norm_id = norm.id
full join ban on norm.ban_id = ban.id
full join basecc20 as b20 on b20."CODGEO" = ban.code_insee
full join basecc17 as b17 on b17."CODGEO" = ban.code_insee

select * from ps_tarif_adresse_bcc where date_source_id = 2101








