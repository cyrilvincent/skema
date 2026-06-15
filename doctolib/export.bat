set PGPASSWORD=sa
"C:\Program Files\PostgreSQL\14\bin\pg_dump.exe" -U postgres -d icip --inserts --encoding=UTF8 -t doctolib.ps -t doctolib.tarif ^ > export_doctolib.sql
