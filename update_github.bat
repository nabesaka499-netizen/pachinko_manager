@echo off
echo Updating GitHub repository...
"C:\Program Files\Git\cmd\git.exe" add .
"C:\Program Files\Git\cmd\git.exe" commit -m "Fix calculator title to show ALTA for non-Lafesta stores"
"C:\Program Files\Git\cmd\git.exe" push origin main
echo.
echo Update complete!
pause
