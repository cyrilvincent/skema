SELECT pg_size_pretty(pg_total_relation_size('apl.apl')) AS taille_totale -- 116Go

-- ok 3320 normalement 2772 mais y"a de vieilles studies
DROP TABLE IF EXISTS apl.apl_study_export;
create table apl.apl_study_export as
	select s.* from apl.apl_study s
	join (
		select max(s2.date) date_latest from apl.apl_study s2
		where s2.source='PA'
		group by s2.year, s2.specialite_id, s2.time, s2.time_type, s2.exp, s2.source
		) latest on s.date = latest.date_latest
	order by s.year, s.specialite_id, s.time, s.time_type, s.exp

CREATE UNIQUE INDEX apl_apl_study_export_key ON apl.apl_study_export (key);
create index ix_apl_apl_study_export_year_specialite_id on apl.apl_study_export (year, specialite_id);

-- ok 3416 normalement 2772 mais y'a de vieilles studies
DROP TABLE IF EXISTS apl.apl_s_study_export;
create table apl.apl_s_study_export as
	select s.* from apl.apl_s_study s
	join (
		select max(s2.date) date_latest from apl.apl_s_study s2
		where s2.source='PA'
		group by s2.year, s2.specialite_id, s2.time, s2.time_type, s2.exp, s2.source
		) latest on s.date = latest.date_latest
	order by s.year, s.specialite_id, s.time, s.time_type, s.exp

CREATE UNIQUE INDEX apl_apl_s_study_export_key ON apl.apl_s_study_export (key);
create index ix_apl_apl_s_study_export_year_specialite_id on apl.apl_s_study_export (year, specialite_id);

-- ok 161151942 1h09
DROP TABLE IF EXISTS apl.apl_export;
create table apl.apl_export as
    select a.* from apl.apl a
    join apl.apl_study_export e on a.study_key=e.key
    order by a.study_key

CREATE UNIQUE INDEX apl_apl_export_iris_year_study_key_key ON apl.apl_export (iris, year, study_key); -- 12 min
create index ix_apl_apl_export_study_key on apl.apl_export (study_key); -- 2.5 min
create index ix_apl_apl_export_code_commune on apl.apl_export (code_commune); -- 7 min

-- ok 165911704 1h09
DROP TABLE IF EXISTS apl.apl_s_export;
create table apl.apl_s_export as
    select a.* from apl.apl_s a
    join apl.apl_s_study_export e on a.study_key=e.key
    order by a.study_key

CREATE UNIQUE INDEX apl_apl_s_export_iris_year_study_key_key ON apl.apl_s_export (iris, year, study_key);
create index ix_apl_apl_s_export_study_key on apl.apl_s_export (study_key);
create index ix_apl_apl_s_export_code_commune on apl.apl_export (code_commune);


-- ok 78
DROP TABLE IF EXISTS sae.dist_study_export;
create table sae.dist_study_export as
    select s.* from sae.dist_study s
	join (
		select max(s2.date) date_latest from sae.dist_study s2
		group by s2.year, s2.bor, s2.time, s2.time_type
		) latest on s.date = latest.date_latest
	order by s.year, s.bor, s.time, s.time_type

CREATE UNIQUE INDEX sae_dist_study_export_key ON sae.dist_study_export (key);
create index ix_sae_dist_study_export_year_bor on sae.dist_study_export (year, bor);

-- ok 78*48000
DROP TABLE IF EXISTS sae.dist_export;
create table sae.dist_export as
    select a.* from sae.dist a
    join sae.dist_study_export e on a.study_key=e.key
    order by a.study_key

create index ix_sae_dist_export_key on sae.dist_export (study_key);
CREATE UNIQUE INDEX sae_dist_export_iris_year_study_key_key ON sae.dist_export (iris, year, study_key);

-- ok 127371
DROP TABLE IF EXISTS adresse_norm_export;
create table adresse_norm_export as
    select distinct(an.*) from adresse_norm an
    join adresse_raw ar on ar.adresse_norm_id = an.id
    join etablissement e on e.adresse_raw_id = ar.id;

ALTER TABLE adresse_norm_export ADD PRIMARY KEY (id);
ALTER TABLE adresse_norm_export ADD CONSTRAINT adresse_norm_dept_id_fk FOREIGN KEY (dept_id) REFERENCES dept(id);
CREATE UNIQUE INDEX adresse_norm_export_numero_rue1_rue2_cp_commune_key ON adresse_norm_export (numero, rue1, rue2, cp, commune);

-- ok 129039k
DROP TABLE IF EXISTS adresse_raw_export;
create table adresse_raw_export as
    select distinct(ar.*) from adresse_raw ar join etablissement e on e.adresse_raw_id = ar.id;

ALTER TABLE adresse_raw_export ADD PRIMARY KEY (id);
CREATE UNIQUE INDEX adresse_raw_export_adresse2_adresse3_adresse4_cp_commune_key ON adresse_raw_export (adresse2, adresse3, adresse4, cp, commune);
ALTER TABLE adresse_raw_export ADD CONSTRAINT adresse_raw_adresse_norm_id_fk FOREIGN KEY (adresse_norm_id) REFERENCES adresse_norm_export(id);
ALTER TABLE adresse_raw_export ADD CONSTRAINT adresse_raw_dept_id_fk FOREIGN KEY (dept_id) REFERENCES dept(id);




