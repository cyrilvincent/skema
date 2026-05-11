SELECT pg_size_pretty(pg_total_relation_size('apl.apl')) AS taille_totale -- 116Go

-- ok
DROP TABLE IF EXISTS apl.apl_study_export;
create table apl.apl_study_export as
	select s.* from apl.apl_study s
	join (
		select max(s2.date) date_latest from apl.apl_study s2
		where s2.source='PA'
		group by s2.year, s2.specialite_id, s2.time, s2.time_type, s2.exp, s2.source
		) latest on s.date = latest.date_latest
	order by s.year, s.specialite_id, s.time, s.time_type, s.exp

-- ok
DROP TABLE IF EXISTS apl.apl_s_study_export;
create table apl.apl_s_study_export as
	select s.* from apl.apl_s_study s
	join (
		select max(s2.date) date_latest from apl.apl_s_study s2
		where s2.source='PA'
		group by s2.year, s2.specialite_id, s2.time, s2.time_type, s2.exp, s2.source
		) latest on s.date = latest.date_latest
	order by s.year, s.specialite_id, s.time, s.time_type, s.exp

-- ok
DROP TABLE IF EXISTS apl.apl_export;
create table apl.apl_export as
    select a.* from apl.apl a
    join apl.apl_study_export e on a.study_key=e.key
    order by a.study_key

-- ok
DROP TABLE IF EXISTS apl.apl_s_export;
create table apl.apl_s_export as
    select a.* from apl.apl_s a
    join apl.apl_s_study_export e on a.study_key=e.key
    order by a.study_key

-- ok 78
DROP TABLE IF EXISTS sae.dist_study_export;
create table sae.dist_study_export as
    select s.* from sae.dist_study s
	join (
		select max(s2.date) date_latest from sae.dist_study s2
		group by s2.year, s2.bor, s2.time, s2.time_type
		) latest on s.date = latest.date_latest
	order by s.year, s.bor, s.time, s.time_type

-- ok 78*48000
DROP TABLE IF EXISTS sae.dist_export;
create table sae.dist_export as
    select a.* from sae.dist a
    join sae.dist_study_export e on a.study_key=e.key
    order by a.study_key

-- ok 151k
DROP TABLE IF EXISTS adresse_raw_export;
create table adresse_raw_export as
    select ar.* from adresse_raw ar join etablissement e on e.adresse_raw_id = ar.id;

--
DROP TABLE IF EXISTS adresse_norm_export;
create table adresse_norm_export as
    select an.* from adresse_norm an
    join adresse_raw ar on ar.adresse_norm_id = an.id
    join etablissement e on e.adresse_raw_id = ar.id;

