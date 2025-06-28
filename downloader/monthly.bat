echo ICIP Monthly
python --version
call %icippath%\.venv\Scripts\activate.bat
cd %icippath%
move %icippath%\downloader\logs\ban.log %icippath%\downloader\logs\ban.1
python -m downloader.ban_downloader > %icippath%\downloader\logs\ban.log 2>&1
move %icippath%\downloader\logs\etalab.log %icippath%\downloader\logs\etalab.1
python -m downloader.etalab_downloader > %icippath%\downloader\logs\etalab.log 2>&1
move %icippath%\downloader\logs\ehpad.log %icippath%\downloader\logs\ehpad.1
python -m downloader.ehpad_downloader > %icippath%\downloader\logs\ehpad.log 2>&1
move %icippath%\downloader\logs\ps_libreacces.1 %icippath%\downloader\logs\ps_libreacces.2
move %icippath%\downloader\logs\ps_libreacces.log %icippath%\downloader\logs\ps_libreacces.1
python -m downloader.ps_libreacces_downloader > %icippath%\downloader\logs\ps_libreacces.log 2>&1
move %icippath%\downloader\logs\rpps.2 %icippath%\downloader\logs\rpps.3
move %icippath%\downloader\logs\rpps.1 %icippath%\downloader\logs\rpps.2
move %icippath%\downloader\logs\rpps.log %icippath%\downloader\logs\rpps.1
python -m downloader.rpps_downloader > %icippath%\downloader\logs\rpps.log 2>&1
move %icippath%\downloader\logs\ps.2 %icippath%\downloader\logs\ps.3
move %icippath%\downloader\logs\ps.1 %icippath%\downloader\logs\ps.2
move %icippath%\downloader\logs\ps.log %icippath%\downloader\logs\ps.1
python -m downloader.ps_downloader > %icippath%\downloader\logs\ps.log 2>&1
move %icippath%\downloader\logs\ban_matcher.log %icippath%\downloader\logs\ban_matcher.1
python ban_matcher.py > %icippath%\downloader\logs\ban_matcher.log 2>&1
move %icippath%\downloader\logs\osm_matcher.log %icippath%\downloader\logs\osm_matcher.1
python osm_matcher.py > %icippath%\downloader\logs\osm_matcher.log 2>&1
move %icippath%\downloader\logs\score_matcher.log %icippath%\downloader\logs\score_matcher.1
python score_matcher.py > %icippath%\downloader\logs\score_matcher.log 2>&1
move %icippath%\downloader\logs\iris_matcher.log %icippath%\downloader\logs\iris_matcher.1
python iris_matcher.py > %icippath%\downloader\logs\iris_matcher.log 2>&1
move "D:\\icip\\backup\\icip.monthly.bak.1" "D:\\icip\\backup\\icip.monthly.bak.2"
move "D:\\icip\\backup\\icip.monthly.bak" "D:\\icip\\backup\\icip.monthly.bak.1"
set PGPASSWORD=sa
D:\PostgreSQL\17\pgAdmin 4\runtime\pg_dump.exe --file "D:\\icip\\backup\\icip.monthly.bak" --host "localhost" --port "5432" --username "postgres" --no-password --verbose --format=c --large-objects --section=pre-data --section=data --section=post-data "icip"