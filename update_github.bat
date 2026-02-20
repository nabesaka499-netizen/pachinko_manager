@echo off
echo Updating GitHub repository...
"C:\Program Files\Git\cmd\git.exe" add .
"C:\Program Files\Git\cmd\git.exe" commit -m "Add P大海物語5SP ALTA expectation calculator to 999 and Super Hollywood stores"
"C:\Program Files\Git\cmd\git.exe" push origin main
echo.
echo Update complete!
pause
