@echo off
echo Updating GitHub repository...
"C:\Program Files\Git\cmd\git.exe" add .
"C:\Program Files\Git\cmd\git.exe" commit -m "Revert Sea 5 SP average hits to previous values (user requested)"
"C:\Program Files\Git\cmd\git.exe" push origin main
echo.
echo Update complete!
pause
