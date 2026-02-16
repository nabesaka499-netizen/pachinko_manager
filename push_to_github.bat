@echo off
echo ==========================================
echo  Pushing to GitHub
echo ==========================================
echo.
echo 1. Go to https://github.com/new
echo 2. Create a new repository (Name it 'pachinko_manager' etc.)
echo 3. IMPORTANT: Do NOT check "Add a README file" (Keep it empty)
echo 4. Click "Create repository"
echo.
set /p REPO_URL="5. Paste the HTTPS URL here (e.g. https://github.com/user/repo.git): "
echo.
echo Setting up remote...
"C:\Program Files\Git\cmd\git.exe" remote remove origin 2>nul
"C:\Program Files\Git\cmd\git.exe" remote add origin %REPO_URL%
echo.
echo Renaming branch...
"C:\Program Files\Git\cmd\git.exe" branch -M main
echo.
echo Pushing code to GitHub...
"C:\Program Files\Git\cmd\git.exe" push -u origin main
echo.
pause
