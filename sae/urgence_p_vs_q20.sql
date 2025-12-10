select d.fi, d.passu, p.etpsal, p.efflib, p2.etpsal, p2.efflib --, e.id etab_id, e.rs, an.dept_id, an.id adresse_norm_id, an.lon, an.lat, i.id iris
from sae.urgence_detail d
left join sae.urgence_p p2 on p2.fi=d.fi
left join sae.q20 p on d.fi=p.fi
join etablissement e on e.nofinesset=d.fi
join adresse_raw ar on e.adresse_raw_id=ar.id
join adresse_norm an on ar.adresse_norm_id=an.id
join iris.iris i on i.code=an.iris
where d.an=2019
and d.urg='GEN'
and p.perso='M1340'
and p.an=d.an
and p2.perso='M9999'
and p2.an=d.an
--and d.fi='010000024'
group by d.fi, d.passu, p.etpsal, p.efflib, p2.etpsal, p2.efflib