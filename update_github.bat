@echo off
echo Updating GitHub repository...
"C:\Program Files\Git\cmd\git.exe" add .
"C:\Program Files\Git\cmd\git.exe" commit -m "Refine Sea 5 SP simulation data (hits/time) for stores 999 and Hollywood"
"C:\Program Files\Git\cmd\git.exe" push origin main
echo.
echo Update complete!
pause
