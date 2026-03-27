create table iris.filo_france as
SELECT sum(f.tp60 * p.pop)/sum(p.pop) tp60, sum(f.med * p.pop)/sum(p.pop) med, sum(f.gi * p.pop)/sum(p.pop) gi, f.year, f.is_dec
FROM iris.filo f
join iris.pop_iris p on p.iris_id=f.iris and f.year=p.year
group by f.year, f.is_dec

create table iris.pop_france as
select p.year, sum(p.pop)::integer pop, sum(p.pop65p)::integer pop65p, sum(p.pop65p)/sum(p.pop) pop65p_ratio from iris.pop_iris p
group by p.year
order by year