@echo off
echo Updating GitHub repository...
"C:\Program Files\Git\cmd\git.exe" add .
"C:\Program Files\Git\cmd\git.exe" commit -m "Remove redundant 'Delete 1 Item' and 'Undo' buttons from sidebar"
"C:\Program Files\Git\cmd\git.exe" push origin main
echo.
echo Update complete!
pause
