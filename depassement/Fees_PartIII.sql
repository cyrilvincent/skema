/////Pédiatres///////

select * from ps p
join tarif t on t.ps_id =p.id
join tarif_date_source tds on tds.tarif_id =t.id 
join cabinet c on t.cabinet_id = c.id
join adresse_raw ar on c.adresse_raw_id = ar.id
join adresse_norm an on ar.adresse_norm_id = an.id
join ban b on an.ban_id  = b.id
where t.profession_id =60
and tds.date_source_id >= 2301 and  tds.date_source_id <= 2308

/////Psychiatres///////
select * from ps p
join tarif t on t.ps_id =p.id
join tarif_date_source tds on tds.tarif_id =t.id 
join cabinet c on t.cabinet_id = c.id
join adresse_raw ar on c.adresse_raw_id = ar.id
join adresse_norm an on ar.adresse_norm_id = an.id
join ban b on an.ban_id  = b.id
where (t.profession_id =65 or t.profession_id =66)
and tds.date_source_id >= 2301 and  tds.date_source_id <= 2308

/////Anesthésiste///////
select * from ps p
join tarif t on t.ps_id =p.id
join tarif_date_source tds on tds.tarif_id =t.id 
join cabinet c on t.cabinet_id = c.id
join adresse_raw ar on c.adresse_raw_id = ar.id
join adresse_norm an on ar.adresse_norm_id = an.id
join ban b on an.ban_id  = b.id
where t.profession_id =3
and tds.date_source_id >= 2301 and  tds.date_source_id <= 2308

/////Radiologistes///////
select * from ps p
join tarif t on t.ps_id =p.id
join tarif_date_source tds on tds.tarif_id =t.id 
join cabinet c on t.cabinet_id = c.id
join adresse_raw ar on c.adresse_raw_id = ar.id
join adresse_norm an on ar.adresse_norm_id = an.id
join ban b on an.ban_id  = b.id
where t.profession_id =67
and tds.date_source_id >= 2301 and  tds.date_source_id <= 2308


/////Gynecologistes///////
select * from ps p
join tarif t on t.ps_id =p.id
join tarif_date_source tds on tds.tarif_id =t.id 
join cabinet c on t.cabinet_id = c.id
join adresse_raw ar on c.adresse_raw_id = ar.id
join adresse_norm an on ar.adresse_norm_id = an.id
join ban b on an.ban_id  = b.id
where (t.profession_id =35 or t.profession_id =36 or t.profession_id =37)
and tds.date_source_id >= 2301 and  tds.date_source_id <= 2308



/////Cardiologues///////
select * from ps p
join tarif t on t.ps_id =p.id
join tarif_date_source tds on tds.tarif_id =t.id 
join cabinet c on t.cabinet_id = c.id
join adresse_raw ar on c.adresse_raw_id = ar.id
join adresse_norm an on ar.adresse_norm_id = an.id
join ban b on an.ban_id  = b.id
where t.profession_id =6
and tds.date_source_id >= 2301 and  tds.date_source_id <= 2308


/////Ophtalmologistes///////
select * from ps p
join tarif t on t.ps_id =p.id
join tarif_date_source tds on tds.tarif_id =t.id 
join cabinet c on t.cabinet_id = c.id
join adresse_raw ar on c.adresse_raw_id = ar.id
join adresse_norm an on ar.adresse_norm_id = an.id
join ban b on an.ban_id  = b.id
where t.profession_id =56
and tds.date_source_id >= 2301 and  tds.date_source_id <= 2308


/////Gastroentérologue///////
select * from ps p
join tarif t on t.ps_id =p.id
join tarif_date_source tds on tds.tarif_id =t.id 
join cabinet c on t.cabinet_id = c.id
join adresse_raw ar on c.adresse_raw_id = ar.id
join adresse_norm an on ar.adresse_norm_id = an.id
join ban b on an.ban_id  = b.id
where t.profession_id =33
and tds.date_source_id >= 2301 and  tds.date_source_id <= 2308


/////dermatologue///////
select * from ps p
join tarif t on t.ps_id =p.id
join tarif_date_source tds on tds.tarif_id =t.id 
join cabinet c on t.cabinet_id = c.id
join adresse_raw ar on c.adresse_raw_id = ar.id
join adresse_norm an on ar.adresse_norm_id = an.id
join ban b on an.ban_id  = b.id
where t.profession_id =22
and tds.date_source_id >= 2301 and  tds.date_source_id <= 2308



/////Dentistes///////
select * from ps p
join tarif t on t.ps_id =p.id
join tarif_date_source tds on tds.tarif_id =t.id 
join cabinet c on t.cabinet_id = c.id
join adresse_raw ar on c.adresse_raw_id = ar.id
join adresse_norm an on ar.adresse_norm_id = an.id
join ban b on an.ban_id  = b.id
where (t.profession_id =18 or t.profession_id =19 or t.profession_id =20 or t.profession_id =21)
and tds.date_source_id >= 2301 and  tds.date_source_id <= 2308

