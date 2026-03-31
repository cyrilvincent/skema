-- lastest study keys
select max(s.date) date, s.key from apl.apl_study s
group by s.specialite_id, s.key
order by max(s.date)

-- export apl_study
SELECT s.* FROM apl.apl_study s
JOIN (
    SELECT MAX(s2.date) AS date, s2.key
    FROM apl.apl_study s2
    GROUP BY s2.specialite_id, s2.key
) latest ON s.key = latest.key
ORDER BY s.specialite_id

--export apl
SELECT a.* FROM apl.apl a
JOIN (
    SELECT MAX(s.date) AS date, s.key
    FROM apl.apl_study s
    GROUP BY s.specialite_id, s.key
) latest ON a.study_key = latest.key
ORDER BY a.date

-- Backup
-- Etape 1
-- Créer une table temporaire pour les exports
-- CREATE TABLE apl.apl_study_export AS
--SELECT s.*
--FROM apl.apl_study s
--JOIN (
--    SELECT MAX(date) AS date, key
--    FROM apl.apl_study
--    GROUP BY key
--) latest ON s.key = latest.key AND s.date = latest.date;

-- Etape 2
--Backup n tables
--pg_dump -U monuser -d mabase \
--  -t apl.apl_study_export \
--  -t apl.apl_specialite \
--  -t apl.apl_autre_table \
--  > backup_multi.sql

-- Etape 3 renommer les tables export
-- wsl sed 's/apl_study_export/apl_study/g' backup_export.sql > backup_temp.sql
-- wsl sed 's/apl_export/apl/g' backup_temp.sql > backup_final.sql


