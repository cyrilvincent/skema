create table apl.damir_age_stats as(
	with total_count as (
		select count(*) total_nb, flx_ann_moi/100 ann, psp_spe_snds from damir
		group by ann, psp_spe_snds
	)
	select d.psp_spe_snds, d.flx_ann_moi/100 ann, d.age_ben_snds, count(d.id) nb, tc.total_nb, count(d.id)/tc.total_nb::float ratio
	from damir d
	join total_count tc on tc.ann=d.flx_ann_moi/100 and tc.psp_spe_snds=d.psp_spe_snds
	group by d.age_ben_snds, d.flx_ann_moi/100, tc.total_nb, d.psp_spe_snds
	order by d.psp_spe_snds, ann, d.age_ben_snds
)
