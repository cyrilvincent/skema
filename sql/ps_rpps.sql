select * from ps
join tarif t on t.ps_id=ps.id
join cabinet c on t.cabinet_id=c.id
join adresse_raw ar on c.adresse_raw_id=ar.id
join adresse_norm an on ar.adresse_norm_id=an.id
join personne p on p.inpp=ps.key
join etat_civil ec on p.id=ec.personne_id
join diplome_obtenu do2 on p.id=do2.personne_id
join specialite_profession sp on sp.profession_id=t.profession_id
where sp.specialite_id=7

select * from specialite pour avoir les specialite_id

-- Ceux qui ne matchent pas
select distinct(ps.*) from ps
join tarif t on t.ps_id=ps.id
left outer join personne p on p.inpp=ps.key
join specialite_profession sp on sp.profession_id=t.profession_id
where p.id is null
and sp.specialite_id=7