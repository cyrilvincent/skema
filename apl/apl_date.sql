select max(date) date from apl.apl_study
group by specialite_id
order by max(date)