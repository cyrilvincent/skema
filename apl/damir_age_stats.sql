
create table apl.damir_age_stats as(
	with total_count as (
		select count(*) total_nb, flx_ann_moi/100 ann, psp_spe_snds from damir
		where prs_rem_typ=0
		group by ann, psp_spe_snds
	)
	select d.psp_spe_snds, d.flx_ann_moi/100 ann, d.age_ben_snds, count(d.id) nb, tc.total_nb, count(d.id)/tc.total_nb::float ratio
	from damir d
	join total_count tc on tc.ann=d.flx_ann_moi/100 and tc.psp_spe_snds=d.psp_spe_snds
	where prs_rem_typ=0
	group by d.age_ben_snds, d.flx_ann_moi/100, tc.total_nb, d.psp_spe_snds
	order by d.psp_spe_snds, ann, d.age_ben_snds
)

-- En test 2h18
create table apl.damir_age_stats_2 as(
with total_count as (
		select count(*) total_nb, flx_ann_moi/100 ann, psp_spe_snds from damir
		where prs_rem_typ=0
		group by ann, psp_spe_snds
	), total_count_2 as (
		select count(*) total_nb, flx_ann_moi/100 ann, psp_act_snds from damir
		where prs_rem_typ=0
		group by ann, psp_act_snds
	)
(select d.psp_spe_snds, null psp_act_snds, d.flx_ann_moi/100 ann, d.age_ben_snds, count(d.id) nb, tc.total_nb, count(d.id)/tc.total_nb::float ratio
from damir d
join total_count tc on tc.ann=d.flx_ann_moi/100 and tc.psp_spe_snds=d.psp_spe_snds
where prs_rem_typ=0
group by d.age_ben_snds, d.flx_ann_moi/100, tc.total_nb, d.psp_spe_snds

union all

select null psp_spe_snds, d.psp_act_snds, d.flx_ann_moi/100 ann, d.age_ben_snds, count(d.id) nb, tc.total_nb, count(d.id)/tc.total_nb::float ratio
from damir d
join total_count_2 tc on tc.ann=d.flx_ann_moi/100 and tc.psp_act_snds=d.psp_act_snds
where prs_rem_typ=0
group by d.age_ben_snds, d.flx_ann_moi/100, tc.total_nb, d.psp_act_snds)

order by  psp_spe_snds,psp_act_snds, ann, age_ben_snds
)

