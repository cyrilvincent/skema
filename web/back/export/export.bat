d:
set PGPASSWORD=sa
D:\PostgreSQL\17\bin\pg_dump -U postgres -d icip --inserts --encoding=UTF8 ^
  -t dept ^
  -t etablissement ^
  -t etablissement_date_source ^
  -t date_source ^
  -t ehpad ^
  > d:\export_public.sql

D:\PostgreSQL\17\bin\pg_dump -U postgres -d icip --inserts --encoding=UTF8 ^
  -t adresse_raw_export ^
  -t adresse_norm_export ^
  > d:\export_public_export.sql

D:\PostgreSQL\17\bin\pg_dump -U postgres -d icip --inserts --encoding=UTF8 ^
  -t iris.commune ^
  -t iris.iris ^
  -t iris.cp_insee ^
  -t iris.filo ^
  -t iris.filo_france ^
  -t iris.pop_iris ^
  -t iris.pop_france ^
  > d:\export_iris.sql

D:\PostgreSQL\17\bin\pg_dump -U postgres -d icip --encoding=UTF8 --verbose ^
  -t sae.dist_study_export ^
  -t sae.dist_export ^
  -t sae.urgence_detail ^
  -t sae.urgence_p ^
  -t sae.psy ^
  -t sae.ehpad_france ^
  > export_sae.sql

D:\PostgreSQL\17\bin\pg_dump -U postgres -d icip --encoding=UTF8 --verbose ^
  -t apl.apl_study_export ^
  -t apl.apl_s_study_export ^
  > export_apl_studies.sql

D:\PostgreSQL\17\bin\pg_dump -U postgres -d icip --encoding=UTF8 --verbose ^
  -t apl.apl_export ^
  > export_apl_export.sql

D:\PostgreSQL\17\bin\pg_dump -U postgres -d icip --encoding=UTF8 --verbose ^
  -t apl.apl_s_export ^
  > export_apl_s_export.sql

Import
======

psql : sudo -u postgres psql -d icip
import : sudo -u postgres psql -d icip < export.sql
\dt
\d table
\dt schema.*


/!\ Faire les trunc et les drop uniquement via psql car le danger de suppression accidentielle sur benjamin est réelle
/!\ Faire un backup avant

schema public: ok
    export_public*
    copier export_public*
    drop *_export
    import
    verif les select count(*) sous psql
    verif les contraintes et index via \d table
    ALTER TABLE adresse_norm_export RENAME TO adresse_norm
    ALTER TABLE adresse_raw_export RENAME TO adresse_raw

schema iris:
    cp_insee unique cyril ok benjamin ok
    filo idem year + is_dec + iris cyril ok & benjamin ok
    Ajouter les index dans *_france.sql cyril ok & benjamin ok
        filo_france year is_dec ok
        pop_france year ok
    pop_iris cyril ok & benjamin ok
    export_iris ok
    copier export_iris ok
    drop les tables sans cascade ok
    import ok
    verif count ok
    verif fk pk index ok

schema sae: ok
    dist_study & dist_study_export : cyril ok benjamin ok
    dist & dist_export cyril ok benjamin ok
    urgence_detail ok pas de key unique table à effacer à chaque import
    urgence_p ok pas de key unique table à effacer à chaque import
    psy ok pas de key unique table à effacer à chaque import
    ehpad_france ok
    modif export_sae pour --insert et utf8 ok
    copier ok
    import en cours ok
    verif rapide ok
    ALTER TABLE sae.dist_study_export RENAME TO dist_study ok
    ALTER TABLE sae.dist_export RENAME TO dist ok

schema apl ok
    apl_study & apl_study_export ok
    apl_s_study & apl_s_study_export ok
    modif export_apl_studies ok
    export_apl_studies ok
    copier ok
    import verif rapide ok
    apl & apl_export ok
    apl_s & apl_s_export ok
    modif export_apl_export & export_apl_s_export & index ok
    export_apl_export ok
    copier ok & import ok
    export_apl_s_export ok
    copier ok & import ok
    ALTER TABLE apl.apl_study_export RENAME TO apl_study;
    ALTER TABLE apl.apl_export RENAME TO apl;
    ALTER TABLE apl.apl_s_study_export RENAME TO apl_s_study;
    ALTER TABLE apl.apl_s_export RENAME TO apl_s;
    tout ok

Sauvegarder la base
pg_dump --file "chaire_paas.bak" --host "localhost" --port "5432" --username "postgres" --verbose --format=c --section=pre-data --section=data --section=post-data "icip"







