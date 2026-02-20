@echo off
echo Updating GitHub repository...
"C:\Program Files\Git\cmd\git.exe" add .
"C:\Program Files\Git\cmd\git.exe" commit -m "Update expectation logic for Lafesta 5 based on Sea Story 4 SP border data"
"C:\Program Files\Git\cmd\git.exe" push origin main
echo.
echo Update complete!
pause
