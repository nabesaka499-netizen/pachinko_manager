@echo off
echo Updating GitHub repository...
"C:\Program Files\Git\cmd\git.exe" add .
"C:\Program Files\Git\cmd\git.exe" commit -m "Refine calculator defaults: Strictly use island average for specific model only (ignore Agnes)"
"C:\Program Files\Git\cmd\git.exe" push origin main
echo.
echo Update complete!
pause
