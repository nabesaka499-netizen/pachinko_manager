@echo off
echo Updating GitHub repository...
"C:\Program Files\Git\cmd\git.exe" add .
"C:\Program Files\Git\cmd\git.exe" commit -m "Rename application title to ホール別 実践データ管理表"
"C:\Program Files\Git\cmd\git.exe" push origin main
echo.
echo Update complete!
pause
