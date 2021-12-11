set session vars.datesource = 0;
select count(*) from ps, ps_cabinet_date_source, cabinet, adresse_raw, adresse_norm, tarif, tarif_date_source
where ps_cabinet_date_source.date_source_id = current_setting('vars.datesource')::int
and ps_cabinet_date_source.ps_id = ps.id
and ps_cabinet_date_source.cabinet_id = cabinet.id
and adresse_raw.id = cabinet.adresse_raw_id
and adresse_norm.id = adresse_raw.adresse_norm_id
and tarif.ps_id = ps.id
and tarif_date_source.tarif_id = tarif.id
and tarif_date_source.date_source_id = current_setting('vars.datesource')::int