@echo off
echo Initializing Git Repository...
"C:\Program Files\Git\cmd\git.exe" init
"C:\Program Files\Git\cmd\git.exe" add .
"C:\Program Files\Git\cmd\git.exe" commit -m "Initial commit"
echo.
echo Git repository initialized successfully!
pause
