@echo off
echo Updating GitHub repository...
"C:\Program Files\Git\cmd\git.exe" add .
"C:\Program Files\Git\cmd\git.exe" commit -m "Simplify exchange rate and average out labels in calculator"
"C:\Program Files\Git\cmd\git.exe" push origin main
echo.
echo Update complete!
pause
