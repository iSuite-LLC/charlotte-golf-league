@echo off
REM ─── IMI Golf League — Register Recap Generator Task ─────────────────────────
REM Run this ONCE (as yourself, no admin needed for /F override on user tasks).
REM Creates a weekly Monday 8 AM task that auto-generates recap email drafts.

schtasks /Create ^
  /TN "IMI Golf League Recap Generator" ^
  /TR "python \"C:\Users\ehigh\claude\Golf League\setup\generate_recap.py\"" ^
  /SC WEEKLY ^
  /D MON ^
  /ST 08:00 ^
  /F

echo.
echo Task registered. It will run every Monday at 8:00 AM.
echo On recap Mondays (May 4, May 18, Jun 1, etc.) it auto-saves a draft to:
echo   C:\Users\ehigh\claude\Golf League\Recap Emails\
echo.
pause
