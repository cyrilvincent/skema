select count(*) from etablissement, etablissement_date_source, adresse_raw, adresse_norm
where etablissement_date_source.date_source_id = 2012
and etablissement_date_source.etablissement_id = etablissement.id
and adresse_raw.id = etablissement.adresse_raw_id
and adresse_norm.id = adresse_raw.adresse_norm_id

93171

select count(*) from etablissement
full join etablissement_date_source as eds on eds.etablissement_id = etablissement.id
full join adresse_raw as raw on raw.id = etablissement.adresse_raw_id
full join adresse_norm as norm on norm.id = raw.adresse_norm_id
where eds.date_source_id = 2012

idem