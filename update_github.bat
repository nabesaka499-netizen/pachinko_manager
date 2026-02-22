@echo off
echo Updating GitHub repository...
"C:\Program Files\Git\cmd\git.exe" add .
"C:\Program Files\Git\cmd\git.exe" commit -m "Fix mobile cut-off by changing metrics to 2x2 grid"
"C:\Program Files\Git\cmd\git.exe" push origin main
echo.
echo Update complete!
pause
