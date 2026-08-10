@echo off
REM ============================================================
REM  IMI Golf League - push pending changes to GitHub
REM  Double-click this file to publish updates to the website.
REM  GitHub Pages rebuilds automatically after the push.
REM ============================================================

cd /d "%~dp0"

echo.
echo ========================================
echo   IMI GOLF LEAGUE - PUBLISH TO WEBSITE
echo ========================================
echo.

echo Pending changes:
echo.
git status --short
echo.

set /p MSG="Commit message (press Enter for default): "
if "%MSG%"=="" set MSG=Update league standings and schedule

echo.
echo Staging changes...
git add -A

echo Committing...
git commit -m "%MSG%"
if errorlevel 1 (
    echo.
    echo Nothing to commit, or the commit failed. See the message above.
    echo.
    pause
    exit /b 1
)

echo Pushing to GitHub...
git push
if errorlevel 1 (
    echo.
    echo ***  PUSH FAILED  ***
    echo The commit was saved locally but did NOT reach GitHub.
    echo Check your internet connection and GitHub credentials, then
    echo run this file again - it will retry the push.
    echo.
    pause
    exit /b 1
)

echo.
echo ========================================
echo   SUCCESS - pushed to GitHub
echo ========================================
echo.
echo The website rebuilds automatically. Give it 1-2 minutes, then check:
echo   https://isuite-llc.github.io/charlotte-golf-league
echo.
pause
