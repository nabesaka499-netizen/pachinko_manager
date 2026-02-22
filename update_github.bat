@echo off
echo Updating GitHub repository...
"C:\Program Files\Git\cmd\git.exe" add .
"C:\Program Files\Git\cmd\git.exe" commit -m "Align Sea 5 SP with reference images: Default 1400 balls and refined hit counts"
"C:\Program Files\Git\cmd\git.exe" push origin main
echo.
echo Update complete!
pause
