set PGPASSWORD=sa
"C:\Program Files\PostgreSQL\14\bin\pg_dump.exe" -U postgres -d icip --inserts --encoding=UTF8 -t doctolib.ps_france_2607 -t doctolib.ps_06_2606 -t doctolib.tarif ^ > export_doctolib.sql
