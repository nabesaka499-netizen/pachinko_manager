@echo off
echo Configuring Git user...
"C:\Program Files\Git\cmd\git.exe" config --global user.email "nabesaka499@gmail.com"
"C:\Program Files\Git\cmd\git.exe" config --global user.name "nabesaka499"
echo.
echo Committing initial files...
"C:\Program Files\Git\cmd\git.exe" add .
"C:\Program Files\Git\cmd\git.exe" commit -m "Initial commit: Pachinko Manager (Sea Story 4 SP)"
echo.
echo Git setup complete!
pause
