select '1' as id, count(distinct(ps.key)) from ps
left join tarif t on t.ps_id = ps.id
left join tarif_date_source tds on tds.tarif_id = t.id
where t.profession_id = 60
union
select '2' as id, count(distinct(ps.key)) from ps
left join tarif t on t.ps_id = ps.id
left join tarif_date_source tds on tds.tarif_id = t.id
where t.profession_id = 60
and tds.date_source_id < 2000
union
select '3' as id, count(distinct(ps.key)) from ps
left join tarif t on t.ps_id = ps.id
left join tarif_date_source tds on tds.tarif_id = t.id
where t.profession_id = 60
and tds.date_source_id > 2000
union
select '4' as id, count(distinct(ps.key)) from ps
left join tarif t on t.ps_id = ps.id
left join tarif_date_source tds on tds.tarif_id = t.id
where t.profession_id = 60
and tds.date_source_id > 2200
and tds.date_source_id < 2299
union
select '5' as id, count(distinct(ps.key)) from ps
left join tarif t on t.ps_id = ps.id
left join tarif_date_source tds on tds.tarif_id = t.id
where t.profession_id = 60
and tds.date_source_id > 2200
order by id