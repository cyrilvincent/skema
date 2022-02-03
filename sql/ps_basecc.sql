select * from ps p, ps_cabinet_date_source pcds, cabinet c, adresse_raw ar, adresse_norm an, ban b, basecc17 bcc
where p.id = pcds.ps_id
and pcds.cabinet_id = c.id
and c.adresse_raw_id = ar.id
and ar.adresse_norm_id = an.id
and an.ban_id  = b.id
and b.code_insee = bcc."CODGEO"
and an.source_id != 3

union

select * from ps p, ps_cabinet_date_source pcds, cabinet c, adresse_raw ar, adresse_norm an, ban b, basecc17 bcc, etablissement e
where p.id = pcds.ps_id
and pcds.cabinet_id = c.id
and c.adresse_raw_id = ar.id
and ar.adresse_norm_id = an.id
and an.ban_id  = b.id
and an.source_id = 3
and e.adresse_raw_id = c.adresse_raw_id
and e.cog = bcc."CODGEO"