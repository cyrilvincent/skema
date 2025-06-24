echo ICIP Daily
call %icippath%\.venv\Scripts\activate.bat
cd %icippath%
move %icippath%\downloader\logs\ps_daily.log %icippath%\downloader\logs\ps_daily.1
python -m downloader.ps_downloader_daily > %icippath%\downloader\logs\ps_daily.log 2>&1