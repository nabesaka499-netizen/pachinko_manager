@echo off
echo Updating GitHub repository...
"C:\Program Files\Git\cmd\git.exe" add .
"C:\Program Files\Git\cmd\git.exe" commit -m "Add remarks and detailed stats to list"
"C:\Program Files\Git\cmd\git.exe" push origin main
echo.
echo Update complete!
pause
