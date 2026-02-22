@echo off
echo Updating GitHub repository...
"C:\Program Files\Git\cmd\git.exe" add .
"C:\Program Files\Git\cmd\git.exe" commit -m "Update Sea 5 SP simulation data with user-provided measured values"
"C:\Program Files\Git\cmd\git.exe" push origin main
echo.
echo Update complete!
pause
