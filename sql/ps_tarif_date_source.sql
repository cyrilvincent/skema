select count(*) from ps, tarif, tarif_date_source
where tarif.ps_id = ps.id
and tarif_date_source.tarif_id = tarif.id
and tarif_date_source.date_source_id = 2101

2332025

select count(*) from ps, tarif
where tarif.ps_id = ps.id

4137810

select count(*) from ps
join tarif on tarif.ps_id = ps.id

idem

select count(*) from ps
full join tarif on tarif.ps_id = ps.id

4137829

select count(*) from ps
full join tarif on tarif.ps_id = ps.id
full join tarif_date_source tds on tds.tarif_id = tarif.id
where tds.date_source_id = 2101

2332025