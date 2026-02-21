@echo off
echo Updating GitHub repository...
"C:\Program Files\Git\cmd\git.exe" add .
"C:\Program Files\Git\cmd\git.exe" commit -m "Fix ValueError (unpacking) and finalize table average formatting"
"C:\Program Files\Git\cmd\git.exe" push origin main
echo.
echo Update complete!
pause
