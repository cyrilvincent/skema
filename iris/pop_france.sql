create table iris.pop_france as
select p.year, sum(p.pop)::integer pop, sum(p.pop65p)::integer pop65p, sum(p.pop65p)/sum(p.pop) pop65p_ratio from iris.pop_iris p
group by p.year
order by year

CREATE UNIQUE INDEX pop_france_year ON iris.pop_france (year);