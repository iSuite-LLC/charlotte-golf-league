@echo off
REM ─── IMI Golf League — Manual Recap Generator ───────────────────────────────
REM Run this bat to force-generate a recap for a specific round.
REM Usage: Double-click (runs for today's scheduled round)
REM        OR drag it into Command Prompt and add a round number: run_recap.bat 1
cd /d "%~dp0"
if "%1"=="" (
    python setup\generate_recap.py
) else (
    python setup\generate_recap.py %1
)
echo.
pause
