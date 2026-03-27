create table sae.ehpad_france as
SELECT avg(e.prixhebpermcs) prixhebpermcs, ds.annee+2000 as year
FROM public.ehpad e
join date_source ds on ds.id=e.datesource_id
group by ds.annee