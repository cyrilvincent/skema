select count(*) from etablissement, etablissement_date_source
where etablissement_date_source.date_source_id = 412
and etablissement_date_source.etablissement_id = etablissement.id