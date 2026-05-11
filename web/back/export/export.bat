d:
move export.sql export.bak
set PGPASSWORD=sa
D:\PostgreSQL\17\bin\pg_dump -U postgres -d icip ^
  -t iris.commune ^
  -t iris.iris ^
  -t iris.cp_insee ^
  -t iris.filo ^
  -t iris.filo_france ^
  -t iris.pop_iris ^
  -t iris.pop_france ^
  -t dept ^
  -t etablissement ^
  -t etablissement_date_source ^
  -t date_source ^
  -t ehpad ^
  -t adresse_raw_export ^
  -t adresse_norm_export ^
  > export.sql

D:\PostgreSQL\17\bin\pg_dump -U postgres -d icip ^
  -t sae.dist_study_export ^
  -t sae.dist_export ^
  -t sae.urgence_detail ^
  -t sae.urgence_p ^
  -t sae.psy ^
  -t sae.ehpad_france ^
  > export_sae.sql

D:\PostgreSQL\17\bin\pg_dump -U postgres -d icip ^
  -t apl.apl_study_export ^
  -t apl.apl_export ^
  > export_apl.sql

D:\PostgreSQL\17\bin\pg_dump -U postgres -d icip ^
  -t apl.apl_s_study_export ^
  -t apl.apl_s_export ^
  > export_apl_s.sql


sed s/adresse_raw_export/adresse_raw/g export.sql > export_temp.sql
sed s/adresse_norm_export/adresse_norm/g export_temp.sql > export_final.sql

sed s/apl_study_export/apl_study/g export_apl.sql > export_temp.sql
sed s/apl_export/apl/g export_temp.sql > export_apl_final.sql

sed s/apl_s_study_export/apl_s_study/g export_apl_s.sql > export_temp.sql
sed s/apl_s_export/apl_s/g export_temp.sql > export_apl_s_final.sql

sed s/dist_study_export/dist_study/g export_sae.sql > export_temp.sql
sed s/dist_export/dist/g export_temp.sql > export_sae_final.sql

