select count(*) from ps, tarif, tarif_date_source
where tarif.ps_id = ps.id
and tarif_date_source.tarif_id = tarif.id
and tarif_date_source.date_source_id = 0