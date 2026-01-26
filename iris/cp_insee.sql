create table iris.cp_insee as
select code_postal, code_insee from ban
group by code_postal, code_insee
order by code_postal, code_insee