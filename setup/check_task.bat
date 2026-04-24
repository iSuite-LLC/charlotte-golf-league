@echo off
timeout /t 3 /nobreak
schtasks /Query /TN "IMI Golf League Watcher" /FO LIST
