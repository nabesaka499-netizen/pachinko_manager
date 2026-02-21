@echo off
echo Updating GitHub repository...
"C:\Program Files\Git\cmd\git.exe" add .
"C:\Program Files\Git\cmd\git.exe" commit -m "Add History Management (Delete past records) and Island-wide weighted averages"
"C:\Program Files\Git\cmd\git.exe" push origin main
echo.
echo Update complete!
pause
