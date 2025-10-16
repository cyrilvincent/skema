select an.id, an.ban_score, abs(an.lon-ban.lon) + abs(an.lat-ban.lat) delta, an.lon alon, ban.lon blon, an.lat alat, ban.lat blat from adresse_norm an
join ban on ban.id=an.ban_id
where source_id=3
and ban_score is not null and ban_score>0.99
and abs(an.lon-ban.lon) + abs(an.lat-ban.lat) > 0.01
and ban.lon != 0 and ban.lat != 0
--and an.id=10532
order by delta desc

-- Pas très fiable
with dup as (
	select count(an.id) nb, an.lon, an.lat from adresse_norm an
	where an.source_id=3
	group by an.lon, an.lat
	having count(an.id)>10
	order by nb desc
)
select an.id, an.ban_score, abs(an.lon-ban.lon) + abs(an.lat-ban.lat) delta, an.lon alon, ban.lon blon, an.lat alat, ban.lat blat from adresse_norm an
join ban on ban.id=an.ban_id
join dup on dup.lon=an.lon and dup.lat=an.lat
where source_id=3
and ban_score is not null and ban_score>0.85
and abs(an.lon-ban.lon) + abs(an.lat-ban.lat) > 0.01
and ban.lon != 0 and ban.lat != 0
--and an.id=105321
order by delta desc
-- Ca ne marche pas pour la pharmacie des menuires an.id=158179

update adresse_norm as an
set an.lon=ban.lon, an.lat=ban.lat, an.source_id=2
from ban
where ban.id=an.ban_id
and an.source_id=3
and an.ban_score is not null and an.ban_score>0.99
and abs(an.lon-ban.lon) + abs(an.lat-ban.lat) > 0.01
and ban.lon != 0 and ban.lat != 0 --1162



