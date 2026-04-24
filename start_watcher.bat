@echo off
title IMI Golf League — Score Watcher
cd /d "C:\Users\ehigh\claude\Golf League"
echo Starting league watcher...
echo Close this window to stop monitoring.
echo.
py -3 setup\watcher.py
pause
