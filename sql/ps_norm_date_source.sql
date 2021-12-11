select count(*) from ps, ps_cabinet_date_source, cabinet, adresse_raw, adresse_norm
where ps_cabinet_date_source.date_source_id = 0
and ps_cabinet_date_source.ps_id = ps.id
and ps_cabinet_date_source.cabinet_id = cabinet.id
and adresse_raw.id = cabinet.adresse_raw_id
and adresse_norm.id = adresse_raw.adresse_norm_id
