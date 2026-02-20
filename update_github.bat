@echo off
echo Updating GitHub repository...
"C:\Program Files\Git\cmd\git.exe" add .
"C:\Program Files\Git\cmd\git.exe" commit -m "Hide expectation calculator for store 999"
"C:\Program Files\Git\cmd\git.exe" push origin main
echo.
echo Update complete!
pause
