-- contient un od mais direct_km > 200
select * from iris.iris_matrix where direct_km is null

-- iles ou loin de routes
select distinct(iris.iris_matrix.iris_id_from), count(iris.iris_matrix.iris_id_from) as nb, iris.iris.nom_norm as iris_nom, iris.commune.code as commune_code, iris.commune.nom_norm as commune
from iris.iris_matrix
join iris.iris on iris.iris.id = iris.iris_matrix.iris_id_from
join iris.commune on iris.commune.id = iris.iris.commune_id
where direct_km <= 100
and route_km is null
group by iris.iris_matrix.iris_id_from, iris.iris.nom_norm, iris.commune.code, iris.commune.nom_norm
having count(iris.iris_matrix.iris_id_from) > 10
order by nb desc

--        # 502180101	1534	"QUARTIER HAUTE VILLE ET CENTRE VILLE"	"50218"	"GRANVILLE"
--        # 830690125	1321	"LE LEVANT"	"83069"	"HYERES"
--        # 830690123	1268	"PORQUEROLLES"	"83069"	"HYERES"
--        # 830690124	1234	"PORT CROS"	"83069"	"HYERES"
--        # 170040000	1147	"ILE D AIX"	"17004"	"ILE D AIX"
--        # 654650000	958	"VIELLE AURE"	"65465"	"VIELLE AURE"  n'est pas une ile'
--        # 642230000	830	"ETSAUT"	"64223"	"ETSAUT"  n'est pas une ile
--        # 851130102	689	"SUD EST"	"85113"	"L ILE D YEU"
--        # 851130101	678	"NORD OUEST"	"85113"	"L ILE D YEU"
--        # 220160000	663	"ILE DE BREHAT"	"22016"	"ILE DE BREHAT"
--        # 660050000	662	"ANGOUSTRINE VILLENEUVE DES ESCALDES"	"66005"	"ANGOUSTRINE VILLENEUVE DES ESCALDES"  pas une ile
--        # 660430000	627	"CASTEIL"	"66043"	"CASTEIL"  pas une ile
--        # 61020000	623	"RIMPLAS"	"06102"	"RIMPLAS"  dans la tinée
--        # 2011960000	121	"ORTO"	"2A196"	"ORTO"  pas de route en corse

-- iris_matrix iles
select distinct(iris_id_from) from iris.iris_matrix
where iris_id_from in (502180101, 830690125, 830690123, 830690124, 170040000, 654650000, 851130102, 851130101, 220160000)

-- update iles
update iris.iris_matrix
set route_km = direct_km * 2, route_min = 60 + direct_km * 2, route_hp_min = 120 + direct_km * 2
where iris_id_from in (502180101, 830690125, 830690123, 830690124, 170040000, 654650000, 851130102, 851130101, 220160000)
or iris_id_to in (502180101, 830690125, 830690123, 830690124, 170040000, 654650000, 851130102, 851130101, 220160000)

-- les non iles ont étés corrigées à la main

-- ne doit pas arriver
select * from iris.iris_matrix where direct_km is null and od_km is null

-- corse vs non corse
update iris.iris_matrix
set route_km = direct_km * 2, route_min = 720 + direct_km * 2, route_hp_min = 1000 + direct_km * 2
where iris_id_from > 2000000000 and iris_id_to < 2000000000
and route_km is null

update iris.iris_matrix
set route_km = direct_km * 2, route_min = 720 + direct_km * 2, route_hp_min = 1000 + direct_km * 2
where iris_id_from < 2000000000 and iris_id_to > 2000000000
and route_km is null

-- les derniers récalcitrants (26)
update iris.iris_matrix
set route_km = direct_km * 2, route_min = direct_km * 3, route_hp_min = 1 + direct_km * 3
where route_km is null and direct_km is not null

-- Gérer les iles de commune comme 22016
update iris.commune_matrix
set route_km = direct_km * 2, route_min = 60 + direct_km * 2, route_hp_min = 120 + direct_km * 2
where (code_id_low in (22016, 17004)
or code_id_high in (22016, 17004))
and route_km is null

-- les derniers récalcitrants (41)
update iris.commune_matrix
set route_km = direct_km * 2, route_min = direct_km * 3, route_hp_min = 1 + direct_km * 3
where route_km is null and direct_km is not null