select * from etablissement e, sae.bio b
where e.nofinesset = b.nofinesset
and b.an = 2019


--select count(*) from etablissement e, sae.bio b, etablissement_date_source ds
--where e.nofinesset = b.nofinesset
--and ds.etablissement_id = e.id
--and b.an = 2019
--and ds.date_source_id = 1912