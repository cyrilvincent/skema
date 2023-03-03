select count(*) from ps, ps_cabinet_date_source, cabinet, adresse_raw, adresse_norm, tarif, tarif_date_source
where ps_cabinet_date_source.date_source_id = 2101
and ps_cabinet_date_source.ps_id = ps.id
and ps_cabinet_date_source.cabinet_id = cabinet.id
and adresse_raw.id = cabinet.adresse_raw_id
and adresse_norm.id = adresse_raw.adresse_norm_id
and tarif.ps_id = ps.id
and tarif_date_source.tarif_id = tarif.id
and tarif_date_source.date_source_id = ps_cabinet_date_source.date_source_id

3516472

select count(*) from ps
full join ps_cabinet_date_source as pcds on pcds.ps_id = ps.id
full join cabinet as c on pcds.cabinet_id = c.id
full join adresse_raw as raw on c.adresse_raw_id = raw.id
full join adresse_norm as norm on raw.adresse_norm_id = norm.id
full join tarif on tarif.ps_id = ps.id
full join tarif_date_source as tds on tds.tarif_id = tarif.id
where tds.date_source_id = pcds.date_source_id
and pcds.date_source_id = 2101

idem



