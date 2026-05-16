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
  -t apl.apl_s_study_export ^
  > export_apl_studies.sql

D:\PostgreSQL\17\bin\pg_dump -U postgres -d icip --encoding=UTF8 ^
  -t apl.apl_export ^
  > export_apl_export.sql

D:\PostgreSQL\17\bin\pg_dump -U postgres -d icip --encoding=UTF8 ^
  -t apl.apl_s_export ^
  > export_apl_s_export.sql

psql : sudo -u postgres psql -d icip
import : sudo -u postgres psql -d icip < export.sql
\dt
\d table
\dt schema.*


/!\ Faire les trunc et les drop uniquement via psql car le danger de suppression accidentielle sur benjamin est réelle
/!\ Faire un backup avant
/!\ avant de trunc ou remove table d'être bien sur chaire_paas, l'erreur est vite arrivée

schema public: ok
    Attendre fin apl_service.py
    Backup db
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
    filo idem year + is_dec + iris cyril & benjamin
    filo_france idem year + is_dec cyril & benjamin
    Ajouter les index dans *_france.sql
    pop_france idem cyril & benjamin
    pop_iris idem cyril & benjamin
    export_iris
    copier export_iris
    effacer et recréer le schema iris drop schema iris cascade; create schema iris
    import
    verif les select count(*) sous psql
    verif les contraintes et index via \d table

schema sae:
    index, fk et pk
    export_sae



Faire les export apl en CSV (trop lent) mettre les 2 studies à part car petits
\copy users FROM 'file.csv' WITH CSV HEADER ENCODING 'UTF8';
Ou bien tester pg_dump avec copy en utf8

ALTER TABLE nom_table ADD PRIMARY KEY (colonne);
CREATE UNIQUE INDEX nom_index ON nom_table (colonne1, colonne2)
CREATE INDEX nom_index ON nom_table (colonne1, colonne2
ALTER TABLE nom_table RENAME TO nouveau_nom
ALTER TABLE table_enfant ADD CONSTRAINT nom_fk FOREIGN KEY (colonne_enfant) REFERENCES table_parent(colonne_parent); les FK suivent le renommage








