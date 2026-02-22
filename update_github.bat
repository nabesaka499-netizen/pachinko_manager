@echo off
echo Updating GitHub repository...
"C:\Program Files\Git\cmd\git.exe" add .
"C:\Program Files\Git\cmd\git.exe" commit -m "Fix Streamlit session state crash by moving record logic above widgets"
"C:\Program Files\Git\cmd\git.exe" push origin main
echo.
echo Update complete!
pause
