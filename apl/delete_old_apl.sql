select * from apl.apl a, apl.apl_study s
--using apl.apl_study s
where s.key=a.study_key
and s.date < '2025-10-25'

delete from apl.apl a --, apl.apl_study s
using apl.apl_study s
where s.key=a.study_key
and s.date < '2025-10-25'

delete from apl.apl_study s
where s.date < '2025-10-25'