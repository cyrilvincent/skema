select * from etablissement e
full join sae.bio as bio on bio.nofinesset = e.nofinesset
full join etablissement_date_source as eds on eds.etablissement_id = e.id
where  bio.an = 2019
and eds.date_source_id = 1912

387

select * from etablissement_adresse_codecc e
full join sae.bio as bio on bio.nofinesset = e.nofinesset
where e.date_source_id = 1912
and  bio.an = 2019

387