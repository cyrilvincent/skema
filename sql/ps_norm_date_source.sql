select count(*) from ps, ps_cabinet_date_source, cabinet, adresse_raw, adresse_norm
where ps_cabinet_date_source.date_source_id = 2101
and ps_cabinet_date_source.ps_id = ps.id
and ps_cabinet_date_source.cabinet_id = cabinet.id
and adresse_raw.id = cabinet.adresse_raw_id
and adresse_norm.id = adresse_raw.adresse_norm_id

160104

select count(*) from ps
full join ps_cabinet_date_source as pcds on pcds.ps_id = ps.id
full join cabinet as c on pcds.cabinet_id = c.id
full join adresse_raw as raw on c.adresse_raw_id = raw.id
full join adresse_norm as norm on raw.adresse_norm_id = norm.id
where pcds.date_source_id = 2101




