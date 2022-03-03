select count(*) from etablissement, etablissement_date_source, adresse_raw, adresse_norm
where etablissement_date_source.date_source_id = 2012
and etablissement_date_source.etablissement_id = etablissement.id
and adresse_raw.id = etablissement.adresse_raw_id
and adresse_norm.id = adresse_raw.adresse_norm_id