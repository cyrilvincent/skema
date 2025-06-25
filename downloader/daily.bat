echo ICIP Daily
call %icippath%\.venv\Scripts\activate.bat
cd %icippath%
move %icippath%\downloader\logs\ps_daily.log %icippath%\downloader\logs\ps_daily.1
python -m downloader.ps_downloader_daily > %icippath%\downloader\logs\ps_daily.log 2>&1
move "D:\\icip\\backup\\icip.bak.4" "D:\\icip\\backup\\icip.bak.5"
move "D:\\icip\\backup\\icip.bak.3" "D:\\icip\\backup\\icip.bak.4"
move "D:\\icip\\backup\\icip.bak.2" "D:\\icip\\backup\\icip.bak.3"
move "D:\\icip\\backup\\icip.bak.1" "D:\\icip\\backup\\icip.bak.2"
move "D:\\icip\\backup\\icip.bak" "D:\\icip\\backup\\icip.bak.1"
D:\PostgreSQL\17\pgAdmin 4\runtime\pg_dump.exe --file "D:\\icip\\backup\\icip.bak" --host "localhost" --port "5432" --username "postgres" --no-password --format=c --large-objects --section=pre-data --section=data --section=post-data "icip"